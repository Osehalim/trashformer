#!/usr/bin/env python3
"""
tools/test_arm_full.py — Simple arm functional test

Sequence:
1) Open gripper
2) Close gripper
3) Raise shoulder to 90° (vertical up)
4) Turn elbow 90° left
5) Open gripper
6) Close gripper
7) Return elbow to 0° (center)
8) Lower shoulder back to 0° (horizontal)

Safety:
- Keep the arm clear.
- Use an external 5-6V servo power supply (NOT Pi 5V).
- Make sure Pi ground and servo power ground are common.
"""

from __future__ import annotations

import time
from utils.logger import setup_logging, get_logger
from utils.config_loader import load_config
from arm.arm_controller import ArmController

logger = get_logger(__name__)


def wait(sec: float = 2.0) -> None:
    """Pause between movements."""
    time.sleep(sec)


def main() -> int:
    setup_logging()
    cfg = load_config("config/default.yaml")

    DELAY = 2.0

    # simulate=False => real PCA9685 on I2C
    with ArmController(config=cfg, simulate=False) as arm:
        logger.info("=" * 60)
        logger.info("SIMPLE ARM TEST START")
        logger.info("=" * 60)
        logger.info("")

        # Start from home
        logger.info("Step 0: Going to HOME position")
        logger.info("  - Shoulder: 0° (horizontal)")
        logger.info("  - Elbow: 0° (center)")
        logger.info("  - Gripper: 0° (open)")
        arm.home()
        wait(DELAY)

        # 1. Open gripper
        logger.info("Step 1: Opening gripper")
        arm.gripper_open()
        wait(DELAY)

        # 2. Close gripper
        logger.info("Step 2: Closing gripper")
        arm.gripper_close()
        wait(DELAY)

        # 3. Raise shoulder to 90 degrees (vertical up)
        logger.info("Step 3: Raising shoulder to 90° (vertical up)")
        arm.shoulder_up()
        wait(DELAY)

        # 4. Turn elbow 90 degrees left
        logger.info("Step 4: Turning elbow 90° to the left")
        arm.elbow_left()
        wait(DELAY)

        # 5. Open gripper
        logger.info("Step 5: Opening gripper")
        arm.gripper_open()
        wait(DELAY)

        # 6. Close gripper
        logger.info("Step 6: Closing gripper")
        arm.gripper_close()
        wait(DELAY)

        # 7. Return elbow to 0 degrees (center)
        logger.info("Step 7: Returning elbow to 0° (center)")
        arm.elbow_center()
        wait(DELAY)

        # 8. Lower shoulder back to 0 degrees (horizontal)
        logger.info("Step 8: Lowering shoulder back to 0° (horizontal)")
        arm.shoulder_down()
        wait(DELAY)

        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ SIMPLE ARM TEST COMPLETE")
        logger.info("=" * 60)
        logger.info("")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())