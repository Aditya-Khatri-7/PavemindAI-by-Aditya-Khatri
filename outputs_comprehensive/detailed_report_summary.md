# Comprehensive Pothole Analytics & Model Benchmark Report
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

* **Detection Count**: Total detections of 2302 potholes.
* **Severity Counts**:
  * Minor: 731 potholes
  * Moderate: 719 potholes
  * Severe: 852 potholes
* **Warning System Durations**:
  * **SAFE**: 134 frames
  * **WARNING**: 81 frames
  * **DANGER**: 477 frames

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
