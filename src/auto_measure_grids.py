import cv2
import numpy as np
import json

img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)

# Detect circles using HoughCircles
circles = cv2.HoughCircles(
    blurred, cv2.HOUGH_GRADIENT,
    dp=1.2, minDist=18,
    param1=50, param2=20,
    minRadius=9, maxRadius=16
)

if circles is not None:
    circles = np.round(circles[0]).astype(int)
    print(f"Total circles detected in canonical image: {len(circles)}")
    
    # Filter circles by region
    # 1. Roll No. region: Y between 250 and 780, X between 100 and 600
    roll_circles = [c for c in circles if 250 < c[1] < 780 and 100 < c[0] < 600]
    print(f"Roll No. circles: {len(roll_circles)}")
    
    # Let's inspect unique X columns and Y rows for Roll No.
    if roll_circles:
        xs = sorted(list(set([c[0] for c in roll_circles])))
        ys = sorted(list(set([c[1] for c in roll_circles])))
        print(f"Roll No. X range: min={min(c[0] for c in roll_circles)}, max={max(c[0] for c in roll_circles)}")
        print(f"Roll No. Y range: min={min(c[1] for c in roll_circles)}, max={max(c[1] for c in roll_circles)}")

    # Let's inspect Section 1 MCQ circles (Y between 900 and 1350)
    sec1_circles = [c for c in circles if 900 < c[1] < 1350]
    print(f"Section 1 circles: {len(sec1_circles)}")

    # Section 3 Numerical circles (Y between 1400 and 2800)
    sec3_circles = [c for c in circles if 1400 < c[1] < 2800]
    print(f"Section 3 circles: {len(sec3_circles)}")

    # Section 4 MCQ circles (Y between 2900 and 3200)
    sec4_circles = [c for c in circles if 2900 < c[1] < 3200]
    print(f"Section 4 circles: {len(sec4_circles)}")
