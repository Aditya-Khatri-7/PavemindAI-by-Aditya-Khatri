import os
import sys
import shutil
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import mimetypes
mimetypes.init()
mimetypes.add_type("video/mp4", ".mp4")
import cv2
import numpy as np
import imageio
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from ultralytics import YOLO

# Add parent path to sys path to import pothole_analyzer
subfolder_path = Path(__file__).parent.parent / 'Pothole-detection'
sys.path.append(str(subfolder_path))

from pothole_analyzer import SeverityEngine, AlertSystem, Visualizer
from database import (
    scans_col, 
    detections_col, 
    save_scan_summary, 
    save_detections, 
    test_db_connection, 
    _load_local_scans,
    _save_local_scans,
    _load_local_detections,
    _save_local_detections
)

# Load configurations
load_dotenv()

app = FastAPI(title="Road Pothole Severity Engine API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories config
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = STATIC_DIR / "uploads"
OUTPUT_DIR = STATIC_DIR / "outputs"
REPORTS_DIR = STATIC_DIR / "reports"

for dir_path in [UPLOAD_DIR, OUTPUT_DIR, REPORTS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

def resolve_static_path(url: str) -> Path:
    if not url:
        return Path()
    clean_url = url.lstrip("/")
    if clean_url.startswith("static/"):
        relative_part = clean_url.replace("static/", "", 1)
        return STATIC_DIR / relative_part
    return BASE_DIR / clean_url


# Load YOLO model
MODEL_PATH = os.getenv("MODEL_PATH", "../Pothole-detection/runs/detect/yolov12n_pothole_detector5/weights/best.pt")
model_path_obj = Path(MODEL_PATH)
if not model_path_obj.is_absolute():
    MODEL_PATH = str((BASE_DIR / model_path_obj).resolve())
print(f"Loading YOLO model from: {MODEL_PATH}")
try:
    model = YOLO(MODEL_PATH)
    print("YOLO Model loaded successfully!")
except Exception as e:
    print(f"Error loading model weights: {e}")
    model = None

# Severity Configuration mappings for DB output
SEVERITY_LABELS = {0: "MINOR", 1: "MODERATE", 2: "SEVERE"}

# Health score calculator
def calculate_road_health(minor_count, moderate_count, severe_count):
    # Steeper deductions: severe=-25, moderate=-10, minor=-4
    score = 100 - (25 * severe_count + 10 * moderate_count + 4 * minor_count)
    return max(0, min(100, score))


# ─── VIDEO PROCESSING TASK ───
def process_video_background(scan_id: str, input_path: str, output_name: str, lat: Optional[float], lon: Optional[float]):
    try:
        if test_db_connection():
            scans_col.update_one({"_id": ObjectId(scan_id)}, {"$set": {"status": "processing", "progress": 0}})
        else:
            scans = _load_local_scans()
            for s in scans:
                if s["_id"] == scan_id:
                    s["status"] = "processing"
                    s["progress"] = 0
            _save_local_scans(scans)
            
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise IOError(f"Could not open video file: {input_path}")
            
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        fps_in = cap.get(cv2.CAP_PROP_FPS) or 25.0
        w_in = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h_in = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        output_file_path = OUTPUT_DIR / f"processed_{output_name}"
        # Use imageio FFMPEG writer to output browser-playable H.264 MP4 with libx264 codec
        writer = imageio.get_writer(
            str(output_file_path), 
            fps=fps_in, 
            codec='libx264', 
            pixelformat='yuv420p', 
            macro_block_size=None
        )
        
        # Initialize severity engine
        severity_engine = SeverityEngine()
        
        frame_idx = 0
        severity_counts = {0: 0, 1: 0, 2: 0}
        processing_times = []
        
        detections_to_save = []
        
        # Keep track of unique pothole IDs to avoid double-counting
        unique_potholes = set()
        
        t_start = time.time()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            t0 = time.time()
            
            # Use model.track() to enable tracking across frames
            results = model.track(frame, persist=True, tracker="bytetrack.yaml", conf=0.15, verbose=False)
            proc_time_ms = (time.time() - t0) * 1000
            processing_times.append(proc_time_ms)
            
            detections = []
            frame_severity_counts = {}
            
            # Process detections in current frame
            if results and results[0].boxes is not None:
                for box in results[0].boxes:
                    det = severity_engine.analyze_pothole(box, w_in, h_in)
                    if det is None:
                        continue
                    track_id = det.get('track_id')
                    
                    # Track unique potholes encountered in this video run
                    if track_id is not None:
                        unique_potholes.add(track_id)
                        
                    # Save every raw detection frame-by-frame
                    det_data = {
                        "frame": frame_idx,
                        "track_id": track_id,
                        "severity": SEVERITY_LABELS[det['severity']],
                        "width_cm": det['width_cm'],
                        "height_cm": det['height_cm'],
                        "confidence": float(det['confidence']),
                        "bbox": [int(x) for x in det['bbox']],
                        "distance_m": det['distance_m'],
                        "x": int((det['bbox'][0] + det['bbox'][2]) / 2),
                        "y": int((det['bbox'][1] + det['bbox'][3]) / 2),
                        "lat": lat + (frame_idx * 0.000005) if lat else None, # simulated forward trajectory
                        "lon": lon + (frame_idx * 0.000005) if lon else None
                    }
                    detections_to_save.append(det_data)
                    detections.append(det)
                    
                    sev = det['severity']
                    severity_counts[sev] = severity_counts.get(sev, 0) + 1
                    frame_severity_counts[sev] = frame_severity_counts.get(sev, 0) + 1
            
            overall_cond = AlertSystem.get_overall_road_condition(frame_severity_counts)
            
            # Draw overlay on video frame
            fps_current = 1000.0 / max(proc_time_ms, 1.0)
            annotated_frame = Visualizer.render(frame, detections, proc_time_ms, overall_cond, fps=fps_current)
            # Convert BGR (OpenCV) to RGB (imageio)
            rgb_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            writer.append_data(rgb_frame)
            
            frame_idx += 1
            if frame_idx % 10 == 0:
                progress_pct = int((frame_idx / total_frames) * 100)
                if test_db_connection():
                    scans_col.update_one({"_id": ObjectId(scan_id)}, {"$set": {"progress": progress_pct}})
                else:
                    scans = _load_local_scans()
                    for s in scans:
                        if s["_id"] == scan_id:
                            s["progress"] = progress_pct
                    _save_local_scans(scans)
                
        cap.release()
        writer.close()
        
        # Verify the generated video file
        if not output_file_path.exists() or output_file_path.stat().st_size == 0:
            raise Exception("Processed video file was not created or is empty.")
            
        test_cap = cv2.VideoCapture(str(output_file_path))
        if not test_cap.isOpened():
            test_cap.release()
            raise Exception("Processed video file is corrupted or unplayable by OpenCV.")
        test_cap.release()
        
        # Calculate summary statistics
        elapsed_sec = time.time() - t_start
        avg_fps = round(frame_idx / max(elapsed_sec, 0.1), 2)
        avg_proc_time = round(float(np.mean(processing_times)), 2) if processing_times else 0.0
        
        # Count unique pothole severities
        # To do this correctly, we can aggregate by track_id
        unique_minor = 0
        unique_moderate = 0
        unique_severe = 0
        
        track_severities = {}
        for d in detections_to_save:
            tid = d.get('track_id')
            if tid is not None:
                # keep track of the maximum severity encountered for this track ID
                sev = d['severity']
                if tid not in track_severities:
                    track_severities[tid] = sev
                else:
                    # Upgrade severity if we saw a worse version
                    if sev == "SEVERE" or (sev == "MODERATE" and track_severities[tid] == "MINOR"):
                        track_severities[tid] = sev
            else:
                # non-tracked potholes (fallback): increment counts directly
                if d['severity'] == "MINOR":
                    unique_minor += 1
                elif d['severity'] == "MODERATE":
                    unique_moderate += 1
                elif d['severity'] == "SEVERE":
                    unique_severe += 1
                    
        for tid, sev in track_severities.items():
            if sev == "MINOR":
                unique_minor += 1
            elif sev == "MODERATE":
                unique_moderate += 1
            elif sev == "SEVERE":
                unique_severe += 1
                
        unique_total = unique_minor + unique_moderate + unique_severe
        health_score = calculate_road_health(unique_minor, unique_moderate, unique_severe)
        
        # Update database with complete results
        if test_db_connection():
            scans_col.update_one(
                {"_id": ObjectId(scan_id)},
                {"$set": {
                    "status": "completed",
                    "progress": 100,
                    "total_potholes": unique_total,
                    "minor": unique_minor,
                    "moderate": unique_moderate,
                    "severe": unique_severe,
                    "avg_fps": avg_fps,
                    "avg_processing_time_ms": avg_proc_time,
                    "road_health_score": health_score,
                    "output_video_url": f"/static/outputs/processed_{output_name}"
                }}
            )
        else:
            scans = _load_local_scans()
            for s in scans:
                if s["_id"] == scan_id:
                    s["status"] = "completed"
                    s["progress"] = 100
                    s["total_potholes"] = unique_total
                    s["minor"] = unique_minor
                    s["moderate"] = unique_moderate
                    s["severe"] = unique_severe
                    s["avg_fps"] = avg_fps
                    s["avg_processing_time_ms"] = avg_proc_time
                    s["road_health_score"] = health_score
                    s["output_video_url"] = f"/static/outputs/processed_{output_name}"
            _save_local_scans(scans)
        
        # Save individual detections
        save_detections(scan_id, detections_to_save)
        print(f"Background video scan {scan_id} completed successfully!")
        
    except Exception as e:
        print(f"Error in video background task: {e}")
        if test_db_connection():
            scans_col.update_one(
                {"_id": ObjectId(scan_id)},
                {"$set": {"status": "failed", "error_message": str(e)}}
            )
        else:
            scans = _load_local_scans()
            for s in scans:
                if s["_id"] == scan_id:
                    s["status"] = "failed"
                    s["error_message"] = str(e)
            _save_local_scans(scans)


# ─── REST ENDPOINTS ───

@app.post("/api/upload/image")
async def upload_image(files: List[UploadFile] = File(...), lat: Optional[float] = Form(None), lon: Optional[float] = Form(None)):
    if not model:
        raise HTTPException(status_code=500, detail="YOLO Model not initialized.")
        
    results_list = []
    
    for file in files:
        # Save original file
        file_ext = Path(file.filename).suffix
        unique_name = f"img_{int(time.time())}_{file.filename}"
        input_file_path = UPLOAD_DIR / unique_name
        
        with open(input_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Process image
        img = cv2.imread(str(input_file_path))
        if img is None:
            try:
                from PIL import Image
                import numpy as np
                pil_img = Image.open(input_file_path).convert("RGB")
                img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            except Exception as e:
                print(f"[ERROR] Failed to read image using PIL fallback: {e}")
                continue

            
        img_h, img_w = img.shape[:2]
        
        t0 = time.time()
        results = model(img, conf=0.15, verbose=False)[0]
        proc_time_ms = (time.time() - t0) * 1000
        
        print(f"[DEBUG UPLOAD] Image resolution: {img_w}x{img_h}")
        print(f"[DEBUG UPLOAD] Detected {len(results.boxes)} raw boxes.")
        
        severity_engine = SeverityEngine()
        detections = []
        severity_counts = {0: 0, 1: 0, 2: 0}
        detections_to_save = []
        
        if results.boxes is not None:
            for box in results.boxes:
                det = severity_engine.analyze_pothole(box, img_w, img_h)
                if det is None:
                    continue
                detections.append(det)
                
                sev = det['severity']
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
                
                # Bbox center coordinates
                det_data = {
                    "frame": 0,
                    "track_id": None,
                    "severity": SEVERITY_LABELS[sev],
                    "width_cm": det['width_cm'],
                    "height_cm": det['height_cm'],
                    "confidence": float(det['confidence']),
                    "bbox": [int(x) for x in det['bbox']],
                    "distance_m": det['distance_m'],
                    "x": int((det['bbox'][0] + det['bbox'][2]) / 2),
                    "y": int((det['bbox'][1] + det['bbox'][3]) / 2),
                    "lat": lat,
                    "lon": lon
                }
                detections_to_save.append(det_data)
                
        overall_cond = AlertSystem.get_overall_road_condition(severity_counts)
        
        # Render annotated overlay
        annotated_img = Visualizer.render(img.copy(), detections, proc_time_ms, overall_cond)
        output_name = Path(unique_name).with_suffix(".jpg").name
        output_file_path = OUTPUT_DIR / f"severity_{output_name}"
        cv2.imwrite(str(output_file_path), annotated_img)
        
        # Save scan details to database
        total_potholes = len(detections)
        minor_cnt = severity_counts[0]
        mod_cnt = severity_counts[1]
        sev_cnt = severity_counts[2]
        health_score = calculate_road_health(minor_cnt, mod_cnt, sev_cnt)
        
        scan_id = save_scan_summary({
            "scan_type": "image",
            "scan_name": file.filename,
            "date": datetime.utcnow(),
            "total_potholes": total_potholes,
            "minor": minor_cnt,
            "moderate": mod_cnt,
            "severe": sev_cnt,
            "avg_fps": 0.0,
            "road_health_score": health_score,
            "input_url": f"/static/uploads/{unique_name}",
            "output_url": f"/static/outputs/severity_{output_name}"
        })
        
        save_detections(scan_id, detections_to_save)
        
        results_list.append({
            "scan_id": scan_id,
            "scan_name": file.filename,
            "total_potholes": total_potholes,
            "minor": minor_cnt,
            "moderate": mod_cnt,
            "severe": sev_cnt,
            "road_health_score": health_score,
            "input_url": f"/static/uploads/{unique_name}",
            "output_url": f"/static/outputs/severity_{output_name}",
            "detections": detections_to_save
        })
        
    return results_list


@app.post("/api/upload/video")
async def upload_video(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    lat: Optional[float] = Form(None), 
    lon: Optional[float] = Form(None)
):
    if not model:
        raise HTTPException(status_code=500, detail="YOLO Model not initialized.")
        
    # Save input video file
    unique_name = f"vid_{int(time.time())}_{file.filename}"
    input_file_path = UPLOAD_DIR / unique_name
    
    with open(input_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Create scan record in database (pending state)
    scan_id = save_scan_summary({
        "scan_type": "video",
        "scan_name": file.filename,
        "date": datetime.utcnow(),
        "total_potholes": 0,
        "minor": 0,
        "moderate": 0,
        "severe": 0,
        "avg_fps": 0.0,
        "road_health_score": 100,
        "input_video_url": f"/static/uploads/{unique_name}",
        "status": "queued",
        "progress": 0,
        "lat": lat,
        "lon": lon
    })
    
    # Launch video frame-by-frame processing in background
    background_tasks.add_task(
        process_video_background, 
        scan_id, 
        str(input_file_path), 
        unique_name, 
        lat, 
        lon
    )
    
    return {"scan_id": scan_id, "status": "queued", "message": "Video uploaded. Processing started in background."}


@app.get("/api/scans")
async def get_scans(type: Optional[str] = None):
    if test_db_connection():
        query = {}
        if type:
            query["scan_type"] = type
            
        cursor = scans_col.find(query).sort("date", -1)
        scans_list = []
        
        for scan in cursor:
            scan["_id"] = str(scan["_id"])
            if "date" in scan and isinstance(scan["date"], datetime):
                scan["date"] = scan["date"].isoformat()
            scans_list.append(scan)
            
        return scans_list
    else:
        # Fallback Local JSON query
        scans = _load_local_scans()
        if type:
            scans = [s for s in scans if s["scan_type"] == type]
        # sort reverse date
        scans.sort(key=lambda s: s.get("date", ""), reverse=True)
        return scans


@app.get("/api/scans/{scan_id}")
async def get_scan_details(scan_id: str):
    if test_db_connection():
        if not ObjectId.is_valid(scan_id):
            raise HTTPException(status_code=400, detail="Invalid Scan ID format.")
            
        scan = scans_col.find_one({"_id": ObjectId(scan_id)})
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found.")
            
        scan["_id"] = str(scan["_id"])
        if "date" in scan and isinstance(scan["date"], datetime):
            scan["date"] = scan["date"].isoformat()
            
        # Get associated detections
        cursor = detections_col.find({"scan_id": ObjectId(scan_id)})
        detections_list = []
        for d in cursor:
            d["_id"] = str(d["_id"])
            d["scan_id"] = str(d["scan_id"])
            detections_list.append(d)
            
        return {"scan": scan, "detections": detections_list}
    else:
        # Fallback Local JSON query
        scans = _load_local_scans()
        scan = None
        for s in scans:
            if s["_id"] == scan_id:
                scan = s
                break
                
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found.")
            
        detections = _load_local_detections()
        detections_list = [d for d in detections if d["scan_id"] == scan_id]
        
        return {"scan": scan, "detections": detections_list}


@app.delete("/api/scans/{scan_id}")
async def delete_scan(scan_id: str):
    # Delete files and database entries
    if test_db_connection():
        if not ObjectId.is_valid(scan_id):
            raise HTTPException(status_code=400, detail="Invalid Scan ID format.")
            
        scan = scans_col.find_one({"_id": ObjectId(scan_id)})
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found.")
            
        # Delete files
        for key in ["input_url", "output_url", "input_video_url", "output_video_url"]:
            if key in scan and scan[key]:
                path = resolve_static_path(scan[key])
                if path.exists():
                    try:
                        path.unlink()
                    except Exception:
                        pass
                        
        scans_col.delete_one({"_id": ObjectId(scan_id)})
        detections_col.delete_many({"scan_id": ObjectId(scan_id)})
    else:
        # Local fallback delete
        scans = _load_local_scans()
        scan = None
        for s in scans:
            if s["_id"] == scan_id:
                scan = s
                break
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found.")
            
        # Delete files
        for key in ["input_url", "output_url", "input_video_url", "output_video_url"]:
            if key in scan and scan[key]:
                path = resolve_static_path(scan[key])
                if path.exists():
                    try:
                        path.unlink()
                    except Exception:
                        pass
                        
        scans = [s for s in scans if s["_id"] != scan_id]
        _save_local_scans(scans)
        
        detections = _load_local_detections()
        detections = [d for d in detections if d["scan_id"] != scan_id]
        _save_local_detections(detections)
        
    return {"status": "deleted", "scan_id": scan_id}


@app.post("/api/scans/{scan_id}/rerun")
async def rerun_scan(scan_id: str, background_tasks: BackgroundTasks):
    if test_db_connection():
        if not ObjectId.is_valid(scan_id):
            raise HTTPException(status_code=400, detail="Invalid Scan ID format.")
        scan = scans_col.find_one({"_id": ObjectId(scan_id)})
    else:
        scans = _load_local_scans()
        scan = next((s for s in scans if s["_id"] == scan_id), None)
        
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found.")
        
    scan_type = scan.get("scan_type")
    if scan_type not in ["video", "image"]:
        raise HTTPException(status_code=400, detail="Rerun is only supported for video and image scans.")
        
    if scan_type == "video":
        input_video_url = scan.get("input_video_url")
        if not input_video_url:
            raise HTTPException(status_code=400, detail="Input video URL is missing.")
            
        input_file_path = resolve_static_path(input_video_url)
        if not input_file_path.exists():
            raise HTTPException(status_code=400, detail="Input video file no longer exists on the server.")
            
        unique_name = input_file_path.name
        
        if test_db_connection():
            # Delete any previous detections for this scan to avoid duplicates on rerun
            detections_col.delete_many({"scan_id": ObjectId(scan_id)})
            scans_col.update_one(
                {"_id": ObjectId(scan_id)},
                {"$set": {
                    "status": "queued",
                    "progress": 0,
                    "total_potholes": 0,
                    "minor": 0,
                    "moderate": 0,
                    "severe": 0,
                    "avg_fps": 0.0,
                    "road_health_score": 100
                }}
            )
        else:
            scans = _load_local_scans()
            for s in scans:
                if s["_id"] == scan_id:
                    s["status"] = "queued"
                    s["progress"] = 0
                    s["total_potholes"] = 0
                    s["minor"] = 0
                    s["moderate"] = 0
                    s["severe"] = 0
                    s["avg_fps"] = 0.0
                    s["road_health_score"] = 100
            _save_local_scans(scans)
            
        background_tasks.add_task(
            process_video_background, 
            scan_id, 
            str(input_file_path), 
            unique_name, 
            scan.get("lat"), 
            scan.get("lon")
        )
        
        return {"scan_id": scan_id, "status": "queued", "scan_type": "video", "message": "Video scan reprocessing started in background."}
        
    else:  # scan_type == "image"
        input_url = scan.get("input_url")
        if not input_url:
            raise HTTPException(status_code=400, detail="Input image URL is missing.")
            
        input_file_path = resolve_static_path(input_url)
        if not input_file_path.exists():
            raise HTTPException(status_code=400, detail="Input image file no longer exists on the server.")
            
        # Process image using model
        img = cv2.imread(str(input_file_path))
        if img is None:
            try:
                from PIL import Image
                import numpy as np
                pil_img = Image.open(input_file_path).convert("RGB")
                img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            except Exception as e:
                print(f"[ERROR] Failed to read image using PIL fallback in rerun: {e}")
                raise HTTPException(status_code=400, detail=f"Could not read the input image file: {e}")
            
        img_h, img_w = img.shape[:2]
        
        t0 = time.time()
        results = model(img, conf=0.15, verbose=False)[0]
        proc_time_ms = (time.time() - t0) * 1000
        
        print(f"[DEBUG RERUN] Image resolution: {img_w}x{img_h}")
        print(f"[DEBUG RERUN] Detected {len(results.boxes)} raw boxes.")
        
        severity_engine = SeverityEngine()
        detections = []
        severity_counts = {0: 0, 1: 0, 2: 0}
        detections_to_save = []
        
        if results.boxes is not None:
            for box in results.boxes:
                det = severity_engine.analyze_pothole(box, img_w, img_h)
                if det is None:
                    continue
                detections.append(det)
                
                sev = det['severity']
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
                
                det_data = {
                    "frame": 0,
                    "track_id": None,
                    "severity": SEVERITY_LABELS[sev],
                    "width_cm": det['width_cm'],
                    "height_cm": det['height_cm'],
                    "confidence": float(det['confidence']),
                    "bbox": [int(x) for x in det['bbox']],
                    "distance_m": det['distance_m'],
                    "x": int((det['bbox'][0] + det['bbox'][2]) / 2),
                    "y": int((det['bbox'][1] + det['bbox'][3]) / 2),
                    "lat": scan.get("lat"),
                    "lon": scan.get("lon")
                }
                detections_to_save.append(det_data)
                
        overall_cond = AlertSystem.get_overall_road_condition(severity_counts)
        
        # Render annotated overlay
        annotated_img = Visualizer.render(img.copy(), detections, proc_time_ms, overall_cond)
        output_url = scan.get("output_url")
        if not output_url:
            output_url = f"/static/outputs/severity_{input_file_path.name}"
            
        # Ensure the output url has a .jpg suffix for OpenCV saving support
        output_url_path = Path(output_url)
        if output_url_path.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
            output_url = str(output_url_path.with_suffix(".jpg")).replace("\\", "/")
            
        output_file_path = resolve_static_path(output_url)
        cv2.imwrite(str(output_file_path), annotated_img)
        
        total_potholes = len(detections)
        minor_cnt = severity_counts[0]
        mod_cnt = severity_counts[1]
        sev_cnt = severity_counts[2]
        health_score = calculate_road_health(minor_cnt, mod_cnt, sev_cnt)
        
        # Save scan details to database (overwriting instead of inserting new)
        if test_db_connection():
            detections_col.delete_many({"scan_id": ObjectId(scan_id)})
            scans_col.update_one(
                {"_id": ObjectId(scan_id)},
                {"$set": {
                    "total_potholes": total_potholes,
                    "minor": minor_cnt,
                    "moderate": mod_cnt,
                    "severe": sev_cnt,
                    "road_health_score": health_score,
                    "output_url": output_url,
                    "date": datetime.utcnow()
                }}
            )
        else:
            scans = _load_local_scans()
            for s in scans:
                if s["_id"] == scan_id:
                    s["total_potholes"] = total_potholes
                    s["minor"] = minor_cnt
                    s["moderate"] = mod_cnt
                    s["severe"] = sev_cnt
                    s["road_health_score"] = health_score
                    s["output_url"] = output_url
                    s["date"] = datetime.utcnow().isoformat()
            _save_local_scans(scans)
            
        save_detections(scan_id, detections_to_save)
        
        updated_scan = {
            "_id": scan_id,
            "scan_type": "image",
            "scan_name": scan.get("scan_name"),
            "date": datetime.utcnow().isoformat(),
            "total_potholes": total_potholes,
            "minor": minor_cnt,
            "moderate": mod_cnt,
            "severe": sev_cnt,
            "road_health_score": health_score,
            "input_url": scan.get("input_url"),
            "output_url": output_url,
            "detections": detections_to_save
        }
        
        return {"status": "completed", "scan_type": "image", "data": updated_scan}


@app.get("/api/analytics")
async def get_analytics():
    if test_db_connection():
        total_scans = scans_col.count_documents({})
        
        pipeline = [
            {"$group": {
                "_id": None,
                "total_minor": {"$sum": "$minor"},
                "total_moderate": {"$sum": "$moderate"},
                "total_severe": {"$sum": "$severe"},
                "avg_health_score": {"$avg": "$road_health_score"}
            }}
        ]
        
        aggregates = list(scans_col.aggregate(pipeline))
        
        if aggregates:
            agg = aggregates[0]
            minor = agg.get("total_minor", 0)
            moderate = agg.get("total_moderate", 0)
            severe = agg.get("total_severe", 0)
            avg_health = round(agg.get("avg_health_score", 100), 2)
        else:
            minor = moderate = severe = 0
            avg_health = 100
            
        total_potholes = minor + moderate + severe
        
        coords_cursor = detections_col.find(
            {"lat": {"$ne": None}, "lon": {"$ne": None}},
            {"lat": 1, "lon": 1, "severity": 1, "width_cm": 1, "confidence": 1, "scan_id": 1}
        )
        
        pothole_coordinates = []
        for c in coords_cursor:
            pothole_coordinates.append({
                "lat": c["lat"],
                "lon": c["lon"],
                "severity": c["severity"],
                "width_cm": c.get("width_cm", 0),
                "confidence": c.get("confidence", 0),
                "scan_id": str(c["scan_id"])
            })
            
        trends_cursor = scans_col.find(
            {}, 
            {"date": 1, "minor": 1, "moderate": 1, "severe": 1, "scan_name": 1}
        ).sort("date", -1).limit(10)
        
        trends = []
        for t in trends_cursor:
            trends.append({
                "name": t.get("scan_name", "Scan"),
                "date": t["date"].strftime("%d %b %H:%M") if "date" in t else "N/A",
                "minor": t.get("minor", 0),
                "moderate": t.get("moderate", 0),
                "severe": t.get("severe", 0)
            })
        trends.reverse()
        
    else:
        # Fallback Local JSON aggregations
        scans = _load_local_scans()
        detections = _load_local_detections()
        
        total_scans = len(scans)
        minor = sum(s.get("minor", 0) for s in scans)
        moderate = sum(s.get("moderate", 0) for s in scans)
        severe = sum(s.get("severe", 0) for s in scans)
        total_potholes = minor + moderate + severe
        
        avg_health = np.mean([s.get("road_health_score", 100) for s in scans]) if scans else 100
        avg_health = round(float(avg_health), 2)
        
        pothole_coordinates = []
        for d in detections:
            if d.get("lat") is not None and d.get("lon") is not None:
                pothole_coordinates.append({
                    "lat": d["lat"],
                    "lon": d["lon"],
                    "severity": d["severity"],
                    "width_cm": d.get("width_cm", 0),
                    "confidence": d.get("confidence", 0),
                    "scan_id": d["scan_id"]
                })
                
        trends = []
        for s in scans[-10:]:
            trends.append({
                "name": s.get("scan_name", "Scan"),
                "date": s.get("date", "")[:16].replace("T", " "),
                "minor": s.get("minor", 0),
                "moderate": s.get("moderate", 0),
                "severe": s.get("severe", 0)
            })
            
    return {
        "total_scans": total_scans,
        "total_potholes": total_potholes,
        "minor": minor,
        "moderate": moderate,
        "severe": severe,
        "avg_health_score": avg_health,
        "coordinates": pothole_coordinates,
        "trends": trends,
        "db_connected": test_db_connection()
    }


@app.get("/api/download/{scan_id}")
async def download_scan_reports(scan_id: str):
    if test_db_connection():
        if not ObjectId.is_valid(scan_id):
            raise HTTPException(status_code=400, detail="Invalid Scan ID format.")
            
        scan = scans_col.find_one({"_id": ObjectId(scan_id)})
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found.")
            
        cursor = detections_col.find({"scan_id": ObjectId(scan_id)})
        detections_list = list(cursor)
    else:
        scans = _load_local_scans()
        scan = None
        for s in scans:
            if s["_id"] == scan_id:
                scan = s
                break
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found.")
            
        detections = _load_local_detections()
        detections_list = [d for d in detections if d["scan_id"] == scan_id]
        
    # Generate CSV
    csv_filename = f"scan_{scan_id}_telemetry.csv"
    csv_filepath = REPORTS_DIR / csv_filename
    
    import csv
    with open(csv_filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['frame', 'track_id', 'severity', 'width_cm', 'height_cm', 'confidence', 'x', 'y', 'distance_m', 'lat', 'lon'])
        for det in detections_list:
            writer.writerow([
                det.get('frame', 0),
                det.get('track_id', 'N/A'),
                det.get('severity', 'N/A'),
                det.get('width_cm', 0),
                det.get('height_cm', 0),
                det.get('confidence', 0),
                det.get('x', 0),
                det.get('y', 0),
                det.get('distance_m', 0),
                det.get('lat', 'N/A'),
                det.get('lon', 'N/A')
            ])
            
    # Generate JSON
    json_filename = f"scan_{scan_id}_telemetry.json"
    json_filepath = REPORTS_DIR / json_filename
    
    import json
    def json_serializer(o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")
        
    with open(json_filepath, 'w') as f:
        json.dump(detections_list, f, default=json_serializer, indent=4)
        
    # Create ZIP
    zip_filename = f"report_{scan_id}.zip"
    zip_filepath = REPORTS_DIR / zip_filename
    
    with zipfile.ZipFile(zip_filepath, 'w') as zipf:
        zipf.write(csv_filepath, arcname=csv_filename)
        zipf.write(json_filepath, arcname=json_filename)
        
        # Add original/processed files
        for key in ["input_url", "output_url", "input_video_url", "output_video_url"]:
            if key in scan and scan[key]:
                file_path = resolve_static_path(scan[key])
                if file_path.exists():
                    zipf.write(file_path, arcname=file_path.name)
                    
    # Clean up files
    csv_filepath.unlink(missing_ok=True)
    json_filepath.unlink(missing_ok=True)
    
    return FileResponse(
        path=zip_filepath,
        filename=zip_filename,
        media_type="application/zip"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
