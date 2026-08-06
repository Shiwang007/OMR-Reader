import cv2

img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\Advance omr 1\Image (3).jpg")
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY_INV)
cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

print(f"Total contours: {len(cnts)}")
for c in cnts:
    x, y, bw, bh = cv2.boundingRect(c)
    # Print any box near bottom left corner (X < 300, Y > 2800)
    if x < 300 and y > 2800:
        area = cv2.contourArea(c)
        print(f"BL candidate contour: X={x}, Y={y}, W={bw}, H={bh}, Area={area}")
