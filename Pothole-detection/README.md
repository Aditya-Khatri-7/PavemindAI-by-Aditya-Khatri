# Road Pothole Detection and Severity Analysis System

**IBM Internship | Group 74 AIML (AIML74) | UPES Dehradun**

An intelligent, real-time computer vision system for automated pothole detection, road severity assessment, and analytical reporting using attention-centric deep learning (YOLOv12n/YOLOv11n).

---

## Key Features

1. **YOLOv12 Nano Base Model**: Attention-centric spatial reasoning with reversed ELAN feature reuse optimized for real-time edge hardware.
2. **Modular Severity Detection Engine**: Evaluates bounding boxes using multi-factor weights (percentage of frame + detection confidence) and aspect ratio filters.
3. **Geometric Physical Dimensioning**: Employs flat-surface perspective projections to estimate distance (meters) and physical size (width $\times$ height in cm) without requiring 3D depth sensors.
4. **Intelligent Alert System**: Translates detection statistics to real-time driver overlays (Good, Warning, Danger alert banners with flashing warning indicators).
5. **Real-time Analytics Pipeline**: Generates JSON, CSV, and human-readable text statistics (average sizes, total counts, worst anomalies) inside `outputs/analysis/` for maintenance logging.

---

## 🛠️ Environment Setup & Installation

The project runs on **Python 3.10+** (Python 3.13 verified) on Windows machines.

### 1. Create a Virtual Environment

Open PowerShell in the workspace folder and run:
```bash
# Using standard Python
python -m venv .venv

# Activate the virtual environment
.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

Install using the custom index URL for lightweight PyTorch CPU binaries (or CUDA versions if an NVIDIA GPU is available):
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install PyTorch CPU
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install remaining libraries
pip install -r requirements.txt
```

---

## 📂 Dataset Preparation

The model trains on YOLO annotated format datasets:
```
class_id x_center y_center width height (all normalized 0.0 - 1.0)
```
Class index is `0` (pothole).

### Integrating RDD2022 dataset:
1. Download the Kaggle YOLO mirror of CRDDC 2022.
2. Extract the labels text files.
3. Run the remapping script to filter out only potholes (class 3 in RDD2022) and map them to class 0:
```bash
python filter_rdd2022_potholes.py --input_dir data/rdd2022_raw/labels --output_dir data/labels
```

---

## 🚀 Model Training

Use `train_yolov12.py` to train the YOLOv12 nano detector:
```bash
python train_yolov12.py
```
This script loads the pre-trained attention weights `yolov12n.pt`, fine-tunes on the dataset referenced in `pothole_dataset.yaml`, exports the model to ONNX format, and saves weights under `runs/detect/`.

---

## 🔍 Inference Pipelines

We provide two primary inference drivers:

### 1. Intelligent Severity Detection CLI (`run_detector_severity.py`)

Main production runner that calculates physical size estimates, displays live overlays, and exports analytical reports.

```bash
# Run on a single image and export analysis reports
python run_detector_severity.py --source input_image.png --save-analysis

# Run on a video file in headless mode (no GUI popping up, perfect for batch scripts)
python run_detector_severity.py --source input_video.mp4 --headless --save-analysis

# Run on live webcam/dashcam stream
python run_detector_severity.py --source 0 --conf 0.40
```

#### Tuning Camera Calibration for Size Estimation:
The script maps pixels to centimeters using assumed camera mounting stats. Override defaults using flags:
- `--height`: Height of the camera above the ground (meters) (Default: `1.3`)
- `--focal`: Camera lens focal length (pixels) (Default: `800.0`)
- `--tilt`: Angle of the camera looking down at the road surface (degrees) (Default: `18.0`)

```bash
python run_detector_severity.py --source input_video.mp4 --height 1.5 --tilt 20.0
```

### 2. Simple Detection CLI (`run_detector.py`)

A standard inference runner that uses the basic Ultralytics visual output boxes.
```bash
python run_detector.py --source input_image.png
python run_detector.py --source input_video.mp4 --headless
```

---

## 📊 Analytics Exports

Report runs are generated automatically inside `outputs/analysis/`:
- **`.json`**: Structured nested data for web app database ingestion.
- **`.csv`**: Tabular format for spreadsheet analysis.
- **`.txt`**: Human-readable status reports.

---

## 🔧 Troubleshooting

- **cv2.imshow errors / blocks**: If running via automation, use the `--headless` flag to bypass native desktop window outputs.
- **Memory leaks / Multiprocessing errors on Windows**: Handled inside scripts by setting `workers=0` and protecting entrypoints inside `if __name__ == '__main__':` wrappers.
