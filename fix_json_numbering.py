import json
import os

files_to_fix = [
    r"f:\Medjeex\Medjeex-OMR-Engine\data\Taj.json",
    r"f:\Medjeex\Medjeex-OMR-Engine\data\Karan.json"
]

def fix_numbering(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    with open(filepath, 'r') as f:
        data = json.load(f)

    new_data = {}
    subjects = ["Physics", "Chemistry", "Biology I", "Biology II"]
    current_num = 1

    for subj in subjects:
        if subj in data:
            new_subj_data = {}
            # The current keys in data[subj] might be 1-45 or strings like "1", "2"
            # We want to re-map them to continuous numbering
            # Assuming they are in order in the JSON
            for q_idx in range(1, 46):
                key = str(q_idx)
                if key in data[subj]:
                    new_subj_data[str(current_num)] = data[subj][key]
                current_num += 1
            new_data[subj] = new_subj_data

    with open(filepath, 'w') as f:
        json.dump(new_data, f, indent=2)
    print(f"Fixed {filepath}")

for f in files_to_fix:
    fix_numbering(f)
