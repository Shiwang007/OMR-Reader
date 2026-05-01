import cv2
import numpy as np
import json
import os

def compare_invalid_thresholds():
    engine_src = r"f:\Medjeex\Medjeex-OMR-Engine\src\neet_processor.py"
    with open(r"f:\Medjeex\Medjeex-OMR-Engine\templates\neet_template.json", "r") as f:
        template = json.load(f)
    
    images = [
        r"f:\Medjeex\Medjeex-OMR-Engine\omr_neet\Image (2).jpg",
        r"f:\Medjeex\Medjeex-OMR-Engine\omr_neet\Image (7).jpg"
    ]
    
    for img_path in images:
        print(f"\n--- ANALYZING INTENSITIES: {os.path.basename(img_path)} ---")
        image = cv2.imread(img_path)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        s_channel = hsv[:, :, 1]
        v_inv = cv2.bitwise_not(hsv[:, :, 2])
        combined = cv2.addWeighted(s_channel, 0.6, v_inv, 0.4, 0)
        kernel = np.ones((5,5), np.uint8)
        morphed = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel)
        
        for subj in ["Physics", "Chemistry", "Biology I", "Biology II"]:
            for q_idx, row in enumerate(template[subj]):
                densities = []
                for c in row:
                    x, y = int(c['abs_x']), int(c['abs_y'])
                    size = 12
                    roi = morphed[y-size:y+size, x-size:x+size]
                    densities.append(np.mean(roi))
                
                sorted_densities = sorted(densities, reverse=True)
                d1, d2 = sorted_densities[0], sorted_densities[1]
                
                # If there's a significant second mark (> 100 intensity)
                if d1 > 100 and d2 > 80:
                    ratio = d2 / d1
                    q_num = ({"Physics":1,"Chemistry":46,"Biology I":91,"Biology II":136}[subj]) + q_idx
                    print(f"  Q{q_num} ({subj}): Max={d1:.1f}, 2nd={d2:.1f}, Ratio={ratio:.3f}")

if __name__ == "__main__":
    compare_invalid_thresholds()
