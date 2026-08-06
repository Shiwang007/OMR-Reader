import cv2
import numpy as np

img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
h, w = gray.shape

# Threshold to get dark circles / text
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
_, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY_INV)

# Find circle-like contours
cnts, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

circles = []
for c in cnts:
    (x, y), r = cv2.minEnclosingCircle(c)
    area = cv2.contourArea(c)
    if 10 < r < 20 and area > 100:
        circles.append((x, y, r))

print(f"Total potential bubble circles found: {len(circles)}")

# Draw all found circles on image
vis = img.copy()
for (x, y, r) in circles:
    cv2.circle(vis, (int(x), int(y)), int(r), (0, 255, 0), 1)

cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\output\measured_all_bubbles.jpg", vis)
print("Saved visualization to output/measured_all_bubbles.jpg")
