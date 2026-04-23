import cv2
import numpy as np
import imutils

def measure():
    img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\data\debug_box_0.jpg")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 170, 255, cv2.THRESH_BINARY_INV)
    
    # Find line
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    detect_h = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel, iterations=2)
    cnts = cv2.findContours(detect_h, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    line_y = min(cv2.boundingRect(c)[1] for c in cnts)
    
    # Find first bubble (using Hough or simple contours)
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=15,
                              param1=50, param2=20, minRadius=8, maxRadius=18)
    
    if circles is not None:
        circles = sorted(circles[0], key=lambda c: c[1])
        first_bubble_y = circles[0][1]
        
        # We need to find which QUESTION this bubble belongs to.
        # It's Q15 (student's first mark).
        # Wait, if we use Hough, we find empty ones too!
        # So first_bubble_y is Q1.
        
        print(f"Line Y: {line_y}")
        print(f"First Bubble Y: {first_bubble_y}")
        print(f"Offset: {first_bubble_y - line_y}")

if __name__ == "__main__":
    measure()
