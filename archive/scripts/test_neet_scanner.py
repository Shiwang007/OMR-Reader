import os
import json
from src.neet_processor import NEETOMREngine

def test_neet_scan():
    engine = NEETOMREngine()
    image_path = r"f:\Medjeex\Medjeex-OMR-Engine\omr\Image.jpg"
    
    print(f"--- SCANNING NEET OMR: {os.path.basename(image_path)} ---")
    results = engine.process_sheet(image_path)
    
    for subj in ["Physics", "Chemistry", "Biology I", "Biology II"]:
        attempted = sum(1 for v in results[subj].values() if v not in ["SKIPPED", "INVALID"])
        print(f"{subj:12}: {attempted} / 45 attempted")
        # Print first 3 results
        first_3 = {k: results[subj][k] for k in list(results[subj].keys())[:3]}
        print(f"  First 3: {first_3}")

    output_path = r"f:\Medjeex\Medjeex-OMR-Engine\data\neet_test_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n[SUCCESS] Results saved to {output_path}")
    print(f"[SUCCESS] Visualization saved to f:\\Medjeex\\Medjeex-OMR-Engine\\data\\viz_neet\\Image.jpg")

if __name__ == "__main__":
    test_neet_scan()
