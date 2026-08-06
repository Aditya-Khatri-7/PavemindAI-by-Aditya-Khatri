"""
run_detector_severity.py  —  CLI tool for Road Pothole Detection & Severity System
IBM Internship | Group 74 | AIML74 | UPES Dehradun

Usage:
  python run_detector_severity.py --source input_image.png --save-analysis
  python run_detector_severity.py --source input_video.mp4 --headless --save-analysis
  python run_detector_severity.py --source 0
"""

import cv2
import time
import argparse
import sys
from pathlib import Path
from ultralytics import YOLO
import torch

# Import core modular classes
from pothole_analyzer import SeverityEngine, AlertSystem, AnalyticsManager, Visualizer, DEFAULT_CALIBRATION

def run_on_image(source_path, model, severity_engine, analytics_mgr, conf, save_analysis):
    """
    Runs pothole detection and severity estimation on a single image.
    """
    print(f"\nProcessing image: {source_path}")
    img = cv2.imread(source_path)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {source_path}")
        
    img_h, img_w = img.shape[:2]
    
    t0 = time.time()
    results = model(img, conf=conf, verbose=False)[0]
    proc_time_ms = (time.time() - t0) * 1000
    
    # Analyze each detected box
    detections = []
    severity_counts = {}
    
    for box in results.boxes:
        det = severity_engine.analyze_pothole(box, img_w, img_h)
        if det is None:
            continue
        detections.append(det)
        sev = det['severity']
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
    overall_cond = AlertSystem.get_overall_road_condition(severity_counts)
    
    # Render overlay using Visualizer
    annotated_img = Visualizer.render(img.copy(), detections, proc_time_ms, overall_cond)
    
    # Save output
    out_dir = Path('outputs')
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"severity_{Path(source_path).name}"
    cv2.imwrite(str(out_path), annotated_img)
    print(f"Annotated image saved to: {out_path}")
    
    # Generate analytics report
    if save_analysis:
        summary = analytics_mgr.generate_image_summary(detections, proc_time_ms, source_path)
        print("\n" + "="*50)
        print(f"  IMAGE ANALYSIS SUMMARY for {source_path}")
        print("="*50)
        print(f"  Total Potholes: {summary['total_potholes']}")
        print(f"  Minor         : {summary['minor_count']}")
        print(f"  Moderate      : {summary['moderate_count']}")
        print(f"  Severe        : {summary['severe_count']}")
        print(f"  Road Condition: {overall_cond['label']} ({overall_cond['alert']})")
        print(f"  Reports saved in outputs/analysis/")
        print("="*50 + "\n")

def run_on_video(source, model, severity_engine, analytics_mgr, conf, save_analysis, headless):
    """
    Runs real-time pothole detection, warning system, and overlays on video/webcam.
    """
    is_webcam = (source == '0')
    video_src = 0 if is_webcam else source
    
    print(f"\nOpening video stream: {'Webcam' if is_webcam else source}")
    cap = cv2.VideoCapture(video_src)
    if not cap.isOpened():
        raise IOError(f"Cannot open video source: {source}")
        
    fps_in = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w_in = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h_in = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    writer = None
    out_path = None
    if not is_webcam:
        out_dir = Path('outputs')
        out_dir.mkdir(exist_ok=True)
        out_path = out_dir / 'pothole_severity_result.mp4'
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(str(out_path), fourcc, fps_in, (w_in, h_in))
        print(f"Saving output video to: {out_path}")
        
    frame_idx = 0
    t_start = time.time()
    
    print("\nRunning inference pipeline. Press 'q' in GUI to quit (or wait for video to end).")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        t0 = time.time()
        results = model(frame, conf=conf, verbose=False)[0]
        proc_time_ms = (time.time() - t0) * 1000
        
        # Analyze detections
        detections = []
        severity_counts = {}
        for box in results.boxes:
            det = severity_engine.analyze_pothole(box, w_in, h_in)
            if det is None:
                continue
            detections.append(det)
            sev = det['severity']
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
        overall_cond = AlertSystem.get_overall_road_condition(severity_counts)
        
        # Record frame analytics
        analytics_mgr.record_frame(frame_idx, detections, proc_time_ms)
        
        # Draw overlay using Visualizer
        fps_current = 1000.0 / max(proc_time_ms, 1.0)
        annotated_frame = Visualizer.render(frame, detections, proc_time_ms, overall_cond, fps=fps_current)
        
        # Save frame to output video
        if writer is not None:
            writer.write(annotated_frame)
            
        # Display window if not in headless mode
        if not headless:
            cv2.imshow('Pothole Severity System  —  Press q to quit', annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        frame_idx += 1
        if frame_idx % 50 == 0:
            print(f"Processed {frame_idx} frames... (Avg FPS: {frame_idx / (time.time() - t_start):.1f})")
            
    cap.release()
    if writer is not None:
        writer.release()
    cv2.destroyAllWindows()
    
    # Save reports
    if save_analysis:
        summary = analytics_mgr.generate_video_summary(source)
        print("\n" + "="*50)
        print(f"  VIDEO RUN STATS SUMMARY for {source}")
        print("="*50)
        print(f"  Total Frames   : {summary['total_frames']}")
        print(f"  Average FPS    : {summary['average_fps']}")
        print(f"  Total Potholes : {summary['total_detections']}")
        print(f"  Avg Dets/Frame : {summary['average_potholes_per_frame']}")
        print(f"  Max Dets/Frame : {summary['max_potholes_in_one_frame']}")
        print(f"  Minor Count    : {summary['minor_count']}")
        print(f"  Moderate Count : {summary['moderate_count']}")
        print(f"  Severe Count   : {summary['severe_count']}")
        print(f"  Worst Severity : {summary['highest_severity_encountered']}")
        print(f"  Avg Proc Time  : {summary['average_processing_time_ms']} ms")
        print(f"  Report files saved in outputs/analysis/")
        print("="*50 + "\n")

def main():
    parser = argparse.ArgumentParser(
        description='Intelligent Road Pothole Detection & Severity System'
    )
    parser.add_argument(
        '--source', default='input_image.png',
        help='Source media: image file (.png/.jpg), video file (.mp4), or "0" for webcam'
    )
    parser.add_argument(
        '--model', default='runs/detect/yolov12n_pothole_detector5/weights/best.pt',
        help='Path to trained YOLO weights file'
    )
    parser.add_argument(
        '--conf', type=float, default=0.15,
        help='Confidence threshold (0.0–1.0)'
    )
    parser.add_argument(
        '--save-analysis', action='store_true', default=True,
        help='Toggle exporting analytics reports (JSON, CSV, TXT)'
    )
    parser.add_argument(
        '--headless', action='store_true',
        help='Run in headless mode (no OpenCV GUI windows shown, recommended for headless servers/scripts)'
    )
    
    # Custom calibration overrides
    parser.add_argument('--height', type=float, default=1.3, help='Camera mounting height in meters')
    parser.add_argument('--focal', type=float, default=800.0, help='Camera focal length in pixels')
    parser.add_argument('--tilt', type=float, default=18.0, help='Camera tilt angle in degrees down')
    
    args = parser.parse_args()
    
    # Build calibration config
    calibration_config = {
        'enabled': True,
        'camera_height_m': args.height,
        'focal_length_px': args.focal,
        'camera_tilt_deg': args.tilt
    }
    
    # Setup engines
    severity_engine = SeverityEngine(calibration_config)
    analytics_mgr = AnalyticsManager()
    
    # Load model
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Loading YOLO model: {args.model}")
    print(f"Using device: {device}")
    
    try:
        model = YOLO(args.model)
        model.to(device)
    except Exception as e:
        print(f"Error loading model weights at {args.model}: {e}")
        print("Please check that the weights exist or train the model first.")
        sys.exit(1)
        
    src = args.source
    is_img = src.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp'))
    
    if is_img:
        run_on_image(src, model, severity_engine, analytics_mgr, args.conf, args.save_analysis)
    else:
        run_on_video(src, model, severity_engine, analytics_mgr, args.conf, args.save_analysis, args.headless)

if __name__ == '__main__':
    main()
