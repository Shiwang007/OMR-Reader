import cv2
import numpy as np
import json

img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (3, 3), 0)

# Use Canny edge + HoughCircles to find exact printed circle centers
circles = cv2.HoughCircles(
    blurred, cv2.HOUGH_GRADIENT,
    dp=1.2, minDist=18,
    param1=50, param2=22,
    minRadius=9, maxRadius=16
)

if circles is None:
    print("Error: HoughCircles found no circles")
    exit(1)

circles = np.round(circles[0]).astype(float)
print(f"Total circles detected via Hough: {len(circles)}")

# Draw overlay of Hough circles
vis = img.copy()
for (x, y, r) in circles:
    cv2.circle(vis, (int(x), int(y)), int(r), (0, 255, 0), 1)

cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\output\hough_measured_bubbles.jpg", vis)
print("Saved visualization to output/hough_measured_bubbles.jpg")
