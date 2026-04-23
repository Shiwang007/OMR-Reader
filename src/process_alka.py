from processor import OMREngine
import json, os, cv2

image_path = r"f:\Medjeex\Medjeex-OMR-Engine\WhatsApp Image 2026-04-23 at 5.20.49 PM.jpeg"
engine = OMREngine()

print("Processing Alka Maurya scan...")
results = engine.process_full_sheet(image_path)

# Visualize
visual = engine.visualize_results(image_path, results)
cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\data\alka_verified.jpg", visual)

# Summary
total = 0
for subj, qs in results.items():
    filled = [a for q, a in qs.items() if a not in ("SKIPPED", "INVALID")]
    skipped = [a for q, a in qs.items() if a == "SKIPPED"]
    invalid = [a for q, a in qs.items() if a == "INVALID"]
    print(f"{subj}: {len(filled)} attempted, {len(skipped)} skipped, {len(invalid)} invalid")
    total += len(filled)
print(f"Total attempted: {total}/180")

with open(r"f:\Medjeex\Medjeex-OMR-Engine\data\alka_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("Results saved.")
