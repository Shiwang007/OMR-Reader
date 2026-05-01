import json
import os
import subprocess
from datetime import datetime

# Paths
DATA_DIR = r"f:\Medjeex\Medjeex-OMR-Engine\data\neet"
ANSWER_KEY_PATH = r"f:\Medjeex\Medjeex-OMR-Engine\answer\neet_answer_key.json"
TEMPLATE_PATH = r"f:\Medjeex\Medjeex-OMR-Engine\templates\omr_report_template.html"
OUTPUT_DIR = r"f:\Medjeex\Medjeex-OMR-Engine\reports\neet"
PDF_DIR = r"f:\Medjeex\Medjeex-OMR-Engine\reports\neet_pdfs"
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
if not os.path.exists(PDF_DIR): os.makedirs(PDF_DIR)

def convert_to_pdf(html_path, pdf_path):
    cmd = [
        EDGE_PATH, "--headless", "--disable-gpu",
        f"--print-to-pdf={pdf_path}", "--no-margins",
        html_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except Exception as e:
        print(f"Error converting to PDF: {e}")
        return False

def generate_neet_html(student_name, student_data, answer_key, template):
    # Overall Stats
    overall = {
        "total_score": 0,
        "attempted": 0,
        "right": 0,
        "wrong": 0,
        "skipped": 0
    }
    
    subj_data = {}
    subjects = ["Physics", "Chemistry", "Biology I", "Biology II"]
    
    for subj in subjects:
        subj_data[subj] = {
            "rows_html": "",
            "right": 0,
            "wrong": 0,
            "score": 0
        }
        
        q_data = student_data.get(subj, {})
        key_data = answer_key.get(subj, {})
        
        # Sort questions numerically
        q_nums = sorted([int(k) for k in q_data.keys()])
        
        for q_num in q_nums:
            q_key = str(q_num)
            student_ans = q_data.get(q_key)
            correct_val = key_data.get(q_key)
            
            # Multi-correct logic
            if isinstance(correct_val, list):
                correct_options = [str(x) for x in correct_val]
            elif isinstance(correct_val, str) and "," in correct_val:
                correct_options = [x.strip() for x in correct_val.split(",")]
            else:
                correct_options = [str(correct_val)]
            
            status_class = ""
            display_ans = student_ans
            
            if student_ans == "SKIPPED":
                status_class = "skipped"
                display_ans = "-"
                overall["skipped"] += 1
            elif student_ans == "INVALID":
                status_class = "wrong" # Invalid counts as wrong
                display_ans = "!!"
                subj_data[subj]["wrong"] += 1
                subj_data[subj]["score"] -= 1
                overall["wrong"] += 1
                overall["total_score"] -= 1
                overall["attempted"] += 1
            elif student_ans in correct_options:
                status_class = "correct"
                subj_data[subj]["right"] += 1
                subj_data[subj]["score"] += 4
                overall["right"] += 1
                overall["total_score"] += 4
                overall["attempted"] += 1
            else:
                status_class = "wrong"
                subj_data[subj]["wrong"] += 1
                subj_data[subj]["score"] -= 1
                overall["wrong"] += 1
                overall["total_score"] -= 1
                overall["attempted"] += 1

            # Build row
            # If multi-correct, just show the first correct one in the 'Correct' column to save space
            disp_correct = correct_options[0] if correct_options else "?"
            
            row_html = f"""
            <tr>
                <td class="q-num">{q_num}</td>
                <td class="ans-cell"><span class="status-dot {status_class}">{display_ans}</span></td>
                <td class="ans-cell">{disp_correct}</td>
            </tr>"""
            subj_data[subj]["rows_html"] += row_html

    # Replace placeholders
    html = template
    html = html.replace("{{STUDENT_NAME}}", student_name.replace("_", " "))
    html = html.replace("{{DATE}}", datetime.now().strftime("%d %b %Y"))
    html = html.replace("{{TOTAL_SCORE}}", str(overall["total_score"]))
    html = html.replace("{{ATTEMPTED}}", str(overall["attempted"]))
    html = html.replace("{{RIGHT}}", str(overall["right"]))
    html = html.replace("{{WRONG}}", str(overall["wrong"]))
    html = html.replace("{{UNATTEMPTED}}", str(overall["skipped"]))
    
    # Subject Specifics
    html = html.replace("{{PHYSICS_ROWS}}", subj_data["Physics"]["rows_html"])
    html = html.replace("{{PHYSICS_RIGHT}}", str(subj_data["Physics"]["right"]))
    html = html.replace("{{PHYSICS_WRONG}}", str(subj_data["Physics"]["wrong"]))
    html = html.replace("{{PHYSICS_SCORE}}", str(subj_data["Physics"]["score"]))
    
    html = html.replace("{{CHEMISTRY_ROWS}}", subj_data["Chemistry"]["rows_html"])
    html = html.replace("{{CHEMISTRY_RIGHT}}", str(subj_data["Chemistry"]["right"]))
    html = html.replace("{{CHEMISTRY_WRONG}}", str(subj_data["Chemistry"]["wrong"]))
    html = html.replace("{{CHEMISTRY_SCORE}}", str(subj_data["Chemistry"]["score"]))
    
    html = html.replace("{{BIOLOGY_I_ROWS}}", subj_data["Biology I"]["rows_html"])
    html = html.replace("{{BIOLOGY_I_RIGHT}}", str(subj_data["Biology I"]["right"]))
    html = html.replace("{{BIOLOGY_I_WRONG}}", str(subj_data["Biology I"]["wrong"]))
    html = html.replace("{{BIOLOGY_I_SCORE}}", str(subj_data["Biology I"]["score"]))
    
    html = html.replace("{{BIOLOGY_II_ROWS}}", subj_data["Biology II"]["rows_html"])
    html = html.replace("{{BIOLOGY_II_RIGHT}}", str(subj_data["Biology II"]["right"]))
    html = html.replace("{{BIOLOGY_II_WRONG}}", str(subj_data["Biology II"]["wrong"]))
    html = html.replace("{{BIOLOGY_II_SCORE}}", str(subj_data["Biology II"]["score"]))

    return html

# Execution
with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
    template_content = f.read()

with open(ANSWER_KEY_PATH, 'r') as f:
    answer_key = json.load(f)

for filename in os.listdir(DATA_DIR):
    if filename.endswith(".json"):
        student_id = filename.replace(".json", "")
        with open(os.path.join(DATA_DIR, filename), 'r') as f:
            student_data = json.load(f)
            
        print(f"Generating Detailed NEET Report: {student_id}...")
        report_html = generate_neet_html(student_id, student_data, answer_key, template_content)
        
        # Save temp HTML
        html_path = os.path.join(OUTPUT_DIR, f"{student_id}_detailed.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(report_html)
            
        # Convert to PDF
        pdf_path = os.path.join(PDF_DIR, f"{student_id}_NEET_Detailed_Report.pdf")
        if convert_to_pdf(os.path.abspath(html_path), os.path.abspath(pdf_path)):
            print(f"  [SUCCESS] Created: {student_id}_NEET_Detailed_Report.pdf")
        else:
            print(f"  [FAILED] {student_id}")

print(f"\n--- ALL DETAILED NEET REPORTS GENERATED IN {PDF_DIR} ---")
