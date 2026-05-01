import cv2
import numpy as np

def find_chem_bubbles():
    image = cv2.imread(r'f:\Medjeex\Medjeex-OMR-Engine\omr\Image.jpg')
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    # Search whole Chemistry block area
    roi_x, roi_y, roi_w, roi_h = 1000, 750, 600, 100
    roi = thresh[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
    contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    bubbles = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 500 < area < 3000:
            M = cv2.moments(cnt)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"]) + roi_x
                cy = int(M["m01"] / M["m00"]) + roi_y
                bubbles.append((cx, cy))
    
    bubbles = sorted(bubbles, key=lambda b: b[0])
    print(f"Chemistry bubbles found in Q26 row: {bubbles}")

if __name__ == "__main__":
    find_chem_bubbles()
