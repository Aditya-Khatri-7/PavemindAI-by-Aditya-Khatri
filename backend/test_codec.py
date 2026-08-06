import cv2
import numpy as np

def test_codecs():
    codecs = [
        ('VP80', '.webm'),
        ('VP90', '.webm'),
        ('X264', '.mp4'),
        ('avc1', '.mp4'),
        ('H264', '.mp4'),
        ('mp4v', '.mp4'),
        ('MJPG', '.avi')
    ]
    
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    
    for codec, ext in codecs:
        filename = f"test_{codec}{ext}"
        try:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            writer = cv2.VideoWriter(filename, fourcc, 25.0, (640, 480))
            if writer.isOpened():
                print(f"Codec {codec} with extension {ext}: SUPPORTED")
                writer.write(img)
                writer.release()
                import os
                if os.path.exists(filename):
                    os.remove(filename)
            else:
                print(f"Codec {codec} with extension {ext}: NOT SUPPORTED (failed to open)")
        except Exception as e:
            print(f"Codec {codec} with extension {ext}: ERROR ({e})")

if __name__ == "__main__":
    test_codecs()
