"""
OMR Calibration Script — Measured Grid Projection
===================================================
Generates template.json using MEASURED physical properties from the OMR sheet.

Measured values (from measure_grid.py on calibration image):
  - Bold header line:     Y = 351 (widest horizontal line)
  - Row 1 offset:         40 px below the bold line
  - Row pitch:            19.0 px
  - Bubble radius:        10 px
  - Option spacing (A→B): 34.7 px

  Subject Option-A X centers (absolute):
    Physics:    137
    Chemistry:  369
    Biology I:  601
    Biology II: 833
"""

import cv2
import numpy as np
import json

# ──────────────────────────────────────────────
# MEASURED CONSTANTS (from the calibration image)
# ──────────────────────────────────────────────
HEADER_Y = 351          # The bold horizontal line Y position (absolute)
ROW1_OFFSET = 72        # First row is 72px below the header line (skips subject header text)
ROW_PITCH = 19.0        # Vertical distance between row centers
NUM_ROWS = 45           # Questions per subject
NUM_OPTIONS = 4         # A, B, C, D
OPTION_SPACING = 34.7   # Horizontal distance between option centers

# Absolute X center of Option A for each subject
SUBJECT_A_X = {
    "Physics":    137,
    "Chemistry":  369,
    "Biology I":  601,
    "Biology II": 833,
}


def calibrate():
    image_path = r"f:\Medjeex\Medjeex-OMR-Engine\WhatsApp Image 2026-04-23 at 3.17.12 PM.jpeg"
    image = cv2.imread(image_path)
    if image is None:
        print("ERROR: Calibration image not found.")
        return

    h, w = image.shape[:2]
    print(f"Calibration image: {w} x {h}")
    print(f"Header Y: {HEADER_Y}")
    print(f"Row 1 Y:  {HEADER_Y + ROW1_OFFSET}")
    print(f"Row 45 Y: {HEADER_Y + ROW1_OFFSET + (NUM_ROWS - 1) * ROW_PITCH:.0f}")
    print()

    template = {}
    for subj, a_x in SUBJECT_A_X.items():
        subj_data = []
        for row in range(NUM_ROWS):
            # Absolute Y of this row's bubble center
            abs_y = HEADER_Y + ROW1_OFFSET + (row * ROW_PITCH)
            row_bubbles = []
            for opt in range(NUM_OPTIONS):
                # Absolute X of this option's bubble center
                abs_x = a_x + (opt * OPTION_SPACING)
                row_bubbles.append({
                    "abs_x": round(abs_x, 1),
                    "abs_y": round(abs_y, 1),
                })
            subj_data.append(row_bubbles)
        template[subj] = subj_data
        print(f"{subj}: Row 1 at ({a_x}, {HEADER_Y + ROW1_OFFSET}), "
              f"Row 45 at ({a_x}, {HEADER_Y + ROW1_OFFSET + 44 * ROW_PITCH:.0f})")

    # Save
    out_path = r"f:\Medjeex\Medjeex-OMR-Engine\templates\template.json"
    with open(out_path, "w") as f:
        json.dump(template, f, indent=2)
    print(f"\nTemplate saved to: {out_path}")
    print(f"Total entries: {sum(len(q) for q in template.values())} rows × 4 options")

    # ── Draw debug overlay ──
    debug = image.copy()
    colors = [(0, 0, 255), (0, 180, 0), (255, 0, 0), (0, 165, 255)]
    for si, (subj, rows) in enumerate(template.items()):
        color = colors[si]
        for row in rows:
            for bubble in row:
                cx, cy = int(bubble["abs_x"]), int(bubble["abs_y"])
                cv2.circle(debug, (cx, cy), 10, color, 1)
    # Draw the header line
    cv2.line(debug, (0, HEADER_Y), (w, HEADER_Y), (0, 0, 255), 2)
    cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\data\debug_calibration.jpg", debug)
    print("Debug overlay saved: data/debug_calibration.jpg")


if __name__ == "__main__":
    calibrate()
