import cv2
import numpy as np

img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
_, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY_INV)

cnts, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

raw_circles = []
for c in cnts:
    (x, y), r = cv2.minEnclosingCircle(c)
    area = cv2.contourArea(c)
    if 10 < r < 20 and area > 100:
        raw_circles.append((float(x), float(y)))

circles = []
for p in raw_circles:
    if not any(np.hypot(p[0] - u[0], p[1] - u[1]) < 18.0 for u in circles):
        circles.append(p)

chem_sec4_r = [p for p in circles if 2100 < p[0] < 2380 and 2950 < p[1] < 3200]
chem_sec4_r.sort(key=lambda p: (p[1], p[0]))

print(f"Chemistry Sec 4 Right points ({len(chem_sec4_r)}):")
for p in chem_sec4_r:
    print(f"  X={p[0]:.1f}, Y={p[1]:.1f}")
