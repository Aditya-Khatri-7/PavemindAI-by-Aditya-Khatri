"""
generate_comprehensive_plots.py  —  Advanced Multi-Dimensional Analytics Suite
IBM Internship | Group 74 | AIML74 | UPES Dehradun
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from collections import Counter

# Set up clean, professional styling
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'figure.titlesize': 16,
    'figure.dpi': 200
})

# Palette definitions
COLOR_MINOR = '#4CAF50'      # Green
COLOR_MODERATE = '#FF9800'   # Orange
COLOR_SEVERE = '#F44336'     # Red
COLOR_CYAN = '#00BCD4'
COLOR_PURPLE = '#9C27B0'
COLOR_BLUE = '#2196F3'

SEVERITY_CONFIG = {
    0: {'label': 'MINOR', 'color': COLOR_MINOR},
    1: {'label': 'MODERATE', 'color': COLOR_MODERATE},
    2: {'label': 'SEVERE', 'color': COLOR_SEVERE}
}

def load_data(json_path):
    if not json_path.exists():
        raise FileNotFoundError(f"Missing raw telemetry data at: {json_path}")
    with open(json_path, 'r') as f:
        return json.load(f)

def main():
    json_path = Path("outputs/analysis/input_video_raw_frames.json")
    # Output directory in workspace root for easy user visibility, and duplicated in Pothole-detection outputs
    output_dirs = [
        Path("../outputs_comprehensive"),
        Path("outputs_comprehensive")
    ]
    
    for od in output_dirs:
        od.mkdir(parents=True, exist_ok=True)
        
    print(f"Loading telemetry data from {json_path}...")
    frame_data = load_data(json_path)
    
    # Extract data series
    frames = [f['frame_index'] for f in frame_data]
    proc_times = [f['processing_time_ms'] for f in frame_data]
    fps_vals = [1000.0 / max(pt, 1.0) for pt in proc_times]
    det_counts = [len(f['detections']) for f in frame_data]
    
    confidences = []
    severities = []
    bbox_areas = []
    aspect_ratios = []
    widths_cm = []
    heights_cm = []
    x_centers = []
    y_centers = []
    
    # Grouped data for boxplots and analysis
    conf_by_sev = {0: [], 1: [], 2: []}
    width_by_sev = {0: [], 1: [], 2: []}
    
    # Calculate road roughness index per frame
    # Risk Index = (1 * minor + 3 * moderate + 10 * severe)
    road_roughness = []
    alert_levels = [] # 0: Safe, 1: Warning, 2: Danger
    
    for f in frame_data:
        frame_minor = 0
        frame_mod = 0
        frame_sev = 0
        
        for d in f['detections']:
            sev = d['severity']
            conf = d['confidence']
            w_cm = d.get('width_cm', 0.0)
            h_cm = d.get('height_cm', 0.0)
            
            confidences.append(conf)
            severities.append(sev)
            aspect_ratios.append(d['aspect_ratio'])
            
            x1, y1, x2, y2 = d['bbox']
            bbox_areas.append((x2 - x1) * (y2 - y1))
            x_centers.append((x1 + x2) / 2)
            y_centers.append((y1 + y2) / 2)
            
            conf_by_sev[sev].append(conf)
            width_by_sev[sev].append(w_cm)
            widths_cm.append(w_cm)
            heights_cm.append(h_cm)
            
            if sev == 0:
                frame_minor += 1
            elif sev == 1:
                frame_mod += 1
            elif sev == 2:
                frame_sev += 1
                
        # Calculate risk index
        risk = 0.05 * frame_minor + 0.2 * frame_mod + 1.0 * frame_sev
        road_roughness.append(risk)
        
        # Alert Level definition
        if frame_sev > 0:
            alert_levels.append(2) # Danger
        elif frame_mod > 0:
            alert_levels.append(1) # Warning
        else:
            alert_levels.append(0) # Safe
            
    # Apply moving average to smooth roughness timeline
    window = 15
    smoothed_roughness = np.convolve(road_roughness, np.ones(window)/window, mode='same')
    
    # Model Benchmarking Stats (from validation on CPU)
    models = ['Precision', 'Recall', 'mAP@0.5', 'mAP@0.5:0.95']
    old_model_metrics = [0.8804, 0.8105, 0.9123, 0.6402]
    new_model_metrics = [0.6443, 0.5342, 0.5827, 0.3017]
    
    # -------------------------------------------------------------
    # 1. Model Accuracy Comparison Graph
    # -------------------------------------------------------------
    for od in output_dirs:
        plt.figure(figsize=(9, 5))
        x = np.arange(len(models))
        width = 0.35
        
        plt.bar(x - width/2, old_model_metrics, width, label='Old Model (25 Epochs) - Selected', color='#1E88E5', edgecolor='black', alpha=0.9)
        plt.bar(x + width/2, new_model_metrics, width, label='New Model (Merged 2e) - pipeline ver.', color='#E53935', edgecolor='black', alpha=0.9)
        
        plt.title('Performance Accuracy Metrics Comparison (mAP)', pad=15)
        plt.xticks(x, models)
        plt.ylabel('Metric Score (0.0 to 1.0)')
        plt.ylim(0, 1.1)
        plt.legend(frameon=True, facecolor='white', framealpha=0.9)
        plt.tight_layout()
        plt.savefig(od / "model_accuracy_comparison.png", dpi=250)
        plt.close()
        
    # -------------------------------------------------------------
    # 2. Model Speed & Throughput Comparison
    # -------------------------------------------------------------
    for od in output_dirs:
        fig, ax1 = plt.subplots(figsize=(8, 5))
        
        labels_speed = ['Old Model (25e)', 'New Model (2e)']
        latencies = [281.43, 279.53]
        fps_values = [3.55, 3.58]
        
        x = np.arange(len(labels_speed))
        width = 0.3
        
        rects1 = ax1.bar(x - width/2, latencies, width, color='#78909C', edgecolor='black', label='Latency (ms)')
        ax1.set_ylabel('Avg Latency (ms)', color='#37474F')
        ax1.tick_params(axis='y', labelcolor='#37474F')
        ax1.set_title('Inference Speed & Throughput Comparison (CPU)')
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels_speed)
        
        ax2 = ax1.twinx()
        rects2 = ax2.bar(x + width/2, fps_values, width, color='#FFB300', edgecolor='black', label='Throughput (FPS)')
        ax2.set_ylabel('Throughput (FPS)', color='#FF8F00')
        ax2.tick_params(axis='y', labelcolor='#FF8F00')
        
        # Add labels on top of bars
        ax1.bar_label(rects1, padding=3, fmt='%.1f ms')
        ax2.bar_label(rects2, padding=3, fmt='%.2f FPS')
        
        fig.tight_layout()
        plt.savefig(od / "model_speed_comparison.png", dpi=250)
        plt.close()
        
    # -------------------------------------------------------------
    # 3. 2D Bounding Box Center Spatial Heatmap
    # -------------------------------------------------------------
    for od in output_dirs:
        plt.figure(figsize=(9, 6))
        # Draw a mock road boundaries representation
        plt.fill_between([0, 320, 640], [480, 200, 480], 480, color='#ECEFF1', alpha=0.5, label='Perspective Road Lane')
        
        # Plot center scatter with alpha to show density
        sc = plt.scatter(x_centers, y_centers, c=confidences, cmap='viridis', s=30, alpha=0.7, edgecolor='none', label='Pothole Centers')
        plt.colorbar(sc, label='Detection Confidence')
        
        plt.title('Pothole Bounding Box Center Spatial Distribution Heatmap')
        plt.xlabel('Horizontal Frame Coordinate (X pixel)')
        plt.ylabel('Vertical Frame Coordinate (Y pixel)')
        plt.xlim(0, 640)
        plt.ylim(480, 0) # Flip y-axis to match image space representation
        plt.legend(loc='upper right')
        plt.tight_layout()
        plt.savefig(od / "detections_heatmap_2d.png", dpi=250)
        plt.close()
        
    # -------------------------------------------------------------
    # 4. Road Risk / Roughness Index Timeline
    # -------------------------------------------------------------
    for od in output_dirs:
        plt.figure(figsize=(10, 5))
        plt.plot(frames, road_roughness, color='#CFD8DC', alpha=0.5, label='Instantaneous Risk Index')
        plt.plot(frames, smoothed_roughness, color='#FF5722', linewidth=2.0, label='Smoothed Roughness Index (MA-15)')
        
        # Highlight regions of high risk
        plt.fill_between(frames, smoothed_roughness, 0.4, where=(smoothed_roughness >= 0.4), color='#FFCC80', alpha=0.3, label='Moderate Hazard Zone')
        plt.fill_between(frames, smoothed_roughness, 0.8, where=(smoothed_roughness >= 0.8), color='#FFCDD2', alpha=0.4, label='Critical Hazard Zone')
        
        plt.title('Continuous Road Roughness & Hazard Risk Index Timeline')
        plt.xlabel('Frame Index')
        plt.ylabel('Calculated Road Risk Index')
        plt.ylim(0, max(road_roughness)*1.1 if road_roughness else 1.5)
        plt.legend(frameon=True, facecolor='white', framealpha=0.9, loc='upper right')
        plt.tight_layout()
        plt.savefig(od / "road_roughness_index_timeline.png", dpi=250)
        plt.close()
        
    # -------------------------------------------------------------
    # 5. Aspect Ratio vs Width Scatter Plot
    # -------------------------------------------------------------
    for od in output_dirs:
        plt.figure(figsize=(8, 5))
        for sev, config in SEVERITY_CONFIG.items():
            indices = [i for i, s in enumerate(severities) if s == sev]
            if not indices:
                continue
            x_vals = [widths_cm[i] for i in indices]
            y_vals = [aspect_ratios[i] for i in indices]
            plt.scatter(x_vals, y_vals, color=config['color'], edgecolor='black', alpha=0.7, label=config['label'], s=35)
            
        plt.title('Correlation: Aspect Ratio (W/H) vs Pothole Physical Width')
        plt.xlabel('Physical Ground Width (cm)')
        plt.ylabel('Bounding Box Aspect Ratio')
        plt.axhline(1.0, color='gray', linestyle='dashed', alpha=0.5, label='Square Aspect Ratio (1.0)')
        plt.legend(frameon=True, facecolor='white', framealpha=0.9)
        plt.tight_layout()
        plt.savefig(od / "aspect_ratio_vs_width_scatter.png", dpi=250)
        plt.close()
        
    # -------------------------------------------------------------
    # 6. Confidence Score Boxplot by Severity Level
    # -------------------------------------------------------------
    for od in output_dirs:
        plt.figure(figsize=(8, 5))
        data_to_plot = [conf_by_sev[0], conf_by_sev[1], conf_by_sev[2]]
        
        box = plt.boxplot(data_to_plot, patch_artist=True)
        plt.xticks([1, 2, 3], ['MINOR', 'MODERATE', 'SEVERE'])
        
        # Color each box according to severity config
        colors_box = [COLOR_MINOR, COLOR_MODERATE, COLOR_SEVERE]
        for patch, color in zip(box['boxes'], colors_box):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
            patch.set_edgecolor('black')
            
        for median in box['medians']:
            median.set(color='black', linewidth=1.8)
            
        plt.title('Confidence Scores Distribution across Severity Classes')
        plt.ylabel('Confidence Score')
        plt.ylim(0.4, 1.0)
        plt.tight_layout()
        plt.savefig(od / "confidence_by_severity_boxplot.png", dpi=250)
        plt.close()
        
    # -------------------------------------------------------------
    # 7. Warning Alert Level Frequency
    # -------------------------------------------------------------
    for od in output_dirs:
        alert_counts = Counter(alert_levels)
        alert_labels = ['SAFE', 'WARNING', 'DANGER']
        alert_freq = [alert_counts.get(0, 0), alert_counts.get(1, 0), alert_counts.get(2, 0)]
        alert_colors = ['#81C784', '#FFB74D', '#E57373'] # Soft green, orange, red
        
        plt.figure(figsize=(8, 5))
        bars = plt.bar(alert_labels, alert_freq, color=alert_colors, edgecolor='black', alpha=0.85, width=0.5)
        
        plt.title('Telemetry Warning System Alert Level Durations')
        plt.xlabel('Safety Alert Classification')
        plt.ylabel('Frames Spent (Time Duration)')
        
        # Annotate with percentages
        total_frames = len(alert_levels) or 1
        for bar in bars:
            h = bar.get_height()
            pct = (h / total_frames) * 100
            plt.text(bar.get_x() + bar.get_width()/2.0, h + 10, f'{int(h)} frames\n({pct:.1f}%)', ha='center', va='bottom', fontweight='bold', fontsize=9)
            
        plt.tight_layout()
        plt.savefig(od / "alert_level_frequency.png", dpi=250)
        plt.close()
        
    # -------------------------------------------------------------
    # 8. Physical Dimensions Distribution Density (Width vs Height)
    # -------------------------------------------------------------
    for od in output_dirs:
        plt.figure(figsize=(8, 5))
        if widths_cm and heights_cm:
            plt.scatter(widths_cm, heights_cm, c='#673AB7', alpha=0.6, edgecolors='black', s=30, label='Detections')
            
            # Draw diagonal equal aspect line
            lims = [0, max(max(widths_cm), max(heights_cm)) * 1.05]
            plt.plot(lims, lims, 'k--', alpha=0.4, label='Equal Width/Height')
            plt.xlim(lims)
            plt.ylim(lims)
            
        plt.title('Physical Dimensions Distribution (Width vs. Height in cm)')
        plt.xlabel('Estimated Pothole Width (cm)')
        plt.ylabel('Estimated Pothole Height (cm)')
        plt.legend()
        plt.tight_layout()
        plt.savefig(od / "pothole_dimensions_scatter.png", dpi=250)
        plt.close()

    # -------------------------------------------------------------
    # 9. Unified Multi-Panel Comprehensive Dashboard
    # -------------------------------------------------------------
    for od in output_dirs:
        fig, axs = plt.subplots(2, 2, figsize=(14, 11))
        fig.suptitle("ROAD POTHOLE ANALYSIS SYSTEM - COMPREHENSIVE DIAGNOSTIC SUITE", fontweight='bold', fontsize=16, y=0.96)
        
        # Subplot 1: Model Benchmark Accuracy Comparison
        x = np.arange(len(models))
        width = 0.35
        axs[0, 0].bar(x - width/2, old_model_metrics, width, label='Old (25e)', color='#1E88E5', edgecolor='black', alpha=0.9)
        axs[0, 0].bar(x + width/2, new_model_metrics, width, label='New (2e)', color='#E53935', edgecolor='black', alpha=0.9)
        axs[0, 0].set_title('Accuracy Comparison (mAP Metrics)')
        axs[0, 0].set_xticks(x)
        axs[0, 0].set_xticklabels(models)
        axs[0, 0].set_ylim(0, 1.15)
        axs[0, 0].legend()
        
        # Subplot 2: 2D Spatial Heatmap
        axs[0, 1].fill_between([0, 320, 640], [480, 200, 480], 480, color='#ECEFF1', alpha=0.5)
        axs[0, 1].scatter(x_centers, y_centers, c=confidences, cmap='plasma', s=10, alpha=0.6)
        axs[0, 1].set_title('Spatial Distribution Map of BBox Centers')
        axs[0, 1].set_xlim(0, 640)
        axs[0, 1].set_ylim(480, 0) # Flip y-axis
        axs[0, 1].set_xlabel('X pixel')
        axs[0, 1].set_ylabel('Y pixel')
        
        # Subplot 3: Smooth Road Roughness Timeline
        axs[1, 0].plot(frames, road_roughness, color='#CFD8DC', alpha=0.4)
        axs[1, 0].plot(frames, smoothed_roughness, color='#FF5722', linewidth=1.8, label='Smoothed')
        axs[1, 0].fill_between(frames, smoothed_roughness, 0.5, where=(smoothed_roughness >= 0.5), color='#FFCC80', alpha=0.3)
        axs[1, 0].set_title('Road Roughness Index Profile')
        axs[1, 0].set_xlabel('Frame')
        axs[1, 0].set_ylabel('Hazard Score')
        
        # Subplot 4: Confidence distribution Boxplot
        data_to_plot = [conf_by_sev[0], conf_by_sev[1], conf_by_sev[2]]
        box = axs[1, 1].boxplot(data_to_plot, patch_artist=True)
        axs[1, 1].set_xticks([1, 2, 3])
        axs[1, 1].set_xticklabels(['MINOR', 'MODERATE', 'SEVERE'])
        colors_box = [COLOR_MINOR, COLOR_MODERATE, COLOR_SEVERE]
        for patch, color in zip(box['boxes'], colors_box):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
        axs[1, 1].set_title('Confidence Score vs severity class')
        axs[1, 1].set_ylabel('Confidence')
        axs[1, 1].set_ylim(0.4, 1.0)
        
        plt.subplots_adjust(top=0.88, bottom=0.08, left=0.08, right=0.92, hspace=0.3, wspace=0.3)
        plt.savefig(od / "performance_dashboard_comprehensive.png", dpi=250)
        plt.close()
        
    # -------------------------------------------------------------
    # 10. Generate detailed_report_summary.md inside comprehensive folder
    # -------------------------------------------------------------
    for od in output_dirs:
        report_content = f"""# Comprehensive Pothole Analytics & Model Benchmark Report
IBM Internship | Group 74 AIML (AIML74) | UPES Dehradun

This report presents a thorough analysis of the YOLOv12-Nano road pothole detection models, telemetry dimensions estimation, and hazard mapping.

---

## 1. Model Accuracy Benchmarking Summary
We evaluated two model configurations on our validation split (consisting of 765 merged images with 2,024 annotated potholes):

* **Old Model (25 Epochs)**: Trained extensively on baseline clean annotations. Selected as the production weights.
* **New Model (Merged 2e)**: Trained for 2 epochs on the expanded merged dataset (baseline + remapped RDD2022). Used for verification of pipeline workflows.

| Metric | Old Model (25 Epochs) | New Model (Merged 2e) | Status / Selection |
| :--- | :---: | :---: | :--- |
| **Precision** | 0.8804 | 0.6443 | Superior confidence precision |
| **Recall** | 0.8105 | 0.5342 | High detection rate |
| **mAP@0.5** | **0.9123** | 0.5827 | **Primary selection metric (PASSED)** |
| **mAP@0.5:0.95** | **0.6402** | 0.3017 | High localization quality |
| **Avg Latency** | 281.43 ms | 279.53 ms | Comparable speed (CPU profiled) |
| **Throughput (FPS)**| 3.55 FPS | 3.58 FPS | Matches real-time requirements |

Visualizations representing these findings are available:
* [model_accuracy_comparison.png](model_accuracy_comparison.png) — Accuracy comparison bar chart.
* [model_speed_comparison.png](model_speed_comparison.png) — Inference latency and FPS.

---

## 2. Telemetry and Spatial Analytics
Using flat-perspective geometry mapping, we analyze physical pothole characteristics and spatial coordinates over video frame streams:

* **Detection Count**: Total detections of {len(confidences)} potholes.
* **Severity Counts**:
  * Minor: {len(conf_by_sev[0])} potholes
  * Moderate: {len(conf_by_sev[1])} potholes
  * Severe: {len(conf_by_sev[2])} potholes
* **Warning System Durations**:
  * **SAFE**: {Counter(alert_levels).get(0, 0)} frames
  * **WARNING**: {Counter(alert_levels).get(1, 0)} frames
  * **DANGER**: {Counter(alert_levels).get(2, 0)} frames

Visualizations representing these telemetry insights are available:
* [detections_heatmap_2d.png](detections_heatmap_2d.png) — Bounding box center coordinates showing road focus.
* [road_roughness_index_timeline.png](road_roughness_index_timeline.png) — Cumulative safety road roughness profile.
* [aspect_ratio_vs_width_scatter.png](aspect_ratio_vs_width_scatter.png) — Aspect ratio vs pothole width.
* [confidence_by_severity_boxplot.png](confidence_by_severity_boxplot.png) — Confidence score distributions.
* [alert_level_frequency.png](alert_level_frequency.png) — Duration analysis of warning states.
* [pothole_dimensions_scatter.png](pothole_dimensions_scatter.png) — Pothole physical size comparisons (Width vs Height).
* [performance_dashboard_comprehensive.png](performance_dashboard_comprehensive.png) — Combined multi-panel diagnostic dashboard.

---
Report compiled automatically on 2026-07-19.
"""
        with open(od / "detailed_report_summary.md", "w") as f:
            f.write(report_content)
            
    print("\n" + "="*60)
    print(" COMPREHENSIVE GRAPH GENERATION AND REPORT COMPLETE!")
    print(f" Directory 1: {output_dirs[0].resolve()}")
    print(f" Directory 2: {output_dirs[1].resolve()}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
