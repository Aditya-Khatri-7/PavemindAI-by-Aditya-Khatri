"""
generate_plots.py  —  Generate 10 High-Resolution Performance Plots and Dashboard
IBM Internship | Group 74 | AIML74 | UPES Dehradun
"""

import os
import json
import csv
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from collections import Counter

# Setup style for clean, premium visualization
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'figure.titlesize': 15,
    'figure.dpi': 200
})

SEVERITY_CONFIG = {
    0: {'label': 'MINOR', 'color': '#4CAF50'},      # Green
    1: {'label': 'MODERATE', 'color': '#009688'},   # Teal / Orange-ish
    2: {'label': 'SEVERE', 'color': '#E53935'}      # Red
}

def load_raw_data(json_path):
    if not json_path.exists():
        raise FileNotFoundError(f"Missing raw telemetry data at: {json_path}")
    with open(json_path, 'r') as f:
        return json.load(f)

def generate_csv_data(frame_data, csv_path):
    print(f"Exporting flat tabular telemetry data to: {csv_path}...")
    headers = [
        'frame_index', 'processing_time_ms', 'fps',
        'detection_index', 'confidence', 'w_px', 'h_px', 'area_px',
        'aspect_ratio', 'pct_area', 'distance_m', 'width_cm', 'height_cm',
        'severity_score', 'severity', 'severity_label'
    ]
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for frame in frame_data:
            frame_idx = frame['frame_index']
            proc_ms = frame['processing_time_ms']
            fps = round(1000.0 / max(proc_ms, 1.0), 2)
            
            detections = frame['detections']
            if not detections:
                # Still output a row representing a frame with no detections
                writer.writerow([
                    frame_idx, proc_ms, fps,
                    -1, 0.0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1, 'NONE'
                ])
            else:
                for det_idx, det in enumerate(detections):
                    x1, y1, x2, y2 = det['bbox']
                    w_px = x2 - x1
                    h_px = y2 - y1
                    area_px = w_px * h_px
                    
                    writer.writerow([
                        frame_idx, proc_ms, fps,
                        det_idx,
                        round(det['confidence'], 4),
                        w_px, h_px, area_px,
                        det['aspect_ratio'],
                        det['pct_area'],
                        det.get('distance_m', 0.0),
                        det.get('width_cm', 0.0),
                        det.get('height_cm', 0.0),
                        det.get('severity_score', 0.0),
                        det['severity'],
                        SEVERITY_CONFIG[det['severity']]['label']
                    ])
                    
    print("CSV export complete.")

def main():
    json_path = Path("outputs/analysis/input_video_raw_frames.json")
    csv_path = Path("outputs/analysis/input_video_raw_frames.csv")
    graph_dir = Path("outputs/graphs")
    graph_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Load data
    frame_data = load_raw_data(json_path)
    
    # 2. Export tabular CSV
    generate_csv_data(frame_data, csv_path)
    
    # 3. Process lists for plotting
    frames = [f['frame_index'] for f in frame_data]
    proc_times = [f['processing_time_ms'] for f in frame_data]
    fps_vals = [1000.0 / max(pt, 1.0) for pt in proc_times]
    det_counts = [len(f['detections']) for f in frame_data]
    
    confidences = []
    severities = []
    bbox_areas = []
    aspect_ratios = []
    pct_areas = []
    widths_cm = []
    heights_cm = []
    
    for f in frame_data:
        for d in f['detections']:
            confidences.append(d['confidence'])
            severities.append(d['severity'])
            aspect_ratios.append(d['aspect_ratio'])
            pct_areas.append(d['pct_area'])
            
            x1, y1, x2, y2 = d['bbox']
            bbox_areas.append((x2 - x1) * (y2 - y1))
            
            if d.get('width_cm') is not None:
                widths_cm.append(d['width_cm'])
                heights_cm.append(d['height_cm'])
                
    total_dets = len(confidences)
    print(f"Total detections collected: {total_dets}")
    
    # -------------------------------------------------------------
    # Plot 1: Detection Confidence Histogram
    # -------------------------------------------------------------
    plt.figure(figsize=(8, 5))
    plt.hist(confidences, bins=20, color='#1976D2', edgecolor='black', alpha=0.85)
    plt.axvline(np.mean(confidences) if confidences else 0.0, color='red', linestyle='dashed', linewidth=1.5, label=f'Mean: {np.mean(confidences):.2f}' if confidences else '')
    plt.title("Pothole Bounding Box Confidence Score Distribution")
    plt.xlabel("Confidence Score")
    plt.ylabel("Frequency")
    plt.legend()
    plt.tight_layout()
    plt.savefig(graph_dir / "confidence_histogram.png", dpi=250)
    plt.close()
    
    # -------------------------------------------------------------
    # Plot 2: Severity Distribution Histogram/Bar
    # -------------------------------------------------------------
    sev_counts = Counter(severities)
    labels = [SEVERITY_CONFIG[i]['label'] for i in sorted(SEVERITY_CONFIG.keys())]
    counts = [sev_counts.get(i, 0) for i in sorted(SEVERITY_CONFIG.keys())]
    colors = [SEVERITY_CONFIG[i]['color'] for i in sorted(SEVERITY_CONFIG.keys())]
    
    plt.figure(figsize=(8, 5))
    bars = plt.bar(labels, counts, color=colors, edgecolor='black', alpha=0.85, width=0.6)
    plt.title("Accumulative Pothole Severity Frequency")
    plt.xlabel("Severity Classification")
    plt.ylabel("Detection Count")
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 10, f'{int(yval)}', ha='center', va='bottom', fontweight='bold')
    plt.tight_layout()
    plt.savefig(graph_dir / "severity_distribution.png", dpi=250)
    plt.close()
    
    # -------------------------------------------------------------
    # Plot 3: Minor vs Moderate vs Severe Pie Chart
    # -------------------------------------------------------------
    plt.figure(figsize=(7, 7))
    plt.pie(
        counts, 
        labels=labels, 
        colors=colors, 
        autopct='%1.1f%%', 
        startangle=140, 
        textprops={'fontweight': 'bold'},
        wedgeprops={'edgecolor': 'black', 'linewidth': 1, 'antialiased': True}
    )
    plt.title("Severity Distribution Proportion", pad=20)
    plt.tight_layout()
    plt.savefig(graph_dir / "severity_pie_chart.png", dpi=250)
    plt.close()
    
    # -------------------------------------------------------------
    # Plot 4: Detection Count per Frame
    # -------------------------------------------------------------
    plt.figure(figsize=(10, 5))
    plt.plot(frames, det_counts, color='#7E57C2', linewidth=1.2, alpha=0.8)
    plt.title("Detections Count per Video Frame")
    plt.xlabel("Frame Index")
    plt.ylabel("Number of Detections")
    plt.tight_layout()
    plt.savefig(graph_dir / "detections_per_frame.png", dpi=250)
    plt.close()
    
    # -------------------------------------------------------------
    # Plot 5: FPS Over Time
    # -------------------------------------------------------------
    plt.figure(figsize=(10, 5))
    plt.plot(frames, fps_vals, color='#00897B', linewidth=1.2, alpha=0.8)
    plt.axhline(np.mean(fps_vals), color='red', linestyle='dashed', linewidth=1.5, label=f'Avg: {np.mean(fps_vals):.1f} FPS')
    plt.title("Model Processing Speed (FPS) Timeline")
    plt.xlabel("Frame Index")
    plt.ylabel("Frames Per Second (FPS)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(graph_dir / "fps_over_time.png", dpi=250)
    plt.close()
    
    # -------------------------------------------------------------
    # Plot 6: Processing Time per Frame
    # -------------------------------------------------------------
    plt.figure(figsize=(10, 5))
    plt.plot(frames, proc_times, color='#FF8F00', linewidth=1.2, alpha=0.8)
    plt.axhline(np.mean(proc_times), color='red', linestyle='dashed', linewidth=1.5, label=f'Avg: {np.mean(proc_times):.1f} ms')
    plt.title("Model Inference & Overhead Latency per Frame")
    plt.xlabel("Frame Index")
    plt.ylabel("Processing Time (ms)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(graph_dir / "processing_time_per_frame.png", dpi=250)
    plt.close()
    
    # -------------------------------------------------------------
    # Plot 7: Bounding-Box Size Distribution (Pixel Area)
    # -------------------------------------------------------------
    plt.figure(figsize=(8, 5))
    plt.hist(bbox_areas, bins=25, color='#AB47BC', edgecolor='black', alpha=0.85)
    plt.title("Pothole Bounding Box Pixel Area Distribution")
    plt.xlabel("Area (Pixels)")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(graph_dir / "bbox_size_distribution.png", dpi=250)
    plt.close()
    
    # -------------------------------------------------------------
    # Plot 8: Estimated Pothole Size Distribution (Width in cm)
    # -------------------------------------------------------------
    plt.figure(figsize=(8, 5))
    if widths_cm:
        plt.hist(widths_cm, bins=20, color='#26A69A', edgecolor='black', alpha=0.85)
        plt.axvline(np.mean(widths_cm), color='red', linestyle='dashed', linewidth=1.5, label=f'Avg: {np.mean(widths_cm):.1f} cm')
        plt.legend()
    plt.title("Estimated Ground Physical Pothole Width Distribution")
    plt.xlabel("Estimated Width (cm)")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(graph_dir / "pothole_physical_width_distribution.png", dpi=250)
    plt.close()
    
    # -------------------------------------------------------------
    # Plot 9: Confidence vs Estimated Size Scatter Plot
    # -------------------------------------------------------------
    plt.figure(figsize=(8, 5))
    if widths_cm and confidences:
        # Match length of arrays
        min_len = min(len(widths_cm), len(confidences))
        x = np.array(widths_cm[:min_len])
        y = np.array(confidences[:min_len])
        
        plt.scatter(x, y, color='#26C6DA', edgecolor='black', alpha=0.6, s=30)
        # Linear trendline
        try:
            m, b = np.polyfit(x, y, 1)
            plt.plot(x, m*x + b, color='red', linewidth=1.5, label='Regression Line')
            plt.legend()
        except Exception:
            pass
            
    plt.title("Detection Confidence vs. Estimated Pothole Width")
    plt.xlabel("Estimated Physical Width (cm)")
    plt.ylabel("Detection Confidence Score")
    plt.tight_layout()
    plt.savefig(graph_dir / "confidence_vs_size_scatter.png", dpi=250)
    plt.close()
    
    # -------------------------------------------------------------
    # Plot 10: Summary Dashboard
    # -------------------------------------------------------------
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("ROAD POTHOLE DETECTOR SYSTEM PERFORMANCE DASHBOARD", fontweight='bold', fontsize=16, y=0.96)
    
    # Subplot 1: FPS & Detections Over Time
    axs[0, 0].plot(frames, det_counts, color='#7E57C2', alpha=0.7, label='Detections')
    axs[0, 0].set_ylabel("Number of Potholes", color='#7E57C2')
    axs[0, 0].tick_params(axis='y', labelcolor='#7E57C2')
    
    ax2 = axs[0, 0].twinx()
    ax2.plot(frames, fps_vals, color='#00897B', alpha=0.4, label='FPS')
    ax2.set_ylabel("FPS", color='#00897B')
    ax2.tick_params(axis='y', labelcolor='#00897B')
    axs[0, 0].set_title("Timeline: Detections & FPS")
    axs[0, 0].set_xlabel("Frame Index")
    
    # Subplot 2: Severity Pie Chart
    axs[0, 1].pie(
        counts, 
        labels=labels, 
        colors=colors, 
        autopct='%1.1f%%', 
        startangle=140,
        textprops={'fontweight': 'bold', 'fontsize': 10},
        wedgeprops={'edgecolor': 'black', 'linewidth': 0.8}
    )
    axs[0, 1].set_title("Accumulated Severity Breakdown")
    
    # Subplot 3: Bounding-Box Area Histogram
    axs[1, 0].hist(bbox_areas, bins=20, color='#AB47BC', edgecolor='black', alpha=0.8)
    axs[1, 0].set_title("Detection Pixel Area Profile")
    axs[1, 0].set_xlabel("BBox Pixel Area")
    axs[1, 0].set_ylabel("Frequency")
    
    # Subplot 4: Physical width vs Confidence
    if widths_cm and confidences:
        min_len = min(len(widths_cm), len(confidences))
        axs[1, 1].scatter(widths_cm[:min_len], confidences[:min_len], color='#26C6DA', alpha=0.5, s=15)
        axs[1, 1].set_title("Correlation: Confidence vs Width")
        axs[1, 1].set_xlabel("Estimated Width (cm)")
        axs[1, 1].set_ylabel("Confidence Score")
        
    plt.subplots_adjust(top=0.88, bottom=0.08, left=0.08, right=0.92, hspace=0.3, wspace=0.3)
    plt.savefig(graph_dir / "performance_dashboard.png", dpi=250)
    plt.close()
    
    print("\n" + "="*50)
    print(" ALL 10 ANALYTICS GRAPHS GENERATED SUCCESSFULLY")
    print("="*50)
    print(f" Saved directory : {graph_dir}")
    print(f" Graphs list     :")
    print("   1. confidence_histogram.png")
    print("   2. severity_distribution.png")
    print("   3. severity_pie_chart.png")
    print("   4. detections_per_frame.png")
    print("   5. fps_over_time.png")
    print("   6. processing_time_per_frame.png")
    print("   7. bbox_size_distribution.png")
    print("   8. pothole_physical_width_distribution.png")
    print("   9. confidence_vs_size_scatter.png")
    print("  10. performance_dashboard.png (Summary Dashboard)")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
