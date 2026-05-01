import cv2
import numpy as np

def get_bubble_center(thresh, x_range, y_range):
    roi = thresh[y_range[0]:y_range[1], x_range[0]:x_range[1]]
    contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    valid_cnts = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 500 < area < 3000:
            valid_cnts.append(cnt)
    
    if not valid_cnts: return None
    best_cnt = max(valid_cnts, key=cv2.contourArea)
    M = cv2.moments(best_cnt)
    if M["m00"] > 0:
        return (int(M["m10"] / M["m00"]) + x_range[0], int(M["m01"] / M["m00"]) + y_range[0])
    return None

def calibrate_v4():
    image = cv2.imread(r'f:\Medjeex\Medjeex-OMR-Engine\omr\Image.jpg')
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Use adaptive threshold or Otsu for better bubble detection
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    points = {
        "Phy Q1 A": ((350, 450), (780, 850)),
        "Phy Q20 A": ((350, 450), (2180, 2260)),
        "Chem Q26 A": ((1080, 1180), (780, 850)),
        "Chem Q45 A": ((1080, 1180), (2180, 2260)),
        "Math Q51 A": ((1800, 1900), (780, 850)),
        "Math Q70 A": ((1800, 1900), (2180, 2260)),
    }
    
    for name, (xr, yr) in points.items():
        c = get_bubble_center(thresh, xr, yr)
        print(f"{name}: {c}")

if __name__ == "__main__":
    calibrate_v4()
