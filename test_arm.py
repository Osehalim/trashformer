#!/usr/bin/env python3
"""
Test script for Trashformer arm - works in simulation mode
"""

from arm.arm_controller import ArmController
from utils.config_loader import load_config
import time

print("="*50)
print("TRASHFORMER ARM TEST")
print("="*50)
print()

# Initialize (simulate=True means no hardware needed)
print("Initializing arm controller...")
config = load_config('config/default.yaml')
arm = ArmController(config=config, simulate=True)  # Change to False when you have PCA9685
print("✓ Arm ready!")
print()

# Test 1: Home position
print("1. Going to HOME position...")
arm.home()
time.sleep(2)

# Test 2: Shoulder movements
print("\n2. Testing SHOULDER (vertical movement)...")
print("   - Moving to horizontal (90°)")
arm.shoulder_horizontal()
time.sleep(2)

print("   - Moving up (135°)")
arm.shoulder_up(135)
time.sleep(2)

print("   - Moving down (0°)")
arm.shoulder_down()
time.sleep(2)

# Test 3: Elbow movements
print("\n3. Testing ELBOW (rotation)...")
print("   - Center position (0°)")
arm.elbow_center()
time.sleep(2)

print("   - Turning right (90°)")
arm.elbow_right(90)
time.sleep(2)

print("   - Back to center (0°)")
arm.elbow_center()
time.sleep(2)

# Test 4: Gripper
print("\n4. Testing GRIPPER...")
print("   - Opening")
arm.open_gripper()
time.sleep(1)

print("   - Closing")
arm.close_gripper()
time.sleep(1)

print("   - Opening")
arm.open_gripper()
time.sleep(1)

# Return home
print("\n5. Returning to HOME...")
arm.home()
time.sleep(1)

arm.close()

print()
print("="*50)
print("TEST COMPLETE!")
print("="*50)