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
from typing import Optional, Tuple
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
            # Initialize dual RoboClaw motor controllers
            from drive.roboclaw_controller import DualRoboClawController
            
            port = config.get("drive.motor_controller.port", "/dev/ttyS0")
            baudrate = int(config.get("drive.motor_controller.baudrate", 38400))
            left_addr = int(config.get("drive.motor_controller.left_address", 0x80))
            right_addr = int(config.get("drive.motor_controller.right_address", 0x81))
            
            self.motor_controller = DualRoboClawController(
                port=port,
                baudrate=baudrate,
                left_address=left_addr,
                right_address=right_addr,
                simulate=False
            )
            logger.info("Dual RoboClaw motor controller initialized")
        else:
            logger.warning("DriveController running in SIMULATION mode")
        
        # State
        self.current_linear_speed = 0.0
        self.current_angular_speed = 0.0
        
        logger.info(f"DriveController initialized (wheel_dia={self.wheel_diameter}m, track={self.track_width}m)")
    
    def stop(self) -> None:
        """Stop all motors immediately."""
        logger.info("STOP")
        
        if self.simulate:
            logger.debug("[SIM] Motors stopped")
        else:
            # Send stop command to goBILDA motor controller
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
        # Clamp speeds
        left_speed = max(-1.0, min(1.0, left_speed))
        right_speed = max(-1.0, min(1.0, right_speed))
        
        if self.simulate:
            logger.debug(f"[SIM] Motors: L={left_speed:.2f}, R={right_speed:.2f}")
        else:
            # Send to goBILDA motor controller
            if self.motor_controller:
                self.motor_controller.set_motors(left_speed, right_speed)
    
    def forward(self, distance: float, speed: float = 0.3) -> None:
        """
        Drive forward a specific distance.
        
        Args:
            distance: Distance in meters
            speed: Speed in m/s (0.0 to max_linear_speed)
        """
        logger.info(f"Driving forward {distance:.2f}m at {speed:.2f}m/s")
        
        speed = min(speed, self.max_linear_speed)
        duration = distance / speed if speed > 0 else 0
        
        if self.simulate:
            logger.debug(f"[SIM] Forward for {duration:.2f}s")
            time.sleep(duration)
        else:
            # Set both motors to same speed
            motor_speed = speed / self.max_linear_speed  # Normalize to -1.0 to 1.0
            self.set_motor_speeds(motor_speed, motor_speed)
            time.sleep(duration)
            self.stop()
    
    def backward(self, distance: float, speed: float = 0.3) -> None:
        """
        Drive backward a specific distance.
        
        Args:
            distance: Distance in meters
            speed: Speed in m/s (0.0 to max_linear_speed)
        """
        logger.info(f"Driving backward {distance:.2f}m at {speed:.2f}m/s")
        
        speed = min(speed, self.max_linear_speed)
        duration = distance / speed if speed > 0 else 0
        
        if self.simulate:
            logger.debug(f"[SIM] Backward for {duration:.2f}s")
            time.sleep(duration)
        else:
            # Set both motors to negative speed
            motor_speed = -(speed / self.max_linear_speed)
            self.set_motor_speeds(motor_speed, motor_speed)
            time.sleep(duration)
            self.stop()
    
    def rotate(self, angle_degrees: float, speed: float = 30.0, pivot_style: str = "spin") -> None:
        """
        Rotate by a specific angle.
        
        Args:
            angle_degrees: Angle in degrees (positive = left/CCW, negative = right/CW)
            speed: Rotation speed in degrees/second
            pivot_style: "spin" (both sides move) or "pivot" (one side stationary)
        """
        logger.info(f"Rotating {angle_degrees:+.1f}° at {speed:.1f}°/s (style={pivot_style})")
        
        # Calculate duration
        duration = abs(angle_degrees) / speed if speed > 0 else 0
        
        # Determine direction
        direction = 1 if angle_degrees > 0 else -1
        
        if self.simulate:
            logger.debug(f"[SIM] Rotate for {duration:.2f}s")
            time.sleep(duration)
        else:
            motor_speed = 0.3  # Base rotation speed
            
            if pivot_style == "pivot":
                # Pivot turn: One side stationary, other side moves
                # Turn left: right motors forward, left motors stationary
                # Turn right: left motors forward, right motors stationary
                if direction > 0:  # Turn left
                    self.set_motor_speeds(0.0, motor_speed)  # Left=0, Right=forward
                else:  # Turn right
                    self.set_motor_speeds(motor_speed, 0.0)  # Left=forward, Right=0
            else:  # "spin"
                # Spin turn: Both sides move opposite directions
                # Turn left: left reverse, right forward
                # Turn right: left forward, right reverse
                self.set_motor_speeds(-motor_speed * direction, motor_speed * direction)
            
            time.sleep(duration)
            self.stop()
    
    def turn_left(self, angle_degrees: float, speed: float = 30.0) -> None:
        """Turn left (counterclockwise)."""
        self.rotate(abs(angle_degrees), speed)
    
    def turn_right(self, angle_degrees: float, speed: float = 30.0) -> None:
        """Turn right (clockwise)."""
        self.rotate(-abs(angle_degrees), speed)
    
    def arc_turn(self, radius: float, angle_degrees: float, speed: float = 0.2) -> None:
        """
        Drive in an arc (curved path).
        
        Args:
            radius: Turn radius in meters
            angle_degrees: Angle to turn through
            speed: Linear speed in m/s
        """
        logger.info(f"Arc turn: radius={radius:.2f}m, angle={angle_degrees:.1f}°")
        
        # Calculate arc length
        import math
        arc_length = abs(radius * math.radians(angle_degrees))
        
        # Calculate differential motor speeds
        # Inner wheel slower, outer wheel faster
        if angle_degrees > 0:  # Left turn
            left_radius = radius - (self.track_width / 2)
            right_radius = radius + (self.track_width / 2)
        else:  # Right turn
            left_radius = radius + (self.track_width / 2)
            right_radius = radius - (self.track_width / 2)
        
        # Speed ratio
        left_speed = speed * (left_radius / radius)
        right_speed = speed * (right_radius / radius)
        
        # Duration
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
        """
        Drive with velocity control (continuous).
        
        Args:
            linear: Linear velocity in m/s (forward/backward)
            angular: Angular velocity in rad/s (rotation)
        """
        # Convert to differential drive
        # v_left = linear - (angular * track_width / 2)
        # v_right = linear + (angular * track_width / 2)
        
        v_left = linear - (angular * self.track_width / 2)
        v_right = linear + (angular * self.track_width / 2)
        
        # Normalize to motor speed range
        left_motor = v_left / self.max_linear_speed
        right_motor = v_right / self.max_linear_speed
        
        # Clamp
        left_motor = max(-1.0, min(1.0, left_motor))
        right_motor = max(-1.0, min(1.0, right_motor))
        
        if self.simulate:
            logger.debug(f"[SIM] Velocity: linear={linear:.2f}, angular={angular:.2f}")
        else:
            self.set_motor_speeds(left_motor, right_motor)
        
        self.current_linear_speed = linear
        self.current_angular_speed = angular
    
    def close(self) -> None:
        """Clean up and stop motors."""
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
        
        # Test movements
        drive.forward(1.0, speed=0.3)
        drive.rotate(90)
        drive.forward(0.5, speed=0.3)
        drive.rotate(-90)
        drive.backward(0.5, speed=0.3)
        
        logger.info("Simulation test complete")