"""
Servo control via PCA9685.

Supports both:
- Position servos (standard 0-180°)
- Continuous rotation servos (speed/direction control with timed movement)

NOTE on continuous servos:
Timed "angle" moves are ALWAYS approximate (no encoder feedback).
Accuracy depends on calibrating:
- stop_pulse
- speed_pulse_range
- degrees_per_second (at your chosen speed_pulse_range and under typical load)
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

    Modes:
    - Position mode (continuous=False): Standard servo, angle -> position
    - Continuous mode (continuous=True): Continuous rotation servo, "angle" -> timed movement
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
        home_angle: float = 0.0,
        neutral_angle: float = 0.0,
        invert: bool = False,
        offset_deg: float = 0.0,
        smooth_hz: float = 10.0,
        continuous: bool = False,
        stop_pulse: int = 1500,
        speed_pulse_range: int = 100,
        degrees_per_second: float = 120.0,
        min_move_deg: float = 1.0,
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
        self.degrees_per_second = float(degrees_per_second)  # calibrate this!
        self.min_move_deg = float(min_move_deg)

        # State tracking
        self._current_angle: Optional[float] = None
        self._target_angle: Optional[float] = None

        # For continuous servos, track estimated position (start at home_angle)
        self._estimated_position: float = self.home_angle

        mode = "CONTINUOUS" if self.continuous else "POSITION"
        logger.info(
            f"Initialized {self.name} servo on channel {self.channel} ({mode} mode) "
            f"(angle range: {self.min_angle}°-{self.max_angle}°, home: {self.home_angle}°)"
        )
        if self.continuous:
            logger.info(
                f"  stop_pulse={self.stop_pulse}μs, speed_range=±{self.speed_pulse_range}μs, "
                f"speed={self.degrees_per_second}°/s"
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
        """Apply offset/invert to logical angle before mapping to pulse (position servos)."""
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

        pulse_i = max(self.min_pulse, min(self.max_pulse, pulse_i))
        return pulse_i

    @staticmethod
    def _normalize_speed(speed: Optional[float]) -> float:
        """
        Convert speed into a 0..1 factor.
        Accepts:
          - None -> 1.0
          - 0..1 -> as-is
          - 1..100 -> treated as percent
          - >100 -> clamped to 1.0
        """
        if speed is None:
            return 1.0
        s = float(speed)
        if s <= 0:
            return 0.0
        if s <= 1.0:
            return s
        if s <= 100.0:
            return s / 100.0
        return 1.0

    def _move_continuous(self, target_angle: float, speed: Optional[float] = None) -> bool:
        """
        Move continuous rotation servo to approximate angle using timed movement.
        No position feedback -> depends on calibration.
        """
        # Clamp and compute delta from estimated position
        target_angle = self._clamp_angle(target_angle)
        start_pos = float(self._estimated_position)
        delta = target_angle - start_pos
        abs_delta = abs(delta)

        if abs_delta < self.min_move_deg:
            logger.debug(f"{self.name}: Already near target ({target_angle:.1f}°)")
            self._current_angle = target_angle
            self._target_angle = target_angle
            self._estimated_position = target_angle
            return True

        # Direction: +1 or -1, apply invert so "positive" stays consistent with your config
        direction = 1 if delta > 0 else -1
        if self.invert:
            direction *= -1

        # Speed factor scales pulse AND (approximately) degrees/sec
        speed_factor = self._normalize_speed(speed)

        # If speed_factor is 0, just stop
        if speed_factor <= 0.0:
            self.stop()
            return True

        # Compute pulse to drive servo
        pulse_offset = int(round(self.speed_pulse_range * speed_factor))
        # Ensure we actually move (avoid tiny offset)
        pulse_offset = max(1, pulse_offset)

        move_pulse = self.stop_pulse + (direction * pulse_offset)

        # Compute movement time based on calibrated degrees/sec
        # Approx assumption: speed roughly scales with pulse_offset.
        effective_dps = max(1e-6, self.degrees_per_second * speed_factor)
        move_time = abs_delta / effective_dps

        logger.info(
            f"{self.name}: CONT move {abs_delta:.1f}° ({start_pos:.1f}° -> {target_angle:.1f}°) "
            f"dir={direction:+d} speed={speed_factor:.2f} "
            f"t={move_time:.2f}s pulse={move_pulse}μs stop={self.stop_pulse}μs"
        )

        # Move
        self.pwm.set_pulse_width(self.channel, move_pulse)
        time.sleep(move_time)

        # Stop
        self.pwm.set_pulse_width(self.channel, self.stop_pulse)

        # Update estimated position
        self._estimated_position = target_angle
        self._current_angle = target_angle
        self._target_angle = target_angle

        logger.debug(f"{self.name}: Stopped at estimated {target_angle:.1f}°")
        return True

    def set_angle(self, angle: float, validate: bool = True) -> bool:
        """Set servo to specific angle."""
        a = float(angle)
        if validate:
            a = self._clamp_angle(a)

        if self.continuous:
            return self._move_continuous(a)
        else:
            calibrated = self._apply_calibration(a)
            pulse = self._angle_to_pulse(calibrated)
            self.pwm.set_pulse_width(self.channel, pulse)
            self._current_angle = a
            self._target_angle = a
            logger.debug(f"{self.name}: set {a}° (cal={calibrated}° -> {pulse}μs)")
            return True

    def move_to(self, angle: float, speed: Optional[float] = None, blocking: bool = True) -> bool:
        """Move servo to angle with optional smoothing (position) or timed movement (continuous)."""
        target = self._clamp_angle(float(angle))

        if self.continuous:
            return self._move_continuous(target, speed)

        # Position servo smoothing
        if speed is None or self._current_angle is None:
            return self.set_angle(target, validate=False)

        start = float(self._current_angle)
        delta = target - start
        if abs(delta) < 0.5:
            self._target_angle = target
            self._current_angle = target
            return True

        speed = max(1e-6, float(speed))
        move_time = abs(delta) / speed
        steps = max(int(move_time * self.smooth_hz), 1)
        step_delay = move_time / steps

        logger.debug(
            f"{self.name}: moving {start:.1f}° -> {target:.1f}° at {speed:.1f}°/s "
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
        """Stop continuous servo immediately."""
        if self.continuous:
            logger.info(f"{self.name}: Stopping continuous servo")
            self.pwm.set_pulse_width(self.channel, self.stop_pulse)

    def get_angle(self) -> Optional[float]:
        """Get current servo angle (estimated for continuous servos)."""
        if self.continuous:
            return float(self._estimated_position)
        return self._current_angle

    def disable(self) -> None:
        """Disable servo output (0% duty)."""
        logger.info(f"{self.name}: disabling output")
        self.pwm.disable_channel(self.channel)

    def __repr__(self) -> str:
        mode = "CONTINUOUS" if self.continuous else "POSITION"
        current = self.get_angle()
        return (
            f"Servo(name='{self.name}', channel={self.channel}, mode={mode}, "
            f"current={current}°, range={self.min_angle}°-{self.max_angle}°)"
        )