"""
Servo control via PCA9685.

Supports both:
- Position servos (standard 0-180°)
- Continuous rotation servos (speed/direction control with timed movement)
"""

from __future__ import annotations

import time
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


class Servo:
    """
    Individual servo controller via PCA9685.

    Supports two modes:
    - Position mode (continuous=False): Standard servo, angle → position
    - Continuous mode (continuous=True): Continuous rotation servo, angle → timed movement
    """

    def __init__(
        self,
        pwm_controller,
        channel: int,
        name: str,
        min_angle: float = 0.0,
        max_angle: float = 180.0,
        min_pulse: int = 500,
        max_pulse: int = 2500,
        home_angle: float = 90.0,
        neutral_angle: float = 90.0,
        invert: bool = False,
        offset_deg: float = 0.0,
        smooth_hz: float = 10.0,
        continuous: bool = False,  # NEW: For continuous rotation servos
        stop_pulse: int = 1500,    # NEW: Stop pulse for continuous servos
        speed_pulse_range: int = 100,  # NEW: Pulse range from stop for speed control
    ):
        self.pwm = pwm_controller
        self.channel = int(channel)
        self.name = name.lower()

        self.min_angle = float(min_angle)
        self.max_angle = float(max_angle)
        self.home_angle = float(home_angle)
        self.neutral_angle = float(neutral_angle)

        self.min_pulse = int(min_pulse)
        self.max_pulse = int(max_pulse)

        self.invert = bool(invert)
        self.offset_deg = float(offset_deg)
        self.smooth_hz = float(smooth_hz)

        # Continuous rotation servo settings
        self.continuous = bool(continuous)
        self.stop_pulse = int(stop_pulse)
        self.speed_pulse_range = int(speed_pulse_range)

        # State tracking
        self._current_angle: Optional[float] = None
        self._target_angle: Optional[float] = None
        
        # For continuous servos, track estimated position
        self._estimated_position: float = 0.0  # Degrees from starting point

        mode = "CONTINUOUS" if self.continuous else "POSITION"
        logger.info(
            f"Initialized {self.name} servo on channel {self.channel} ({mode} mode) "
            f"(angle range: {self.min_angle}°-{self.max_angle}°, home: {self.home_angle}°)"
        )

    def _clamp_angle(self, angle: float) -> float:
        a = float(angle)
        if a < self.min_angle:
            logger.warning(f"{self.name}: angle {a}° below min {self.min_angle}°, clamping")
            return self.min_angle
        if a > self.max_angle:
            logger.warning(f"{self.name}: angle {a}° above max {self.max_angle}°, clamping")
            return self.max_angle
        return a

    def _apply_calibration(self, angle: float) -> float:
        """Apply offset/invert to logical angle before mapping to pulse."""
        a = float(angle) + self.offset_deg
        if self.invert:
            a = self.max_angle - (a - self.min_angle)
        return a

    def _angle_to_pulse(self, angle: float) -> int:
        """Convert angle to pulse width (for position servos)."""
        if self.max_angle == self.min_angle:
            logger.warning(f"{self.name}: max_angle == min_angle; defaulting to midpoint pulse")
            return int(round((self.min_pulse + self.max_pulse) / 2))

        ratio = (angle - self.min_angle) / (self.max_angle - self.min_angle)
        ratio = _clamp(ratio, 0.0, 1.0)
        pulse = self.min_pulse + ratio * (self.max_pulse - self.min_pulse)
        pulse_i = int(round(pulse))

        if pulse_i < self.min_pulse:
            pulse_i = self.min_pulse
        if pulse_i > self.max_pulse:
            pulse_i = self.max_pulse
        return pulse_i

    def _move_continuous(self, target_angle: float, speed: Optional[float] = None) -> bool:
        """
        Move continuous rotation servo to approximate angle using timed movement.
        
        This is APPROXIMATE - no position feedback!
        """
        if self._estimated_position is None:
            self._estimated_position = self.home_angle

        start_pos = self._estimated_position
        delta = target_angle - start_pos
        
        if abs(delta) < 1.0:
            logger.debug(f"{self.name}: Already at target ({target_angle}°)")
            self._current_angle = target_angle
            self._target_angle = target_angle
            return True

        # Determine direction and calculate movement time
        direction = 1 if delta > 0 else -1
        abs_delta = abs(delta)
        
        # Estimate movement time (you'll need to calibrate this!)
        # This is a ROUGH estimate - adjust based on your servo
        DEGREES_PER_SECOND = 120  # Estimate, needs calibration!
        move_time = abs_delta / DEGREES_PER_SECOND
        
        # Generate pulse for movement
        # stop_pulse ± speed_pulse_range
        move_pulse = self.stop_pulse + (direction * self.speed_pulse_range)
        
        logger.info(
            f"{self.name}: Moving {abs_delta:.1f}° ({start_pos:.1f}° → {target_angle:.1f}°) "
            f"for {move_time:.2f}s at pulse {move_pulse}μs"
        )
        
        # Start movement
        self.pwm.set_pulse_width(self.channel, move_pulse)
        time.sleep(move_time)
        
        # STOP
        self.pwm.set_pulse_width(self.channel, self.stop_pulse)
        
        # Update estimated position
        self._estimated_position = target_angle
        self._current_angle = target_angle
        self._target_angle = target_angle
        
        logger.debug(f"{self.name}: Stopped at estimated {target_angle}°")
        return True

    def set_angle(self, angle: float, validate: bool = True) -> bool:
        """Set servo to specific angle."""
        a = float(angle)
        if validate:
            a = self._clamp_angle(a)

        if self.continuous:
            # Continuous servo: use timed movement
            return self._move_continuous(a)
        else:
            # Position servo: direct angle control
            calibrated = self._apply_calibration(a)
            pulse = self._angle_to_pulse(calibrated)

            self.pwm.set_pulse_width(self.channel, pulse)

            self._current_angle = a
            self._target_angle = a

            logger.debug(f"{self.name}: set {a}° (cal={calibrated}° -> {pulse}μs)")
            return True

    def move_to(self, angle: float, speed: Optional[float] = None, blocking: bool = True) -> bool:
        """Move servo to angle with optional smoothing."""
        target = self._clamp_angle(float(angle))

        if self.continuous:
            # Continuous servo: always use timed movement
            return self._move_continuous(target, speed)

        # Position servo: smooth movement
        if speed is None or self._current_angle is None:
            return self.set_angle(target, validate=False)

        start = float(self._current_angle)
        delta = target - start
        if abs(delta) < 0.5:
            self._target_angle = target
            return True

        speed = max(1e-6, float(speed))
        move_time = abs(delta) / speed

        steps = max(int(move_time * self.smooth_hz), 1)
        step_delay = move_time / steps

        logger.debug(
            f"{self.name}: moving {start}° -> {target}° at {speed}°/s "
            f"({move_time:.2f}s, {steps} steps)"
        )

        for i in range(steps + 1):
            t = i / steps
            a = start + delta * t
            self.set_angle(a, validate=False)
            if blocking and i < steps:
                time.sleep(step_delay)

        self._current_angle = target
        self._target_angle = target
        return True

    def home(self, speed: Optional[float] = None, blocking: bool = True) -> bool:
        """Move to home position."""
        return self.move_to(self.home_angle, speed, blocking)

    def neutral(self, speed: Optional[float] = None, blocking: bool = True) -> bool:
        """Move to neutral position."""
        return self.move_to(self.neutral_angle, speed, blocking)

    def stop(self) -> None:
        """
        Stop continuous servo immediately.
        For position servos, this does nothing (they don't move continuously).
        """
        if self.continuous:
            logger.info(f"{self.name}: Stopping continuous servo")
            self.pwm.set_pulse_width(self.channel, self.stop_pulse)

    def get_angle(self) -> Optional[float]:
        """Get current servo angle (estimated for continuous servos)."""
        if self.continuous:
            return self._estimated_position
        return self._current_angle

    def disable(self) -> None:
        """Disable servo output (0% duty)."""
        logger.info(f"{self.name}: disabling output")
        self.pwm.disable_channel(self.channel)

    def __repr__(self) -> str:
        mode = "CONTINUOUS" if self.continuous else "POSITION"
        return (
            f"Servo(name='{self.name}', channel={self.channel}, mode={mode}, "
            f"current={self._current_angle}°, range={self.min_angle}°-{self.max_angle}°)"
        )