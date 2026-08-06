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

def get_b(x1, x2, y1, y2):
    pts = [p for p in circles if x1 < p[0] < x2 and y1 < p[1] < y2]
    # cluster by X
    xs = sorted([p[0] for p in pts])
    if not xs: return "0 cols"
    clusters = []
    curr = [xs[0]]
    for x in xs[1:]:
        if x - curr[-1] < 15:
            curr.append(x)
        else:
            clusters.append(curr)
            curr = [x]
    clusters.append(curr)
    return f"{len(pts)} bubbles, {len(clusters)} columns. Col centers: {[int(np.mean(c)) for c in clusters]}"

print("=== MATHS (X: 100 - 800) ===")
print("Roll No area (Y: 100 - 800):", get_b(100, 400, 100, 800))
print("Right side top (Y: 100 - 800):", get_b(400, 800, 100, 800))

print("\nY: 800 - 1300")
print("Left side:", get_b(100, 400, 800, 1300))
print("Right side:", get_b(400, 800, 800, 1300))

print("\nY: 1300 - 1800")
print("Left side:", get_b(100, 400, 1300, 1800))
print("Right side:", get_b(400, 800, 1300, 1800))

print("\nY: 1800 - 2300")
print("Left side:", get_b(100, 400, 1800, 2300))
print("Right side:", get_b(400, 800, 1800, 2300))

print("\nY: 2300 - 2800")
print("Left side:", get_b(100, 400, 2300, 2800))
print("Right side:", get_b(400, 800, 2300, 2800))

print("\nY: 2800 - 3300")
print("Left side:", get_b(100, 400, 2800, 3300))
print("Right side:", get_b(400, 800, 2800, 3300))
