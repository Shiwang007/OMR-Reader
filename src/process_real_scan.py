from processor import OMREngine
import json
import os
import cv2

def process_real():
    image_path = r"f:\Medjeex\Medjeex-OMR-Engine\WhatsApp Image 2026-04-23 at 3.17.12 PM.jpeg"
    if not os.path.exists(image_path):
        print("Real scan not found.")
        return

    engine = OMREngine()
    print("Processing Real Student Scan (Nishu)...")
    results = engine.process_full_sheet(image_path)
    
    if "error" in results:
        print(f"Error: {results['error']}")
        return

    # Visualize results
    print("Generating verification image...")
    visual_img = engine.visualize_results(image_path, results)
    visual_path = r"f:\Medjeex\Medjeex-OMR-Engine\data\nishu_verified_FINAL.jpg"
    os.makedirs(os.path.dirname(visual_path), exist_ok=True)
    cv2.imwrite(visual_path, visual_img)
    print(f"Verification image saved to: {visual_path}")

    # Print summary
    total_answers = 0
    for subject, q_map in results.items():
        filled = [ans for q, ans in q_map.items() if not ans.startswith("SKIPPED")]
        print(f"{subject}: {len(filled)} answers extracted.")
        total_answers += len(filled)
    
    print(f"Total extracted for Nishu: {total_answers}")
    
    # Save results
    output_json = r"f:\Medjeex\Medjeex-OMR-Engine\data\nishu_results.json"
    with open(output_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to: {output_json}")

if __name__ == "__main__":
    process_real()
