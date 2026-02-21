#!/usr/bin/env python3
"""
Arm control demo script.

Demonstrates how to use the arm controller for the Trashformer robot.
Run this script to test arm movements in simulation or on real hardware.
"""

import time
import argparse
from utils.logger import setup_logging, get_logger
from utils.config_loader import load_config
from arm import ArmController

logger = get_logger(__name__)


def demo_basic_movement(arm: ArmController):
    """Demonstrate basic arm movements."""
    logger.info("=== DEMO: Basic Movement ===")
    
    # Move to home
    logger.info("Moving to home position")
    arm.home(speed=50)
    time.sleep(1)
    
    # Move to ready position
    logger.info("Moving to ready position")
    arm.go_to_pose('ready', speed=40)
    time.sleep(1)
    
    # Move to rest position
    logger.info("Moving to rest position")
    arm.go_to_pose('rest', speed=40)
    time.sleep(1)


def demo_gripper(arm: ArmController):
    """Demonstrate gripper control."""
    logger.info("=== DEMO: Gripper Control ===")
    
    # Open and close gripper
    logger.info("Opening gripper")
    arm.open_gripper(speed=30)
    time.sleep(1)
    
    logger.info("Closing gripper")
    arm.close_gripper(speed=30)
    time.sleep(1)
    
    logger.info("Partial grip")
    arm.set_gripper(45, speed=30)
    time.sleep(1)
    
    logger.info("Opening gripper")
    arm.open_gripper(speed=30)
    time.sleep(1)


def demo_manual_control(arm: ArmController):
    """Demonstrate manual servo control."""
    logger.info("=== DEMO: Manual Control ===")
    
    # Set individual angles
    logger.info("Setting base to 45°")
    arm.set_angles({'base': 45})
    time.sleep(1)
    
    logger.info("Setting base to 135°")
    arm.set_angles({'base': 135})
    time.sleep(1)
    
    logger.info("Setting base back to center")
    arm.set_angles({'base': 90})
    time.sleep(1)
    
    # Move multiple servos
    logger.info("Moving shoulder and elbow together")
    arm.move_to_angles({
        'shoulder': 120,
        'elbow': 60
    }, speed=30)
    time.sleep(1)


def demo_pickup_sequence(arm: ArmController):
    """Demonstrate trash pickup sequence."""
    logger.info("=== DEMO: Trash Pickup Sequence ===")
    
    pickup_sequence = [
        ('ready', 40, 0.5),           # Get ready
        ('approach_trash', 30, 0.5),  # Approach the trash
        ('grab_trash', 20, 1.0),      # Grab it (slower, pause to grip)
        ('lift_trash', 35, 0.5),      # Lift up
        ('transport', 40, 0.5),       # Move to transport position
        ('over_bin', 35, 0.5),        # Position over bin
        ('release', 20, 1.0),         # Release trash
        ('home', 40, 0.0),            # Return home
    ]
    
    logger.info("Executing trash pickup sequence...")
    success = arm.execute_sequence(pickup_sequence, pause_between=0.3)
    
    if success:
        logger.info("Pickup sequence completed successfully!")
    else:
        logger.error("Pickup sequence failed")


def demo_reaching(arm: ArmController):
    """Demonstrate reaching in different directions."""
    logger.info("=== DEMO: Reaching Movements ===")
    
    directions = ['reach_forward', 'reach_left', 'reach_right', 'reach_up']
    
    for direction in directions:
        logger.info(f"Reaching: {direction}")
        arm.go_to_pose(direction, speed=40)
        time.sleep(1.5)
    
    # Return home
    logger.info("Returning home")
    arm.home(speed=40)
    time.sleep(1)


def demo_wave(arm: ArmController):
    """Fun demo - make the arm wave."""
    logger.info("=== DEMO: Waving ===")
    
    # Go to wave position
    arm.go_to_pose('wave', speed=40)
    time.sleep(0.5)
    
    # Wave by rotating wrist back and forth
    logger.info("Waving...")
    for _ in range(3):
        arm.set_angles({'wrist': 60}, validate=True)
        time.sleep(0.3)
        arm.set_angles({'wrist': 120}, validate=True)
        time.sleep(0.3)
    
    # Return to center
    arm.set_angles({'wrist': 90}, validate=True)
    time.sleep(0.5)


def demo_calibration(arm: ArmController):
    """Demonstrate calibration routine."""
    logger.info("=== DEMO: Calibration ===")
    
    logger.info("Testing calibration poses...")
    
    # Go through calibration positions
    for pose in ['calibrate_min', 'calibrate_center', 'calibrate_max']:
        logger.info(f"Moving to: {pose}")
        arm.go_to_pose(pose, speed=20)
        time.sleep(2)
    
    # Return home
    logger.info("Returning to home")
    arm.home(speed=30)


def interactive_mode(arm: ArmController):
    """Interactive mode - control arm from keyboard."""
    logger.info("=== INTERACTIVE MODE ===")
    logger.info("Available commands:")
    logger.info("  h - Home position")
    logger.info("  r - Ready position")
    logger.info("  o - Open gripper")
    logger.info("  c - Close gripper")
    logger.info("  p - Pickup sequence")
    logger.info("  w - Wave")
    logger.info("  l - List all poses")
    logger.info("  [pose_name] - Go to named pose")
    logger.info("  q - Quit")
    
    while True:
        try:
            cmd = input("\nEnter command: ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 'h':
                arm.home()
            elif cmd == 'r':
                arm.go_to_pose('ready')
            elif cmd == 'o':
                arm.open_gripper()
            elif cmd == 'c':
                arm.close_gripper()
            elif cmd == 'p':
                demo_pickup_sequence(arm)
            elif cmd == 'w':
                demo_wave(arm)
            elif cmd == 'l':
                poses = arm.list_poses()
                logger.info(f"Available poses ({len(poses)}):")
                for pose in sorted(poses):
                    logger.info(f"  - {pose}")
            elif cmd in arm.list_poses():
                arm.go_to_pose(cmd)
            else:
                logger.warning(f"Unknown command: {cmd}")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Error: {e}")
    
    logger.info("Exiting interactive mode")


def main():
    """Main demo function."""
    parser = argparse.ArgumentParser(description='Arm Control Demo')
    parser.add_argument('--simulate', action='store_true',
                       help='Run in simulation mode (no hardware)')
    parser.add_argument('--demo', choices=['basic', 'gripper', 'manual', 
                                          'pickup', 'reach', 'wave', 
                                          'calibrate', 'all', 'interactive'],
                       default='all',
                       help='Which demo to run')
    parser.add_argument('--config', default='config/default.yaml',
                       help='Configuration file path')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    logger.info("=" * 60)
    logger.info("Trashformer Arm Control Demo")
    logger.info("=" * 60)
    logger.info(f"Mode: {'SIMULATION' if args.simulate else 'HARDWARE'}")
    logger.info(f"Config: {args.config}")
    logger.info("")
    
    # Load configuration
    config = load_config(args.config)
    
    # Create arm controller
    try:
        with ArmController(config=config, simulate=args.simulate) as arm:
            logger.info(f"Arm controller initialized: {arm}")
            logger.info(f"Available poses: {len(arm.list_poses())}")
            logger.info("")
            
            # Run selected demo
            if args.demo == 'all':
                logger.info("Running all demos...")
                logger.info("")
                
                demo_basic_movement(arm)
                time.sleep(1)
                
                demo_gripper(arm)
                time.sleep(1)
                
                demo_manual_control(arm)
                time.sleep(1)
                
                demo_pickup_sequence(arm)
                time.sleep(1)
                
                demo_reaching(arm)
                time.sleep(1)
                
                demo_wave(arm)
                time.sleep(1)
                
            elif args.demo == 'basic':
                demo_basic_movement(arm)
            elif args.demo == 'gripper':
                demo_gripper(arm)
            elif args.demo == 'manual':
                demo_manual_control(arm)
            elif args.demo == 'pickup':
                demo_pickup_sequence(arm)
            elif args.demo == 'reach':
                demo_reaching(arm)
            elif args.demo == 'wave':
                demo_wave(arm)
            elif args.demo == 'calibrate':
                demo_calibration(arm)
            elif args.demo == 'interactive':
                interactive_mode(arm)
            
            logger.info("")
            logger.info("Demo complete!")
            logger.info("Returning arm to home position...")
            
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Error during demo: {e}")
        raise
    
    logger.info("Goodbye!")


if __name__ == "__main__":
    main()