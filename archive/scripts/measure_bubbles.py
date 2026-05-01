import cv2
import numpy as np

def measure_bubbles(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Use Hough Circle Transform or simple contour detection for circles
    # Bubbles are roughly 30-40px in diameter
    circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
        param1=50, param2=20, minRadius=10, maxRadius=25
    )
    
    if circles is not None:
        circles = np.uint16(np.around(circles))
        return circles[0]
    return []

if __name__ == "__main__":
    image_path = r'f:\Medjeex\Medjeex-OMR-Engine\omr\Image.jpg'
    bubbles = measure_bubbles(image_path)
    print(f"Found {len(bubbles)} potential bubbles.")
    
    # Sort bubbles by Y then X
    bubbles = sorted(bubbles, key=lambda b: (b[1], b[0]))
    
    # Print the first few and last few to get ranges
    print("\nTop bubbles:")
    for b in bubbles[:10]:
        print(f"X: {b[0]}, Y: {b[1]}, R: {b[2]}")
        
    print("\nBottom bubbles:")
    for b in bubbles[-10:]:
        print(f"X: {b[0]}, Y: {b[1]}, R: {b[2]}")
