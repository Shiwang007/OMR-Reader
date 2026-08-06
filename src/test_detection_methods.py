import cv2
import numpy as np

img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Test Canny edge detection + HoughCircles
blurred = cv2.medianBlur(gray, 3)
circles = cv2.HoughCircles(
    blurred, cv2.HOUGH_GRADIENT,
    dp=1, minDist=20,
    param1=100, param2=25,
    minRadius=10, maxRadius=25
)

if circles is not None:
    circles = np.round(circles[0]).astype(int)
    print(f"HoughCircles detected: {len(circles)}")
    vis = img.copy()
    for (x, y, r) in circles:
        cv2.circle(vis, (x, y), r, (0, 0, 255), 2)
    cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\output\debug_hough.jpg", vis)
else:
    print("No circles found with current parameters")

# Let's also print statistics of image gray values
print(f"Gray shape: {gray.shape}, min={gray.min()}, max={gray.max()}, mean={gray.mean():.1f}")
