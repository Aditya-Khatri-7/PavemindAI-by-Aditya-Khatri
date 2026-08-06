"""
filter_rdd2022_potholes.py  —  Extract and Remap Pothole (D40) Annotations from RDD2022
IBM Internship | Group 74 | AIML74 | UPES Dehradun

Usage:
  python filter_rdd2022_potholes.py --input_dir /path/to/rdd2022/labels --output_dir /path/to/filtered/labels
"""

import argparse
from pathlib import Path
from tqdm import tqdm

POTHOLE_CLASS_ID = 3  # D40 = pothole in RDD2022

def filter_labels(input_dir, output_dir):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' does not exist.")
        return
        
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"Filtering files from '{input_path}' into '{output_path}'...")
    
    label_files = list(input_path.glob('*.txt'))
    print(f"Found {len(label_files)} label files.")
    
    filtered_count = 0
    for label_file in tqdm(label_files):
        try:
            pothole_lines = []
            content = label_file.read_text().strip()
            if not content:
                continue
                
            for line in content.splitlines():
                parts = line.split()
                if len(parts) >= 5 and int(parts[0]) == POTHOLE_CLASS_ID:
                    # Remap from class 3 to class 0
                    pothole_lines.append('0 ' + ' '.join(parts[1:]))
                    
            if pothole_lines:
                out_file = output_path / label_file.name
                out_file.write_text('\n'.join(pothole_lines))
                filtered_count += 1
        except Exception as e:
            print(f"Error processing {label_file.name}: {e}")
            
    print(f"Filtering complete! Saved {filtered_count} label files containing potholes to: {output_dir}")

def main():
    parser = argparse.ArgumentParser(description='Filter RDD2022 labels to include only pothole class (remapped to index 0)')
    parser.add_argument('--input_dir', default='data/rdd2022_raw/labels', help='Path to raw RDD2022 label text files')
    parser.add_argument('--output_dir', default='data/rdd2022_filtered/labels', help='Path to save remapped labels')
    args = parser.parse_args()
    
    filter_labels(args.input_dir, args.output_dir)

if __name__ == '__main__':
    main()
