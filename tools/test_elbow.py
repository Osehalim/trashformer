#!/usr/bin/env python3
"""
tools/test_elbow_only.py — Elbow-only continuous servo test

What this tests:
- Elbow center (0° virtual)
- Move RIGHT to 90°
- Pause
- Move back to CENTER
- Stop safely

This assumes:
- Elbow is configured as continuous=True
- degrees_per_second is calibrated (or close)
- stop_pulse is calibrated (true neutral)
"""

from __future__ import annotations

import time
from utils.logger import setup_logging, get_logger
from utils.config_loader import load_config
from arm.arm_controller import ArmController

logger = get_logger(__name__)


def wait(sec: float = 2.0) -> None:
    time.sleep(sec)


def main() -> int:
    setup_logging()
    cfg = load_config("config/default.yaml")

    SPEED = 50.0  # adjust if needed

    with ArmController(config=cfg, simulate=False) as arm:
        logger.info("=" * 60)
        logger.info("ELBOW ONLY TEST START")
        logger.info("=" * 60)

        # ------------------------------------------------
        # Step 1: Ensure elbow at center
        # ------------------------------------------------
        logger.info("Step 1: Moving elbow to CENTER (0°)")
        arm.elbow_center(speed=SPEED)
        wait(2.0)

        # ------------------------------------------------
        # Step 2: Move elbow RIGHT to 90°
        # ------------------------------------------------
        logger.info("Step 2: Moving elbow RIGHT to 90°")
        arm.elbow_right(90, speed=SPEED)
        wait(2.0)

        # ------------------------------------------------
        # Step 3: Return to CENTER
        # ------------------------------------------------
        logger.info("Step 3: Returning elbow to CENTER (0°)")
        arm.elbow_center(speed=SPEED)
        wait(2.0)

        logger.info("")

        # Safety: explicitly stop continuous servo
        logger.info("Stopping elbow (safety stop)")
        arm.servos["elbow"].stop()

        logger.info("")
        logger.info("✅ ELBOW TEST COMPLETE")
        logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())