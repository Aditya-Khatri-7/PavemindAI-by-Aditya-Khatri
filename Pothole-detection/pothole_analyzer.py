"""
pothole_analyzer.py  —  Modular Analysis and Visualization Engine
IBM Internship | Group 74 | AIML74 | UPES Dehradun

Contains the logic for:
1. Physical size estimation & severity scoring (SeverityEngine)
2. Road condition warning system (AlertSystem)
3. CSV/JSON/TXT Report Generation (AnalyticsManager)
4. OpenCV drawing overlays (Visualizer)
"""

import cv2
import numpy as np
import time
import os
import json
import csv
from pathlib import Path
from collections import Counter

# ─────────────────────────────────────────────────────────────────
#  CONFIGURABLE THRESHOLDS & SETTINGS
# ─────────────────────────────────────────────────────────────────

# Severity classification configs
# Combining two factors: Frame Area Percentage and Confidence
# Weight: Area % (70%) and Confidence (30%)
SEVERITY_ENGINE_CONFIG = {
    'weights': {
        'physical_size': 0.45,
        'depth_proxy': 0.20,
        'confidence': 0.15,
        'aspect': 0.10,
        'persistence': 0.10
    },
    'thresholds': {
        'severe': 0.58,    # lowered from 0.70 — >=58% score = SEVERE
        'moderate': 0.35   # lowered from 0.45 — >=35% score = MODERATE
    },
    'limits': {
        'minor_pct': 0.5,     # fallback limits
        'severe_pct': 2.5,
        'ideal_aspect_min': 1.0,
        'ideal_aspect_max': 3.0,
        'minor_w_cm': 20.0,   # <20cm is minor  (was 30cm)
        'severe_w_cm': 50.0,  # >=50cm is severe (was 70cm)
        'minor_h_cm': 10.0,   # <10cm is minor   (was 15cm)
        'severe_h_cm': 25.0   # >=25cm is severe  (was 35cm)
    },
    'filters': {
        'min_confidence': 0.15,       # Reject low-probability detections (changed from 0.25)
        'horizon_y2_pct': 0.30,       # Bottom edge must be below 30% height (was 40%)
        'horizon_y1_pct': 0.20,       # Top edge must be below 20% height (was 30%)
        'min_aspect_ratio': 0.40,     # Discard vertical lines/tire tracks (was 0.80)
        'max_aspect_ratio': 6.00,     # Discard flat bands/lines (was 5.00)
        'min_w_px': 10,               # Discard tiny noise width (was 15)
        'min_h_px': 8,                # Discard tiny noise height (was 10)
        'min_area_px': 80,            # Discard tiny area noise (was 150)
        'max_area_pct': 30.0          # Discard extremely large boxes spanning windshield/wiper (was 25.0)
    }
}

# Real-world camera calibration default values
# Assuming standard dashcam placement on a mid-sized vehicle
DEFAULT_CALIBRATION = {
    'enabled': True,
    'camera_height_m': 1.3,      # height of camera above ground
    'focal_length_px': 800,      # approximate focal length for 640x640 frame
    'camera_tilt_deg': 18.0,     # downwards tilt angle relative to horizon
}

SEVERITY_CONFIG = {
    0: {
        'label': 'MINOR',
        'alert': 'Road Condition Good — Small Pothole Ahead',
        'color': (76, 175, 80),      # Bright Green (BGR: 76, 175, 80)
        'bg_color': (27, 94, 32),     # Dark Green (BGR: 27, 94, 32)
        'tag': '[  OK  ]',
    },
    1: {
        'label': 'MODERATE',
        'alert': 'Drive Carefully — Potholes Detected',
        'color': (0, 150, 136),      # Teal / Dark Orange (BGR: 0, 150, 136)
        'bg_color': (0, 77, 64),      # Deep Teal (BGR: 0, 77, 64)
        'tag': '[ WARN ]',
    },
    2: {
        'label': 'SEVERE',
        'alert': 'DANGER — Large Pothole Ahead!',
        'color': (30, 30, 244),      # Vivid Crimson Red (BGR: 30, 30, 244)
        'bg_color': (15, 15, 110),    # Deep Red (BGR: 15, 15, 110)
        'tag': '[DANGER]',
    }
}

# ─────────────────────────────────────────────────────────────────
#  1. SEVERITY ENGINE
# ─────────────────────────────────────────────────────────────────

class SeverityEngine:
    """
    Computes size, aspect ratios, estimated physical parameters, and severity
    score for detected potholes using a multi-factor logic.
    """
    def __init__(self, calibration_config=None):
        self.cal = calibration_config if calibration_config is not None else DEFAULT_CALIBRATION
        self.track_history = {} # Maps track_id -> frame_count

    def estimate_physical_dimensions(self, x1, y1, x2, y2, img_w, img_h):
        """
        Estimates the physical distance and size of the pothole (in cm)
        on the flat-ground projection assumption.
        """
        w_px = x2 - x1
        h_px = y2 - y1
        x_c = (x1 + x2) / 2
        
        # We use the bottom y2 as the contact point on the road
        c_x, c_y = img_w / 2.0, img_h / 2.0
        
        if not self.cal.get('enabled', False):
            return None, None, None # Calibration disabled
        
        H = self.cal['camera_height_m']
        # Scale focal length to match image width relative to the base 640px calibration
        base_width = 640.0
        f = self.cal['focal_length_px'] * (img_w / base_width)
        theta_rad = np.radians(self.cal['camera_tilt_deg'])
        
        # Angular offset of the base of the pothole from the center vertical pixel
        # positive values mean below optical center (closer)
        phi_rad = (y2 - c_y) / f
        
        # Ground angle of projection
        alpha = theta_rad + phi_rad
        
        # If angle is parallel to or above horizon, cap distance at a default far value
        if alpha <= 0.05:
            distance_m = 25.0
        else:
            distance_m = H / np.tan(alpha)
            
        # Physical width (horizontal distance projection)
        # horizontal angle from center
        phi_x_rad = (x_c - c_x) / f
        slant_distance = distance_m / np.cos(phi_x_rad)
        width_m = (w_px * slant_distance) / f
        
        # Physical height (depth distance projection)
        # using derivative of distance w.r.t tilt/pixel offset
        # delta_d = H * (1 + tan^2(alpha)) * delta_alpha / tan^2(alpha)
        # simplier projection:
        angle_top = theta_rad + ((y1 - c_y) / f)
        if angle_top <= 0.05:
            distance_top_m = 30.0
        else:
            distance_top_m = H / np.tan(angle_top)
            
        height_m = max(distance_top_m - distance_m, 0.01)
        
        # Convert to centimeters
        width_cm = max(width_m * 100.0, 1.0)
        height_cm = max(height_m * 100.0, 1.0)
        
        return round(distance_m, 2), round(width_cm, 1), round(height_cm, 1)

    def analyze_pothole(self, box, img_w, img_h, track_id=None):
        """
        Extracts image space metrics, runs physical size estimation,
        and determines multi-factor severity.
        """
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        conf = float(box.conf[0])
        
        # Post-Processing Filters to eliminate false positives (clouds, tyre tracks, good road marks, etc.)
        filters = SEVERITY_ENGINE_CONFIG.get('filters', {})
        
        # 1. Confidence Filter
        min_conf = filters.get('min_confidence', 0.15)
        if conf < min_conf:
            return None
            
        # 2. Horizon & Sky Filter (Spatial Constraint)
        # Road surfaces occupy the lower portion of the frame; sky/hills/clouds occupy the upper portion.
        horizon_y2 = img_h * filters.get('horizon_y2_pct', 0.30)
        horizon_y1 = img_h * filters.get('horizon_y1_pct', 0.20)
        if y2 < horizon_y2:  # Bottom edge is too high up (floating in sky or horizon)
            return None
        if y1 < horizon_y1:  # Top edge is too high up (starts in sky or background hills)
            return None
            
        w_px = x2 - x1
        h_px = y2 - y1
        area_px = w_px * h_px
        total_area = img_w * img_h
        
        # 3. Aspect Ratio Filter (Geometric Constraint)
        # Due to perspective foreshortening, real road potholes appear wide and flat (aspect ratio > 1.0).
        # Vertical markings like tyre tracks, seams, or poles are narrow and tall (aspect ratio < 0.60).
        aspect = round(w_px / max(h_px, 1), 2)
        min_aspect = filters.get('min_aspect_ratio', 0.40)
        max_aspect = filters.get('max_aspect_ratio', 6.00)
        if aspect < min_aspect or aspect > max_aspect:
            return None
            
        # 4. Scale & Area Filter (Noise / windshield obstruction rejection)
        min_w = filters.get('min_w_px', 10)
        min_h = filters.get('min_h_px', 8)
        min_area = filters.get('min_area_px', 80)
        max_area_p = filters.get('max_area_pct', 30.0)
        
        if w_px < min_w or h_px < min_h or area_px < min_area:
            return None
        if (area_px / total_area) * 100 > max_area_p:
            return None
            
        # Try to retrieve tracking ID directly from box if it is present
        if track_id is None and hasattr(box, 'id') and box.id is not None:
            try:
                track_id = int(box.id[0].item())
            except Exception:
                pass
        
        # Basic pixel dimensions
        w_px = x2 - x1
        h_px = y2 - y1
        area_px = w_px * h_px
        total_area = img_w * img_h
        
        # Aspect ratio (width / height)
        aspect = round(w_px / max(h_px, 1), 2)
        
        # Frame percentage area
        pct_area = (area_px / total_area) * 100
        
        # Estimate physical sizes if calibration is configured
        distance, p_w_cm, p_h_cm = self.estimate_physical_dimensions(x1, y1, x2, y2, img_w, img_h)
        
        # 1. Physical Size factor (based on estimated width)
        if self.cal.get('enabled', False) and p_w_cm is not None:
            min_w = SEVERITY_ENGINE_CONFIG['limits']['minor_w_cm']
            sev_w = SEVERITY_ENGINE_CONFIG['limits']['severe_w_cm']
            if p_w_cm >= sev_w:
                physical_size_factor = 1.0
            elif p_w_cm < min_w:
                physical_size_factor = (max(p_w_cm, 0.0) / min_w) * 0.3
            else:
                physical_size_factor = 0.3 + (p_w_cm - min_w) / (sev_w - min_w) * 0.4
        else:
            # Fallback to image space percentage area if calibration is not available
            min_p = SEVERITY_ENGINE_CONFIG['limits']['minor_pct']
            sev_p = SEVERITY_ENGINE_CONFIG['limits']['severe_pct']
            if pct_area >= sev_p:
                physical_size_factor = 1.0
            elif pct_area < min_p:
                physical_size_factor = (pct_area / min_p) * 0.3
            else:
                physical_size_factor = 0.3 + (pct_area - min_p) / (sev_p - min_p) * 0.4
                
        # 2. Depth Proxy factor (based on estimated physical height or h_px as fallback)
        if self.cal.get('enabled', False) and p_h_cm is not None:
            min_h = SEVERITY_ENGINE_CONFIG['limits']['minor_h_cm']
            sev_h = SEVERITY_ENGINE_CONFIG['limits']['severe_h_cm']
            if p_h_cm >= sev_h:
                depth_proxy_factor = 1.0
            elif p_h_cm < min_h:
                depth_proxy_factor = (max(p_h_cm, 0.0) / min_h) * 0.3
            else:
                depth_proxy_factor = 0.3 + (p_h_cm - min_h) / (sev_h - min_h) * 0.4
        else:
            # Fallback to height ratio relative to frame height
            h_ratio = h_px / img_h
            depth_proxy_factor = min(h_ratio * 4.0, 1.0)
            
        # 3. Confidence factor
        conf_factor = conf
        
        # 4. Aspect/Shape factor
        asp_min = SEVERITY_ENGINE_CONFIG['limits']['ideal_aspect_min']
        asp_max = SEVERITY_ENGINE_CONFIG['limits']['ideal_aspect_max']
        if asp_min <= aspect <= asp_max:
            aspect_factor = 1.0
        else:
            aspect_factor = max(1.0 - min(abs(aspect - asp_min), abs(aspect - asp_max)) / 3.0, 0.2)
            
        # 5. Tracking Persistence factor
        if track_id is not None:
            self.track_history[track_id] = self.track_history.get(track_id, 0) + 1
            persistence_factor = min(self.track_history[track_id], 15) / 15.0
        else:
            persistence_factor = 0.5 # Default middle value for single images or un-tracked detections
            
        # Combine using weights
        w_size = SEVERITY_ENGINE_CONFIG['weights']['physical_size']
        w_depth = SEVERITY_ENGINE_CONFIG['weights']['depth_proxy']
        w_conf = SEVERITY_ENGINE_CONFIG['weights']['confidence']
        w_asp = SEVERITY_ENGINE_CONFIG['weights']['aspect']
        w_pers = SEVERITY_ENGINE_CONFIG['weights']['persistence']
        
        sev_score = (
            w_size * physical_size_factor +
            w_depth * depth_proxy_factor +
            w_conf * conf_factor +
            w_asp * aspect_factor +
            w_pers * persistence_factor
        )
        
        # Classify based on configurable thresholds
        thresh_sev = SEVERITY_ENGINE_CONFIG['thresholds']['severe']
        thresh_mod = SEVERITY_ENGINE_CONFIG['thresholds']['moderate']
        
        if sev_score >= thresh_sev:
            severity = 2  # Severe
        elif sev_score >= thresh_mod:
            severity = 1  # Moderate
        else:
            severity = 0  # Minor
            
        return {
            'bbox': (x1, y1, x2, y2),
            'track_id': track_id,
            'confidence': conf,
            'w_px': w_px,
            'h_px': h_px,
            'area_px': area_px,
            'aspect_ratio': aspect,
            'pct_area': round(pct_area, 3),
            'distance_m': distance,
            'width_cm': p_w_cm,
            'height_cm': p_h_cm,
            'severity_score': round(sev_score, 3),
            'severity': severity
        }

# ─────────────────────────────────────────────────────────────────
#  2. ROAD ALERT SYSTEM
# ─────────────────────────────────────────────────────────────────

class AlertSystem:
    """
    Computes overall road condition and alerts based on the highest
    severity detection in the current frame.
    """
    @staticmethod
    def get_overall_road_condition(severity_counts):
        """
        Determines overall alert status:
        No detections -> Green (Good)
        Highest severity is 0 -> Yellow (Good/Minor warnings)
        Highest severity is 1 -> Orange (Drive Carefully)
        Highest severity is 2 -> Red (Danger)
        """
        # Filter out keys with 0 count
        active_counts = {k: v for k, v in severity_counts.items() if v > 0}
        if not active_counts:
            return {
                'level': -1,
                'label': 'GOOD',
                'alert': 'Road Condition Good — Keep Driving',
                'color': (76, 175, 80),      # Green
                'bg_color': (27, 94, 32),
                'tag': '[  OK  ]'
            }
            
        max_severity = max(active_counts.keys())
        return {
            'level': max_severity,
            **SEVERITY_CONFIG[max_severity]
        }

# ─────────────────────────────────────────────────────────────────
#  3. ANALYTICS MANAGER
# ─────────────────────────────────────────────────────────────────

class AnalyticsManager:
    """
    Collects per-frame metrics and exports JSON, CSV, and TXT analytics summaries.
    """
    def __init__(self):
        self.frame_data = []
        self.start_time = time.time()

    def record_frame(self, frame_idx, detections, processing_time_ms):
        """
        Records the structured details of all detections in a single frame.
        """
        self.frame_data.append({
            'frame_index': frame_idx,
            'processing_time_ms': processing_time_ms,
            'detections': detections
        })

    def generate_image_summary(self, detections, processing_time_ms, source_name):
        """
        Generates and saves analytics files for single-image runs.
        """
        total_potholes = len(detections)
        confidences = [d['confidence'] for d in detections]
        areas = [d['pct_area'] for d in detections]
        
        avg_conf = np.mean(confidences) if confidences else 0.0
        avg_size = np.mean(areas) if areas else 0.0
        
        largest = max(detections, key=lambda x: x['area_px']) if detections else None
        smallest = min(detections, key=lambda x: x['area_px']) if detections else None
        
        severity_counts = Counter([d['severity'] for d in detections])
        
        summary = {
            'source': source_name,
            'total_potholes': total_potholes,
            'minor_count': severity_counts[0],
            'moderate_count': severity_counts[1],
            'severe_count': severity_counts[2],
            'average_confidence': round(float(avg_conf), 3),
            'average_size_pct': round(float(avg_size), 3),
            'largest_pothole': {
                'width_cm': largest['width_cm'] if largest else None,
                'height_cm': largest['height_cm'] if largest else None,
                'pct_area': largest['pct_area'] if largest else None,
                'confidence': largest['confidence'] if largest else None
            } if largest else None,
            'smallest_pothole': {
                'width_cm': smallest['width_cm'] if smallest else None,
                'height_cm': smallest['height_cm'] if smallest else None,
                'pct_area': smallest['pct_area'] if smallest else None,
                'confidence': smallest['confidence'] if smallest else None
            } if smallest else None,
            'processing_time_ms': round(processing_time_ms, 2)
        }
        
        self.export_reports(summary, 'image', source_name)
        return summary

    def generate_video_summary(self, source_name):
        """
        Generates and saves analytics files for video or webcam runs.
        """
        total_frames = len(self.frame_data)
        if total_frames == 0:
            return {}
            
        elapsed_sec = time.time() - self.start_time
        avg_fps = total_frames / max(elapsed_sec, 0.1)
        
        total_detections_count = 0
        max_potholes_in_frame = 0
        severity_counts = Counter()
        processing_times = []
        
        all_detections = []
        
        for f in self.frame_data:
            num_dets = len(f['detections'])
            total_detections_count += num_dets
            max_potholes_in_frame = max(max_potholes_in_frame, num_dets)
            processing_times.append(f['processing_time_ms'])
            
            for d in f['detections']:
                severity_counts[d['severity']] += 1
                all_detections.append(d)
                
        avg_potholes = total_detections_count / total_frames
        avg_proc_time = np.mean(processing_times) if processing_times else 0.0
        
        dominant_severity = max(severity_counts.keys()) if severity_counts else -1
        highest_severity_str = SEVERITY_CONFIG[dominant_severity]['label'] if dominant_severity != -1 else 'NONE'
        
        summary = {
            'source': source_name,
            'total_frames': total_frames,
            'average_fps': round(avg_fps, 2),
            'total_detections': total_detections_count,
            'average_potholes_per_frame': round(avg_potholes, 2),
            'max_potholes_in_one_frame': max_potholes_in_frame,
            'minor_count': severity_counts[0],
            'moderate_count': severity_counts[1],
            'severe_count': severity_counts[2],
            'highest_severity_encountered': highest_severity_str,
            'average_processing_time_ms': round(float(avg_proc_time), 2),
            'total_elapsed_seconds': round(elapsed_sec, 2)
        }
        
        # Export raw frame telemetry data for plot generation
        out_dir = Path('outputs/analysis')
        out_dir.mkdir(parents=True, exist_ok=True)
        base_name = Path(source_name).stem
        raw_json_path = out_dir / f"{base_name}_raw_frames.json"
        with open(raw_json_path, 'w') as f:
            json.dump(self.frame_data, f, indent=4)
            
        self.export_reports(summary, 'video', source_name)
        return summary

    def export_reports(self, summary, run_type, source_name):
        """
        Saves reports to outputs/analysis/ folder in JSON, CSV, and TXT formats.
        """
        out_dir = Path('outputs/analysis')
        out_dir.mkdir(parents=True, exist_ok=True)
        
        base_name = Path(source_name).stem
        
        # 1. Export JSON
        json_path = out_dir / f"{base_name}_analysis.json"
        with open(json_path, 'w') as f:
            json.dump(summary, f, indent=4)
            
        # 2. Export CSV
        csv_path = out_dir / f"{base_name}_analysis.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            for k, v in summary.items():
                if isinstance(v, dict):
                    # Flatten child dictionaries
                    for sub_k, sub_v in v.items():
                        writer.writerow([f"{k}_{sub_k}", sub_v])
                else:
                    writer.writerow([k, v])
                    
        # 3. Export TXT (Human readable report)
        txt_path = out_dir / f"{base_name}_analysis.txt"
        with open(txt_path, 'w') as f:
            f.write("="*60 + "\n")
            f.write(f" ROAD DETECTOR SYSTEM - ANALYTICS REPORT ({run_type.upper()})\n")
            f.write("="*60 + "\n")
            f.write(f"Source file        : {summary.get('source')}\n")
            
            if run_type == 'image':
                f.write(f"Total Detections   : {summary.get('total_potholes')}\n")
                f.write(f"  - Minor          : {summary.get('minor_count')}\n")
                f.write(f"  - Moderate       : {summary.get('moderate_count')}\n")
                f.write(f"  - Severe         : {summary.get('severe_count')}\n")
                f.write(f"Average Confidence : {summary.get('average_confidence')}\n")
                f.write(f"Average Area %     : {summary.get('average_size_pct')}%\n")
                f.write(f"Processing Time    : {summary.get('processing_time_ms')} ms\n")
                if summary.get('largest_pothole'):
                    lg = summary['largest_pothole']
                    f.write(f"Largest Pothole    : Width={lg.get('width_cm')}cm, Height={lg.get('height_cm')}cm\n")
            else:
                f.write(f"Total Frames       : {summary.get('total_frames')}\n")
                f.write(f"Average FPS        : {summary.get('average_fps')}\n")
                f.write(f"Total Detections   : {summary.get('total_detections')}\n")
                f.write(f"Avg Potholes/Frame : {summary.get('average_potholes_per_frame')}\n")
                f.write(f"Max Potholes/Frame : {summary.get('max_potholes_in_one_frame')}\n")
                f.write(f"  - Minor Total    : {summary.get('minor_count')}\n")
                f.write(f"  - Moderate Total : {summary.get('moderate_count')}\n")
                f.write(f"  - Severe Total   : {summary.get('severe_count')}\n")
                f.write(f"Worst Severity Seen: {summary.get('highest_severity_encountered')}\n")
                f.write(f"Average Proc Time  : {summary.get('average_processing_time_ms')} ms\n")
                f.write(f"Total Time Elapsed : {summary.get('total_elapsed_seconds')} seconds\n")
                
            f.write("="*60 + "\n")
            f.write("Generated automatically by Antigravity Road Severity Engine\n")

# ─────────────────────────────────────────────────────────────────
#  4. VISUALIZER OVERLAYS
# ─────────────────────────────────────────────────────────────────

class Visualizer:
    """
    Renders bounding boxes, counters, panels, and alert banners onto the frame.
    """
    @staticmethod
    def render(frame, detections, processing_time_ms, overall_condition, fps=None):
        """
        Performs all drawing overlays on the frame.
        """
        img_h, img_w = frame.shape[:2]
        
        # 1. Draw each bounding box & label chip
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            conf = det['confidence']
            severity = det['severity']
            cfg = SEVERITY_CONFIG[severity]
            track_id = det.get('track_id')
            
            # Box color and thickness
            color = cfg['color']
            thickness = 2 + severity # 2px for Minor, 3px Mod, 4px Severe
            
            # Draw bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
            
            # Build labeling string
            lbl = ""
            if track_id is not None:
                lbl += f"#{track_id} "
            lbl += f"{cfg['label']} ({conf:.2f})"
            if det['width_cm'] is not None:
                lbl += f" {int(det['width_cm'])}x{int(det['height_cm'])}cm"
            else:
                lbl += f" {det['pct_area']:.2f}%"
                
            # Draw Label Chip directly above the bounding box
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.45
            (tw, th), baseline = cv2.getTextSize(lbl, font, font_scale, 1)
            
            chip_top = max(y1 - th - 10, 0)
            chip_bot = max(y1 - 2, th + 8)
            cv2.rectangle(frame, (x1, chip_top), (x1 + tw + 10, chip_bot), color, -1)
            cv2.putText(frame, lbl, (x1 + 5, chip_bot - 4), font, font_scale, (255, 255, 255), 1, cv2.LINE_AA)
            
        # 2. Draw Top-Left Panel: FPS & Processing Time
        # Background block
        panel_tl_w, panel_tl_h = 190, 55
        overlay_tl = frame.copy()
        cv2.rectangle(overlay_tl, (10, 10), (10 + panel_tl_w, 10 + panel_tl_h), (20, 20, 20), -1)
        cv2.addWeighted(overlay_tl, 0.65, frame, 0.35, 0, frame)
        
        # Text details
        fps_text = f"FPS: {fps:.1f}" if fps is not None else "FPS: N/A"
        time_text = f"Proc Time: {processing_time_ms:.1f}ms"
        cv2.putText(frame, fps_text, (18, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (230, 230, 230), 1, cv2.LINE_AA)
        cv2.putText(frame, time_text, (18, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (230, 230, 230), 1, cv2.LINE_AA)
        
        # 3. Draw Top-Right Panel: Severity Counts Summary
        counts = Counter([d['severity'] for d in detections])
        panel_tr_w, panel_tr_h = 240, 100
        x0_tr = img_w - panel_tr_w - 10
        
        overlay_tr = frame.copy()
        cv2.rectangle(overlay_tr, (x0_tr, 10), (x0_tr + panel_tr_w, 10 + panel_tr_h), (20, 20, 20), -1)
        cv2.addWeighted(overlay_tr, 0.65, frame, 0.35, 0, frame)
        
        # Counter lines
        cv2.putText(frame, "DETECTION SUMMARY", (x0_tr + 10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 160, 160), 1, cv2.LINE_AA)
        
        for i, level in enumerate(sorted(SEVERITY_CONFIG)):
            count = counts.get(level, 0)
            cfg = SEVERITY_CONFIG[level]
            lbl_color = cfg['color'] if count > 0 else (100, 100, 100)
            line = f"{cfg['label']:<10s} : {count}"
            cv2.putText(frame, line, (x0_tr + 10, 48 + i * 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, lbl_color, 1, cv2.LINE_AA)
            
        cv2.putText(frame, f"Total Potholes: {len(detections)}", (x0_tr + 10, 98), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 200, 200), 1, cv2.LINE_AA)
        
        # 4. Draw Bottom Banner: Overall Alert message
        ban_h = 42
        y_top = img_h - ban_h
        
        # Draw full width semi-transparent banner
        overlay_ban = frame.copy()
        cv2.rectangle(overlay_ban, (0, y_top), (img_w, img_h), overall_condition['bg_color'], -1)
        cv2.addWeighted(overlay_ban, 0.75, frame, 0.25, 0, frame)
        
        # Overlay warning text
        alert_msg = f"{overall_condition['tag']} {overall_condition['alert']}"
        cv2.putText(frame, alert_msg, (15, img_h - 13), cv2.FONT_HERSHEY_SIMPLEX, 0.68, overall_condition['color'], 2, cv2.LINE_AA)
        
        # Flashing indicator circle for SEVERE warnings
        if overall_condition['level'] == 2:
            if int(time.time() * 2) % 2 == 0: # 1Hz flashing
                cv2.circle(frame, (img_w - 20, y_top + ban_h // 2), 8, overall_condition['color'], -1)
                
        return frame
