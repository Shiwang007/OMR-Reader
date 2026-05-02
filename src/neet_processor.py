import cv2
import numpy as np
import json
import os
from typing import Dict, List, Tuple

class NEETOMREngine:
    def __init__(self):
        self.template_path = r"f:\Medjeex\Medjeex-OMR-Engine\templates\neet_template.json"
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
        # Assuming NEET template structure
        for section in self.template.get("sections", []):
            sec_name = section["name"]
            sec_results = {}
            for q_idx, row in enumerate(section["rows"]):
                densities = []
                coords = []
                for c in row:
                    sx, sy = int(c['abs_x'] + total_x), int(c['abs_y'] + total_y)
                    coords.append((sx, sy))
                    roi = morphed[max(0, sy-10):min(h_img, sy+10), max(0, sx-10):min(w_img, sx+10)]
                    densities.append(np.mean(roi) if roi.size > 0 else 0)
                
                marked = [i for i, d in enumerate(densities) if d > 100]
                for i, coord in enumerate(coords):
                    color = (0, 255, 0) if i in marked else (255, 0, 0)
                    cv2.circle(viz_img, coord, 10, color, 2)
                
                q_num = section["start_q"] + q_idx
                sec_results[str(q_num)] = ["A", "B", "C", "D"][marked[0]] if len(marked) == 1 else ("INVALID" if len(marked) > 1 else "SKIPPED")
            results[sec_name] = sec_results
            
        return results, viz_img
