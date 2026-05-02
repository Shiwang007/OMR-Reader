import cv2
import numpy as np
import json
import os
from typing import Dict, List

class JEEOMREngine:
    def __init__(self):
        self.fill_threshold = 0.60 
        self.template_path = r"f:\Medjeex\Medjeex-OMR-Engine\templates\jee_mains_template.json"
        with open(self.template_path, 'r') as f:
            self.template = json.load(f)

    def get_intensity(self, thresh, x, y, size=10):
        h, w = thresh.shape
        if size < x < w - size and size < y < h - size:
            roi = thresh[int(y-size):int(y+size), int(x-size):int(x+size)]
            return cv2.countNonZero(roi) / float(roi.size)
        return 0

    def process_page1(self, image_path: str, save_viz: bool = True) -> Dict:
        """Processes MCQ Page with Alignment Calibration and Visualization"""
        image = cv2.imread(image_path)
        viz_img = image.copy()
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Alignment Calibration: Pull slightly to the left
        x_shift = -20
        
        s_channel = hsv[:, :, 1]
        v_inv = cv2.bitwise_not(hsv[:, :, 2])
        combined = cv2.addWeighted(s_channel, 0.6, v_inv, 0.4, 0)
        
        results = {}
        page_data = self.template["page1"]
        
        sub_map = {
            "Physics": {"mcq": range(1, 21), "num": range(21, 26)},
            "Chemistry": {"mcq": range(26, 46), "num": range(46, 51)},
            "Mathematics": {"mcq": range(51, 71), "num": range(71, 76)}
        }
        
        mark_threshold = 120 
        
        for subj in ["Physics", "Chemistry", "Mathematics"]:
            subj_results = {}
            for q_idx, row in enumerate(page_data[subj]):
                densities = []
                for c in row:
                    x, y = int(c['abs_x'] + x_shift), int(c['abs_y'])
                    size = 12
                    roi = combined[y-size:y+size, x-size:x+size]
                    densities.append(np.mean(roi))
                
                marked = []
                for i, d in enumerate(densities):
                    color = (255, 0, 0) # Blue for empty
                    if d > mark_threshold:
                        marked.append(["A", "B", "C", "D"][i])
                        color = (0, 255, 0) # Green for mark
                    
                    if save_viz:
                        cv2.circle(viz_img, (int(row[i]['abs_x'] + x_shift), int(row[i]['abs_y'])), 12, color, 2)
                
                q_num = sub_map[subj]["mcq"][q_idx]
                if len(marked) == 1:
                    subj_results[q_num] = marked[0]
                elif len(marked) > 1:
                    subj_results[q_num] = "INVALID"
                    # Highlight invalid in Red
                    if save_viz:
                        for c in row:
                            cv2.circle(viz_img, (int(c['abs_x']), int(c['abs_y'])), 15, (0, 0, 255), 3)
                else:
                    subj_results[q_num] = "SKIPPED"
            
            # Add Numerical Placeholders
            for q_num in sub_map[subj]["num"]:
                subj_results[q_num] = "SKIPPED"
                
            results[subj] = subj_results
            
        if save_viz:
            output_dir = r"f:\Medjeex\Medjeex-OMR-Engine\data\jee"
            if not os.path.exists(output_dir): os.makedirs(output_dir)
            viz_path = os.path.join(output_dir, os.path.basename(image_path))
            cv2.imwrite(viz_path, viz_img)
            
        return results

    def process_page2(self, image_path: str) -> Dict:
        """Processes Numerical Page (Placeholder for future expansion)"""
        # Note: Numerical section is currently handled as SKIPPED placeholders in process_page1
        return {}

    def score_test(self, results: Dict, answer_key: Dict) -> Dict:
        """Calculates JEE Scores (+4/-1)"""
        summary = {}
        total_score = 0
        
        for subj in ["Physics", "Chemistry", "Mathematics"]:
            subj_score = 0
            correct = 0
            incorrect = 0
            
            for q_num, marked in results[subj].items():
                q_key = str(q_num)
                if q_key in answer_key:
                    correct_val = answer_key[q_key]
                    # Handle multiple correct options (list or comma-separated)
                    if isinstance(correct_val, list):
                        correct_options = correct_val
                    elif isinstance(correct_val, str) and "," in correct_val:
                        correct_options = [x.strip() for x in correct_val.split(",")]
                    else:
                        correct_options = [str(correct_val)]

                    if marked in correct_options:
                        subj_score += 4
                        correct += 1
                    elif marked != "SKIPPED" and marked != "INVALID":
                        subj_score -= 1
                        incorrect += 1
            
            summary[subj] = {
                "score": subj_score,
                "correct": correct,
                "incorrect": incorrect
            }
            total_score += subj_score
            
        summary["total_score"] = total_score
        return summary
