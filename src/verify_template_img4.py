import cv2
import json

img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped_img4.jpg")

with open(r"f:\Medjeex\Medjeex-OMR-Engine\output\img4_template.json", "r") as f:
    template = json.load(f)

for q_num, q_data in template["questions"].items():
    pts = q_data["bubbles"]
    for p in pts:
        cv2.circle(img, (int(p["x"]), int(p["y"])), 15, (0, 255, 0), 2)
    
    # Put question number near the top-left most bubble
    if pts:
        min_x = min(p["x"] for p in pts)
        min_y = min(p["y"] for p in pts)
        cv2.putText(img, f"Q{q_num}", (int(min_x)-40, int(min_y)-20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\output\template_overlay_verification_img4.jpg", img)
