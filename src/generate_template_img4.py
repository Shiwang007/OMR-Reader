"""
Generate img4_template.json using EXACT pixel positions from the same detection
as measured_all_bubbles_img4.jpg.

Layout (Image 4 - JEE Advanced with Numerical):
  MATHS:
    MCQ  Q1-4   : Section 1, left column
    MCQ  Q5-9   : Section 2, left column
    NUM  pairs  : Section 3 - Q10+Q11 (row1), Q12+Q13 (row2), Q14+Q15 (row3), Q16+Q17 (row4), Q18 (row5 left only)
  PHYSICS:
    MCQ  Q19-23 : Section 1
    MCQ  Q24-28 : Section 2
    NUM  pairs  : Q29+Q30, Q31+Q32, Q33+Q34, Q35+Q36
  CHEMISTRY:
    MCQ  Q37-40 : Section 1
    MCQ  Q41-45 : Section 2
    NUM  Q46    : Section 3, alone top-left
    NUM  pairs  : Q47+Q48, Q49+Q50, Q51+Q52, Q53+Q54
"""
import cv2
import numpy as np
import json
import os
import sys

# ─────────────────────────────────────────────
# STEP 1: IDENTICAL detection to analyze_img4.py / measured_all_bubbles_img4.jpg
# ─────────────────────────────────────────────
img_path = r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped_img4.jpg"
if not os.path.exists(img_path):
    raw_path = r"f:\Medjeex\Medjeex-OMR-Engine\Advance omr 2\Image (4).jpg"
    raw_img = cv2.imread(raw_path)
    if raw_img is None:
        raise FileNotFoundError(f"Cannot find {raw_path}")
    
    sys.path.insert(0, os.path.dirname(__file__))
    from jee_advanced_processor_img4 import Img4Processor
    p = Img4Processor.__new__(Img4Processor)
    img = p._align(raw_img)
    os.makedirs(r"f:\Medjeex\Medjeex-OMR-Engine\output", exist_ok=True)
    cv2.imwrite(img_path, img)
else:
    img = cv2.imread(img_path)
gray_w = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blurred_w = cv2.GaussianBlur(gray_w, (5, 5), 0)
_, thresh_w = cv2.threshold(blurred_w, 150, 255, cv2.THRESH_BINARY_INV)
cnts_w, _ = cv2.findContours(thresh_w, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

all_raw = []
for c in cnts_w:
    (x, y), r = cv2.minEnclosingCircle(c)
    area = cv2.contourArea(c)
    if 10 < r < 20 and area > 100:
        all_raw.append((float(x), float(y), float(r)))

# Dedup concentric rings (same as analyze_img4.py)
unique = []
for p in all_raw:
    x, y, r = p
    if not any(np.hypot(x-u[0], y-u[1]) < 10.0 for u in unique):
        unique.append((float(x), float(y)))

# Filter out noise bubbles caused by the "SECTION" text spanning across the page at Y=2215
unique = [p for p in unique if not (2200 < p[1] < 2230)]

print(f"Detected {len(unique)} unique bubbles (matches measured_all_bubbles_img4.jpg)")
pts = [(x, y) for x, y in unique]

# ─────────────────────────────────────────────
# STEP 2: Helper functions
# ─────────────────────────────────────────────
def cluster_1d(vals, tol=14):
    if not vals: return []
    vals = sorted(vals)
    clusters, curr = [], [vals[0]]
    for v in vals[1:]:
        if v - curr[-1] <= tol:
            curr.append(v)
        else:
            clusters.append(float(np.mean(curr)))
            curr = [v]
    clusters.append(float(np.mean(curr)))
    return clusters

def region(x0, x1, y0, y1):
    return [(x, y) for x, y in pts if x0 <= x <= x1 and y0 <= y <= y1]

def mcq_rows(rpts, q_start):
    """Extract MCQ questions: each row >= 4 bubbles = one question (rightmost 4 taken).
    Rows with <4 bubbles are section labels/noise and are skipped."""
    ys = cluster_1d([p[1] for p in rpts], tol=14)
    result = {}
    q = q_start
    for cy in ys:
        row = sorted([(x,y) for x,y in rpts if abs(y-cy)<14], key=lambda p: p[0])
        if len(row) >= 4:
            row = row[-4:]
            result[str(q)] = {
                "type": "mcq",
                "bubbles": [{"opt": o, "x": round(x,1), "y": round(y,1)} for o,(x,y) in zip("ABCD", row)]
            }
            q += 1
    return result

def numerical_grid(rpts, q_num):
    """
    Single numerical question grid.
    Structure: 6 digit columns + 1 optional minus column (total 7 cols).
    Minus column is leftmost if present.
    """
    xs = cluster_1d([p[0] for p in rpts], tol=14)
    ys = cluster_1d([p[1] for p in rpts], tol=14)
    
    bubbles = []
    
    # The digits are in the rightmost 6 columns
    digit_xs = xs[-6:] if len(xs) >= 6 else xs
    
    # Filter out Y clusters that have no actual digit bubbles (border artifacts)
    real_ys = [cy for cy in ys if any(
        abs(p[0]-cx) < 14 and abs(p[1]-cy) < 14
        for p in rpts for cx in digit_xs
    )]
    
    for ci, cx in enumerate(digit_xs):
        for vi, cy in enumerate(real_ys[:10]):
            near = [(x,y) for x,y in rpts if abs(x-cx)<14 and abs(y-cy)<14]
            if near:
                x, y = near[0]
                bubbles.append({"opt": f"{ci}_{vi}", "x": round(x,1), "y": round(y,1)})
                
    # Minus bubble (leftmost column, if we have 7 columns)
    if len(xs) >= 7:
        mx = xs[0]
        minus_pts = [(x,y) for x,y in rpts if abs(x-mx)<20]
        if minus_pts:
            # The minus bubble in Image 4 is on the last row (highest Y)
            x, y = max(minus_pts, key=lambda p: p[1])
            bubbles.append({"opt": "minus", "x": round(x,1), "y": round(y,1)})
            
    return {str(q_num): {"type": "numerical", "bubbles": bubbles}}

# ─────────────────────────────────────────────
# STEP 3: Roll Number (Y < 400, all X)
# ─────────────────────────────────────────────
roll_pts = region(60, 820, 130, 400)
roll_ys = cluster_1d([p[1] for p in roll_pts], tol=12)
roll_xs = cluster_1d([p[0] for p in roll_pts], tol=12)
print(f"Roll: {len(roll_xs)} cols × {len(roll_ys)} rows (expected 10×10)")

roll_grid = []
for cx in roll_xs[:10]:
    col = []
    for ri, cy in enumerate(roll_ys[:10]):
        near = [(x,y) for x,y in roll_pts if abs(x-cx)<12 and abs(y-cy)<12]
        if near:
            x, y = near[0]
            col.append({"val": str(ri), "x": round(x,1), "y": round(y,1)})
    if col:
        roll_grid.append(col)

# ─────────────────────────────────────────────
# STEP 4: MATHS MCQ
# From image: Q1-4 in Section1 (upper left), Q5-9 in Section2 (below)
# Approx X: 60-440, Section1 Y: 700-1000, Section2 Y: 1050-1300
# ─────────────────────────────────────────────
# MATHS MCQ: all MCQ bubbles in one region, pick the first 9 rows (Q1-9)
# X: 195-360 (answer columns only), Y: 720-1220
m_mcq_all = region(195, 360, 780, 1220)
maths_mcq_raw = mcq_rows(m_mcq_all, 1)
# Keep only Q1-9
maths_mcq = {k: v for k, v in maths_mcq_raw.items() if int(k) <= 9}
print(f"Maths MCQ: {sorted(maths_mcq.keys(), key=int)}")

# ─────────────────────────────────────────────
# STEP 5: MATHS NUMERICAL Q10-18
# Section 3: pairs side-by-side
# Left question X≈455-680, Right question X≈700-840
# 5 Y-groups, alternating 2 per group (except last group = 1)
# ─────────────────────────────────────────────
m_num_all = region(60, 840, 850, 3200)
m_num_ys = cluster_1d([p[1] for p in m_num_all], tol=14)
# Group by gaps >60px
m_num_groups = []
curr_g = [m_num_ys[0]]
for y in m_num_ys[1:]:
    if y - curr_g[-1] > 80:
        m_num_groups.append(curr_g)
        curr_g = [y]
    else:
        curr_g.append(y)
m_num_groups.append(curr_g)
print(f"Maths NUM: {len(m_num_groups)} Y-groups")

maths_num = {}
q = 10
for gi, g in enumerate(m_num_groups):
    y0, y1 = g[0] - 20, g[-1] + 20
    g_pts = [(x,y) for x,y in m_num_all if y0 <= y <= y1]
    # Split into left and right questions by X gap
    g_xs = cluster_1d([p[0] for p in g_pts], tol=14)
    # Find the large gap (>90px) splitting left from right
    split_x = (np.min(g_xs) + np.max(g_xs)) / 2
    left_pts  = [(x,y) for x,y in g_pts if x <= split_x]
    right_pts = [(x,y) for x,y in g_pts if x > split_x]
    
    if gi == 0:
        maths_num.update(numerical_grid(right_pts, q)); q += 1
    else:
        maths_num.update(numerical_grid(left_pts, q)); q += 1
        maths_num.update(numerical_grid(right_pts, q)); q += 1

maths_num = {k: v for k, v in maths_num.items() if 10 <= int(k) <= 18}

# ─────────────────────────────────────────────
# STEP 6: PHYSICS MCQ Q19-27
# ─────────────────────────────────────────────
# PHYSICS MCQ: all MCQ bubbles in one region, pick Q19-27 (9 questions)
p_mcq_all = region(935, 1120, 780, 1220)
phys_mcq_raw = mcq_rows(p_mcq_all, 19)
# Keep only Q19-27
phys_mcq = {k: v for k, v in phys_mcq_raw.items() if 19 <= int(k) <= 27}

print(f"Physics MCQ: {sorted(phys_mcq.keys(), key=int)}")

# ─────────────────────────────────────────────
# STEP 7: PHYSICS NUMERICAL Q28-36
# ─────────────────────────────────────────────
# Range: X: 850-1600, Y: 850-3200
p_num_all = region(850, 1600, 850, 3200)
p_num_ys = cluster_1d([p[1] for p in p_num_all], tol=14)
p_num_groups = []
curr_g = [p_num_ys[0]]
for y in p_num_ys[1:]:
    if y - curr_g[-1] > 80:
        p_num_groups.append(curr_g)
        curr_g = [y]
    else:
        curr_g.append(y)
p_num_groups.append(curr_g)
p_num_groups = p_num_groups[-5:]
print(f"Physics NUM: {len(p_num_groups)} Y-groups")

phys_num = {}
q = 28

for gi, g in enumerate(p_num_groups):
    y0, y1 = g[0] - 20, g[-1] + 20
    g_pts = [(x,y) for x,y in p_num_all if y0 <= y <= y1]
    g_xs = cluster_1d([p[0] for p in g_pts], tol=14)
    split_x = (np.min(g_xs) + np.max(g_xs)) / 2
    left_pts  = [(x,y) for x,y in g_pts if x <= split_x]
    right_pts = [(x,y) for x,y in g_pts if x > split_x]
    
    if gi == 0:
        phys_num.update(numerical_grid(right_pts, q)); q += 1
    else:
        phys_num.update(numerical_grid(left_pts, q)); q += 1
        phys_num.update(numerical_grid(right_pts, q)); q += 1

phys_num = {k: v for k, v in phys_num.items() if 28 <= int(k) <= 36}

# ─────────────────────────────────────────────

# STEP 8: CHEMISTRY MCQ Q37-45
# ─────────────────────────────────────────────
# CHEMISTRY MCQ: all MCQ bubbles in one region, pick Q37-45 (9 questions)
c_mcq_all = region(1700, 1965, 780, 1220)
chem_mcq_raw = mcq_rows(c_mcq_all, 37)
# Keep only Q37-45
chem_mcq = {k: v for k, v in chem_mcq_raw.items() if 37 <= int(k) <= 45}
print(f"Chemistry MCQ: {sorted(chem_mcq.keys(), key=int)}")

# ─────────────────────────────────────────────
# STEP 9: CHEMISTRY NUMERICAL Q46-54
# Q46 is alone at top-left of Section 3, then pairs Q47+48 etc.
# ─────────────────────────────────────────────
c_num_all = region(1610, 2400, 850, 3200)
c_num_ys = cluster_1d([p[1] for p in c_num_all], tol=14)
c_num_groups = []
curr_g = [c_num_ys[0]]
for y in c_num_ys[1:]:
    if y - curr_g[-1] > 80:
        c_num_groups.append(curr_g)
        curr_g = [y]
    else:
        curr_g.append(y)
c_num_groups.append(curr_g)
print(f"Chemistry NUM: {len(c_num_groups)} Y-groups")

chem_num = {}
q = 46
for gi, g in enumerate(c_num_groups):
    y0, y1 = g[0] - 20, g[-1] + 20
    g_pts = [(x,y) for x,y in c_num_all if y0 <= y <= y1]
    g_xs = cluster_1d([p[0] for p in g_pts], tol=14)
    split_x = (np.min(g_xs) + np.max(g_xs)) / 2
    left_pts  = [(x,y) for x,y in g_pts if x <= split_x]
    right_pts = [(x,y) for x,y in g_pts if x > split_x]
    
    if gi == 0:
        chem_num.update(numerical_grid(right_pts, q)); q += 1
    else:
        chem_num.update(numerical_grid(left_pts, q)); q += 1
        chem_num.update(numerical_grid(right_pts, q)); q += 1

chem_num = {k: v for k, v in chem_num.items() if 46 <= int(k) <= 54}

# ─────────────────────────────────────────────
# STEP 10: Merge and save
# ─────────────────────────────────────────────
all_questions = {}
for d in [maths_mcq, maths_num, phys_mcq, phys_num, chem_mcq, chem_num]:
    all_questions.update(d)

output = {"roll_number": roll_grid, "questions": all_questions}
os.makedirs(r"f:\Medjeex\Medjeex-OMR-Engine\output", exist_ok=True)
os.makedirs(r"f:\Medjeex\Medjeex-OMR-Engine\templates", exist_ok=True)

with open(r"f:\Medjeex\Medjeex-OMR-Engine\output\img4_template.json", "w") as f:
    json.dump(output, f, indent=4)

with open(r"f:\Medjeex\Medjeex-OMR-Engine\templates\jee_advanced_template_img4.json", "w") as f:
    json.dump(output, f, indent=4)

found = sorted(all_questions.keys(), key=int)
missing = sorted(set(map(str, range(1, 55))) - set(all_questions.keys()), key=int)
print(f"\nDONE: {len(all_questions)}/54 questions found")
if missing:
    print(f"Missing: {missing}")
else:
    print("All 54 questions mapped perfectly!")
