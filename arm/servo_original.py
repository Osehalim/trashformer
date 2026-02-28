"""
Servo control via PCA9685.

Provides:
- angle limits
- pulse mapping
- optional invert/offset calibration
- smooth movement
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

    Notes:
    - Angles are logical angles (degrees) you define for the robot.
    - Use invert + offset to fix physical mounting differences.
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
        smooth_hz: float = 10.0,  # updates/sec when smoothing
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

        self._current_angle: Optional[float] = None
        self._target_angle: Optional[float] = None

        logger.info(
            f"Initialized {self.name} servo on channel {self.channel} "
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
        """
        Apply offset/invert to logical angle before mapping to pulse.
        This lets you keep poses stable even if a servo is mounted flipped.
        """
        a = float(angle) + self.offset_deg
        if self.invert:
            # mirror within [min_angle, max_angle]
            a = self.max_angle - (a - self.min_angle)
        return a

    def _angle_to_pulse(self, angle: float) -> int:
        # Prevent bad config divide-by-zero
        if self.max_angle == self.min_angle:
            logger.warning(f"{self.name}: max_angle == min_angle; defaulting to midpoint pulse")
            return int(round((self.min_pulse + self.max_pulse) / 2))

        # Normalize to 0..1
        ratio = (angle - self.min_angle) / (self.max_angle - self.min_angle)
        ratio = _clamp(ratio, 0.0, 1.0)
        pulse = self.min_pulse + ratio * (self.max_pulse - self.min_pulse)
        pulse_i = int(round(pulse))

        # Final pulse clamp
        if pulse_i < self.min_pulse:
            pulse_i = self.min_pulse
        if pulse_i > self.max_pulse:
            pulse_i = self.max_pulse
        return pulse_i

    def set_angle(self, angle: float, validate: bool = True) -> bool:
        """
        Set servo to specific angle immediately.
        """
        a = float(angle)
        if validate:
            a = self._clamp_angle(a)

        calibrated = self._apply_calibration(a)
        pulse = self._angle_to_pulse(calibrated)

        self.pwm.set_pulse_width(self.channel, pulse)

        self._current_angle = a
        self._target_angle = a

        logger.debug(f"{self.name}: set {a}° (cal={calibrated}° -> {pulse}us)")
        return True

    def move_to(self, angle: float, speed: Optional[float] = None, blocking: bool = True) -> bool:
        """
        Move servo to angle with optional smoothing.
        speed: degrees/second. None => instant.
        """
        target = self._clamp_angle(float(angle))

        # Instant if no speed or unknown current
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
        return self.move_to(self.home_angle, speed, blocking)

    def neutral(self, speed: Optional[float] = None, blocking: bool = True) -> bool:
        return self.move_to(self.neutral_angle, speed, blocking)

    def get_angle(self) -> Optional[float]:
        return self._current_angle

    def disable(self) -> None:
        """
        Disable servo output (0% duty).
        """
        logger.info(f"{self.name}: disabling output")
        self.pwm.disable_channel(self.channel)

    def __repr__(self) -> str:
        return (
            f"Servo(name='{self.name}', channel={self.channel}, "
            f"current={self._current_angle}°, range={self.min_angle}°-{self.max_angle}°)"
        )