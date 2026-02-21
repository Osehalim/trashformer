"""
Arm controller for 3-servo arm via PCA9685 (Direct from Raspberry Pi).

Controls:
- Shoulder: Vertical movement (up/down) - Channel 0
  * 0° = Down (neutral), 90° = Horizontal, 180° = Up
- Elbow: Horizontal rotation (center to right - LEFT ARM) - Channel 1
  * 0° = Center/Straight (neutral), 90° = Turned right, 180° = Fully right
- Gripper: Open/close - Channel 2
  * 0° = Open, 90° = Closed

No Arduino needed - Raspberry Pi controls PCA9685 directly via I2C!
"""

import yaml
import time
from pathlib import Path
from typing import Dict, Optional, List
from utils.logger import get_logger
from arm.pca9685_driver import PCA9685
from arm.servo import Servo

logger = get_logger(__name__)


class ArmController:
    """
    3-servo arm controller via PCA9685.
    
    Arm configuration (LEFT ARM):
    - Shoulder (Channel 0): 0° (down/neutral) to 180° (up)
      * 0° = Down, 90° = Horizontal, 180° = Up
    - Elbow (Channel 1): 0° (center/neutral) to 180° (fully right)
      * Only rotates RIGHT from center (left arm design)
    - Gripper (Channel 2): 0° (open) to 90° (closed)
    """
    
    def __init__(self, config=None, simulate: bool = False):
        """
        Initialize arm controller.
        
        Args:
            config: Configuration object
            simulate: Run in simulation mode
        """
        # Load configuration
        if config is None:
            from utils.config_loader import load_config
            config = load_config()
        
        self.config = config
        self.simulate = simulate
        
        # Initialize PCA9685
        i2c_bus = config.get('hardware.i2c_bus', 1)
        i2c_address = config.get('hardware.i2c_address', 0x40)
        pwm_freq = config.get('arm.pwm_frequency', 50)
        
        logger.info(f"Initializing arm controller (simulate={simulate})")
        self.pwm = PCA9685(i2c_bus=i2c_bus, 
                          address=i2c_address,
                          frequency=pwm_freq,
                          simulate=simulate)
        
        # Create servos
        self.servos: Dict[str, Servo] = {}
        self._init_servos()
        
        # Load poses
        self.poses: Dict[str, Dict[str, float]] = {}
        self._load_poses()
        
        # Movement parameters
        self.default_speed = config.get('arm.movement.default_speed', 50)
        
        # State
        self.current_pose_name: Optional[str] = None
        self.is_enabled = True
        
        logger.info("Arm controller initialized")
    
    def _init_servos(self):
        """Initialize servo instances."""
        arm_config = self.config.get_section('arm')
        channels = arm_config.get('servo_channels', {})
        limits = arm_config.get('angle_limits', {})
        pwm_limits = arm_config.get('pwm_limits', {})
        
        # Shoulder servo (vertical movement) - Channel 0
        # 0° = down (neutral), 90° = horizontal, 180° = up
        shoulder_limits = limits.get('shoulder', {})
        self.servos['shoulder'] = Servo(
            pwm_controller=self.pwm,
            channel=channels.get('shoulder', 0),
            name='shoulder',
            min_angle=shoulder_limits.get('min', 0),
            max_angle=shoulder_limits.get('max', 180),
            min_pulse=pwm_limits.get('min_pulse', 500),
            max_pulse=pwm_limits.get('max_pulse', 2500),
            home_angle=shoulder_limits.get('home', 0),  # Down position
            neutral_angle=0  # Down is neutral/rest
        )
        
        # Elbow servo (horizontal rotation - LEFT ARM) - Channel 1
        # 0° = center (straight), 90° = turned right, 180° = fully right
        # Only rotates RIGHT from center (for left arm)
        elbow_limits = limits.get('elbow', {})
        self.servos['elbow'] = Servo(
            pwm_controller=self.pwm,
            channel=channels.get('elbow', 1),
            name='elbow',
            min_angle=elbow_limits.get('min', 0),
            max_angle=elbow_limits.get('max', 180),
            min_pulse=pwm_limits.get('min_pulse', 500),
            max_pulse=pwm_limits.get('max_pulse', 2500),
            home_angle=elbow_limits.get('home', 0),  # Center/straight
            neutral_angle=0  # Center is neutral
        )
        
        # Gripper servo - Channel 2
        gripper_limits = limits.get('gripper', {})
        self.servos['gripper'] = Servo(
            pwm_controller=self.pwm,
            channel=channels.get('gripper', 2),
            name='gripper',
            min_angle=gripper_limits.get('min', 0),
            max_angle=gripper_limits.get('max', 90),
            min_pulse=pwm_limits.get('min_pulse', 500),
            max_pulse=pwm_limits.get('max_pulse', 2500),
            home_angle=gripper_limits.get('home', 0),  # Open
            neutral_angle=0  # Open
        )
        
        logger.debug("Created 3 servos: shoulder (Ch0), elbow (Ch1), gripper (Ch2)")
    
    def _load_poses(self):
        """Load predefined poses from YAML."""
        # Try the 3-servo poses file first
        poses_file = Path("arm/poses_3servo.yaml")
        if not poses_file.exists():
            poses_file = Path("arm/poses.yaml")
        
        if not poses_file.exists():
            logger.warning(f"Poses file not found")
            return
        
        try:
            with open(poses_file, 'r') as f:
                self.poses = yaml.safe_load(f)
            
            logger.info(f"Loaded {len(self.poses)} poses from {poses_file}")
            
        except Exception as e:
            logger.error(f"Error loading poses: {e}")
    
    def get_servo(self, name: str) -> Optional[Servo]:
        """Get specific servo."""
        return self.servos.get(name)
    
    def set_angles(self, angles: Dict[str, float], validate: bool = True) -> bool:
        """
        Set multiple servos simultaneously.
        
        Args:
            angles: Dict mapping servo names to angles
            validate: Apply safety limits
            
        Returns:
            True if all successful
        """
        logger.debug(f"Setting angles: {angles}")
        
        success = True
        for name, angle in angles.items():
            if name in self.servos:
                if not self.servos[name].set_angle(angle, validate):
                    success = False
            else:
                logger.warning(f"Unknown servo: {name}")
                success = False
        
        return success
    
    def move_to_angles(self,
                      angles: Dict[str, float],
                      speed: Optional[float] = None,
                      blocking: bool = True) -> bool:
        """
        Move multiple servos with coordinated motion.
        
        Args:
            angles: Target angles
            speed: Movement speed in degrees/second
            blocking: Wait for completion
            
        Returns:
            True if successful
        """
        if speed is None:
            speed = self.default_speed
        
        logger.info(f"Moving to angles: {angles} at {speed}°/s")
        
        # Calculate max movement time for synchronization
        max_time = 0
        movements = []
        
        for name, target in angles.items():
            if name not in self.servos:
                continue
            
            servo = self.servos[name]
            current = servo.get_angle()
            
            if current is None:
                servo.set_angle(target)
                continue
            
            delta = abs(target - current)
            move_time = delta / speed
            max_time = max(max_time, move_time)
            movements.append((servo, target, delta))
        
        if not movements:
            return True
        
        # Execute synchronized movement
        success = True
        for servo, target, delta in movements:
            # Calculate speed so all servos finish at same time
            servo_speed = delta / max_time if max_time > 0 else speed
            if not servo.move_to(target, speed=servo_speed, blocking=False):
                success = False
        
        if blocking:
            time.sleep(max_time)
        
        return success
    
    def go_to_pose(self,
                   pose_name: str,
                   speed: Optional[float] = None,
                   blocking: bool = True) -> bool:
        """
        Move to predefined pose.
        
        Args:
            pose_name: Name of pose from poses_3servo.yaml
            speed: Movement speed
            blocking: Wait for completion
            
        Returns:
            True if successful
        """
        if pose_name not in self.poses:
            logger.error(f"Unknown pose: {pose_name}")
            logger.info(f"Available poses: {', '.join(list(self.poses.keys())[:5])}...")
            return False
        
        logger.info(f"Moving to pose: {pose_name}")
        
        pose_angles = self.poses[pose_name]
        success = self.move_to_angles(pose_angles, speed, blocking)
        
        if success:
            self.current_pose_name = pose_name
        
        return success
    
    def home(self, speed: Optional[float] = None, blocking: bool = True) -> bool:
        """Move to home position."""
        logger.info("Moving to home")
        return self.go_to_pose('home', speed, blocking)
    
    def neutral(self, speed: Optional[float] = None, blocking: bool = True) -> bool:
        """Move to neutral position (arm down, elbow center, gripper open)."""
        logger.info("Moving to neutral")
        return self.move_to_angles({
            'shoulder': 0,   # Down (neutral position)
            'elbow': 0,      # Center/straight (neutral position)
            'gripper': 0     # Open
        }, speed, blocking)
    
    # ========================================================================
    # Shoulder controls (vertical movement)
    # ========================================================================
    
    def shoulder_up(self, angle: float = 180, speed: Optional[float] = None) -> bool:
        """Move shoulder up (max 180°)."""
        logger.info(f"Moving shoulder up to {angle}°")
        return self.servos['shoulder'].move_to(angle, speed)
    
    def shoulder_down(self, angle: float = 0, speed: Optional[float] = None) -> bool:
        """Move shoulder down (min 0°)."""
        logger.info(f"Moving shoulder down to {angle}°")
        return self.servos['shoulder'].move_to(angle, speed)
    
    def shoulder_horizontal(self, speed: Optional[float] = None) -> bool:
        """Move shoulder to horizontal (90°)."""
        logger.info("Moving shoulder to horizontal")
        return self.servos['shoulder'].move_to(90, speed)
    
    # ========================================================================
    # Elbow controls (horizontal rotation - LEFT ARM only rotates RIGHT)
    # ========================================================================
    
    def elbow_center(self, speed: Optional[float] = None) -> bool:
        """Move elbow to center/straight position (0°)."""
        logger.info("Moving elbow to center")
        return self.servos['elbow'].move_to(0, speed)
    
    def elbow_right(self, angle: float = 90, speed: Optional[float] = None) -> bool:
        """Move elbow right (0° = center, 90° = right, 180° = fully right)."""
        logger.info(f"Moving elbow right to {angle}°")
        return self.servos['elbow'].move_to(angle, speed)
    
    def elbow_full_right(self, speed: Optional[float] = None) -> bool:
        """Move elbow to fully right position (180°)."""
        logger.info("Moving elbow fully right")
        return self.servos['elbow'].move_to(180, speed)
    
    # ========================================================================
    # Gripper controls
    # ========================================================================
    
    def open_gripper(self, speed: Optional[float] = None) -> bool:
        """Open gripper (0°)."""
        logger.info("Opening gripper")
        return self.servos['gripper'].move_to(0, speed)
    
    def close_gripper(self, speed: Optional[float] = None) -> bool:
        """Close gripper (90°)."""
        logger.info("Closing gripper")
        return self.servos['gripper'].move_to(90, speed)
    
    def set_gripper(self, angle: float, speed: Optional[float] = None) -> bool:
        """Set gripper to specific angle (0-90°)."""
        return self.servos['gripper'].move_to(angle, speed)
    
    # ========================================================================
    # Status and utility
    # ========================================================================
    
    def get_current_angles(self) -> Dict[str, Optional[float]]:
        """Get current angles of all servos."""
        return {name: servo.get_angle() for name, servo in self.servos.items()}
    
    def list_poses(self) -> List[str]:
        """Get list of available poses."""
        return list(self.poses.keys())
    
    def execute_sequence(self,
                        sequence: List[tuple],
                        pause_between: float = 0.5) -> bool:
        """
        Execute sequence of poses.
        
        Args:
            sequence: List of (pose_name, speed, pause) tuples
            pause_between: Default pause between poses
            
        Returns:
            True if successful
        """
        logger.info(f"Executing sequence of {len(sequence)} poses")
        
        for i, step in enumerate(sequence):
            if len(step) == 1:
                pose_name = step[0]
                speed = None
                pause = pause_between
            elif len(step) == 2:
                pose_name, speed = step
                pause = pause_between
            else:
                pose_name, speed, pause = step
            
            logger.info(f"Step {i+1}/{len(sequence)}: {pose_name}")
            
            if not self.go_to_pose(pose_name, speed, blocking=True):
                logger.error(f"Sequence failed at step {i+1}")
                return False
            
            time.sleep(pause)
        
        logger.info("Sequence complete")
        return True
    
    def emergency_stop(self) -> bool:
        """Emergency stop - go to safe position."""
        logger.warning("EMERGENCY STOP")
        return self.go_to_pose('emergency', speed=100, blocking=False)
    
    def disable(self):
        """Disable all servos."""
        logger.info("Disabling arm")
        for servo in self.servos.values():
            servo.disable()
        self.is_enabled = False
    
    def close(self):
        """Clean up and close."""
        logger.info("Closing arm controller")
        self.home(blocking=True)
        self.pwm.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __repr__(self):
        """String representation."""
        return f"ArmController(servos={list(self.servos.keys())}, poses={len(self.poses)})"


if __name__ == "__main__":
    # Test arm controller
    from utils.logger import setup_logging
    from utils.config_loader import load_config
    
    setup_logging()
    
    logger.info("Testing ArmController")
    
    config = load_config("config/default.yaml")
    
    with ArmController(config=config, simulate=True) as arm:
        logger.info(f"Arm: {arm}")
        
        # Test basic movements
        logger.info("Testing basic movements...")
        arm.home()
        time.sleep(1)
        
        # Test shoulder (vertical)
        arm.shoulder_up(135)
        time.sleep(1)
        arm.shoulder_horizontal()
        time.sleep(1)
        arm.shoulder_down(45)
        time.sleep(1)
        
        # Test elbow (horizontal)
        arm.elbow_left(45)
        time.sleep(1)
        arm.elbow_center()
        time.sleep(1)
        arm.elbow_right(135)
        time.sleep(1)
        
        # Test gripper
        arm.open_gripper()
        time.sleep(0.5)
        arm.close_gripper()
        time.sleep(0.5)
        arm.open_gripper()
        
        logger.info("Test complete")