import cv2
import numpy as np
import json

def save_crop():
    image = cv2.imread(r'f:\Medjeex\Medjeex-OMR-Engine\omr\Image.jpg')
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.medianBlur(gray, 5)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    with open(r'f:\Medjeex\Medjeex-OMR-Engine\templates\jee_mains_template.json', 'r') as f:
        template = json.load(f)
    
    subj = "Physics"
    q_idx = 0 
    row = template["page1"][subj][q_idx]
    
    for i, c in enumerate(row):
        x, y = int(c['abs_x']), int(c['abs_y'])
        size = 20
        crop = thresh[y-size:y+size, x-size:x+size]
        cv2.imwrite(f'f:\\Medjeex\\Medjeex-OMR-Engine\\crop_q1_{["A","B","C","D"][i]}.jpg', crop)
    print("Crops saved.")

if __name__ == "__main__":
    save_crop()
