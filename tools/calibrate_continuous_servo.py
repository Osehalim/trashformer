#!/usr/bin/env python3
"""
tools/calibrate_continuous_servo.py - Find the STOP pulse for continuous servo

The elbow servo is a continuous rotation servo. We need to find the exact
pulse width that makes it STOP (not spin).

This script will help you:
1. Find the stop pulse (usually around 1500μs but varies)
2. Test movement speeds

After calibration, update config/default.yaml with the stop_pulse value.
"""

from __future__ import annotations

import time
from arm.pca9685_driver import PCA9685
from utils.logger import setup_logging, get_logger

logger = get_logger(__name__)


def main() -> int:
    setup_logging()
    
    print("\n" + "=" * 60)
    print("CONTINUOUS SERVO CALIBRATION")
    print("=" * 60)
    print("\nElbow Servo: ServoCityServo 2000 Series 5-Turn")
    print("Channel: 1")
    print()
    print("Goal: Find the pulse width that STOPS the servo")
    print()
    print("MAKE SURE:")
    print("  - Elbow servo is connected to Channel 1")
    print("  - Servo has room to spin")
    print("  - External 5V power is connected")
    print()
    
    input("Press Enter to start...")
    
    pwm = PCA9685(i2c_bus=1, address=0x40, frequency=50, simulate=False)
    channel = 1  # Elbow
    
    # ================================================================
    # STEP 1: Find STOP pulse
    # ================================================================
    print("\n" + "=" * 60)
    print("STEP 1: FIND STOP PULSE")
    print("=" * 60)
    print("\nWe'll try different pulse widths.")
    print("Watch the servo and tell me when it STOPS completely.")
    print()
    
    test_pulses = [1500, 1480, 1520, 1460, 1540, 1450, 1550, 1470, 1530]
    stop_pulse = 1500
    
    for pulse in test_pulses:
        print(f"\nTrying {pulse}μs...")
        pwm.set_pulse_width(channel, pulse)
        time.sleep(2)
        
        response = input("Is servo STOPPED? (y/n/quit): ").lower()
        if response == 'y':
            stop_pulse = pulse
            print(f"✓ Stop pulse found: {pulse}μs")
            break
        elif response == 'quit':
            print("Calibration cancelled")
            pwm.close()
            return 1
    
    print(f"\nUsing stop pulse: {stop_pulse}μs")
    
    # ================================================================
    # STEP 2: Test movement directions
    # ================================================================
    print("\n" + "=" * 60)
    print("STEP 2: TEST MOVEMENT")
    print("=" * 60)
    print("\nNow we'll test spinning in both directions")
    print()
    
    # Test one direction
    print(f"Setting pulse to {stop_pulse + 100}μs (should spin one way)")
    pwm.set_pulse_width(channel, stop_pulse + 100)
    input("Watch it spin. Press Enter to stop...")
    pwm.set_pulse_width(channel, stop_pulse)
    
    print(f"\nSetting pulse to {stop_pulse - 100}μs (should spin other way)")
    pwm.set_pulse_width(channel, stop_pulse - 100)
    input("Watch it spin. Press Enter to stop...")
    pwm.set_pulse_width(channel, stop_pulse)
    
    # ================================================================
    # STEP 3: Estimate timing
    # ================================================================
    print("\n" + "=" * 60)
    print("STEP 3: ESTIMATE ROTATION SPEED")
    print("=" * 60)
    print("\nWe'll spin for 2 seconds and you estimate how far it moved")
    print()
    
    input("Ready? Press Enter to start 2-second test spin...")
    
    print(f"Spinning at {stop_pulse + 100}μs for 2 seconds...")
    pwm.set_pulse_width(channel, stop_pulse + 100)
    time.sleep(2.0)
    pwm.set_pulse_width(channel, stop_pulse)
    
    print("\nHow many degrees did it rotate? (estimate)")
    print("Examples: 90, 180, 270, 360, etc.")
    degrees = float(input("Degrees: "))
    
    degrees_per_second = degrees / 2.0
    print(f"\nEstimated speed: {degrees_per_second:.1f} degrees/second")
    
    # ================================================================
    # RESULTS
    # ================================================================
    print("\n\n" + "=" * 60)
    print("CALIBRATION COMPLETE!")
    print("=" * 60)
    print()
    print(f"Stop Pulse:  {stop_pulse}μs")
    print(f"Speed Range: ±100μs from stop")
    print(f"Est. Speed:  {degrees_per_second:.1f}°/sec at ±100μs")
    print()
    print("=" * 60)
    print("UPDATE config/default.yaml:")
    print("=" * 60)
    print()
    print("arm:")
    print("  continuous_servo:")
    print(f"    stop_pulse: {stop_pulse}")
    print(f"    speed_pulse_range: 100")
    print()
    print("# Also update servo_continuous.py if needed:")
    print(f"# DEGREES_PER_SECOND = {degrees_per_second:.1f}")
    print()
    
    # Return to stop
    pwm.set_pulse_width(channel, stop_pulse)
    time.sleep(0.5)
    pwm.close()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())