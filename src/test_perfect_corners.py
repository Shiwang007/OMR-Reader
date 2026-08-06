import cv2
import numpy as np

img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\Advance omr 1\Image (3).jpg")
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

candidates = []
margin = 350
for c in cnts:
    x, y, bw, bh = cv2.boundingRect(c)
    area = cv2.contourArea(c)
    aspect_ratio = bw / float(bh)
    if 10 < bw < 100 and 10 < bh < 100 and 0.4 < aspect_ratio < 2.5 and area > 100:
        if (x < margin or x > w - margin) and (y < margin or y > h - margin):
            candidates.append((x + bw/2.0, y + bh/2.0, bw, bh))

tl = min(candidates, key=lambda c: c[0]**2 + c[1]**2)
tr = min(candidates, key=lambda c: (w - c[0])**2 + c[1]**2)
bl = min(candidates, key=lambda c: c[0]**2 + (h - c[1])**2)
br = min(candidates, key=lambda c: (w - c[0])**2 + (h - c[1])**2)

print("TL:", tl)
print("TR:", tr)
print("BL:", bl)
print("BR:", br)

src_pts = np.float32([tl[:2], tr[:2], br[:2], bl[:2]])
dst_pts = np.float32([
    [65.0, 211.0],
    [2365.0, 211.0],
    [2365.0, 3200.0],
    [65.0, 3200.0]
])

M = cv2.getPerspectiveTransform(src_pts, dst_pts)
warped = cv2.warpPerspective(img, M, (w, h))
print("Warped shape:", warped.shape, "min:", warped.min(), "max:", warped.max(), "mean:", warped.mean())

cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped.jpg", warped)
print("Perfect canonical warped image written to output/canonical_warped.jpg")
