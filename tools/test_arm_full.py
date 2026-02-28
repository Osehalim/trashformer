#!/usr/bin/env python3
"""
tools/test_arm_full.py — Single trash pickup simulation (hardware)

What this does (ONE cycle):
1) Go to "hanging/home" pose (shoulder hanging, elbow centered, gripper open)
2) Open gripper (hold 1s)
3) Close gripper (grab)
4) Lift shoulder to horizontal
5) Rotate elbow right to drop position
6) Open gripper to drop (hold 1s)
7) Close gripper
8) Return elbow to center
9) Lower shoulder back to hanging
10) Open gripper (ready)

NOTES:
- This assumes your ELBOW is a CONTINUOUS servo and ArmController/Servo already handle
  timed motion for elbow when you call move_to()/elbow_right()/elbow_center().

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
    # TUNE THESE NUMBERS
    # -----------------------------
    # You said: shoulder "regular hanging position" is 90 degrees
    SHOULDER_HANGING = 90.0
    # Shoulder horizontal: adjust if 180 isn't correct for your mounting
    # (If hanging is 90, horizontal is often 180, but depends on install.)
    SHOULDER_HORIZONTAL = 180.0

    # Elbow angles are "virtual degrees" for the continuous servo timing model.
    # 0 = center/in line; 90 = right
    ELBOW_CENTER = 0.0
    ELBOW_RIGHT = 90.0

    # Gripper: adjust these if your linkage binds or doesn't open enough
    GRIPPER_OPEN = 0.0
    GRIPPER_CLOSED = 90.0

    # Timing / speed
    # For position servos, ArmController treats speed as deg/sec.
    # For your continuous elbow, your Servo should interpret speed as a scaling factor/percent.
    SPEED = 50.0          # start here
    PAUSE = 1.0           # pause between steps
    HOLD_OPEN_SEC = 1.0   # how long to keep gripper open at pickup/drop

    # simulate=False => real PCA9685 on I2C
    with ArmController(config=cfg, simulate=False) as arm:
        logger.info("=" * 60)
        logger.info("SINGLE PICKUP CYCLE TEST START")
        logger.info("=" * 60)

        # Print servo channels for debugging
        logger.info("Servo Channel Mapping:")
        for name, servo in arm.servos.items():
            logger.info(f"  {name}: Channel {servo.channel}")
        logger.info("")

        # ------------------------------------------------
        # Step 1: Go to hanging/home pose
        # ------------------------------------------------
        logger.info("Step 1: Going to HANGING pose (home)")
        logger.info(f"  - Shoulder: {SHOULDER_HANGING}° (hanging)")
        logger.info(f"  - Elbow: {ELBOW_CENTER}° (center)")
        logger.info(f"  - Gripper: {GRIPPER_OPEN}° (open)")

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
        # Step 2: Open gripper (ensure open) and hold
        # ------------------------------------------------
        logger.info("Step 2: Opening gripper (prepare to pickup) + hold")
        arm.set_gripper(GRIPPER_OPEN, speed=SPEED)
        wait(HOLD_OPEN_SEC)

        # ------------------------------------------------
        # Step 3: Close gripper to grab
        # ------------------------------------------------
        logger.info("Step 3: Closing gripper (GRAB)")
        arm.set_gripper(GRIPPER_CLOSED, speed=SPEED)
        wait(PAUSE)

        # ------------------------------------------------
        # Step 4: Lift shoulder to horizontal
        # ------------------------------------------------
        logger.info("Step 4: Lifting shoulder to HORIZONTAL")
        logger.info(f"  - Shoulder: {SHOULDER_HANGING}° -> {SHOULDER_HORIZONTAL}°")
        arm.shoulder_up(SHOULDER_HORIZONTAL, speed=SPEED)
        wait(PAUSE)

        # ------------------------------------------------
        # Step 5: Rotate elbow right (continuous servo timed move)
        # ------------------------------------------------
        logger.info("Step 5: Rotating elbow RIGHT to drop position")
        logger.info(f"  - Elbow: {ELBOW_CENTER}° -> {ELBOW_RIGHT}°")
        arm.elbow_right(ELBOW_RIGHT, speed=SPEED)
        wait(PAUSE)

        # ------------------------------------------------
        # Step 6: Open gripper to drop + hold
        # ------------------------------------------------
        logger.info("Step 6: Opening gripper to DROP + hold")
        arm.set_gripper(GRIPPER_OPEN, speed=SPEED)
        wait(HOLD_OPEN_SEC)

        # ------------------------------------------------
        # Step 7: Close gripper again
        # ------------------------------------------------
        logger.info("Step 7: Closing gripper (reset)")
        arm.set_gripper(GRIPPER_CLOSED, speed=SPEED)
        wait(PAUSE)

        # ------------------------------------------------
        # Step 8: Return elbow to center
        # ------------------------------------------------
        logger.info("Step 8: Returning elbow to CENTER")
        logger.info(f"  - Elbow: {ELBOW_RIGHT}° -> {ELBOW_CENTER}°")
        arm.elbow_center(speed=SPEED)
        wait(PAUSE)

        # ------------------------------------------------
        # Step 9: Lower shoulder back to hanging
        # ------------------------------------------------
        logger.info("Step 9: Lowering shoulder back to HANGING")
        logger.info(f"  - Shoulder: {SHOULDER_HORIZONTAL}° -> {SHOULDER_HANGING}°")
        arm.shoulder_down(SHOULDER_HANGING, speed=SPEED)
        wait(PAUSE)

        # ------------------------------------------------
        # Step 10: Open gripper (ready)
        # ------------------------------------------------
        logger.info("Step 10: Opening gripper (ready)")
        arm.set_gripper(GRIPPER_OPEN, speed=SPEED)
        wait(PAUSE)

        logger.info("")
        logger.info("✅ SINGLE PICKUP CYCLE COMPLETE")
        logger.info("=" * 60)
        logger.info("")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())