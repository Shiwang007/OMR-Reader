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

print(f"Unique circles with min_dist=10.0: {len(circles)}")

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
    if not ys:
        print(f"[{label}] ERROR: No Y points found!")
        return []
    row_centers = cluster_1d(ys, tol=15)[:num_rows]
    
    rows = []
    for ry in row_centers:
        r_pts = [p for p in pts if abs(p[1] - ry) < 15]
        # Deduplicate points in same row closer than 20px
        r_unique = []
        for p in r_pts:
            if not any(abs(p[0] - u[0]) < 20.0 for u in r_unique):
                r_unique.append(p)
        r_pts = sorted(r_unique, key=lambda p: p[0])[:num_cols]
        if len(r_pts) < num_cols:
            print(f"[{label}] ROW WARN: Expected {num_cols} pts, got {len(r_pts)}")
        rows.append(r_pts)
    return rows

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
        "mcq_l": (1720, 1895), "mcq_r": (2100, 2275),
        "num_l": (1729, 1899), "num_r": (2119, 2289),
        "sec1_qs": [33, 34, 35, 36], "sec2_qs": [37, 38, 39, 40],
        "sec3_qs": [41, 42, 43, 44], "sec4_qs": [45, 46, 47, 48]
    }
]

for s in subjects_data:
    subj = s["name"]
    ml_min, ml_max = s["mcq_l"]
    mr_min, mr_max = s["mcq_r"]
    
    sec4_l_pts = [p for p in circles if ml_min < p[0] < ml_max and 3000 < p[1] < 3150]
    extract_row_pts(sec4_l_pts, 2, 4, f"{subj} Sec 4 Left")

    sec4_r_pts = [p for p in circles if mr_min < p[0] < mr_max and 3000 < p[1] < 3150]
    extract_row_pts(sec4_r_pts, 2, 4, f"{subj} Sec 4 Right")
