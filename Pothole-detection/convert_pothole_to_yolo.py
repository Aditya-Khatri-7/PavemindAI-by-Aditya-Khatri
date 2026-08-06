import xml.etree.ElementTree as ET
import glob
import os
from PIL import Image
from tqdm import tqdm 

CLASSES = ['pothole']

ANNOT_PATH = "data/annotations" 
IMG_PATH = "data/images"
OUTPUT_PATH = "data/labels/" 

def convert_voc_to_yolo(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # --- THIS IS THE FIX ---
        img_filename_from_xml = root.find('filename').text
        base_filename = os.path.splitext(img_filename_from_xml)[0]
        img_file_with_png = base_filename + ".png"
        img_path = os.path.join(IMG_PATH, img_file_with_png)
        # --- END OF FIX ---

        # Get image size
        try:
            img = Image.open(img_path)
            img_width, img_height = img.size
        except FileNotFoundError:
             # Fallback just in case the <size> tag exists
            print(f"Warning: {img_path} not found. Trying <size> tag.")
            size = root.find('size')
            if size is not None:
                img_width = float(size.find('width').text)
                img_height = float(size.find('height').text)
            else:
                raise Exception(f"Cannot find image file {img_path} or <size> tag in {xml_file}")
        
        yolo_lines = []
        for obj in root.findall('object'):
            obj_name = obj.find('name').text
            if obj_name not in CLASSES:
                continue
            
            class_id = CLASSES.index(obj_name)
            bndbox = obj.find('bndbox')
            xmin = float(bndbox.find('xmin').text)
            ymin = float(bndbox.find('ymin').text)
            xmax = float(bndbox.find('xmax').text)
            ymax = float(bndbox.find('ymax').text)
            
            x_center = (xmin + xmax) / 2.0
            y_center = (ymin + ymax) / 2.0
            width = xmax - xmin
            height = ymax - ymin
            
            x_center_norm = x_center / img_width
            y_center_norm = y_center / img_height
            width_norm = width / img_width
            height_norm = height / img_height
            
            yolo_lines.append(f"{class_id} {x_center_norm} {y_center_norm} {width_norm} {height_norm}")

        return yolo_lines

    except Exception as e:
        print(f"Error processing {xml_file}: {e}")
        return None

def main():
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)
        print(f"Created output directory: {OUTPUT_PATH}")
        
    xml_files = glob.glob(os.path.join(ANNOT_PATH, '*.xml'))
    print(f"Found {len(xml_files)} XML files. Starting conversion...")
    
    for xml_file in tqdm(xml_files):
        base_filename = os.path.splitext(os.path.basename(xml_file))[0]
        yolo_data = convert_voc_to_yolo(xml_file)
        
        if yolo_data:
            output_file_path = os.path.join(OUTPUT_PATH, f"{base_filename}.txt")
            with open(output_file_path, 'w') as f:
                f.write('\n'.join(yolo_data))
            
    print(f"\nConversion complete! {len(xml_files)} YOLO labels saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()