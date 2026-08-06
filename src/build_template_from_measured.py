import cv2
import numpy as np
import json
import os

img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
_, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY_INV)

cnts, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

circles = []
for c in cnts:
    (x, y), r = cv2.minEnclosingCircle(c)
    area = cv2.contourArea(c)
    if 10 < r < 20 and area > 100:
        circles.append((float(x), float(y)))

print(f"Total bubble candidates from measure_all_grid_centers: {len(circles)}")

def find_nearest_bubble(target_x, target_y, candidate_pts, max_dist=25.0):
    best_pt = None
    best_dist = max_dist
    for (cx, cy) in candidate_pts:
        dist = np.hypot(cx - target_x, cy - target_y)
        if dist < best_dist:
            best_dist = dist
            best_pt = (cx, cy)
    if best_pt is not None:
        return round(best_pt[0], 1), round(best_pt[1], 1)
    else:
        # Fallback to target if slight occlusion/noise
        return round(target_x, 1), round(target_y, 1)

# Helper grid generators based on exact measured base anchors & step pitch
roll_start_x, roll_start_y = 157.0, 347.0
pitch = 46.1

# 1. Roll No Grid
roll_grid = []
for col in range(10):
    col_bubbles = []
    for val in range(10):
        tx = roll_start_x + col * pitch
        ty = roll_start_y + val * pitch
        bx, by = find_nearest_bubble(tx, ty, circles)
        col_bubbles.append({"val": str(val), "x": bx, "y": by})
    roll_grid.append(col_bubbles)

# Submap definitions
subjects = ["Maths", "Physics", "Chemistry"]
subj_offsets = {"Maths": 0.0, "Physics": 792.0, "Chemistry": 1584.0}

sec1_map = {"Maths": [1, 2, 3, 4], "Physics": [17, 18, 19, 20], "Chemistry": [33, 34, 35, 36]}
sec2_map = {"Maths": [5, 6, 7, 8], "Physics": [21, 22, 23, 24], "Chemistry": [37, 38, 39, 40]}
sec3_map = {"Maths": [9, 10, 11, 12], "Physics": [25, 26, 27, 28], "Chemistry": [41, 42, 43, 44]}
sec4_map = {"Maths": [13, 14, 15, 16], "Physics": [29, 30, 31, 32], "Chemistry": [45, 46, 47, 48]}

questions_template = {}

for subj in subjects:
    s_off = subj_offsets[subj]
    
    # Sec 1 (MCQ)
    for idx, q_num in enumerate(sec1_map[subj]):
        row_bubbles = []
        for opt_i, opt in enumerate(["A", "B", "C", "D"]):
            tx = 203.4 + s_off + opt_i * pitch
            ty = 968.0 + idx * pitch
            bx, by = find_nearest_bubble(tx, ty, circles)
            row_bubbles.append({"opt": opt, "x": bx, "y": by})
        questions_template[str(q_num)] = {"type": "mcq", "section": "1", "subject": subj, "bubbles": row_bubbles}

    # Sec 2 (MCQ)
    for idx, q_num in enumerate(sec2_map[subj]):
        row_bubbles = []
        for opt_i, opt in enumerate(["A", "B", "C", "D"]):
            tx = 594.8 + s_off + opt_i * pitch
            ty = 968.0 + idx * pitch
            bx, by = find_nearest_bubble(tx, ty, circles)
            row_bubbles.append({"opt": opt, "x": bx, "y": by})
        questions_template[str(q_num)] = {"type": "mcq", "section": "2", "subject": subj, "bubbles": row_bubbles}

    # Sec 3 (Numerical)
    sec3_qs = sec3_map[subj]
    # Q0: Left top
    q0_cols = []
    for d_col in range(4):
        col_b = []
        for val in range(10):
            tx = 157.0 + s_off + d_col * pitch
            ty = 1617.3 + val * pitch
            bx, by = find_nearest_bubble(tx, ty, circles)
            col_b.append({"val": str(val), "x": bx, "y": by})
        q0_cols.append(col_b)
    questions_template[str(sec3_qs[0])] = {"type": "numerical", "section": "3", "subject": subj, "columns": q0_cols}

    # Q1: Right top
    q1_cols = []
    for d_col in range(4):
        col_b = []
        for val in range(10):
            tx = 548.4 + s_off + d_col * pitch
            ty = 1617.3 + val * pitch
            bx, by = find_nearest_bubble(tx, ty, circles)
            col_b.append({"val": str(val), "x": bx, "y": by})
        q1_cols.append(col_b)
    questions_template[str(sec3_qs[1])] = {"type": "numerical", "section": "3", "subject": subj, "columns": q1_cols}

    # Q2: Left bottom
    q2_cols = []
    for d_col in range(4):
        col_b = []
        for val in range(10):
            tx = 157.0 + s_off + d_col * pitch
            ty = 2264.0 + val * pitch
            bx, by = find_nearest_bubble(tx, ty, circles)
            col_b.append({"val": str(val), "x": bx, "y": by})
        q2_cols.append(col_b)
    questions_template[str(sec3_qs[2])] = {"type": "numerical", "section": "3", "subject": subj, "columns": q2_cols}

    # Q3: Right bottom
    q3_cols = []
    for d_col in range(4):
        col_b = []
        for val in range(10):
            tx = 548.4 + s_off + d_col * pitch
            ty = 2264.0 + val * pitch
            bx, by = find_nearest_bubble(tx, ty, circles)
            col_b.append({"val": str(val), "x": bx, "y": by})
        q3_cols.append(col_b)
    questions_template[str(sec3_qs[3])] = {"type": "numerical", "section": "3", "subject": subj, "columns": q3_cols}

    # Sec 4 (MCQ)
    q_s4 = sec4_map[subj]
    for idx, q_num in enumerate(q_s4[:2]):
        row_bubbles = []
        for opt_i, opt in enumerate(["A", "B", "C", "D"]):
            tx = 203.4 + s_off + opt_i * pitch
            ty = 2984.0 + idx * 46.1
            bx, by = find_nearest_bubble(tx, ty, circles)
            row_bubbles.append({"opt": opt, "x": bx, "y": by})
        questions_template[str(q_num)] = {"type": "mcq", "section": "4", "subject": subj, "bubbles": row_bubbles}

    for idx, q_num in enumerate(q_s4[2:]):
        row_bubbles = []
        for opt_i, opt in enumerate(["A", "B", "C", "D"]):
            tx = 594.8 + s_off + opt_i * pitch
            ty = 2984.0 + idx * 46.1
            bx, by = find_nearest_bubble(tx, ty, circles)
            row_bubbles.append({"opt": opt, "x": bx, "y": by})
        questions_template[str(q_num)] = {"type": "mcq", "section": "4", "subject": subj, "bubbles": row_bubbles}

template_full = {
    "roll_number_grid": roll_grid,
    "questions": questions_template
}

out_path = r"f:\Medjeex\Medjeex-OMR-Engine\templates\jee_advanced_template.json"
with open(out_path, "w") as f:
    json.dump(template_full, f, indent=2)
print(f"Saved template built from measured circles to {out_path}")

# Draw overlay on canonical_warped.jpg
vis = img.copy()
for col in roll_grid:
    for b in col:
        cv2.circle(vis, (int(b['x']), int(b['y'])), 12, (255, 0, 0), 1)

for q_num, q_info in questions_template.items():
    if q_info['type'] == 'mcq':
        for b in q_info['bubbles']:
            cv2.circle(vis, (int(b['x']), int(b['y'])), 12, (0, 180, 0), 1)
    elif q_info['type'] == 'numerical':
        for col in q_info['columns']:
            for b in col:
                cv2.circle(vis, (int(b['x']), int(b['y'])), 12, (0, 0, 255), 1)

cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\output\template_overlay_verification.jpg", vis)
print("Saved template_overlay_verification.jpg")
