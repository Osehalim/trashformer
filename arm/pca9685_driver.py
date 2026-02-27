"""
PCA9685 PWM Driver for servo control.

Low-level control of the PCA9685 16-channel PWM controller used to drive servos.

Hardware: Adafruit PCA9685 PWM Servo Driver
Interface: I2C
"""

from __future__ import annotations

import time
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

try:
    import smbus2 as smbus
    I2C_AVAILABLE = True
except ImportError:
    I2C_AVAILABLE = False
    logger.warning("smbus2 not available - PCA9685 will run in simulation mode")


# PCA9685 Register Addresses
MODE1 = 0x00
MODE2 = 0x01
PRESCALE = 0xFE
LED0_ON_L = 0x06
ALL_LED_ON_L = 0xFA
ALL_LED_ON_H = 0xFB
ALL_LED_OFF_L = 0xFC
ALL_LED_OFF_H = 0xFD

# Mode register bits
RESTART = 0x80
SLEEP = 0x10
OUTDRV = 0x04
INVRT = 0x10


def _clamp_int(x: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, x))


class PCA9685:
    """
    PCA9685 PWM driver for servo control.

    Controls up to 16 channels with 12-bit resolution (0-4095).
    """

    def __init__(
        self,
        i2c_bus: int = 1,
        address: int = 0x40,
        frequency: int = 50,
        simulate: bool = False,
    ):
        self.address = address
        self.frequency = int(frequency)
        self.simulate = bool(simulate) or (not I2C_AVAILABLE)

        self.bus: Optional[smbus.SMBus] = None

        if self.simulate:
            logger.warning("PCA9685 running in SIMULATION mode")
            return

        try:
            self.bus = smbus.SMBus(i2c_bus)
            logger.info(f"PCA9685 initialized on bus {i2c_bus}, address 0x{address:02X}")
            self._initialize()
        except Exception as e:
            logger.error(f"Failed to initialize PCA9685: {e}")
            logger.warning("Falling back to simulation mode")
            self.simulate = True
            self.bus = None

    def _write_byte(self, register: int, value: int) -> None:
        if self.simulate or self.bus is None:
            return
        self.bus.write_byte_data(self.address, register, value & 0xFF)

    def _read_byte(self, register: int) -> int:
        if self.simulate or self.bus is None:
            return 0
        return int(self.bus.read_byte_data(self.address, register))

    def _initialize(self) -> None:
        """Initialize the PCA9685 chip."""
        # Reset MODE1
        self._write_byte(MODE1, 0x00)
        time.sleep(0.005)

        # Set PWM frequency
        self.set_pwm_freq(self.frequency)

        # Configure MODE2 for servo output (totem pole, non-inverted)
        mode2 = self._read_byte(MODE2)
        mode2 = mode2 | OUTDRV
        mode2 = mode2 & ~INVRT
        self._write_byte(MODE2, mode2)

        logger.debug("PCA9685 initialized successfully")

    def set_pwm_freq(self, freq_hz: int) -> None:
        """
        Set the PWM frequency (Hz). For servos typically 50 Hz.
        """
        freq_hz = int(freq_hz)

        if self.simulate:
            self.frequency = freq_hz
            logger.debug(f"[SIM] Set PWM frequency to {freq_hz}Hz")
            return

        # PCA9685 prescale formula:
        # prescale = round(osc_clock / (4096 * freq)) - 1
        # osc_clock default is ~25MHz
        osc_clock = 25_000_000.0
        prescaleval = (osc_clock / (4096.0 * float(freq_hz))) - 1.0
        prescale = int(prescaleval + 0.5)

        # Datasheet typical prescale bounds: 3..255
        prescale = _clamp_int(prescale, 3, 255)

        logger.debug(f"Setting PWM frequency to {freq_hz}Hz (prescale: {prescale})")

        oldmode = self._read_byte(MODE1)
        newmode = (oldmode & 0x7F) | SLEEP  # sleep
        self._write_byte(MODE1, newmode)
        self._write_byte(PRESCALE, prescale)
        self._write_byte(MODE1, oldmode)
        time.sleep(0.005)
        self._write_byte(MODE1, oldmode | RESTART)

        self.frequency = freq_hz

    def set_pwm(self, channel: int, on: int, off: int) -> None:
        """
        Set PWM timing for a channel.

        channel: 0-15
        on/off: 0-4095 (tick counts in the cycle)
        """
        if channel < 0 or channel > 15:
            raise ValueError(f"Channel must be 0-15, got {channel}")

        on = int(on)
        off = int(off)
        if not (0 <= on <= 4095) or not (0 <= off <= 4095):
            raise ValueError(f"ON/OFF must be 0-4095 (on={on}, off={off})")

        if self.simulate:
            logger.debug(f"[SIM] Channel {channel}: ON={on}, OFF={off}")
            return

        base_reg = LED0_ON_L + 4 * channel
        self._write_byte(base_reg + 0, on & 0xFF)
        self._write_byte(base_reg + 1, (on >> 8) & 0xFF)
        self._write_byte(base_reg + 2, off & 0xFF)
        self._write_byte(base_reg + 3, (off >> 8) & 0xFF)

    def set_pulse_width(self, channel: int, pulse_width_us: int) -> None:
        """
        Set servo position using pulse width in microseconds.
        Typical servo range: ~500-2500us.
        """
        pulse_width_us = int(pulse_width_us)
        if pulse_width_us < 0 or pulse_width_us > 10000:
            raise ValueError(f"Pulse width must be 0-10000us, got {pulse_width_us}")

        # One PWM period in microseconds
        period_us = 1_000_000.0 / float(self.frequency)
        # Microseconds per PCA tick
        us_per_tick = period_us / 4096.0

        ticks = int(round(pulse_width_us / us_per_tick))
        ticks = _clamp_int(ticks, 0, 4095)

        logger.debug(f"Channel {channel}: {pulse_width_us}us -> {ticks} ticks @ {self.frequency}Hz")
        self.set_pwm(channel, 0, ticks)

    def disable_channel(self, channel: int) -> None:
        """
        Disable a channel by setting it to 0% duty cycle.
        (For most servos this effectively stops holding torque / pulses.)
        """
        self.set_pwm(channel, 0, 0)

    def set_all_pwm(self, on: int, off: int) -> None:
        if self.simulate:
            logger.debug(f"[SIM] All channels: ON={on}, OFF={off}")
            return

        on = _clamp_int(int(on), 0, 4095)
        off = _clamp_int(int(off), 0, 4095)

        self._write_byte(ALL_LED_ON_L, on & 0xFF)
        self._write_byte(ALL_LED_ON_H, (on >> 8) & 0xFF)
        self._write_byte(ALL_LED_OFF_L, off & 0xFF)
        self._write_byte(ALL_LED_OFF_H, (off >> 8) & 0xFF)

    def reset(self) -> None:
        """Reset all PWM channels to 0."""
        logger.info("Resetting all PWM channels")
        self.set_all_pwm(0, 0)

    def close(self) -> None:
        """Clean up and close I2C bus."""
        if not self.simulate and self.bus:
            logger.info("Closing PCA9685")
            self.reset()
            self.bus.close()
            self.bus = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()