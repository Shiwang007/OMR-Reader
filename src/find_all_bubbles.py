import cv2
import numpy as np

img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (3, 3), 0)

# Binary threshold
_, thresh = cv2.threshold(blurred, 180, 255, cv2.THRESH_BINARY_INV)

# Find contours
cnts, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

bubbles = []
for c in cnts:
    (x, y), radius = cv2.minEnclosingCircle(c)
    area = cv2.contourArea(c)
    perimeter = cv2.arcLength(c, True)
    if perimeter > 0:
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        # Bubbles have radius around 9 to 16 px and high circularity
        if 8 <= radius <= 16 and circularity > 0.5:
            bubbles.append((float(x), float(y), float(radius)))

print(f"Total bubbles found via circularity: {len(bubbles)}")

# Let's save a visualization overlay to inspect detected bubbles
vis = img.copy()
for b in bubbles:
    cv2.circle(vis, (int(b[0]), int(b[1])), int(b[2]), (0, 255, 0), 1)

cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\output\debug_all_bubbles.jpg", vis)
print("Saved visualization to output/debug_all_bubbles.jpg")
