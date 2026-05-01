import json
import os
import subprocess
from datetime import datetime

# Paths
DATA_DIR = r"f:\Medjeex\Medjeex-OMR-Engine\data\jee"
ANSWER_KEY_PATH = r"f:\Medjeex\Medjeex-OMR-Engine\answer\jee_answer_key.json"
TEMPLATE_PATH = r"f:\Medjeex\Medjeex-OMR-Engine\templates\jee_report_template.html"
HTML_DIR = r"f:\Medjeex\Medjeex-OMR-Engine\reports\jee_detailed_html"
PDF_DIR = r"f:\Medjeex\Medjeex-OMR-Engine\reports\jee_detailed_pdfs"
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

if not os.path.exists(HTML_DIR): os.makedirs(HTML_DIR)
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

def generate_jee_detailed_html(student_name, student_data, answer_key, template):
    stats = {
        "total_score": 0, "total_correct": 0, "total_wrong": 0, "total_skipped": 0, "total_attempted": 0
    }
    
    subjects = ["Physics", "Chemistry", "Mathematics"]
    subject_placeholders = {}

    for subj in subjects:
        subj_q_data = student_data.get(subj, {})
        subj_key_data = answer_key.get(subj, {})
        
        subj_right = 0
        subj_wrong = 0
        subj_score = 0
        rows_html = ""
        
        sorted_qs = sorted(subj_q_data.keys(), key=lambda x: int(x))
        
        for q_num in sorted_qs:
            marked = subj_q_data[q_num]
            correct_val = subj_key_data.get(q_num, "-")
            
            # Handle multiple correct options
            if isinstance(correct_val, list):
                correct_options = [str(x) for x in correct_val]
            elif isinstance(correct_val, str) and "," in correct_val:
                correct_options = [x.strip() for x in correct_val.split(",")]
            else:
                correct_options = [str(correct_val)]

            marked_disp = marked
            status_class = ""
            
            if marked == "SKIPPED":
                marked_disp = "-"
                status_class = "skipped"
                stats["total_skipped"] += 1
            elif marked == "INVALID":
                marked_disp = "INV"
                status_class = "invalid"
                subj_wrong += 1
                subj_score -= 1
                stats["total_wrong"] += 1
                stats["total_attempted"] += 1
            elif str(marked) in correct_options:
                status_class = "correct"
                subj_right += 1
                subj_score += 4
                stats["total_correct"] += 1
                stats["total_attempted"] += 1
            else:
                status_class = "wrong"
                subj_wrong += 1
                subj_score -= 1
                stats["total_wrong"] += 1
                stats["total_attempted"] += 1
                
            marked_html = f'<span class="status-dot {status_class}">{marked_disp}</span>'
            # For correct key display
            disp_correct = ",".join(correct_options) if isinstance(correct_val, list) else correct_val
            rows_html += f'<tr><td class="q-num">{q_num}</td><td class="ans-cell">{marked_html}</td><td class="ans-cell">{disp_correct}</td></tr>\n'

        subject_placeholders[f"{subj.upper()}_ROWS"] = rows_html
        subject_placeholders[f"{subj.upper()}_RIGHT"] = subj_right
        subject_placeholders[f"{subj.upper()}_WRONG"] = subj_wrong
        subject_placeholders[f"{subj.upper()}_SCORE"] = subj_score
        stats["total_score"] += subj_score

    html = template
    html = html.replace("{{STUDENT_NAME}}", student_name)
    html = html.replace("{{TOTAL_SCORE}}", str(stats["total_score"]))
    html = html.replace("{{ATTEMPTED}}", str(stats["total_attempted"]))
    html = html.replace("{{RIGHT}}", str(stats["total_correct"]))
    html = html.replace("{{WRONG}}", str(stats["total_wrong"]))
    html = html.replace("{{UNATTEMPTED}}", str(stats["total_skipped"]))
    html = html.replace("{{DATE}}", datetime.now().strftime("%d-%m-%Y"))
    
    for key, val in subject_placeholders.items():
        html = html.replace(f"{{{{{key}}}}}", str(val))
        
    return html

# Main
with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
    template_content = f.read()
with open(ANSWER_KEY_PATH, 'r') as f:
    answer_key = json.load(f)

for filename in os.listdir(DATA_DIR):
    if filename.endswith(".json"):
        student_id = filename.replace(".json", "")
        with open(os.path.join(DATA_DIR, filename), 'r') as f:
            student_data = json.load(f)
        
        print(f"Generating Detailed JEE PDF: {student_id}...")
        html_content = generate_jee_detailed_html(student_id, student_data, answer_key, template_content)
        
        temp_html_path = os.path.join(HTML_DIR, f"{student_id}_detailed.html")
        with open(temp_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        pdf_path = os.path.join(PDF_DIR, f"{student_id}_JEE_Report.pdf")
        if convert_to_pdf(os.path.abspath(temp_html_path), os.path.abspath(pdf_path)):
            print(f"  [SUCCESS] PDF Created: {student_id}")
        else:
            print(f"  [FAILED] PDF Creation: {student_id}")

print(f"\n--- ALL JEE DETAILED REPORTS GENERATED IN {PDF_DIR} ---")
