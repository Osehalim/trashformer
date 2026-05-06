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
    from drive.roboclaw_3 import Roboclaw
    ROBOCLAW_AVAILABLE = True
except ImportError:
    try:
        from drive.roboclaw import Roboclaw
        ROBOCLAW_AVAILABLE = True
    except ImportError:
        ROBOCLAW_AVAILABLE = False
        logger.warning("roboclaw library not available - see setup instructions")


class DualRoboClawController:
    """
    Controller for dual RoboClaw setup (left and right tracks).

    Supports two communication modes:
    - usb:   one RoboClaw per serial device (/dev/ttyACM0, /dev/ttyACM2)
    - uart:  both RoboClaws on one shared packet-serial bus
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
        right_port: str = "/dev/ttyACM2",
    ):
        self.port = port
        self.baudrate = baudrate
        self.left_address = left_address
        self.right_address = right_address
        self.mode = str(mode).lower().strip()
        self.left_port = left_port
        self.right_port = right_port
        self.simulate = simulate or (not ROBOCLAW_AVAILABLE)

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
            self.rc = None
            self.rc_left = None
            self.rc_right = None

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
            logger.info(
                f"Left RoboClaw ({self.left_port}, 0x{self.left_address:02X}): {left_version[1]}"
            )
        else:
            logger.error(
                f"Failed to connect to left RoboClaw on {self.left_port} at 0x{self.left_address:02X}"
            )

        if right_version[0]:
            logger.info(
                f"Right RoboClaw ({self.right_port}, 0x{self.right_address:02X}): {right_version[1]}"
            )
        else:
            logger.error(
                f"Failed to connect to right RoboClaw on {self.right_port} at 0x{self.right_address:02X}"
            )

        logger.info(
            f"Dual RoboClaw initialized in USB mode: left={self.left_port}, right={self.right_port}, baud={self.baudrate}"
        )

    def _init_uart(self) -> None:
        if not self._controller_exists(self.port):
            raise FileNotFoundError(f"UART RoboClaw port not found: {self.port}")

        self.rc = self._open_controller(self.port)

        left_version = self.rc.ReadVersion(self.left_address)
        right_version = self.rc.ReadVersion(self.right_address)

        if left_version[0]:
            logger.info(f"Left RoboClaw (0x{self.left_address:02X}): {left_version[1]}")
        else:
            logger.error(f"Failed to connect to left RoboClaw at 0x{self.left_address:02X}")

        if right_version[0]:
            logger.info(f"Right RoboClaw (0x{self.right_address:02X}): {right_version[1]}")
        else:
            logger.error(f"Failed to connect to right RoboClaw at 0x{self.right_address:02X}")

        logger.info(f"Dual RoboClaw initialized in UART mode on {self.port} @ {self.baudrate}")

    def _speed_to_duty(self, speed: float) -> int:
        """Convert speed (-1.0 to 1.0) to RoboClaw duty cycle (0-127)."""
        speed = max(-1.0, min(1.0, float(speed)))
        return int(abs(speed) * 127)

    def _set_pair(self, controller: Optional[Roboclaw], address: int, speed: float, side: str) -> None:
        duty = self._speed_to_duty(speed)

        if self.simulate:
            logger.debug(f"[SIM] {side} motors: {speed:.2f} ({duty})")
            return

        if not controller:
            logger.warning(f"{side} RoboClaw controller is not available")
            return

        if speed >= 0:
            controller.ForwardM1(address, duty)
            controller.ForwardM2(address, duty)
        else:
            controller.BackwardM1(address, duty)
            controller.BackwardM2(address, duty)

    def _stop_pair(self, controller: Optional[Roboclaw], address: int) -> None:
        if self.simulate or not controller:
            return
        controller.ForwardM1(address, 0)
        controller.ForwardM2(address, 0)

    def set_left_motors(self, speed: float) -> None:
        """Set left track motors (both motors on left RoboClaw)."""
        controller = self.rc_left if self.mode == "usb" else self.rc
        self._set_pair(controller, self.left_address, speed, "Left")

    def set_right_motors(self, speed: float) -> None:
        """Set right track motors (both motors on right RoboClaw)."""
        controller = self.rc_right if self.mode == "usb" else self.rc
        self._set_pair(controller, self.right_address, speed, "Right")

    def set_motors(self, left_speed: float, right_speed: float) -> None:
        """Set both left and right motors."""
        self.set_left_motors(left_speed)
        self.set_right_motors(right_speed)

    def stop(self) -> None:
        """Stop all motors."""
        logger.debug("Stopping all motors")

        if self.mode == "usb":
            self._stop_pair(self.rc_left, self.left_address)
            self._stop_pair(self.rc_right, self.right_address)
        else:
            self._stop_pair(self.rc, self.left_address)
            self._stop_pair(self.rc, self.right_address)

    def _read_encoder_pair(self, controller: Optional[Roboclaw], address: int) -> tuple[int, int]:
        if self.simulate or not controller:
            return 0, 0

        enc1 = controller.ReadEncM1(address)
        enc2 = controller.ReadEncM2(address)
        return (
            enc1[1] if enc1[0] else 0,
            enc2[1] if enc2[0] else 0,
        )

    def read_encoders(self) -> dict:
        """Read encoder values from both RoboClaws."""
        if self.simulate:
            return {
                "left_m1": 0, "left_m2": 0,
                "right_m1": 0, "right_m2": 0,
            }

        try:
            if self.mode == "usb":
                left_m1, left_m2 = self._read_encoder_pair(self.rc_left, self.left_address)
                right_m1, right_m2 = self._read_encoder_pair(self.rc_right, self.right_address)
            else:
                left_m1, left_m2 = self._read_encoder_pair(self.rc, self.left_address)
                right_m1, right_m2 = self._read_encoder_pair(self.rc, self.right_address)

            return {
                "left_m1": left_m1,
                "left_m2": left_m2,
                "right_m1": right_m1,
                "right_m2": right_m2,
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
            mode_desc = "SIMULATION"
        elif self.mode == "usb":
            mode_desc = f"USB(L={self.left_port}, R={self.right_port}, {self.baudrate})"
        else:
            mode_desc = f"UART({self.port}@{self.baudrate})"
        return (
            f"DualRoboClawController({mode_desc}, "
            f"L=0x{self.left_address:02X}, R=0x{self.right_address:02X})"
        )


if __name__ == "__main__":
    from utils.logger import setup_logging

    setup_logging()

    logger.info("Testing Dual RoboClaw controller")

    with DualRoboClawController(simulate=True, mode="usb") as controller:
        logger.info(f"{controller}")

        logger.info("Forward")
        controller.set_motors(0.5, 0.5)
        time.sleep(2)

        logger.info("Backward")
        controller.set_motors(-0.5, -0.5)
        time.sleep(2)

        logger.info("Rotate left")
        controller.set_motors(-0.5, 0.5)
        time.sleep(2)

        logger.info("Stop")
        controller.stop()

        logger.info("Test complete")