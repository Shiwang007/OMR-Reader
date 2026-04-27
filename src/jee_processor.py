import cv2
import numpy as np
import json
from typing import Dict, List

class JEEOMREngine:
    def __init__(self):
        self.fill_threshold = 0.35
        self.template_path = r"f:\Medjeex\Medjeex-OMR-Engine\templates\jee_mains_template.json"
        with open(self.template_path, 'r') as f:
            self.template = json.load(f)

    def get_intensity(self, thresh, x, y, size=12):
        h, w = thresh.shape
        if size < x < w - size and size < y < h - size:
            roi = thresh[int(y-size):int(y+size), int(x-size):int(x+size)]
            return cv2.countNonZero(roi) / float(roi.size)
        return 0

    def process_page1(self, image_path: str) -> Dict:
        """Processes MCQ Page"""
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(cv2.medianBlur(gray, 3), 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        results = {}
        page_data = self.template["page1"]
        
        q_counter = 1
        for subj in ["Physics", "Chemistry", "Mathematics"]:
            subj_results = {}
            for q_idx, row in enumerate(page_data[subj]):
                densities = [self.get_intensity(thresh, c['abs_x'], c['abs_y']) for c in row]
                
                marked = []
                for i, d in enumerate(densities):
                    if d > self.fill_threshold:
                        marked.append(["A", "B", "C", "D"][i])
                
                if len(marked) == 1:
                    subj_results[q_counter] = marked[0]
                elif len(marked) > 1:
                    subj_results[q_counter] = "INVALID"
                else:
                    subj_results[q_counter] = "SKIPPED"
                q_counter += 1
            results[subj] = subj_results
        return results

    def process_page2(self, image_path: str) -> Dict:
        """Processes Numerical Page"""
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(cv2.medianBlur(gray, 3), 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        results = {}
        page_data = self.template["page2"]
        
        q_start = 61
        for subj in ["Physics", "Chemistry", "Mathematics"]:
            subj_results = {}
            for q_idx, q_config in enumerate(page_data[subj]):
                # 1. Sign
                sign = ""
                minus_d = self.get_intensity(thresh, q_config["special"][0]['abs_x'], q_config["special"][0]['abs_y'])
                if minus_d > self.fill_threshold:
                    sign = "-"
                
                # 2. Digits
                integer_part = ""
                for col in q_config["digits"]:
                    densities = [self.get_intensity(thresh, c['abs_x'], c['abs_y']) for c in col]
                    marked = [i for i, d in enumerate(densities) if d > self.fill_threshold]
                    integer_part += str(marked[0]) if len(marked) == 1 else "?" 

                # 3. Decimals
                decimal_part = ""
                for col in q_config["decimals"]:
                    densities = [self.get_intensity(thresh, c['abs_x'], c['abs_y']) for c in col]
                    marked = [i for i, d in enumerate(densities) if d > self.fill_threshold]
                    decimal_part += str(marked[0]) if len(marked) == 1 else "?"

                # Construct final value
                if "?" in integer_part and "?" in decimal_part:
                    val = "SKIPPED"
                else:
                    integer_part = integer_part.replace("?", "0")
                    decimal_part = decimal_part.replace("?", "0")
                    val = f"{sign}{int(integer_part)}.{decimal_part}"
                
                subj_results[q_start] = val
                q_start += 1
            results[subj] = subj_results
        return results

    def score_test(self, student_answers: Dict, key: Dict) -> Dict:
        report = {"total_score": 0, "subjects": {}}
        
        for subj in ["Physics", "Chemistry", "Mathematics"]:
            subj_report = {"score": 0, "correct": 0, "incorrect": 0, "skipped": 0}
            
            # Combine MCQs and Numericals for this subject
            all_q = student_answers[subj]
            
            for q_num, ans in all_q.items():
                correct_ans = str(key.get(str(q_num)))
                
                if ans == "SKIPPED":
                    subj_report["skipped"] += 1
                elif str(ans) == correct_ans:
                    subj_report["correct"] += 1
                    subj_report["score"] += 4
                else:
                    subj_report["incorrect"] += 1
                    # Scoring logic: -1 for MCQ (1-60), 0 for Numerical (61-75)
                    if int(q_num) <= 60:
                        subj_report["score"] -= 1
            
            report["subjects"][subj] = subj_report
            report["total_score"] += subj_report["score"]
            
        return report

if __name__ == "__main__":
    # Test stub
    engine = JEEOMREngine()
    print("JEE OMR Engine initialized.")
