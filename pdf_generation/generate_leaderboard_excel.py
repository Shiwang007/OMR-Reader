import json
import os
import pandas as pd
from datetime import datetime

# Paths
DATA_DIR = r"f:\Medjeex\Medjeex-OMR-Engine\data\neet"
ANSWER_KEY_PATH = r"f:\Medjeex\Medjeex-OMR-Engine\answer\neet_answer_key.json"
OUTPUT_EXCEL = r"f:\Medjeex\Medjeex-OMR-Engine\reports\NEET_Leaderboard_Final.xlsx"

def calculate_neet_leaderboard():
    with open(ANSWER_KEY_PATH, 'r') as f:
        answer_key = json.load(f)
        
    students_data = []
    
    # 1. Process all student JSONs
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".json"):
            student_id = filename.replace(".json", "")
            with open(os.path.join(DATA_DIR, filename), 'r') as f:
                scan = json.load(f)
                
            stats = {
                "name": student_id.replace("_", " "),
                "Physics": 0,
                "Chemistry": 0,
                "Biology": 0, # Combined Bio I and Bio II
                "total_marks": 0,
                "attempted": 0,
                "correct": 0,
                "incorrect": 0
            }
            
            for subj in ["Physics", "Chemistry", "Biology I", "Biology II"]:
                q_data = scan.get(subj, {})
                key_data = answer_key.get(subj, {})
                
                target_col = "Biology" if "Biology" in subj else subj
                
                for q_num, ans in q_data.items():
                    correct_val = key_data.get(q_num)
                    
                    # Handle multi-correct
                    if isinstance(correct_val, list):
                        correct_options = [str(x) for x in correct_val]
                    elif isinstance(correct_val, str) and "," in correct_val:
                        correct_options = [x.strip() for x in correct_val.split(",")]
                    else:
                        correct_options = [str(correct_val)]
                        
                    if ans == "SKIPPED":
                        continue
                    
                    stats["attempted"] += 1
                    if ans in correct_options:
                        stats[target_col] += 4
                        stats["total_marks"] += 4
                        stats["correct"] += 1
                    else:
                        stats[target_col] -= 1
                        stats["total_marks"] -= 1
                        stats["incorrect"] += 1
            
            # Calculate Exam Percentage (out of 720 for NEET)
            stats["percentage"] = (stats["total_marks"] / 720 * 100)
            # Store Accuracy separately for tie-breaking
            stats["accuracy"] = (stats["correct"] / stats["attempted"] * 100) if stats["attempted"] > 0 else 0
            students_data.append(stats)

    # 2. Rank Students
    # Rank by Total Marks (Primary) then Accuracy (Secondary tie-breaker)
    students_data.sort(key=lambda x: (x["total_marks"], x["accuracy"]), reverse=True)
    
    # 3. Create DataFrame in Template Format
    rows = []
    for i, s in enumerate(students_data):
        rows.append([
            i + 1,              # S.NO.
            s["name"],          # NAME OF STUDENT
            s["Physics"],       # PHYSICS
            s["Chemistry"],     # CHEMISTRY
            s["Biology"],       # BIOLOGY
            s["total_marks"],   # TOTAL MARKS
            f"{s['percentage']:.1f}%", # PERCENTAGE
            i + 1,              # RANK
            s["attempted"],     # ATTEMPT
            s["correct"],       # CORRECT
            s["incorrect"]      # INCORRECT
        ])

    df = pd.DataFrame(rows, columns=[
        "S.NO.", "NAME OF STUDENT", "PHYSICS", "CHEMISTRY", "BIOLOGY", 
        "TOTAL MARKS", "PERCENTAGE", "RANK", "ATTEMPT", "CORRECT", "INCORRECT"
    ])

    # 4. Save with Header Banner
    title = f"MEDJEEX NEET RESULT SHEET - {datetime.now().strftime('%d %b %Y')}"
    
    # Use ExcelWriter to add the title row
    with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, startrow=1)
        
        # Add the title at the top
        workbook = writer.book
        sheet = writer.sheets['Sheet1']
        sheet.cell(row=1, column=1, value=title)
        
        # Adjust column widths for better look
        for col in sheet.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except: pass
            sheet.column_dimensions[column].width = max_length + 5

    print(f"\n--- SUCCESS! NEET Excel Leaderboard created at: {OUTPUT_EXCEL} ---")

if __name__ == "__main__":
    calculate_neet_leaderboard()
