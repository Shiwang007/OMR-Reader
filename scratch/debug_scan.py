"""Debug scanner — traces exactly what the engine does on Image (2).jpg"""
import cv2
import numpy as np
import imutils
import json

image_path = r"f:\Medjeex\Medjeex-OMR-Engine\omr\Image (5).jpg"
template_path = r"f:\Medjeex\Medjeex-OMR-Engine\templates\template.json"

image = cv2.imread(image_path)
h_img, w_img = image.shape[:2]
print(f"Image: {w_img}x{h_img}")

with open(template_path) as f:
    template = json.load(f)

# --- Step 1: Header detection ---
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(gray, 50, 150)
h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (w_img // 4, 5))
detect_h = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, h_kernel)
cnts = imutils.grab_contours(cv2.findContours(detect_h, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE))

candidates = []
for c in cnts:
    x, y, lw, lh = cv2.boundingRect(c)
    if lw > w_img * 0.6 and y < h_img * 0.4:
        candidates.append((y, lw, lh))
        
print(f"\nHeader candidates: {candidates}")
cal_header = 495
if candidates:
    best = min(candidates, key=lambda t: abs(t[0] - cal_header))
    scan_header_y = best[0]
else:
    scan_header_y = cal_header
    
y_shift = scan_header_y - cal_header
print(f"Detected header Y: {scan_header_y}")
print(f"Y-shift: {y_shift}")

# --- Step 2: Threshold ---
blurred = cv2.medianBlur(gray, 3)
_, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
print(f"\nThreshold image shape: {thresh.shape}")

# --- Step 3: Check a few known bubbles ---
subj = "Physics"
questions = template[subj]
print(f"\n=== Checking {subj} Q1-Q5 ===")
for q_idx in range(5):
    row = questions[q_idx]
    for opt_idx, coord in enumerate(row):
        ax = int(coord['abs_x'])
        ay = int(coord['abs_y']) + y_shift
        size = 16
        if size < ay < h_img - size and size < ax < w_img - size:
            roi = thresh[ay - size:ay + size, ax - size:ax + size]
            density = cv2.countNonZero(roi) / float(roi.size)
            opt_letter = ["A","B","C","D"][opt_idx]
            mark = " <<< FILLED" if density > 0.22 else ""
            print(f"  Q{q_idx+1} {opt_letter}: ({ax},{ay}) density={density:.3f}{mark}")
        else:
            opt_letter = ["A","B","C","D"][opt_idx]
            print(f"  Q{q_idx+1} {opt_letter}: OUT OF BOUNDS ({ax},{ay})")

# --- Step 4: Fine-shift debug ---
print(f"\n=== Fine-shift calculation for {subj} ===")
fine_shifts = []
for q_idx in range(5, min(40, len(questions))):
    for opt_idx in range(4):
        coord = questions[q_idx][opt_idx]
        ax = int(coord['abs_x'])
        ay = int(coord['abs_y']) + y_shift
        r = 25
        if r < ay < h_img - r and r < ax < w_img - r:
            roi = thresh[ay - r:ay + r, ax - r:ax + r]
            fill = cv2.countNonZero(roi) / float(roi.size)
            if fill > 0.25:
                M = cv2.moments(roi)
                if M["m00"] > 0:
                    cy_local = int(M["m01"] / M["m00"]) - r
                    fine_shifts.append(cy_local)

if fine_shifts:
    print(f"  Fine shifts collected: {len(fine_shifts)}")
    print(f"  Min: {min(fine_shifts)}, Max: {max(fine_shifts)}, Median: {int(np.median(fine_shifts))}")
    total_shift = y_shift + int(np.median(fine_shifts))
else:
    print(f"  No fine shifts found!")
    total_shift = y_shift
    
print(f"  Total shift applied: {total_shift}")

# --- Step 5: Re-check Q1-Q5 with total_shift ---
print(f"\n=== Re-checking {subj} Q1-Q5 with total_shift={total_shift} ===")
for q_idx in range(5):
    row = questions[q_idx]
    for opt_idx, coord in enumerate(row):
        ax = int(coord['abs_x'])
        ay = int(coord['abs_y']) + total_shift
        size = 16
        if size < ay < h_img - size and size < ax < w_img - size:
            roi = thresh[ay - size:ay + size, ax - size:ax + size]
            density = cv2.countNonZero(roi) / float(roi.size)
            opt_letter = ["A","B","C","D"][opt_idx]
            mark = " <<< FILLED" if density > 0.22 else ""
            print(f"  Q{q_idx+1} {opt_letter}: ({ax},{ay}) density={density:.3f}{mark}")
