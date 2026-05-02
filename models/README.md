# Models Directory

This directory contains all machine learning models, 3D CAD models, simulation files, and other data models used by the Trashformer robotic system. These models enable vision-based trash detection, physical simulation, and system design.

## Directory Structure

```
models/
├── vision/              # Machine learning models for computer vision
│   ├── trash_detector.pt     # Main trash detection model
│   ├── object_classifier.pt  # Object classification model
│   └── segmentation.onnx     # Instance segmentation model
├── simulation/          # Simulation and physics models
│   ├── robot.urdf            # Unified Robot Description Format
│   ├── world.sdf             # Simulation Description Format worlds
│   └── meshes/               # 3D mesh files for simulation
├── cad/                 # Computer-aided design files
│   ├── chassis/             # Robot frame and body
│   ├── arm/                 # Robotic arm assembly
│   └── electronics/         # Custom electronics enclosures
└── config/              # Model configuration files
    ├── model_metadata.json  # Model information and versions
    └── preprocessing.yaml   # Data preprocessing parameters
```

## Machine Learning Models (vision/)

### **trash_detector.pt** - Primary Trash Detection Model
PyTorch model for real-time trash object detection and localization.

**Model specifications:**
- **Architecture**: YOLOv8/YOLOv5 or similar one-stage detector
- **Input**: RGB images (typically 640×480 or 416×416)
- **Output**: Bounding boxes, class probabilities, confidence scores
- **Classes**: plastic_bag, metal_can, paper, glass_bottle, cardboard, organic_waste
- **Performance**: 20-50 FPS on embedded hardware

**Usage in code:**
```python
from vision.detector import TrashDetector

# Load model
detector = TrashDetector(model_path='models/vision/trash_detector.pt')

# Detect objects
detections = detector.detect(frame)

# Process results
for det in detections:
    if det['confidence'] > 0.5:
        bbox = det['bbox']  # [x, y, width, height]
        class_name = det['class']
        print(f"Found {class_name} at {bbox}")
```

**Model requirements:**
- **Input format**: BGR uint8 numpy array (OpenCV convention)
- **Normalization**: None (expects 0-255 range)
- **Output format**: List of detection dictionaries
- **Dependencies**: PyTorch, OpenCV, numpy

**Location:** `models/vision/trash_detector.pt`

**Training data:** Typically trained on:
- COCO dataset (general objects)
- Custom trash dataset (bottles, cans, bags)
- Domain-specific images (indoor/outdoor trash)

### **object_classifier.pt** - Object Classification Model
Secondary classifier for detailed object categorization and material identification.

**Use cases:**
- Distinguish between different types of plastic
- Identify recyclable vs. non-recyclable materials
- Determine object properties (rigid, flexible, heavy, light)

**Architecture options:**
- **ResNet**: Residual network for image classification
- **EfficientNet**: Efficient scaled architecture
- **Vision Transformer**: Modern attention-based model

**Input/Output:**
- **Input**: Cropped object images (224×224 RGB)
- **Output**: Class probabilities for material types
- **Classes**: PET_plastic, HDPE_plastic, aluminum, steel, glass, paper, cardboard, organic

### **segmentation.onnx** - Instance Segmentation Model
ONNX format model for pixel-level object segmentation and precise boundary detection.

**Benefits:**
- **Precise boundaries**: Better than bounding boxes for irregular shapes
- **Occlusion handling**: Segments partially hidden objects
- **Pose estimation**: Enables better grasping pose calculation

**Architectures:**
- **Mask R-CNN**: Two-stage detection + segmentation
- **YOLACT**: Real-time instance segmentation
- **DeepLab**: Semantic segmentation with instance separation

## Simulation Models (simulation/)

### **robot.urdf** - Robot Description Format
Unified Robot Description Format file defining the robot's physical structure for simulation and kinematics.

**URDF contents:**
```xml
<robot name="trashformer">
  <!-- Links (rigid bodies) -->
  <link name="base_link">
    <visual><geometry><box size="0.4 0.3 0.1"/></geometry></visual>
    <collision><geometry><box size="0.4 0.3 0.1"/></geometry></collision>
  </link>
  
  <!-- Joints (connections between links) -->
  <joint name="base_to_arm" type="revolute">
    <parent link="base_link"/>
    <child link="arm_base"/>
    <origin xyz="0 0 0.05"/>
    <axis xyz="0 0 1"/>
    <limit lower="-3.14" upper="3.14" effort="100" velocity="1.0"/>
  </joint>
  
  <!-- Complete kinematic chain -->
  <!-- base -> arm_base -> shoulder -> elbow -> wrist -> gripper -->
</robot>
```

**Usage:**
```python
import pybullet as p
import pybullet_data

# Load robot
p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
robot_id = p.loadURDF("models/simulation/robot.urdf")

# Get joint information
num_joints = p.getNumJoints(robot_id)
print(f"Robot has {num_joints} joints")

# Control robot
joint_indices = [0, 1, 2, 3, 4]  # arm joints
target_positions = [0, 0.5, 1.0, 0, 0]
p.setJointMotorControlArray(robot_id, joint_indices, 
                           controlMode=p.POSITION_CONTROL,
                           targetPositions=target_positions)
```

**Location:** `models/simulation/robot.urdf`

**Validation:**
```bash
# Check URDF syntax
check_urdf models/simulation/robot.urdf

# Visualize in RViz
roslaunch urdf_tutorial display.launch model:=models/simulation/robot.urdf
```

### **world.sdf** - Simulation World Files
Simulation Description Format files defining environments for testing.

**World contents:**
- **Ground plane**: Floor surface
- **Obstacles**: Walls, furniture, objects
- **Lighting**: Light sources and shadows
- **Physics properties**: Friction, restitution

**Example world file:**
```xml
<sdf version="1.6">
  <world name="kitchen">
    <physics>
      <gravity>0 0 -9.8</gravity>
    </physics>
    
    <model name="ground_plane">
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry><plane><normal>0 0 1</normal></plane></geometry>
        </collision>
      </link>
    </model>
    
    <model name="table">
      <pose>2 0 0 0 0 0</pose>
      <link name="link">
        <collision name="collision">
          <geometry><box><size>1 1 0.1</size></geometry></collision>
      </link>
    </model>
  </world>
</sdf>
```

### **meshes/** - 3D Mesh Files
STL, OBJ, or COLLADA files for complex geometries in simulation.

**Mesh requirements:**
- **Manifold**: No holes or self-intersections
- **Reasonable polygon count**: <10k triangles for real-time sim
- **Proper scaling**: Units in meters
- **Origin**: At logical center of object

## CAD Models (cad/)

### **chassis/** - Robot Frame and Body
Mechanical design files for the robot's structural components.

**Files:**
- `base_plate.step`: Main mounting plate
- `battery_box.step`: Battery enclosure
- `electronics_mount.step`: Computer and controller mounting
- `wheel_mounts.step`: Drive wheel attachments

### **arm/** - Robotic Arm Assembly
Complete arm design including all links and joints.

**Components:**
- `base_link.step`: Arm mounting base
- `upper_arm.step`: Main arm segment
- `forearm.step`: Second arm segment
- `wrist.step`: End effector mounting
- `gripper.step`: Trash grasping mechanism

### **electronics/** - Custom Enclosures
Protective housings for electronics and sensors.

**Enclosures:**
- `raspberry_pi_case.step`: Main computer housing
- `servo_controller_box.step`: PWM controller enclosure
- `sensor_mount.step`: IMU and camera mounts

## Model Configuration (config/)

### **model_metadata.json** - Model Information
Metadata about all models including versions, training data, and performance metrics.

```json
{
  "trash_detector": {
    "version": "1.2.0",
    "architecture": "YOLOv8m",
    "training_date": "2024-01-15",
    "dataset": "TrashDataset-v3",
    "metrics": {
      "mAP50": 0.85,
      "mAP50-95": 0.62,
      "inference_time": "25ms"
    },
    "classes": ["plastic", "metal", "paper", "glass", "organic"],
    "input_size": [640, 640]
  },
  "robot_urdf": {
    "version": "2.1.0",
    "last_modified": "2024-01-10",
    "author": "Design Team",
    "validation_status": "passed"
  }
}
```

### **preprocessing.yaml** - Data Preprocessing Parameters
Configuration for data preprocessing pipelines used in model training and inference.

```yaml
preprocessing:
  image:
    resize: [640, 640]
    normalize:
      mean: [0.485, 0.456, 0.406]
      std: [0.229, 0.224, 0.225]
    augmentations:
      - random_crop: 0.8
      - random_flip: 0.5
      - color_jitter: 0.2
  
  pointcloud:
    voxel_size: 0.02
    remove_outliers: true
    radius: 0.1
```

## Working with Models

### **Loading Models in Code**
```python
import torch
from pathlib import Path

class ModelManager:
    def __init__(self, model_dir="models"):
        self.model_dir = Path(model_dir)
        
    def load_trash_detector(self):
        model_path = self.model_dir / "vision" / "trash_detector.pt"
        model = torch.load(model_path)
        model.eval()
        return model
        
    def load_urdf(self):
        urdf_path = self.model_dir / "simulation" / "robot.urdf"
        with open(urdf_path, 'r') as f:
            urdf_xml = f.read()
        return urdf_xml
```

### **Model Validation**
```python
# Validate ML model
def validate_ml_model(model_path):
    try:
        model = torch.load(model_path)
        # Test forward pass with dummy input
        dummy_input = torch.randn(1, 3, 640, 640)
        output = model(dummy_input)
        print(f"Model output shape: {output.shape}")
        return True
    except Exception as e:
        print(f"Model validation failed: {e}")
        return False

# Validate URDF
def validate_urdf(urdf_path):
    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse(urdf_path)
        root = tree.getroot()
        num_links = len(root.findall(".//link"))
        num_joints = len(root.findall(".//joint"))
        print(f"URDF valid: {num_links} links, {num_joints} joints")
        return True
    except Exception as e:
        print(f"URDF validation failed: {e}")
        return False
```

## Common Model Issues and Debugging

### Issue: Model file not found

**Symptoms:**
```
FileNotFoundError: models/vision/trash_detector.pt not found
```

**Debug:**
```bash
# Check file exists
ls -la models/vision/trash_detector.pt

# Check permissions
stat models/vision/trash_detector.pt

# Check path from working directory
pwd
find . -name "trash_detector.pt"
```

**Fix:**
- Download missing model from repository
- Check model directory structure
- Update model path in configuration

### Issue: Model loading fails

**Symptoms:**
```
RuntimeError: version mismatch
KeyError: 'state_dict'
```

**Debug:**
```python
# Check PyTorch version
import torch
print(f"PyTorch version: {torch.__version__}")

# Inspect model file
model_dict = torch.load('models/vision/trash_detector.pt', map_location='cpu')
print("Model keys:", list(model_dict.keys()))

# Try loading with different options
model = torch.load(path, map_location='cpu', weights_only=False)
```

**Fix:**
- Retrain model with current PyTorch version
- Use compatible model format
- Update model loading code

### Issue: Poor detection performance

**Symptoms:**
- Low accuracy, false positives, missed detections

**Debug:**
```python
# Test on known images
from vision.detector import TrashDetector
detector = TrashDetector()

# Load test image
test_image = cv2.imread('test_trash.jpg')
detections = detector.detect(test_image)

print(f"Number of detections: {len(detections)}")
for det in detections:
    print(f"Class: {det['class']}, Confidence: {det['confidence']:.3f}")
```

**Fix:**
- Retrain model with more/better data
- Adjust confidence threshold
- Check input image preprocessing
- Validate model architecture

### Issue: Simulation model errors

**Symptoms:**
```
URDF parsing error
Joint limit exceeded
Collision detection issues
```

**Debug:**
```bash
# Validate URDF
check_urdf models/simulation/robot.urdf

# Check joint limits
python -c "
import pybullet as p
p.connect(p.DIRECT)
robot = p.loadURDF('models/simulation/robot.urdf')
for i in range(p.getNumJoints(robot)):
    info = p.getJointInfo(robot, i)
    print(f'Joint {i}: {info[1].decode()}, limits: {info[8:10]}')
"
```

**Fix:**
- Correct URDF syntax errors
- Adjust joint limits to match hardware
- Fix mesh file paths
- Validate collision geometries

### Issue: CAD model import fails

**Symptoms:**
- Cannot open STEP/STL files
- Missing components in assembly

**Debug:**
```bash
# Check file format
file models/cad/arm/upper_arm.step

# Try different software
# FreeCAD: File -> Open
# Fusion 360: Insert -> Import
```

**Fix:**
- Export in different format
- Repair model geometry
- Check for corrupted files
- Update CAD software

## Model Development Workflow

### **Training New Models**
```bash
# 1. Prepare dataset
python tools/prepare_dataset.py --images data/images/ --labels data/labels/

# 2. Train model
python tools/train_detector.py --config config/train.yaml

# 3. Evaluate performance
python tools/evaluate_model.py --model models/vision/trash_detector.pt

# 4. Export for deployment
python tools/export_model.py --input pytorch --output onnx
```

### **Updating Simulation Models**
```bash
# 1. Modify URDF
# Edit models/simulation/robot.urdf

# 2. Validate
check_urdf models/simulation/robot.urdf

# 3. Test in simulation
python tools/test_simulation.py --urdf models/simulation/robot.urdf
```

### **Version Control for Models**
```bash
# Large model files - use Git LFS
git lfs track "*.pt"
git lfs track "*.onnx"
git lfs track "*.stl"

# Model metadata
git add models/config/model_metadata.json

# Commit with descriptive message
git commit -m "Update trash detector v1.3.0: improved plastic detection"
```

## Performance Optimization

### **Model Size Optimization**
- **Quantization**: Reduce precision (float32 → int8)
- **Pruning**: Remove unnecessary weights
- **Knowledge distillation**: Train smaller model from larger teacher

### **Inference Speed Optimization**
- **TensorRT**: NVIDIA GPU optimization
- **OpenVINO**: Intel hardware optimization
- **ONNX Runtime**: Cross-platform acceleration
- **Model parallelism**: Split across multiple devices

### **Memory Optimization**
- **Model sharding**: Split large models across devices
- **Dynamic batching**: Process multiple inputs together
- **Memory pooling**: Reuse allocated memory

## Where to Find Everything

**Vision models:** `models/vision/`
- `trash_detector.pt`: Main detection model
- `object_classifier.pt`: Material classification
- `segmentation.onnx`: Pixel-level segmentation

**Simulation models:** `models/simulation/`
- `robot.urdf`: Robot description for physics sim
- `world.sdf`: Environment definitions
- `meshes/`: 3D geometry files

**CAD models:** `models/cad/`
- `chassis/`: Robot frame components
- `arm/`: Robotic arm parts
- `electronics/`: Custom enclosures

**Configuration:** `models/config/`
- `model_metadata.json`: Model information
- `preprocessing.yaml`: Data processing parameters

**Training tools:** `tools/train_*.py`
- Dataset preparation, model training, evaluation

**Model repositories:** 
- Company internal: `https://models.company.com/trashformer/`
- Public models: Download from model zoos (YOLO, PyTorch Hub)
├── gripper/
└── electronics/
```

## Versioning

When updating CAD files:
1. Document changes in design notes
2. Update assembly drawings
3. Verify all part tolerances
4. Test fit critical interfaces
5. Update model version number

## References

See hardware.md for CAD specifications and dimensions.
