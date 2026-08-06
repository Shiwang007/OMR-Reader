import cv2
import numpy as np
import json
from jee_advanced_processor import JEEAdvancedOMREngine

def main():
    engine = JEEAdvancedOMREngine()
    image_path = r"f:\Medjeex\Medjeex-OMR-Engine\Advance omr 1\Image (3).jpg"
    warped, M = engine.align_image(cv2.imread(image_path))

    with open("templates/jee_advanced_template.json", "r") as f:
        tmpl = json.load(f)

    def draw_filled_mark(img, x, y, radius=13):
        cv2.circle(img, (int(x), int(y)), radius, (20, 20, 20), -1)

    # 1. Fill Roll Number: 9 8 7 6 5 4 3 2 1 0
    roll_digits = ["9", "8", "7", "6", "5", "4", "3", "2", "1", "0"]
    for col_i, digit in enumerate(roll_digits):
        val_int = int(digit)
        b = tmpl["roll_number_grid"][col_i][val_int]
        draw_filled_mark(warped, b["x"], b["y"])

    # 2. Fill Question Marks
    # Q1: A, C
    for b in tmpl["questions"]["1"]["bubbles"]:
        if b["opt"] in ["A", "C"]:
            draw_filled_mark(warped, b["x"], b["y"])

    # Q2: B
    for b in tmpl["questions"]["2"]["bubbles"]:
        if b["opt"] == "B":
            draw_filled_mark(warped, b["x"], b["y"])

    # Q9 (Numerical): fill first 4 integer digits, leave decimal cols unfilled
    q9_cols = tmpl["questions"]["9"]["columns"]
    fill_digits = ["0", "5", "2", "4"]
    for col_i, val_str in enumerate(fill_digits):
        if col_i < len(q9_cols):
            b = q9_cols[col_i][int(val_str)]
            draw_filled_mark(warped, b["x"], b["y"])
    # Also fill remaining columns with 0 so they don't show as '?'
    for col_i in range(len(fill_digits), len(q9_cols)):
        b = q9_cols[col_i][0]  # fill with 0
        draw_filled_mark(warped, b["x"], b["y"])

    # Q17 (Physics Sec 1): D
    for b in tmpl["questions"]["17"]["bubbles"]:
        if b["opt"] == "D":
            draw_filled_mark(warped, b["x"], b["y"])

    # Q33 (Chemistry Sec 1): A, B, D
    for b in tmpl["questions"]["33"]["bubbles"]:
        if b["opt"] in ["A", "B", "D"]:
            draw_filled_mark(warped, b["x"], b["y"])

    sim_filled_path = r"f:\Medjeex\Medjeex-OMR-Engine\output\simulated_filled_Image_(3).jpg"
    cv2.imwrite(sim_filled_path, warped)
    print(f"Saved simulated filled image to {sim_filled_path}")

    # Process simulated filled image through engine
    res, _, vis_img = engine.process_omr(sim_filled_path)
    
    print("\n=== Extraction Results on Simulated Filled Sheet ===")
    print(f"Roll Number Detected: {res['roll_number']} (Expected: '9876543210')")
    print(f"Q1 (Maths Sec 1): {res['questions']['1']} (Expected: 'A,C')")
    print(f"Q2 (Maths Sec 1): {res['questions']['2']} (Expected: 'B')")
    print(f"Q9 (Maths Sec 3 Numerical): {res['questions']['9']} (Expected: '05240')")
    print(f"Q17 (Physics Sec 1): {res['questions']['17']} (Expected: 'D')")
    print(f"Q33 (Chemistry Sec 1): {res['questions']['33']} (Expected: 'A,B,D')")

    vis_path = r"f:\Medjeex\Medjeex-OMR-Engine\output\simulated_vis_Image_(3).jpg"
    cv2.imwrite(vis_path, vis_img)
    print(f"Saved simulated visualization to {vis_path}")

if __name__ == "__main__":
    main()
