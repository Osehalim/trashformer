#!/usr/bin/env python3
from arm.arm_controller import ArmController
from utils.config_loader import load_config
import time

print("Initializing arm...")
config = load_config('config/default.yaml')
arm = ArmController(config=config, simulate=False)

print("Going home...")
arm.home()
time.sleep(2)

print("Testing shoulder...")
arm.shoulder_horizontal()
time.sleep(2)

print("Testing elbow...")
arm.elbow_right(90)
time.sleep(2)

print("Testing gripper...")
arm.close_gripper()
time.sleep(1)
arm.open_gripper()
time.sleep(1)

print("Done!")
arm.close()