import os
import json
from src.jee_processor import JEEOMREngine

def run_batch_jee_consolidated():
    # Setup paths
    input_dir = r"f:\Medjeex\Medjeex-OMR-Engine\omr_jee"
    output_dir = r"f:\Medjeex\Medjeex-OMR-Engine\data\jee"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    engine = JEEOMREngine()
    
    # Supported extensions
    valid_exts = (".jpg", ".jpeg", ".png")
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(valid_exts)]
    
    print(f"--- BATCH PROCESSING {len(files)} JEE OMR SHEETS ---")
    
    for filename in files:
        student_id = os.path.splitext(filename)[0]
        img_path = os.path.join(input_dir, filename)
        print(f"Processing: {student_id}...", end=" ", flush=True)
        
        try:
            # Process page and save visualization directly to data/jee/
            results = engine.process_page1(img_path, save_viz=True)
            
            # Save individual student JSON to data/jee/
            output_filename = f"{student_id}.json"
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            print("SUCCESS")
        except Exception as e:
            print(f"FAILED: {str(e)}")

    print(f"\n--- JEE BATCH COMPLETE. Results in {output_dir} ---")

if __name__ == "__main__":
    run_batch_jee_consolidated()
