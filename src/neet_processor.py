import cv2
import numpy as np
import json
import os
from typing import Dict, List, Tuple

class NEETOMREngine:
    def __init__(self):
        self.template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates", "neet_template.json")
        with open(self.template_path, 'r') as f:
            self.template = json.load(f)
        self.X_SHIFT = 0
        self.Y_SHIFT = 0

    def compute_scaling_shift(self, h: int) -> int:
        cal_h = 3442
        cal_first_row = 972.5
        expected_first_row = cal_first_row * (h / cal_h)
        return int(round(expected_first_row - cal_first_row))

    def process_sheet(self, image_path: str) -> Tuple[Dict, np.ndarray]:
        image = cv2.imread(image_path)
        if image is None: return {}, None
        
        h_img, w_img = image.shape[:2]
        viz_img = image.copy()
        
        # Simple thresholding for NEET
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        morphed = cv2.bitwise_not(gray)
        
        total_x = self.X_SHIFT
        total_y = self.Y_SHIFT + self.compute_scaling_shift(h_img)
        
        results = {}
        start_q = 1
        
        # NEET subjects in order
        subjects = ["Physics", "Chemistry", "Biology I", "Biology II"]
        
        for sec_name in subjects:
            rows = self.template.get(sec_name, [])
            sec_results = {}
            
            for q_idx, row in enumerate(rows):
                densities = []
                coords = []
                for c in row:
                    sx, sy = int(c['abs_x'] + total_x), int(c['abs_y'] + total_y)
                    coords.append((sx, sy))
                    # Use slightly larger ROI for NEET bubbles
                    roi = morphed[max(0, sy-12):min(h_img, sy+12), max(0, sx-12):min(w_img, sx+12)]
                    densities.append(np.mean(roi) if roi.size > 0 else 0)
                
                # Dynamic thresholding per row
                row_baseline = np.median(densities) if densities else 0
                marked = [i for i, d in enumerate(densities) if d > 80 and d > row_baseline * 1.3]
                
                # Draw visualization
                for i, coord in enumerate(coords):
                    if i in marked:
                        color = (0, 255, 0) if len(marked) == 1 else (0, 0, 255)
                        cv2.circle(viz_img, coord, 12, color, -1)
                        cv2.circle(viz_img, coord, 12, color, 2)
                    else:
                        cv2.circle(viz_img, coord, 12, (200, 200, 200), 1)
                
                q_num = start_q + q_idx
                sec_results[str(q_num)] = ["A", "B", "C", "D"][marked[0]] if len(marked) == 1 else ("INVALID" if len(marked) > 1 else "SKIPPED")
            
            results[sec_name] = sec_results
            start_q += len(rows)
            
        return results, viz_img
