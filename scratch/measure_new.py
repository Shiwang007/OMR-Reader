"""
Precise OMR Grid Measurement Script
====================================
Measures all grid constants from Image (2).jpg
"""
import cv2
import numpy as np
import imutils

image_path = r"f:\Medjeex\Medjeex-OMR-Engine\omr\Image (2).jpg"
image = cv2.imread(image_path)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
h, w = gray.shape
print(f"Image size: {w} x {h}")

# ── Step 1: Find ALL wide horizontal lines ──
edges = cv2.Canny(gray, 50, 150)
h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (w // 4, 5))
detect_h = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, h_kernel)
cnts = imutils.grab_contours(cv2.findContours(detect_h, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE))

print("\n=== ALL WIDE HORIZONTAL LINES ===")
all_lines = []
for c in cnts:
    x, y, lw, lh = cv2.boundingRect(c)
    if lw > w * 0.3:
        all_lines.append((y, lw, lh))
all_lines.sort()
for i, (y, lw, lh) in enumerate(all_lines):
    print(f"  Line {i+1}: Y={y}, Width={lw}, Height={lh}")

# ── Step 2: Find bubbles using HoughCircles ──
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
circles = cv2.HoughCircles(
    blurred, cv2.HOUGH_GRADIENT,
    dp=1.2, minDist=25,
    param1=50, param2=28,
    minRadius=12, maxRadius=22
)

if circles is None:
    print("No circles found!")
    exit()

circles = np.round(circles[0]).astype(int)
print(f"\nTotal bubbles detected: {len(circles)}")

# ── Step 3: Find the Y where question bubbles START ──
# Sort all Y values and find the dense cluster
all_ys = sorted([c[1] for c in circles])
print(f"Min bubble Y: {all_ys[0]}, Max bubble Y: {all_ys[-1]}")

# Cluster Y values into rows
rows_y = []
curr = [all_ys[0]]
for y in all_ys[1:]:
    if y - curr[-1] < 15:
        curr.append(y)
    else:
        rows_y.append((np.mean(curr), len(curr)))
        curr = [y]
rows_y.append((np.mean(curr), len(curr)))

print(f"\n=== ALL DETECTED ROWS (Y, count) ===")
for i, (ry, rc) in enumerate(rows_y):
    marker = " <<< SMALL" if rc < 10 else ""
    print(f"  Row {i+1}: Y={ry:.1f} ({rc} bubbles){marker}")

# Filter to only rows with enough bubbles (16 = 4 subjects x 4 options)
question_rows = [(ry, rc) for ry, rc in rows_y if rc >= 12]
print(f"\n=== QUESTION ROWS ONLY (>= 12 bubbles) ===")
print(f"Total question rows: {len(question_rows)}")
if question_rows:
    print(f"First question row Y: {question_rows[0][0]:.1f}")
    print(f"Last question row Y: {question_rows[-1][0]:.1f}")
    if len(question_rows) > 1:
        pitches = [question_rows[i+1][0] - question_rows[i][0] for i in range(len(question_rows)-1)]
        print(f"Row pitch - min: {min(pitches):.1f}, max: {max(pitches):.1f}, avg: {np.mean(pitches):.1f}, median: {np.median(pitches):.1f}")

# ── Step 4: Column analysis ──
# Only use bubbles from question rows
first_q_y = question_rows[0][0] - 20 if question_rows else 0
last_q_y = question_rows[-1][0] + 20 if question_rows else h
q_circles = [c for c in circles if first_q_y <= c[1] <= last_q_y]

sorted_x = sorted(q_circles, key=lambda c: c[0])
columns = []
curr = [sorted_x[0]]
for c in sorted_x[1:]:
    if c[0] - curr[-1][0] < 20:
        curr.append(c)
    else:
        if len(curr) >= 10:
            columns.append(curr)
        curr = [c]
if len(curr) >= 10:
    columns.append(curr)

col_xs = [np.mean([c[0] for c in col]) for col in columns]
print(f"\n=== COLUMN CENTERS ({len(col_xs)} columns) ===")
for i, x in enumerate(col_xs):
    print(f"  Col {i+1}: X={x:.1f} ({len(columns[i])} bubbles)")

# ── Step 5: Subject grouping ──
if len(col_xs) >= 2:
    print(f"\n=== COLUMN GAPS ===")
    gaps = []
    for i in range(1, len(col_xs)):
        g = col_xs[i] - col_xs[i-1]
        gaps.append(g)
        marker = " <<<< SUBJECT BOUNDARY" if g > 100 else ""
        print(f"  Col{i} -> Col{i+1}: {g:.1f} px{marker}")

    # Group by subject boundary
    subject_groups = []
    curr_group = [0]
    for i, g in enumerate(gaps):
        if g > 100:
            subject_groups.append(curr_group)
            curr_group = [i+1]
        else:
            curr_group.append(i+1)
    subject_groups.append(curr_group)

    subjects = ["Physics", "Chemistry", "Biology I", "Biology II"]
    print(f"\n=== SUBJECT SUMMARY ===")
    for i, group in enumerate(subject_groups):
        name = subjects[i] if i < len(subjects) else f"Extra-{i}"
        x_vals = [col_xs[ci] for ci in group]
        print(f"\n  [{name}]")
        print(f"    Option A X: {x_vals[0]:.1f}")
        if len(x_vals) >= 4:
            print(f"    Option B X: {x_vals[1]:.1f}")
            print(f"    Option C X: {x_vals[2]:.1f}")
            print(f"    Option D X: {x_vals[3]:.1f}")
            spacings = [x_vals[j+1] - x_vals[j] for j in range(len(x_vals)-1)]
            print(f"    Avg option spacing: {np.mean(spacings):.1f}")

# ── Step 6: Final constants ──
if question_rows and len(col_xs) >= 16:
    print(f"\n{'='*60}")
    print(f"FINAL CALIBRATION CONSTANTS")
    print(f"{'='*60}")
    print(f"FIRST_ROW_Y = {question_rows[0][0]:.1f}")
    pitches = [question_rows[i+1][0] - question_rows[i][0] for i in range(len(question_rows)-1)]
    print(f"ROW_PITCH = {np.median(pitches):.2f}")
    print(f"NUM_ROWS = {len(question_rows)}")
    print(f"OPTION_SPACING = {np.mean([col_xs[1]-col_xs[0], col_xs[5]-col_xs[4], col_xs[9]-col_xs[8], col_xs[13]-col_xs[12]]):.1f}")
    
    for i, group in enumerate(subject_groups):
        if i < len(subjects):
            print(f"SUBJECT_{subjects[i].upper().replace(' ','_')}_X = {col_xs[group[0]]:.1f}")
