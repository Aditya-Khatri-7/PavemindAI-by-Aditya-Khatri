"""
benchmark_models.py  —  Automated Model Benchmarking and Weight Configurations
IBM Internship | Group 74 | AIML74 | UPES Dehradun
"""

import time
import os
import sys
from pathlib import Path
from ultralytics import YOLO
import torch
import numpy as np

def benchmark_model(weights_path, val_data_yaml, device):
    print(f"\nBenchmarking model: {weights_path}")
    if not Path(weights_path).exists():
        print(f"Error: Weights file '{weights_path}' does not exist.")
        return None
        
    try:
        model = YOLO(weights_path)
        model.to(device)
    except Exception as e:
        print(f"Error loading model: {e}")
        return None
        
    # 1. Run Validation using Ultralytics
    print("Running dataset validation...")
    val_results = model.val(data=val_data_yaml, split='val', verbose=False)
    
    # 2. Profile Inference speed (on first 50 images in test/val split)
    print("Profiling CPU inference speed...")
    # Find some PNG images to test speed
    img_files = list(Path("data_merged/images/val").glob("*.png"))[:50]
    if not img_files:
        img_files = list(Path("data/images").glob("*.png"))[:50]
        
    latencies = []
    # Warmup
    if img_files:
        for _ in range(5):
            model(img_files[0], conf=0.35, verbose=False)
            
        for img_path in img_files:
            t0 = time.time()
            model(img_path, conf=0.35, verbose=False)
            latencies.append((time.time() - t0) * 1000)
            
    avg_latency = np.mean(latencies) if latencies else 0.0
    avg_fps = 1000.0 / max(avg_latency, 1.0)
    
    # Extract box metrics
    precision = val_results.box.mp
    recall = val_results.box.mr
    map50 = val_results.box.map50
    map50_95 = val_results.box.map
    
    return {
        'path': weights_path,
        'precision': round(float(precision), 4),
        'recall': round(float(recall), 4),
        'map50': round(float(map50), 4),
        'map50_95': round(float(map50_95), 4),
        'latency_ms': round(float(avg_latency), 2),
        'fps': round(float(avg_fps), 2)
    }

def main():
    device = 'cpu' # Profile on CPU to match user hardware constraints
    val_data_yaml = 'pothole_dataset.yaml'
    
    old_weights = "runs/detect/yolov12n_pothole_detector5/weights/best.pt"
    new_weights = "runs/detect/yolov12n_merged_run/weights/best.pt"
    
    # Run benchmarks
    old_stats = benchmark_model(old_weights, val_data_yaml, device)
    new_stats = benchmark_model(new_weights, val_data_yaml, device)
    
    if not old_stats and not new_stats:
        print("Error: Could not benchmark any model.")
        sys.exit(1)
        
    print("\n" + "="*70)
    print(" MODEL BENCHMARK COMPARISON REPORT")
    print("="*70)
    print(f"{'Metric':<25s} | {'Old Model (25 Epochs)':<20s} | {'New Model (Merged 2e)':<20s}")
    print("-"*70)
    
    metrics_to_print = [
        ('path', 'Weights Path', str),
        ('precision', 'Precision', float),
        ('recall', 'Recall', float),
        ('map50', 'mAP@0.5', float),
        ('map50_95', 'mAP@0.5:0.95', float),
        ('latency_ms', 'Avg Latency (ms)', float),
        ('fps', 'Throughput (FPS)', float)
    ]
    
    for key, label, val_type in metrics_to_print:
        v1 = old_stats.get(key, "N/A") if old_stats else "N/A"
        v2 = new_stats.get(key, "N/A") if new_stats else "N/A"
        if val_type == float:
            v1_str = f"{v1:.4f}" if isinstance(v1, float) else str(v1)
            v2_str = f"{v2:.4f}" if isinstance(v2, float) else str(v2)
        else:
            v1_str = str(v1)
            v2_str = str(v2)
            
        print(f"{label:<25s} | {v1_str:<20s} | {v2_str:<20s}")
        
    print("="*70)
    
    # Auto-selection logic: Select based on mAP@0.5
    selected_model = None
    if old_stats and new_stats:
        if new_stats['map50'] >= old_stats['map50']:
            selected_model = new_stats
            print("\n>> Selected NEW MODEL trained on merged dataset as primary.")
        else:
            selected_model = old_stats
            print("\n>> Selected OLD MODEL as primary (better accuracy).")
    elif old_stats:
        selected_model = old_stats
        print("\n>> Selected OLD MODEL (new weights missing).")
    else:
        selected_model = new_stats
        print("\n>> Selected NEW MODEL (old weights missing).")
        
    best_weights = selected_model['path']
    
    # Automatically configure inference scripts to use these weights
    scripts_to_update = [
        Path("run_detector.py"),
        Path("run_detector_severity.py"),
        Path("../run_detector_severity.py") # Wrapper in parent
    ]
    
    for script_path in scripts_to_update:
        if script_path.exists():
            try:
                content = script_path.read_text()
                # Replace the defaults
                old_default = "runs/detect/yolov12n_pothole_detector5/weights/best.pt"
                new_default = best_weights
                
                # Check and replace
                if old_default in content and old_default != new_default:
                    content = content.replace(old_default, new_default)
                    script_path.write_text(content)
                    print(f"Updated default weights in: {script_path}")
            except Exception as e:
                print(f"Error updating script {script_path}: {e}")
                
    # Save the report to outputs/analysis
    out_dir = Path("outputs/analysis")
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "benchmark_report.txt"
    
    with open(report_path, 'w') as f:
        f.write("="*70 + "\n")
        f.write(" MODEL BENCHMARK ANALYSIS REPORT\n")
        f.write("="*70 + "\n")
        for key, label, _ in metrics_to_print:
            v1 = old_stats.get(key, "N/A") if old_stats else "N/A"
            v2 = new_stats.get(key, "N/A") if new_stats else "N/A"
            f.write(f"{label:<25} | Old: {str(v1):<20} | New: {str(v2):<20}\n")
        f.write("="*70 + "\n")
        f.write(f"Selected Best Weights: {best_weights}\n")
        f.write("="*70 + "\n")
        
    print(f"Benchmark report saved to: {report_path}\n")

if __name__ == "__main__":
    main()
