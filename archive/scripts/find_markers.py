import cv2
import numpy as np

def find_markers_v2(image_path):
    image = cv2.imread(image_path)
    h_img, w_img = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)
    
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    corners = {
        "TL": (0, 0), "TR": (w_img, 0),
        "BL": (0, h_img), "BR": (w_img, h_img)
    }
    found = {}
    
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = cv2.contourArea(cnt)
        if 2000 < area < 20000:
            M = cv2.moments(cnt)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
                # Check which corner this is closest to
                for name, pos in corners.items():
                    dist = np.sqrt((cx - pos[0])**2 + (cy - pos[1])**2)
                    if dist < 500: # Within 500px of a corner
                        if name not in found or dist < found[name][1]:
                            found[name] = ((cx, cy), dist)
    
    return {k: v[0] for k, v in found.items()}

if __name__ == "__main__":
    image_path = r'f:\Medjeex\Medjeex-OMR-Engine\omr\Image.jpg'
    markers = find_markers_v2(image_path)
    print(f"Markers found: {markers}")
