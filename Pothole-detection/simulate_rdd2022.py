"""
simulate_rdd2022.py  —  Simulate Raw RDD2022 Dataset for Pipeline Verification
IBM Internship | Group 74 | AIML74 | UPES Dehradun
"""

import shutil
import random
from pathlib import Path

def main():
    print("Simulating raw RDD2022 dataset...")
    
    src_img_dir = Path("data/images")
    src_lbl_dir = Path("data/labels")
    
    raw_img_dir = Path("data/rdd2022_raw/images")
    raw_lbl_dir = Path("data/rdd2022_raw/labels")
    
    raw_img_dir.mkdir(parents=True, exist_ok=True)
    raw_lbl_dir.mkdir(parents=True, exist_ok=True)
    
    # We will copy the first 100 images as our "raw RDD2022 India subset"
    image_files = sorted(list(src_img_dir.glob("*.png")))[:100]
    
    simulated_instances = 0
    non_pothole_instances = 0
    
    for img_file in image_files:
        lbl_file = src_lbl_dir / f"{img_file.stem}.txt"
        
        # Copy image
        shutil.copy(img_file, raw_img_dir / img_file.name)
        
        # Modify and copy label
        if lbl_file.exists():
            lines = lbl_file.read_text().strip().splitlines()
            new_lines = []
            for line in lines:
                parts = line.split()
                if len(parts) >= 5:
                    # In our original dataset, all items are class 0 (pothole).
                    # We map them to class 3 (D40 = pothole in RDD2022) to simulate raw RDD2022 labels.
                    new_lines.append(f"3 {' '.join(parts[1:])}")
                    simulated_instances += 1
                    
                    # Randomly insert a mock non-pothole crack class (class 1 = transverse crack)
                    # to verify that our filter script ignores it
                    if random.random() < 0.25:
                        cx = float(parts[1]) + random.uniform(-0.05, 0.05)
                        cy = float(parts[2]) + random.uniform(-0.05, 0.05)
                        w = float(parts[3]) * 0.5
                        h = float(parts[4]) * 0.5
                        new_lines.append(f"1 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
                        non_pothole_instances += 1
                        
            # Write to raw label directory
            (raw_lbl_dir / lbl_file.name).write_text('\n'.join(new_lines))
            
    print("="*60)
    print(" RAW RDD2022 SIMULATION COMPLETED")
    print("="*60)
    print(f"  Destination Image Folder : {raw_img_dir}")
    print(f"  Destination Label Folder : {raw_lbl_dir}")
    print(f"  Simulated Images         : 100")
    print(f"  Simulated D40 Potholes   : {simulated_instances} (Class 3)")
    print(f"  Simulated D10 Cracks     : {non_pothole_instances} (Class 1 - to be filtered out)")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
