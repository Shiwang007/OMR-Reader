import cv2
import numpy as np
import json

# ──────────────────────────────────────────────
# FINAL CALIBRATION CONSTANTS (from Image (2).jpg — 2480x3442)
# Measured using HoughCircles + row/column clustering
# ──────────────────────────────────────────────
FIRST_ROW_Y = 960.4   # Y-center of Question 1 / 46 / 91 / 136
ROW_PITCH   = 41.0     # Vertical spacing between rows
NUM_ROWS    = 45       # 45 questions per subject
NUM_OPTIONS = 4        # A, B, C, D
OPTION_SPACING = 74.6  # Horizontal spacing between options

SUBJECT_A_X = {
    "Physics":    314.1,
    "Chemistry":  813.0,
    "Biology I":  1313.1,
    "Biology II": 1813.0,
}

def calibrate(debug_image_path=None):
    template = {}
    for subj, a_x in SUBJECT_A_X.items():
        subj_data = []
        for row in range(NUM_ROWS):
            abs_y = FIRST_ROW_Y + (row * ROW_PITCH)
            row_bubbles = []
            for opt in range(NUM_OPTIONS):
                abs_x = a_x + (opt * OPTION_SPACING)
                row_bubbles.append({
                    "abs_x": round(abs_x, 1),
                    "abs_y": round(abs_y, 1),
                })
            subj_data.append(row_bubbles)
        template[subj] = subj_data

    out_path = r"f:\Medjeex\Medjeex-OMR-Engine\templates\template.json"
    with open(out_path, "w") as f:
        json.dump(template, f, indent=2)
    print(f"Template saved: {out_path}")
    print(f"  Subjects: {list(template.keys())}")
    print(f"  Rows per subject: {NUM_ROWS}")
    print(f"  Total bubbles: {NUM_ROWS * NUM_OPTIONS * len(SUBJECT_A_X)}")

    # Debug overlay on reference image
    if debug_image_path:
        image = cv2.imread(debug_image_path)
        if image is not None:
            colors = [(0, 0, 255), (0, 180, 0), (255, 0, 0), (0, 165, 255)]
            for si, (subj, rows) in enumerate(template.items()):
                color = colors[si % 4]
                for row in rows:
                    for bubble in row:
                        cx, cy = int(bubble["abs_x"]), int(bubble["abs_y"])
                        cv2.circle(image, (cx, cy), 16, color, 2)
            out = r"f:\Medjeex\Medjeex-OMR-Engine\data\debug_calibration_HIRES.jpg"
            cv2.imwrite(out, image)
            print(f"Debug overlay saved: {out}")

if __name__ == "__main__":
    calibrate(r"f:\Medjeex\Medjeex-OMR-Engine\omr\Image (2).jpg")
