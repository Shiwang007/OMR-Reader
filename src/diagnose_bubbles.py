"""
Full diagnostic: Dump every detected column in every numerical question region.
"""
import cv2
import numpy as np
from collections import defaultdict

img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
_, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY_INV)
cnts, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

raw = []
for c in cnts:
    (x, y), r = cv2.minEnclosingCircle(c)
    area = cv2.contourArea(c)
    if 10 < r < 20 and area > 100:
        raw.append((float(x), float(y), float(r)))

deduped = []
for p in raw:
    if not any(np.hypot(p[0] - u[0], p[1] - u[1]) < 10.0 for u in deduped):
        deduped.append(p)

def analyze_region(name, x1, x2, y1, y2):
    pts = [(x,y,r) for x,y,r in deduped if x1 < x < x2 and y1 < y < y2]
    if not pts:
        print(f"  {name}: NO POINTS")
        return
    
    # Cluster by X
    xs = sorted([p[0] for p in pts])
    cols = []
    curr = [xs[0]]
    for v in xs[1:]:
        if v - curr[-1] <= 15:
            curr.append(v)
        else:
            cols.append(float(np.mean(curr)))
            curr = [v]
    cols.append(float(np.mean(curr)))
    
    print(f"  {name}: {len(pts)} pts, {len(cols)} cols")
    for cx in cols:
        col_pts = [p for p in pts if abs(p[0] - cx) < 15]
        print(f"    Col X~{cx:.0f}: {len(col_pts)} bubbles (x range: {min(p[0] for p in col_pts):.0f}-{max(p[0] for p in col_pts):.0f})")

# Wide bounds to capture everything in each numerical section
print("=== MATHS NUMERICAL ===")
analyze_region("Q9  (LT)", 100, 380, 1600, 2100)
analyze_region("Q10 (RT)", 480, 760, 1600, 2100)
analyze_region("Q11 (LB)", 100, 380, 2250, 2750)
analyze_region("Q12 (RB)", 480, 760, 2250, 2750)

print("\n=== PHYSICS NUMERICAL ===")
analyze_region("Q25 (LT)", 870, 1150, 1600, 2100)
analyze_region("Q26 (RT)", 1260, 1540, 1600, 2100)
analyze_region("Q27 (LB)", 870, 1150, 2250, 2750)
analyze_region("Q28 (RB)", 1260, 1540, 2250, 2750)

print("\n=== CHEMISTRY NUMERICAL ===")
analyze_region("Q41 (LT)", 1660, 1940, 1600, 2100)
analyze_region("Q42 (RT)", 2060, 2340, 1600, 2100)
analyze_region("Q43 (LB)", 1660, 1940, 2250, 2750)
analyze_region("Q44 (RB)", 2060, 2340, 2250, 2750)

# Also check the MCQ sections for completeness
print("\n=== MATHS MCQ ===")
analyze_region("Sec1 (L)", 190, 365, 1000, 1310)
analyze_region("Sec2 (R)", 580, 770, 1000, 1310)
analyze_region("Sec4 (L)", 190, 365, 3000, 3150)
analyze_region("Sec4 (R)", 580, 770, 3000, 3150)
