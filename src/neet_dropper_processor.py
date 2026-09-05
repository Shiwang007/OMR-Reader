import cv2
import numpy as np
import json
import os
from typing import Dict, Tuple, Optional

class NEETDropperOMREngine:
    """
    Dedicated OMR Processing Engine for NEET Dropper 1.O sheets.
    Format: 180 questions (45 questions x 4 subjects: Physics, Chemistry, Biology I, Biology II).
    Calibrated for 2480x3442 scans with dynamic shift and adaptive density estimation.
    """
    def __init__(self, template_path: Optional[str] = None):
        if template_path is None:
            self.template_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "templates",
                "neet_dropper_template.json"
            )
        else:
            self.template_path = template_path

        with open(self.template_path, 'r') as f:
            self.template = json.load(f)

        self.X_SHIFT = 0
        self.Y_SHIFT = 0
        self.CALIBRATION_HEIGHT = 3442
        self.CALIBRATION_WIDTH = 2480

    def compute_scaling_shift(self, h: int) -> int:
        """Compute Y-shift proportional to scan height variations."""
        cal_h = self.CALIBRATION_HEIGHT
        cal_first_row = 1008.9
        expected_first_row = cal_first_row * (h / cal_h)
        return int(round(expected_first_row - cal_first_row))

    def process_sheet(self, image_path: str, custom_x_shift: int = 0, custom_y_shift: int = 0) -> Tuple[Dict, np.ndarray]:
        """
        Process a NEET Dropper OMR sheet image and return detected answers + visualization image.
        """
        image = cv2.imread(image_path)
        if image is None:
            return {}, None

        h_img, w_img = image.shape[:2]
        viz_img = image.copy()

        # Image preprocessing for accurate bubble reading
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        morphed = cv2.bitwise_not(gray)

        total_x = self.X_SHIFT + custom_x_shift
        total_y = self.Y_SHIFT + custom_y_shift + self.compute_scaling_shift(h_img)

        results = {}
        start_q = 1

        subjects = ["Physics", "Chemistry", "Biology I", "Biology II"]

        for sec_name in subjects:
            rows = self.template.get(sec_name, [])
            sec_results = {}

            for q_idx, row in enumerate(rows):
                densities = []
                coords = []

                for c in row:
                    sx = int(round(c['abs_x'] + total_x))
                    sy = int(round(c['abs_y'] + total_y))
                    coords.append((sx, sy))

                    # 25x25 circular bubble ROI
                    r = 12
                    y1, y2 = max(0, sy - r), min(h_img, sy + r)
                    x1, x2 = max(0, sx - r), min(w_img, sx + r)
                    roi = morphed[y1:y2, x1:x2]
                    densities.append(np.mean(roi) if roi.size > 0 else 0.0)

                # Dynamic row baseline thresholding
                row_baseline = np.median(densities) if densities else 0.0
                marked = [
                    i for i, d in enumerate(densities)
                    if d > 75.0 and (row_baseline < 1.0 or d > row_baseline * 1.35)
                ]

                # Draw visualization
                for i, coord in enumerate(coords):
                    if i in marked:
                        color = (0, 220, 0) if len(marked) == 1 else (0, 0, 255)
                        cv2.circle(viz_img, coord, 13, color, -1)
                        cv2.circle(viz_img, coord, 13, (0, 100, 0), 2)
                    else:
                        cv2.circle(viz_img, coord, 12, (210, 210, 210), 1)

                q_num = start_q + q_idx
                if len(marked) == 1:
                    ans = ["A", "B", "C", "D"][marked[0]]
                elif len(marked) > 1:
                    ans = "INVALID"
                else:
                    ans = "SKIPPED"

                sec_results[str(q_num)] = ans

            results[sec_name] = sec_results
            start_q += len(rows)

        return results, viz_img

if __name__ == "__main__":
    import sys
    engine = NEETDropperOMREngine()
    sample_path = r"f:\Medjeex\Medjeex-OMR-Engine\NEET Dropper 1.O (2)\Image (2).jpg"
    res, viz = engine.process_sheet(sample_path)
    print("NEET Dropper Processing Results:")
    for subj, q_map in res.items():
        marked = {q: a for q, a in q_map.items() if a not in ["SKIPPED", "INVALID"]}
        invalid = {q: a for q, a in q_map.items() if a == "INVALID"}
        skipped = {q: a for q, a in q_map.items() if a == "SKIPPED"}
        print(f"  {subj}: {len(marked)} marked, {len(invalid)} invalid, {len(skipped)} skipped")
        if marked:
            print(f"    Marked answers: {marked}")
