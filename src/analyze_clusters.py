import cv2
import numpy as np
import json

img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
h, w = gray.shape

blurred = cv2.GaussianBlur(gray, (5, 5), 0)
_, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY_INV)
cnts, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

circles = []
for c in cnts:
    (x, y), r = cv2.minEnclosingCircle(c)
    area = cv2.contourArea(c)
    if 9 < r < 18 and area > 120:
        circles.append((x, y))

print(f"Total valid bubbles: {len(circles)}")

# Helper to cluster 1D values with tolerance
def cluster_points(points, tolerance=12):
    points = sorted(points)
    clusters = []
    curr = [points[0]]
    for p in points[1:]:
        if p - curr[-1] <= tolerance:
            curr.append(p)
        else:
            clusters.append(np.mean(curr))
            curr = [p]
    clusters.append(np.mean(curr))
    return sorted(clusters)

# 1. Roll No. grid analysis (X in [130, 560], Y in [330, 750])
roll_pts = [c for c in circles if 120 < c[0] < 580 and 320 < c[1] < 770]
roll_xs = cluster_points([c[0] for c in roll_pts], tolerance=10)
roll_ys = cluster_points([c[1] for c in roll_pts], tolerance=10)

print(f"\nRoll No. grid: {len(roll_xs)} columns, {len(roll_ys)} rows")
print("  Roll X centers:", [round(x, 1) for x in roll_xs])
print("  Roll Y centers:", [round(y, 1) for y in roll_ys])

# 2. Section 1 & Section 2 MCQ Grid (Maths, Y in [930, 1150])
m_s1_pts = [c for c in circles if 140 < c[0] < 450 and 930 < c[1] < 1150]
m_s1_xs = cluster_points([c[0] for c in m_s1_pts], tolerance=10)
m_s1_ys = cluster_points([c[1] for c in m_s1_pts], tolerance=10)
print(f"\nMaths Sec 1 MCQ: {len(m_s1_xs)} options (A,B,C,D), {len(m_s1_ys)} question rows")
print("  Sec 1 X:", [round(x, 1) for x in m_s1_xs])
print("  Sec 1 Y:", [round(y, 1) for y in m_s1_ys])

m_s2_pts = [c for c in circles if 530 < c[0] < 800 and 930 < c[1] < 1150]
m_s2_xs = cluster_points([c[0] for c in m_s2_pts], tolerance=10)
m_s2_ys = cluster_points([c[1] for c in m_s2_pts], tolerance=10)
print(f"\nMaths Sec 2 MCQ: {len(m_s2_xs)} options, {len(m_s2_ys)} rows")
print("  Sec 2 X:", [round(x, 1) for x in m_s2_xs])
print("  Sec 2 Y:", [round(y, 1) for y in m_s2_ys])

# 3. Section 3 Numerical Grid (Q9: X in [120, 380], Y in [1600, 2020])
q9_pts = [c for c in circles if 120 < c[0] < 380 and 1600 < c[1] < 2050]
q9_xs = cluster_points([c[0] for c in q9_pts], tolerance=10)
q9_ys = cluster_points([c[1] for c in q9_pts], tolerance=10)
print(f"\nMaths Q9 Numerical: {len(q9_xs)} digit cols, {len(q9_ys)} digit rows (0-9)")
print("  Q9 X:", [round(x, 1) for x in q9_xs])
print("  Q9 Y:", [round(y, 1) for y in q9_ys])

# Section 4 MCQ Grid (Maths, Y in [2950, 3150])
m_s4_pts = [c for c in circles if 140 < c[0] < 450 and 2950 < c[1] < 3150]
m_s4_xs = cluster_points([c[0] for c in m_s4_pts], tolerance=10)
m_s4_ys = cluster_points([c[1] for c in m_s4_pts], tolerance=10)
print(f"\nMaths Sec 4 MCQ: {len(m_s4_xs)} options, {len(m_s4_ys)} rows")
print("  Sec 4 X:", [round(x, 1) for x in m_s4_xs])
print("  Sec 4 Y:", [round(y, 1) for y in m_s4_ys])
