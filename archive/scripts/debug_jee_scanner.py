import cv2
import json
import os
import numpy as np
from src.jee_processor import JEEOMREngine

def debug_scanner():
    engine = JEEOMREngine()
    image_path = r'f:\Medjeex\Medjeex-OMR-Engine\JEE_MAINS_SAMPLE_FILLED.jpg'
    
    full_img = cv2.imread(image_path)
    h, w = full_img.shape[:2]
    mid = h // 2
    
    page1 = full_img[0:mid, :]
    
    # Draw circles on Page 1 for debugging
    template = engine.template["page1"]
    for subj, questions in template.items():
        for row in questions:
            for coord in row:
                cx, cy = int(coord['abs_x']), int(coord['abs_y'])
                cv2.circle(page1, (cx, cy), 12, (0, 0, 255), 2)
    
    cv2.imwrite(r'f:\Medjeex\Medjeex-OMR-Engine\debug_page1.jpg', page1)
    print("Debug image saved at f:\\Medjeex\\Medjeex-OMR-Engine\\debug_page1.jpg")

if __name__ == "__main__":
    debug_scanner()
