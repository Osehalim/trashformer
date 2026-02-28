#!/usr/bin/env python3
"""
Elbow Continuous Servo Test

This script:
1. Finds the exact stop pulse for your elbow servo
2. Tests turning right and returning to center
3. Helps calibrate the movement speed

Your elbow servo: ServoCity 2000 Series 5-Turn (CONTINUOUS)
"""

from __future__ import annotations
import time
from utils.logger import setup_logging, get_logger
from utils.config_loader import load_config
from arm.arm_controller import ArmController

logger = get_logger(__name__)


def find_stop_pulse(arm: ArmController) -> int:
    """
    Find the exact pulse width that stops the elbow servo.
    
    Returns the stop pulse value.
    """
    elbow = arm.servos["elbow"]
    
    print("\n" + "=" * 60)
    print("STEP 1: FIND STOP PULSE")
    print("=" * 60)
    print("\nWe need to find the pulse that makes the elbow STOP spinning.")
    print("Watch the elbow carefully and tell me when it's completely stopped.")
    print()
    
    # First, try to stop it with a very low value
    print("First, I'll send a LOW pulse to try to stop any movement...")
    elbow.pwm.set_pulse_width(elbow.channel, 1450)
    time.sleep(2)
    
    print("\nNow testing different pulses, starting low and going higher.")
    print("We're looking for the LOWEST pulse that keeps it STOPPED.")
    print()
    
    # Test values starting LOW and increasing
    # Start well below typical stop point to avoid spinning
    test_pulses = [1450, 1460, 1470, 1480, 1490, 1500, 1510, 1520, 1530]
    
    for pulse in test_pulses:
        print(f"\nTesting {pulse}μs...")
        elbow.pwm.set_pulse_width(elbow.channel, pulse)
        print("  (waiting 3 seconds for you to observe...)")
        time.sleep(3)
        
        response = input(f"  Is elbow COMPLETELY STOPPED at {pulse}μs? (y/n/skip): ").lower()
        if response == 'y':
            print(f"\n✓ Stop pulse found: {pulse}μs")
            print(f"  (If it starts spinning again, the true stop is higher)")
            return pulse
        elif response == 'skip':
            break
    
    # If none worked, ask user
    print("\nCouldn't find it automatically.")
    stop_pulse = int(input("Enter stop pulse manually (try values 1450-1550): "))
    
    # Verify
    elbow.pwm.set_pulse_width(elbow.channel, stop_pulse)
    time.sleep(2)
    response = input(f"Stopped at {stop_pulse}? (y/n): ").lower()
    
    if response == 'y':
        return stop_pulse
    else:
        print("Using 1500μs as default")
        return 1500


def test_elbow_movement(arm: ArmController, stop_pulse: int):
    """
    Test elbow turning right and returning to center.
    """
    elbow = arm.servos["elbow"]
    
    print("\n" + "=" * 60)
    print("STEP 2: TEST ELBOW MOVEMENT")
    print("=" * 60)
    print(f"\nUsing stop pulse: {stop_pulse}μs")
    print()
    
    # Update the servo's stop pulse
    elbow.stop_pulse = stop_pulse
    elbow._estimated_position = 0.0  # Reset to center
    
    input("Press Enter to start movement test...")
    
    # ================================================================
    # Movement 1: Turn RIGHT
    # ================================================================
    print("\n--- Movement 1: Turning RIGHT (0° → 90°) ---")
    print("Watch how far the elbow turns...")
    
    start_time = time.time()
    elbow.move_to(90)  # Turn right 90 degrees
    elapsed = time.time() - start_time
    
    print(f"Movement took {elapsed:.2f} seconds")
    print(f"Estimated speed: {90/elapsed:.1f} degrees/second")
    
    input("\nDid it turn about 90° to the right? Press Enter...")
    
    # ================================================================
    # Pause at right position
    # ================================================================
    print("\nElbow should be at 90° right position now.")
    print("Servo should be STOPPED (not spinning).")
    time.sleep(2)
    
    # ================================================================
    # Movement 2: Return to CENTER
    # ================================================================
    print("\n--- Movement 2: Returning to CENTER (90° → 0°) ---")
    
    start_time = time.time()
    elbow.move_to(0)  # Return to center
    elapsed = time.time() - start_time
    
    print(f"Movement took {elapsed:.2f} seconds")
    
    input("\nDid it return to center? Press Enter...")
    
    # ================================================================
    # Verify it's stopped
    # ================================================================
    print("\nElbow should be at center now.")
    print("Servo should be STOPPED (not spinning).")
    time.sleep(2)
    
    print("\n✓ Movement test complete!")


def calibrate_speed(arm: ArmController, stop_pulse: int):
    """
    Help user calibrate the movement speed.
    """
    elbow = arm.servos["elbow"]
    elbow.stop_pulse = stop_pulse
    
    print("\n" + "=" * 60)
    print("STEP 3: CALIBRATE SPEED (Optional)")
    print("=" * 60)
    print()
    
    response = input("Do you want to calibrate the movement speed? (y/n): ").lower()
    if response != 'y':
        return
    
    print("\nWe'll measure how long it takes to move a known distance.")
    print("This helps make movements more accurate.")
    print()
    
    # Reset position
    elbow._estimated_position = 0.0
    
    print("I'll turn the elbow right for exactly 2 seconds.")
    print("Count how many degrees it rotates (estimate).")
    input("Press Enter to start...")
    
    # Move for exactly 2 seconds
    speed_pulse = stop_pulse + 100  # Slow speed
    
    print(f"\nSpinning at {speed_pulse}μs for 2 seconds...")
    elbow.pwm.set_pulse_width(elbow.channel, speed_pulse)
    time.sleep(2.0)
    
    # STOP
    elbow.pwm.set_pulse_width(elbow.channel, stop_pulse)
    
    print("\nStopped.")
    print("\nHow many degrees did it rotate? (estimate)")
    print("Examples: 45, 90, 120, 180, 240, etc.")
    
    degrees = float(input("Degrees rotated: "))
    
    degrees_per_second = degrees / 2.0
    
    print(f"\n✓ Measured speed: {degrees_per_second:.1f} degrees/second")
    print()
    print("Update servo.py, line ~145:")
    print(f"  DEGREES_PER_SECOND = {degrees_per_second:.1f}  # Was 120")
    
    # Return to center
    print("\nReturning to center...")
    move_time = degrees / degrees_per_second
    reverse_pulse = stop_pulse - 100
    
    elbow.pwm.set_pulse_width(elbow.channel, reverse_pulse)
    time.sleep(move_time)
    elbow.pwm.set_pulse_width(elbow.channel, stop_pulse)


def main() -> int:
    setup_logging()
    cfg = load_config("config/default.yaml")
    
    print("=" * 60)
    print("ELBOW CONTINUOUS SERVO TEST")
    print("=" * 60)
    print()
    print("Servo: ServoCity 2000 Series 5-Turn (CONTINUOUS)")
    print("Channel: 1")
    print()
    print("This test will:")
    print("  1. Find the stop pulse")
    print("  2. Test turning right and returning to center")
    print("  3. Optionally calibrate movement speed")
    print()
    
    input("Make sure elbow servo is connected to Channel 1. Press Enter...")
    
    with ArmController(config=cfg, simulate=False) as arm:
        
        # Step 1: Find stop pulse
        stop_pulse = find_stop_pulse(arm)
        
        # Step 2: Test movement
        test_elbow_movement(arm, stop_pulse)
        
        # Step 3: Calibrate speed (optional)
        calibrate_speed(arm, stop_pulse)
        
        # Final summary
        print("\n" + "=" * 60)
        print("TEST COMPLETE!")
        print("=" * 60)
        print()
        print(f"Stop Pulse: {stop_pulse}μs")
        print()
        print("Update config/default.yaml:")
        print("  continuous_servo:")
        print(f"    stop_pulse: {stop_pulse}")
        print()
        
        # Ensure stopped
        elbow = arm.servos["elbow"]
        elbow.pwm.set_pulse_width(elbow.channel, stop_pulse)
        
        return 0


if __name__ == "__main__":
    raise SystemExit(main())