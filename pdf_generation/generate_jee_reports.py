import json
import os
import subprocess
from datetime import datetime

# Paths
DATA_DIR = r"f:\Medjeex\Medjeex-OMR-Engine\data\jee"
ANSWER_KEY_PATH = r"f:\Medjeex\Medjeex-OMR-Engine\answer\jee_answer_key.json"
TEMPLATE_PATH = r"f:\Medjeex\Medjeex-OMR-Engine\templates\jee_report_template.html"
OUTPUT_DIR = r"f:\Medjeex\Medjeex-OMR-Engine\reports\jee"
PDF_DIR = r"f:\Medjeex\Medjeex-OMR-Engine\reports\jee_pdfs"
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

def generate_jee_html(student_name, student_data, answer_key, template):
    overall = {"total_score": 0, "attempted": 0, "right": 0, "wrong": 0, "skipped": 0}
    subj_data = {}
    subjects = ["Physics", "Chemistry", "Mathematics"]
    
    for subj in subjects:
        subj_data[subj] = {"rows_html": "", "right": 0, "wrong": 0, "score": 0}
        q_data = student_data.get(subj, {})
        key_data = answer_key.get(subj, {})
        
        q_nums = sorted([int(k) for k in q_data.keys()])
        for q_num in q_nums:
            q_key = str(q_num)
            student_ans = q_data.get(q_key)
            correct_val = key_data.get(q_key)
            
            if not correct_val:
                correct_options = []
            else:
                correct_options = [str(correct_val)] if not isinstance(correct_val, list) else [str(x) for x in correct_val]

            status_class, display_ans = "", student_ans
            if student_ans == "SKIPPED":
                status_class, display_ans = "skipped", "-"
                overall["skipped"] += 1
            elif student_ans == "INVALID":
                status_class, display_ans = "wrong", "!!"
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

            disp_correct = correct_options[0] if correct_options else "?"
            row_html = f"<tr><td class='q-num'>{q_num}</td><td class='ans-cell'><span class='status-dot {status_class}'>{display_ans}</span></td><td class='ans-cell'>{disp_correct}</td></tr>"
            subj_data[subj]["rows_html"] += row_html

    # Injection using the new JEE template placeholders
    html = template
    html = html.replace("{{STUDENT_NAME}}", student_name.replace("_", " ").title())
    html = html.replace("{{DATE}}", datetime.now().strftime("%d %b %Y"))
    html = html.replace("{{TOTAL_SCORE}}", str(overall["total_score"]))
    html = html.replace("{{ATTEMPTED}}", str(overall["attempted"]))
    html = html.replace("{{RIGHT}}", str(overall["right"]))
    html = html.replace("{{WRONG}}", str(overall["wrong"]))
    html = html.replace("{{UNATTEMPTED}}", str(overall["skipped"]))
    
    for subj in subjects:
        prefix = subj.upper()
        html = html.replace("{{" + prefix + "_ROWS}}", subj_data[subj]["rows_html"])
        html = html.replace("{{" + prefix + "_RIGHT}}", str(subj_data[subj]["right"]))
        html = html.replace("{{" + prefix + "_WRONG}}", str(subj_data[subj]["wrong"]))
        html = html.replace("{{" + prefix + "_SCORE}}", str(subj_data[subj]["score"]))
    
    return html

# Main Execution
with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
    template_content = f.read()

with open(ANSWER_KEY_PATH, 'r') as f:
    answer_key = json.load(f)

for filename in os.listdir(DATA_DIR):
    if filename.endswith(".json"):
        student_id = filename.replace(".json", "")
        with open(os.path.join(DATA_DIR, filename), 'r') as f:
            student_data = json.load(f)
            
        print(f"Generating JEE Report: {student_id}...")
        report_html = generate_jee_html(student_id, student_data, answer_key, template_content)
        
        html_path = os.path.join(OUTPUT_DIR, f"{student_id}_detailed.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(report_html)
            
        pdf_path = os.path.join(PDF_DIR, f"{student_id}_JEE_Report.pdf")
        if convert_to_pdf(os.path.abspath(html_path), os.path.abspath(pdf_path)):
            print(f"  [SUCCESS] {student_id}_JEE_Report.pdf")

print(f"\n--- ALL JEE REPORTS GENERATED IN {PDF_DIR} ---")
