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

print(f"Total circles found: {len(circles)}")

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

def match_grid_points(pts, expected_cols, expected_rows, label=""):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    
    row_centers = cluster_1d(ys, tol=15)
    col_centers = cluster_1d(xs, tol=15)
    
    if len(row_centers) != expected_rows or len(col_centers) != expected_cols:
        print(f"[{label}] Expected {expected_rows} rows, {expected_cols} cols; Got {len(row_centers)} rows, {len(col_centers)} cols")
        
    grid = []
    for r_y in row_centers[:expected_rows]:
        row_bubbles = []
        for c_x in col_centers[:expected_cols]:
            best_pt = min(pts, key=lambda p: (p[0]-c_x)**2 + (p[1]-r_y)**2)
            row_bubbles.append((round(best_pt[0], 1), round(best_pt[1], 1)))
        grid.append(row_bubbles)
    return grid

# 1. Roll No Grid
roll_pts = [p for p in circles if 140 < p[0] < 585 and 330 < p[1] < 775]
roll_grid_pts = match_grid_points(roll_pts, 10, 10, label="Roll No")
roll_grid = []
for c_i in range(10):
    col_b = []
    for r_i in range(10):
        pt = roll_grid_pts[r_i][c_i]
        col_b.append({"val": str(r_i), "x": pt[0], "y": pt[1]})
    roll_grid.append(col_b)

subjects_data = [
    {
        "name": "Maths",
        "mcq_l": (190, 365), "mcq_r": (580, 755),
        "num_l": (145, 315), "num_r": (535, 705),
        "sec1_qs": [1, 2, 3, 4], "sec2_qs": [5, 6, 7, 8],
        "sec3_qs": [9, 10, 11, 12], "sec4_qs": [13, 14, 15, 16]
    },
    {
        "name": "Physics",
        "mcq_l": (980, 1155), "mcq_r": (1370, 1545),
        "num_l": (937, 1107), "num_r": (1327, 1497),
        "sec1_qs": [17, 18, 19, 20], "sec2_qs": [21, 22, 23, 24],
        "sec3_qs": [25, 26, 27, 28], "sec4_qs": [29, 30, 31, 32]
    },
    {
        "name": "Chemistry",
        "mcq_l": (1770, 1945), "mcq_r": (2160, 2335),
        "num_l": (1729, 1899), "num_r": (2119, 2289),
        "sec1_qs": [33, 34, 35, 36], "sec2_qs": [37, 38, 39, 40],
        "sec3_qs": [41, 42, 43, 44], "sec4_qs": [45, 46, 47, 48]
    }
]

questions_template = {}

for s in subjects_data:
    subj = s["name"]
    ml_min, ml_max = s["mcq_l"]
    mr_min, mr_max = s["mcq_r"]
    nl_min, nl_max = s["num_l"]
    nr_min, nr_max = s["num_r"]
    
    # Sec 1 (MCQ left)
    sec1_pts = [p for p in circles if ml_min < p[0] < ml_max and 900 < p[1] < 1250]
    sec1_grid = match_grid_points(sec1_pts, 4, 4, label=f"{subj} Sec 1")
    for q_i, q_num in enumerate(s["sec1_qs"]):
        bubbles = []
        for opt_i, opt in enumerate(["A", "B", "C", "D"]):
            pt = sec1_grid[q_i][opt_i]
            bubbles.append({"opt": opt, "x": pt[0], "y": pt[1]})
        questions_template[str(q_num)] = {"type": "mcq", "section": "1", "subject": subj, "bubbles": bubbles}

    # Sec 2 (MCQ right)
    sec2_pts = [p for p in circles if mr_min < p[0] < mr_max and 900 < p[1] < 1250]
    sec2_grid = match_grid_points(sec2_pts, 4, 4, label=f"{subj} Sec 2")
    for q_i, q_num in enumerate(s["sec2_qs"]):
        bubbles = []
        for opt_i, opt in enumerate(["A", "B", "C", "D"]):
            pt = sec2_grid[q_i][opt_i]
            bubbles.append({"opt": opt, "x": pt[0], "y": pt[1]})
        questions_template[str(q_num)] = {"type": "mcq", "section": "2", "subject": subj, "bubbles": bubbles}

    # Sec 3 Numerical
    # Q0: Left top
    q0_pts = [p for p in circles if nl_min < p[0] < nl_max and 1600 < p[1] < 2100]
    q0_grid = match_grid_points(q0_pts, 4, 10, label=f"{subj} Sec 3 Q{s['sec3_qs'][0]}")
    q0_cols = []
    for c_i in range(4):
        col_b = []
        for r_i in range(10):
            pt = q0_grid[r_i][c_i]
            col_b.append({"val": str(r_i), "x": pt[0], "y": pt[1]})
        q0_cols.append(col_b)
    questions_template[str(s["sec3_qs"][0])] = {"type": "numerical", "section": "3", "subject": subj, "columns": q0_cols}

    # Q1: Right top
    q1_pts = [p for p in circles if nr_min < p[0] < nr_max and 1600 < p[1] < 2100]
    q1_grid = match_grid_points(q1_pts, 4, 10, label=f"{subj} Sec 3 Q{s['sec3_qs'][1]}")
    q1_cols = []
    for c_i in range(4):
        col_b = []
        for r_i in range(10):
            pt = q1_grid[r_i][c_i]
            col_b.append({"val": str(r_i), "x": pt[0], "y": pt[1]})
        q1_cols.append(col_b)
    questions_template[str(s["sec3_qs"][1])] = {"type": "numerical", "section": "3", "subject": subj, "columns": q1_cols}

    # Q2: Left bottom
    q2_pts = [p for p in circles if nl_min < p[0] < nl_max and 2250 < p[1] < 2750]
    q2_grid = match_grid_points(q2_pts, 4, 10, label=f"{subj} Sec 3 Q{s['sec3_qs'][2]}")
    q2_cols = []
    for c_i in range(4):
        col_b = []
        for r_i in range(10):
            pt = q2_grid[r_i][c_i]
            col_b.append({"val": str(r_i), "x": pt[0], "y": pt[1]})
        q2_cols.append(col_b)
    questions_template[str(s["sec3_qs"][2])] = {"type": "numerical", "section": "3", "subject": subj, "columns": q2_cols}

    # Q3: Right bottom
    q3_pts = [p for p in circles if nr_min < p[0] < nr_max and 2250 < p[1] < 2750]
    q3_grid = match_grid_points(q3_pts, 4, 10, label=f"{subj} Sec 3 Q{s['sec3_qs'][3]}")
    q3_cols = []
    for c_i in range(4):
        col_b = []
        for r_i in range(10):
            pt = q3_grid[r_i][c_i]
            col_b.append({"val": str(r_i), "x": pt[0], "y": pt[1]})
        q3_cols.append(col_b)
    questions_template[str(s["sec3_qs"][3])] = {"type": "numerical", "section": "3", "subject": subj, "columns": q3_cols}

    # Sec 4 (MCQ bottom)
    sec4_l_pts = [p for p in circles if ml_min < p[0] < ml_max and 2950 < p[1] < 3200]
    sec4_l_grid = match_grid_points(sec4_l_pts, 4, 2, label=f"{subj} Sec 4 Left")
    for q_i, q_num in enumerate(s["sec4_qs"][:2]):
        bubbles = []
        for opt_i, opt in enumerate(["A", "B", "C", "D"]):
            pt = sec4_l_grid[q_i][opt_i]
            bubbles.append({"opt": opt, "x": pt[0], "y": pt[1]})
        questions_template[str(q_num)] = {"type": "mcq", "section": "4", "subject": subj, "bubbles": bubbles}

    sec4_r_pts = [p for p in circles if mr_min < p[0] < mr_max and 2950 < p[1] < 3200]
    sec4_r_grid = match_grid_points(sec4_r_pts, 4, 2, label=f"{subj} Sec 4 Right")
    for q_i, q_num in enumerate(s["sec4_qs"][2:]):
        bubbles = []
        for opt_i, opt in enumerate(["A", "B", "C", "D"]):
            pt = sec4_r_grid[q_i][opt_i]
            bubbles.append({"opt": opt, "x": pt[0], "y": pt[1]})
        questions_template[str(q_num)] = {"type": "mcq", "section": "4", "subject": subj, "bubbles": bubbles}

template_full = {
    "roll_number_grid": roll_grid,
    "questions": questions_template
}

out_path = r"f:\Medjeex\Medjeex-OMR-Engine\templates\jee_advanced_template.json"
with open(out_path, "w") as f:
    json.dump(template_full, f, indent=2)
print(f"\nSaved PERFECT template from exact contour centroids to {out_path}")

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
print("Saved PERFECT template_overlay_verification.jpg")
