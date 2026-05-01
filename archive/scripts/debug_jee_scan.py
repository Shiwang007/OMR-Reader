import cv2
import json
import os
import numpy as np
from src.jee_processor import JEEOMREngine

def debug_jee_scan():
    engine = JEEOMREngine()
    image_path = r'f:\Medjeex\Medjeex-OMR-Engine\omr\Image.jpg'
    
    if not os.path.exists(image_path):
        print(f"Error: {image_path} not found.")
        return

    image = cv2.imread(image_path)
    if image is None:
        print("Error: Could not read image.")
        return

    # Draw Page 1 MCQ circles
    template = engine.template["page1"]
    colors = [(0, 0, 255), (0, 180, 0), (255, 0, 0)] # BGR
    
    for si, (subj, questions) in enumerate(template.items()):
        color = colors[si % 3]
        for row in questions:
            for coord in row:
                cx, cy = int(coord['abs_x']), int(coord['abs_y'])
                cv2.circle(image, (cx, cy), 10, color, -1)
    
    debug_path = r'f:\Medjeex\Medjeex-OMR-Engine\debug_jee_scan_v1.jpg'
    cv2.imwrite(debug_path, image)
    print(f"Debug image saved at {debug_path}")

if __name__ == "__main__":
    debug_jee_scan()
