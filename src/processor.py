"""
OMR Processor — Absolute Coordinate Engine
============================================
Uses absolute pixel coordinates from template.json to extract answers.

The template stores exact (abs_x, abs_y) positions for every bubble.
For a new scan, the engine:
  1. Finds the bold header line to determine the Y-anchor
  2. Calculates the vertical shift between the calibration image and this scan
  3. Applies the shift to every bubble coordinate
  4. Reads the fill density at each shifted coordinate
"""

import cv2
import numpy as np
import imutils
import json
from typing import Dict


class OMREngine:
    def __init__(self):
        self.fill_threshold = 0.30
        self.template_path = r"f:\Medjeex\Medjeex-OMR-Engine\templates\template.json"

    # ──────────────────────────────────────────────────────
    # FIND THE BOLD HEADER LINE
    # ──────────────────────────────────────────────────────
    def find_header_line(self, image) -> int:
        """
        Finds the Y position of the bold horizontal line that sits
        just above the subject headers (PHYSICS | CHEMISTRY | ...).
        Returns the Y coordinate (absolute pixels).
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Look for long horizontal edges
        h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (80, 3))
        detect_h = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, h_kernel, iterations=1)

        cnts = cv2.findContours(detect_h, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        # Filter for lines that span at least 60% of the image width
        h, w = image.shape[:2]
        wide_lines = []
        for c in cnts:
            x, y, lw, lh = cv2.boundingRect(c)
            if lw > w * 0.6:
                wide_lines.append((y, lw))

        if not wide_lines:
            # Fallback: assume header is at ~22% of image height
            return int(h * 0.22)

        # Sort by Y and pick the one closest to the expected header position (~22%)
        wide_lines.sort()
        expected_y = h * 0.22
        best = min(wide_lines, key=lambda yl: abs(yl[0] - expected_y))
        return best[0]

    # ──────────────────────────────────────────────────────
    # PROCESS A FULL OMR SHEET
    # ──────────────────────────────────────────────────────
    def process_full_sheet(self, image_path: str) -> Dict:
        image = cv2.imread(image_path)
        if image is None:
            return {"error": "Image not found"}

        # 1. Load template (absolute coordinates from calibration image)
        with open(self.template_path, 'r') as f:
            template = json.load(f)

        # 2. Find the header line on THIS scan
        scan_header_y = self.find_header_line(image)

        # 3. The template was calibrated with HEADER_Y = 351.
        #    Calculate the vertical shift between calibration and this scan.
        CALIBRATION_HEADER_Y = 351
        y_shift = scan_header_y - CALIBRATION_HEADER_Y

        # 4. Prepare the image for extraction
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        extraction_gray = cv2.medianBlur(gray, 3)
        _, extraction_thresh = cv2.threshold(
            extraction_gray, 0, 255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )

        # 5. Extract answers
        final_results = {}
        for subj, questions in template.items():
            subj_results = {}

            # ── Self-healing: fine-tune y_shift using actual bubble positions ──
            fine_shifts = []
            for q_idx in range(5, min(40, len(questions))):
                for opt_idx in range(4):
                    coord = questions[q_idx][opt_idx]
                    ax = int(coord['abs_x'])
                    ay = int(coord['abs_y']) + y_shift

                    # Bounds check
                    if ay - 15 < 0 or ay + 15 >= image.shape[0]: continue
                    if ax - 10 < 0 or ax + 10 >= image.shape[1]: continue

                    roi = extraction_thresh[ay - 15:ay + 15, ax - 10:ax + 10]
                    if roi.size > 0 and (cv2.countNonZero(roi) / float(roi.size)) > 0.35:
                        M = cv2.moments(roi)
                        if M["m00"] > 0:
                            local_cy = int(M["m01"] / M["m00"]) - 15
                            fine_shifts.append(local_cy)

            fine_shift = int(np.median(fine_shifts)) if fine_shifts else 0
            total_shift = y_shift + fine_shift

            # ── Read each bubble ──
            for q_idx, row_coords in enumerate(questions):
                q_num = q_idx + 1
                marked = []
                options = ["A", "B", "C", "D"]

                for opt_idx, coord in enumerate(row_coords):
                    ax = int(coord['abs_x'])
                    ay = int(coord['abs_y']) + total_shift

                    # Bounds check
                    if ay - 10 < 0 or ay + 10 >= image.shape[0]: continue
                    if ax - 10 < 0 or ax + 10 >= image.shape[1]: continue

                    size = 10  # bubble radius = 10px
                    roi = extraction_thresh[ay - size:ay + size, ax - size:ax + size]
                    if roi.size == 0:
                        continue

                    density = cv2.countNonZero(roi) / float(roi.size)
                    if density > self.fill_threshold:
                        marked.append(options[opt_idx])

                ans = "SKIPPED"
                if len(marked) == 1:
                    ans = marked[0]
                elif len(marked) > 1:
                    ans = "INVALID"
                subj_results[q_num] = ans

            final_results[subj] = subj_results

        return final_results

    # ──────────────────────────────────────────────────────
    # VISUALIZE — Draw green dots where the engine "looked"
    # ──────────────────────────────────────────────────────
    def visualize_results(self, image_path: str, results: Dict) -> np.ndarray:
        image = cv2.imread(image_path)
        if image is None:
            return None

        with open(self.template_path, 'r') as f:
            template = json.load(f)

        scan_header_y = self.find_header_line(image)
        CALIBRATION_HEADER_Y = 351
        y_shift = scan_header_y - CALIBRATION_HEADER_Y

        # Prepare extraction thresh for fine-shift calculation
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        extraction_gray = cv2.medianBlur(gray, 3)
        _, extraction_thresh = cv2.threshold(
            extraction_gray, 0, 255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )

        # Draw header line
        cv2.line(image, (0, scan_header_y), (image.shape[1], scan_header_y), (0, 0, 255), 2)

        colors = [(0, 0, 255), (0, 180, 0), (255, 0, 0), (0, 165, 255)]
        subj_names = list(template.keys())

        for si, (subj, questions) in enumerate(template.items()):
            color = colors[si % len(colors)]

            # Recalculate fine-shift for this subject
            fine_shifts = []
            for q_idx in range(5, min(40, len(questions))):
                for opt_idx in range(4):
                    coord = questions[q_idx][opt_idx]
                    ax = int(coord['abs_x'])
                    ay = int(coord['abs_y']) + y_shift
                    if ay - 15 < 0 or ay + 15 >= image.shape[0]: continue
                    if ax - 10 < 0 or ax + 10 >= image.shape[1]: continue
                    roi = extraction_thresh[ay - 15:ay + 15, ax - 10:ax + 10]
                    if roi.size > 0 and (cv2.countNonZero(roi) / float(roi.size)) > 0.35:
                        M = cv2.moments(roi)
                        if M["m00"] > 0:
                            fine_shifts.append(int(M["m01"] / M["m00"]) - 15)
            fine_shift = int(np.median(fine_shifts)) if fine_shifts else 0
            total_shift = y_shift + fine_shift

            for q_idx, row_coords in enumerate(questions):
                for opt_idx, coord in enumerate(row_coords):
                    ax = int(coord['abs_x'])
                    ay = int(coord['abs_y']) + total_shift
                    cv2.circle(image, (ax, ay), 5, color, -1)

        return image
