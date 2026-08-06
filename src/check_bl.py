import cv2
import numpy as np

img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\Advance omr 1\Image (3).jpg")
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)

cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

print("Checking contours in Bottom-Left region (X < 200, Y > 3000):")
for c in cnts:
    x, y, bw, bh = cv2.boundingRect(c)
    if x < 200 and y > 3000:
        area = cv2.contourArea(c)
        print(f"  Box: X={x}, Y={y}, W={bw}, H={bh}, Area={area}")
