#!/usr/bin/env python3
"""
tools/teleop_gamepad.py - USB Gamepad teleoperation

Control robot with Xbox/PlayStation controller via USB or Bluetooth.

Supported controllers:
  - Xbox One/Series controller
  - Xbox 360 controller
  - PlayStation DualShock 4
  - PlayStation DualSense
  - Generic USB gamepads

Controls (Xbox layout):
  Left stick: Drive forward/backward + turn
  Right stick: Rotate in place
  A button: Stop
  Start: Quit

Usage:
  python3 teleop_gamepad.py
"""

from __future__ import annotations

import time
from utils.logger import setup_logging, get_logger
from utils.config_loader import load_config
from drive.drive_controller import DriveController

logger = get_logger(__name__)

try:
    from inputs import get_gamepad
    GAMEPAD_AVAILABLE = True
except ImportError:
    GAMEPAD_AVAILABLE = False
    logger.warning("'inputs' library not available - install with: pip3 install inputs")


class GamepadTeleop:
    """
    USB/Bluetooth gamepad teleoperation.
    
    Continuously reads gamepad input and controls motors.
    """
    
    def __init__(self, config, simulate: bool = False):
        self.config = config
        self.simulate = simulate or (not GAMEPAD_AVAILABLE)
        self.drive = DriveController(config=config, simulate=simulate)
        
        # Control settings
        self.max_linear_speed = 0.5   # m/s
        self.max_angular_speed = 1.0  # rad/s
        self.deadzone = 0.15          # Joystick deadzone
        
        # Gamepad state
        self.left_stick_x = 0.0   # Left/right
        self.left_stick_y = 0.0   # Forward/back
        self.right_stick_x = 0.0  # Rotate
        
        self.running = True
        
        if self.simulate:
            logger.warning("GamepadTeleop running in SIMULATION mode")
        else:
            logger.info("Gamepad teleop initialized")
            logger.info(f"Max speed: {self.max_linear_speed} m/s")
    
    def apply_deadzone(self, value: float) -> float:
        """
        Apply deadzone to joystick value.
        
        Args:
            value: Raw joystick value (-1.0 to 1.0)
            
        Returns:
            Processed value with deadzone applied
        """
        if abs(value) < self.deadzone:
            return 0.0
        
        # Scale to full range after deadzone
        if value > 0:
            return (value - self.deadzone) / (1.0 - self.deadzone)
        else:
            return (value + self.deadzone) / (1.0 - self.deadzone)
    
    def process_gamepad_event(self, event):
        """
        Process gamepad event.
        
        Args:
            event: Gamepad event from inputs library
        """
        # Left stick Y-axis (forward/backward)
        if event.code == 'ABS_Y':
            # Invert Y axis (up = negative, we want up = positive)
            self.left_stick_y = -event.state / 32768.0
        
        # Left stick X-axis (left/right turning)
        elif event.code == 'ABS_X':
            self.left_stick_x = event.state / 32768.0
        
        # Right stick X-axis (rotation)
        elif event.code == 'ABS_RX':
            self.right_stick_x = event.state / 32768.0
        
        # A button (stop)
        elif event.code == 'BTN_SOUTH' and event.state == 1:
            logger.info("Stop button pressed")
            self.drive.stop()
            self.left_stick_x = 0.0
            self.left_stick_y = 0.0
            self.right_stick_x = 0.0
        
        # Start button (quit)
        elif event.code == 'BTN_START' and event.state == 1:
            logger.info("Start button pressed - quitting")
            self.running = False
    
    def update_motors(self):
        """Update motor commands based on current gamepad state."""
        # Apply deadzones
        forward = self.apply_deadzone(self.left_stick_y)
        turn = self.apply_deadzone(self.left_stick_x)
        rotate = self.apply_deadzone(self.right_stick_x)
        
        # Calculate velocities
        if abs(rotate) > 0.05:
            # Rotation mode (right stick has priority)
            linear = 0.0
            angular = rotate * self.max_angular_speed
        else:
            # Drive mode (left stick)
            linear = forward * self.max_linear_speed
            angular = turn * self.max_angular_speed
        
        # Send to drive controller
        self.drive.drive_velocity(linear, angular)
    
    def run(self):
        """Main teleoperation loop."""
        if self.simulate:
            logger.error("No gamepad available - install 'inputs' library")
            logger.info("Install with: pip3 install inputs --break-system-packages")
            return
        
        print("\n" + "=" * 60)
        print("GAMEPAD TELEOPERATION")
        print("=" * 60)
        print()
        print("Controls:")
        print("  Left stick: Drive and turn")
        print("  Right stick (horizontal): Rotate in place")
        print("  A button: Stop")
        print("  Start button: Quit")
        print()
        print(f"Max speed: {self.max_linear_speed} m/s")
        print("=" * 60)
        print()
        
        logger.info("Waiting for gamepad input...")
        logger.info("Connect gamepad via USB or Bluetooth")
        
        try:
            while self.running:
                # Read gamepad events
                from inputs import devices

                gamepad = devices.gamepads[0]

                while self.running:
                    events = gamepad.read()
                
                for event in events:
                    self.process_gamepad_event(event)
                
                # Update motors based on current state
                self.update_motors()
        
        except KeyboardInterrupt:
            logger.info("\nKeyboard interrupt")
        
        except Exception as e:
            logger.error(f"Gamepad error: {e}")
            logger.info("Make sure gamepad is connected")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Stop motors and clean up."""
        logger.info("Cleaning up...")
        self.drive.stop()
        self.drive.close()
        logger.info("Teleop stopped")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


def main() -> int:
    setup_logging()
    cfg = load_config("config/default.yaml")
    
    with GamepadTeleop(config=cfg, simulate=False) as teleop:
        teleop.run()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())