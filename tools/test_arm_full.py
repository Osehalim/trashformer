#!/usr/bin/env python3
"""
tools/test_arm_full.py — Full arm functional test (hardware)

What it does:
1) Joint-by-joint sanity test (shoulder / elbow / gripper)
2) Pose-based sequence test (ready -> pickup -> grip -> lift -> release)

Safety:
- Keep the arm clear.
- Prefer robot on blocks / arm not near chassis.
- External 5–6V servo power supply (NOT Pi 5V).
- Common ground with Pi.
"""

from __future__ import annotations

import time

from utils.logger import setup_logging, get_logger
from utils.config_loader import load_config
from arm.arm_controller import ArmController

logger = get_logger(__name__)


def pause(msg: str, sec: float = 0.8) -> None:
    logger.info(msg)
    time.sleep(sec)


def main() -> int:
    setup_logging()
    cfg = load_config("config/default.yaml")

    # simulate=False => real PCA9685 on I2C
    with ArmController(config=cfg, simulate=False) as arm:
        logger.info("=== ARM FULL TEST START ===")

        # 1) Safe start
        pause("Going to home...")
        arm.home(speed=60, blocking=True)

        # 2) Shoulder check (keep it moderate first)
        pause("Shoulder to ~60° (clearance check)")
        arm.shoulder_down(angle=0, speed=60)  # should be safe down
        pause("Shoulder to 60°")
        arm.shoulder_up(angle=60, speed=60)
        pause("Shoulder to 90° (horizontal)")
        arm.shoulder_horizontal(speed=60)

        # 3) Elbow check (0 forward -> 90 right)
        pause("Elbow to forward (0°)")
        arm.elbow_center(speed=60)
        pause("Elbow to right (45°)")
        arm.elbow_right(angle=45, speed=60)
        pause("Elbow to max right (90°)")
        arm.elbow_right(angle=90, speed=60)
        pause("Elbow back to forward (0°)")
        arm.elbow_center(speed=60)

        # 4) Gripper check
        pause("Gripper open")
        arm.open_gripper(speed=80)
        pause("Gripper close (90°)")
        arm.close_gripper(speed=80)
        pause("Gripper open")
        arm.open_gripper(speed=80)

        # 5) Simple pickup-style cycle (pose-driven if you have them)
        # If your poses.yaml includes these names, great. If not, it’ll fallback to direct angles below.
        pause("=== Pickup-style test cycle ===", 0.5)

        if "ready" in arm.poses and "approach_trash" in arm.poses and "grab_trash" in arm.poses and "lift_trash" in arm.poses:
            pause("Pose: ready")
            arm.go_to_pose("ready", speed=70, blocking=True)

            pause("Pose: approach_trash")
            arm.go_to_pose("approach_trash", speed=60, blocking=True)

            pause("Pose: grab_trash (close gripper)")
            arm.go_to_pose("grab_trash", speed=80, blocking=True)

            pause("Pose: lift_trash")
            arm.go_to_pose("lift_trash", speed=60, blocking=True)

            pause("Pose: release_trash (open gripper)")
            if "release_trash" in arm.poses:
                arm.go_to_pose("release_trash", speed=80, blocking=True)
            else:
                arm.open_gripper(speed=80)

            pause("Pose: home")
            arm.home(speed=70, blocking=True)
        else:
            # Fallback: direct angles
            pause("Fallback: direct-angle pickup cycle")
            # ready
            arm.move_to_angles({"shoulder": 90, "elbow": 0, "gripper": 0}, speed=70, blocking=True)
            # approach
            arm.move_to_angles({"shoulder": 40, "elbow": 0, "gripper": 0}, speed=60, blocking=True)
            # grip
            arm.move_to_angles({"gripper": 90}, speed=80, blocking=True)
            # lift
            arm.move_to_angles({"shoulder": 110}, speed=60, blocking=True)
            # release
            arm.move_to_angles({"gripper": 0}, speed=80, blocking=True)
            # home
            arm.home(speed=70, blocking=True)

        logger.info("✅ ARM FULL TEST COMPLETE")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())