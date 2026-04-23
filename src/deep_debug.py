import cv2
import numpy as np
from processor import OMREngine
import json

def deep_debug():
    image_path = r"f:\Medjeex\Medjeex-OMR-Engine\WhatsApp Image 2026-04-23 at 3.17.12 PM.jpeg"
    image = cv2.imread(image_path)
    engine = OMREngine()
    
    # Let's inspect Physics Q14 A (which should be empty)
    # and Chemistry Q47 D (which should be filled)
    
    # 1. Get extraction thresh
    ext_thresh = engine.get_extraction_thresh(image)
    
    # 2. Get boxes
    thresh = engine.preprocess(image)
    boxes = engine.find_subject_boxes(thresh)
    
    # 3. Load template
    with open(r"f:\Medjeex\Medjeex-OMR-Engine\templates\template.json", "r") as f:
        template = json.load(f)
        
    # Inspect Physics Q14 (Row 13, Index 13*4)
    x, y, w, h = boxes[0]
    bx, by = template["Physics"][13*4] # Q14 A
    size = 12
    roi = ext_thresh[y+by-size:y+by+size, x+bx-size:x+bx+size]
    
    cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\data\debug_q14_a.jpg", roi)
    print("Debug ROI for Q14 A saved.")

if __name__ == "__main__":
    deep_debug()
