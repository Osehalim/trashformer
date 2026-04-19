#!/usr/bin/env python3
"""
teleop/teleop_gamepad.py

Control robot with a gamepad using pygame.

Debug version using PS5 face buttons:
  Triangle: Forward
  Cross: Backward
  Square: Turn left
  Circle: Turn right
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

    Debug version that uses buttons instead of joysticks.
    """

    def __init__(self, config, simulate: bool = False):
        self.config = config
        self.simulate = simulate
        self.drive = DriveController(config=config, simulate=simulate)

        # Movement speed for button control
        self.move_speed = 0.3

        # Polling loop delay
        self.loop_delay = 0.05  # seconds

        # Running state
        self.running = True

        # Button mapping (common PS5 pygame mapping)
        self.cross_button = 0
        self.circle_button = 1
        self.triangle_button = 2
        self.square_button = 3
        self.start_button = 9   # sometimes Options/Start may vary

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
        logger.info(f"Buttons: {self.joystick.get_numbuttons()}")
        logger.info(f"Move speed: {self.move_speed}")

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

    def print_instructions(self) -> None:
        """
        Print controller instructions.
        """
        print("\n" + "=" * 60)
        print("GAMEPAD TELEOPERATION (BUTTON DEBUG MODE)")
        print("=" * 60)
        print()
        print(f"Connected controller: {self.joystick.get_name()}")
        print()
        print("Controls:")
        print("  Triangle: Forward")
        print("  Cross: Backward")
        print("  Square: Turn left")
        print("  Circle: Turn right")
        print("  Start / Options: Stop")
        print()
        print(f"Move speed: {self.move_speed:.2f}")
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
                pygame.event.pump()

                triangle = self.get_button_safe(self.triangle_button)
                cross = self.get_button_safe(self.cross_button)
                circle = self.get_button_safe(self.circle_button)
                square = self.get_button_safe(self.square_button)
                start = self.get_button_safe(self.start_button)

                if triangle:
                    logger.info("Forward")
                    self.drive.set_motor_speeds(self.move_speed, self.move_speed)

                elif cross:
                    logger.info("Backward")
                    self.drive.set_motor_speeds(-self.move_speed, -self.move_speed)

                elif square:
                    logger.info("Turn left")
                    self.drive.set_motor_speeds(self.move_speed, -self.move_speed)

                elif circle:
                    logger.info("Turn right")
                    self.drive.set_motor_speeds(-self.move_speed, self.move_speed)

                elif start:
                    logger.info("STOP")
                    self.drive.stop()

                else:
                    # No button pressed -> stop
                    self.drive.stop()

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