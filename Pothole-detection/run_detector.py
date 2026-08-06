"""
run_detector.py  —  Simple CLI tool for Road Pothole Detection (without severity alerts)
IBM Internship | Group 74 | AIML74 | UPES Dehradun

Usage:
  python run_detector.py --source input_image.png
  python run_detector.py --source input_video.mp4 --headless
"""

import cv2
import argparse
from pathlib import Path
from ultralytics import YOLO
import torch
import sys

def main():
    parser = argparse.ArgumentParser(description='Simple Pothole Detection CLI')
    parser.add_argument('--source', default='input_image.png', help='Source media file or 0 for webcam')
    parser.add_argument('--model', default='runs/detect/yolov12n_pothole_detector5/weights/best.pt', help='Weights path')
    parser.add_argument('--conf', type=float, default=0.5, help='Confidence threshold')
    parser.add_argument('--headless', action='store_true', help='Disable showing GUI windows')
    args = parser.parse_args()
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Loading model: {args.model}")
    print(f"Using device: {device}")
    
    try:
        model = YOLO(args.model)
        model.to(device)
    except Exception as e:
        print(f"Error loading model weights: {e}")
        sys.exit(1)
        
    src = args.source
    is_img = src.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp'))
    
    if is_img:
        img = cv2.imread(src)
        if img is None:
            print(f"Error: Cannot read image {src}")
            return
            
        results = model.predict(src, save=True, conf=args.conf)
        saved_path = Path(results[0].save_dir) / Path(src).name
        print(f"Detection complete! Annotated image saved to: {saved_path}")
        
    else:
        is_webcam = (src == '0')
        video_src = 0 if is_webcam else src
        cap = cv2.VideoCapture(video_src)
        if not cap.isOpened():
            print(f"Error: Cannot open video source: {src}")
            return
            
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        writer = None
        if not is_webcam:
            Path('outputs').mkdir(exist_ok=True)
            out_path = Path('outputs') / 'pothole_detection_result.mp4'
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(str(out_path), fourcc, fps, (w, h))
            print(f"Saving output video to: {out_path}")
            
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            results = model(frame, conf=args.conf, verbose=False)[0]
            annotated_frame = results.plot()
            
            if writer is not None:
                writer.write(annotated_frame)
                
            if not args.headless:
                cv2.imshow("Pothole Detector (Simple) - Press q to quit", annotated_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        cap.release()
        if writer is not None:
            writer.release()
        cv2.destroyAllWindows()
        print("Video processing finished.")

if __name__ == '__main__':
    main()