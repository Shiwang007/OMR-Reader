from src.processor1 import OMREngine
import json, cv2, os

omr_dir = r"f:\Medjeex\Medjeex-OMR-Engine\omr"
images = [os.path.join(omr_dir, f) for f in os.listdir(omr_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

engine = OMREngine()

for img_path in images:
    filename = os.path.basename(img_path)
    print(f"\n--- SCANNING: {filename} ---")
    
    results = engine.process_full_sheet(img_path)
    
    # Save verification image
    visual = engine.visualize_results(img_path, results)
    base_name = os.path.splitext(filename)[0]
    save_name = f"{base_name}_verified.jpg"
    cv2.imwrite(os.path.join(r"f:\Medjeex\Medjeex-OMR-Engine\data", save_name), visual)
    
    total = 0
    for subj, qs in results.items():
        filled = [a for q, a in qs.items() if a not in ("SKIPPED", "INVALID")]
        print(f"{subj:10}: {len(filled):2} attempted")
        total += len(filled)
    print(f"TOTAL: {total}/180")
    
    # Save results
    res_name = f"{base_name}_results.json"
    with open(os.path.join(r"f:\Medjeex\Medjeex-OMR-Engine\data", res_name), "w") as f:
        json.dump(results, f, indent=2)

print("\n[SUCCESS] Both scans complete. Results saved in 'data' directory.")
