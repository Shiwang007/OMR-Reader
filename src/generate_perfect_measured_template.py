"""
Generate JEE Advanced OMR template by detecting ALL bubble centroids from
canonical_warped.jpg using the EXACT same method as measure_all_grid_centers.py.

Key difference from prior version:
  - Numerical questions now capture ALL 6 digit columns (4 integer + 2 decimal)
  - Verification overlay draws every detected bubble with its actual radius,
    producing output identical to measured_all_bubbles.jpg
  - Wider region bounds derived from the diagnostic dump of actual centroid X positions
"""
import cv2
import numpy as np
import json

img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
_, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY_INV)
cnts, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# Step 1: detect all circle-like contours (same filter as measure_all_grid_centers.py)
all_raw = []
for c in cnts:
    (x, y), r = cv2.minEnclosingCircle(c)
    area = cv2.contourArea(c)
    if 10 < r < 20 and area > 100:
        all_raw.append((float(x), float(y), float(r)))

# Step 2: dedup concentric rings (inner/outer contours of same bubble)
circles = []  # (x, y, r) - keeping radius for verification drawing
for p in all_raw:
    if not any(np.hypot(p[0] - u[0], p[1] - u[1]) < 10.0 for u in circles):
        circles.append(p)

print(f"Raw contours: {len(all_raw)}, unique bubbles: {len(circles)}")

# ── helpers ──────────────────────────────────────────────────────────────────

def cluster_1d(vals, tol=12):
    vals = sorted(vals)
    if not vals: return []
    clusters = []
    curr = [vals[0]]
    for v in vals[1:]:
        if v - curr[-1] <= tol:
            curr.append(v)
        else:
            clusters.append(float(sum(curr)/len(curr)))
            curr = [v]
    clusters.append(float(sum(curr)/len(curr)))
    return sorted(clusters)

def get_10_rows(ys):
    """Robustly extract exactly 10 digit rows by looking for the correct physical height span (~414 pixels)."""
    if len(ys) <= 10:
        return ys[-10:]
    
    best_subset = None
    best_error = float('inf')
    
    for i in range(len(ys) - 9):
        subset = ys[i:i+10]
        span = subset[-1] - subset[0]
        error = abs(span - 415.0) # 9 gaps of ~46.1 pixels = 415
        
        # Check max internal gap to avoid skipping a real digit row
        max_gap = max(subset[j] - subset[j-1] for j in range(1, 10))
        if max_gap > 55:
            continue
            
        if error < best_error:
            best_error = error
            best_subset = subset
            
    return best_subset if best_subset else ys[-10:]


def extract_grid_rows(pts, num_rows, num_cols, pitch_x=46.1):
    """Cluster points into rows by Y, then within each row sort by X.
    Uses globally detected X columns to ensure missing left bubbles don't shift the row."""
    if not pts:
        return [[(0, 0)] * num_cols] * num_rows

    ys = [p[1] for p in pts]
    xs = [p[0] for p in pts]
    
    row_centers = cluster_1d(ys, tol=15)[:num_rows]
    col_centers = cluster_1d(xs, tol=15)[:num_cols]

    rows = []
    for ry in row_centers:
        r_pts = [p for p in pts if abs(p[1] - ry) < 15]
        
        # Snap each point to the nearest global col_center
        slots = [None] * num_cols
        for p in r_pts:
            # find closest col_center
            best_cidx = min(range(len(col_centers)), key=lambda i: abs(col_centers[i] - p[0]))
            if abs(col_centers[best_cidx] - p[0]) < 15:
                slots[best_cidx] = p
                
        # Fill in missing slots with col_center X and current row Y
        for i in range(num_cols):
            if slots[i] is None:
                # If a whole column is missing from col_centers, extrapolate from others
                if i < len(col_centers):
                    cx = col_centers[i]
                else:
                    cx = col_centers[0] + i * pitch_x if col_centers else 0
                slots[i] = (round(cx, 1), round(ry, 1))

        rows.append(slots[:num_cols])
    return rows


def extract_grid_cols(pts, num_cols, num_rows, pitch_y=46.1):
    """Cluster points into columns by X, then within each column sort by Y."""
    if not pts:
        return [[(0, 0)] * num_rows] * num_cols

    xs = [p[0] for p in pts]
    col_centers = cluster_1d(xs, tol=15)[:num_cols]

    cols = []
    for cx in col_centers:
        c_pts = [p for p in pts if abs(p[0] - cx) < 15]
        unique = []
        for p in c_pts:
            if not any(abs(p[1] - u[1]) < 15.0 for u in unique):
                unique.append(p)
        unique.sort(key=lambda p: p[1])

        # interpolate missing rows
        if len(unique) < num_rows and unique:
            if len(unique) >= 2:
                actual_pitch = (unique[-1][1] - unique[0][1]) / (len(unique) - 1)
                if actual_pitch < 20:
                    actual_pitch = pitch_y
            else:
                actual_pitch = pitch_y
            ref = unique[0]
            slots = [None] * num_rows
            for p in unique:
                idx = int(round((p[1] - ref[1]) / actual_pitch))
                if 0 <= idx < num_rows:
                    slots[idx] = p
            ref_idx = next(i for i, s in enumerate(slots) if s is not None)
            ref_pt = slots[ref_idx]
            for i in range(num_rows):
                if slots[i] is None:
                    slots[i] = (round(ref_pt[0], 1),
                                round(ref_pt[1] + (i - ref_idx) * actual_pitch, 1))
            unique = slots

        cols.append(unique[:num_rows])
    return cols


def pts_in_box(x1, x2, y1, y2):
    """Filter deduped circles to (x, y) tuples inside a bounding box."""
    return [(p[0], p[1]) for p in circles if x1 < p[0] < x2 and y1 < p[1] < y2]


# ── 1. Roll Number Grid ─────────────────────────────────────────────────────
roll_pts = pts_in_box(140, 585, 330, 775)
roll_cols = extract_grid_cols(roll_pts, 10, 10)
roll_grid = []
for col in roll_cols:
    roll_grid.append([{"val": str(v), "x": round(pt[0], 1), "y": round(pt[1], 1)}
                      for v, pt in enumerate(col)])

# ── 2. Question definitions ─────────────────────────────────────────────────
# Region bounds derived from diagnostic X-coordinate analysis:
#
# MATHS:
#   MCQ  left  cols: X ~ 203, 249, 296, 342   -> x_range (190, 360)
#   MCQ  right cols: X ~ 594, 640, 687, 733   -> x_range (580, 750)
#   Num  LT cols:    X ~ 157, 203, 249, 295, [gap], 365  -> x_range (140, 380)
#   Num  RT cols:    X ~ 526, 572, 618, 663, [gap], 733  -> x_range (510, 750)
#
# PHYSICS:
#   MCQ  left  cols: same pattern offset +760px
#   Num  LT cols:    X ~ 917, 963, 1009, 1054, [gap], 1124  -> x_range (900, 1140)
#   Num  RT cols:    X ~ 1284, 1331, 1377, 1423, [gap], 1491, 1537 -> x_range (1270, 1550)
#
# CHEMISTRY:
#   Num  LT cols:    X ~ 1676, 1721, 1767, 1814, [gap], 1883, 1928 -> x_range (1660, 1940)
#   Num  RT cols:    X ~ 2090, 2135, 2181, [gap], 2250, 2296 -> x_range (2075, 2310)

subjects = [
    {
        "name": "Maths",
        "mcq_l_x": (190, 360), "mcq_r_x": (580, 750),
        "num_lt_x": (90, 445), "num_rt_x": (445, 810),
        "num_lb_x": (90, 445), "num_rb_x": (445, 810),
        "sec1_qs": [1, 2, 3, 4], "sec2_qs": [5, 6, 7, 8],
        "sec3_qs": [9, 10, 11, 12], "sec4_qs": [13, 14, 15, 16],
    },
    {
        "name": "Physics",
        "mcq_l_x": (940, 1130), "mcq_r_x": (1330, 1510),
        "num_lt_x": (840, 1204), "num_rt_x": (1204, 1580),
        "num_lb_x": (840, 1204), "num_rb_x": (1204, 1580),
        "sec1_qs": [17, 18, 19, 20], "sec2_qs": [21, 22, 23, 24],
        "sec3_qs": [25, 26, 27, 28], "sec4_qs": [29, 30, 31, 32],
    },
    {
        "name": "Chemistry",
        "mcq_l_x": (1710, 1900), "mcq_r_x": (2090, 2310),
        "num_lt_x": (1610, 1973), "num_rt_x": (1973, 2350),
        "num_lb_x": (1610, 1973), "num_rb_x": (1973, 2350),
        "sec1_qs": [33, 34, 35, 36], "sec2_qs": [37, 38, 39, 40],
        "sec3_qs": [41, 42, 43, 44], "sec4_qs": [45, 46, 47, 48],
    },
]

# Y-ranges
SEC1_Y = (1000, 1310)
SEC2_Y = (1000, 1310)
SEC3_TOP_Y = (1600, 2100)
SEC3_BOT_Y = (2250, 2750)
SEC4_Y = (3000, 3150)

questions_template = {}

for s in subjects:
    subj = s["name"]

    # ── Section 1: MCQ left (4 questions x 4 options) ────────────────────────
    sec1_pts = pts_in_box(*s["mcq_l_x"], *SEC1_Y)
    sec1_rows = extract_grid_rows(sec1_pts, 4, 4)
    for qi, qnum in enumerate(s["sec1_qs"]):
        bubbles = [{"opt": opt, "x": round(sec1_rows[qi][oi][0], 1),
                     "y": round(sec1_rows[qi][oi][1], 1)}
                   for oi, opt in enumerate("ABCD")]
        questions_template[str(qnum)] = {"type": "mcq", "section": "1",
                                          "subject": subj, "bubbles": bubbles}

    # ── Section 2: MCQ right (4 questions x 4 options) ───────────────────────
    sec2_pts = pts_in_box(*s["mcq_r_x"], *SEC2_Y)
    sec2_rows = extract_grid_rows(sec2_pts, 4, 4)
    for qi, qnum in enumerate(s["sec2_qs"]):
        bubbles = [{"opt": opt, "x": round(sec2_rows[qi][oi][0], 1),
                     "y": round(sec2_rows[qi][oi][1], 1)}
                   for oi, opt in enumerate("ABCD")]
        questions_template[str(qnum)] = {"type": "mcq", "section": "2",
                                          "subject": subj, "bubbles": bubbles}

    # ── Section 3: Numerical (4 questions, each with up to 6 digit columns) ─
    num_regions = [
        (s["sec3_qs"][0], s["num_lt_x"], SEC3_TOP_Y),
        (s["sec3_qs"][1], s["num_rt_x"], SEC3_TOP_Y),
        (s["sec3_qs"][2], s["num_lb_x"], SEC3_BOT_Y),
        (s["sec3_qs"][3], s["num_rb_x"], SEC3_BOT_Y),
    ]

    def numerical_grid(rpts, qnum):
        if not rpts:
            return {"type": "numerical", "section": "3", "subject": subj, "columns": []}

        xs = sorted([p[0] for p in rpts])
        ys = sorted([p[1] for p in rpts])
        col_centers = cluster_1d(xs, tol=15)
        
        real_ys = [cy for cy in ys if any(
            abs(p[0]-cx) < 14 and abs(p[1]-cy) < 14
            for p in rpts for cx in col_centers
        )]
        row_centers = get_10_rows(cluster_1d(real_ys, tol=12))

        cols_data = []
        
        # Determine minus sign column vs digit columns based on bubble count in that column
        for cx in col_centers:
            col_pts = [p for p in rpts if abs(p[0]-cx) < 15]
            # Since RETR_LIST finds multiple contours per bubble, a minus sign has 1-4 points, 
            # while a 10-digit column has 10-20 points.
            if len(col_pts) <= 4:
                # Minus sign
                # Find the actual coordinates of the minus sign bubble (closest to bottom)
                m_pt = max(col_pts, key=lambda p: p[1])
                cols_data.append([{"val": "-", "x": round(m_pt[0], 1), "y": round(m_pt[1], 1)}])
            elif len(col_pts) >= 6:
                # Digit column
                col_bubbles = []
                for vi, cy in enumerate(row_centers):
                    near = [(x,y) for x,y in rpts if abs(x-cx)<15 and abs(y-cy)<15]
                    if near:
                        col_bubbles.append({"val": str(vi), "x": round(near[0][0], 1), "y": round(near[0][1], 1)})
                    else:
                        col_bubbles.append({"val": str(vi), "x": round(cx, 1), "y": round(cy, 1)})
                cols_data.append(col_bubbles)

        return {"type": "numerical", "section": "3", "subject": subj, "columns": cols_data}

    for qnum, x_range, y_range in num_regions:
        npts = pts_in_box(*x_range, *y_range)
        questions_template[str(qnum)] = numerical_grid(npts, qnum)

    # ── Section 4: MCQ bottom (4 questions x 4 options, 2 left + 2 right) ────
    sec4l_pts = pts_in_box(*s["mcq_l_x"], *SEC4_Y)
    sec4l_rows = extract_grid_rows(sec4l_pts, 2, 4)
    for qi, qnum in enumerate(s["sec4_qs"][:2]):
        bubbles = [{"opt": opt, "x": round(sec4l_rows[qi][oi][0], 1),
                     "y": round(sec4l_rows[qi][oi][1], 1)}
                   for oi, opt in enumerate("ABCD")]
        questions_template[str(qnum)] = {"type": "mcq", "section": "4",
                                          "subject": subj, "bubbles": bubbles}

    sec4r_pts = pts_in_box(*s["mcq_r_x"], *SEC4_Y)
    sec4r_rows = extract_grid_rows(sec4r_pts, 2, 4)
    for qi, qnum in enumerate(s["sec4_qs"][2:]):
        bubbles = [{"opt": opt, "x": round(sec4r_rows[qi][oi][0], 1),
                     "y": round(sec4r_rows[qi][oi][1], 1)}
                   for oi, opt in enumerate("ABCD")]
        questions_template[str(qnum)] = {"type": "mcq", "section": "4",
                                          "subject": subj, "bubbles": bubbles}

# ── Save template ────────────────────────────────────────────────────────────
template = {"roll_number_grid": roll_grid, "questions": questions_template}
out_path = r"f:\Medjeex\Medjeex-OMR-Engine\templates\jee_advanced_template.json"
with open(out_path, "w") as f:
    json.dump(template, f, indent=2)
print(f"Saved template to {out_path}")

# ── Verification overlay (same drawing style as measured_all_bubbles.jpg) ────
vis = img.copy()

# Draw ALL detected raw contour circles in green (exactly like measure_all_grid_centers.py)
for (x, y, r) in all_raw:
    cv2.circle(vis, (int(x), int(y)), int(r), (0, 255, 0), 1)

cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\output\template_overlay_verification.jpg", vis)
print("Saved template_overlay_verification.jpg (identical style to measured_all_bubbles.jpg)")

# ── Summary stats ────────────────────────────────────────────────────────────
total_bubbles = 0
for col in template["roll_number_grid"]:
    total_bubbles += len(col)
for qinfo in template["questions"].values():
    if qinfo["type"] == "mcq":
        total_bubbles += len(qinfo["bubbles"])
    elif qinfo["type"] == "numerical":
        for col in qinfo["columns"]:
            total_bubbles += len(col)
print(f"Template bubble count: {total_bubbles}")
print(f"  Roll grid: {sum(len(c) for c in template['roll_number_grid'])}")
mcq_count = sum(len(q['bubbles']) for q in template['questions'].values() if q['type'] == 'mcq')
num_count = sum(len(b) for q in template['questions'].values() if q['type'] == 'numerical' for b in q['columns'])
print(f"  MCQ bubbles: {mcq_count}")
print(f"  Numerical bubbles: {num_count}")
