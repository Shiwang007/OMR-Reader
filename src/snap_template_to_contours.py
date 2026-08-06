import cv2
import numpy as np
import json

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

def snap_to_closest(tx, ty, max_radius=18.0):
    best_pt = None
    best_d = max_radius
    for (cx, cy) in circles:
        d = np.hypot(cx - tx, cy - ty)
        if d < best_d:
            best_d = d
            best_pt = (cx, cy)
    if best_pt is not None:
        return round(best_pt[0], 1), round(best_pt[1], 1)
    else:
        return round(tx, 1), round(ty, 1)

# 1. Roll No Grid
roll_start_x, roll_start_y = 157.0, 347.0
pitch = 46.1

roll_grid = []
for col in range(10):
    col_b = []
    for val in range(10):
        tx = roll_start_x + col * pitch
        ty = roll_start_y + val * pitch
        bx, by = snap_to_closest(tx, ty)
        col_b.append({"val": str(val), "x": bx, "y": by})
    roll_grid.append(col_b)

subjects = ["Maths", "Physics", "Chemistry"]
subj_offsets = {"Maths": 0.0, "Physics": 792.0, "Chemistry": 1584.0}

sec1_map = {"Maths": [1, 2, 3, 4], "Physics": [17, 18, 19, 20], "Chemistry": [33, 34, 35, 36]}
sec2_map = {"Maths": [5, 6, 7, 8], "Physics": [21, 22, 23, 24], "Chemistry": [37, 38, 39, 40]}
sec3_map = {"Maths": [9, 10, 11, 12], "Physics": [25, 26, 27, 28], "Chemistry": [41, 42, 43, 44]}
sec4_map = {"Maths": [13, 14, 15, 16], "Physics": [29, 30, 31, 32], "Chemistry": [45, 46, 47, 48]}

questions_template = {}

for subj in subjects:
    s_off = subj_offsets[subj]
    
    # Sec 1 & 2 MCQs (Q1..4 and Q5..8): Y centers are 1014.8, 1109.0, 1201.8, 1294.6
    sec1_ys = [1014.8, 1109.0, 1201.8, 1294.6]
    sec2_ys = [1014.8, 1109.0, 1201.8, 1294.6]
    
    for idx, q_num in enumerate(sec1_map[subj]):
        row_b = []
        for opt_i, opt in enumerate(["A", "B", "C", "D"]):
            tx = 203.4 + s_off + opt_i * pitch
            ty = sec1_ys[idx]
            bx, by = snap_to_closest(tx, ty)
            row_b.append({"opt": opt, "x": bx, "y": by})
        questions_template[str(q_num)] = {"type": "mcq", "section": "1", "subject": subj, "bubbles": row_b}

    for idx, q_num in enumerate(sec2_map[subj]):
        row_b = []
        for opt_i, opt in enumerate(["A", "B", "C", "D"]):
            tx = 594.8 + s_off + opt_i * pitch
            ty = sec2_ys[idx]
            bx, by = snap_to_closest(tx, ty)
            row_b.append({"opt": opt, "x": bx, "y": by})
        questions_template[str(q_num)] = {"type": "mcq", "section": "2", "subject": subj, "bubbles": row_b}

    # Sec 3 (Numerical)
    sec3_qs = sec3_map[subj]
    q0_cols = []
    for d_col in range(4):
        col_b = []
        for val in range(10):
            tx = 157.0 + s_off + d_col * pitch
            ty = 1663.4 + val * pitch
            bx, by = snap_to_closest(tx, ty)
            col_b.append({"val": str(val), "x": bx, "y": by})
        q0_cols.append(col_b)
    questions_template[str(sec3_qs[0])] = {"type": "numerical", "section": "3", "subject": subj, "columns": q0_cols}

    q1_cols = []
    for d_col in range(4):
        col_b = []
        for val in range(10):
            tx = 548.4 + s_off + d_col * pitch
            ty = 1663.4 + val * pitch
            bx, by = snap_to_closest(tx, ty)
            col_b.append({"val": str(val), "x": bx, "y": by})
        q1_cols.append(col_b)
    questions_template[str(sec3_qs[1])] = {"type": "numerical", "section": "3", "subject": subj, "columns": q1_cols}

    q2_cols = []
    for d_col in range(4):
        col_b = []
        for val in range(10):
            tx = 157.0 + s_off + d_col * pitch
            ty = 2310.1 + val * pitch
            bx, by = snap_to_closest(tx, ty)
            col_b.append({"val": str(val), "x": bx, "y": by})
        q2_cols.append(col_b)
    questions_template[str(sec3_qs[2])] = {"type": "numerical", "section": "3", "subject": subj, "columns": q2_cols}

    q3_cols = []
    for d_col in range(4):
        col_b = []
        for val in range(10):
            tx = 548.4 + s_off + d_col * pitch
            ty = 2310.1 + val * pitch
            bx, by = snap_to_closest(tx, ty)
            col_b.append({"val": str(val), "x": bx, "y": by})
        q3_cols.append(col_b)
    questions_template[str(sec3_qs[3])] = {"type": "numerical", "section": "3", "subject": subj, "columns": q3_cols}

    # Sec 4 (MCQ) - Q13/14 Y centers: 3029.0, 3122.5
    sec4_ys = [3029.0, 3122.5]
    q_s4 = sec4_map[subj]
    for idx, q_num in enumerate(q_s4[:2]):
        row_b = []
        for opt_i, opt in enumerate(["A", "B", "C", "D"]):
            tx = 203.4 + s_off + opt_i * pitch
            ty = sec4_ys[idx]
            bx, by = snap_to_closest(tx, ty)
            row_b.append({"opt": opt, "x": bx, "y": by})
        questions_template[str(q_num)] = {"type": "mcq", "section": "4", "subject": subj, "bubbles": row_b}

    for idx, q_num in enumerate(q_s4[2:]):
        row_b = []
        for opt_i, opt in enumerate(["A", "B", "C", "D"]):
            tx = 594.8 + s_off + opt_i * pitch
            ty = sec4_ys[idx]
            bx, by = snap_to_closest(tx, ty)
            row_b.append({"opt": opt, "x": bx, "y": by})
        questions_template[str(q_num)] = {"type": "mcq", "section": "4", "subject": subj, "bubbles": row_b}

template_full = {
    "roll_number_grid": roll_grid,
    "questions": questions_template
}

out_path = r"f:\Medjeex\Medjeex-OMR-Engine\templates\jee_advanced_template.json"
with open(out_path, "w") as f:
    json.dump(template_full, f, indent=2)
print(f"Successfully generated template by snapping to measured circle centroids: {out_path}")

# Overlay verification
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
