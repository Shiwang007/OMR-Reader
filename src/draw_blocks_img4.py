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

img_annotated = img.copy()

for i, (x, y) in enumerate(circles):
    cv2.circle(img_annotated, (int(x), int(y)), 15, (0, 0, 255), 2)
    # only print coords for top half to avoid clutter
    if y < 1400:
        # cv2.putText(img_annotated, f"{int(x)},{int(y)}", (int(x)-20, int(y)-20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
        pass

# Actually let's just group them into grids using my cluster_1d function and draw boxes around the grids!
def cluster_1d(vals, tol=20):
    if not vals: return []
    vals = sorted(vals)
    clusters = []
    curr = [vals[0]]
    for v in vals[1:]:
        if v - curr[-1] <= tol:
            curr.append(v)
        else:
            clusters.append(curr)
            curr = [v]
    clusters.append(curr)
    return clusters

unvisited = set(circles)
blocks = []
while unvisited:
    start = unvisited.pop()
    current_block = [start]
    q = [start]
    while q:
        curr = q.pop(0)
        neighbors = [p for p in unvisited if abs(p[0] - curr[0]) < 45 and abs(p[1] - curr[1]) < 45]
        for n in neighbors:
            unvisited.remove(n)
            current_block.append(n)
            q.append(n)
    if len(current_block) >= 4:
        blocks.append(current_block)

for i, b in enumerate(blocks):
    min_x, max_x = min(p[0] for p in b), max(p[0] for p in b)
    min_y, max_y = min(p[1] for p in b), max(p[1] for p in b)
    cv2.rectangle(img_annotated, (int(min_x)-10, int(min_y)-10), (int(max_x)+10, int(max_y)+10), (0, 255, 0), 3)
    cv2.putText(img_annotated, f"B{i}: {len(b)}b", (int(min_x), int(min_y)-15), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    print(f"Block {i}: X={min_x:.0f}-{max_x:.0f}, Y={min_y:.0f}-{max_y:.0f}, bubbles={len(b)}")

cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\output\annotated_blocks_img4.jpg", img_annotated)
