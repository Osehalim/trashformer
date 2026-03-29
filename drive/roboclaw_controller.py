"""
drive/roboclaw_controller.py - RoboClaw Motor Controller Driver

For dual RoboClaw setup:
- RoboClaw 1: Controls left tracks (2 motors)
- RoboClaw 2: Controls right tracks (2 motors)

Communication:
- USB mode: one USB serial device per RoboClaw (recommended)
- UART mode: one shared serial bus with unique controller addresses
"""

from __future__ import annotations

import os
import time
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

try:
    from drive.roboclaw import Roboclaw
    ROBOCLAW_AVAILABLE = True
except ImportError:
    try:
        from roboclaw import Roboclaw
        ROBOCLAW_AVAILABLE = True
    except ImportError:
        ROBOCLAW_AVAILABLE = False
        logger.warning("roboclaw library not available")


class DualRoboClawController:
    """
    Controller for dual RoboClaw setup (left and right tracks).
    
    Now supports motor inversion for backwards-wired motors!
    """

    def __init__(
        self,
        port: str = "/dev/ttyAMA0",
        baudrate: int = 38400,
        left_address: int = 0x80,
        right_address: int = 0x81,
        simulate: bool = False,
        mode: str = "usb",
        left_port: str = "/dev/ttyACM0",
        right_port: str = "/dev/ttyACM1",
        invert_left_m1: bool = False,   # Front left motor
        invert_left_m2: bool = True,    # Rear left motor (INVERTED!)
        invert_right_m1: bool = False,  # Front right motor
        invert_right_m2: bool = True,   # Rear right motor (INVERTED!)
    ):
        self.port = port
        self.baudrate = baudrate
        self.left_address = left_address
        self.right_address = right_address
        self.mode = str(mode).lower().strip()
        self.left_port = left_port
        self.right_port = right_port
        self.simulate = simulate or (not ROBOCLAW_AVAILABLE)
        
        # Motor inversions
        self.invert_left_m1 = invert_left_m1
        self.invert_left_m2 = invert_left_m2
        self.invert_right_m1 = invert_right_m1
        self.invert_right_m2 = invert_right_m2

        self.rc: Optional[Roboclaw] = None
        self.rc_left: Optional[Roboclaw] = None
        self.rc_right: Optional[Roboclaw] = None

        if self.simulate:
            logger.warning("RoboClaw controller running in SIMULATION mode")
            return

        try:
            if self.mode == "usb":
                self._init_usb()
            elif self.mode == "uart":
                self._init_uart()
            else:
                raise ValueError(f"Unsupported RoboClaw mode: {self.mode}")
        except Exception as e:
            logger.error(f"Failed to initialize RoboClaw: {e}")
            logger.warning("Falling back to simulation mode")
            self.simulate = True

    def _open_controller(self, port: str) -> Roboclaw:
        controller = Roboclaw(port, self.baudrate)
        controller.Open()
        return controller

    def _controller_exists(self, port: str) -> bool:
        return os.path.exists(port)

    def _init_usb(self) -> None:
        if not self._controller_exists(self.left_port):
            raise FileNotFoundError(f"Left RoboClaw USB port not found: {self.left_port}")
        if not self._controller_exists(self.right_port):
            raise FileNotFoundError(f"Right RoboClaw USB port not found: {self.right_port}")

        self.rc_left = self._open_controller(self.left_port)
        self.rc_right = self._open_controller(self.right_port)

        left_version = self.rc_left.ReadVersion(self.left_address)
        right_version = self.rc_right.ReadVersion(self.right_address)

        if left_version[0]:
            logger.info(f"✓ Left RoboClaw: {left_version[1]}")
        if right_version[0]:
            logger.info(f"✓ Right RoboClaw: {right_version[1]}")
        
        logger.info(f"Motor inversions: L_M1={self.invert_left_m1}, L_M2={self.invert_left_m2}, R_M1={self.invert_right_m1}, R_M2={self.invert_right_m2}")

    def _init_uart(self) -> None:
        if not self._controller_exists(self.port):
            raise FileNotFoundError(f"UART RoboClaw port not found: {self.port}")

        self.rc = self._open_controller(self.port)
        left_version = self.rc.ReadVersion(self.left_address)
        right_version = self.rc.ReadVersion(self.right_address)

        if left_version[0]:
            logger.info(f"✓ Left RoboClaw: {left_version[1]}")
        if right_version[0]:
            logger.info(f"✓ Right RoboClaw: {right_version[1]}")

    def _speed_to_duty(self, speed: float) -> int:
        """Convert speed (-1.0 to 1.0) to duty cycle (0-127)."""
        speed = max(-1.0, min(1.0, float(speed)))
        return int(abs(speed) * 127)

    def _set_motor(self, controller: Optional[Roboclaw], address: int, 
                   motor_num: int, speed: float, invert: bool) -> None:
        """Set a single motor with optional inversion."""
        if self.simulate or not controller:
            return
        
        # Apply inversion if needed
        if invert:
            speed = -speed
        
        duty = self._speed_to_duty(speed)
        
        if motor_num == 1:
            if speed >= 0:
                controller.ForwardM1(address, duty)
            else:
                controller.BackwardM1(address, duty)
        else:  # motor_num == 2
            if speed >= 0:
                controller.ForwardM2(address, duty)
            else:
                controller.BackwardM2(address, duty)

    def set_left_motors(self, speed: float) -> None:
        """Set left track motors (M1=front, M2=rear)."""
        controller = self.rc_left if self.mode == "usb" else self.rc
        
        if self.simulate:
            logger.debug(f"[SIM] Left motors: {speed:.2f}")
            return
        
        # Set M1 (front left) and M2 (rear left) with their inversion flags
        self._set_motor(controller, self.left_address, 1, speed, self.invert_left_m1)
        self._set_motor(controller, self.left_address, 2, speed, self.invert_left_m2)

    def set_right_motors(self, speed: float) -> None:
        """Set right track motors (M1=front, M2=rear)."""
        controller = self.rc_right if self.mode == "usb" else self.rc
        
        if self.simulate:
            logger.debug(f"[SIM] Right motors: {speed:.2f}")
            return
        
        # Set M1 (front right) and M2 (rear right) with their inversion flags
        self._set_motor(controller, self.right_address, 1, speed, self.invert_right_m1)
        self._set_motor(controller, self.right_address, 2, speed, self.invert_right_m2)

    def set_motors(self, left_speed: float, right_speed: float) -> None:
        """Set both left and right motors."""
        self.set_left_motors(left_speed)
        self.set_right_motors(right_speed)

    def stop(self) -> None:
        """Stop all motors."""
        logger.debug("Stopping all motors")
        
        if self.simulate:
            return
        
        if self.mode == "usb":
            if self.rc_left:
                self.rc_left.ForwardM1(self.left_address, 0)
                self.rc_left.ForwardM2(self.left_address, 0)
            if self.rc_right:
                self.rc_right.ForwardM1(self.right_address, 0)
                self.rc_right.ForwardM2(self.right_address, 0)
        else:
            if self.rc:
                self.rc.ForwardM1(self.left_address, 0)
                self.rc.ForwardM2(self.left_address, 0)
                self.rc.ForwardM1(self.right_address, 0)
                self.rc.ForwardM2(self.right_address, 0)

    def read_encoders(self) -> dict:
        """Read encoder values from both RoboClaws."""
        if self.simulate:
            return {"left_m1": 0, "left_m2": 0, "right_m1": 0, "right_m2": 0}
        
        try:
            if self.mode == "usb":
                left_m1 = self.rc_left.ReadEncM1(self.left_address) if self.rc_left else (0, 0)
                left_m2 = self.rc_left.ReadEncM2(self.left_address) if self.rc_left else (0, 0)
                right_m1 = self.rc_right.ReadEncM1(self.right_address) if self.rc_right else (0, 0)
                right_m2 = self.rc_right.ReadEncM2(self.right_address) if self.rc_right else (0, 0)
            else:
                left_m1 = self.rc.ReadEncM1(self.left_address) if self.rc else (0, 0)
                left_m2 = self.rc.ReadEncM2(self.left_address) if self.rc else (0, 0)
                right_m1 = self.rc.ReadEncM1(self.right_address) if self.rc else (0, 0)
                right_m2 = self.rc.ReadEncM2(self.right_address) if self.rc else (0, 0)
            
            return {
                "left_m1": left_m1[1] if left_m1[0] else 0,
                "left_m2": left_m2[1] if left_m2[0] else 0,
                "right_m1": right_m1[1] if right_m1[0] else 0,
                "right_m2": right_m2[1] if right_m2[0] else 0,
            }
        except Exception as e:
            logger.error(f"Error reading encoders: {e}")
            return {"left_m1": 0, "left_m2": 0, "right_m1": 0, "right_m2": 0}

    def close(self) -> None:
        """Clean up and stop motors."""
        logger.info("Closing RoboClaw controller")
        self.stop()
        self.rc = None
        self.rc_left = None
        self.rc_right = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __repr__(self) -> str:
        if self.simulate:
            return "DualRoboClawController(SIMULATION)"
        elif self.mode == "usb":
            return f"DualRoboClawController(USB)"
        else:
            return f"DualRoboClawController(UART)"