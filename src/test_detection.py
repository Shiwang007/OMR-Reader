import cv2
from processor import OMREngine
import os

def test():
    image_path = r"f:\Medjeex\Docx-Parser\WhatsApp Image 2026-04-23 at 1.56.06 PM.jpeg"
    if not os.path.exists(image_path):
        print(f"File not found: {image_path}")
        return

    print(f"Loading image: {image_path}")
    image = cv2.imread(image_path)
    engine = OMREngine()
    
    print("Preprocessing...")
    thresh = engine.preprocess(image)
    cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\data\debug_thresh.jpg", thresh)
    
    print("Detecting boxes...")
    boxes = engine.find_subject_boxes(thresh)
    
    print(f"Found {len(boxes)} subject boxes.")
    
    # Save a debug image to see what was detected
    debug_img = image.copy()
    for i, b in enumerate(boxes):
        x, y, w, h = b
        cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0, 255, 0), 5)
        cv2.putText(debug_img, f"Box {i+1}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 5)
    
    output_path = r"f:\Medjeex\Medjeex-OMR-Engine\data\debug_detection.jpg"
    cv2.imwrite(output_path, debug_img)
    print(f"Debug image saved to: {output_path}")

if __name__ == "__main__":
    test()
