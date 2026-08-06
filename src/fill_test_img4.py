import cv2
import json

img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped_img4.jpg")

with open(r"f:\Medjeex\Medjeex-OMR-Engine\output\img4_template.json", "r") as f:
    template = json.load(f)

# Fill all bubbles with blue
for q_num, q_data in template["questions"].items():
    pts = q_data["bubbles"]
    for p in pts:
        cv2.circle(img, (int(p["x"]), int(p["y"])), 12, (255, 0, 0), -1)

# Fill roll numbers
for col in template["roll_number"]:
    for p in col:
        cv2.circle(img, (int(p["x"]), int(p["y"])), 12, (255, 0, 0), -1)

cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\output\filled_test_img4.jpg", img)
