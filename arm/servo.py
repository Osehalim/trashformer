"""
Servo control for 3-servo arm via PCA9685.

Direct control from Raspberry Pi - no Arduino needed!

Manages three servos:
- Shoulder: Vertical movement (up/down) - 0° to 180°
- Elbow: Horizontal movement (left/right) - 0° to 180° (90° is neutral)
- Gripper: Open/close - 0° (open) to 90° (closed)
"""

import time
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class Servo:
    """
    Individual servo controller via PCA9685.
    
    Provides angle tracking, limits, and smooth movement control.
    """
    
    def __init__(self,
                 pwm_controller,
                 channel: int,
                 name: str,
                 min_angle: float = 0,
                 max_angle: float = 180,
                 min_pulse: int = 500,
                 max_pulse: int = 2500,
                 home_angle: float = 90,
                 neutral_angle: float = 90):
        """
        Initialize a servo.
        
        Args:
            pwm_controller: PCA9685 instance
            channel: PWM channel (0-15)
            name: Servo name ('shoulder', 'elbow', or 'gripper')
            min_angle: Minimum allowed angle (degrees)
            max_angle: Maximum allowed angle (degrees)
            min_pulse: PWM pulse width at min_angle (microseconds)
            max_pulse: PWM pulse width at max_angle (microseconds)
            home_angle: Default "home" position
            neutral_angle: Neutral/rest position
        """
        self.pwm = pwm_controller
        self.channel = channel
        self.name = name.lower()
        
        # Angle limits
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.home_angle = home_angle
        self.neutral_angle = neutral_angle
        
        # PWM limits
        self.min_pulse = min_pulse
        self.max_pulse = max_pulse
        
        # Current state
        self._current_angle: Optional[float] = None
        self._target_angle: Optional[float] = None
        
        logger.info(f"Initialized {name} servo on channel {channel} "
                   f"(range: {min_angle}°-{max_angle}°, home: {home_angle}°)")
    
    def _angle_to_pulse(self, angle: float) -> int:
        """Convert angle to PWM pulse width."""
        # Linear interpolation
        angle_range = self.max_angle - self.min_angle
        pulse_range = self.max_pulse - self.min_pulse
        
        normalized = (angle - self.min_angle) / angle_range
        pulse = self.min_pulse + (normalized * pulse_range)
        
        return int(pulse)
    
    def _clamp_angle(self, angle: float) -> float:
        """Clamp angle to valid range."""
        if angle < self.min_angle:
            logger.warning(f"{self.name}: Angle {angle}° below minimum {self.min_angle}°, clamping")
            return self.min_angle
        if angle > self.max_angle:
            logger.warning(f"{self.name}: Angle {angle}° above maximum {self.max_angle}°, clamping")
            return self.max_angle
        return angle
    
    def set_angle(self, angle: float, validate: bool = True) -> bool:
        """
        Set servo to specific angle immediately.
        
        Args:
            angle: Target angle in degrees
            validate: Apply safety limits
            
        Returns:
            True if successful
        """
        if validate:
            angle = self._clamp_angle(angle)
        
        # Convert to pulse width
        pulse = self._angle_to_pulse(angle)
        
        # Send to PCA9685
        self.pwm.set_pulse_width(self.channel, pulse)
        
        # Update state
        self._current_angle = angle
        self._target_angle = angle
        
        logger.debug(f"{self.name}: Set to {angle}° (pulse: {pulse}μs)")
        return True
    
    def move_to(self, angle: float, speed: Optional[float] = None, blocking: bool = True) -> bool:
        """
        Move servo to angle with optional speed control.
        
        Args:
            angle: Target angle
            speed: Movement speed in degrees/second (None = instant)
            blocking: Wait for movement to complete
            
        Returns:
            True if successful
        """
        angle = self._clamp_angle(angle)
        
        if speed is None or self._current_angle is None:
            # Instant movement
            return self.set_angle(angle)
        
        # Calculate smooth movement
        start_angle = self._current_angle
        delta = angle - start_angle
        
        if abs(delta) < 1:  # Already there
            return True
        
        move_time = abs(delta) / speed
        steps = max(int(move_time * 10), 1)  # 10 updates per second
        step_delay = move_time / steps
        
        logger.debug(f"{self.name}: Moving from {start_angle}° to {angle}° "
                    f"at {speed}°/s ({move_time:.2f}s)")
        
        # Execute movement
        for i in range(steps + 1):
            progress = i / steps
            current = start_angle + (delta * progress)
            
            if not self.set_angle(current, validate=False):
                return False
            
            if blocking and i < steps:
                time.sleep(step_delay)
        
        self._target_angle = angle
        return True
    
    def home(self, speed: Optional[float] = None, blocking: bool = True) -> bool:
        """Move to home position."""
        logger.info(f"{self.name}: Moving to home position ({self.home_angle}°)")
        return self.move_to(self.home_angle, speed, blocking)
    
    def neutral(self, speed: Optional[float] = None, blocking: bool = True) -> bool:
        """Move to neutral position."""
        logger.info(f"{self.name}: Moving to neutral position ({self.neutral_angle}°)")
        return self.move_to(self.neutral_angle, speed, blocking)
    
    def get_angle(self) -> Optional[float]:
        """Get current servo angle."""
        return self._current_angle
    
    def get_target_angle(self) -> Optional[float]:
        """Get target servo angle."""
        return self._target_angle
    
    def is_moving(self) -> bool:
        """Check if servo is moving."""
        if self._current_angle is None or self._target_angle is None:
            return False
        return abs(self._current_angle - self._target_angle) > 1
    
    def disable(self):
        """Disable servo (stop PWM signal)."""
        logger.info(f"{self.name}: Disabling")
        self.pwm.set_pwm(self.channel, 0, 0)
    
    def __repr__(self):
        """String representation."""
        return (f"Servo(name='{self.name}', channel={self.channel}, "
                f"current={self._current_angle}°, range={self.min_angle}°-{self.max_angle}°)")