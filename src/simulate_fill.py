import cv2
import numpy as np
from processor import OMREngine
import os
import json

def simulate():
    master_path = r"f:\Medjeex\Docx-Parser\WhatsApp Image 2026-04-23 at 1.56.06 PM.jpeg"
    attempts_file = r"f:\Medjeex\Docx-Parser\attempts.md"
    
    if not os.path.exists(master_path):
        print("Master scan not found.")
        return

    # Load blank sheet
    image = cv2.imread(master_path)
    engine = OMREngine()
    
    # Use the same logic as the processor to find and split boxes
    thresh = engine.preprocess(image)
    boxes = engine.find_subject_boxes(thresh)
    
    if len(boxes) != 4:
        print(f"Failed to find 4 boxes. Found {len(boxes)}")
        return

    # Parse attempts.md
    attempts = {}
    with open(attempts_file, "r", encoding="utf-8") as f:
        for line in f:
            if "-" in line and len(line) > 3:
                # Option is usually at the start (e.g. "A-1,2" or "A - 1,2")
                parts = line.split("-", 1) # Split only on the first hyphen
                if len(parts) != 2: continue
                
                option = parts[0].strip()
                if option not in ["A", "B", "C", "D"]: continue
                
                q_str = parts[1].strip()
                q_tokens = q_str.split(",")
                for token in q_tokens:
                    token = token.strip()
                    if "-" in token: # Range handling (e.g. "20-25")
                        try:
                            start, end = token.split("-")
                            for q in range(int(start), int(end) + 1):
                                attempts[q] = option
                        except:
                            pass
                    else:
                        try:
                            attempts[int(token)] = option
                        except:
                            pass

    # Load template
    template_path = r"f:\Medjeex\Medjeex-OMR-Engine\templates\template.json"
    with open(template_path, "r") as f:
        template = json.load(f)

    subjects = ["Physics", "Chemistry", "Biology I", "Biology II"]

    # Fill bubbles in the image
    for i, box_roi in enumerate(boxes):
        subj = subjects[i]
        x, y, w, h = box_roi
        bubble_coords = template[subj]
        
        for q_idx in range(45):
            q_num = (i * 45) + (q_idx + 1)
            if q_num in attempts:
                option = attempts[q_num]
                opt_idx = ["A", "B", "C", "D"].index(option)
                
                # Get coordinates from template
                try:
                    bx, by = bubble_coords[q_idx * 4 + opt_idx]
                    # Convert ROI coords back to full image coords
                    abs_x = x + bx
                    abs_y = y + by
                    # Draw a solid black circle
                    cv2.circle(image, (abs_x, abs_y), 10, (0, 0, 0), -1)
                except IndexError:
                    print(f"Warning: Bubble index {q_idx * 4 + opt_idx} missing for {subj} Q{q_num}")

    output_path = r"f:\Medjeex\Medjeex-OMR-Engine\data\simulated_filled.jpg"
    cv2.imwrite(output_path, image)
    print(f"Simulated filled OMR saved to: {output_path}")

if __name__ == "__main__":
    simulate()
