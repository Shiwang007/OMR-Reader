import os
import json
from src.neet_processor import NEETOMREngine

def run_batch_neet_individual_json():
    # Configuration
    input_dir = r"f:\Medjeex\Medjeex-OMR-Engine\omr_neet"
    output_dir = r"f:\Medjeex\Medjeex-OMR-Engine\data\neet"
    
    if not os.path.exists(input_dir):
        print(f"ERROR: Input directory {input_dir} not found.")
        return
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    engine = NEETOMREngine()

    # Get all images
    images = [f for f in os.listdir(input_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    print(f"--- GENERATING INDIVIDUAL JSON RESULTS ({len(images)} students) ---")

    for img_name in images:
        student_id = os.path.splitext(img_name)[0]
        img_path = os.path.join(input_dir, img_name)
        print(f"Processing: {student_id}...")
        
        try:
            # Get the raw scan (Subject -> Qnum -> Answer)
            raw_scan = engine.process_sheet(img_path, save_viz=True)
            
            # Format the output to match the Answer Key structure exactly
            student_json = {
                "Physics": {str(k): v for k, v in raw_scan["Physics"].items()},
                "Chemistry": {str(k): v for k, v in raw_scan["Chemistry"].items()},
                "Biology I": {str(k): v for k, v in raw_scan["Biology I"].items()},
                "Biology II": {str(k): v for k, v in raw_scan["Biology II"].items()}
            }
            
            # Save individual JSON for the student
            json_filename = f"{student_id}.json"
            json_path = os.path.join(output_dir, json_filename)
            with open(json_path, 'w') as f:
                json.dump(student_json, f, indent=2)
                
            print(f"  [SUCCESS] Saved to {json_filename}")
            
        except Exception as e:
            print(f"  [FAILED] {student_id}: {e}")

    print(f"\n--- ALL RESULTS GENERATED IN {output_dir} ---")

if __name__ == "__main__":
    run_batch_neet_individual_json()
