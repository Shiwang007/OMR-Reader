import cv2
import numpy as np
import json

def debug_red_morphed():
    image = cv2.imread(r'f:\Medjeex\Medjeex-OMR-Engine\omr\Image.jpg')
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.medianBlur(gray, 5)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    kernel = np.ones((5,5), np.uint8)
    morphed = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    
    with open(r'f:\Medjeex\Medjeex-OMR-Engine\templates\jee_mains_template.json', 'r') as f:
        template = json.load(f)
    
    def get_intensity(thresh, x, y, size=15):
        roi = thresh[int(y-size):int(y+size), int(x-size):int(x+size)]
        return cv2.countNonZero(roi) / float(roi.size)

    # Physics Q20 (Index 19)
    row = template["page1"]["Physics"][19]
    print(f"Morphed Intensity for Physics Q20 (Red Mark):")
    for i, c in enumerate(row):
        intensity = get_intensity(morphed, c['abs_x'], c['abs_y'])
        print(f"  Option {['A','B','C','D'][i]}: {intensity:.4f}")

if __name__ == "__main__":
    debug_red_morphed()
