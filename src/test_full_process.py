import json
from processor import OMREngine
import os

def test_full():
    image_path = r"f:\Medjeex\Medjeex-OMR-Engine\data\simulated_filled.jpg"
    if not os.path.exists(image_path):
        print("Simulated image not found.")
        return

    engine = OMREngine()
    print("Processing full sheet...")
    results = engine.process_full_sheet(image_path)
    
    if "error" in results:
        print(f"Error: {results['error']}")
        return

    # Print a summary of counts
    total_answers = 0
    for subject, q_map in results.items():
        filled = [ans for q, ans in q_map.items() if ans != "SKIPPED"]
        print(f"{subject}: {len(filled)} answers found.")
        total_answers += len(filled)
    
    print(f"Total answers extracted: {total_answers}")
    
    # Save to JSON for inspection
    output_json = r"f:\Medjeex\Medjeex-OMR-Engine\data\results.json"
    with open(output_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to: {output_json}")

if __name__ == "__main__":
    test_full()
