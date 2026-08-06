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

    def draw_filled_mark(img, x, y, radius=13):
        cv2.circle(img, (int(x), int(y)), radius, (20, 20, 20), -1)

    expected_results = {
        "roll_number": "1234567890",
        "questions": {}
    }

    # Fill Roll Number: 1 2 3 4 5 6 7 8 9 0
    roll_digits = list(expected_results["roll_number"])
    for col_i, digit in enumerate(roll_digits):
        val_int = int(digit)
        b = tmpl["roll_number_grid"][col_i][val_int]
        draw_filled_mark(warped, b["x"], b["y"])

    # Fill Questions
    opts = ["A", "B", "C", "D"]
    for q_str, q_info in tmpl["questions"].items():
        q_num = int(q_str)
        q_type = q_info["type"]
        
        if q_type == "mcq":
            # Pick a deterministic option: (q_num % 4)
            # If section 4, let's mark two options sometimes just to test multi-mark. Let's do single mark for simplicity of verification, or multi-mark for even numbers.
            opt_idx = q_num % 4
            opt = opts[opt_idx]
            
            # Let's do multi-mark for some questions: e.g. if q_num is divisible by 5
            marked_opts = [opt]
            if q_num % 5 == 0:
                opt_idx_2 = (q_num + 1) % 4
                marked_opts.append(opts[opt_idx_2])
                marked_opts.sort()
            
            for b in q_info["bubbles"]:
                if b["opt"] in marked_opts:
                    draw_filled_mark(warped, b["x"], b["y"])
            
            expected_results["questions"][q_str] = ",".join(marked_opts)
            
        elif q_type == "numerical":
            cols = q_info["columns"]
            filled_str = ""
            for col_i in range(len(cols)):
                # Pick a deterministic digit: (q_num + col_i) % 10
                digit = (q_num + col_i) % 10
                b = cols[col_i][digit]
                draw_filled_mark(warped, b["x"], b["y"])
                filled_str += str(digit)
            expected_results["questions"][q_str] = filled_str

    sim_filled_path = r"f:\Medjeex\Medjeex-OMR-Engine\output\comprehensive_filled.jpg"
    cv2.imwrite(sim_filled_path, warped)
    print(f"Saved comprehensive filled image to {sim_filled_path}")

    # Process simulated filled image through engine
    res, _, vis_img = engine.process_omr(sim_filled_path)
    
    print("\n=== Extraction Results ===")
    
    passed = True
    
    if res["roll_number"] != expected_results["roll_number"]:
        print(f"FAIL Roll Number: {res['roll_number']} (Expected: {expected_results['roll_number']})")
        passed = False
    else:
        print(f"PASS Roll Number: {res['roll_number']}")
        
    for q_str in sorted(expected_results["questions"].keys(), key=int):
        expected = expected_results["questions"][q_str]
        actual = res["questions"].get(q_str, "NOT FOUND")
        if actual != expected:
            print(f"FAIL Q{q_str}: {actual} (Expected: {expected})")
            passed = False
        else:
            pass # print(f"PASS Q{q_str}: {actual}")

    if passed:
        print("\nSUCCESS: ALL 48 QUESTIONS AND ROLL NUMBER EXTRACTED CORRECTLY!")
    else:
        print("\nWARNING: SOME EXTRACTIONS FAILED. Check above.")

    vis_path = r"f:\Medjeex\Medjeex-OMR-Engine\output\comprehensive_vis.jpg"
    cv2.imwrite(vis_path, vis_img)
    print(f"Saved comprehensive visualization to {vis_path}")

if __name__ == "__main__":
    main()
