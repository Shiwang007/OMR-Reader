import cv2
import numpy as np
import json

def debug_neet_row_morphed():
    image = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\omr\Image.jpg")
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    s_channel = hsv[:, :, 1]
    v_inv = cv2.bitwise_not(hsv[:, :, 2])
    combined = cv2.addWeighted(s_channel, 0.6, v_inv, 0.4, 0)
    
    kernel = np.ones((5,5), np.uint8)
    morphed = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel)
    
    with open(r"f:\Medjeex\Medjeex-OMR-Engine\templates\neet_template.json", "r") as f:
        template = json.load(f)
    
    # Biology I Q92
    row = template["Biology I"][1]
    
    print(f"Morphed Intensities for Biology I Q92:")
    densities = []
    for i, c in enumerate(row):
        x, y = int(c['abs_x']), int(c['abs_y'])
        size = 12
        roi = morphed[y-size:y+size, x-size:x+size]
        d = np.mean(roi)
        densities.append(d)
        print(f"  Option {['A','B','C','D'][i]}: {d:.4f}")
    
    row_max = max(densities)
    print(f"  Row Max: {row_max:.4f}")
    for i, d in enumerate(densities):
        ratio = d / (row_max + 0.1)
        print(f"  Ratio {['A','B','C','D'][i]}: {ratio:.4f}")

if __name__ == "__main__":
    debug_neet_row_morphed()
