import cv2
import numpy as np
import json
import os

def generate_template():
    # 1. Roll No. grid (10 digits x 10 values 0-9)
    roll_start_x = 157.0
    roll_start_y = 347.0
    pitch = 46.1
    
    roll_grid = []
    for col in range(10):
        col_coords = []
        for val in range(10):
            cx = roll_start_x + col * pitch
            cy = roll_start_y + val * pitch
            col_coords.append({"val": str(val), "x": round(cx, 1), "y": round(cy, 1)})
        roll_grid.append(col_coords)

    # Submap & Layout definitions
    subjects = ["Maths", "Physics", "Chemistry"]
    subj_offsets = {"Maths": 0.0, "Physics": 792.0, "Chemistry": 1584.0}

    # Sec 1: 4 MCQs per subject
    sec1_map = {
        "Maths": [1, 2, 3, 4],
        "Physics": [17, 18, 19, 20],
        "Chemistry": [33, 34, 35, 36]
    }
    sec1_start_x = 203.4
    sec1_start_y = 968.0
    
    # Sec 2: 4 MCQs per subject
    sec2_map = {
        "Maths": [5, 6, 7, 8],
        "Physics": [21, 22, 23, 24],
        "Chemistry": [37, 38, 39, 40]
    }
    sec2_start_x = 594.8
    sec2_start_y = 968.0

    # Sec 3: 4 Numerical matrix questions per subject
    sec3_map = {
        "Maths": [9, 10, 11, 12],
        "Physics": [25, 26, 27, 28],
        "Chemistry": [41, 42, 43, 44]
    }
    
    # Sec 4: 4 MCQs per subject
    sec4_map = {
        "Maths": [13, 14, 15, 16],
        "Physics": [29, 30, 31, 32],
        "Chemistry": [45, 46, 47, 48]
    }

    questions_template = {}

    for subj in subjects:
        s_off = subj_offsets[subj]
        
        # --- Section 1 (MCQ) ---
        for idx, q_num in enumerate(sec1_map[subj]):
            row_bubbles = []
            for opt_i, opt in enumerate(["A", "B", "C", "D"]):
                cx = sec1_start_x + s_off + opt_i * pitch
                cy = sec1_start_y + idx * pitch
                row_bubbles.append({"opt": opt, "x": round(cx, 1), "y": round(cy, 1)})
            questions_template[str(q_num)] = {"type": "mcq", "section": "1", "subject": subj, "bubbles": row_bubbles}

        # --- Section 2 (MCQ) ---
        for idx, q_num in enumerate(sec2_map[subj]):
            row_bubbles = []
            for opt_i, opt in enumerate(["A", "B", "C", "D"]):
                cx = sec2_start_x + s_off + opt_i * pitch
                cy = sec2_start_y + idx * pitch
                row_bubbles.append({"opt": opt, "x": round(cx, 1), "y": round(cy, 1)})
            questions_template[str(q_num)] = {"type": "mcq", "section": "2", "subject": subj, "bubbles": row_bubbles}

        # --- Section 3 (Numerical Matrix) ---
        sec3_qs = sec3_map[subj]
        # Q0: Left top
        q0_num = sec3_qs[0]
        q0_cols = []
        for digit_col in range(4):
            col_bubbles = []
            for val in range(10):
                cx = 157.0 + s_off + digit_col * pitch
                cy = 1617.3 + val * pitch
                col_bubbles.append({"val": str(val), "x": round(cx, 1), "y": round(cy, 1)})
            q0_cols.append(col_bubbles)
        questions_template[str(q0_num)] = {"type": "numerical", "section": "3", "subject": subj, "columns": q0_cols}

        # Q1: Right top
        q1_num = sec3_qs[1]
        q1_cols = []
        for digit_col in range(4):
            col_bubbles = []
            for val in range(10):
                cx = 548.4 + s_off + digit_col * pitch
                cy = 1617.3 + val * pitch
                col_bubbles.append({"val": str(val), "x": round(cx, 1), "y": round(cy, 1)})
            q1_cols.append(col_bubbles)
        questions_template[str(q1_num)] = {"type": "numerical", "section": "3", "subject": subj, "columns": q1_cols}

        # Q2: Left bottom
        q2_num = sec3_qs[2]
        q2_cols = []
        for digit_col in range(4):
            col_bubbles = []
            for val in range(10):
                cx = 157.0 + s_off + digit_col * pitch
                cy = 2264.0 + val * pitch
                col_bubbles.append({"val": str(val), "x": round(cx, 1), "y": round(cy, 1)})
            q2_cols.append(col_bubbles)
        questions_template[str(q2_num)] = {"type": "numerical", "section": "3", "subject": subj, "columns": q2_cols}

        # Q3: Right bottom
        q3_num = sec3_qs[3]
        q3_cols = []
        for digit_col in range(4):
            col_bubbles = []
            for val in range(10):
                cx = 548.4 + s_off + digit_col * pitch
                cy = 2264.0 + val * pitch
                col_bubbles.append({"val": str(val), "x": round(cx, 1), "y": round(cy, 1)})
            q3_cols.append(col_bubbles)
        questions_template[str(q3_num)] = {"type": "numerical", "section": "3", "subject": subj, "columns": q3_cols}

        # --- Section 4 (MCQ) ---
        q_s4 = sec4_map[subj]
        for idx, q_num in enumerate(q_s4[:2]):
            row_bubbles = []
            for opt_i, opt in enumerate(["A", "B", "C", "D"]):
                cx = sec1_start_x + s_off + opt_i * pitch
                cy = 2984.0 + idx * 46.1
                row_bubbles.append({"opt": opt, "x": round(cx, 1), "y": round(cy, 1)})
            questions_template[str(q_num)] = {"type": "mcq", "section": "4", "subject": subj, "bubbles": row_bubbles}

        for idx, q_num in enumerate(q_s4[2:]):
            row_bubbles = []
            for opt_i, opt in enumerate(["A", "B", "C", "D"]):
                cx = sec2_start_x + s_off + opt_i * pitch
                cy = 2984.0 + idx * 46.1
                row_bubbles.append({"opt": opt, "x": round(cx, 1), "y": round(cy, 1)})
            questions_template[str(q_num)] = {"type": "mcq", "section": "4", "subject": subj, "bubbles": row_bubbles}

    template_full = {
        "roll_number_grid": roll_grid,
        "questions": questions_template
    }

    out_path = r"f:\Medjeex\Medjeex-OMR-Engine\templates\jee_advanced_template.json"
    with open(out_path, "w") as f:
        json.dump(template_full, f, indent=2)
    print(f"Generated JEE Advanced template at {out_path}")

    # Overlay
    img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped.jpg")
    vis = img.copy()
    
    for col in roll_grid:
        for b in col:
            cv2.circle(vis, (int(b['x']), int(b['y'])), 12, (255, 0, 0), 1)

    for q_num, q_info in questions_template.items():
        if q_info['type'] == 'mcq':
            for b in q_info['bubbles']:
                cv2.circle(vis, (int(b['x']), int(b['y'])), 12, (0, 180, 0), 1)
        elif q_info['type'] == 'numerical':
            for col in q_info['columns']:
                for b in col:
                    cv2.circle(vis, (int(b['x']), int(b['y'])), 12, (0, 0, 255), 1)

    cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\output\template_overlay_verification.jpg", vis)
    print("Saved perfect template overlay verification.")

if __name__ == "__main__":
    generate_template()
