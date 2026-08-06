import cv2
import numpy as np
import json
import os

def detect_fiducials(img):
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)
    cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    candidates = []
    margin = 250
    for c in cnts:
        x, y, bw, bh = cv2.boundingRect(c)
        area = cv2.contourArea(c)
        aspect_ratio = bw / float(bh)
        if 10 < bw < 100 and 10 < bh < 100 and 0.4 < aspect_ratio < 2.5 and area > 100:
            if (x < margin or x > w - margin) and (y < margin or y > h - margin):
                cx, cy = x + bw/2.0, y + bh/2.0
                candidates.append((cx, cy))
                
    tl = min(candidates, key=lambda c: c[0]**2 + c[1]**2)
    tr = min(candidates, key=lambda c: (w - c[0])**2 + c[1]**2)
    bl = min(candidates, key=lambda c: c[0]**2 + (h - c[1])**2)
    br = min(candidates, key=lambda c: (w - c[0])**2 + (h - c[1])**2)
    
    return np.float32([tl, tr, br, bl])

def get_canonical_image(img, target_w=2480, target_h=3508):
    src_pts = detect_fiducials(img)
    # Define standard canonical target points corresponding to corners
    # TL=(60, 210), TR=(2370, 210), BR=(2370, 3200), BL=(60, 3200)
    dst_pts = np.float32([
        [60, 210],
        [2370, 210],
        [2370, 3200],
        [60, 3200]
    ])
    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(img, M, (target_w, target_h))
    return warped, M

img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\Advance omr 1\Image (3).jpg")
warped, _ = get_canonical_image(img)

# Save warped image to verify canonical image quality
cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped.jpg", warped)
print("Canonical warped image saved to output/canonical_warped.jpg")
