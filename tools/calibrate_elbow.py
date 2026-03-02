#!/usr/bin/env python3
"""
tools/calibrate_elbow_center.py - Find elbow servo's TRUE center

This finds the pulse width where the elbow is physically IN LINE with the arm.
Then we'll adjust the config so 0° maps to this true center.
"""

from __future__ import annotations

import time
from utils.logger import setup_logging, get_logger
from arm.pca9685_driver import PCA9685

logger = get_logger(__name__)


def find_true_center() -> int:
    """
    Find the pulse width where elbow is physically centered (in line with arm).
    
    Returns: center pulse width in microseconds
    """
    print("\n" + "=" * 60)
    print("FINDING ELBOW TRUE CENTER")
    print("=" * 60)
    print()
    print("We'll test different pulse widths to find where the elbow")
    print("is physically IN LINE with the rest of the arm (straight).")
    print()
    
    pwm = PCA9685(i2c_bus=1, address=0x40, frequency=50, simulate=False)
    elbow_channel = 1
    
    # Start with typical servo center
    print("Testing common servo center values...")
    print()
    
    test_pulses = [1500, 1400, 1600, 1300, 1700, 1200, 1800, 1450, 1550]
    
    for pulse in test_pulses:
        print(f"\n>>> Testing {pulse}μs...")
        pwm.set_pulse_width(elbow_channel, pulse)
        time.sleep(2)
        
        response = input(f"    Is elbow IN LINE with arm (straight)? (y/n/skip): ").lower()
        
        if response == 'y':
            print(f"\n✓ TRUE CENTER found: {pulse}μs")
            pwm.close()
            return pulse
        elif response == 'skip':
            break
    
    # Manual entry
    print("\nLet's find it manually...")
    print("I'll move the servo slowly. Tell me when it's centered.")
    print()
    
    current_pulse = 1500
    
    while True:
        print(f"\nCurrent pulse: {current_pulse}μs")
        pwm.set_pulse_width(elbow_channel, current_pulse)
        time.sleep(1)
        
        print()
        print("Commands:")
        print("  + : Increase pulse (+10μs)")
        print("  - : Decrease pulse (-10μs)")
        print("  ++ : Increase pulse (+50μs)")
        print("  -- : Decrease pulse (-50μs)")
        print("  ok : This is the center!")
        print()
        
        cmd = input("Enter command: ").lower().strip()
        
        if cmd == '+':
            current_pulse += 10
        elif cmd == '-':
            current_pulse -= 10
        elif cmd == '++':
            current_pulse += 50
        elif cmd == '--':
            current_pulse -= 50
        elif cmd == 'ok':
            print(f"\n✓ TRUE CENTER found: {current_pulse}μs")
            pwm.close()
            return current_pulse
        else:
            print("Invalid command. Try +, -, ++, --, or ok")
        
        # Clamp to safe range
        current_pulse = max(500, min(2500, current_pulse))


def find_right_90_degrees(center_pulse: int) -> int:
    """
    Find the pulse width for 90° to the right from center.
    
    Returns: right 90° pulse width
    """
    print("\n" + "=" * 60)
    print("FINDING 90° RIGHT POSITION")
    print("=" * 60)
    print()
    print("Now we need to find the pulse where elbow is turned")
    print("90° to the RIGHT from center.")
    print()
    
    pwm = PCA9685(i2c_bus=1, address=0x40, frequency=50, simulate=False)
    elbow_channel = 1
    
    # First, go to center
    print(f"Going to center ({center_pulse}μs)...")
    pwm.set_pulse_width(elbow_channel, center_pulse)
    time.sleep(2)
    
    print("\nNow testing positions to the RIGHT of center...")
    print()
    
    # Try pulses ABOVE center (usually right)
    test_pulses = [
        center_pulse + 200,
        center_pulse + 400,
        center_pulse + 600,
        center_pulse + 800,
        center_pulse + 1000,
    ]
    
    for pulse in test_pulses:
        if pulse > 2500:
            continue
            
        print(f"\n>>> Testing {pulse}μs...")
        pwm.set_pulse_width(elbow_channel, pulse)
        time.sleep(2)
        
        response = input(f"    Is elbow turned ~90° RIGHT? (y/n/skip): ").lower()
        
        if response == 'y':
            print(f"\n✓ 90° RIGHT found: {pulse}μs")
            pwm.close()
            return pulse
        elif response == 'skip':
            break
    
    # Manual adjustment
    print("\nLet's find 90° right manually...")
    print()
    
    current_pulse = center_pulse + 400  # Start a bit right of center
    
    while True:
        print(f"\nCurrent pulse: {current_pulse}μs")
        pwm.set_pulse_width(elbow_channel, current_pulse)
        time.sleep(1)
        
        print()
        print("Commands:")
        print("  + : Turn more right (+10μs)")
        print("  - : Turn less right (-10μs)")
        print("  ++ : Turn more right (+50μs)")
        print("  -- : Turn less right (-50μs)")
        print("  ok : This is 90° right!")
        print()
        
        cmd = input("Enter command: ").lower().strip()
        
        if cmd == '+':
            current_pulse += 10
        elif cmd == '-':
            current_pulse -= 10
        elif cmd == '++':
            current_pulse += 50
        elif cmd == '--':
            current_pulse -= 50
        elif cmd == 'ok':
            print(f"\n✓ 90° RIGHT found: {current_pulse}μs")
            pwm.close()
            return current_pulse
        else:
            print("Invalid command")
        
        current_pulse = max(500, min(2500, current_pulse))


def main() -> int:
    setup_logging()
    
    print("=" * 60)
    print("ELBOW SERVO CENTER CALIBRATION")
    print("=" * 60)
    print()
    print("This will find:")
    print("  1. TRUE CENTER pulse (elbow in line with arm)")
    print("  2. 90° RIGHT pulse (elbow turned right)")
    print()
    print("Then we'll calculate the correct config values.")
    print()
    
    input("Press Enter to start...")
    
    # Step 1: Find true center
    center_pulse = find_true_center()
    
    # Step 2: Find 90° right
    right_90_pulse = find_right_90_degrees(center_pulse)
    
    # Calculate configuration
    print("\n" + "=" * 60)
    print("CALIBRATION COMPLETE!")
    print("=" * 60)
    print()
    print(f"True Center: {center_pulse}μs (0° - in line with arm)")
    print(f"90° Right:   {right_90_pulse}μs (90° - turned right)")
    print()
    
    # Calculate the range
    range_width = right_90_pulse - center_pulse
    
    print("=" * 60)
    print("UPDATE config/default.yaml:")
    print("=" * 60)
    print()
    print("arm:")
    print("  angle_limits:")
    print("    elbow:")
    print("      min: 0")
    print("      max: 90")
    print("      home: 0")
    print()
    print("  pwm_limits:")
    print(f"    min_pulse: {center_pulse}   # ← TRUE CENTER (was 600)")
    print(f"    max_pulse: {right_90_pulse}   # ← 90° RIGHT (was 2400)")
    print()
    print("=" * 60)
    print()
    print("EXPLANATION:")
    print(f"  0° (center) → {center_pulse}μs (elbow in line)")
    print(f"  90° (right) → {right_90_pulse}μs (elbow turned right)")
    print()
    print("After updating config, test with:")
    print("  python3 tools/test_elbow_simple.py")
    print()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())