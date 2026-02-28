#!/usr/bin/env python3
"""
tools/test_arm_full.py — Full arm functional test (hardware)

Test Sequence:
1) Full pickup and drop cycle (step by step)
2) Shoulder full range test (0° to 180° and back)
3) Elbow full range test (0° to 90° and back)

Safety:
- Keep the arm clear.
- External 5V servo power supply (NOT Pi 5V).
- Common ground with Pi.
"""

from __future__ import annotations

import time
from utils.logger import setup_logging, get_logger
from utils.config_loader import load_config
from arm.arm_controller import ArmController

logger = get_logger(__name__)


def wait(sec: float = 1.5) -> None:
    """Wait with visual feedback."""
    time.sleep(sec)


def main() -> int:
    setup_logging()
    cfg = load_config("config/default.yaml")

    # Timing
    DELAY = 2.0  # Pause between movements
    SPEED = 50   # Movement speed (degrees/sec)

    # simulate=False => real PCA9685 on I2C
    # Change to simulate=True to test without hardware
    with ArmController(config=cfg, simulate=False) as arm:
        logger.info("=" * 60)
        logger.info("ARM FULL TEST START")
        logger.info("=" * 60)
        logger.info("")

        # Print servo channels for debugging
        logger.info("Servo Channel Mapping:")
        for name, servo in arm.servos.items():
            logger.info(f"  {name}: Channel {servo.channel}")
        logger.info("")

        # ================================================================
        # TEST 1: FULL PICKUP AND DROP CYCLE
        # ================================================================
        logger.info("=" * 60)
        logger.info("TEST 1: FULL PICKUP AND DROP CYCLE")
        logger.info("=" * 60)
        logger.info("")

        # Step 1: Start at home position
        logger.info("Step 1: Going to HOME position")
        logger.info("  - Shoulder: 0° (down)")
        logger.info("  - Elbow: 0° (center)")
        logger.info("  - Gripper: 0° (open)")
        arm.home(speed=SPEED, blocking=True)
        wait(DELAY)

        # Step 2: Open gripper (ensure it's open)
        logger.info("Step 2: Opening gripper to prepare for pickup")
        logger.info("  - Gripper: 0° (open)")
        arm.open_gripper(speed=SPEED)
        wait(DELAY)

        # Step 3: Close gripper to grab trash
        logger.info("Step 3: Closing gripper to GRAB trash")
        logger.info("  - Gripper: 90° (closed)")
        arm.close_gripper(speed=SPEED)
        wait(DELAY)

        # Step 4: Lift shoulder to horizontal (90°)
        logger.info("Step 4: Lifting shoulder to HORIZONTAL")
        logger.info("  - Shoulder: 0° → 90° (horizontal)")
        arm.shoulder_horizontal(speed=SPEED)
        wait(DELAY)

        # Step 5: Turn elbow right to drop position (90°)
        logger.info("Step 5: Turning elbow RIGHT to drop position")
        logger.info("  - Elbow: 0° → 90° (fully right)")
        arm.elbow_right(90, speed=SPEED)
        wait(DELAY)

        # Step 6: Open gripper to drop trash
        logger.info("Step 6: Opening gripper to DROP trash")
        logger.info("  - Gripper: 90° → 0° (open)")
        arm.open_gripper(speed=SPEED)
        wait(DELAY)

        # Step 7: Close gripper (ready for next cycle)
        logger.info("Step 7: Closing gripper")
        logger.info("  - Gripper: 0° → 90° (closed)")
        arm.close_gripper(speed=SPEED)
        wait(DELAY)

        # Step 8: Return elbow to center
        logger.info("Step 8: Returning elbow to CENTER")
        logger.info("  - Elbow: 90° → 0° (center)")
        arm.elbow_center(speed=SPEED)
        wait(DELAY)

        # Step 9: Lower shoulder back to home
        logger.info("Step 9: Lowering shoulder back to HOME")
        logger.info("  - Shoulder: 90° → 0° (down)")
        arm.shoulder_down(0, speed=SPEED)
        wait(DELAY)

        # Step 10: Open gripper to complete cycle
        logger.info("Step 10: Opening gripper to complete cycle")
        logger.info("  - Gripper: 90° → 0° (open)")
        arm.open_gripper(speed=SPEED)
        wait(DELAY)

        logger.info("")
        logger.info("✅ TEST 1 COMPLETE: Full pickup cycle finished!")
        logger.info("")
        wait(2)

        # ================================================================
        # TEST 2: SHOULDER FULL RANGE TEST
        # ================================================================
        logger.info("=" * 60)
        logger.info("TEST 2: SHOULDER FULL RANGE TEST")
        logger.info("=" * 60)
        logger.info("")

        # Ensure we start from home
        logger.info("Starting from HOME position")
        arm.home(speed=SPEED, blocking=True)
        wait(DELAY)

        # Shoulder up to full 180°
        logger.info("Moving shoulder UP to 180° (fully up)")
        logger.info("  - Shoulder: 0° → 180°")
        arm.shoulder_up(180, speed=SPEED)
        wait(DELAY)

        # Shoulder back down to 0°
        logger.info("Moving shoulder DOWN to 0° (home)")
        logger.info("  - Shoulder: 180° → 0°")
        arm.shoulder_down(0, speed=SPEED)
        wait(DELAY)

        logger.info("")
        logger.info("✅ TEST 2 COMPLETE: Shoulder range test finished!")
        logger.info("")
        wait(2)

        # ================================================================
        # TEST 3: ELBOW FULL RANGE TEST
        # ================================================================
        logger.info("=" * 60)
        logger.info("TEST 3: ELBOW FULL RANGE TEST")
        logger.info("=" * 60)
        logger.info("")

        # Lift shoulder to horizontal for safety during elbow test
        logger.info("Lifting shoulder to HORIZONTAL for elbow test")
        logger.info("  - Shoulder: 0° → 90°")
        arm.shoulder_horizontal(speed=SPEED)
        wait(DELAY)

        # Elbow to center (should already be there)
        logger.info("Ensuring elbow is at CENTER")
        logger.info("  - Elbow: 0° (center)")
        arm.elbow_center(speed=SPEED)
        wait(DELAY)

        # Elbow right to 90°
        logger.info("Moving elbow RIGHT to 90° (fully right)")
        logger.info("  - Elbow: 0° → 90°")
        arm.elbow_right(90, speed=SPEED)
        wait(DELAY)

        # Elbow back to center
        logger.info("Moving elbow back to CENTER")
        logger.info("  - Elbow: 90° → 0°")
        arm.elbow_center(speed=SPEED)
        wait(DELAY)

        logger.info("")
        logger.info("✅ TEST 3 COMPLETE: Elbow range test finished!")
        logger.info("")
        wait(2)

        # ================================================================
        # FINAL: RETURN TO HOME
        # ================================================================
        logger.info("=" * 60)
        logger.info("RETURNING TO HOME POSITION")
        logger.info("=" * 60)
        logger.info("")

        arm.home(speed=SPEED, blocking=True)
        wait(DELAY)

        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ ALL TESTS COMPLETE!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Test Summary:")
        logger.info("  ✅ Test 1: Full pickup and drop cycle")
        logger.info("  ✅ Test 2: Shoulder full range (0° to 180°)")
        logger.info("  ✅ Test 3: Elbow full range (0° to 90°)")
        logger.info("")
        logger.info("Arm is now at HOME position (safe)")
        logger.info("")

        return 0


if __name__ == "__main__":
    raise SystemExit(main())