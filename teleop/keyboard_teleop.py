#!/usr/bin/env python3
"""
teleop/keyboard_teleop.py

Control robot with keyboard keys over SSH.

Controls:
  W/S: Forward/Backward
  A/D: Turn left/right
  Q/E: Rotate left/right (in place)
  Space: Stop
  +/-: Increase/decrease speed
  ESC: Quit

Usage:
  python3 teleop_keyboard.py
"""

from __future__ import annotations

import sys
import termios
import tty
import time
from utils.logger import setup_logging, get_logger
from utils.config_loader import load_config
from drive.drive_controller import DriveController

logger = get_logger(__name__)


class KeyboardTeleop:
    """
    Keyboard teleoperation for robot control.
    
    Continuously reads keyboard input and controls motors.
    """
    
    def __init__(self, config, simulate: bool = False):
        self.config = config
        self.drive = DriveController(config=config, simulate=simulate)
        
        # Control settings
        self.linear_speed = 0.3    # m/s
        self.angular_speed = 0.5   # rad/s
        self.speed_increment = 0.1
        
        self.running = True
        
        logger.info("Keyboard teleop initialized")
        logger.info(f"Linear speed: {self.linear_speed} m/s")
        logger.info(f"Angular speed: {self.angular_speed} rad/s")
    
    def get_key(self):
        """Read a single keypress from stdin."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    
    def print_instructions(self):
        """Print control instructions."""
        print("\n" + "=" * 60)
        print("KEYBOARD TELEOPERATION")
        print("=" * 60)
        print()
        print("Controls:")
        print("  W: Forward")
        print("  S: Backward")
        print("  A: Turn left (while moving)")
        print("  D: Turn right (while moving)")
        print("  Q: Rotate left (in place)")
        print("  E: Rotate right (in place)")
        print()
        print("  Space: Stop")
        print("  +: Increase speed")
        print("  -: Decrease speed")
        print("  ESC or Ctrl+C: Quit")
        print()
        print(f"Current speed: {self.linear_speed:.1f} m/s")
        print("=" * 60)
        print()
    
    def process_key(self, key: str):
        """
        Process keyboard input and control robot.
        
        Args:
            key: Key character
        """
        # Movement keys
        if key == 'w' or key == 'W':
            # Forward
            logger.info(f"Forward at {self.linear_speed} m/s")
            self.drive.drive_velocity(self.linear_speed, 0.0)
        
        elif key == 's' or key == 'S':
            # Backward
            logger.info(f"Backward at {self.linear_speed} m/s")
            self.drive.drive_velocity(-self.linear_speed, 0.0)
        
        elif key == 'a' or key == 'A':
            logger.info("Turn left (skid steer)")
            self.drive.set_motor_speeds(1.0, -1.0)

        elif key == 'd' or key == 'D':
            logger.info("Turn right (skid steer)")
            self.drive.set_motor_speeds(-1.0, 1.0)
        
        elif key == 'q' or key == 'Q':
            # Rotate left (in place)
            logger.info("Rotate left")
            self.drive.drive_velocity(0.0, self.angular_speed)
        
        elif key == 'e' or key == 'E':
            # Rotate right (in place)
            logger.info("Rotate right")
            self.drive.drive_velocity(0.0, -self.angular_speed)
        
        elif key == ' ':
            # Stop
            logger.info("STOP")
            self.drive.stop()
        
        # Speed control
        elif key == '+' or key == '=':
            self.linear_speed = min(1.0, self.linear_speed + self.speed_increment)
            logger.info(f"Speed increased to {self.linear_speed:.1f} m/s")
        
        elif key == '-' or key == '_':
            self.linear_speed = max(0.1, self.linear_speed - self.speed_increment)
            logger.info(f"Speed decreased to {self.linear_speed:.1f} m/s")
        
        # Quit
        elif key == '\x1b':  # ESC
            logger.info("ESC pressed - quitting")
            self.running = False
            self.drive.stop()
        
        elif key == '\x03':  # Ctrl+C
            logger.info("Ctrl+C pressed - quitting")
            self.running = False
            self.drive.stop()
    
    def run(self):
        """Main teleoperation loop."""
        self.print_instructions()
        
        logger.info("Waiting for keyboard input...")
        logger.info("Press any movement key to start")
        
        try:
            while self.running:
                key = self.get_key()
                self.process_key(key)
                
                # Small delay to prevent CPU overload
                time.sleep(0.05)
        
        except KeyboardInterrupt:
            logger.info("\nKeyboard interrupt")
        
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
    
    with KeyboardTeleop(config=cfg, simulate=False) as teleop:
        teleop.run()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())