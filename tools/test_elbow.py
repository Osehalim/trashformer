#!/usr/bin/env python3
"""
tools/test_elbow_simple.py - Simple elbow position servo test

Tests:
1. Start at current position (set to 0°)
2. Move right to 90°
3. Return to center (0°)

For: Standard POSITION servo on elbow (Channel 1)
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

    print("=" * 60)
    print("ELBOW POSITION SERVO TEST")
    print("=" * 60)
    print()
    print("This test will:")
    print("  1. Set current position as 0° (center)")
    print("  2. Move elbow RIGHT to 90°")
    print("  3. Return elbow to CENTER (0°)")
    print()
    print("Make sure:")
    print("  - Elbow servo is connected to Channel 1")
    print("  - External 5V power is connected")
    print("  - Arm has room to move")
    print()
    
    input("Press Enter to start test...")

    SPEED = 50  # degrees/second
    PAUSE = 3   # seconds between movements

    with ArmController(config=cfg, simulate=False) as arm:
        
        elbow = arm.servos["elbow"]
        
        print()
        print("=" * 60)
        print("ELBOW SERVO INFO")
        print("=" * 60)
        print(f"  Name: {elbow.name}")
        print(f"  Channel: {elbow.channel}")
        print(f"  Range: {elbow.min_angle}° to {elbow.max_angle}°")
        print(f"  Home: {elbow.home_angle}°")
        print(f"  Pulse range: {elbow.min_pulse}μs to {elbow.max_pulse}μs")
        print()
        
        # ================================================================
        # Step 1: Set starting position to 0° (center)
        # ================================================================
        print("=" * 60)
        print("STEP 1: Setting current position as CENTER (0°)")
        print("=" * 60)
        print()
        print("Whatever position the elbow is at RIGHT NOW will be")
        print("considered 0° (center/straight).")
        print()
        
        # Set the current angle to 0° without moving
        elbow._current_angle = 0.0
        elbow._target_angle = 0.0
        
        print("✓ Current position set to 0° (center)")
        print()
        
        input("Press Enter to move RIGHT to 90°...")
        
        # ================================================================
        # Step 2: Move right to 90°
        # ================================================================
        print()
        print("=" * 60)
        print("STEP 2: Moving RIGHT to 90°")
        print("=" * 60)
        print()
        print(f"Moving from 0° → 90° at {SPEED}°/second")
        print()
        
        start_time = time.time()
        arm.elbow_right(90, speed=SPEED)
        elapsed = time.time() - start_time
        
        print()
        print(f"✓ Movement complete in {elapsed:.2f} seconds")
        print(f"  Expected time: {90/SPEED:.2f} seconds")
        print()
        print("Elbow should now be turned 90° to the RIGHT")
        print()
        
        time.sleep(PAUSE)
        
        response = input("Did elbow move ~90° to the right? (y/n): ").lower()
        if response == 'y':
            print("✓ Good! Movement looks correct.")
        else:
            print("⚠️  Movement may need calibration.")
            print("   Run: python3 tools/calibrate_servos.py")
        
        print()
        input("Press Enter to return to CENTER (0°)...")
        
        # ================================================================
        # Step 3: Return to center
        # ================================================================
        print()
        print("=" * 60)
        print("STEP 3: Returning to CENTER (0°)")
        print("=" * 60)
        print()
        print(f"Moving from 90° → 0° at {SPEED}°/second")
        print()
        
        start_time = time.time()
        arm.elbow_center(speed=SPEED)
        elapsed = time.time() - start_time
        
        print()
        print(f"✓ Movement complete in {elapsed:.2f} seconds")
        print(f"  Expected time: {90/SPEED:.2f} seconds")
        print()
        print("Elbow should now be back at ORIGINAL position")
        print()
        
        time.sleep(PAUSE)
        
        response = input("Did elbow return to ORIGINAL position? (y/n): ").lower()
        if response == 'y':
            print("✓ Perfect! Elbow is working correctly!")
        else:
            print("⚠️  Position mismatch detected.")
            print("   Possible causes:")
            print("   - Incorrect pulse width calibration")
            print("   - Servo not centered at startup")
            print("   Run calibration: python3 tools/calibrate_servos.py")
        
        # ================================================================
        # Summary
        # ================================================================
        print()
        print("=" * 60)
        print("✅ TEST COMPLETE")
        print("=" * 60)
        print()
        print("Test Summary:")
        print("  ✓ Set starting position to 0°")
        print("  ✓ Moved right to 90°")
        print("  ✓ Returned to center 0°")
        print()
        print("Current elbow angle: 0° (center)")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())