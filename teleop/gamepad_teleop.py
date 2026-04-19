#!/usr/bin/env python3
"""
teleop/teleop_gamepad.py

Control robot with a gamepad using pygame.

Supports USB and Bluetooth controllers that appear as joystick devices.
Works well with PlayStation DualSense / PS5 controllers on Raspberry Pi.

Controls:
  Left stick: Drive forward/backward + turn
  Right stick X: Rotate in place
  Cross / A: Stop
  Options / Start: Quit

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

    Continuously reads joystick input and controls the robot.
    """

    def __init__(self, config, simulate: bool = False):
        self.config = config
        self.simulate = simulate
        self.drive = DriveController(config=config, simulate=simulate)

        # Control settings
        self.max_linear_speed = 0.5   # m/s
        self.max_angular_speed = 1.0  # rad/s
        self.deadzone = 0.15

        # Polling loop delay
        self.loop_delay = 0.05  # seconds

        # Running state
        self.running = True

        # Joystick state
        self.left_stick_x = 0.0
        self.left_stick_y = 0.0
        self.right_stick_x = 0.0

        # Button mapping
        # These are common defaults for PS5 / many controllers in pygame,
        # but may vary slightly depending on system/controller.
        self.stop_button = 0     # Cross / A
        self.quit_button = 9     # Options / Start

        # Initialize pygame + joystick
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
        logger.info(f"Max linear speed: {self.max_linear_speed} m/s")
        logger.info(f"Max angular speed: {self.max_angular_speed} rad/s")

    def apply_deadzone(self, value: float) -> float:
        """
        Apply deadzone to joystick value.

        Args:
            value: Raw joystick value (-1.0 to 1.0)

        Returns:
            Value with deadzone applied
        """
        if abs(value) < self.deadzone:
            return 0.0

        if value > 0:
            return (value - self.deadzone) / (1.0 - self.deadzone)
        return (value + self.deadzone) / (1.0 - self.deadzone)

    def get_axis_safe(self, axis_index: int) -> float:
        """
        Safely read a joystick axis.

        Args:
            axis_index: Axis number

        Returns:
            Axis value, or 0.0 if axis does not exist
        """
        if axis_index < self.joystick.get_numaxes():
            return self.joystick.get_axis(axis_index)
        return 0.0

    def get_button_safe(self, button_index: int) -> int:
        """
        Safely read a joystick button.

        Args:
            button_index: Button number

        Returns:
            Button state, or 0 if button does not exist
        """
        if button_index < self.joystick.get_numbuttons():
            return self.joystick.get_button(button_index)
        return 0

    def read_controller(self) -> None:
        """
        Read current controller state.

        Typical pygame mapping for PS5 controller:
          axis 0 = left stick X
          axis 1 = left stick Y
          axis 2 or 3 = right stick X depending on setup

        We try axis 2 first, then fall back to axis 3 if needed.
        """
        pygame.event.pump()

        self.left_stick_x = self.get_axis_safe(0)
        self.left_stick_y = -self.get_axis_safe(1)  # invert so stick up = forward

        # Try common right-stick X mappings
        right_x_axis_2 = self.get_axis_safe(2)
        right_x_axis_3 = self.get_axis_safe(3)

        # Use whichever has larger magnitude
        if abs(right_x_axis_3) > abs(right_x_axis_2):
            self.right_stick_x = right_x_axis_3
        else:
            self.right_stick_x = right_x_axis_2

    def update_motors(self) -> None:
        """
        Update motor commands from current stick positions.
        """
        forward = self.apply_deadzone(self.left_stick_y)
        turn = self.apply_deadzone(self.left_stick_x)
        rotate = self.apply_deadzone(self.right_stick_x)

        # Right stick rotation gets priority for in-place rotate
        if abs(rotate) > 0.05:
            linear = 0.0
            angular = rotate * self.max_angular_speed
        else:
            linear = forward * self.max_linear_speed
            angular = turn * self.max_angular_speed

        self.drive.drive_velocity(linear, angular)

    def print_instructions(self) -> None:
        """
        Print controller instructions.
        """
        print("\n" + "=" * 60)
        print("GAMEPAD TELEOPERATION")
        print("=" * 60)
        print()
        print(f"Connected controller: {self.joystick.get_name()}")
        print()
        print("Controls:")
        print("  Left stick: Drive and turn")
        print("  Right stick X: Rotate in place")
        print("  Cross / A: Stop")
        print("  Options / Start: Quit")
        print()
        print(f"Max linear speed:  {self.max_linear_speed:.2f} m/s")
        print(f"Max angular speed: {self.max_angular_speed:.2f} rad/s")
        print("=" * 60)
        print()

    def run(self) -> None:
        """
        Main teleoperation loop.
        """
        self.print_instructions()
        logger.info("Waiting for gamepad input...")

        try:
            while self.running:
                self.read_controller()

                stop_pressed = self.get_button_safe(self.stop_button)
                quit_pressed = self.get_button_safe(self.quit_button)

                if stop_pressed:
                    logger.info("Stop button pressed")
                    self.drive.stop()
                    time.sleep(0.1)
                    continue

                if quit_pressed:
                    logger.info("Quit button pressed")
                    self.running = False
                    break

                self.update_motors()
                time.sleep(self.loop_delay)

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt")

        except Exception as e:
            logger.error(f"Gamepad error: {e}")

        finally:
            self.cleanup()

    def cleanup(self) -> None:
        """
        Stop motors and clean up.
        """
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