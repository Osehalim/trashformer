#!/usr/bin/env python3
"""
ToF-Only Trash Detection System

Uses a scanning ToF sensor (no camera) to find and approach objects.

Hardware:
- 1x VL53L1X ToF sensor on a servo
- Servo rotates sensor to scan area
- Robot drives toward detected objects
"""

from __future__ import annotations

import time
from typing import List, Tuple, Optional


class ScanningToFDetector:
    """
    Trash detection using a single ToF sensor on a rotating servo.
    """
    
    def __init__(self, tof_sensor, scan_servo):
        self.tof = tof_sensor
        self.servo = scan_servo
        
        # Configuration
        self.scan_range = (-90, 90)  # degrees
        self.scan_step = 10          # degrees per reading
        self.min_distance = 0.1      # meters (too close)
        self.max_distance = 2.0      # meters (too far)
        self.floor_height = 0.05     # meters (objects on floor)
    
    def scan_area(self) -> List[Tuple[int, float]]:
        """
        Scan the area and return list of (angle, distance) for detected objects.
        
        Returns:
            List of (angle_degrees, distance_meters)
        """
        print("\n🔍 Scanning for objects...")
        
        detections = []
        
        start_angle, end_angle = self.scan_range
        
        for angle in range(start_angle, end_angle + 1, self.scan_step):
            # Rotate servo to angle
            self.servo.move_to(angle)
            time.sleep(0.1)  # Let servo settle
            
            # Take ToF measurement
            distance = self.tof.get_distance()
            
            print(f"  {angle:+4d}°: {distance:.2f}m")
            
            # Filter valid detections
            if self.min_distance < distance < self.max_distance:
                detections.append((angle, distance))
        
        # Return to center
        self.servo.move_to(0)
        
        print(f"\n✓ Found {len(detections)} potential objects")
        return detections
    
    def find_nearest_object(self) -> Optional[Tuple[int, float]]:
        """
        Scan and return the nearest object.
        
        Returns:
            (angle, distance) of nearest object, or None
        """
        detections = self.scan_area()
        
        if not detections:
            print("❌ No objects detected")
            return None
        
        # Find closest
        nearest = min(detections, key=lambda x: x[1])
        angle, distance = nearest
        
        print(f"\n🎯 Nearest object: {angle:+d}° at {distance:.2f}m")
        return nearest
    
    def filter_floor_objects(self, detections: List[Tuple[int, float]], 
                            robot_height: float = 0.2) -> List[Tuple[int, float]]:
        """
        Filter detections to only include objects on the floor.
        
        This is approximate - assumes objects closer than walls are on floor.
        For better accuracy, need a tilted ToF or height-measuring sensor.
        
        Args:
            detections: List of (angle, distance)
            robot_height: Height of ToF sensor above ground
            
        Returns:
            Filtered list of likely floor objects
        """
        if not detections:
            return []
        
        # Simple heuristic: Objects significantly closer than the background
        # are likely on the floor rather than walls
        
        distances = [d for _, d in detections]
        avg_distance = sum(distances) / len(distances)
        
        # Keep objects that are much closer than average (likely floor objects)
        floor_threshold = avg_distance * 0.6  # 60% of average
        
        floor_objects = [
            (angle, dist) for angle, dist in detections 
            if dist < floor_threshold
        ]
        
        print(f"  Floor filter: {len(floor_objects)}/{len(detections)} objects")
        return floor_objects if floor_objects else detections


class SimpleTrashRobot:
    """
    Simple autonomous trash collection robot using ToF only.
    """
    
    def __init__(self, detector, drive, arm):
        self.detector = detector
        self.drive = drive
        self.arm = arm
    
    def search_and_collect(self):
        """
        Main autonomous loop: search, approach, grab, return.
        """
        print("\n" + "=" * 60)
        print("🤖 STARTING AUTONOMOUS TRASH COLLECTION")
        print("=" * 60)
        
        while True:
            # 1. Scan for objects
            nearest = self.detector.find_nearest_object()
            
            if nearest is None:
                print("\n✓ Area clear - rotating to search more...")
                self.drive.rotate(45)  # Turn to scan new area
                continue
            
            angle, distance = nearest
            
            # 2. Approach object
            print(f"\n📍 Approaching object at {angle:+d}° / {distance:.2f}m")
            
            # Turn to face object
            self.drive.rotate(angle)
            time.sleep(1)
            
            # Drive forward (stop a bit before the object)
            approach_distance = distance - 0.15  # Stop 15cm before
            if approach_distance > 0:
                self.drive.forward(approach_distance)
                time.sleep(2)
            
            # 3. Verify object is still there
            print("\n🔍 Verifying object...")
            verification = self.detector.tof.get_distance()
            
            if verification > 0.3:
                print(f"⚠️  Object moved or too far ({verification:.2f}m)")
                continue
            
            # 4. Pick up object
            print("\n🦾 Attempting pickup...")
            self.pickup_sequence()
            
            # 5. Return to start (simplified)
            print("\n🔄 Returning to base...")
            self.drive.rotate(180)
            self.drive.forward(1.0)  # Drive back
            
            # 6. Drop trash
            print("\n🗑️  Dropping trash...")
            self.drop_sequence()
            
            # 7. Turn back around
            self.drive.rotate(180)
            
            print("\n✓ Cycle complete! Searching for next object...")
            time.sleep(1)
    
    def pickup_sequence(self):
        """Execute pickup sequence."""
        # Open gripper
        self.arm.open_gripper()
        time.sleep(0.5)
        
        # Lower arm to ground
        self.arm.move_to_angles(shoulder=30, elbow=0, gripper=0)
        time.sleep(1)
        
        # Close gripper
        self.arm.close_gripper()
        time.sleep(0.5)
        
        # Lift arm
        self.arm.move_to_angles(shoulder=90, elbow=0, gripper=90)
        time.sleep(1)
    
    def drop_sequence(self):
        """Execute drop sequence."""
        # Move to drop position
        self.arm.move_to_angles(shoulder=120, elbow=90, gripper=90)
        time.sleep(1)
        
        # Open gripper
        self.arm.open_gripper()
        time.sleep(0.5)
        
        # Return to home
        self.arm.home()
        time.sleep(1)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # This is pseudocode showing how to use the system
    
    # Initialize hardware (you'll need actual sensor objects)
    # tof_sensor = VL53L1X(i2c_address=0x29)
    # scan_servo = Servo(channel=3, ...)  # Extra servo for scanning
    # arm = ArmController(...)
    # drive = DriveController(...)
    
    # Create detector
    # detector = ScanningToFDetector(tof_sensor, scan_servo)
    
    # Test scanning
    # detections = detector.scan_area()
    # print(f"\nFound {len(detections)} objects:")
    # for angle, dist in detections:
    #     print(f"  {angle:+4d}° at {dist:.2f}m")
    
    # Or run autonomous
    # robot = SimpleTrashRobot(detector, drive, arm)
    # robot.search_and_collect()
    
    print("Example implementation - see code for usage")