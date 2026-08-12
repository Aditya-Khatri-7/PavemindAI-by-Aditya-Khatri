import os
import json
import time
from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")  # Set in backend/.env — never hardcode credentials

# Configuration for local fallback
BASE_DIR = Path(__file__).resolve().parent
LOCAL_DATA_DIR = BASE_DIR / "static" / "local_db"
LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOCAL_SCANS_FILE = LOCAL_DATA_DIR / "scans.json"

if not LOCAL_SCANS_FILE.exists():
    with open(LOCAL_SCANS_FILE, "w") as f:
        json.dump([], f)

client = None
db = None
scans_col = None
detections_col = None
db_connected = False

last_connection_attempt = 0.0
last_ping_time = 0.0
CONNECTION_RETRY_COOLDOWN = 30.0  # seconds to wait before retrying to connect if down
PING_INTERVAL = 5.0  # seconds to cache a successful ping status

def try_mongodb_connect():
    global client, db, scans_col, detections_col, db_connected, last_connection_attempt, last_ping_time
    last_connection_attempt = time.time()
    try:
        print(f"Connecting to MongoDB Atlas at URI (length={len(MONGODB_URI)})...")
        # Set selection and connection timeouts to 2000ms for faster fallback with TLS bypass if needed
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000, connectTimeoutMS=2000, tlsAllowInvalidCertificates=True)
        client.admin.command('ping')
        db = client["pothole_detection_db"]
        scans_col = db["scans"]
        detections_col = db["detections"]
        db_connected = True
        last_ping_time = time.time()
        print("MongoDB Atlas: Connected and verified successfully!")
        return True
    except Exception as e:
        print(f"MongoDB Atlas connection failed: {e}")
        print(">>> System is running in LOCAL FALLBACK mode (JSON-based storage).")
        db_connected = False
        return False

# Initial connection attempt
try_mongodb_connect()

def test_db_connection():
    global db_connected, last_ping_time
    now = time.time()
    if db_connected:
        if now - last_ping_time < PING_INTERVAL:
            return True
        try:
            client.admin.command('ping')
            last_ping_time = now
            return True
        except Exception:
            db_connected = False
            return False
    else:
        # If connection is down, respect cooldown
        if now - last_connection_attempt > CONNECTION_RETRY_COOLDOWN:
            return try_mongodb_connect()
        return False


# --- LOCAL STORE HELPERS (Fallback) ---
def _load_local_scans():
    with open(LOCAL_SCANS_FILE, "r") as f:
        return json.load(f)

def _save_local_scans(scans):
    with open(LOCAL_SCANS_FILE, "w") as f:
        json.dump(scans, f, indent=4)

def _get_detections_file(scan_id):
    return LOCAL_DATA_DIR / f"detections_{scan_id}.json"

def _load_local_detections():
    all_detections = []
    for filepath in LOCAL_DATA_DIR.glob("detections_*.json"):
        try:
            with open(filepath, "r") as f:
                all_detections.extend(json.load(f))
        except Exception:
            pass
    return all_detections

def _save_local_detections(detections):
    # Group detections by scan_id
    by_scan = {}
    for det in detections:
        scan_id = det.get("scan_id")
        if scan_id:
            by_scan.setdefault(scan_id, []).append(det)
            
    # Write updated files
    for scan_id, det_list in by_scan.items():
        with open(_get_detections_file(scan_id), "w") as f:
            json.dump(det_list, f, indent=4)
            
    # Delete files that are no longer in by_scan
    active_ids = set(by_scan.keys())
    for filepath in LOCAL_DATA_DIR.glob("detections_*.json"):
        scan_id = filepath.name.replace("detections_", "").replace(".json", "")
        if scan_id not in active_ids:
            try:
                filepath.unlink()
            except Exception:
                pass

# --- PUBLIC INTERFACE ---
def save_scan_summary(scan_data):
    """
    Saves a summary of the scan. Returns the scan ID string.
    """
    if "date" not in scan_data:
        scan_data["date"] = datetime.utcnow()
        
    if db_connected:
        result = scans_col.insert_one(scan_data)
        return str(result.inserted_id)
    else:
        scans = _load_local_scans()
        scan_id = str(ObjectId())
        
        serialized_data = {**scan_data}
        serialized_data["_id"] = scan_id
        if isinstance(serialized_data["date"], datetime):
            serialized_data["date"] = serialized_data["date"].isoformat()
            
        scans.append(serialized_data)
        _save_local_scans(scans)
        return scan_id

def save_detections(scan_id, detections_list):
    """
    Saves multiple individual pothole detections linked to a scan ID.
    """
    if db_connected:
        # Use copies so we don't pollute the caller's dicts with ObjectId fields
        docs = [{**det, "scan_id": ObjectId(scan_id)} for det in detections_list]
        if docs:
            detections_col.insert_many(docs)
    else:
        file_path = _get_detections_file(scan_id)
        serialized_list = []
        for det in detections_list:
            det_copy = {**det}
            det_copy["_id"] = str(ObjectId())
            det_copy["scan_id"] = scan_id
            serialized_list.append(det_copy)
        with open(file_path, "w") as f:
            json.dump(serialized_list, f, indent=4)
