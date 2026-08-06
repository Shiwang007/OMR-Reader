import cv2
import numpy as np
import os

image_path = r"f:\Medjeex\Medjeex-OMR-Engine\Advance omr 1\Image (3).jpg"
img = cv2.imread(image_path)
if img is None:
    print("Error: Could not load image:", image_path)
    exit(1)

h, w = img.shape[:2]
print(f"Loaded image size: {w} x {h}")

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)

cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

candidates = []
margin = 250
for c in cnts:
    x, y, bw, bh = cv2.boundingRect(c)
    area = cv2.contourArea(c)
    aspect_ratio = bw / float(bh)
    if 10 < bw < 100 and 10 < bh < 100 and 0.4 < aspect_ratio < 2.5 and area > 100:
        if (x < margin or x > w - margin) and (y < margin or y > h - margin):
            candidates.append((x, y, bw, bh, x + bw/2.0, y + bh/2.0))

print(f"Found {len(candidates)} potential fiducial corner markers:")
for c in candidates:
    print(f"  Box at X={c[0]}, Y={c[1]}, W={c[2]}, H={c[3]}, Center=({c[4]:.1f}, {c[5]:.1f})")

tl = min(candidates, key=lambda c: c[4]**2 + c[5]**2) if candidates else None
tr = min(candidates, key=lambda c: (w - c[4])**2 + c[5]**2) if candidates else None
bl = min(candidates, key=lambda c: c[4]**2 + (h - c[5])**2) if candidates else None
br = min(candidates, key=lambda c: (w - c[4])**2 + (h - c[5])**2) if candidates else None

print("\nCategorized Fiducials:")
print(f"  Top-Left:     {tl}")
print(f"  Top-Right:    {tr}")
print(f"  Bottom-Left:  {bl}")
print(f"  Bottom-Right: {br}")

debug_img = img.copy()
for c in candidates:
    cv2.rectangle(debug_img, (c[0], c[1]), (c[0]+c[2], c[1]+c[3]), (0, 255, 0), 3)

os.makedirs(r"f:\Medjeex\Medjeex-OMR-Engine\output", exist_ok=True)
cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\output\debug_fiducials.jpg", debug_img)
print("Saved debug fiducials to output/debug_fiducials.jpg")
