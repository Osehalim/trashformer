# Vision Module

This module handles real-time camera input, trash object detection using machine learning, and visual tracking of detected objects. The vision system is the "eyes" of the autonomous operation, enabling the robot to locate and identify trash items to pick up.

## Module Architecture Overview

```
Physical Hardware (camera sensor)
    ↓
Camera driver (USB/CSI interface)
    ↓  
camera.py (Image capture and preprocessing)
    ↓
detector.py (ML model inference - detect trash)
    ↓
tracking.py (Track objects across frames)
    ↓
Robot behavior (Move toward detected trash)
```

## Files and Detailed Descriptions

### **camera.py** - Camera hardware interface
Handles image capture from various camera types:
- Frames from USB cameras (webcams, industrial cameras)
- Frames from CSI cameras (Raspberry Pi ribbon camera)
- Network camera streams (RTSP, HTTP)
- File sequences (for testing/replay)

**Supported camera types:**

**USB Cameras (most common):**
- Standard USB webcams (Logitech, etc.)
- USB3 industrial cameras
- Thermal cameras
- Multi-camera support (by device ID)

**CSI Camera (Raspberry Pi):**
- Official Pi camera (v1, v2, HQ)
- High performance option
- Connected via ribbon cable on CSI port
- Usually faster than USB on Pi

**Network Cameras:**
- RTSP streams (IP cameras, video servers)
- HTTP/MJPEG streams
- Useful for remote monitoring
- Higher latency than local cameras

**Usage example:**
```python
from vision.camera import Camera

# Open first USB camera (camera_id defaults to 0)
camera = Camera(camera_id=0)

# Read frames in loop
while True:
    frame = camera.read()
    if frame is None:
        print("Error reading frame")
        break
    
    # Frame is numpy array (height, width, 3 channels)
    # Format: BGR (OpenCV convention, not RGB)
    print(f"Frame shape: {frame.shape}")  # e.g., (480, 640, 3)
    
    # Process frame...
    
camera.release()  # Clean up when done
```

**Location:** `vision/camera.py` - `Camera` class definition

**Configuration:**
```yaml
camera:
  camera_type: "usb"  # or "csi", "network"
  camera_id: 0  # For USB cameras
  
  # Resolution (lower = faster but less detail)
  width: 640
  height: 480
  
  # Frame rate (higher = more compute)
  fps: 30
  
  # Codec optimization
  fourcc: "MJPG"  # Motion JPEG compression
  
  # Auto-focus/exposure
  auto_focus: true
  auto_exposure: true
  exposure_value: -5  # Manual exposure if auto disabled
```

**Important parameters:**
- **Resolution (640×480 typical):**
  - Higher res → Better detail, slower processing
  - Lower res → Faster, less detail
  - Sweet spot: 640×480 or 320×240

- **Frame rate (30 FPS typical):**
  - 30 FPS = ~33ms per frame
  - 60 FPS = ~17ms per frame (faster, more CPU)
  - Detection might process every Nth frame

- **Codec (MJPG typical):**
  - Raw video: No compression, large bandwidth
  - MJPG: Compressed per-frame, good for USB
  - H.264: Better compression, requires decode

### **detector.py** - Trash object detection
Machine learning model for identifying trash items:
- Real-time object detection
- Multi-class classification (plastic, metal, paper, glass, etc.)
- Bounding box generation
- Confidence/probability scores

**Machine Learning model (typically YOLO family):**

YOLO = "You Only Look Once"
- Single-pass detection (fast, 20-100ms per frame)
- Input: Full image
- Output: Bounding boxes + class + confidence

```python
from vision.detector import TrashDetector

# Load pretrained model
detector = TrashDetector(model_path='models/trash_detector.pt')

# Detect objects in frame
detections = detector.detect(frame)

# Each detection is dict with:
# - 'class': class name (e.g., "plastic_bag")
# - 'confidence': confidence score 0-1 (>0.5 usually valid)
# - 'bbox': bounding box [x, y, width, height] in pixels
# - 'center': [center_x, center_y] for targeting
# - 'area': pixel area of bbox

for detection in detections:
    if detection['confidence'] > 0.5:  # Only high-confidence detections
        print(f"Found {detection['class']} at {detection['center']}")
        print(f"Confidence: {detection['confidence']*100:.1f}%")
```

**Location:** `vision/detector.py` - `TrashDetector` class

**Detection tuning parameters in `vision_config.yaml`:**
```yaml
detector:
  model_path: "models/trash_detector.pt"
  
  # How confident must detection be?
  confidence_threshold: 0.5  # 0-1, higher = stricter
  
  # Overlap threshold for combining boxes (NMS)
  nms_threshold: 0.4  # 0-1, lower = more aggressive merging
  
  # Input resolution for model
  # (model may have been trained on specific size)
  input_resolution: [640, 480]
  
  # Classes the model can detect
  classes: ["plastic", "metal", "paper", "glass", "organic"]
```

**Typical performance:**
- Modern GPU: 30-100 FPS (YOLOv8 medium)
- Modern CPU: 5-20 FPS (YOLOv8 small)
- RPi: 1-5 FPS (YOLOv8 nano, with acceleration)

**Model size options:**
- Nano: Fastest, least accurate
- Small/Micro: Good balance
- Medium: Slower, better accuracy
- Large: Slowest, best accuracy
- Choose based on speed requirements vs. accuracy needs

### **tracking.py** - Multi-object tracking
Associates detections across frames to track objects over time:

**Why tracking is important:**
- Single frame: Detects objects with noise/false positives
- Across frames: Persistent object identity (is this the same can?)
- Velocity estimation: How fast is object moving
- Prediction: Where will it appear in next frame

**Tracking algorithm:**
1. Get detections from detector (boxes + classes)
2. Predict where tracked objects appear in this frame
3. Match new detections to existing tracks (assignment problem)
4. Update existing tracks with new measurements
5. Create new tracks for unmatched detections
6. Remove old tracks that disappeared

```python
from vision.tracking import TargetTracker

tracker = TargetTracker()

# Main loop
while True:
    frame = camera.read()
    detections = detector.detect(frame)
    
    # Update tracker with new detections
    tracks = tracker.update(detections, timestamp=time.time())
    
    # Each track represents persistent object
    for track in tracks:
        track_id = track['id']        # 0, 1, 2, etc.
        position = track['position']  # (x, y, z) in robot frame (m)
        velocity = track['velocity']  # (vx, vy, vz) m/s
        age = track['age']            # Frames since creation
        confidence = track['confidence']  # Tracking confidence
        
        if age > 5 and confidence > 0.7:  # Only mature tracks
            print(f"Track {track_id} at {position}, moving {velocity}")
```

**Location:** `vision/tracking.py` - `TargetTracker` class

**Tracking configuration:**
```yaml
tracking:
  # How far can object move between frames?
  max_distance: 0.5  # meters
  
  # Kalman filter tuning
  process_noise: 0.01
  measurement_noise: 0.1
  
  # Track lifecycle
  min_hits: 3  # Detections needed before accepting track
  max_age: 30  # Frames before removing track if not seen
  
  # Matching algorithm
  use_kalman: true  # Kalman prediction vs simple centroid
  association_method: "hungarian"  # Hungarian algorithm
```

## How Everything Works Together

### Full Detection Pipeline Example

```python
# Step 1: Capture image
frame = camera.read()  # BGR image, shape (480, 640, 3)

# Step 2: Detect trash
detections = detector.detect(frame)
# Returns: [
#   {'class': 'plastic', 'confidence': 0.92, 
#    'center': [320, 240], 'bbox': [250, 180, 140, 120]},
#   {'class': 'metal', 'confidence': 0.78,
#    'center': [450, 180], 'bbox': [400, 140, 100, 80]},
# ]

# Step 3: Track objects
tracks = tracker.update(detections)
# Returns: [
#   {'id': 0, 'class': 'plastic', 'position': [0.5, -0.1, 0.8],
#    'velocity': [0.01, -0.02, 0.0], 'age': 15, 'confidence': 0.88},
#   {'id': 1, 'class': 'metal', 'position': [0.7, 0.0, 0.6],
#    'velocity': [0.0, 0.0, 0.0], 'age': 8, 'confidence': 0.75},
# ]

# Step 4: Select target (e.g., closest plastic item)
plastic_tracks = [t for t in tracks if t['class'] == 'plastic' and t['age'] > 3]
if plastic_tracks:
    target = min(plastic_tracks, key=lambda t: t['position'][2])  # Closest
    print(f"Target at {target['position']}")
    
    # Step 5: Command robot movement
    robot.aim_gripper_at(target['position'])
    robot.move_forward_until(distance=0.2)
```

## Coordinate Systems and Transformations

**Image space (pixel coordinates):**
- Origin at top-left (0, 0)
- X increases rightward, Y increases downward
- Units: pixels
- Example: center at (320, 240) means 320 pixels right, 240 pixels down

**Camera space (3D coordinates):**
- Origin at camera center
- Z-axis forward (away from camera)
- X-axis right, Y-axis down
- Units: meters (requires calibration)

**Robot body space:**
- Origin at robot center
- X-axis forward, Y-axis left, Z-axis up
- Transform camera space to body space using camera mounting calibration

**Transformation pipeline:**
```
Pixel coordinates (image_x, image_y)
    ↓ [Camera calibration]
Camera coordinates (cam_x, cam_y, cam_z)
    ↓ [Apply distortion correction]
Undistorted camera coords
    ↓ [Camera-to-robot transform]
Robot body coordinates (body_x, body_y, body_z)
    ↓ [Use in navigation/gripper control]
```

## Important Configuration Files

**Camera settings:** `config/hardware_config.yaml`
```yaml
vision:
  camera:
    type: "usb"
    device_id: 0
    width: 640
    height: 480
    fps: 30
```

**Detection model and thresholds:** `vision/vision_config.yaml`
```yaml
detector:
  model_path: "models/trash_detector.pt"
  confidence_threshold: 0.5
  nms_threshold: 0.4
```

**Camera calibration:** `data/calibration/camera_params.json`
```json
{
  "intrinsic_matrix": [[fx, 0, cx], [0, fy, cy], [0, 0, 1]],
  "distortion_coefficients": [k1, k2, p1, p2, k3],
  "image_width": 640,
  "image_height": 480,
  "camera_to_robot_transform": {...}
}
```

**Logs:** `logs/trashformer_*.log` - Search for "vision" or "detect"

## Common Issues and Debugging

### Issue: Camera won't initialize

**Steps to diagnose:**

1. **Check camera connection physical**
   ```bash
   # Linux: List USB devices
   lsusb | grep -i camera
   # or
   v4l2-ctl --list-devices
   ```

2. **Check permissions**
   - May need `sudo` on Linux
   - Check /dev/video* permissions:
     ```bash
     ls -la /dev/video*
     # May need: sudo chmod 666 /dev/video0
     ```

3. **Test camera directly with OpenCV**
   ```python
   import cv2
   cap = cv2.VideoCapture(0)
   ret, frame = cap.read()
   if ret:
       print(f"Camera working! Frame shape: {frame.shape}")
   else:
       print("Camera failed to capture")
   cap.release()
   ```

4. **Try different camera ID**
   ```python
   for i in range(5):
       cap = cv2.VideoCapture(i)
       if cap.isOpened():
           print(f"Camera {i} available")
       cap.release()
   ```

### Issue: Camera captures frames but image is black/blank

**Root causes:**

1. **Camera not powered correctly**
   - For USB cameras, usually power comes from USB
   - For CSI cameras, check Pi configuration
   - Try different USB port (may have power issues)

2. **Lens cap on!**
   - Check physical lens
   - Dust or dirt on lens

3. **Auto-exposure/auto-focus not converging**
   ```python
   # Fix: Manually set exposure
   camera.set_property('exposure', -5)  # Manual exposure
   camera.set_property('auto_focus', False)
   camera.set_property('focus', 50)  # Manual focus
   ```

4. **Camera pointed wrong direction**
   - Verify camera isn't pointed at ceiling/wall

### Issue: Detector not finding trash (zero detections)

**Debug systematically:**

1. **Verify model is loaded correctly**
   ```python
   from vision.detector import TrashDetector
   detector = TrashDetector(model_path='models/trash_detector.pt')
   print(f"Model loaded: {detector.model}")
   print(f"Model classes: {detector.class_names}")
   ```

2. **Check confidence threshold not too high**
   ```yaml
   # In vision_config.yaml
   confidence_threshold: 0.3  # Lower threshold to see detections
   ```

3. **Verify image format**
   - Detector expects BGR (OpenCV standard)
   - If RGB: `frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)`
   - Check shape is correct (height, width, 3)

4. **Test on known image**
   ```python
   # Create simple test: Draw red rectangle (should be detected as object)
   test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
   cv2.rectangle(test_frame, (200, 150), (400, 350), (0, 0, 255), -1)
   
   detections = detector.detect(test_frame)
   if not detections:
       print("Model not detecting anything - check model file")
   ```

5. **Check model file integrity**
   ```bash
   # Verify file exists and is reasonable size
   ls -lh models/trash_detector.pt
   # Should be >50MB typically for YOLOv8
   ```

### Issue: Too many false detections (detecting things that aren't trash)

**Solutions:**

1. **Increase confidence threshold**
   ```yaml
   confidence_threshold: 0.7  # or higher (0-1)
   ```

2. **Check model training**
   - Some false positives are normal
   - May need to retrain model with more data
   - Or use different model version

3. **Filter by class**
   ```python
   # Only accept certain classes
   detections = [d for d in detections 
                 if d['class'] in ['plastic', 'metal']]
   ```

4. **Spatial filtering**
   ```python
   # Ignore detections outside region of interest
   detections = [d for d in detections
                 if 100 < d['center'][0] < 540 and  # X range
                    100 < d['center'][1] < 380]     # Y range
   ```

### Issue: Object detection is very slow (<5 FPS)

**Performance debugging:**

1. **Check model size**
   - YOLOv8 small: ~10FPS on modern CPU
   - YOLOv8 nano: ~30FPS on modern CPU
   - Consider using smaller model: `-n` suffix

2. **Check input resolution**
   ```yaml
   # In vision_config.yaml
   input_resolution: [320, 240]  # Smaller = faster
   ```

3. **Skip frames**
   ```python
   # Process every Nth frame, display previous results
   frame_skip = 3
   frame_count = 0
   
   while True:
       frame = camera.read()
       if frame_count % frame_skip == 0:
           detections = detector.detect(frame)
       frame_count += 1
   ```

4. **Check GPU usage**
   ```bash
   # On system with GPU
   nvidia-smi  # Watch GPU utilization
   ```
   - Should show model using GPU if available
   - If CPU-only: May be slow on Raspberry Pi

### Issue: Tracking losing objects (IDs changing frequently)

**Root causes:**

1. **Detection isn't stable**
   - Bounding box jittering between frames
   - Detection confidence fluctuating
   - Fix: Increase confidence threshold (fewer detections but stable)

2. **Objects moving too fast**
   ```yaml
   # In vision_config.yaml
   tracking:
     max_distance: 1.0  # Increase allowed movement
   ```

3. **Detection inconsistent**
   - Sometimes detects object, sometimes doesn't
   - Solution: Requires better detector training

4. **Frame to frame motion is large**
   - High speed movement or low frame rate
   - Solution: Increase camera FPS or smooth motion

### Issue: Camera calibration data missing

**Impact:** Robot can't correctly position gripper at detected objects

**Fix:**
```bash
python tools/camera_preview.py --calibrate
```
This will interactively calibrate camera and generate:
- `data/calibration/camera_params.json` - Intrinsic parameters
- Camera-to-robot transform - Mounting offset

**Manual calibration alternative:**
1. Place known-size object at known distance
2. Measure pixel size in image
3. Compute focal length: fx = (pixel_size × distance) / real_size
4. Repeat for multiple distances to verify
5. Calculate principal point (image center)

## Where to Find Everything

**Camera code:** `vision/camera.py` - `Camera` class
**Detector code:** `vision/detector.py` - `TrashDetector` class
**Tracker code:** `vision/tracking.py` - `TargetTracker` class

**Configuration files:**
- `vision/vision_config.yaml` - Model paths, thresholds
- `config/hardware_config.yaml` - Camera device, resolution
- `data/calibration/camera_params.json` - Camera calibration

**Model files:**
- `models/trash_detector.pt` - ML model for detection
- Download from model repository if missing

**Log files:**
- `logs/trashformer_*.log` - Search for "vision" or "detect"
- Real-time logging available in debug mode

**Test tools:**
- `python tools/camera_preview.py` - Live camera feed viewer
- `python tools/test_vision.py` - Vision system test suite

## Performance Optimization

**Frame processing pipeline (typical 30 FPS):**
```
Capture frame:      3ms
Detect objects:    15ms (bottleneck!)
Track objects:      2ms
Output results:     1ms
Total:             21ms (48 FPS max)
```

**Optimization strategies:**

1. **Reduce detection frequency**
   - Detect every frame: High overhead
   - Detect every 3 frames: See detections every 100ms
   - Trade off responsiveness vs. CPU usage

2. **Reduce image resolution**
   - 1280×960 → 640×480: 4× faster
   - But less detail for small objects

3. **Model quantization**
   - Float32 model: Most accurate
   - Int8 quantized: 2-4× faster, slightly less accurate
   - Deploy quantized version on resource-limited systems

4. **GPU acceleration**
   - Jetson Nano: ~50% speedup with CUDA
   - Desktop GPU: 10-100× speedup possible
   - Check PyTorch CUDA support

## Advanced Debugging

### Visualize detections
```python
# Draw bounding boxes on frame for debugging
import cv2

frame = camera.read()
detections = detector.detect(frame)

for det in detections:
    x, y, w, h = det['bbox']
    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
    cv2.putText(frame, f"{det['class']} {det['confidence']:.2f}",
                (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0))

cv2.imshow("Detections", frame)
cv2.waitKey(1)
```

### Profile detection time
```python
import time

for i in range(10):
    frame = camera.read()
    
    start = time.time()
    detections = detector.detect(frame)
    elapsed = time.time() - start
    
    print(f"Detection {i}: {elapsed*1000:.1f}ms")
```

### Log all detections
```python
# Save detections to file for analysis
import json

detections_log = []
for i in range(100):
    frame = camera.read()
    dets = detector.detect(frame)
    detections_log.append({
        'frame': i,
        'detections': dets,
        'timestamp': time.time()
    })

with open('detections.json', 'w') as f:
    json.dump(detections_log, f)
```
