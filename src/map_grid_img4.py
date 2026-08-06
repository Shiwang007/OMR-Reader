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

def get_cell_info(x1, x2, y1, y2):
    pts = [p for p in circles if x1 < p[0] < x2 and y1 < p[1] < y2]
    if not pts: return "EMPTY"
    
    # filter out question numbers (usually the leftmost column in the cell, if it has 1 bubble per row and is far from the rest)
    xs = sorted([p[0] for p in pts])
    ys = sorted([p[1] for p in pts])
    if not xs: return "EMPTY"
    
    # cluster by Y to find rows
    row_centers = []
    curr = [ys[0]]
    for y in ys[1:]:
        if y - curr[-1] < 15:
            curr.append(y)
        else:
            row_centers.append(curr)
            curr = [y]
    row_centers.append(curr)
    
    num_rows = len(row_centers)
    total_bubbles = len(pts)
    
    if num_rows >= 8:
        return f"NUMERICAL ({total_bubbles} bubbles)"
    elif 1 < num_rows <= 5:
        return f"MCQ ({num_rows} questions, {total_bubbles} bubbles)"
    else:
        return f"UNKNOWN ({num_rows} rows, {total_bubbles} bubbles)"

bands_y = [
    (300, 750),
    (760, 1250),
    (1300, 1750),
    (1800, 2250),
    (2300, 2750),
    (2800, 3250)
]

cols_x = [
    ("Maths L", 100, 350),
    ("Maths R", 370, 780),
    ("Phys L", 850, 1150),
    ("Phys R", 1200, 1550),
    ("Chem L", 1600, 1920),
    ("Chem R", 1950, 2350)
]

for i, (y1, y2) in enumerate(bands_y):
    print(f"--- BAND {i+1} (Y: {y1}-{y2}) ---")
    for name, x1, x2 in cols_x:
        info = get_cell_info(x1, x2, y1, y2)
        print(f"{name:<10}: {info}")
