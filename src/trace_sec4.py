import cv2
import numpy as np

img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
_, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY_INV)

cnts, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

raw_circles = []
for c in cnts:
    (x, y), r = cv2.minEnclosingCircle(c)
    area = cv2.contourArea(c)
    if 10 < r < 20 and area > 100:
        raw_circles.append((float(x), float(y)))

circles = []
for p in raw_circles:
    if not any(np.hypot(p[0] - u[0], p[1] - u[1]) < 10.0 for u in circles):
        circles.append(p)

def cluster_1d(vals, tol=12):
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

def extract_row_pts(pts, num_rows, num_cols, label=""):
    ys = [p[1] for p in pts]
    row_centers = cluster_1d(ys, tol=15)[:num_rows]
    
    rows = []
    for ry in row_centers:
        r_pts = [p for p in pts if abs(p[1] - ry) < 15]
        r_unique = []
        for p in r_pts:
            if not any(abs(p[0] - u[0]) < 15.0 for u in r_unique):
                r_unique.append(p)
        r_pts = sorted(r_unique, key=lambda p: p[0])[:num_cols]
        print(f"[{label}] ry={ry:.1f} row pts count: {len(r_pts)}")
        rows.append(r_pts)
    return rows

subjects_data = [
    {
        "name": "Maths",
        "mcq_l": (190, 365), "mcq_r": (580, 770),
        "sec4_qs": [13, 14, 15, 16]
    },
    {
        "name": "Physics",
        "mcq_l": (950, 1125), "mcq_r": (1340, 1515),
        "sec4_qs": [29, 30, 31, 32]
    },
    {
        "name": "Chemistry",
        "mcq_l": (1720, 1895), "mcq_r": (2100, 2310),
        "sec4_qs": [45, 46, 47, 48]
    }
]

for s in subjects_data:
    subj = s["name"]
    ml_min, ml_max = s["mcq_l"]
    mr_min, mr_max = s["mcq_r"]
    
    sec4_r_pts = [p for p in circles if mr_min < p[0] < mr_max and 3000 < p[1] < 3150]
    sec4_r_rows = extract_row_pts(sec4_r_pts, 2, 4, f"{subj} Sec 4 Right")
    for q_i, q_num in enumerate(s["sec4_qs"][2:]):
        for opt_i, opt in enumerate(["A", "B", "C", "D"]):
            pt = sec4_r_rows[q_i][opt_i]
            print(f"  {subj} Q{q_num} opt {opt}: {pt}")
