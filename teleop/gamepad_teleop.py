#!/usr/bin/env python3
"""
teleop/teleop_gamepad.py

Control robot with a gamepad using pygame.

PS5 controller mapping on this Raspberry Pi:
  Left stick X: axis 0
  Left stick Y: axis 1
  Right stick X: axis 3
  Right stick Y: axis 4

Controls:
  Left stick: Drive forward/backward + turn
  Right stick X: Rotate in place
  Triangle: Forward (backup/debug)
  Cross: Backward (backup/debug)
  Square: Turn left (backup/debug)
  Circle: Turn right (backup/debug)
  Start / Options: Stop

Usage:
  python3 teleop_gamepad.py
"""

from __future__ import annotations

import time
import pygame
from utils.logger import setup_logging, get_logger
from utils.config_loader import load_config
from drive.drive_controller import DriveController

logger = get_logger(__name__)


class GamepadTeleop:
    """
    Gamepad teleoperation using pygame.
    """

    def __init__(self, config, simulate: bool = False):
        self.config = config
        self.simulate = simulate
        self.drive = DriveController(config=config, simulate=simulate)

        # Speed settings
        self.max_linear_speed = 1.0   # m/s
        self.max_angular_speed = 1.0   # rad/s
        self.button_turn_speed = 0.50
        self.deadzone = 0.25
        self.loop_delay = 0.05

        self.running = True

        # Button mapping for PS5 controller
        self.cross_button = 0
        self.circle_button = 1
        self.triangle_button = 2
        self.square_button = 3
        self.start_button = 9   # if this doesn't work, try 10

        pygame.init()
        pygame.joystick.init()

        joystick_count = pygame.joystick.get_count()
        if joystick_count == 0:
            raise RuntimeError("No joystick found")

        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

        logger.info("Gamepad teleop initialized")
        logger.info(f"Connected joystick: {self.joystick.get_name()}")
        logger.info(f"Axes: {self.joystick.get_numaxes()}, Buttons: {self.joystick.get_numbuttons()}")

    def apply_deadzone(self, value: float) -> float:
        if abs(value) < self.deadzone:
            return 0.0
        if value > 0:
            return (value - self.deadzone) / (1.0 - self.deadzone)
        return (value + self.deadzone) / (1.0 - self.deadzone)

    def get_axis_safe(self, axis_index: int) -> float:
        if axis_index < self.joystick.get_numaxes():
            return self.joystick.get_axis(axis_index)
        return 0.0

    def get_button_safe(self, button_index: int) -> int:
        if button_index < self.joystick.get_numbuttons():
            return self.joystick.get_button(button_index)
        return 0

    def print_instructions(self) -> None:
        print("\n" + "=" * 60)
        print("GAMEPAD TELEOPERATION")
        print("=" * 60)
        print()
        print(f"Connected controller: {self.joystick.get_name()}")
        print()
        print("Stick controls:")
        print("  Left stick: Drive and turn")
        print("  Right stick X: Rotate in place")
        print()
        print("Button controls (backup/debug):")
        print("  Triangle: Forward")
        print("  Cross: Backward")
        print("  Square: Turn left")
        print("  Circle: Turn right")
        print("  Start / Options: Stop")
        print()
        print(f"Max linear speed:  {self.max_linear_speed:.2f} m/s")
        print(f"Max angular speed: {self.max_angular_speed:.2f} rad/s")
        print("=" * 60)
        print()

    def update_motors_from_sticks(self) -> None:
        # Confirmed mapping for your controller
        left_x = self.get_axis_safe(0)      # Left stick left/right
        left_y = -self.get_axis_safe(1)     # Left stick up/down (inverted)
        right_x = self.get_axis_safe(3)     # Right stick left/right

        # Apply deadzones
        forward = self.apply_deadzone(left_y)    # Forward/backward
        turn = self.apply_deadzone(left_x)       # Turn left/right
        rotate = self.apply_deadzone(right_x)    # Rotate in place

        # Right stick rotation gets priority
        if abs(rotate) > 0.05:
            # Pure rotation - both motors opposite directions
            left_motor = -rotate
            right_motor = rotate
        else:
            # Normal driving - combine forward and turn
            # Forward: both motors same speed
            # Turn: differential speed between left and right
            left_motor = forward - turn
            right_motor = forward + turn
        
        # Clamp to -1.0 to 1.0
        left_motor = max(-1.0, min(1.0, left_motor))
        right_motor = max(-1.0, min(1.0, right_motor))
        
        # Send to motors
        self.drive.set_motor_speeds(left_motor, right_motor)

    def run(self) -> None:
        self.print_instructions()
        logger.info("Waiting for gamepad input...")

        try:
            while self.running:
                pygame.event.pump()

                triangle = self.get_button_safe(self.triangle_button)
                cross = self.get_button_safe(self.cross_button)
                circle = self.get_button_safe(self.circle_button)
                square = self.get_button_safe(self.square_button)
                start = self.get_button_safe(self.start_button)

                # Stop button always has priority
                if start:
                    logger.info("STOP")
                    self.drive.stop()
                    time.sleep(0.1)
                    continue

                # Backup/debug button controls
                if triangle:
                    self.drive.set_motor_speeds(self.button_turn_speed, self.button_turn_speed)

                elif cross:
                    self.drive.set_motor_speeds(-self.button_turn_speed, -self.button_turn_speed)

                elif square:
                    self.drive.set_motor_speeds(self.button_turn_speed, -self.button_turn_speed)

                elif circle:
                    self.drive.set_motor_speeds(-self.button_turn_speed, self.button_turn_speed)

                else:
                    # Normal stick control
                    self.update_motors_from_sticks()

                time.sleep(self.loop_delay)

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt")

        except Exception as e:
            logger.error(f"Gamepad error: {e}")

        finally:
            self.cleanup()

    def cleanup(self) -> None:
        logger.info("Cleaning up...")
        self.drive.stop()
        self.drive.close()
        pygame.quit()
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