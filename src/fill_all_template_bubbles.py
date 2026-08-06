import cv2
import numpy as np
import json
import os
from jee_advanced_processor import JEEAdvancedOMREngine

def main():
    engine = JEEAdvancedOMREngine()
    image_path = r"f:\Medjeex\Medjeex-OMR-Engine\Advance omr 1\Image (3).jpg"
    warped, M = engine.align_image(cv2.imread(image_path))

    with open("templates/jee_advanced_template.json", "r") as f:
        tmpl = json.load(f)

    # Use a highly visible color (e.g. bright green) to show exactly what the template targets
    def draw_filled_mark(img, x, y, radius=13):
        cv2.circle(img, (int(x), int(y)), radius, (0, 200, 0), -1)

    # 1. Fill ALL Roll Number Bubbles
    for col in tmpl["roll_number_grid"]:
        for b in col:
            draw_filled_mark(warped, b["x"], b["y"])

    # 2. Fill ALL Question Bubbles
    for q_str, q_info in tmpl["questions"].items():
        q_type = q_info["type"]
        
        if q_type == "mcq":
            for b in q_info["bubbles"]:
                draw_filled_mark(warped, b["x"], b["y"])
            
        elif q_type == "numerical":
            cols = q_info["columns"]
            for col in cols:
                for b in col:
                    draw_filled_mark(warped, b["x"], b["y"])

    out_path = r"f:\Medjeex\Medjeex-OMR-Engine\output\filled_all_template_bubbles.jpg"
    cv2.imwrite(out_path, warped)
    print(f"Saved filled all template bubbles image to {out_path}")

if __name__ == "__main__":
    main()
