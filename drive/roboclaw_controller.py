"""
drive/roboclaw_controller.py - RoboClaw Motor Controller Driver

For dual RoboClaw setup:
- RoboClaw 1: Controls left tracks (2 motors)
- RoboClaw 2: Controls right tracks (2 motors)

Communication: Serial (UART/TTL)
Addresses: 0x80 (left), 0x81 (right) - configurable

Requires roboclaw_3 Python library:
  pip3 install roboclaw_3 --break-system-packages
"""

from __future__ import annotations

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
    except:
        ROBOCLAW_AVAILABLE = False
        logger.warning("roboclaw_3 not available - install with: pip3 install roboclaw_3")


class DualRoboClawController:
    """
    Controller for dual RoboClaw setup (left and right tracks).
    
    Each RoboClaw controls 2 motors on one side of the robot.
    """
    
    def __init__(
        self,
        port: str = "/dev/ttyS0",
        baudrate: int = 38400,
        left_address: int = 0x80,   # 128
        right_address: int = 0x81,  # 129
        simulate: bool = False,
    ):
        self.port = port
        self.baudrate = baudrate
        self.left_address = left_address
        self.right_address = right_address
        self.simulate = simulate or (not ROBOCLAW_AVAILABLE)
        
        self.rc: Optional[Roboclaw] = None
        
        if self.simulate:
            logger.warning("RoboClaw controller running in SIMULATION mode")
            return
        
        try:
            # Create RoboClaw object
            self.rc = Roboclaw(self.port, self.baudrate)
            self.rc.Open()
            
            # Verify connection
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
            
            logger.info(f"Dual RoboClaw initialized on {port} @ {baudrate}")
        
        except Exception as e:
            logger.error(f"Failed to initialize RoboClaw: {e}")
            logger.warning("Falling back to simulation mode")
            self.simulate = True
            self.rc = None
    
    def _speed_to_duty(self, speed: float) -> int:
        """
        Convert speed (-1.0 to 1.0) to RoboClaw duty cycle.
        
        Args:
            speed: Normalized speed
            
        Returns:
            Duty cycle value (0-127, with 64 = stopped for mixed mode)
                             OR (-127 to 127 for individual motor control)
        """
        # Clamp speed
        speed = max(-1.0, min(1.0, float(speed)))
        
        # Convert to RoboClaw range: 0-127 where 64 = stop
        # For mixed mode (we'll use individual motor commands instead)
        # For individual motors: -127 to 127 where 0 = stop
        duty = int(speed * 127)
        
        return duty
    
    def set_left_motors(self, speed: float) -> None:
        """
        Set left track motors (both motors on left RoboClaw).
        
        Args:
            speed: -1.0 (full reverse) to 1.0 (full forward)
        """
        duty = self._speed_to_duty(speed)
        
        if self.simulate:
            logger.debug(f"[SIM] Left motors: {speed:.2f} ({duty})")
            return
        
        if not self.rc:
            return
        
        # Control both motors on left RoboClaw
        # M1 and M2 both get same command
        if duty >= 0:
            # Forward
            self.rc.ForwardM1(self.left_address, duty)
            self.rc.ForwardM2(self.left_address, duty)
        else:
            # Backward
            self.rc.BackwardM1(self.left_address, abs(duty))
            self.rc.BackwardM2(self.left_address, abs(duty))
    
    def set_right_motors(self, speed: float) -> None:
        """
        Set right track motors (both motors on right RoboClaw).
        
        Args:
            speed: -1.0 (full reverse) to 1.0 (full forward)
        """
        duty = self._speed_to_duty(speed)
        
        if self.simulate:
            logger.debug(f"[SIM] Right motors: {speed:.2f} ({duty})")
            return
        
        if not self.rc:
            return
        
        # Control both motors on right RoboClaw
        if duty >= 0:
            # Forward
            self.rc.ForwardM1(self.right_address, duty)
            self.rc.ForwardM2(self.right_address, duty)
        else:
            # Backward
            self.rc.BackwardM1(self.right_address, abs(duty))
            self.rc.BackwardM2(self.right_address, abs(duty))
    
    def set_motors(self, left_speed: float, right_speed: float) -> None:
        """
        Set both left and right motors.
        
        Args:
            left_speed: Left track speed (-1.0 to 1.0)
            right_speed: Right track speed (-1.0 to 1.0)
        """
        self.set_left_motors(left_speed)
        self.set_right_motors(right_speed)
    
    def stop(self) -> None:
        """Stop all motors."""
        logger.debug("Stopping all motors")
        
        if self.simulate:
            return
        
        if not self.rc:
            return
        
        # Stop all motors on both RoboClaws
        self.rc.ForwardM1(self.left_address, 0)
        self.rc.ForwardM2(self.left_address, 0)
        self.rc.ForwardM1(self.right_address, 0)
        self.rc.ForwardM2(self.right_address, 0)
    
    def read_encoders(self) -> dict:
        """
        Read encoder values from both RoboClaws.
        
        Returns:
            Dictionary with encoder counts
        """
        if self.simulate or not self.rc:
            return {
                "left_m1": 0, "left_m2": 0,
                "right_m1": 0, "right_m2": 0
            }
        
        try:
            left_m1 = self.rc.ReadEncM1(self.left_address)
            left_m2 = self.rc.ReadEncM2(self.left_address)
            right_m1 = self.rc.ReadEncM1(self.right_address)
            right_m2 = self.rc.ReadEncM2(self.right_address)
            
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
        # RoboClaw library doesn't have explicit close method
        self.rc = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def __repr__(self) -> str:
        mode = "SIMULATION" if self.simulate else f"{self.port}@{self.baudrate}"
        return f"DualRoboClawController({mode}, L=0x{self.left_address:02X}, R=0x{self.right_address:02X})"


if __name__ == "__main__":
    from utils.logger import setup_logging
    
    setup_logging()
    
    logger.info("Testing Dual RoboClaw controller")
    
    with DualRoboClawController(simulate=True) as controller:
        logger.info(f"{controller}")
        
        # Test forward
        logger.info("Forward")
        controller.set_motors(0.5, 0.5)
        time.sleep(2)
        
        # Test backward
        logger.info("Backward")
        controller.set_motors(-0.5, -0.5)
        time.sleep(2)
        
        # Test rotate left
        logger.info("Rotate left")
        controller.set_motors(-0.5, 0.5)
        time.sleep(2)
        
        # Stop
        logger.info("Stop")
        controller.stop()
        
        logger.info("Test complete")