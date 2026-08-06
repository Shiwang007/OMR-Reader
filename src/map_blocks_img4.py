import cv2
import numpy as np
import json

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

# Group into blocks
unvisited = set(unique)
blocks = []
while unvisited:
    start = unvisited.pop()
    current_block = [start]
    q = [start]
    while q:
        curr = q.pop(0)
        # 60px is a good threshold for bubbles belonging to the same grid
        neighbors = [p for p in unvisited if abs(p[0] - curr[0]) < 65 and abs(p[1] - curr[1]) < 65]
        for n in neighbors:
            unvisited.remove(n)
            current_block.append(n)
            q.append(n)
    
    # Only keep blocks with enough bubbles (e.g., at least 4 for MCQ, 10 for Roll)
    if len(current_block) >= 4:
        blocks.append(current_block)

print(f"Found {len(blocks)} blocks.")

# Separate Roll number block (it's the top-left most big block, typically Y < 500 and X < 500)
roll_block = None
question_blocks = []

for b in blocks:
    cx, cy = np.mean([p[0] for p in b]), np.mean([p[1] for p in b])
    if cy < 280 and cx < 500:
        roll_block = b
    else:
        question_blocks.append(b)

print(f"Roll block found: {roll_block is not None}, Question blocks: {len(question_blocks)}")

# A numerical question might be split into multiple sub-blocks if the gap between integer digits and decimal is > 65px
# Let's merge blocks that are horizontally or vertically close
merged_blocks = []
unvisited_q = list(question_blocks)
while unvisited_q:
    start = unvisited_q.pop(0)
    current_block = list(start)
    
    added = True
    while added:
        added = False
        to_remove = []
        for other in unvisited_q:
            # Check bounding box distance
            min_x1, max_x1 = min(p[0] for p in current_block), max(p[0] for p in current_block)
            min_y1, max_y1 = min(p[1] for p in current_block), max(p[1] for p in current_block)
            min_x2, max_x2 = min(p[0] for p in other), max(p[0] for p in other)
            min_y2, max_y2 = min(p[1] for p in other), max(p[1] for p in other)
            
            # If they are within 120px horizontally and 50px vertically, they are part of the same question
            dx = max(0, max(min_x1 - max_x2, min_x2 - max_x1))
            dy = max(0, max(min_y1 - max_y2, min_y2 - max_y1))
            
            if dx < 120 and dy < 120:
                current_block.extend(other)
                to_remove.append(other)
                added = True
        
        for r in to_remove:
            unvisited_q.remove(r)
            
    merged_blocks.append(current_block)

print(f"After merging, found {len(merged_blocks)} question blocks.")

for i, b in enumerate(merged_blocks):
    min_x, max_x = min(p[0] for p in b), max(p[0] for p in b)
    min_y, max_y = min(p[1] for p in b), max(p[1] for p in b)
    print(f"Q-Block {i+1}: X={min_x:.0f}-{max_x:.0f}, Y={min_y:.0f}-{max_y:.0f}, total_bubbles={len(b)}")

# Let's try drawing these blocks to visually see them
vis = img.copy()
for i, b in enumerate(merged_blocks):
    min_x, max_x = min(p[0] for p in b), max(p[0] for p in b)
    min_y, max_y = min(p[1] for p in b), max(p[1] for p in b)
    cv2.rectangle(vis, (int(min_x)-10, int(min_y)-10), (int(max_x)+10, int(max_y)+10), (0, 0, 255), 3)
    cv2.putText(vis, str(i), (int(min_x), int(min_y)-15), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

if roll_block:
    min_x, max_x = min(p[0] for p in roll_block), max(p[0] for p in roll_block)
    min_y, max_y = min(p[1] for p in roll_block), max(p[1] for p in roll_block)
    cv2.rectangle(vis, (int(min_x)-10, int(min_y)-10), (int(max_x)+10, int(max_y)+10), (0, 255, 0), 3)
    cv2.putText(vis, "ROLL", (int(min_x), int(min_y)-15), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\output\mapped_blocks_img4.jpg", vis)
