"""
Step 1: Warp Image (4) to canonical coordinates, detect all bubbles,
and produce measured_all_bubbles.jpg for visual verification.
"""
import cv2
import numpy as np

# Load image
img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\Advance omr 2\Image (4).jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
_, thresh = cv2.threshold(blurred, 80, 255, cv2.THRESH_BINARY_INV)

# Detect corner markers for perspective warp
cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
corners = []
for c in cnts:
    x, y, cw, ch = cv2.boundingRect(c)
    aspect_ratio = cw / float(ch)
    area = cv2.contourArea(c)
    if 10 < cw < 110 and 10 < ch < 110 and 0.7 < aspect_ratio < 1.3 and area > 200:
        cx, cy = x + cw/2.0, y + ch/2.0
        h, w = img.shape[:2]
        if (cx < 200 or cx > w - 200) and (cy < 200 or cy > h - 200):
            corners.append((cx, cy))

print(f"Found {len(corners)} corner markers")

if len(corners) >= 4:
    corners = sorted(corners, key=lambda p: p[1])
    top_two = sorted(corners[:2], key=lambda p: p[0])
    bottom_two = sorted(corners[-2:], key=lambda p: p[0])
    tl, tr = top_two[0], top_two[1]
    bl, br = bottom_two[0], bottom_two[1]
    
    print(f"TL: {tl}, TR: {tr}")
    print(f"BL: {bl}, BR: {br}")
    
    # Warp to canonical size (same as Image 3)
    W, H = 2480, 3442
    pts_src = np.array([tl, tr, br, bl], dtype="float32")
    pts_dst = np.array([
        [66, 211],
        [2365, 220],
        [2357, 3205],
        [57, 3194]
    ], dtype="float32")
    
    M = cv2.getPerspectiveTransform(pts_src, pts_dst)
    warped = cv2.warpPerspective(img, M, (W, H))
    
    cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped_img4.jpg", warped)
    print("Saved canonical_warped_img4.jpg")
    
    # Detect all circles in warped image
    gray_w = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    blurred_w = cv2.GaussianBlur(gray_w, (5, 5), 0)
    _, thresh_w = cv2.threshold(blurred_w, 150, 255, cv2.THRESH_BINARY_INV)
    cnts_w, _ = cv2.findContours(thresh_w, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    all_raw = []
    for c in cnts_w:
        (x, y), r = cv2.minEnclosingCircle(c)
        area = cv2.contourArea(c)
        if 10 < r < 20 and area > 100:
            all_raw.append((float(x), float(y), float(r)))
    
    # Dedup concentric rings
    unique = []
    for p in all_raw:
        if not any(np.hypot(p[0] - u[0], p[1] - u[1]) < 10.0 for u in unique):
            unique.append(p)
    
    print(f"Raw contours: {len(all_raw)}, unique bubbles: {len(unique)}")
    
    # Draw all detected bubbles on visualization
    vis = warped.copy()
    for (x, y, r) in all_raw:
        cv2.circle(vis, (int(x), int(y)), int(r), (0, 255, 0), 1)
    
    cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\output\measured_all_bubbles_img4.jpg", vis)
    print("Saved measured_all_bubbles_img4.jpg")
    
    # Print Y-band analysis for layout understanding
    print("\n=== Y-band distribution (50px bands) ===")
    y_vals = sorted([p[1] for p in unique])
    band_size = 50
    y_min, y_max = int(y_vals[0]), int(y_vals[-1])
    for y_start in range(y_min, y_max + 1, band_size):
        count = len([p for p in unique if y_start <= p[1] < y_start + band_size])
        if count > 0:
            print(f"  Y {y_start:4d}-{y_start + band_size:4d}: {count:3d} bubbles")
    
    # Print X-band analysis
    print("\n=== X-band distribution (100px bands) ===")
    x_vals = sorted([p[0] for p in unique])
    x_min, x_max = int(x_vals[0]), int(x_vals[-1])
    for x_start in range(x_min, x_max + 1, 100):
        count = len([p for p in unique if x_start <= p[0] < x_start + 100])
        if count > 0:
            print(f"  X {x_start:4d}-{x_start + 100:4d}: {count:3d} bubbles")

else:
    print("ERROR: Could not find 4 corner markers!")
