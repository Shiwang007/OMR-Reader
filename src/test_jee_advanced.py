import os
import json
import cv2
from jee_advanced_processor import JEEAdvancedOMREngine

import sys

def main():
    engine = JEEAdvancedOMREngine()
    image_path = r"f:\Medjeex\Medjeex-OMR-Engine\Advance omr 1\Image (3).jpg"
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    
    print(f"Processing image: {image_path}")

    results, warped, vis_img = engine.process_omr(image_path)

    print("\n--- OMR Extraction Results ---")
    print(f"Roll Number: {results['roll_number']}")
    print("\nSubjects Breakdown:")
    
    for subj, q_dict in results["subjects"].items():
        print(f"\n[{subj}]")
        for q_key, val in q_dict.items():
            print(f"  {q_key}: {val}")

    out_dir = r"f:\Medjeex\Medjeex-OMR-Engine\output"
    os.makedirs(out_dir, exist_ok=True)
    
    json_path = os.path.join(out_dir, "results_Image_(3).json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved JSON results to {json_path}")

    vis_path = os.path.join(out_dir, "visualized_Image_(3).jpg")
    cv2.imwrite(vis_path, vis_img)
    print(f"Saved visualization overlay to {vis_path}")

if __name__ == "__main__":
    main()
