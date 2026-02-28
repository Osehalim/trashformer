#!/usr/bin/env python3
"""
Elbow Continuous Servo Calibration - Direct PWM Control

This script finds the stop pulse WITHOUT using ArmController.
It sends raw PWM values directly to avoid any automatic movement.

Your elbow servo: ServoCity 2000 Series 5-Turn (CONTINUOUS)
"""

from __future__ import annotations
import time
from utils.logger import setup_logging, get_logger
from arm.pca9685_driver import PCA9685

logger = get_logger(__name__)


def find_stop_pulse_direct() -> int:
    """
    Find stop pulse using DIRECT PWM control (no ArmController).
    
    Returns the stop pulse value.
    """
    print("\n" + "=" * 60)
    print("ELBOW STOP PULSE CALIBRATION (Direct PWM)")
    print("=" * 60)
    print()
    print("This uses RAW PWM commands to avoid automatic movement.")
    print("Watch the elbow and tell me when it STOPS spinning.")
    print()
    
    # Initialize PCA9685 directly
    pwm = PCA9685(i2c_bus=1, address=0x40, frequency=50, simulate=False)
    elbow_channel = 1
    
    print("Initializing...")
    print("First, sending 1450μs (very low) to try to stop any movement...")
    pwm.set_pulse_width(elbow_channel, 1450)
    time.sleep(3)
    
    print()
    print("Now testing pulses from LOW to HIGH...")
    print("We're looking for the pulse where it STOPS completely.")
    print()
    
    # Test from LOW to HIGH
    test_pulses = [1450, 1460, 1470, 1480, 1490, 1500, 1510, 1520, 1530, 1540, 1550]
    
    stop_pulse = 1500  # default
    
    for pulse in test_pulses:
        print(f"\nTesting {pulse}μs...")
        pwm.set_pulse_width(elbow_channel, pulse)
        print(f"  (Sent {pulse}μs to elbow, waiting 4 seconds...)")
        time.sleep(4)
        
        response = input(f"  Is elbow COMPLETELY STOPPED at {pulse}μs? (y/n/skip): ").lower()
        
        if response == 'y':
            print(f"\n✓ Stop pulse found: {pulse}μs")
            stop_pulse = pulse
            pwm.close()
            return stop_pulse
        elif response == 'skip':
            break
    
    # Manual entry
    print("\nCouldn't find it automatically.")
    stop_pulse = int(input("Enter stop pulse manually (1450-1550): "))
    
    # Verify
    print(f"\nVerifying {stop_pulse}μs...")
    pwm.set_pulse_width(elbow_channel, stop_pulse)
    time.sleep(3)
    
    response = input(f"Stopped at {stop_pulse}μs? (y/n): ").lower()
    if response != 'y':
        stop_pulse = int(input("Enter correct stop pulse: "))
    
    pwm.close()
    return stop_pulse


def test_movement_with_stop_pulse(stop_pulse: int):
    """
    Test elbow movement using the calibrated stop pulse.
    """
    from utils.config_loader import load_config
    from arm.arm_controller import ArmController
    
    print("\n" + "=" * 60)
    print("TESTING ELBOW MOVEMENT")
    print("=" * 60)
    print(f"\nUsing stop_pulse: {stop_pulse}μs")
    print()
    
    # Load config
    cfg = load_config("config/default.yaml")
    
    print("Creating ArmController...")
    with ArmController(config=cfg, simulate=False) as arm:
        
        elbow = arm.servos["elbow"]
        
        # Update stop pulse
        elbow.stop_pulse = stop_pulse
        print(f"✓ Updated elbow stop_pulse to {stop_pulse}μs")
        
        # Make sure we're at center
        print("\nEnsuring elbow is at center...")
        elbow._estimated_position = 0.0
        elbow.pwm.set_pulse_width(elbow.channel, stop_pulse)
        time.sleep(2)
        
        input("\nPress Enter to test turning RIGHT 90°...")
        
        # Test 1: Turn right
        print("\n--- Test 1: Turning RIGHT (0° → 90°) ---")
        start_time = time.time()
        elbow.move_to(90)
        elapsed = time.time() - start_time
        
        print(f"Movement took {elapsed:.2f} seconds")
        print(f"Estimated speed: {90/elapsed:.1f} degrees/second")
        print("Elbow should be stopped at ~90° right")
        
        time.sleep(3)
        input("\nPress Enter to return to CENTER...")
        
        # Test 2: Return to center
        print("\n--- Test 2: Returning to CENTER (90° → 0°) ---")
        start_time = time.time()
        elbow.move_to(0)
        elapsed = time.time() - start_time
        
        print(f"Movement took {elapsed:.2f} seconds")
        print("Elbow should be stopped at center")
        
        time.sleep(2)
        
        print("\n✓ Movement test complete!")
        print()
        print("Did the elbow:")
        print("  1. Stop at 90° right?")
        print("  2. Return to center?")
        print("  3. Stop at each position?")
        
        response = input("\nDid it work correctly? (y/n): ").lower()
        
        if response == 'y':
            print("\n✓ Great! The stop pulse is correct.")
        else:
            print("\n⚠ If movement distance was wrong:")
            print("   - Too far: Decrease degrees_per_second in default.yaml")
            print("   - Too short: Increase degrees_per_second in default.yaml")
            print("   - Kept spinning: Try different stop_pulse values")


def main() -> int:
    setup_logging()
    
    print("=" * 60)
    print("ELBOW CONTINUOUS SERVO CALIBRATION")
    print("=" * 60)
    print()
    print("Servo: ServoCity 2000 Series 5-Turn")
    print("Channel: 1 (Elbow)")
    print()
    print("This will:")
    print("  1. Find the stop pulse (using direct PWM)")
    print("  2. Test turning right and returning to center")
    print()
    
    input("Make sure elbow is connected to Channel 1. Press Enter...")
    
    # Step 1: Find stop pulse (direct PWM, no ArmController)
    stop_pulse = find_stop_pulse_direct()
    
    # Step 2: Test movement (with ArmController)
    test_movement_with_stop_pulse(stop_pulse)
    
    # Final summary
    print("\n" + "=" * 60)
    print("CALIBRATION COMPLETE!")
    print("=" * 60)
    print()
    print(f"Stop Pulse: {stop_pulse}μs")
    print()
    print("=" * 60)
    print("UPDATE config/default.yaml:")
    print("=" * 60)
    print()
    print("continuous_servo:")
    print(f"  stop_pulse: {stop_pulse}")
    print(f"  speed_pulse_range: 120")
    print(f"  degrees_per_second: 180")
    print()
    print("If movement distance was wrong, adjust degrees_per_second.")
    print()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())