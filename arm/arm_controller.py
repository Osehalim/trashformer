"""
Arm controller for a 3-servo arm via PCA9685 (Pi -> I2C -> PCA9685).

Semantics (per your default.yaml):
- Shoulder: 0° down, 90° horizontal, 180° up (POSITION servo)
- Elbow: 0° center/straight, rotates RIGHT to 90° (CONTINUOUS servo - timed movement)
- Gripper: 0° open, 90° closed (POSITION servo)

IMPORTANT:
- arm.servo_continuous.py no longer exists.
- We now import Servo from arm.servo (which supports BOTH position + continuous).
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Optional, List, Tuple

import yaml

from utils.logger import get_logger
from utils.config_loader import load_config, ConfigLoader
from arm.pca9685_driver import PCA9685
from arm.servo import Servo  # <-- updated: continuous-capable Servo lives here now

logger = get_logger(__name__)


class ArmController:
    def __init__(self, config: Optional[ConfigLoader] = None, simulate: bool = False):
        if config is None:
            config = load_config()  # loads config/default.yaml by default

        self.config = config
        self.simulate = bool(simulate)

        # PCA9685 settings from default.yaml
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
        # In your config this key is called smooth_steps, but Servo expects smooth_hz.
        smooth_hz = float(self.config.get("arm.movement.smooth_steps", 10))

        # PWM limits (global defaults)
        min_pulse = int(self.config.get("arm.pwm_limits.min_pulse", 500))
        max_pulse = int(self.config.get("arm.pwm_limits.max_pulse", 2500))

        # Channels + limits
        arm_section = self.config.get_section("arm")
        channels = arm_section.get("servo_channels", {})
        limits = arm_section.get("angle_limits", {})

        # Continuous servo settings (for elbow)
        continuous_config = arm_section.get("continuous_servo", {})

        # Create servos
        self.servos: Dict[str, Servo] = {}

        # -----------------------
        # Shoulder (POSITION servo)
        # -----------------------
        shoulder = limits.get("shoulder", {})
        self.servos["shoulder"] = Servo(
            pwm_controller=self.pwm,
            channel=int(channels.get("shoulder", 0)),
            name="shoulder",
            min_angle=float(shoulder.get("min", 0)),
            max_angle=float(shoulder.get("max", 180)),
            min_pulse=min_pulse,
            max_pulse=max_pulse,
            home_angle=float(shoulder.get("home", 0)),
            neutral_angle=float(shoulder.get("home", 0)),
            smooth_hz=smooth_hz,
            continuous=False,
        )

        # -----------------------
        # Elbow (CONTINUOUS servo)
        # -----------------------
        elbow = limits.get("elbow", {})
        self.servos["elbow"] = Servo(
            pwm_controller=self.pwm,
            channel=int(channels.get("elbow", 1)),
            name="elbow",
            min_angle=float(elbow.get("min", 0)),
            max_angle=float(elbow.get("max", 90)),
            min_pulse=min_pulse,
            max_pulse=max_pulse,
            home_angle=float(elbow.get("home", 0)),
            neutral_angle=float(elbow.get("home", 0)),
            smooth_hz=smooth_hz,
            continuous=True,
            stop_pulse=int(continuous_config.get("stop_pulse", 1500)),
            speed_pulse_range=int(continuous_config.get("speed_pulse_range", 100)),
            degrees_per_second=float(continuous_config.get("degrees_per_second", 120.0)),
            min_move_deg=float(continuous_config.get("min_move_deg", 1.0)),
        )

        # -----------------------
        # Gripper (POSITION servo)
        # -----------------------
        gripper = limits.get("gripper", {})
        self.servos["gripper"] = Servo(
            pwm_controller=self.pwm,
            channel=int(channels.get("gripper", 2)),
            name="gripper",
            min_angle=float(gripper.get("min", 0)),
            max_angle=float(gripper.get("max", 90)),
            min_pulse=min_pulse,
            max_pulse=max_pulse,
            home_angle=float(gripper.get("home", 0)),
            neutral_angle=float(gripper.get("home", 0)),
            smooth_hz=smooth_hz,
            continuous=False,
        )

        # Poses
        self.poses: Dict[str, Dict[str, float]] = {}
        self._load_poses()

        self.current_pose_name: Optional[str] = None
        self.is_enabled: bool = True

        logger.info(f"ArmController ready: servos={list(self.servos.keys())}, poses={len(self.poses)}")

    # ------------------------------------------------------------
    # Poses
    # ------------------------------------------------------------
    def _load_poses(self) -> None:
        """Load poses from arm/poses.yaml relative to this file."""
        poses_file = Path(__file__).with_name("poses.yaml")
        if not poses_file.exists():
            logger.warning(f"Poses file not found: {poses_file}")
            return

        try:
            with poses_file.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
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

    # ------------------------------------------------------------
    # Basic helpers
    # ------------------------------------------------------------
    def get_servo(self, name: str) -> Optional[Servo]:
        return self.servos.get(name)

    def get_current_angles(self) -> Dict[str, Optional[float]]:
        return {name: servo.get_angle() for name, servo in self.servos.items()}

    def set_angles(self, angles: Dict[str, float], validate: bool = True) -> bool:
        """Immediate set (no smoothing for position; continuous will still time-move)."""
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
            if not servo.set_angle(float(angle), validate=validate):
                ok = False
        return ok

    # ------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------
    def move_to_angles(self, angles: Dict[str, float], speed: Optional[float] = None, blocking: bool = True) -> bool:
        """
        Move multiple servos.

        POSITION servos:
          - We try to synchronize timing using a simple max_time approach.

        CONTINUOUS servos:
          - Servo.move_to() is inherently blocking because it sleeps to time the move.
          - So for continuous servos, we move them sequentially here to keep behavior predictable.

        In practice, your test scripts mostly move one joint at a time, so this is fine.
        """
        if not self.is_enabled:
            logger.warning("Arm is disabled; ignoring move_to_angles")
            return False

        speed_val = float(speed) if speed is not None else self.default_speed
        speed_val = max(1.0, speed_val)

        # Split moves into position vs continuous
        pos_moves: List[Tuple[Servo, float, float]] = []
        cont_moves: List[Tuple[Servo, float]] = []

        for name, target in angles.items():
            servo = self.servos.get(name)
            if servo is None:
                logger.warning(f"Unknown servo: {name}")
                continue

            target_f = float(target)

            if servo.continuous:
                cont_moves.append((servo, target_f))
            else:
                current = servo.get_angle()
                if current is None:
                    servo.set_angle(target_f)
                    continue
                delta = abs(target_f - float(current))
                pos_moves.append((servo, target_f, delta))

        ok = True

        # 1) Move POSITION servos synchronized
        if pos_moves:
            max_time = 0.0
            for _servo, _target, delta in pos_moves:
                t = delta / speed_val if speed_val > 0 else 0.0
                max_time = max(max_time, t)

            if max_time <= 0.0:
                for servo, target, _delta in pos_moves:
                    if not servo.set_angle(target):
                        ok = False
            else:
                for servo, target, delta in pos_moves:
                    servo_speed = (delta / max_time) if max_time > 0 else speed_val
                    servo_speed = max(1.0, servo_speed)
                    if not servo.move_to(target, speed=servo_speed, blocking=False):
                        ok = False

                if blocking:
                    time.sleep(max_time)

        # 2) Move CONTINUOUS servos sequentially (predictable)
        # speed_val is treated as a "speed scaling factor/percent" by your Servo implementation.
        for servo, target in cont_moves:
            if not servo.move_to(target, speed=speed_val, blocking=True):
                ok = False

        return ok

    # ------------------------------------------------------------
    # Pose control
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # Convenience controls
    # ------------------------------------------------------------
    def shoulder_up(self, angle: float = 180, speed: Optional[float] = None) -> bool:
        return self.servos["shoulder"].move_to(angle, speed=speed)

    def shoulder_down(self, angle: float = 0, speed: Optional[float] = None) -> bool:
        return self.servos["shoulder"].move_to(angle, speed=speed)

    def shoulder_horizontal(self, speed: Optional[float] = None) -> bool:
        # Your semantics say 90 is horizontal
        return self.servos["shoulder"].move_to(90, speed=speed)

    def elbow_center(self, speed: Optional[float] = None) -> bool:
        return self.servos["elbow"].move_to(0, speed=speed)

    def elbow_right(self, angle: float = 90, speed: Optional[float] = None) -> bool:
        return self.servos["elbow"].move_to(angle, speed=speed)

    def elbow_full_right(self, speed: Optional[float] = None) -> bool:
        return self.servos["elbow"].move_to(90, speed=speed)

    def open_gripper(self, speed: Optional[float] = None) -> bool:
        return self.servos["gripper"].move_to(0, speed=speed)

    def close_gripper(self, speed: Optional[float] = None) -> bool:
        return self.servos["gripper"].move_to(90, speed=speed)

    def set_gripper(self, angle: float, speed: Optional[float] = None) -> bool:
        return self.servos["gripper"].move_to(angle, speed=speed)

    # ------------------------------------------------------------
    # Utility / sequences
    # ------------------------------------------------------------
    def list_poses(self) -> List[str]:
        return sorted(self.poses.keys())

    def execute_sequence(self, sequence: List[Tuple], pause_between: float = 0.5) -> bool:
        logger.info(f"Executing sequence of {len(sequence)} poses")
        for i, step in enumerate(sequence):
            pose_name = step[0]
            speed = step[1] if len(step) >= 2 else None
            pause = step[2] if len(step) >= 3 else pause_between

            logger.info(f"Step {i + 1}/{len(sequence)}: {pose_name}")
            if not self.go_to_pose(pose_name, speed=speed, blocking=True):
                logger.error(f"Sequence failed at step {i + 1} ({pose_name})")
                return False
            time.sleep(pause)

        logger.info("Sequence complete")
        return True

    # ------------------------------------------------------------
    # Safety / lifecycle
    # ------------------------------------------------------------
    def emergency_stop(self) -> None:
        logger.critical("EMERGENCY STOP: disabling all servos NOW")
        for servo in self.servos.values():
            if servo.continuous:
                servo.stop()
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
        logger.info("Closing ArmController")
        try:
            for servo in self.servos.values():
                if servo.continuous:
                    servo.stop()
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

        arm.home()
        time.sleep(0.5)

        arm.shoulder_horizontal()
        time.sleep(0.5)

        arm.elbow_right(90)
        time.sleep(0.5)

        arm.close_gripper()
        time.sleep(0.5)

        arm.open_gripper()
        time.sleep(0.5)

        logger.info("Simulation test complete")