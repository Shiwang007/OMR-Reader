import cv2
import numpy as np

img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped_img4.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
_, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY_INV)

cnts, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

all_raw = []
for c in cnts:
    (x, y), r = cv2.minEnclosingCircle(c)
    area = cv2.contourArea(c)
    if 10 < r < 20 and area > 100:
        all_raw.append((float(x), float(y), float(r)))

unique = []
for p in all_raw:
    if not any(np.hypot(p[0] - u[0], p[1] - u[1]) < 10.0 for u in unique):
        unique.append(p)

# Q10 is roughly at top right of MATHS section. Let's find bubbles around X=500-800, Y=300-800.
q10_bubbles = [p for p in unique if 400 < p[0] < 800 and 300 < p[1] < 1000]

print(f"Found {len(q10_bubbles)} bubbles for Q10 area.")
for p in sorted(q10_bubbles, key=lambda b: (b[0], b[1])): # sort by X then Y
    print(f"X: {p[0]:.1f}, Y: {p[1]:.1f}")
