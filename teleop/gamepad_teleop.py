#!/usr/bin/env python3
"""
teleop/gamepad_teleop.py

Control robot with a gamepad using pygame.

PS5 controller mapping on this Raspberry Pi:
  Left stick X: axis 0
  Left stick Y: axis 1
  Right stick X: axis 3
  Right stick Y: axis 4

Controls:
  Left stick: Drive forward/backward + turn
  Right stick X: Rotate in place
  R1: Increase speed (+0.1 m/s)
  L1: Decrease speed (-0.1 m/s)
  Cross (X): Run pickup sequence
  Triangle: Forward (backup/debug)
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
        
        # Initialize arm (lazy loading)
        self.arm = None

        # Speed settings
        self.current_speed = 0.5      # Start at 0.5 m/s
        self.min_speed = 0.1          # Minimum speed
        self.max_speed = 1.0          # Maximum speed
        self.speed_increment = 0.1    # Speed change per button press
        
        self.max_angular_speed = 1.0   # rad/s
        self.button_turn_speed = 0.50
        self.deadzone = 0.05
        self.loop_delay = 0.05

        self.running = True
        
        # Button press tracking (for single press detection)
        self.r1_was_pressed = False
        self.l1_was_pressed = False
        self.cross_was_pressed = False

        # Button mapping for PS5 controller
        self.cross_button = 0        # X button
        self.circle_button = 1
        self.triangle_button = 2
        self.square_button = 3
        self.l1_button = 4
        self.r1_button = 5
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
        logger.info(f"Starting speed: {self.current_speed:.1f} m/s")

    def initialize_arm(self):
        """Lazy load arm controller when needed."""
        if self.arm is None:
            try:
                from arm.arm_controller import ArmController
                self.arm = ArmController(config=self.config, simulate=self.simulate)
                logger.info("✓ Arm initialized")
            except Exception as e:
                logger.error(f"Failed to initialize arm: {e}")
                self.arm = None

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

    def increase_speed(self):
        """Increase speed by 0.1 m/s."""
        old_speed = self.current_speed
        self.current_speed = min(self.current_speed + self.speed_increment, self.max_speed)
        if old_speed != self.current_speed:
            logger.info(f"Speed increased: {self.current_speed:.1f} m/s")
            print(f">>> Speed: {self.current_speed:.1f} m/s")

    def decrease_speed(self):
        """Decrease speed by 0.1 m/s."""
        old_speed = self.current_speed
        self.current_speed = max(self.current_speed - self.speed_increment, self.min_speed)
        if old_speed != self.current_speed:
            logger.info(f"Speed decreased: {self.current_speed:.1f} m/s")
            print(f">>> Speed: {self.current_speed:.1f} m/s")

    def run_pickup_sequence(self):
        """
        Execute complete pickup sequence:
        1. Gripper open (ready to pickup)
        2. Gripper close (grab object)
        3. Shoulder servo up
        4. Elbow servo right
        5. Gripper open (drop object)
        6. Elbow back to 0
        7. Shoulder down
        """
        logger.info("Starting pickup sequence...")
        print("\n" + "="*60)
        print("PICKUP SEQUENCE INITIATED")
        print("="*60)
        
        # Stop driving during pickup
        self.drive.stop()
        
        # Initialize arm if needed
        self.initialize_arm()
        
        if self.arm is None:
            logger.error("Arm not available - cannot run pickup sequence")
            print("ERROR: Arm system not initialized!")
            return
        
        try:
            # Step 1: Open gripper (ready to pickup)
            print("Step 1: Opening gripper...")
            logger.info("Pickup sequence: Opening gripper")
            self.arm.gripper_open()
            time.sleep(1.0)
            
            # Step 2: Close gripper (grab object)
            print("Step 2: Closing gripper (grabbing)...")
            logger.info("Pickup sequence: Closing gripper")
            self.arm.gripper_close()
            time.sleep(1.5)
            
            # Step 3: Shoulder up
            print("Step 3: Lifting (shoulder up)...")
            logger.info("Pickup sequence: Shoulder up")
            self.arm.move_shoulder(120)  # 120° up (adjust as needed)
            time.sleep(1.5)
            
            # Step 4: Elbow right (rotate to drop zone)
            print("Step 4: Moving elbow right...")
            logger.info("Pickup sequence: Elbow right")
            self.arm.move_elbow(90)  # Full right to drop zone
            time.sleep(1.5)
            
            # Step 5: Open gripper (drop object)
            print("Step 5: Opening gripper (dropping)...")
            logger.info("Pickup sequence: Opening gripper to drop")
            self.arm.gripper_open()
            time.sleep(1.0)
            
            # Step 6: Elbow back to center (0)
            print("Step 6: Returning elbow to center...")
            logger.info("Pickup sequence: Elbow to 0")
            self.arm.move_elbow(0)
            time.sleep(1.5)
            
            # Step 7: Shoulder down
            print("Step 7: Lowering (shoulder down)...")
            logger.info("Pickup sequence: Shoulder down")
            self.arm.move_shoulder(0)
            time.sleep(1.5)
            
            print("="*60)
            print("PICKUP SEQUENCE COMPLETE!")
            print("="*60 + "\n")
            logger.info("✓ Pickup sequence complete")
            
        except Exception as e:
            logger.error(f"Pickup sequence failed: {e}")
            print(f"ERROR: Pickup sequence failed - {e}")

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
        print("Speed control:")
        print("  R1: Increase speed (+0.1 m/s)")
        print("  L1: Decrease speed (-0.1 m/s)")
        print(f"  Current speed: {self.current_speed:.1f} m/s")
        print()
        print("Action buttons:")
        print("  Cross (X): Run pickup sequence")
        print()
        print("Button controls (backup/debug):")
        print("  Triangle: Forward")
        print("  Square: Turn left")
        print("  Circle: Turn right")
        print("  Start / Options: Stop")
        print()
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
            left_motor = -rotate * self.current_speed
            right_motor = rotate * self.current_speed
        else:
            # Normal driving - combine forward and turn
            # Forward: both motors same speed
            # Turn: differential speed between left and right
            left_motor = (forward - turn) * self.current_speed
            right_motor = (forward + turn) * self.current_speed
        
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

                # Read all buttons
                triangle = self.get_button_safe(self.triangle_button)
                cross = self.get_button_safe(self.cross_button)
                circle = self.get_button_safe(self.circle_button)
                square = self.get_button_safe(self.square_button)
                start = self.get_button_safe(self.start_button)
                r1 = self.get_button_safe(self.r1_button)
                l1 = self.get_button_safe(self.l1_button)

                # Speed control (single press detection)
                if r1 and not self.r1_was_pressed:
                    self.increase_speed()
                self.r1_was_pressed = r1

                if l1 and not self.l1_was_pressed:
                    self.decrease_speed()
                self.l1_was_pressed = l1

                # Pickup sequence (single press detection)
                if cross and not self.cross_was_pressed:
                    self.run_pickup_sequence()
                self.cross_was_pressed = cross

                # Stop button always has priority
                if start:
                    logger.info("STOP")
                    self.drive.stop()
                    time.sleep(0.1)
                    continue

                # Check if any debug buttons are pressed
                any_button_pressed = triangle or square or circle

                # Backup/debug button controls (only if pressed)
                if any_button_pressed:
                    if triangle:
                        self.drive.set_motor_speeds(self.button_turn_speed, self.button_turn_speed)
                    elif square:
                        self.drive.set_motor_speeds(self.button_turn_speed, -self.button_turn_speed)
                    elif circle:
                        self.drive.set_motor_speeds(-self.button_turn_speed, self.button_turn_speed)
                else:
                    # Normal stick control - ALWAYS runs when no buttons pressed
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
        
        if self.arm:
            self.arm.close()
        
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