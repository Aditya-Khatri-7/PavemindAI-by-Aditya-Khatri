import os
import sys
import cv2
import time
from pathlib import Path
from datetime import datetime
from ultralytics import YOLO

# Add parent path to sys path to import pothole_analyzer
sys.path.append(str(Path(__file__).parent.parent / 'Pothole-detection'))

from pothole_analyzer import SeverityEngine, AlertSystem, Visualizer

def main():
    MODEL_PATH = "../Pothole-detection/runs/detect/yolov12n_pothole_detector5/weights/best.pt"
    img_path = "static/uploads/img_1783839683_input_image.png"
    
    print(f"CWD: {os.getcwd()}")
    print(f"Model: {MODEL_PATH} (exists: {Path(MODEL_PATH).exists()})")
    print(f"Image: {img_path} (exists: {Path(img_path).exists()})")
    
    model = YOLO(MODEL_PATH)
    img = cv2.imread(img_path)
    if img is None:
        print("Failed to read image")
        return
        
    img_h, img_w = img.shape[:2]
    
    results = model(img, conf=0.45, verbose=False)[0]
    print(f"Detected {len(results.boxes)} raw boxes")
    
    severity_engine = SeverityEngine()
    detections = []
    
    for box in results.boxes:
        det = severity_engine.analyze_pothole(box, img_w, img_h)
        if det is None:
            continue
        detections.append(det)
        
    print(f"Passed SeverityEngine filters: {len(detections)}")
    for d in detections:
        print(f"  Det: severity={d['severity']}, width={d['width_cm']}, height={d['height_cm']}, bbox={d['bbox']}")

if __name__ == "__main__":
    main()
