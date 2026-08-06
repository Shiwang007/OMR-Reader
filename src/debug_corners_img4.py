import cv2
import numpy as np

img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\Advance omr 2\Image (4).jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
_, thresh = cv2.threshold(blurred, 80, 255, cv2.THRESH_BINARY_INV)

cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
h, w = img.shape[:2]

corners = []
for c in cnts:
    x, y, cw, ch = cv2.boundingRect(c)
    aspect_ratio = cw / float(ch)
    area = cv2.contourArea(c)
    
    # Relax constraints to find the corner markers
    if 10 < cw < 200 and 10 < ch < 200 and 0.5 < aspect_ratio < 2.0 and area > 100:
        cx, cy = x + cw/2.0, y + ch/2.0
        # Only keep if it's near one of the 4 corners
        if (cx < 200 or cx > w - 200) and (cy < 200 or cy > h - 200):
            corners.append((cx, cy, cw, ch, area))

for cx, cy, cw, ch, area in corners:
    print(f"Corner candidate: X={cx:.1f}, Y={cy:.1f}, W={cw}, H={ch}, Area={area}")
