#!/usr/bin/env python3
"""
tools/test_arm_full.py — Simple arm functional test (hardware)

Sequence:
1) Open gripper
2) Close gripper
3) Raise shoulder to 90° (arm horizontal)
4) Turn elbow to 90° (operating stroke)
5) Open gripper
6) Close gripper
7) Return elbow to 0°
8) Lower shoulder back to 0°

Safety:
- Keep the arm clear.
- Use an external 5V/6V servo power supply (NOT Pi 5V).
- Make sure Pi ground and servo power ground are common.

Shoulder logical angles:
  0°   = arm pointing straight DOWN  (home/rest, 1500µs)
  90°  = arm horizontal              (500µs or 2500µs depending on mount side)
  180° = arm pointing straight UP

Elbow logical angles:
  0°   = center / forward            (1000µs)
  100° = full operating stroke       (2000µs)
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
    SPEED = 50

    # simulate=False => real PCA9685 on I2C
    with ArmController(config=cfg, simulate=False) as arm:
        logger.info("=" * 60)
        logger.info("SIMPLE ARM TEST START")
        logger.info("=" * 60)
        logger.info("")

        logger.info("Servo Channel Mapping:")
        for name, servo in arm.servos.items():
            logger.info(
                f"  {name}: Channel {servo.channel}  "
                f"pulse=[{servo.min_pulse},{servo.max_pulse}]µs  "
                f"angle=[{servo.min_angle}°,{servo.max_angle}°]  home={servo.home_angle}°"
            )
        logger.info("")

        # Start from home
        logger.info("Step 0: Going to HOME position")
        logger.info("  - Shoulder: 0° (arm straight down)")
        logger.info("  - Elbow:    0° (center/forward)")
        logger.info("  - Gripper:  0° (open)")
        arm.home(speed=SPEED, blocking=True)
        wait(DELAY)

        # 1. Open gripper
        logger.info("Step 1: Opening gripper")
        arm.open_gripper(speed=SPEED)
        wait(DELAY)

        # 2. Close gripper
        logger.info("Step 2: Closing gripper")
        arm.close_gripper(speed=SPEED)
        wait(DELAY)

        # 3. Raise shoulder to 90° (horizontal)
        logger.info("Step 3: Raising shoulder to 90° (horizontal)")
        logger.info("  - Shoulder: 0° → 90°")
        arm.shoulder_horizontal(speed=SPEED)
        wait(DELAY)

        # 4. Turn elbow 90° (within its 0-100° operating stroke)
        logger.info("Step 4: Turning elbow to 90°")
        logger.info("  - Elbow: 0° → 90°  (1000µs → 1900µs)")
        arm.elbow_right(90, speed=SPEED)   # FIXED: was elbow_right(-90, ...) which clamped to 0°
        wait(DELAY)

        # 5. Open gripper
        logger.info("Step 5: Opening gripper")
        arm.open_gripper(speed=SPEED)
        wait(DELAY)

        # 6. Close gripper
        logger.info("Step 6: Closing gripper")
        arm.close_gripper(speed=SPEED)
        wait(DELAY)

        # 7. Return elbow to 0°
        logger.info("Step 7: Returning elbow to 0°")
        logger.info("  - Elbow: 90° → 0°")
        arm.elbow_center(speed=SPEED)
        wait(DELAY)

        # 8. Lower shoulder back to 0°
        logger.info("Step 8: Lowering shoulder back to 0°")
        logger.info("  - Shoulder: 90° → 0°")
        arm.shoulder_down(0, speed=SPEED)
        wait(DELAY)

        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ SIMPLE ARM TEST COMPLETE")
        logger.info("=" * 60)
        logger.info("")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())