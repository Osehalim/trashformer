#!/usr/bin/env python3
"""
Elbow Continuous Servo Calibration - FIXED VERSION

Key fixes:
1. Manually set the starting position to match reality
2. Use direct PWM control for stop pulse finding
3. Test actual movement from TRUE current position

Your elbow servo: ServoCity 2000 Series 5-Turn (CONTINUOUS)
"""

from __future__ import annotations
import time
from utils.logger import setup_logging, get_logger
from arm.pca9685_driver import PCA9685

logger = get_logger(__name__)


def find_stop_pulse_direct() -> int:
    """
    Find stop pulse using DIRECT PWM control.
    
    Returns the stop pulse value.
    """
    print("\n" + "=" * 60)
    print("ELBOW STOP PULSE CALIBRATION")
    print("=" * 60)
    print()
    print("⚠️  IMPORTANT: Before we start...")
    print("   Manually position the elbow so it's IN LINE with the rest of the arm")
    print("   (straight forward, not turned left or right)")
    print()
    
    input("Position elbow straight, then press Enter...")
    
    print()
    print("Good! Now we'll find the pulse that KEEPS it there (stopped).")
    print()
    
    # Initialize PCA9685 directly
    pwm = PCA9685(i2c_bus=1, address=0x40, frequency=50, simulate=False)
    elbow_channel = 1
    
    print("Sending 1450μs (very low) to try to stop it...")
    pwm.set_pulse_width(elbow_channel, 1450)
    time.sleep(3)
    
    print()
    print("Now testing pulses from LOW to HIGH...")
    print("Watch for the pulse where it stays COMPLETELY STILL.")
    print()
    
    # Test from LOW to HIGH
    test_pulses = [1450, 1460, 1470, 1480, 1490, 1500, 1510, 1520, 1530, 1540, 1550]
    
    stop_pulse = 1500  # default
    
    for pulse in test_pulses:
        print(f"\n>>> Testing {pulse}μs...")
        pwm.set_pulse_width(elbow_channel, pulse)
        print(f"    Waiting 5 seconds for you to observe...")
        time.sleep(5)
        
        response = input(f"    Is elbow COMPLETELY STOPPED at {pulse}μs? (y/n/skip): ").lower()
        
        if response == 'y':
            print(f"\n✓ Stop pulse found: {pulse}μs")
            stop_pulse = pulse
            # Keep it at stop pulse
            pwm.set_pulse_width(elbow_channel, stop_pulse)
            time.sleep(1)
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
        pwm.set_pulse_width(elbow_channel, stop_pulse)
        time.sleep(2)
    
    pwm.close()
    return stop_pulse


def test_movement_with_stop_pulse(stop_pulse: int):
    """
    Test elbow movement using the calibrated stop pulse.
    CRITICAL: Set starting position to match physical reality!
    """
    from utils.config_loader import load_config
    from arm.arm_controller import ArmController
    
    print("\n" + "=" * 60)
    print("TESTING ELBOW MOVEMENT")
    print("=" * 60)
    print(f"\nUsing stop_pulse: {stop_pulse}μs")
    print()
    
    print("⚠️  IMPORTANT:")
    print("   Make sure elbow is still IN LINE with the arm (straight forward)")
    print("   We'll set the code's position to match reality.")
    print()
    
    input("Press Enter when elbow is straight...")
    
    # Load config
    cfg = load_config("config/default.yaml")
    
    print("\nCreating ArmController...")
    with ArmController(config=cfg, simulate=False) as arm:
        
        elbow = arm.servos["elbow"]
        
        # CRITICAL FIX: Set estimated position to match physical reality
        print(f"✓ Setting stop_pulse to {stop_pulse}μs")
        elbow.stop_pulse = stop_pulse
        
        print("✓ Setting estimated position to 0° (center/straight)")
        elbow._estimated_position = 0.0  # Physical reality = code reality
        
        # Send stop pulse to ensure it's not moving
        print("✓ Sending stop pulse to ensure elbow is stopped...")
        elbow.pwm.set_pulse_width(elbow.channel, stop_pulse)
        time.sleep(2)
        
        print()
        print("Current state:")
        print(f"  Physical position: Straight forward (in line with arm)")
        print(f"  Code position: {elbow._estimated_position}° (center)")
        print(f"  ✓ These match!")
        print()
        
        input("Press Enter to test turning RIGHT 90°...")
        
        # Test 1: Turn right
        print("\n" + "=" * 50)
        print("TEST 1: Turning RIGHT (0° → 90°)")
        print("=" * 50)
        print("Watch the elbow turn to the RIGHT...")
        print()
        
        start_time = time.time()
        elbow.move_to(90)
        elapsed = time.time() - start_time
        
        print()
        print(f"✓ Movement took {elapsed:.2f} seconds")
        print(f"  Estimated speed: {90/elapsed:.1f} degrees/second")
        print()
        print("The elbow should now be:")
        print("  - Turned 90° to the RIGHT")
        print("  - STOPPED (not spinning)")
        print()
        
        time.sleep(2)
        
        response = input("Did it turn ~90° to the right and STOP? (y/n): ").lower()
        if response != 'y':
            print("\n⚠️  Problem detected!")
            print("Possible causes:")
            print("  - Wrong stop pulse (it kept spinning)")
            print("  - Wrong degrees_per_second (moved too far/short)")
            print()
        
        time.sleep(1)
        input("\nPress Enter to return to CENTER (original position)...")
        
        # Test 2: Return to center
        print("\n" + "=" * 50)
        print("TEST 2: Returning to CENTER (90° → 0°)")
        print("=" * 50)
        print("Watch the elbow return to the ORIGINAL position...")
        print()
        
        start_time = time.time()
        elbow.move_to(0)
        elapsed = time.time() - start_time
        
        print()
        print(f"✓ Movement took {elapsed:.2f} seconds")
        print()
        print("The elbow should now be:")
        print("  - Back IN LINE with the arm (straight forward)")
        print("  - At the SAME position where we started")
        print("  - STOPPED (not spinning)")
        print()
        
        time.sleep(2)
        
        response = input("Did it return to the ORIGINAL straight position? (y/n): ").lower()
        
        print()
        print("=" * 60)
        if response == 'y':
            print("✓✓✓ SUCCESS! ✓✓✓")
            print()
            print("The elbow:")
            print("  ✓ Turned right 90°")
            print("  ✓ Returned to original position")
            print("  ✓ Stopped at each position")
            print()
            print("Your stop_pulse is correct!")
        else:
            print("⚠️  NEEDS ADJUSTMENT")
            print()
            
            print("If it didn't return to original position:")
            print()
            print("  Problem: Moved too far")
            print("  Solution: DECREASE degrees_per_second in default.yaml")
            print("            (try 150 if it's currently 180)")
            print()
            print("  Problem: Didn't move far enough")
            print("  Solution: INCREASE degrees_per_second in default.yaml")
            print("            (try 210 if it's currently 180)")
            print()
            print("  Problem: Kept spinning, didn't stop")
            print("  Solution: Re-run calibration to find correct stop_pulse")
        print("=" * 60)


def main() -> int:
    setup_logging()
    
    print("=" * 60)
    print("ELBOW CONTINUOUS SERVO CALIBRATION v2")
    print("=" * 60)
    print()
    print("Servo: ServoCity 2000 Series 5-Turn")
    print("Channel: 1 (Elbow)")
    print()
    print("This will:")
    print("  1. Find the stop pulse")
    print("  2. Set starting position to match reality")
    print("  3. Test movement and return to original position")
    print()
    
    input("Make sure elbow is connected to Channel 1. Press Enter...")
    
    # Step 1: Find stop pulse (direct PWM, no ArmController)
    stop_pulse = find_stop_pulse_direct()
    
    # Step 2: Test movement (with corrected starting position)
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
    print("  speed_pulse_range: 120")
    print("  degrees_per_second: 180  # Adjust if needed")
    print()
    print("If movement distance was wrong:")
    print("  - Too far: Decrease degrees_per_second (try 150)")
    print("  - Too short: Increase degrees_per_second (try 210)")
    print()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())