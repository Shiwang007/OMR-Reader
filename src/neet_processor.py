import cv2
import numpy as np
import json
import os
from typing import Dict, List

class NEETOMREngine:
    def __init__(self):
        self.template_path = r"f:\Medjeex\Medjeex-OMR-Engine\templates\neet_template.json"
        with open(self.template_path, 'r') as f:
            self.template = json.load(f)
            
        # --- MANUAL CALIBRATION (Adjust these to move the grid) ---
        self.X_SHIFT = 0  # Positive = Right, Negative = Left
        self.Y_SHIFT = 0  # Positive = Down, Negative = Up

    def compute_scaling_shift(self, h: int) -> int:
        """Ported from processor1.py: Proportional Y-adjustment"""
        cal_h = 3442
        cal_first_row = 972.5 # NEET baseline
        expected_first_row = cal_first_row * (h / cal_h)
        return int(round(expected_first_row - cal_first_row))

    def process_sheet(self, image_path: str, save_viz: bool = True) -> Dict:
        """Processes NEET MCQ Sheet with Manual and Auto Calibration"""
        image = cv2.imread(image_path)
        if image is None: return {"error": "Image not found"}
        
        h_img, w_img = image.shape[:2]
        
        # 1. Calculate Total Shifts
        auto_y = self.compute_scaling_shift(h_img)
        total_x = self.X_SHIFT
        total_y = auto_y + self.Y_SHIFT
        
        print(f"  [DEBUG] Calibration -> Auto_Y: {auto_y}, Manual_X: {self.X_SHIFT}, Manual_Y: {self.Y_SHIFT}")
        print(f"  [DEBUG] Final Grid Shift -> X: {total_x}, Y: {total_y}")
        
        viz_img = image.copy()
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Signal Extraction (Saturation + Inverted Value)
        s_channel = hsv[:, :, 1]
        v_inv = cv2.bitwise_not(hsv[:, :, 2])
        combined = cv2.addWeighted(s_channel, 0.6, v_inv, 0.4, 0)
        
        # Morphological Filtering
        kernel = np.ones((5,5), np.uint8)
        morphed = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel)
        
        results = {}
        sub_offsets = {"Physics": 1, "Chemistry": 46, "Biology I": 91, "Biology II": 136}
        
        mark_threshold = 80 # Absolute threshold (morphed density)
        relative_ratio = 1.6 # Must be 1.6x darker than row baseline to be a mark
        
        for subj in ["Physics", "Chemistry", "Biology I", "Biology II"]:
            subj_results = {}
            offset = sub_offsets[subj]
            
            for q_idx, row in enumerate(self.template[subj]):
                densities = []
                coords = []
                for c in row:
                    sx = int(c['abs_x'] + total_x)
                    sy = int(c['abs_y'] + total_y)
                    coords.append((sx, sy))
                    
                    size = 12
                    y1, y2 = max(0, sy-size), min(morphed.shape[0], sy+size)
                    x1, x2 = max(0, sx-size), min(morphed.shape[1], sx+size)
                    roi = morphed[y1:y2, x1:x2]
                    densities.append(np.mean(roi) if roi.size > 0 else 0)
                
                # BASELINE LOGIC (from processor1.py)
                row_baseline = np.median(densities) if densities else 0
                marked_indices = []
                
                for i, d in enumerate(densities):
                    # A bubble is marked if it's above absolute threshold 
                    # AND significantly darker than the row baseline
                    is_marked = d > mark_threshold and (row_baseline < 5 or d / max(1, row_baseline) > relative_ratio)
                    
                    sx, sy = coords[i]
                    color = (255, 0, 0) # Blue
                    if is_marked:
                        marked_indices.append(i)
                        color = (0, 255, 0) # Green
                    
                    if save_viz:
                        cv2.circle(viz_img, (sx, sy), 12, color, 2)
                
                q_num = offset + q_idx
                if len(marked_indices) == 1:
                    subj_results[q_num] = ["A", "B", "C", "D"][marked_indices[0]]
                elif len(marked_indices) > 1:
                    subj_results[q_num] = "INVALID"
                    if save_viz:
                        for sx, sy in coords:
                            cv2.circle(viz_img, (sx, sy), 15, (0, 0, 255), 3)
                else:
                    subj_results[q_num] = "SKIPPED"
            
            results[subj] = subj_results

        if save_viz:
            output_dir = r"f:\Medjeex\Medjeex-OMR-Engine\data\neet"
            if not os.path.exists(output_dir): os.makedirs(output_dir)
            viz_path = os.path.join(output_dir, os.path.basename(image_path))
            cv2.imwrite(viz_path, viz_img)
            
        return results
