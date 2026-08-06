import cv2
import numpy as np

img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped_img4.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

cnts, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
circles = []
for c in cnts:
    (x, y), r = cv2.minEnclosingCircle(c)
    area = cv2.contourArea(c)
    if 10 < r < 20 and area > 100:
        if not any(np.hypot(x - u[0], y - u[1]) < 10.0 for u in circles):
            circles.append((float(x), float(y)))

phys_mcq = [p for p in circles if 800 < p[0] < 1200 and 750 < p[1] < 1250]
ys = sorted([p[1] for p in phys_mcq])
row_centers = []
curr = [ys[0]]
for y in ys[1:]:
    if y - curr[-1] < 15:
        curr.append(y)
    else:
        row_centers.append(np.mean(curr))
        curr = [y]
row_centers.append(np.mean(curr))

for ry in row_centers:
    r_pts = [p for p in phys_mcq if abs(p[1] - ry) < 15]
    print(f"Y={ry:.0f} : {len(r_pts)} bubbles. X coords: {[int(p[0]) for p in sorted(r_pts, key=lambda x: x[0])]}")

