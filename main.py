#!/usr/bin/env python3
"""
main.py - Trashformer Robot Main Controller

This is the main entry point for the robot.
Coordinates all subsystems and provides different operating modes.

Usage:
  python3 main.py                    # Interactive mode selection
  python3 main.py --mode teleop      # Keyboard teleop
  python3 main.py --mode gamepad     # PS5 controller
  python3 main.py --mode autonomous  # Autonomous operation
  python3 main.py --mode test        # Test all systems
"""

from __future__ import annotations

import sys
import argparse
import signal
import time
from utils.logger import setup_logging, get_logger
from utils.config_loader import load_config

logger = get_logger(__name__)


class RobotController:
    """
    Main robot controller - coordinates all subsystems.
    """
    
    def __init__(self, config):
        self.config = config
        self.running = False
        
        # Subsystems (initialized on demand)
        self.drive = None
        self.arm = None
        self.sensors = None
        self.vision = None
        
        logger.info("RobotController initialized")
    
    def initialize_drive(self):
        """Initialize drive system."""
        if self.drive is None:
            from drive.drive_controller import DriveController
            self.drive = DriveController(config=self.config, simulate=False)
            logger.info("✓ Drive system initialized")
    
    def initialize_arm(self):
        """Initialize arm system."""
        if self.arm is None:
            from arm.arm_controller import ArmController
            self.arm = ArmController(config=self.config, simulate=False)
            logger.info("✓ Arm system initialized")
    
    def initialize_sensors(self):
        """Initialize sensor system."""
        if self.sensors is None:
            from sensors.sensor_manager import SensorManager
            self.sensors = SensorManager(config=self.config, simulate=False)
            self.sensors.start()
            logger.info("✓ Sensor system initialized")
    
    def initialize_vision(self):
        """Initialize vision system."""
        if self.vision is None:
            # TODO: Add vision system when ready
            logger.info("✓ Vision system (placeholder)")
    
    def mode_teleop_keyboard(self):
        """Run keyboard teleoperation mode."""
        logger.info("Starting KEYBOARD TELEOP mode")
        
        self.initialize_drive()
        
        from teleop.keyboard_teleop import KeyboardTeleop
        
        with KeyboardTeleop(config=self.config, simulate=False) as teleop:
            teleop.run()
    
    def mode_teleop_gamepad(self):
        """Run gamepad teleoperation mode."""
        logger.info("Starting GAMEPAD TELEOP mode")
        
        self.initialize_drive()
        
        # Check if gamepad is connected
        try:
            from inputs import devices
            if not devices.gamepads:
                logger.error("No gamepad detected!")
                logger.info("Connect your PS5 controller via Bluetooth")
                logger.info("Run: bluetoothctl -> connect <MAC_ADDRESS>")
                return
        except ImportError:
            logger.error("'inputs' library not installed")
            logger.info("Install with: pip3 install inputs --break-system-packages")
            return
        
        from teleop.teleop_gamepad import GamepadTeleop
        
        with GamepadTeleop(config=self.config, simulate=False) as teleop:
            teleop.run()
    
    def mode_autonomous(self):
        """Run autonomous operation mode."""
        logger.info("Starting AUTONOMOUS mode")
        
        # Initialize all systems
        self.initialize_drive()
        self.initialize_arm()
        self.initialize_sensors()
        
        logger.info("Running autonomous trash collection...")
        
        try:
            while self.running:
                # Get sensor data
                distance = self.sensors.get_distance()
                
                # Simple autonomous behavior
                if distance and distance < 0.3:
                    # Obstacle ahead - stop
                    logger.info(f"Obstacle at {distance:.2f}m - stopping")
                    self.drive.stop()
                    time.sleep(1)
                    
                    # Back up
                    logger.info("Backing up...")
                    self.drive.backward(distance=0.2, speed=0.2)
                    
                    # Turn
                    logger.info("Turning...")
                    self.drive.rotate(angle_degrees=45, speed=30)
                else:
                    # Path clear - drive forward slowly
                    logger.info("Path clear - driving forward")
                    self.drive.forward(distance=0.1, speed=0.2)
                
                time.sleep(0.1)
        
        except KeyboardInterrupt:
            logger.info("Autonomous mode stopped")
        
        finally:
            self.drive.stop()
    
    def mode_test(self):
        """Test all robot systems."""
        logger.info("Starting SYSTEM TEST mode")
        
        results = {}
        
        # Test drive
        logger.info("\n" + "="*60)
        logger.info("Testing Drive System")
        logger.info("="*60)
        try:
            self.initialize_drive()
            logger.info("✓ Drive initialized")
            
            # Test motors briefly
            logger.info("Testing motors (2 seconds)...")
            self.drive.set_motor_speeds(0.2, 0.2)
            time.sleep(2)
            self.drive.stop()
            
            results["Drive"] = True
        except Exception as e:
            logger.error(f"✗ Drive failed: {e}")
            results["Drive"] = False
        
        # Test arm
        logger.info("\n" + "="*60)
        logger.info("Testing Arm System")
        logger.info("="*60)
        try:
            self.initialize_arm()
            logger.info("✓ Arm initialized")
            
            # Test servos briefly
            logger.info("Testing servos...")
            self.arm.move_to_home()
            time.sleep(1)
            
            results["Arm"] = True
        except Exception as e:
            logger.error(f"✗ Arm failed: {e}")
            results["Arm"] = False
        
        # Test sensors
        logger.info("\n" + "="*60)
        logger.info("Testing Sensor System")
        logger.info("="*60)
        try:
            self.initialize_sensors()
            logger.info("✓ Sensors initialized")
            
            # Read sensors
            distance = self.sensors.get_distance()
            logger.info(f"Distance: {distance}")
            
            results["Sensors"] = True
        except Exception as e:
            logger.error(f"✗ Sensors failed: {e}")
            results["Sensors"] = False
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("TEST SUMMARY")
        logger.info("="*60)
        for system, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            logger.info(f"{system:20s} {status}")
        
        if all(results.values()):
            logger.info("\n✓ All systems operational!")
        else:
            logger.error("\n✗ Some systems failed")
    
    def mode_interactive(self):
        """Interactive mode selection menu."""
        print("\n" + "="*60)
        print("TRASHFORMER ROBOT - MODE SELECTION")
        print("="*60)
        print()
        print("Select operating mode:")
        print("  1. Keyboard Teleop (WASD control via SSH)")
        print("  2. Gamepad Teleop (PS5 controller)")
        print("  3. Autonomous (automatic trash collection)")
        print("  4. System Test (test all systems)")
        print("  5. Exit")
        print()
        
        try:
            choice = input("Enter choice (1-5): ").strip()
            
            if choice == "1":
                self.mode_teleop_keyboard()
            elif choice == "2":
                self.mode_teleop_gamepad()
            elif choice == "3":
                self.running = True
                self.mode_autonomous()
            elif choice == "4":
                self.mode_test()
            elif choice == "5":
                logger.info("Exiting...")
            else:
                logger.error("Invalid choice")
        
        except KeyboardInterrupt:
            logger.info("\nExiting...")
    
    def shutdown(self):
        """Shutdown all systems gracefully."""
        logger.info("Shutting down robot systems...")
        
        self.running = False
        
        if self.drive:
            self.drive.close()
        if self.arm:
            self.arm.close()
        if self.sensors:
            self.sensors.close()
        
        logger.info("✓ Shutdown complete")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


def main() -> int:
    # Setup logging
    setup_logging()
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Trashformer Robot Controller")
    parser.add_argument(
        "--mode",
        choices=["teleop", "gamepad", "autonomous", "test", "interactive"],
        default="interactive",
        help="Operating mode"
    )
    args = parser.parse_args()
    
    # Load configuration
    cfg = load_config("config/default.yaml")
    
    # Banner
    logger.info("\n" + "="*60)
    logger.info("TRASHFORMER ROBOT")
    logger.info("="*60)
    logger.info(f"Mode: {args.mode.upper()}")
    logger.info("="*60 + "\n")
    
    # Create robot controller
    with RobotController(config=cfg) as robot:
        # Setup signal handler for graceful shutdown
        def signal_handler(sig, frame):
            logger.info("\nShutdown signal received")
            robot.running = False
            robot.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Run selected mode
        try:
            if args.mode == "teleop":
                robot.mode_teleop_keyboard()
            elif args.mode == "gamepad":
                robot.mode_teleop_gamepad()
            elif args.mode == "autonomous":
                robot.running = True
                robot.mode_autonomous()
            elif args.mode == "test":
                robot.mode_test()
            elif args.mode == "interactive":
                robot.mode_interactive()
        
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            return 1
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())