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
    if 9 < r < 18 and area > 120:
        circles.append((float(x), float(y)))

print(f"Total detected bubble candidates: {len(circles)}")

def sort_by_rows_and_cols(pts, num_cols, num_rows):
    # Sort into num_cols columns by X
    pts_by_x = sorted(pts, key=lambda p: p[0])
    cols = []
    chunk_size = len(pts) // num_cols
    for i in range(num_cols):
        col_pts = pts_by_x[i*chunk_size : (i+1)*chunk_size]
        # Sort each column vertically by Y
        col_pts = sorted(col_pts, key=lambda p: p[1])
        cols.append(col_pts)
    return cols

def extract_mcq_section(pts, q_nums):
    # pts has num_rows * 4 points
    # Sort into rows by Y
    sorted_pts = sorted(pts, key=lambda p: p[1])
    rows = []
    for r in range(len(q_nums)):
        row_pts = sorted_pts[r*4 : (r+1)*4]
        # Sort each row horizontally by X
        row_pts = sorted(row_pts, key=lambda p: p[0])
        rows.append(row_pts)
        
    q_dict = {}
    for r, q_num in enumerate(q_nums):
        bubbles = []
        for c, opt in enumerate(["A", "B", "C", "D"]):
            pt = rows[r][c]
            bubbles.append({"opt": opt, "x": round(pt[0], 1), "y": round(pt[1], 1)})
        q_dict[str(q_num)] = bubbles
    return q_dict

def extract_numerical_question(pts, q_num):
    # 40 points: 4 columns x 10 rows
    cols = sort_by_rows_and_cols(pts, num_cols=4, num_rows=10)
    q_cols = []
    for col in cols:
        col_bubbles = []
        for val, pt in enumerate(col):
            col_bubbles.append({"val": str(val), "x": round(pt[0], 1), "y": round(pt[1], 1)})
        q_cols.append(col_bubbles)
    return q_cols

# 1. Roll No Grid: 100 points
roll_pts = [p for p in circles if 130 < p[0] < 590 and 320 < p[1] < 780]
print(f"Roll No pts: {len(roll_pts)}")
roll_cols = sort_by_rows_and_cols(roll_pts, 10, 10)
roll_grid = []
for col in roll_cols:
    col_bubbles = []
    for val, pt in enumerate(col):
        col_bubbles.append({"val": str(val), "x": round(pt[0], 1), "y": round(pt[1], 1)})
    roll_grid.append(col_bubbles)

# Subjects mapping
subjects_data = [
    {
        "name": "Maths",
        "x_min": 100, "x_max": 800,
        "sec1_qs": [1, 2, 3, 4],
        "sec2_qs": [5, 6, 7, 8],
        "sec3_qs": [9, 10, 11, 12],
        "sec4_qs": [13, 14, 15, 16]
    },
    {
        "name": "Physics",
        "x_min": 850, "x_max": 1600,
        "sec1_qs": [17, 18, 19, 20],
        "sec2_qs": [21, 22, 23, 24],
        "sec3_qs": [25, 26, 27, 28],
        "sec4_qs": [29, 30, 31, 32]
    },
    {
        "name": "Chemistry",
        "x_min": 1600, "x_max": 2380,
        "sec1_qs": [33, 34, 35, 36],
        "sec2_qs": [37, 38, 39, 40],
        "sec3_qs": [41, 42, 43, 44],
        "sec4_qs": [45, 46, 47, 48]
    }
]

questions_template = {}

for s in subjects_data:
    subj = s["name"]
    xmin, xmax = s["x_min"], s["x_max"]
    mid_x = (xmin + xmax) / 2.0
    
    # Sec 1 (MCQ left)
    sec1_pts = [p for p in circles if xmin < p[0] < mid_x and 930 < p[1] < 1200]
    print(f"{subj} Sec 1 pts: {len(sec1_pts)}")
    sec1_dict = extract_mcq_section(sec1_pts, s["sec1_qs"])
    for q_num, bubbles in sec1_dict.items():
        questions_template[q_num] = {"type": "mcq", "section": "1", "subject": subj, "bubbles": bubbles}
        
    # Sec 2 (MCQ right)
    sec2_pts = [p for p in circles if mid_x < p[0] < xmax and 930 < p[1] < 1200]
    print(f"{subj} Sec 2 pts: {len(sec2_pts)}")
    sec2_dict = extract_mcq_section(sec2_pts, s["sec2_qs"])
    for q_num, bubbles in sec2_dict.items():
        questions_template[q_num] = {"type": "mcq", "section": "2", "subject": subj, "bubbles": bubbles}

    # Sec 3 Numerical (4 questions)
    # Q_top_left
    q_tl_pts = [p for p in circles if xmin < p[0] < mid_x and 1550 < p[1] < 2100]
    print(f"{subj} Sec 3 Q{s['sec3_qs'][0]} pts: {len(q_tl_pts)}")
    q_tl_cols = extract_numerical_question(q_tl_pts, s['sec3_qs'][0])
    questions_template[str(s['sec3_qs'][0])] = {"type": "numerical", "section": "3", "subject": subj, "columns": q_tl_cols}

    # Q_top_right
    q_tr_pts = [p for p in circles if mid_x < p[0] < xmax and 1550 < p[1] < 2100]
    print(f"{subj} Sec 3 Q{s['sec3_qs'][1]} pts: {len(q_tr_pts)}")
    q_tr_cols = extract_numerical_question(q_tr_pts, s['sec3_qs'][1])
    questions_template[str(s['sec3_qs'][1])] = {"type": "numerical", "section": "3", "subject": subj, "columns": q_tr_cols}

    # Q_bottom_left
    q_bl_pts = [p for p in circles if xmin < p[0] < mid_x and 2200 < p[1] < 2750]
    print(f"{subj} Sec 3 Q{s['sec3_qs'][2]} pts: {len(q_bl_pts)}")
    q_bl_cols = extract_numerical_question(q_bl_pts, s['sec3_qs'][2])
    questions_template[str(s['sec3_qs'][2])] = {"type": "numerical", "section": "3", "subject": subj, "columns": q_bl_cols}

    # Q_bottom_right
    q_br_pts = [p for p in circles if mid_x < p[0] < xmax and 2200 < p[1] < 2750]
    print(f"{subj} Sec 3 Q{s['sec3_qs'][3]} pts: {len(q_br_pts)}")
    q_br_cols = extract_numerical_question(q_br_pts, s['sec3_qs'][3])
    questions_template[str(s['sec3_qs'][3])] = {"type": "numerical", "section": "3", "subject": subj, "columns": q_br_cols}

    # Sec 4 (MCQ bottom)
    # Q_left (2 questions)
    sec4_l_pts = [p for p in circles if xmin < p[0] < mid_x and 2950 < p[1] < 3250]
    print(f"{subj} Sec 4 Left pts: {len(sec4_l_pts)}")
    sec4_l_dict = extract_mcq_section(sec4_l_pts, s["sec4_qs"][:2])
    for q_num, bubbles in sec4_l_dict.items():
        questions_template[q_num] = {"type": "mcq", "section": "4", "subject": subj, "bubbles": bubbles}

    # Q_right (2 questions)
    sec4_r_pts = [p for p in circles if mid_x < p[0] < xmax and 2950 < p[1] < 3250]
    print(f"{subj} Sec 4 Right pts: {len(sec4_r_pts)}")
    sec4_r_dict = extract_mcq_section(sec4_r_pts, s["sec4_qs"][2:])
    for q_num, bubbles in sec4_r_dict.items():
        questions_template[q_num] = {"type": "mcq", "section": "4", "subject": subj, "bubbles": bubbles}

template_full = {
    "roll_number_grid": roll_grid,
    "questions": questions_template
}

out_path = r"f:\Medjeex\Medjeex-OMR-Engine\templates\jee_advanced_template.json"
with open(out_path, "w") as f:
    json.dump(template_full, f, indent=2)
print(f"\nSaved EXACT MEASURED template to {out_path}")

# Overlay verification image
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
print("Saved EXACT template overlay verification to output/template_overlay_verification.jpg")
