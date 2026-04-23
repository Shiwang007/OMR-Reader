"""
OMR Grid Measurement Script v2
================================
Measures physical properties with header-region filtering.
"""

import cv2
import numpy as np

image_path = r"f:\Medjeex\Medjeex-OMR-Engine\WhatsApp Image 2026-04-23 at 3.17.12 PM.jpeg"
image = cv2.imread(image_path)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
h, w = gray.shape
print(f"Image size: {w} x {h}\n")

# --- Step 1: Find the BOLD header line (Y-anchor) ---
edges = cv2.Canny(gray, 50, 150)
h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 3))
detect_h = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, h_kernel)
h_cnts = cv2.findContours(detect_h, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
import imutils
h_cnts = imutils.grab_contours(h_cnts)
wide_lines = [(cv2.boundingRect(c)[1], cv2.boundingRect(c)[2]) for c in h_cnts if cv2.boundingRect(c)[2] > w * 0.3]
wide_lines.sort()
print("Wide horizontal lines found (Y, Width):")
for y, lw in wide_lines[:10]:
    print(f"  Y={y}, width={lw}")

# The subject header line
header_y = wide_lines[0][0] if wide_lines else 350
print(f"\nHeader Y-anchor: {header_y}")

# --- Step 2: Detect bubbles ONLY in the OMR area (below header) ---
omr_region = gray[header_y:, :]
blurred = cv2.GaussianBlur(omr_region, (5, 5), 0)
circles = cv2.HoughCircles(
    blurred, cv2.HOUGH_GRADIENT,
    dp=1.2, minDist=15,
    param1=50, param2=25,
    minRadius=8, maxRadius=16
)

if circles is None:
    print("No circles found in OMR region")
    exit()

# Adjust Y coordinates back to full image
circles = np.round(circles[0]).astype(int)
for c in circles:
    c[1] += header_y

print(f"\nBubbles in OMR area: {len(circles)}")
radii = [c[2] for c in circles]
print(f"Radius — min:{min(radii)}, max:{max(radii)}, avg:{np.mean(radii):.1f}, median:{int(np.median(radii))}")

# --- Step 3: Cluster into columns ---
sorted_x = sorted(circles, key=lambda c: c[0])
columns = []
curr = [sorted_x[0]]
for c in sorted_x[1:]:
    if c[0] - curr[-1][0] < 20:
        curr.append(c)
    else:
        if len(curr) >= 10:  # real bubble columns have many bubbles
            columns.append(curr)
        curr = [c]
if len(curr) >= 10:
    columns.append(curr)

col_centers = [np.mean([c[0] for c in col]) for col in columns]
print(f"\nFiltered columns (>=10 bubbles): {len(columns)}")
for i, (col, center) in enumerate(zip(columns, col_centers)):
    print(f"  Col {i+1}: X={center:.1f} ({len(col)} bubbles)")

# --- Step 4: Identify subject groups ---
# Look at gaps between column centers
print(f"\nColumn gaps:")
gaps = []
for i in range(1, len(col_centers)):
    g = col_centers[i] - col_centers[i-1]
    gaps.append(g)
    marker = " <<<< SUBJECT BOUNDARY" if g > 80 else ""
    print(f"  Col{i} -> Col{i+1}: {g:.1f} px{marker}")

# Group by subject boundary (gap > 80px)
subject_groups = []
curr_group = [0]
for i, g in enumerate(gaps):
    if g > 80:
        subject_groups.append(curr_group)
        curr_group = [i+1]
    else:
        curr_group.append(i+1)
subject_groups.append(curr_group)

subjects = ["Physics", "Chemistry", "Biology I", "Biology II"]
print(f"\n{'='*60}")
print(f"SUBJECT ANALYSIS")
print(f"{'='*60}")

for i, group in enumerate(subject_groups):
    name = subjects[i] if i < len(subjects) else f"Extra-{i}"
    x_vals = [col_centers[ci] for ci in group]
    
    print(f"\n  [{name}]")
    print(f"  Option columns: {len(group)}")
    print(f"  Option A center-X: {x_vals[0]:.1f}")
    if len(x_vals) >= 4:
        print(f"  Option B center-X: {x_vals[1]:.1f}")
        print(f"  Option C center-X: {x_vals[2]:.1f}")
        print(f"  Option D center-X: {x_vals[3]:.1f}")
        horiz_gaps = [x_vals[j+1] - x_vals[j] for j in range(len(x_vals)-1)]
        print(f"  A->B: {horiz_gaps[0]:.1f}, B->C: {horiz_gaps[1]:.1f}, C->D: {horiz_gaps[2]:.1f}")
        print(f"  Avg option spacing: {np.mean(horiz_gaps):.1f} px")
    print(f"  Subject X-start: {min(x_vals):.1f}, X-end: {max(x_vals):.1f}")

# --- Step 5: Vertical row pitch ---
print(f"\n{'='*60}")
print(f"ROW (VERTICAL) ANALYSIS")
print(f"{'='*60}")

# Use the largest subject group (most columns = most data)
best_group = max(subject_groups, key=len)
# Get ALL bubbles in this group
all_ys = []
for ci in best_group:
    for c in columns[ci]:
        all_ys.append(c[1])

all_ys.sort()
rows_y = []
curr = [all_ys[0]]
for y in all_ys[1:]:
    if y - curr[-1] < 12:
        curr.append(y)
    else:
        rows_y.append(np.mean(curr))
        curr = [y]
rows_y.append(np.mean(curr))

print(f"  Rows detected: {len(rows_y)}")
print(f"  First row Y: {rows_y[0]:.1f}")
print(f"  Last row Y:  {rows_y[-1]:.1f}")

if len(rows_y) >= 2:
    row_gaps = [rows_y[j+1] - rows_y[j] for j in range(len(rows_y)-1)]
    print(f"  Row pitch — min: {min(row_gaps):.1f}, max: {max(row_gaps):.1f}")
    print(f"  Row pitch — avg: {np.mean(row_gaps):.1f}, median: {np.median(row_gaps):.1f}")
    
    # Show all row positions
    print(f"\n  Individual row Y-positions:")
    for ri, ry in enumerate(rows_y):
        gap_str = f"  (gap from prev: {row_gaps[ri-1]:.1f})" if ri > 0 else ""
        print(f"    Row {ri+1}: Y={ry:.1f}{gap_str}")

# --- Step 6: Draw annotated debug image ---
debug = image.copy()
colors = [(0,0,255), (0,255,0), (255,0,0), (255,255,0)]
for i, group in enumerate(subject_groups):
    color = colors[i % len(colors)]
    for ci in group:
        for c in columns[ci]:
            cv2.circle(debug, (c[0], c[1]), c[2], color, 2)

# Draw row lines
for ry in rows_y:
    cv2.line(debug, (0, int(ry)), (w, int(ry)), (128, 128, 128), 1)

cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\data\debug_measured.jpg", debug)
print(f"\nAnnotated debug image saved: data/debug_measured.jpg")
