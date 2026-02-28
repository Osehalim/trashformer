#!/usr/bin/env python3
"""
Find the exact neutral stop pulse for the elbow continuous servo.
"""

from __future__ import annotations
import time
from utils.logger import setup_logging
from utils.config_loader import load_config
from arm.arm_controller import ArmController

def main():
    setup_logging()
    cfg = load_config("config/default.yaml")

    with ArmController(config=cfg, simulate=False) as arm:
        elbow = arm.servos["elbow"]

        print("\nTesting neutral pulse values...")
        print("Watch the elbow carefully.\n")

        for pulse in range(1470, 1531, 2):  # sweep around 1500
            print(f"Testing stop_pulse = {pulse}")
            elbow.pwm.set_pulse_width(elbow.channel, pulse)
            time.sleep(2)

        # finally send known 1500
        elbow.pwm.set_pulse_width(elbow.channel, 1500)
        time.sleep(1)

if __name__ == "__main__":
    main()