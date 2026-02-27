#!/usr/bin/env python3
"""
tools/test_arm_full.py — Full arm functional test (hardware)

What it does:
1) Joint-by-joint sanity test (shoulder / elbow / gripper)
   - Each joint is moved to a test position then returned to its starting position.
2) Simple pickup-style sequence test (pose-based if available, else direct angles)

Safety:
- Keep the arm clear.
- Prefer robot on blocks / arm not near chassis.
- External 5–6V servo power supply (NOT Pi 5V).
- Common ground with Pi.
"""

from __future__ import annotations

import time
from typing import Optional, Dict

from utils.logger import setup_logging, get_logger
from utils.config_loader import load_config
from arm.arm_controller import ArmController

logger = get_logger(__name__)


def wait(sec: float = 1.5) -> None:
    time.sleep(sec)


def get_angle_or(arm: ArmController, joint: str, default: float) -> float:
    angles = arm.get_current_angles()
    a = angles.get(joint)
    return float(a) if a is not None else float(default)


def move_joint_and_return(
    arm: ArmController,
    joint: str,
    target: float,
    speed: float = 60,
    delay_after: float = 1.5,
    default_start: float = 0.0,
) -> None:
    """
    Move one joint to target, wait, then return to its original angle, wait.
    Uses arm.get_current_angles() as the reference for original.
    """
    start = get_angle_or(arm, joint, default_start)
    logger.info(f"[{joint}] start={start:.1f}° -> target={target:.1f}° -> return={start:.1f}°")

    arm.move_to_angles({joint: target}, speed=speed, blocking=True)
    wait(delay_after)

    arm.move_to_angles({joint: start}, speed=speed, blocking=True)
    wait(delay_after)


def set_pose_and_wait(arm: ArmController, desc: str, pose: Dict[str, float], speed: float, delay_after: float) -> None:
    logger.info(desc)
    arm.move_to_angles(pose, speed=speed, blocking=True)
    wait(delay_after)


def try_pose(arm: ArmController, pose_name: str, speed: float, delay_after: float) -> bool:
    if pose_name not in arm.poses:
        return False
    logger.info(f"Pose: {pose_name}")
    arm.go_to_pose(pose_name, speed=speed, blocking=True)
    wait(delay_after)
    return True


def main() -> int:
    setup_logging()
    cfg = load_config("config/default.yaml")

    # Tuning knobs
    DELAY = 1.5
    SPEED_JOINT = 60
    SPEED_GRIP = 80

    # simulate=False => real PCA9685 on I2C
    with ArmController(config=cfg, simulate=False) as arm:
        logger.info("=== ARM FULL TEST START ===")

        # Print channel mapping (helps debug if only one servo moves)
        try:
            logger.info("Channel mapping (from ArmController):")
            for name, servo in arm.servos.items():
                logger.info(f"  {name}: channel {servo.channel}")
        except Exception:
            pass

        # 1) Safe start
        logger.info("Going to home...")
        arm.home(speed=60, blocking=True)
        wait(DELAY)

        # Capture a baseline pose (what we return to between tests)
        base_sh = get_angle_or(arm, "shoulder", 0.0)
        base_el = get_angle_or(arm, "elbow", 0.0)
        base_gr = get_angle_or(arm, "gripper", 0.0)
        logger.info(f"Baseline angles: shoulder={base_sh:.1f}°, elbow={base_el:.1f}°, gripper={base_gr:.1f}°")

        # ---------------------------------------------------------------------
        # 2) Joint-by-joint test (each returns to baseline)
        # ---------------------------------------------------------------------

        # Shoulder test: move up to 60°, return
        move_joint_and_return(
            arm,
            joint="shoulder",
            target=60,
            speed=SPEED_JOINT,
            delay_after=DELAY,
            default_start=base_sh,
        )

        # Shoulder test: move to 90°, return
        move_joint_and_return(
            arm,
            joint="shoulder",
            target=90,
            speed=SPEED_JOINT,
            delay_after=DELAY,
            default_start=base_sh,
        )

        # For elbow tests, first put shoulder at a safe height (reduce collision risk),
        # then restore shoulder afterward.
        logger.info("Raising shoulder to 90° for elbow clearance...")
        arm.move_to_angles({"shoulder": 90}, speed=SPEED_JOINT, blocking=True)
        wait(DELAY)

        # Elbow test: 45° right, return
        move_joint_and_return(
            arm,
            joint="elbow",
            target=45,
            speed=SPEED_JOINT,
            delay_after=DELAY,
            default_start=base_el,
        )

        # Elbow test: 90° (max right), return
        move_joint_and_return(
            arm,
            joint="elbow",
            target=90,
            speed=SPEED_JOINT,
            delay_after=DELAY,
            default_start=base_el,
        )

        # Restore shoulder to baseline after elbow tests
        logger.info("Restoring shoulder to baseline...")
        arm.move_to_angles({"shoulder": base_sh}, speed=SPEED_JOINT, blocking=True)
        wait(DELAY)

        # Gripper test: open then return
        move_joint_and_return(
            arm,
            joint="gripper",
            target=0,
            speed=SPEED_GRIP,
            delay_after=DELAY,
            default_start=base_gr,
        )

        # Gripper test: close (90) then return
        move_joint_and_return(
            arm,
            joint="gripper",
            target=90,
            speed=SPEED_GRIP,
            delay_after=DELAY,
            default_start=base_gr,
        )

        # After joint tests, go back to home to start sequence test cleanly
        logger.info("Returning to home before pickup-style sequence...")
        arm.home(speed=60, blocking=True)
        wait(DELAY)

        # ---------------------------------------------------------------------
        # 3) Pickup-style sequence test
        # ---------------------------------------------------------------------
        logger.info("=== Pickup-style test cycle ===")
        wait(0.5)

        # Prefer pose-driven if those poses exist
        poses_needed = {"ready", "approach_trash", "grab_trash", "lift_trash"}
        if poses_needed.issubset(set(arm.poses.keys())):
            try_pose(arm, "ready", speed=70, delay_after=DELAY)
            try_pose(arm, "approach_trash", speed=60, delay_after=DELAY)
            try_pose(arm, "grab_trash", speed=80, delay_after=DELAY)
            try_pose(arm, "lift_trash", speed=60, delay_after=DELAY)

            # Release
            if "release_trash" in arm.poses:
                try_pose(arm, "release_trash", speed=80, delay_after=DELAY)
            else:
                logger.info("Release: opening gripper")
                arm.open_gripper(speed=80)
                wait(DELAY)

            logger.info("Pose: home")
            arm.home(speed=70, blocking=True)
            wait(DELAY)

        else:
            # Fallback: direct angles (kept conservative)
            logger.info("Fallback: direct-angle pickup cycle")

            set_pose_and_wait(
                arm,
                desc="Ready (shoulder 90, elbow 0, gripper 0)",
                pose={"shoulder": 90, "elbow": 0, "gripper": 0},
                speed=70,
                delay_after=DELAY,
            )

            set_pose_and_wait(
                arm,
                desc="Approach (shoulder 40, elbow 0, gripper 0)",
                pose={"shoulder": 40, "elbow": 0, "gripper": 0},
                speed=60,
                delay_after=DELAY,
            )

            set_pose_and_wait(
                arm,
                desc="Grip (gripper 90)",
                pose={"gripper": 90},
                speed=80,
                delay_after=DELAY,
            )

            set_pose_and_wait(
                arm,
                desc="Lift (shoulder 110)",
                pose={"shoulder": 110},
                speed=60,
                delay_after=DELAY,
            )

            set_pose_and_wait(
                arm,
                desc="Release (gripper 0)",
                pose={"gripper": 0},
                speed=80,
                delay_after=DELAY,
            )

            logger.info("Home")
            arm.home(speed=70, blocking=True)
            wait(DELAY)

        logger.info("✅ ARM FULL TEST COMPLETE")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())