import imageio
import numpy as np

def test_imageio_write():
    filename = "test_imageio.mp4"
    try:
        # Create a writer using FFMPEG format and h264 codec
        writer = imageio.get_writer(filename, fps=25, codec='h264', quality=8)
        
        # Write 50 frames of black/white moving circle
        for i in range(50):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            # Draw a simple white square moving across
            x = (i * 10) % 600
            frame[200:280, x:x+80] = 255
            writer.append_data(frame)
        writer.close()
        print("Successfully wrote H.264 video with imageio!")
        
        # Clean up
        import os
        if os.path.exists(filename):
            os.remove(filename)
    except Exception as e:
        print(f"Imageio write failed: {e}")

if __name__ == "__main__":
    test_imageio_write()
