import cv2
import numpy as np
import imutils
import json
from typing import Dict

class OMREngine:
    """
    OMR Engine — High-Resolution (2480x3442)
    Now supports both Y-shift and X-shift alignment.
    """

    def __init__(self):
        self.fill_threshold = 0.40
        self.relative_ratio = 1.5
        self.template_path = r"f:\Medjeex\Medjeex-OMR-Engine\templates\template.json"

    # -------------------- Y SHIFT --------------------
    def compute_y_shift(self, image: np.ndarray) -> int:
        h = image.shape[0]

        cal_h = 3442
        cal_first_row = 960.4

        expected_first_row = cal_first_row * (h / cal_h)
        return int(round(expected_first_row - cal_first_row))

    # -------------------- X SHIFT (NEW) --------------------
    def compute_x_shift(self, image: np.ndarray) -> int:
        """
        Positive value → shift RIGHT
        Tune this once (10–20 works for your case)
        """
        return 50  # 🔥 adjust if needed

    # -------------------- MAIN --------------------
    def process_full_sheet(self, image_path: str) -> Dict:
        image = cv2.imread(image_path)
        if image is None:
            return {"error": "Image not found"}

        with open(self.template_path, 'r') as f:
            template = json.load(f)

        y_shift = self.compute_y_shift(image)
        x_shift = self.compute_x_shift(image)   # ✅ NEW

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.medianBlur(gray, 3)
        _, thresh = cv2.threshold(
            blurred, 0, 255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )

        h_img, w_img = image.shape[:2]
        final_results = {}

        for subj, questions in template.items():
            subj_results = {}

            # -------- Fine Y alignment --------
            fine_shifts = []
            for q_idx in range(5, min(40, len(questions))):
                for opt_idx in range(4):
                    coord = questions[q_idx][opt_idx]

                    ax = int(coord['abs_x']) + x_shift   # ✅ UPDATED
                    ay = int(coord['abs_y']) + y_shift

                    r = 25
                    if r < ay < h_img - r and r < ax < w_img - r:
                        roi = thresh[ay - r:ay + r, ax - r:ax + r]
                        fill = cv2.countNonZero(roi) / float(roi.size)

                        if fill > 0.25:
                            M = cv2.moments(roi)
                            if M["m00"] > 0:
                                cy_local = int(M["m01"] / M["m00"]) - r
                                fine_shifts.append(cy_local)

            total_shift = y_shift + (int(np.median(fine_shifts)) if fine_shifts else 0)

            # -------- Bubble Reading --------
            global_q_offset = list(template.keys()).index(subj) * len(questions)

            for q_idx, row_coords in enumerate(questions):
                q_num = global_q_offset + q_idx + 1
                densities = []

                for opt_idx, coord in enumerate(row_coords):
                    ax = int(coord['abs_x']) + x_shift   # ✅ UPDATED
                    ay = int(coord['abs_y']) + total_shift

                    size = 16
                    if size < ay < h_img - size and size < ax < w_img - size:
                        roi = thresh[ay - size:ay + size, ax - size:ax + size]
                        density = cv2.countNonZero(roi) / float(roi.size)
                    else:
                        density = 0.0

                    densities.append(density)

                if not densities or max(densities) < 0.01:
                    subj_results[q_num] = "SKIPPED"
                    continue

                baseline = np.median(densities)
                marked = []

                for i, d in enumerate(densities):
                    if d > self.fill_threshold and (baseline < 0.01 or d / baseline > self.relative_ratio):
                        marked.append(["A", "B", "C", "D"][i])

                if len(marked) == 1:
                    subj_results[q_num] = marked[0]
                elif len(marked) > 1:
                    subj_results[q_num] = "INVALID"
                else:
                    subj_results[q_num] = "SKIPPED"

            final_results[subj] = subj_results

        return final_results

    # -------------------- VISUALIZATION --------------------
    def visualize_results(self, image_path: str, results: Dict) -> np.ndarray:
        image = cv2.imread(image_path)
        if image is None:
            return None

        with open(self.template_path, 'r') as f:
            template = json.load(f)

        y_shift = self.compute_y_shift(image)
        x_shift = self.compute_x_shift(image)   # ✅ NEW

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.medianBlur(gray, 3)
        _, thresh = cv2.threshold(
            blurred, 0, 255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )

        h_img, w_img = image.shape[:2]
        colors = [(0, 0, 255), (0, 180, 0), (255, 0, 0), (0, 165, 255)]

        for si, (subj, questions) in enumerate(template.items()):
            color = colors[si % 4]

            fine_shifts = []
            for q_idx in range(5, min(40, len(questions))):
                for opt_idx in range(4):
                    coord = questions[q_idx][opt_idx]

                    ax = int(coord['abs_x']) + x_shift   # ✅ UPDATED
                    ay = int(coord['abs_y']) + y_shift

                    r = 25
                    if r < ay < h_img - r and r < ax < w_img - r:
                        roi = thresh[ay - r:ay + r, ax - r:ax + r]

                        if cv2.countNonZero(roi) / float(roi.size) > 0.25:
                            M = cv2.moments(roi)
                            if M["m00"] > 0:
                                fine_shifts.append(int(M["m01"] / M["m00"]) - r)

            total_shift = y_shift + (int(np.median(fine_shifts)) if fine_shifts else 0)

            for row in questions:
                for coord in row:
                    cx = int(coord['abs_x']) + x_shift   # ✅ UPDATED
                    cy = int(coord['abs_y']) + total_shift
                    cv2.circle(image, (cx, cy), 8, color, -1)

        return image