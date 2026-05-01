import cv2
import json
import os
import numpy as np
from src.jee_processor import JEEOMREngine

def test_actual_scan():
    engine = JEEOMREngine()
    image_path = r'f:\Medjeex\Medjeex-OMR-Engine\omr\Image.jpg'
    
    # Process Page 1 (MCQs)
    print("\n--- SCANNING JEE OMR (MCQs) ---")
    results = engine.process_page1(image_path)
    
    # Print Subject-wise Attempts
    total_attempted = 0
    for subj in ["Physics", "Chemistry", "Mathematics"]:
        attempted = [q for q, a in results[subj].items() if a not in ("SKIPPED", "INVALID")]
        print(f"{subj:12}: {len(attempted)} / 20 attempted")
        total_attempted += len(attempted)
        
        # Print specific marked answers for first 5 of each
        print(f"  First 5: { {k: results[subj][k] for k in list(results[subj].keys())[:5]} }")
    
    print(f"\nTOTAL MCQs ATTEMPTED: {total_attempted} / 60")
    
    # Save results to data folder
    save_path = r'f:\Medjeex\Medjeex-OMR-Engine\data\Image_jee_results.json'
    with open(save_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n[SUCCESS] Results saved to {save_path}")

if __name__ == "__main__":
    test_actual_scan()
