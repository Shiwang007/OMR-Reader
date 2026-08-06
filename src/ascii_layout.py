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

# Create a 2D ASCII grid
width = 2500 // 20
height = 3500 // 40

grid = [[' ' for _ in range(width)] for _ in range(height)]

for cx, cy in circles:
    x_idx = int(cx // 20)
    y_idx = int(cy // 40)
    if 0 <= x_idx < width and 0 <= y_idx < height:
        grid[y_idx][x_idx] = 'O'

with open(r"f:\Medjeex\Medjeex-OMR-Engine\output\ascii_img4.txt", "w") as f:
    for row in grid:
        f.write("".join(row) + "\n")
