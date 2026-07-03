import cv2
import numpy as np
import json
import os
from typing import Dict, List, Tuple

class JEEOMREngine:
    def __init__(self):
        self.template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates", "jee_mains_template.json")
        with open(self.template_path, 'r') as f:
            self.template = json.load(f)
        self.X_SHIFT = -20
        self.Y_SHIFT = -80

    def compute_scaling_shift(self, h: int) -> int:
        baseline_h = 2479 
        return int((h - baseline_h) * 0.1)

    def process_page1(self, image_path: str) -> Tuple[Dict, np.ndarray]:
        image = cv2.imread(image_path)
        if image is None: return {}, None
        
        h_img, w_img = image.shape[:2]
        viz_img = image.copy()
        
        # Pre-processing
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        s_channel = hsv[:, :, 1]
        v_inv = cv2.bitwise_not(hsv[:, :, 2])
        morphed = cv2.addWeighted(s_channel, 0.6, v_inv, 0.4, 0)
        
        total_x = self.X_SHIFT
        total_y = self.Y_SHIFT + self.compute_scaling_shift(h_img)
        
        results = {}
        page_data = self.template["page1"]
        sub_map = {
            "Physics": {"mcq": range(1, 21), "num": range(21, 26)},
            "Chemistry": {"mcq": range(26, 46), "num": range(46, 51)},
            "Mathematics": {"mcq": range(51, 71), "num": range(71, 76)}
        }
        
        for subj in ["Physics", "Chemistry", "Mathematics"]:
            subj_results = {}
            for q_idx, row in enumerate(page_data[subj]):
                densities = []
                coords = []
                for c in row:
                    sx, sy = int(c['abs_x'] + total_x), int(c['abs_y'] + total_y)
                    coords.append((sx, sy))
                    roi = morphed[max(0, sy-12):min(h_img, sy+12), max(0, sx-12):min(w_img, sx+12)]
                    densities.append(np.mean(roi) if roi.size > 0 else 0)
                
                row_baseline = np.median(densities) if densities else 0
                marked = []
                for i, d in enumerate(densities):
                    is_marked = d > 80 and (row_baseline < 10 or d / max(1, row_baseline) > 1.3)
                    if is_marked: marked.append(i)
                
                # Draw visualization based on result
                for i in range(len(coords)):
                    if i in marked:
                        if len(marked) == 1:
                            color = (0, 200, 0)    # Green = valid single mark
                        else:
                            color = (0, 0, 255)     # Red = INVALID (multiple)
                        cv2.circle(viz_img, coords[i], 12, color, -1)   # filled
                        cv2.circle(viz_img, coords[i], 12, color, 2)
                    else:
                        cv2.circle(viz_img, coords[i], 12, (200, 200, 200), 1)  # Gray outline
                
                q_num = sub_map[subj]["mcq"][q_idx]
                subj_results[str(q_num)] = ["A", "B", "C", "D"][marked[0]] if len(marked) == 1 else ("INVALID" if len(marked) > 1 else "SKIPPED")
            
            # Add numerical questions as SKIPPED (not on MCQ grid)
            for q_num in sub_map[subj]["num"]:
                subj_results[str(q_num)] = "SKIPPED"
            
            results[subj] = subj_results
            
        return results, viz_img
