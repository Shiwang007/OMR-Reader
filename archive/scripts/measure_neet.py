import cv2
import numpy as np
import json
import os

def rebuild_neet_template_final_v2():
    image_path = r"f:\Medjeex\Medjeex-OMR-Engine\omr\Image (2).jpg"
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h_img, w_img = image.shape[:2]
    
    # 1. Circle Detection
    all_circles = cv2.HoughCircles(
        cv2.medianBlur(gray, 5), cv2.HOUGH_GRADIENT, 1, 20,
        param1=50, param2=20, minRadius=10, maxRadius=30
    )
    if all_circles is None: return
    circles = all_circles[0]
    
    # 2. Find the 45 MCQ rows vertically
    circles_y = sorted(circles, key=lambda x: x[1])
    rows_y = []
    curr = [circles_y[0]]
    for i in range(1, len(circles_y)):
        if abs(circles_y[i][1] - curr[-1][1]) < 18: curr.append(circles_y[i])
        else:
            if len(curr) >= 4: # A valid row should have at least 4 bubbles
                rows_y.append(np.mean([c[1] for c in curr]))
            curr = [circles_y[i]]
    if len(curr) >= 4: rows_y.append(np.mean([c[1] for c in curr]))
    
    rows_y = sorted(rows_y)
    # The MCQ block is the dense cluster of 45 rows at the bottom
    if len(rows_y) > 45:
        rows_y = rows_y[-45:]
    print(f"Detected {len(rows_y)} rows for MCQs.")

    # 3. Grid Search for each of the 4 subjects
    avg_dx = 83.5
    col_bounds = [
        {"name": "Physics", "x1": 50, "x2": 260},
        {"name": "Chemistry", "x1": 270, "x2": 480},
        {"name": "Biology I", "x1": 490, "x2": 700},
        {"name": "Biology II", "x1": 710, "x2": 950}
    ]
    
    full_template = {}
    for col in col_bounds:
        x1, x2 = int(col["x1"] * w_img / 1000), int(col["x2"] * w_img / 1000)
        col_circles = [c for c in circles if x1 < c[0] < x2]
        
        best_anchor, max_score = 0, 0
        for test_x in np.arange(x1, x1 + 250, 0.5): # Finer search
            score = 0
            for y in rows_y:
                for b_idx in range(4):
                    tx = test_x + b_idx * avg_dx
                    for c in col_circles:
                        if abs(c[0] - tx) < 15 and abs(c[1] - y) < 15:
                            score += 1; break
            if score > max_score: max_score, best_anchor = score, test_x
        
        print(f"{col['name']}: Anchor {best_anchor:.1f}, Score {max_score}")
        
        subj_data = []
        for y in rows_y:
            row_bubbles = []
            for b_idx in range(4):
                ex = best_anchor + b_idx * avg_dx
                closest = None
                for c in col_circles:
                    if abs(c[0] - ex) < 18 and abs(c[1] - y) < 18:
                        closest = c; break
                row_bubbles.append({"abs_x": float(closest[0] if closest is not None else ex),
                                   "abs_y": float(closest[1] if closest is not None else y)})
            subj_data.append(row_bubbles)
        full_template[col["name"]] = subj_data

    with open(r"f:\Medjeex\Medjeex-OMR-Engine\templates\neet_template.json", "w") as f:
        json.dump(full_template, f, indent=2)
    print("Master NEET Template generated from Image (2).jpg.")

if __name__ == "__main__":
    rebuild_neet_template_final_v2()
