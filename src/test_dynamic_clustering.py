import cv2
import numpy as np
import json

def detect_bubbles_dynamically(canonical_img):
    gray = cv2.cvtColor(canonical_img, cv2.COLOR_BGR2GRAY) if len(canonical_img.shape) == 3 else canonical_img
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY_INV)
    cnts, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    circles = []
    for c in cnts:
        (x, y), r = cv2.minEnclosingCircle(c)
        area = cv2.contourArea(c)
        if 10 < r < 20 and area > 100:
            circles.append((float(x), float(y)))
    return circles

def cluster_1d(vals, tol=15):
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

def extract_4col_10row_question(pts):
    # pts has bubbles for a numerical matrix
    # First, cluster X coordinates into 4 column centers
    xs = [p[0] for p in pts]
    col_centers = cluster_1d(xs, tol=15)
    if len(col_centers) > 4:
        # take the 4 main columns (ignore small overflow points)
        col_centers = col_centers[:4]
        
    cols = []
    for cx in col_centers:
        # filter points belonging to this column
        col_pts = [p for p in pts if abs(p[0] - cx) < 15]
        # sort vertically by Y
        col_pts = sorted(col_pts, key=lambda p: p[1])
        # take top 10 bubbles (values 0 to 9)
        col_pts = col_pts[:10]
        cols.append(col_pts)
    return cols

def extract_roll_number_grid(pts):
    xs = [p[0] for p in pts]
    col_centers = cluster_1d(xs, tol=15)[:10]
    cols = []
    for cx in col_centers:
        col_pts = [p for p in pts if abs(p[0] - cx) < 15]
        col_pts = sorted(col_pts, key=lambda p: p[1])[:10]
        cols.append(col_pts)
    return cols

def extract_mcq_section(pts, num_qs):
    # Group by Y into num_qs rows
    ys = [p[1] for p in pts]
    row_centers = cluster_1d(ys, tol=15)[:num_qs]
    rows = []
    for ry in row_centers:
        row_pts = [p for p in pts if abs(p[1] - ry) < 15]
        row_pts = sorted(row_pts, key=lambda p: p[0])[:4]
        rows.append(row_pts)
    return rows

def build_dynamic_grid(circles):
    # 1. Roll No grid (100 bubbles)
    roll_pts = [p for p in circles if 130 < p[0] < 590 and 320 < p[1] < 780]
    roll_cols_pts = extract_roll_number_grid(roll_pts)
    roll_grid = []
    for col_pts in roll_cols_pts:
        col_bubbles = []
        for val, pt in enumerate(col_pts):
            col_bubbles.append({"val": str(val), "x": round(pt[0], 1), "y": round(pt[1], 1)})
        roll_grid.append(col_bubbles)

    subjects_data = [
        {
            "name": "Maths",
            "x_left": (140, 450), "x_right": (520, 800),
            "sec1_qs": [1, 2, 3, 4], "sec2_qs": [5, 6, 7, 8],
            "sec3_qs": [9, 10, 11, 12], "sec4_qs": [13, 14, 15, 16]
        },
        {
            "name": "Physics",
            "x_left": (930, 1240), "x_right": (1310, 1590),
            "sec1_qs": [17, 18, 19, 20], "sec2_qs": [21, 22, 23, 24],
            "sec3_qs": [25, 26, 27, 28], "sec4_qs": [29, 30, 31, 32]
        },
        {
            "name": "Chemistry",
            "x_left": (1720, 2030), "x_right": (2100, 2380),
            "sec1_qs": [33, 34, 35, 36], "sec2_qs": [37, 38, 39, 40],
            "sec3_qs": [41, 42, 43, 44], "sec4_qs": [45, 46, 47, 48]
        }
    ]

    questions_template = {}

    for s in subjects_data:
        subj = s["name"]
        xl_min, xl_max = s["x_left"]
        xr_min, xr_max = s["x_right"]
        
        # Sec 1 (MCQ left)
        sec1_pts = [p for p in circles if xl_min < p[0] < xl_max and 980 < p[1] < 1320]
        sec1_rows = extract_mcq_section(sec1_pts, 4)
        for q_i, q_num in enumerate(s["sec1_qs"]):
            bubbles = []
            for opt_i, opt in enumerate(["A", "B", "C", "D"]):
                pt = sec1_rows[q_i][opt_i]
                bubbles.append({"opt": opt, "x": round(pt[0], 1), "y": round(pt[1], 1)})
            questions_template[str(q_num)] = {"type": "mcq", "section": "1", "subject": subj, "bubbles": bubbles}

        # Sec 2 (MCQ right)
        sec2_pts = [p for p in circles if xr_min < p[0] < xr_max and 980 < p[1] < 1320]
        sec2_rows = extract_mcq_section(sec2_pts, 4)
        for q_i, q_num in enumerate(s["sec2_qs"]):
            bubbles = []
            for opt_i, opt in enumerate(["A", "B", "C", "D"]):
                pt = sec2_rows[q_i][opt_i]
                bubbles.append({"opt": opt, "x": round(pt[0], 1), "y": round(pt[1], 1)})
            questions_template[str(q_num)] = {"type": "mcq", "section": "2", "subject": subj, "bubbles": bubbles}

        # Sec 3 (Numerical)
        # Q0: Left top
        q0_pts = [p for p in circles if xl_min < p[0] < xl_max and 1600 < p[1] < 2120]
        q0_cols_pts = extract_4col_10row_question(q0_pts)
        q0_cols = []
        for col_pts in q0_cols_pts:
            q0_cols.append([{"val": str(v), "x": round(pt[0], 1), "y": round(pt[1], 1)} for v, pt in enumerate(col_pts)])
        questions_template[str(s["sec3_qs"][0])] = {"type": "numerical", "section": "3", "subject": subj, "columns": q0_cols}

        # Q1: Right top
        q1_pts = [p for p in circles if xr_min < p[0] < xr_max and 1600 < p[1] < 2120]
        q1_cols_pts = extract_4col_10row_question(q1_pts)
        q1_cols = []
        for col_pts in q1_cols_pts:
            q1_cols.append([{"val": str(v), "x": round(pt[0], 1), "y": round(pt[1], 1)} for v, pt in enumerate(col_pts)])
        questions_template[str(s["sec3_qs"][1])] = {"type": "numerical", "section": "3", "subject": subj, "columns": q1_cols}

        # Q2: Left bottom
        q2_pts = [p for p in circles if xl_min < p[0] < xl_max and 2240 < p[1] < 2760]
        q2_cols_pts = extract_4col_10row_question(q2_pts)
        q2_cols = []
        for col_pts in q2_cols_pts:
            q2_cols.append([{"val": str(v), "x": round(pt[0], 1), "y": round(pt[1], 1)} for v, pt in enumerate(col_pts)])
        questions_template[str(s["sec3_qs"][2])] = {"type": "numerical", "section": "3", "subject": subj, "columns": q2_cols}

        # Q3: Right bottom
        q3_pts = [p for p in circles if xr_min < p[0] < xr_max and 2240 < p[1] < 2760]
        q3_cols_pts = extract_4col_10row_question(q3_pts)
        q3_cols = []
        for col_pts in q3_cols_pts:
            q3_cols.append([{"val": str(v), "x": round(pt[0], 1), "y": round(pt[1], 1)} for v, pt in enumerate(col_pts)])
        questions_template[str(s["sec3_qs"][3])] = {"type": "numerical", "section": "3", "subject": subj, "columns": q3_cols}

        # Sec 4 (MCQ bottom)
        sec4_l_pts = [p for p in circles if xl_min < p[0] < xl_max and 2980 < p[1] < 3200]
        sec4_l_rows = extract_mcq_section(sec4_l_pts, 2)
        for q_i, q_num in enumerate(s["sec4_qs"][:2]):
            bubbles = []
            for opt_i, opt in enumerate(["A", "B", "C", "D"]):
                pt = sec4_l_rows[q_i][opt_i]
                bubbles.append({"opt": opt, "x": round(pt[0], 1), "y": round(pt[1], 1)})
            questions_template[str(q_num)] = {"type": "mcq", "section": "4", "subject": subj, "bubbles": bubbles}

        sec4_r_pts = [p for p in circles if xr_min < p[0] < xr_max and 2980 < p[1] < 3200]
        sec4_r_rows = extract_mcq_section(sec4_r_pts, 2)
        for q_i, q_num in enumerate(s["sec4_qs"][2:]):
            bubbles = []
            for opt_i, opt in enumerate(["A", "B", "C", "D"]):
                pt = sec4_r_rows[q_i][opt_i]
                bubbles.append({"opt": opt, "x": round(pt[0], 1), "y": round(pt[1], 1)})
            questions_template[str(q_num)] = {"type": "mcq", "section": "4", "subject": subj, "bubbles": bubbles}

    return {
        "roll_number_grid": roll_grid,
        "questions": questions_template
    }

# Test script
img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped.jpg")
circles = detect_bubbles_dynamically(img)
print(f"Total dynamic circles detected: {len(circles)}")

template_full = build_dynamic_grid(circles)

out_path = r"f:\Medjeex\Medjeex-OMR-Engine\templates\jee_advanced_template.json"
with open(out_path, "w") as f:
    json.dump(template_full, f, indent=2)
print(f"Saved PERFECT DYNAMIC TEMPLATE to {out_path}")

# Draw overlay directly on canonical_warped.jpg
vis = img.copy()
for col in template_full["roll_number_grid"]:
    for b in col:
        cv2.circle(vis, (int(b['x']), int(b['y'])), 12, (255, 0, 0), 1)

for q_num, q_info in template_full["questions"].items():
    if q_info['type'] == 'mcq':
        for b in q_info['bubbles']:
            cv2.circle(vis, (int(b['x']), int(b['y'])), 12, (0, 180, 0), 1)
    elif q_info['type'] == 'numerical':
        for col in q_info['columns']:
            for b in col:
                cv2.circle(vis, (int(b['x']), int(b['y'])), 12, (0, 0, 255), 1)

cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\output\template_overlay_verification.jpg", vis)
print("Saved PERFECT DYNAMIC template_overlay_verification.jpg")
