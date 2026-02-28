#!/usr/bin/env python3
"""
tools/calibrate_servos.py - Find the actual pulse widths for your servos

This script helps you find the REAL min/max pulse widths for each servo
instead of assuming 500-2500μs works for all servos.

HOW TO USE:
1. Run this script
2. Follow prompts to test each servo
3. Write down the pulse widths that work
4. Update config/default.yaml with the correct values
"""

from __future__ import annotations

import time
from utils.logger import setup_logging, get_logger
from arm.pca9685_driver import PCA9685

logger = get_logger(__name__)


def wait(msg: str = "Press Enter to continue...", sec: float = 0.0) -> None:
    """Wait for user input."""
    if sec > 0:
        time.sleep(sec)
    input(msg)


def test_servo_range(pwm: PCA9685, channel: int, name: str) -> tuple:
    """
    Interactively find the working pulse range for a servo.
    
    Returns: (min_pulse, center_pulse, max_pulse)
    """
    print("\n" + "=" * 60)
    print(f"CALIBRATING: {name.upper()} (Channel {channel})")
    print("=" * 60)
    
    # Test common center position first
    print(f"\n1. Testing CENTER position (1500μs)...")
    pwm.set_pulse_width(channel, 1500)
    wait("Does the servo move to a middle position? Press Enter...")
    
    # Find minimum
    print(f"\n2. Finding MINIMUM position...")
    print("We'll try different pulse widths. Watch the servo.")
    
    test_values = [1000, 800, 600, 500, 700, 900]
    min_pulse = 1000
    
    for pulse in test_values:
        pwm.set_pulse_width(channel, pulse)
        time.sleep(0.5)
        response = input(f"  Pulse {pulse}μs - Did it move to minimum? (y/n/skip): ").lower()
        if response == 'y':
            min_pulse = pulse
            print(f"  ✓ Minimum found: {pulse}μs")
            break
        elif response == 'skip':
            min_pulse = int(input("  Enter minimum pulse width manually: "))
            break
    
    # Find maximum
    print(f"\n3. Finding MAXIMUM position...")
    
    test_values = [2000, 2200, 2400, 2500, 2600, 2700]
    max_pulse = 2000
    
    for pulse in test_values:
        pwm.set_pulse_width(channel, pulse)
        time.sleep(0.5)
        response = input(f"  Pulse {pulse}μs - Did it move to maximum? (y/n/skip): ").lower()
        if response == 'y':
            max_pulse = pulse
            print(f"  ✓ Maximum found: {pulse}μs")
            break
        elif response == 'skip':
            max_pulse = int(input("  Enter maximum pulse width manually: "))
            break
    
    # Return to center
    center_pulse = (min_pulse + max_pulse) // 2
    print(f"\n4. Returning to center ({center_pulse}μs)...")
    pwm.set_pulse_width(channel, center_pulse)
    time.sleep(0.5)
    
    print(f"\n✓ {name} calibration complete!")
    print(f"  Min:    {min_pulse}μs")
    print(f"  Center: {center_pulse}μs")
    print(f"  Max:    {max_pulse}μs")
    
    return (min_pulse, center_pulse, max_pulse)


def test_direction(pwm: PCA9685, channel: int, name: str, min_p: int, max_p: int) -> bool:
    """
    Test if servo is inverted.
    
    Returns: True if inverted, False if normal
    """
    print(f"\n" + "=" * 60)
    print(f"TESTING DIRECTION: {name.upper()}")
    print("=" * 60)
    
    print(f"\nGoing to MIN position ({min_p}μs)...")
    pwm.set_pulse_width(channel, min_p)
    wait("Observe the position. Press Enter...", 1.0)
    
    print(f"\nGoing to MAX position ({max_p}μs)...")
    pwm.set_pulse_width(channel, max_p)
    wait("Observe the position. Press Enter...", 1.0)
    
    # Ask about direction
    if name == "shoulder":
        response = input("\nWhen going MIN→MAX, did shoulder move DOWN→UP? (y/n): ").lower()
        return response != 'y'  # inverted if it went UP→DOWN
    
    elif name == "elbow":
        response = input("\nWhen going MIN→MAX, did elbow move CENTER→RIGHT? (y/n): ").lower()
        return response != 'y'  # inverted if it went RIGHT→CENTER
    
    elif name == "gripper":
        response = input("\nWhen going MIN→MAX, did gripper move OPEN→CLOSED? (y/n): ").lower()
        return response != 'y'  # inverted if it went CLOSED→OPEN
    
    return False


def main() -> int:
    setup_logging()
    
    print("\n" + "=" * 60)
    print("SERVO CALIBRATION TOOL")
    print("=" * 60)
    print("\nThis will help you find the correct pulse widths for your servos.")
    print("\nMAKE SURE:")
    print("  - Servos are powered (external 5V)")
    print("  - Arm has room to move")
    print("  - You're ready to watch each servo carefully")
    
    wait("\nPress Enter to start calibration...")
    
    # Initialize PCA9685
    pwm = PCA9685(i2c_bus=1, address=0x40, frequency=50, simulate=False)
    
    # Servo channels (from your config)
    servos = [
        (0, "shoulder"),
        (1, "elbow"),
        (2, "gripper"),
    ]
    
    results = {}
    
    # Calibrate each servo
    for channel, name in servos:
        min_p, center_p, max_p = test_servo_range(pwm, channel, name)
        inverted = test_direction(pwm, channel, name, min_p, max_p)
        
        results[name] = {
            'channel': channel,
            'min_pulse': min_p,
            'max_pulse': max_p,
            'center_pulse': center_p,
            'inverted': inverted,
        }
        
        # Return to center
        pwm.set_pulse_width(channel, center_p)
        time.sleep(0.5)
    
    # Print summary
    print("\n\n" + "=" * 60)
    print("CALIBRATION COMPLETE!")
    print("=" * 60)
    print("\nRESULTS:\n")
    
    for name, data in results.items():
        print(f"{name.upper()}:")
        print(f"  Channel:  {data['channel']}")
        print(f"  Min:      {data['min_pulse']}μs")
        print(f"  Max:      {data['max_pulse']}μs")
        print(f"  Center:   {data['center_pulse']}μs")
        print(f"  Inverted: {data['inverted']}")
        print()
    
    # Generate config
    print("=" * 60)
    print("UPDATE YOUR config/default.yaml:")
    print("=" * 60)
    print()
    print("arm:")
    print("  pwm_limits:")
    print(f"    min_pulse: {min(r['min_pulse'] for r in results.values())}")
    print(f"    max_pulse: {max(r['max_pulse'] for r in results.values())}")
    print()
    print("  # If any servos are inverted, add this to servo.py __init__:")
    for name, data in results.items():
        if data['inverted']:
            print(f"  # {name}: invert=True")
    
    print("\n" + "=" * 60)
    
    # Safe shutdown
    print("\nReturning all servos to center...")
    for name, data in results.items():
        pwm.set_pulse_width(data['channel'], data['center_pulse'])
    
    time.sleep(1)
    pwm.close()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())