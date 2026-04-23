from src.processor import OMREngine
import json, cv2, os

images = [
    r"f:\Medjeex\Medjeex-OMR-Engine\WhatsApp Image 2026-04-23 at 3.17.12 PM.jpeg",
    r"f:\Medjeex\Medjeex-OMR-Engine\WhatsApp Image 2026-04-23 at 5.20.49 PM.jpeg"
]

engine = OMREngine()

for img_path in images:
    filename = os.path.basename(img_path)
    print(f"\n--- SCANNING: {filename} ---")
    
    results = engine.process_full_sheet(img_path)
    
    # Save verification image
    visual = engine.visualize_results(img_path, results)
    save_name = filename.replace(".jpeg", "_verified.jpg")
    cv2.imwrite(os.path.join(r"f:\Medjeex\Medjeex-OMR-Engine\data", save_name), visual)
    
    total = 0
    for subj, qs in results.items():
        filled = [a for q, a in qs.items() if a not in ("SKIPPED", "INVALID")]
        print(f"{subj:10}: {len(filled):2} attempted")
        total += len(filled)
    print(f"TOTAL: {total}/180")
    
    # Save results
    res_name = filename.replace(".jpeg", "_results.json")
    with open(os.path.join(r"f:\Medjeex\Medjeex-OMR-Engine\data", res_name), "w") as f:
        json.dump(results, f, indent=2)

print("\n[SUCCESS] Both scans complete. Results saved in 'data' directory.")
