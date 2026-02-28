#!/usr/bin/env python3
"""
tools/test_simple_sequence.py — Simple arm test for your exact servo setup

Your Servos:
- Shoulder (Channel 0): Savox SC-1268SG - POSITION servo
- Elbow (Channel 1): ServoCity 2000 Series - CONTINUOUS/timing servo  
- Gripper (Channel 2): ServoCity Gripper Kit - POSITION servo

This test does exactly what you asked:
1. Shoulder up to horizontal
2. Elbow turns right
3. Gripper opens
4. Gripper closes
5. Elbow returns to center
6. Shoulder returns down
"""

from __future__ import annotations

import time
from utils.logger import setup_logging, get_logger
from utils.config_loader import load_config
from arm.arm_controller import ArmController

logger = get_logger(__name__)


def main() -> int:
    setup_logging()
    cfg = load_config("config/default.yaml")

    logger.info("=" * 60)
    logger.info("SIMPLE ARM SEQUENCE TEST")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Servo Setup:")
    logger.info("  Shoulder (Ch0): Savox SC-1268SG (POSITION)")
    logger.info("  Elbow (Ch1): ServoCity 2000 (CONTINUOUS/timing)")
    logger.info("  Gripper (Ch2): ServoCity Kit (POSITION)")
    logger.info("")

    with ArmController(config=cfg, simulate=False) as arm:
        
        # Print current configuration
        logger.info("Current Configuration:")
        for name, servo in arm.servos.items():
            mode = "CONTINUOUS" if servo.continuous else "POSITION"
            logger.info(f"  {name}: Channel {servo.channel}, Mode={mode}")
        logger.info("")
        
        DELAY = 3.0  # Long pauses so you can see each movement
        
        # ============================================================
        # SEQUENCE
        # ============================================================
        
        logger.info("Starting sequence...")
        logger.info("")
        
        # Step 1: Shoulder up to horizontal
        logger.info("STEP 1: Shoulder UP to HORIZONTAL (90°)")
        arm.shoulder_horizontal()
        time.sleep(DELAY)
        
        # Step 2: Elbow turn right (90°)
        logger.info("STEP 2: Elbow turning RIGHT (90°)")
        arm.elbow_right(90)
        time.sleep(DELAY)
        
        # Step 3: Gripper open
        logger.info("STEP 3: Gripper OPEN")
        arm.open_gripper()
        time.sleep(DELAY)
        
        # Step 4: Gripper close
        logger.info("STEP 4: Gripper CLOSE")
        arm.close_gripper()
        time.sleep(DELAY)
        
        # Step 5: Elbow back to center
        logger.info("STEP 5: Elbow returning to CENTER")
        arm.elbow_center()
        time.sleep(DELAY)
        
        # Step 6: Shoulder down
        logger.info("STEP 6: Shoulder DOWN to home")
        arm.shoulder_down()
        time.sleep(DELAY)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ SEQUENCE COMPLETE!")
        logger.info("=" * 60)
        
        return 0


if __name__ == "__main__":
    raise SystemExit(main())