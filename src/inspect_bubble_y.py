import cv2
import numpy as np

img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
_, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY_INV)

cnts, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

circles = []
for c in cnts:
    (x, y), r = cv2.minEnclosingCircle(c)
    area = cv2.contourArea(c)
    if 10 < r < 20 and area > 100:
        circles.append((float(x), float(y)))

# Let's inspect Maths Section 1 (X between 150 and 350)
maths_sec1 = [c for c in circles if 150 < c[0] < 350 and 800 < c[1] < 1250]
maths_sec1.sort(key=lambda c: c[1])

print("Maths Section 1 bubble Y positions:")
for c in maths_sec1:
    print(f"  X={c[0]:.1f}, Y={c[1]:.1f}")

# Let's inspect Maths Section 3 Top (X between 150 and 350, Y between 1500 and 2100)
maths_sec3 = [c for c in circles if 150 < c[0] < 350 and 1500 < c[1] < 2100]
maths_sec3.sort(key=lambda c: c[1])

print("\nMaths Section 3 Top bubble Y positions:")
for c in maths_sec3[:10]:
    print(f"  X={c[0]:.1f}, Y={c[1]:.1f}")

# Let's inspect Maths Section 4 (X between 150 and 350, Y between 2900 and 3250)
maths_sec4 = [c for c in circles if 150 < c[0] < 350 and 2900 < c[1] < 3250]
maths_sec4.sort(key=lambda c: c[1])

print("\nMaths Section 4 bubble Y positions:")
for c in maths_sec4:
    print(f"  X={c[0]:.1f}, Y={c[1]:.1f}")
