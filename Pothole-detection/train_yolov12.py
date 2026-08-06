import torch
import os
from ultralytics import YOLO
import glob

# This function will hold all our code
def main():
    # -------------------------------------------------------------------
    # 1. SETUP
    # -------------------------------------------------------------------
    print(f"Using torch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")

    # -------------------------------------------------------------------
    # 2. LOAD A PRE-TRAINED YOLOv12 MODEL
    # -------------------------------------------------------------------
    model = YOLO('yolov12n.pt')
    print("Loaded YOLOv12n model.")
    print(f"Model will train on: {model.device.type}")

    # -------------------------------------------------------------------
    # 3. TRAIN THE MODEL
    # -------------------------------------------------------------------
    print("Starting model training...")
    results = model.train(
        data='pothole_dataset.yaml',
        epochs=2,
        imgsz=640,
        batch=4,
        name='yolov12n_merged_run',
        workers=0,  # <--- THIS IS THE FIX
        patience=5  # Early stopping patience
    )
    print("Training complete.")

    # -------------------------------------------------------------------
    # 4. VALIDATE AND TEST
    # -------------------------------------------------------------------
    print("Final validation metrics:")
    print(f"mAP50-95: {results.box.map}")
    print(f"mAP50: {results.box.map50}")

    # --- Test on a sample image ---
    try:
        # Find a random .png file to test
        test_img_path = glob.glob("data/images/*.png")[0]
        print(f"Running prediction on a sample image: {test_img_path}")
        
        predict_results = model.predict(test_img_path, save=True, conf=0.5)

        pred_img_path = predict_results[0].save_dir
        print(f"Prediction image saved to: {pred_img_path}")

    except IndexError:
        print("Could not find any .png images in 'data/images/' to test.")
    except Exception as e:
        print(f"Error during prediction: {e}")

    # -------------------------------------------------------------------
    # 5. EXPORT THE MODEL
    # -------------------------------------------------------------------
    print("Exporting model to ONNX format...")
    model.export(format='onnx')
    print(f"Model exported to 'runs/detect/{results.save_dir}/weights/best.onnx'")


# -------------------------------------------------------------------
# We must call main() from inside this "if" block
# -------------------------------------------------------------------
if __name__ == "__main__":
    torch.multiprocessing.freeze_support()
    main()