import cv2
import numpy as np
import json
from collections import defaultdict

# 1. Load image and find bubbles
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

print(f"Total unique bubbles found: {len(unique)}")

# 2. Group into X columns and Y rows
x_coords = [b[0] for b in unique]
y_coords = [b[1] for b in unique]

def group_1d(coords, tol=15):
    coords = sorted(coords)
    groups = []
    current_group = [coords[0]]
    for c in coords[1:]:
        if c - current_group[-1] <= tol:
            current_group.append(c)
        else:
            groups.append(np.mean(current_group))
            current_group = [c]
    groups.append(np.mean(current_group))
    return groups

x_groups = group_1d(x_coords)
y_groups = group_1d(y_coords)

# 3. Find blocks (questions)
# A block is a set of bubbles that form a grid.
# We will identify bubbles by their (x_idx, y_idx) in the groups.
grid_bubbles = []
for bx, by, r in unique:
    cx = min(x_groups, key=lambda x: abs(x - bx))
    cy = min(y_groups, key=lambda y: abs(y - by))
    if abs(cx - bx) < 15 and abs(cy - by) < 15:
        grid_bubbles.append((cx, cy))

# Group bubbles into contiguous blocks
# A block is connected if x distance < 80 and y distance < 80
blocks = []
unvisited = set(grid_bubbles)

while unvisited:
    start = unvisited.pop()
    current_block = [start]
    q = [start]
    while q:
        curr = q.pop(0)
        neighbors = [p for p in unvisited if abs(p[0] - curr[0]) < 80 and abs(p[1] - curr[1]) < 80]
        for n in neighbors:
            unvisited.remove(n)
            current_block.append(n)
            q.append(n)
    blocks.append(current_block)

print(f"Found {len(blocks)} distinct blocks.")

# Sort blocks by Y then X
blocks.sort(key=lambda b: (min(p[1] for p in b), min(p[0] for p in b)))

for i, b in enumerate(blocks):
    min_x, max_x = min(p[0] for p in b), max(p[0] for p in b)
    min_y, max_y = min(p[1] for p in b), max(p[1] for p in b)
    xs = sorted(list(set([p[0] for p in b])))
    ys = sorted(list(set([p[1] for p in b])))
    
    # Is it a standard MCQ (4 options in 1 row?) or numerical (multiple rows/cols)
    print(f"Block {i+1}: X={min_x:.0f}-{max_x:.0f}, Y={min_y:.0f}-{max_y:.0f}, cols={len(xs)}, rows={len(ys)}, total_bubbles={len(b)}")

    # Special check for decimal bubble:
    # Are there any single row columns or off-grid bubbles inside the bounding box of this block?
    block_all_bubbles = [p for p in unique if min_x - 30 <= p[0] <= max_x + 30 and min_y - 30 <= p[1] <= max_y + 30]
    if len(block_all_bubbles) > len(b):
        print(f"  -> Has {len(block_all_bubbles) - len(b)} extra bubbles possibly off-grid (e.g. decimals).")
        # Print their coordinates relative to the block
        extras = [p for p in block_all_bubbles if not any(abs(p[0]-gx)<15 and abs(p[1]-gy)<15 for gx, gy in b)]
        for ep in extras:
            print(f"      Extra bubble at X={ep[0]:.0f}, Y={ep[1]:.0f}")
