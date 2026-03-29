"""
drive/drive_controller.py - Basic robot drive control

Controls robot movement using motor controller.
Supports differential drive (left/right motors).

Hardware:
- Motor controller (e.g., Sabertooth, Roboclaw, L298N)
- 2 motors (left and right)
- Wheel encoders (optional, for odometry)
"""

from __future__ import annotations

import time
from utils.logger import get_logger

logger = get_logger(__name__)


class DriveController:
    """
    Basic differential drive controller.

    Controls robot movement: forward, backward, turning, rotation.
    """

    def __init__(self, config, simulate: bool = False):
        self.config = config
        self.simulate = simulate

        # Get configuration
        self.wheel_diameter = float(config.get("drive.wheel_diameter", 0.15))  # meters
        self.track_width = float(config.get("drive.track_width", 0.30))  # meters
        self.max_linear_speed = float(config.get("drive.max_linear_speed", 1.0))  # m/s
        self.max_angular_speed = float(config.get("drive.max_angular_speed", 2.0))  # rad/s

        # Motor controller - Dual RoboClaw (left and right tracks)
        self.motor_controller = None

        if not simulate:
            from drive.roboclaw_controller import DualRoboClawController

            controller_mode = str(config.get("drive.motor_controller.mode", "usb")).lower().strip()
            baudrate = int(config.get("drive.motor_controller.baudrate", 38400))
            left_addr = int(config.get("drive.motor_controller.left_address", 0x80))
            right_addr = int(config.get("drive.motor_controller.right_address", 0x80))

            # USB defaults
            left_port = config.get("drive.motor_controller.left_port", "/dev/ttyACM0")
            right_port = config.get("drive.motor_controller.right_port", "/dev/ttyACM1")

            # UART fallback/defaults
            port = config.get("drive.motor_controller.port", "/dev/ttyAMA0")

            self.motor_controller = DualRoboClawController(
                mode=controller_mode,
                port=port,
                left_port=left_port,
                right_port=right_port,
                baudrate=baudrate,
                left_address=left_addr,
                right_address=right_addr,
                simulate=False,
            )
            logger.info(f"Dual RoboClaw motor controller initialized in {controller_mode.upper()} mode")
        else:
            logger.warning("DriveController running in SIMULATION mode")

        self.current_linear_speed = 0.0
        self.current_angular_speed = 0.0

        logger.info(f"DriveController initialized (wheel_dia={self.wheel_diameter}m, track={self.track_width}m)")

    def stop(self) -> None:
        """Stop all motors immediately."""
        logger.info("STOP")

        if self.simulate:
            logger.debug("[SIM] Motors stopped")
        else:
            if self.motor_controller:
                self.motor_controller.stop()

        self.current_linear_speed = 0.0
        self.current_angular_speed = 0.0

    def set_motor_speeds(self, left_speed: float, right_speed: float) -> None:
        """
        Set individual motor speeds.

        Args:
            left_speed: -1.0 to 1.0 (negative = backward)
            right_speed: -1.0 to 1.0 (negative = backward)
        """
        left_speed = max(-1.0, min(1.0, left_speed))
        right_speed = max(-1.0, min(1.0, right_speed))

        if self.simulate:
            logger.debug(f"[SIM] Motors: L={left_speed:.2f}, R={right_speed:.2f}")
        else:
            if self.motor_controller:
                self.motor_controller.set_motors(left_speed, right_speed)

    def forward(self, distance: float, speed: float = 0.3) -> None:
        logger.info(f"Driving forward {distance:.2f}m at {speed:.2f}m/s")

        speed = min(speed, self.max_linear_speed)
        duration = distance / speed if speed > 0 else 0

        if self.simulate:
            logger.debug(f"[SIM] Forward for {duration:.2f}s")
            time.sleep(duration)
        else:
            motor_speed = speed / self.max_linear_speed
            self.set_motor_speeds(motor_speed, motor_speed)
            time.sleep(duration)
            self.stop()

    def backward(self, distance: float, speed: float = 0.3) -> None:
        logger.info(f"Driving backward {distance:.2f}m at {speed:.2f}m/s")

        speed = min(speed, self.max_linear_speed)
        duration = distance / speed if speed > 0 else 0

        if self.simulate:
            logger.debug(f"[SIM] Backward for {duration:.2f}s")
            time.sleep(duration)
        else:
            motor_speed = -(speed / self.max_linear_speed)
            self.set_motor_speeds(motor_speed, motor_speed)
            time.sleep(duration)
            self.stop()

    def rotate(self, angle_degrees: float, speed: float = 30.0, pivot_style: str = "spin") -> None:
        logger.info(f"Rotating {angle_degrees:+.1f}° at {speed:.1f}°/s (style={pivot_style})")

        duration = abs(angle_degrees) / speed if speed > 0 else 0
        direction = 1 if angle_degrees > 0 else -1

        if self.simulate:
            logger.debug(f"[SIM] Rotate for {duration:.2f}s")
            time.sleep(duration)
        else:
            motor_speed = 0.3

            if pivot_style == "pivot":
                if direction > 0:
                    self.set_motor_speeds(0.0, motor_speed)
                else:
                    self.set_motor_speeds(motor_speed, 0.0)
            else:
                self.set_motor_speeds(-motor_speed * direction, motor_speed * direction)

            time.sleep(duration)
            self.stop()

    def turn_left(self, angle_degrees: float, speed: float = 30.0) -> None:
        self.rotate(abs(angle_degrees), speed)

    def turn_right(self, angle_degrees: float, speed: float = 30.0) -> None:
        self.rotate(-abs(angle_degrees), speed)

    def arc_turn(self, radius: float, angle_degrees: float, speed: float = 0.2) -> None:
        logger.info(f"Arc turn: radius={radius:.2f}m, angle={angle_degrees:.1f}°")

        import math
        arc_length = abs(radius * math.radians(angle_degrees))

        if angle_degrees > 0:
            left_radius = radius - (self.track_width / 2)
            right_radius = radius + (self.track_width / 2)
        else:
            left_radius = radius + (self.track_width / 2)
            right_radius = radius - (self.track_width / 2)

        left_speed = speed * (left_radius / radius)
        right_speed = speed * (right_radius / radius)
        duration = arc_length / speed if speed > 0 else 0

        if self.simulate:
            logger.debug(f"[SIM] Arc turn for {duration:.2f}s")
            time.sleep(duration)
        else:
            left_motor = left_speed / self.max_linear_speed
            right_motor = right_speed / self.max_linear_speed
            self.set_motor_speeds(left_motor, right_motor)
            time.sleep(duration)
            self.stop()

    def drive_velocity(self, linear: float, angular: float) -> None:
        v_left = linear - (angular * self.track_width / 2)
        v_right = linear + (angular * self.track_width / 2)

        left_motor = v_left / self.max_linear_speed
        right_motor = v_right / self.max_linear_speed

        left_motor = max(-1.0, min(1.0, left_motor))
        right_motor = max(-1.0, min(1.0, right_motor))

        if self.simulate:
            logger.debug(f"[SIM] Velocity: linear={linear:.2f}, angular={angular:.2f}")
        else:
            self.set_motor_speeds(left_motor, right_motor)

        self.current_linear_speed = linear
        self.current_angular_speed = angular

    def close(self) -> None:
        logger.info("Closing DriveController")
        self.stop()

        if self.motor_controller:
            self.motor_controller.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __repr__(self) -> str:
        return f"DriveController(wheel={self.wheel_diameter}m, track={self.track_width}m)"


if __name__ == "__main__":
    from utils.logger import setup_logging
    from utils.config_loader import load_config

    setup_logging()

    logger.info("Testing DriveController (simulation)")
    cfg = load_config("config/default.yaml")

    with DriveController(config=cfg, simulate=True) as drive:
        logger.info(f"{drive}")

        drive.forward(1.0, speed=0.3)
        drive.rotate(90)
        drive.forward(0.5, speed=0.3)
        drive.rotate(-90)
        drive.backward(0.5, speed=0.3)

        logger.info("Simulation test complete")