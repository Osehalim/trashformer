#!/usr/bin/env python3
"""
arm/arm_controller.py — Arm controller for a 3-servo arm via PCA9685 (Pi -> I2C -> PCA9685)

Semantics (as you described):
- Shoulder: 0° down, 90° horizontal, 180° up
- Elbow: 0° forward/center, rotates RIGHT up to MAX (you set MAX=90 in config)
- Gripper: 0° open, 90° closed

This version:
- Loads config/default.yaml via ConfigLoader
- Loads poses from arm/poses.yaml (relative path)
- Loads servo calibration from data/calibration/servo_limits.json (if present)
  and applies per-servo min/max pulse widths (and optional invert/offset).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, Optional, List, Tuple

import yaml

from utils.logger import get_logger
from utils.config_loader import load_config, ConfigLoader
from arm.pca9685_driver import PCA9685
from arm.servo import Servo

logger = get_logger(__name__)

CALIB_PATH = Path("data/calibration/servo_limits.json")


def _load_servo_calibration(path: Path = CALIB_PATH) -> Dict[str, dict]:
    """Load calibration dict keyed by servo name, or {} if missing/invalid."""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        return {k: v for k, v in data.items() if isinstance(v, dict)}
    except Exception as e:
        logger.warning(f"Could not read calibration file {path}: {e}")
        return {}


def _apply_offset_invert(angle: float, offset_deg: float = 0.0, invert: bool = False) -> float:
    """
    Apply optional offset/invert from calibration.
    Note: invert here means: logical angle increases -> physical decreases.
    """
    a = float(angle) + float(offset_deg)
    if invert:
        a = 180.0 - a
    return a


class ArmController:
    def __init__(self, config: Optional[ConfigLoader] = None, simulate: bool = False):
        if config is None:
            config = load_config()  # defaults to config/default.yaml in your loader

        self.config = config
        self.simulate = bool(simulate)

        # PCA9685 settings (default.yaml)
        i2c_bus = int(self.config.get("hardware.i2c_bus", 1))
        i2c_address = int(self.config.get("hardware.i2c_address", 0x40))
        pwm_freq = int(self.config.get("arm.pwm_frequency", 50))

        logger.info(f"Initializing ArmController (simulate={self.simulate})")
        self.pwm = PCA9685(
            i2c_bus=i2c_bus,
            address=i2c_address,
            frequency=pwm_freq,
            simulate=self.simulate,
        )

        # Movement settings
        self.default_speed = float(self.config.get("arm.movement.default_speed", 50))

        # Global PWM limits (fallbacks)
        global_min_pulse = int(self.config.get("arm.pwm_limits.min_pulse", 500))
        global_max_pulse = int(self.config.get("arm.pwm_limits.max_pulse", 2500))

        # Channels + angle limits
        arm_section = self.config.get_section("arm")
        channels = arm_section.get("servo_channels", {}) or {}
        limits = arm_section.get("angle_limits", {}) or {}

        # Load calibration (if available)
        self.calib = _load_servo_calibration()

        # Create servos
        self.servos: Dict[str, Servo] = {}

        def _servo_pulses(name: str) -> Tuple[int, int, float, bool]:
            """
            Returns (min_pulse, max_pulse, offset_deg, invert) for a servo name.
            Falls back to global pulses if not calibrated.
            """
            c = self.calib.get(name, {})
            min_p = int(c.get("min_pulse", global_min_pulse))
            max_p = int(c.get("max_pulse", global_max_pulse))
            # Optional extras (your calibrator stored these)
            offset = float(c.get("offset_deg", 0.0))
            invert = bool(c.get("invert", False))
            return min_p, max_p, offset, invert

        # Shoulder
        shoulder_cfg = limits.get("shoulder", {}) or {}
        sh_min_p, sh_max_p, sh_off, sh_inv = _servo_pulses("shoulder")
        self._shoulder_offset = sh_off
        self._shoulder_invert = sh_inv

        self.servos["shoulder"] = Servo(
            pwm_controller=self.pwm,
            channel=int(channels.get("shoulder", 0)),
            name="shoulder",
            min_angle=float(shoulder_cfg.get("min", 0)),
            max_angle=float(shoulder_cfg.get("max", 180)),
            min_pulse=sh_min_p,
            max_pulse=sh_max_p,
            home_angle=float(shoulder_cfg.get("home", 0)),
            neutral_angle=float(shoulder_cfg.get("home", 0)),
        )

        # Elbow (your config sets max to 90 for “fully right”)
        elbow_cfg = limits.get("elbow", {}) or {}
        el_min_p, el_max_p, el_off, el_inv = _servo_pulses("elbow")
        self._elbow_offset = el_off
        self._elbow_invert = el_inv

        self.servos["elbow"] = Servo(
            pwm_controller=self.pwm,
            channel=int(channels.get("elbow", 1)),
            name="elbow",
            min_angle=float(elbow_cfg.get("min", 0)),
            max_angle=float(elbow_cfg.get("max", 90)),
            min_pulse=el_min_p,
            max_pulse=el_max_p,
            home_angle=float(elbow_cfg.get("home", 0)),
            neutral_angle=float(elbow_cfg.get("home", 0)),
        )

        # Gripper
        gripper_cfg = limits.get("gripper", {}) or {}
        gr_min_p, gr_max_p, gr_off, gr_inv = _servo_pulses("gripper")
        self._gripper_offset = gr_off
        self._gripper_invert = gr_inv

        self.servos["gripper"] = Servo(
            pwm_controller=self.pwm,
            channel=int(channels.get("gripper", 2)),
            name="gripper",
            min_angle=float(gripper_cfg.get("min", 0)),
            max_angle=float(gripper_cfg.get("max", 90)),
            min_pulse=gr_min_p,
            max_pulse=gr_max_p,
            home_angle=float(gripper_cfg.get("home", 0)),
            neutral_angle=float(gripper_cfg.get("home", 0)),
        )

        # Poses
        self.poses: Dict[str, Dict[str, float]] = {}
        self._load_poses()

        self.current_pose_name: Optional[str] = None
        self.is_enabled: bool = True

        logger.info(
            f"ArmController ready: servos={list(self.servos.keys())}, poses={len(self.poses)}, "
            f"calibration={'FOUND' if self.calib else 'NOT FOUND'}"
        )

    def _load_poses(self) -> None:
        """Load poses from arm/poses.yaml relative to this file."""
        poses_file = Path(__file__).with_name("poses.yaml")
        if not poses_file.exists():
            logger.warning(f"Poses file not found: {poses_file}")
            return

        try:
            data = yaml.safe_load(poses_file.read_text(encoding="utf-8")) or {}
            if not isinstance(data, dict):
                logger.warning("poses.yaml did not parse to a dict; ignoring")
                return

            cleaned: Dict[str, Dict[str, float]] = {}
            for pose_name, pose in data.items():
                if isinstance(pose, dict):
                    cleaned[pose_name] = {k: float(v) for k, v in pose.items()}
            self.poses = cleaned
            logger.info(f"Loaded {len(self.poses)} poses from {poses_file}")
        except Exception as e:
            logger.error(f"Error loading poses: {e}")

    def get_servo(self, name: str) -> Optional[Servo]:
        return self.servos.get(name)

    def get_current_angles(self) -> Dict[str, Optional[float]]:
        return {name: servo.get_angle() for name, servo in self.servos.items()}

    # ---------------- Core movement ----------------

    def set_angles(self, angles: Dict[str, float], validate: bool = True) -> bool:
        if not self.is_enabled:
            logger.warning("Arm is disabled; ignoring set_angles")
            return False

        ok = True
        for name, angle in angles.items():
            servo = self.servos.get(name)
            if servo is None:
                logger.warning(f"Unknown servo: {name}")
                ok = False
                continue

            # Apply optional calibration transform
            if name == "shoulder":
                angle = _apply_offset_invert(angle, self._shoulder_offset, self._shoulder_invert)
            elif name == "elbow":
                angle = _apply_offset_invert(angle, self._elbow_offset, self._elbow_invert)
            elif name == "gripper":
                angle = _apply_offset_invert(angle, self._gripper_offset, self._gripper_invert)

            if not servo.set_angle(float(angle), validate=validate):
                ok = False
        return ok

    def move_to_angles(self, angles: Dict[str, float], speed: Optional[float] = None, blocking: bool = True) -> bool:
        if not self.is_enabled:
            logger.warning("Arm is disabled; ignoring move_to_angles")
            return False

        speed = float(speed) if speed is not None else self.default_speed
        speed = max(1.0, speed)

        # Determine max move time for synchronization
        max_time = 0.0
        moves: List[Tuple[Servo, str, float, float]] = []  # (servo, name, target, delta)

        for name, target in angles.items():
            servo = self.servos.get(name)
            if servo is None:
                logger.warning(f"Unknown servo: {name}")
                continue

            target = float(target)

            # Apply optional calibration transform
            if name == "shoulder":
                target = _apply_offset_invert(target, self._shoulder_offset, self._shoulder_invert)
            elif name == "elbow":
                target = _apply_offset_invert(target, self._elbow_offset, self._elbow_invert)
            elif name == "gripper":
                target = _apply_offset_invert(target, self._gripper_offset, self._gripper_invert)

            current = servo.get_angle()
            if current is None:
                servo.set_angle(target)
                continue

            delta = abs(target - float(current))
            t = delta / speed if speed > 0 else 0.0
            max_time = max(max_time, t)
            moves.append((servo, name, target, delta))

        if not moves:
            return True

        if max_time <= 0:
            for servo, _name, target, _delta in moves:
                servo.set_angle(target)
            return True

        ok = True
        for servo, _name, target, delta in moves:
            servo_speed = (delta / max_time) if max_time > 0 else speed
            servo_speed = max(1.0, servo_speed)
            if not servo.move_to(target, speed=servo_speed, blocking=False):
                ok = False

        if blocking:
            time.sleep(max_time)

        return ok

    # ---------------- Poses ----------------

    def go_to_pose(self, pose_name: str, speed: Optional[float] = None, blocking: bool = True) -> bool:
        pose = self.poses.get(pose_name)
        if pose is None:
            logger.error(f"Unknown pose: {pose_name}")
            return False

        ok = self.move_to_angles(pose, speed=speed, blocking=blocking)
        if ok:
            self.current_pose_name = pose_name
        return ok

    def home(self, speed: Optional[float] = None, blocking: bool = True) -> bool:
        if "home" in self.poses:
            return self.go_to_pose("home", speed=speed, blocking=blocking)
        return self.move_to_angles({"shoulder": 0, "elbow": 0, "gripper": 0}, speed=speed, blocking=blocking)

    def neutral(self, speed: Optional[float] = None, blocking: bool = True) -> bool:
        if "neutral" in self.poses:
            return self.go_to_pose("neutral", speed=speed, blocking=blocking)
        return self.move_to_angles({"shoulder": 0, "elbow": 0, "gripper": 0}, speed=speed, blocking=blocking)

    # ---------------- Convenience controls ----------------

    def shoulder_up(self, angle: float = 180, speed: Optional[float] = None) -> bool:
        return self.move_to_angles({"shoulder": angle}, speed=speed, blocking=True)

    def shoulder_down(self, angle: float = 0, speed: Optional[float] = None) -> bool:
        return self.move_to_angles({"shoulder": angle}, speed=speed, blocking=True)

    def shoulder_horizontal(self, speed: Optional[float] = None) -> bool:
        return self.move_to_angles({"shoulder": 90}, speed=speed, blocking=True)

    def elbow_center(self, speed: Optional[float] = None) -> bool:
        # 0° = forward/center
        return self.move_to_angles({"elbow": 0}, speed=speed, blocking=True)

    def elbow_right(self, angle: float = 90, speed: Optional[float] = None) -> bool:
        # RIGHT only; your max is enforced by servo max_angle (from config)
        return self.move_to_angles({"elbow": angle}, speed=speed, blocking=True)

    def elbow_full_right(self, speed: Optional[float] = None) -> bool:
        # Full-right = elbow servo's configured max (likely 90)
        max_right = float(self.servos["elbow"].max_angle)
        return self.move_to_angles({"elbow": max_right}, speed=speed, blocking=True)

    def open_gripper(self, speed: Optional[float] = None) -> bool:
        return self.move_to_angles({"gripper": 0}, speed=speed, blocking=True)

    def close_gripper(self, speed: Optional[float] = None) -> bool:
        # Note: if your gripper “close” is less than 90 mechanically,
        # put that in poses or change max_angle/home in config or calibration.
        return self.move_to_angles({"gripper": 90}, speed=speed, blocking=True)

    def set_gripper(self, angle: float, speed: Optional[float] = None) -> bool:
        return self.move_to_angles({"gripper": angle}, speed=speed, blocking=True)

    # ---------------- Utilities ----------------

    def list_poses(self) -> List[str]:
        return sorted(self.poses.keys())

    def execute_sequence(self, sequence: List[Tuple], pause_between: float = 0.5) -> bool:
        """
        sequence elements:
          - (pose_name,)
          - (pose_name, speed)
          - (pose_name, speed, pause)
        """
        logger.info(f"Executing sequence of {len(sequence)} poses")
        for i, step in enumerate(sequence):
            pose_name = step[0]
            speed = step[1] if len(step) >= 2 else None
            pause = step[2] if len(step) >= 3 else pause_between

            logger.info(f"Step {i+1}/{len(sequence)}: {pose_name}")
            if not self.go_to_pose(pose_name, speed=speed, blocking=True):
                logger.error(f"Sequence failed at step {i+1} ({pose_name})")
                return False
            time.sleep(pause)

        logger.info("Sequence complete")
        return True

    def emergency_stop(self) -> None:
        """Immediate safest action: disable outputs now."""
        logger.critical("EMERGENCY STOP: disabling all servos NOW")
        self.disable()

    def disable(self) -> None:
        logger.warning("Disabling arm (all servos)")
        for servo in self.servos.values():
            servo.disable()
        self.is_enabled = False

    def enable(self) -> None:
        logger.info("Enabling arm")
        self.is_enabled = True

    def close(self) -> None:
        """
        Clean shutdown:
        - do NOT automatically move the arm
        - disable outputs
        - close PCA9685
        """
        logger.info("Closing ArmController")
        try:
            self.disable()
        finally:
            self.pwm.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __repr__(self) -> str:
        return f"ArmController(servos={list(self.servos.keys())}, poses={len(self.poses)})"


if __name__ == "__main__":
    from utils.logger import setup_logging

    setup_logging()

    logger.info("Testing ArmController (simulation)")
    cfg = load_config("config/default.yaml")

    with ArmController(config=cfg, simulate=True) as arm:
        logger.info(f"{arm}")

        arm.home(speed=60, blocking=True)
        time.sleep(0.5)

        arm.shoulder_horizontal(speed=60)
        time.sleep(0.5)

        arm.elbow_right(45, speed=60)
        time.sleep(0.5)

        arm.elbow_full_right(speed=60)
        time.sleep(0.5)

        arm.close_gripper(speed=80)
        time.sleep(0.5)

        arm.open_gripper(speed=80)
        time.sleep(0.5)

        logger.info("Simulation test complete")