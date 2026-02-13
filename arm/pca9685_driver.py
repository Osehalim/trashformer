"""
PCA9685 PWM Driver for servo control.

This module provides low-level control of the PCA9685 16-channel PWM controller
used to drive servos for the robot arm.

Hardware: Adafruit PCA9685 PWM Servo Driver
Interface: I2C
"""

import time
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

try:
    import smbus2 as smbus
    I2C_AVAILABLE = True
except ImportError:
    logger.warning("smbus2 not available - PCA9685 will run in simulation mode")
    I2C_AVAILABLE = False


# PCA9685 Register Addresses
MODE1 = 0x00
MODE2 = 0x01
SUBADR1 = 0x02
SUBADR2 = 0x03
SUBADR3 = 0x04
PRESCALE = 0xFE
LED0_ON_L = 0x06
LED0_ON_H = 0x07
LED0_OFF_L = 0x08
LED0_OFF_H = 0x09
ALL_LED_ON_L = 0xFA
ALL_LED_ON_H = 0xFB
ALL_LED_OFF_L = 0xFC
ALL_LED_OFF_H = 0xFD

# Mode register bits
RESTART = 0x80
SLEEP = 0x10
ALLCALL = 0x01
INVRT = 0x10
OUTDRV = 0x04


class PCA9685:
    """
    PCA9685 PWM driver for servo control.
    
    This class provides an interface to the PCA9685 16-channel PWM controller.
    It can control up to 16 servos with 12-bit resolution (0-4095).
    """
    
    def __init__(self, 
                 i2c_bus: int = 1, 
                 address: int = 0x40,
                 frequency: int = 50,
                 simulate: bool = False):
        """
        Initialize PCA9685 controller.
        
        Args:
            i2c_bus: I2C bus number (typically 1 on Raspberry Pi)
            address: I2C address of PCA9685 (default 0x40)
            frequency: PWM frequency in Hz (default 50Hz for servos)
            simulate: Run in simulation mode without hardware
        """
        self.address = address
        self.frequency = frequency
        self.simulate = simulate or not I2C_AVAILABLE
        
        if self.simulate:
            logger.warning("PCA9685 running in SIMULATION mode")
            self.bus = None
        else:
            try:
                self.bus = smbus.SMBus(i2c_bus)
                logger.info(f"PCA9685 initialized on bus {i2c_bus}, address 0x{address:02X}")
                self._initialize()
            except Exception as e:
                logger.error(f"Failed to initialize PCA9685: {e}")
                logger.warning("Falling back to simulation mode")
                self.simulate = True
                self.bus = None
    
    def _initialize(self):
        """Initialize the PCA9685 chip."""
        if self.simulate:
            return
        
        try:
            # Reset
            self._write_byte(MODE1, 0x00)
            time.sleep(0.005)
            
            # Set PWM frequency
            self.set_pwm_freq(self.frequency)
            
            # Configure for servo output
            mode2 = self._read_byte(MODE2)
            mode2 = mode2 | OUTDRV  # Totem pole output
            mode2 = mode2 & ~INVRT  # Not inverted
            self._write_byte(MODE2, mode2)
            
            logger.debug("PCA9685 initialized successfully")
            
        except Exception as e:
            logger.error(f"Error during PCA9685 initialization: {e}")
            raise
    
    def _write_byte(self, register: int, value: int):
        """Write a byte to a register."""
        if not self.simulate:
            self.bus.write_byte_data(self.address, register, value)
    
    def _read_byte(self, register: int) -> int:
        """Read a byte from a register."""
        if not self.simulate:
            return self.bus.read_byte_data(self.address, register)
        return 0
    
    def set_pwm_freq(self, freq_hz: int):
        """
        Set the PWM frequency.
        
        Args:
            freq_hz: Frequency in Hz (typically 50Hz for servos)
        """
        if self.simulate:
            logger.debug(f"[SIM] Set PWM frequency to {freq_hz}Hz")
            return
        
        try:
            # Calculate prescale value
            prescaleval = 25000000.0    # 25MHz internal oscillator
            prescaleval /= 4096.0       # 12-bit resolution
            prescaleval /= float(freq_hz)
            prescaleval -= 1.0
            
            prescale = int(prescaleval + 0.5)
            
            logger.debug(f"Setting PWM frequency to {freq_hz}Hz (prescale: {prescale})")
            
            # Must be in sleep mode to set prescale
            oldmode = self._read_byte(MODE1)
            newmode = (oldmode & 0x7F) | SLEEP
            self._write_byte(MODE1, newmode)
            
            # Set prescale
            self._write_byte(PRESCALE, prescale)
            
            # Wake up
            self._write_byte(MODE1, oldmode)
            time.sleep(0.005)
            
            # Restart
            self._write_byte(MODE1, oldmode | RESTART)
            
            self.frequency = freq_hz
            
        except Exception as e:
            logger.error(f"Error setting PWM frequency: {e}")
            raise
    
    def set_pwm(self, channel: int, on: int, off: int):
        """
        Set PWM for a specific channel.
        
        Args:
            channel: Channel number (0-15)
            on: When to turn on (0-4095)
            off: When to turn off (0-4095)
        """
        if channel < 0 or channel > 15:
            raise ValueError(f"Channel must be 0-15, got {channel}")
        
        if on < 0 or on > 4095:
            raise ValueError(f"ON value must be 0-4095, got {on}")
        
        if off < 0 or off > 4095:
            raise ValueError(f"OFF value must be 0-4095, got {off}")
        
        if self.simulate:
            logger.debug(f"[SIM] Channel {channel}: ON={on}, OFF={off}")
            return
        
        try:
            # Calculate register addresses for this channel
            base_reg = LED0_ON_L + 4 * channel
            
            # Write ON value (low byte, high byte)
            self._write_byte(base_reg, on & 0xFF)
            self._write_byte(base_reg + 1, on >> 8)
            
            # Write OFF value (low byte, high byte)
            self._write_byte(base_reg + 2, off & 0xFF)
            self._write_byte(base_reg + 3, off >> 8)
            
        except Exception as e:
            logger.error(f"Error setting PWM on channel {channel}: {e}")
            raise
    
    def set_pulse_width(self, channel: int, pulse_width_us: int):
        """
        Set servo position using pulse width in microseconds.
        
        Args:
            channel: Channel number (0-15)
            pulse_width_us: Pulse width in microseconds (typically 500-2500)
        """
        if pulse_width_us < 0 or pulse_width_us > 10000:
            raise ValueError(f"Pulse width must be 0-10000μs, got {pulse_width_us}")
        
        # Calculate pulse length in 4096 steps
        # At 50Hz, each cycle is 20ms = 20000μs
        pulse_length = 1000000.0 / self.frequency  # Pulse cycle length in μs
        pulse_length /= 4096.0  # 12-bit resolution
        
        pulse = int(pulse_width_us / pulse_length)
        
        logger.debug(f"Channel {channel}: {pulse_width_us}μs -> pulse value {pulse}")
        
        self.set_pwm(channel, 0, pulse)
    
    def set_duty_cycle(self, channel: int, duty_cycle: float):
        """
        Set PWM duty cycle as a percentage.
        
        Args:
            channel: Channel number (0-15)
            duty_cycle: Duty cycle 0.0-100.0 (percentage)
        """
        if duty_cycle < 0 or duty_cycle > 100:
            raise ValueError(f"Duty cycle must be 0-100%, got {duty_cycle}")
        
        pulse = int(4095 * duty_cycle / 100.0)
        self.set_pwm(channel, 0, pulse)
    
    def set_all_pwm(self, on: int, off: int):
        """
        Set PWM for all channels simultaneously.
        
        Args:
            on: When to turn on (0-4095)
            off: When to turn off (0-4095)
        """
        if self.simulate:
            logger.debug(f"[SIM] All channels: ON={on}, OFF={off}")
            return
        
        try:
            self._write_byte(ALL_LED_ON_L, on & 0xFF)
            self._write_byte(ALL_LED_ON_H, on >> 8)
            self._write_byte(ALL_LED_OFF_L, off & 0xFF)
            self._write_byte(ALL_LED_OFF_H, off >> 8)
        except Exception as e:
            logger.error(f"Error setting all PWM: {e}")
            raise
    
    def reset(self):
        """Reset all PWM channels to 0."""
        logger.info("Resetting all PWM channels")
        self.set_all_pwm(0, 0)
    
    def close(self):
        """Clean up and close I2C bus."""
        if not self.simulate and self.bus:
            logger.info("Closing PCA9685")
            self.reset()
            self.bus.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


if __name__ == "__main__":
    # Test the PCA9685 driver
    from utils.logger import setup_logging
    setup_logging()
    
    logger.info("Testing PCA9685 driver")
    
    # Create PCA9685 instance
    pwm = PCA9685(i2c_bus=1, address=0x40, frequency=50, simulate=True)
    
    try:
        # Test setting pulse width (typical servo range)
        logger.info("Testing pulse width control")
        pwm.set_pulse_width(0, 1500)  # Center position
        time.sleep(1)
        
        pwm.set_pulse_width(0, 1000)  # Min position
        time.sleep(1)
        
        pwm.set_pulse_width(0, 2000)  # Max position
        time.sleep(1)
        
        # Test duty cycle
        logger.info("Testing duty cycle control")
        pwm.set_duty_cycle(1, 50)  # 50% duty cycle
        
        logger.info("Test complete")
        
    finally:
        pwm.close()