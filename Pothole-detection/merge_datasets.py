"""
merge_datasets.py  —  Merge Kaggle Dataset and Filtered RDD2022 Dataset
IBM Internship | Group 74 | AIML74 | UPES Dehradun
"""

import shutil
import random
from pathlib import Path
from collections import Counter

def read_instance_count(label_path):
    if not label_path.exists():
        return 0
    lines = label_path.read_text().strip().splitlines()
    count = 0
    for line in lines:
        parts = line.split()
        if len(parts) >= 5 and int(parts[0]) == 0:
            count += 1
    return count

def main():
    print("Starting dataset merge...")
    
    # Paths
    kaggle_img_dir = Path("data/images")
    kaggle_lbl_dir = Path("data/labels")
    
    rdd_img_dir = Path("data/rdd2022_raw/images")
    rdd_lbl_dir = Path("data/rdd2022_filtered/labels")
    
    merged_root = Path("data_merged")
    
    # Subdirectories for splits
    splits = ['train', 'val', 'test']
    for split in splits:
        (merged_root / "images" / split).mkdir(parents=True, exist_ok=True)
        (merged_root / "labels" / split).mkdir(parents=True, exist_ok=True)
        
    # Gather Kaggle files
    kaggle_images = sorted(list(kaggle_img_dir.glob("*.png")))
    all_items = [] # list of dicts: {'src_img', 'src_lbl', 'dest_stem'}
    
    for img_file in kaggle_images:
        lbl_file = kaggle_lbl_dir / f"{img_file.stem}.txt"
        if lbl_file.exists():
            all_items.append({
                'src_img': img_file,
                'src_lbl': lbl_file,
                'dest_stem': img_file.stem
            })
            
    # Gather RDD2022 files (prefix with 'rdd_' to avoid collisions)
    rdd_images = sorted(list(rdd_img_dir.glob("*.png")))
    for img_file in rdd_images:
        lbl_file = rdd_lbl_dir / f"{img_file.stem}.txt"
        if lbl_file.exists():
            all_items.append({
                'src_img': img_file,
                'src_lbl': lbl_file,
                'dest_stem': f"rdd_{img_file.stem}"
            })
            
    print(f"Total files collected for merge: {len(all_items)}")
    
    # Shuffle and split: 70% train / 20% val / 10% test
    random.seed(42)
    random.shuffle(all_items)
    
    total = len(all_items)
    train_end = int(total * 0.70)
    val_end = train_end + int(total * 0.20)
    
    split_items = {
        'train': all_items[:train_end],
        'val': all_items[train_end:val_end],
        'test': all_items[val_end:]
    }
    
    stats = {}
    
    for split in splits:
        items = split_items[split]
        split_potholes = 0
        
        for item in items:
            dest_img = merged_root / "images" / split / f"{item['dest_stem']}.png"
            dest_lbl = merged_root / "labels" / split / f"{item['dest_stem']}.txt"
            
            # Copy files
            shutil.copy(item['src_img'], dest_img)
            shutil.copy(item['src_lbl'], dest_lbl)
            
            # Read pothole count
            split_potholes += read_instance_count(dest_lbl)
            
        stats[split] = {
            'images': len(items),
            'potholes': split_potholes
        }
        
    # Output detailed statistics
    total_imgs = sum(s['images'] for s in stats.values())
    total_potholes = sum(s['potholes'] for s in stats.values())
    
    print("\n" + "="*60)
    print(" MERGED DATASET STATISTICS")
    print("="*60)
    print(f"  Total Images       : {total_imgs}")
    print(f"  Total Annotations  : {total_potholes} potholes")
    print("-"*60)
    for split in splits:
        img_count = stats[split]['images']
        pot_count = stats[split]['potholes']
        img_pct = (img_count / total_imgs) * 100
        avg_density = pot_count / max(img_count, 1)
        print(f"  {split.capitalize():<5s} Split        : {img_count:4d} images ({img_pct:.1f}%) | {pot_count:4d} pothole instances (Avg: {avg_density:.2f}/img)")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
