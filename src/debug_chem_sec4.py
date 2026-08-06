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

sec4_r_pts = [p for p in circles if 2100 < p[0] < 2275 and 3000 < p[1] < 3150]
print(f"Filtered sec4_r_pts count: {len(sec4_r_pts)}")
for p in sec4_r_pts:
    print(f"  X={p[0]:.1f}, Y={p[1]:.1f}")
