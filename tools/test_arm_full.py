#!/usr/bin/env python3
"""
tools/test_arm_full.py — Single trash pickup simulation (hardware)

UPDATES:
- Tests shoulder up to 360° to check if Savox SC-1268SG can handle arm weight
- Fixes elbow starting position to match physical reality
- Clearer logging at each step

What this does (ONE cycle):
1) Set elbow starting position to match physical reality (CRITICAL FIX)
2) Go to hanging pose (shoulder 90°, elbow center, gripper open)
3) TEST: Lift shoulder to 360° to test servo strength
4) Lower to horizontal (180°)
5) Open gripper (hold 1s)
6) Close gripper (grab)
7) Rotate elbow right 90° to drop position
8) Open gripper to drop (hold 1s)
9) Close gripper
10) Return elbow to center (should match original position)
11) Lower shoulder back to hanging (90°)
12) Open gripper (ready)

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


def wait(sec: float) -> None:
    time.sleep(sec)


def main() -> int:
    setup_logging()
    cfg = load_config("config/default.yaml")

    # -----------------------------
    # CONFIGURATION
    # -----------------------------
    SHOULDER_HANGING = 90.0        # Regular hanging position
    SHOULDER_HORIZONTAL = 180.0    # Horizontal
    SHOULDER_MAX_TEST = 360.0      # Test if servo can lift to full rotation
    
    ELBOW_CENTER = 0.0             # Center/straight (in line with arm)
    ELBOW_RIGHT = 90.0             # Turned right
    
    GRIPPER_OPEN = 0.0
    GRIPPER_CLOSED = 90.0
    
    SPEED = 50.0
    PAUSE = 2.0
    HOLD_OPEN_SEC = 1.5

    with ArmController(config=cfg, simulate=False) as arm:
        logger.info("=" * 60)
        logger.info("FULL ARM TEST - WITH 360° SHOULDER TEST")
        logger.info("=" * 60)
        logger.info("")

        # Print servo info
        logger.info("Servo Configuration:")
        for name, servo in arm.servos.items():
            mode = "CONTINUOUS" if servo.continuous else "POSITION"
            logger.info(f"  {name}: Ch{servo.channel}, {mode}")
        logger.info("")

        # ================================================================
        # CRITICAL FIX: Set elbow starting position to match reality
        # ================================================================
        elbow = arm.servos["elbow"]
        if elbow.continuous:
            logger.info("=" * 60)
            logger.info("⚠️  IMPORTANT: ELBOW STARTING POSITION")
            logger.info("=" * 60)
            logger.info("")
            logger.info("The elbow is a continuous servo with NO position feedback.")
            logger.info("We need to set the code's position to match physical reality.")
            logger.info("")
            logger.info("BEFORE continuing:")
            logger.info("  1. Manually position the elbow STRAIGHT")
            logger.info("     (in line with the rest of the arm)")
            logger.info("  2. This is the '0° center' position")
            logger.info("")
            
            input("Position elbow STRAIGHT, then press Enter...")
            
            # Set estimated position to match physical reality
            logger.info("")
            logger.info("Setting elbow code position to match reality...")
            elbow._estimated_position = ELBOW_CENTER
            elbow.pwm.set_pulse_width(elbow.channel, elbow.stop_pulse)
            
            logger.info(f"✓ Physical position: Straight (in line with arm)")
            logger.info(f"✓ Code position: {ELBOW_CENTER}° (center)")
            logger.info(f"✓ Stop pulse: {elbow.stop_pulse}μs")
            logger.info(f"✓ Speed: {elbow.degrees_per_second}°/s")
            logger.info("")
            logger.info("These now match! Elbow is ready.")
            logger.info("=" * 60)
            logger.info("")
            time.sleep(2)

        # ------------------------------------------------
        # Step 1: Go to hanging pose
        # ------------------------------------------------
        logger.info("Step 1: Going to HANGING pose (starting position)")
        logger.info(f"  Shoulder: {SHOULDER_HANGING}° (hanging)")
        logger.info(f"  Elbow: {ELBOW_CENTER}° (center - already there)")
        logger.info(f"  Gripper: {GRIPPER_OPEN}° (open)")

        arm.move_to_angles(
            {
                "shoulder": SHOULDER_HANGING,
                "elbow": ELBOW_CENTER,
                "gripper": GRIPPER_OPEN,
            },
            speed=SPEED,
            blocking=True,
        )
        wait(PAUSE)

        # ------------------------------------------------
        # Step 2: SHOULDER WEIGHT TEST - 360°
        # ------------------------------------------------
        logger.info("")
        logger.info("=" * 60)
        logger.info("Step 2: SHOULDER WEIGHT TEST - Lifting to 360°")
        logger.info("=" * 60)
        logger.info(f"  Testing if Savox SC-1268SG can lift to {SHOULDER_MAX_TEST}°")
        logger.info(f"  Shoulder: {SHOULDER_HANGING}° → {SHOULDER_MAX_TEST}°")
        logger.info("  This tests if servo is strong enough for full arm weight")
        logger.info("")

        arm.shoulder_up(SHOULDER_MAX_TEST, speed=SPEED)
        wait(PAUSE)

        logger.info("")
        response = input(f"Did shoulder reach {SHOULDER_MAX_TEST}°? (y/n): ").lower()
        if response == 'y':
            logger.info("✓ SUCCESS: Servo is strong enough at full extension!")
        else:
            logger.info("⚠️  ISSUE: Servo struggled - arm may be too heavy at this angle")
            logger.info("   Consider: lighter arm materials or stronger servo")
        logger.info("")
        wait(1)

        # ------------------------------------------------
        # Step 3: Lower to horizontal
        # ------------------------------------------------
        logger.info("Step 3: Lowering to HORIZONTAL (180°)")
        logger.info(f"  Shoulder: {SHOULDER_MAX_TEST}° → {SHOULDER_HORIZONTAL}°")

        arm.shoulder_up(SHOULDER_HORIZONTAL, speed=SPEED)
        wait(PAUSE)

        # ------------------------------------------------
        # Step 4: Open gripper (prepare to grab)
        # ------------------------------------------------
        logger.info("")
        logger.info("Step 4: Opening gripper (prepare to pickup)")
        logger.info(f"  Gripper: {GRIPPER_OPEN}°")

        arm.set_gripper(GRIPPER_OPEN, speed=SPEED)
        wait(HOLD_OPEN_SEC)

        # ------------------------------------------------
        # Step 5: Close gripper (grab)
        # ------------------------------------------------
        logger.info("")
        logger.info("Step 5: Closing gripper (GRAB trash)")
        logger.info(f"  Gripper: {GRIPPER_CLOSED}°")

        arm.set_gripper(GRIPPER_CLOSED, speed=SPEED)
        wait(PAUSE)

        # ------------------------------------------------
        # Step 6: Rotate elbow right (continuous servo)
        # ------------------------------------------------
        logger.info("")
        logger.info("Step 6: Rotating elbow RIGHT to drop position")
        logger.info(f"  Elbow: {ELBOW_CENTER}° → {ELBOW_RIGHT}°")
        logger.info("  (Continuous servo - using timed movement)")

        arm.elbow_right(ELBOW_RIGHT, speed=SPEED)
        wait(PAUSE)

        # ------------------------------------------------
        # Step 7: Open gripper (drop)
        # ------------------------------------------------
        logger.info("")
        logger.info("Step 7: Opening gripper (DROP trash)")
        logger.info(f"  Gripper: {GRIPPER_OPEN}°")

        arm.set_gripper(GRIPPER_OPEN, speed=SPEED)
        wait(HOLD_OPEN_SEC)

        # ------------------------------------------------
        # Step 8: Close gripper
        # ------------------------------------------------
        logger.info("")
        logger.info("Step 8: Closing gripper (reset)")
        logger.info(f"  Gripper: {GRIPPER_CLOSED}°")

        arm.set_gripper(GRIPPER_CLOSED, speed=SPEED)
        wait(PAUSE)

        # ------------------------------------------------
        # Step 9: Return elbow to center
        # ------------------------------------------------
        logger.info("")
        logger.info("Step 9: Returning elbow to CENTER")
        logger.info(f"  Elbow: {ELBOW_RIGHT}° → {ELBOW_CENTER}°")
        logger.info("  Should return to ORIGINAL straight position")

        arm.elbow_center(speed=SPEED)
        wait(PAUSE)

        # Check if it returned correctly
        logger.info("")
        response = input("Did elbow return to ORIGINAL straight position? (y/n): ").lower()
        if response == 'y':
            logger.info("✓ SUCCESS: Elbow calibration is correct!")
        else:
            logger.info("⚠️  ISSUE: Elbow didn't return to original position")
            logger.info("   Solution: Adjust degrees_per_second in default.yaml")
            logger.info("   - Moved too far: DECREASE degrees_per_second (try 150)")
            logger.info("   - Didn't move enough: INCREASE degrees_per_second (try 210)")
        logger.info("")
        wait(1)

        # ------------------------------------------------
        # Step 10: Lower shoulder to hanging
        # ------------------------------------------------
        logger.info("Step 10: Lowering shoulder to HANGING")
        logger.info(f"  Shoulder: {SHOULDER_HORIZONTAL}° → {SHOULDER_HANGING}°")

        arm.shoulder_down(SHOULDER_HANGING, speed=SPEED)
        wait(PAUSE)

        # ------------------------------------------------
        # Step 11: Open gripper (ready)
        # ------------------------------------------------
        logger.info("")
        logger.info("Step 11: Opening gripper (ready for next cycle)")
        logger.info(f"  Gripper: {GRIPPER_OPEN}°")

        arm.set_gripper(GRIPPER_OPEN, speed=SPEED)
        wait(PAUSE)

        # ================================================
        # FINAL SUMMARY
        # ================================================
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ FULL ARM TEST COMPLETE!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Test Summary:")
        logger.info(f"  ✓ Shoulder tested up to {SHOULDER_MAX_TEST}°")
        logger.info("  ✓ Elbow tested right/center movement")
        logger.info("  ✓ Gripper tested open/close")
        logger.info("")
        logger.info("The arm completed a full pickup/drop cycle!")
        logger.info("")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())