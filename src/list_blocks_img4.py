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

roll_pts = [p for p in circles if 100 < p[0] < 800 and 100 < p[1] < 300]
q_pts = [p for p in circles if not any(abs(p[0]-rp[0])<1 and abs(p[1]-rp[1])<1 for rp in roll_pts)]

unvisited = set(q_pts)
blocks = []
while unvisited:
    start = unvisited.pop()
    current_block = [start]
    q = [start]
    while q:
        curr = q.pop(0)
        neighbors = [p for p in unvisited if abs(p[0] - curr[0]) < 50 and abs(p[1] - curr[1]) < 50]
        for n in neighbors:
            unvisited.remove(n)
            current_block.append(n)
            q.append(n)
    
    if len(current_block) >= 12:
        xs = [p[0] for p in current_block]
        span_x = max(xs) - min(xs)
        if span_x > 250:
            mid_x = min(xs) + span_x / 2.0
            left_b = [p for p in current_block if p[0] < mid_x]
            right_b = [p for p in current_block if p[0] >= mid_x]
            if len(left_b) >= 12: blocks.append(left_b)
            if len(right_b) >= 12: blocks.append(right_b)
        else:
            blocks.append(current_block)

def cluster_1d(vals, tol=15):
    if not vals: return []
    vals = sorted(vals)
    clusters = []
    curr = [vals[0]]
    for v in vals[1:]:
        if v - curr[-1] <= tol:
            curr.append(v)
        else:
            clusters.append(float(np.mean(curr)))
            curr = [v]
    clusters.append(float(np.mean(curr)))
    return sorted(clusters)

block_infos = []
for b in blocks:
    cx = np.mean([p[0] for p in b])
    cy = np.mean([p[1] for p in b])
    ys = cluster_1d([p[1] for p in b], tol=15)
    b_type = "num" if len(ys) >= 8 else "mcq"
    
    col = 0
    if cx < 360: col = 0
    elif cx < 800: col = 1
    elif cx < 1180: col = 2
    elif cx < 1580: col = 3
    elif cx < 1920: col = 4
    else: col = 5
    
    block_infos.append({
        "cx": cx, "cy": cy, "col": col, "type": b_type, "bubbles": len(b)
    })

block_infos.sort(key=lambda x: (x["col"], x["cy"]))

print("List of all blocks sorted by Column then Y:")
for i, b in enumerate(block_infos):
    print(f"Col {b['col']}, Y={b['cy']:5.0f} : {b['type'].upper():4s} ({b['bubbles']} bubbles)")
