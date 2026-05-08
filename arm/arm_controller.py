#!/usr/bin/env python3
"""
arm/arm_controller.py - Simplified Arm Controller

Simple 3-servo arm control:
- Shoulder: Up (90°) / Down (0°)
- Elbow: Left (90°) / Center (0°)
- Gripper: Open (0°) / Close (90°)
"""

from __future__ import annotations

import time
from typing import Optional
from utils.logger import get_logger
from arm.pca9685_driver import PCA9685

logger = get_logger(__name__)


class ArmController:
    """Simple 3-servo arm controller."""
    
    def __init__(self, config, simulate: bool = False):
        self.config = config
        self.simulate = simulate
        
        # Get PCA9685 settings from config
        i2c_address = int(config.get("arm.i2c_address", 0x40))
        pwm_frequency = int(config.get("arm.pwm_frequency", 50))
        
        # Initialize PCA9685
        self.pwm = PCA9685(
            i2c_bus=1,
            address=i2c_address,
            frequency=pwm_frequency,
            simulate=simulate
        )
        
        # Get servo channels from config
        self.shoulder_channel = int(config.get("arm.shoulder_channel", 0))
        self.elbow_channel = int(config.get("arm.elbow_channel", 1))
        self.gripper_channel = int(config.get("arm.gripper_channel", 2))
        
        # Get per-servo pulse limits
        self.shoulder_min_pulse = int(config.get("arm.shoulder.min_pulse", 500))
        self.shoulder_max_pulse = int(config.get("arm.shoulder.max_pulse", 2500))
        
        self.elbow_min_pulse = int(config.get("arm.elbow.min_pulse", 1000))
        self.elbow_max_pulse = int(config.get("arm.elbow.max_pulse", 2000))
        
        self.gripper_min_pulse = int(config.get("arm.gripper.min_pulse", 500))
        self.gripper_max_pulse = int(config.get("arm.gripper.max_pulse", 2500))
        
        logger.info("✓ Arm controller initialized")
        logger.info(f"  Shoulder: Channel {self.shoulder_channel} ({self.shoulder_min_pulse}-{self.shoulder_max_pulse}μs)")
        logger.info(f"  Elbow: Channel {self.elbow_channel} ({self.elbow_min_pulse}-{self.elbow_max_pulse}μs)")
        logger.info(f"  Gripper: Channel {self.gripper_channel} ({self.gripper_min_pulse}-{self.gripper_max_pulse}μs)")
    
    def _angle_to_pulse(self, angle: float, servo: str) -> int:
        """
        Convert servo angle (0-180°) to pulse width in microseconds.
        Uses per-servo pulse limits for different servo models.
        
        Args:
            angle: Target angle (0-180°)
            servo: 'shoulder', 'elbow', or 'gripper'
        """
        angle = max(0, min(180, angle))
        
        # Get pulse limits for this servo
        if servo == 'shoulder':
            min_pulse = self.shoulder_min_pulse
            max_pulse = self.shoulder_max_pulse
        elif servo == 'elbow':
            min_pulse = self.elbow_min_pulse
            max_pulse = self.elbow_max_pulse
        elif servo == 'gripper':
            min_pulse = self.gripper_min_pulse
            max_pulse = self.gripper_max_pulse
        else:
            # Default fallback
            min_pulse = 500
            max_pulse = 2500
        
        # Calculate pulse width
        pulse_us = int(min_pulse + (angle / 180.0) * (max_pulse - min_pulse))
        return pulse_us
    
    def _set_servo(self, channel: int, angle: float, servo: str) -> None:
        """Set a servo to a specific angle."""
        pulse_us = self._angle_to_pulse(angle, servo)
        self.pwm.set_pulse_width(channel, pulse_us)
        logger.debug(f"{servo.capitalize()} channel {channel}: {angle}° ({pulse_us}μs)")
    
    # ============ SHOULDER FUNCTIONS ============
    # NOTE: Shoulder servo is mounted horizontally
    # 0° = horizontal (rest position, 1500μs)
    # 90° = vertical up (500μs)
    
    def shoulder_up(self) -> None:
        """Raise shoulder to 90° (vertical up)."""
        logger.info("Shoulder UP (90° vertical)")
        self._set_servo(self.shoulder_channel, 90, 'shoulder')
    
    def shoulder_down(self) -> None:
        """Lower shoulder to 0° (horizontal rest)."""
        logger.info("Shoulder DOWN (0° horizontal)")
        self._set_servo(self.shoulder_channel, 0, 'shoulder')
    
    def move_shoulder(self, angle: float) -> None:
        """
        Move shoulder to specific angle.
        0° = horizontal (rest)
        90° = vertical up
        """
        angle = max(0, min(90, angle))
        logger.info(f"Shoulder to {angle}°")
        self._set_servo(self.shoulder_channel, angle, 'shoulder')
    
    # ============ ELBOW FUNCTIONS ============
    
    def elbow_left(self) -> None:
        """Turn elbow 90° to the left."""
        logger.info("Elbow LEFT (90°)")
        self._set_servo(self.elbow_channel, 90, 'elbow')
    
    def elbow_center(self) -> None:
        """Return elbow to center (0°)."""
        logger.info("Elbow CENTER (0°)")
        self._set_servo(self.elbow_channel, 0, 'elbow')
    
    def move_elbow(self, angle: float) -> None:
        """Move elbow to specific angle (0-90°)."""
        angle = max(0, min(90, angle))
        logger.info(f"Elbow to {angle}°")
        self._set_servo(self.elbow_channel, angle, 'elbow')
    
    # ============ GRIPPER FUNCTIONS ============
    
    def gripper_open(self) -> None:
        """Open gripper (0°)."""
        logger.info("Gripper OPEN (0°)")
        self._set_servo(self.gripper_channel, 0, 'gripper')
    
    def gripper_close(self) -> None:
        """Close gripper (90°)."""
        logger.info("Gripper CLOSE (90°)")
        self._set_servo(self.gripper_channel, 90, 'gripper')
    
    def move_gripper(self, angle: float) -> None:
        """Move gripper to specific angle (0-90°)."""
        angle = max(0, min(90, angle))
        logger.info(f"Gripper to {angle}°")
        self._set_servo(self.gripper_channel, angle, 'gripper')
    
    # ============ UTILITY ============
    
    def home(self) -> None:
        """Return all servos to home position (all at 0°)."""
        logger.info("Moving to HOME position")
        self.shoulder_down()
        self.elbow_center()
        self.gripper_open()
    
    def close(self) -> None:
        """Clean up and close."""
        logger.info("Closing arm controller")
        self.home()
        if self.pwm:
            self.pwm.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    from utils.logger import setup_logging
    from utils.config_loader import load_config
    
    setup_logging()
    cfg = load_config("config/default.yaml")
    
    logger.info("Testing arm controller")
    
    with ArmController(config=cfg, simulate=True) as arm:
        logger.info("\n1. Testing gripper")
        arm.gripper_open()
        time.sleep(1)
        arm.gripper_close()
        time.sleep(1)
        
        logger.info("\n2. Testing shoulder")
        arm.shoulder_up()
        time.sleep(1)
        arm.shoulder_down()
        time.sleep(1)
        
        logger.info("\n3. Testing elbow")
        arm.elbow_left()
        time.sleep(1)
        arm.elbow_center()
        time.sleep(1)
        
        logger.info("\n4. Returning home")
        arm.home()
    
    logger.info("✓ Test complete")