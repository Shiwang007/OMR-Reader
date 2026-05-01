import json
import os
import subprocess
from datetime import datetime

# Paths
DATA_DIR = r"f:\Medjeex\Medjeex-OMR-Engine\data"
ANSWER_KEY_PATH = r"f:\Medjeex\Medjeex-OMR-Engine\answer\answer_key.json"
TEMPLATE_PATH = r"f:\Medjeex\Medjeex-OMR-Engine\templates\omr_report_template.html"
HTML_DIR = r"f:\Medjeex\Medjeex-OMR-Engine\omr_reports"
PDF_DIR = r"f:\Medjeex\Medjeex-OMR-Engine\omr_pdfs"
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

if not os.path.exists(PDF_DIR):
    os.makedirs(PDF_DIR)
if not os.path.exists(HTML_DIR):
    os.makedirs(HTML_DIR)

def generate_omr_html(student_name, student_data, answer_key, template):
    stats = {
        "total_score": 0, "total_correct": 0, "total_wrong": 0, "total_skipped": 0, "total_attempted": 0
    }
    
    subjects = ["Physics", "Chemistry", "Biology I", "Biology II"]
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
            correct = subj_key_data.get(q_num, "-")
            
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
            elif marked == correct:
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
            rows_html += f'<tr><td class="q-num">{q_num}</td><td class="ans-cell">{marked_html}</td><td class="ans-cell">{correct}</td></tr>\n'

        prefix = subj.upper().replace(" ", "_")
        subject_placeholders[f"{prefix}_ROWS"] = rows_html
        subject_placeholders[f"{prefix}_RIGHT"] = subj_right
        subject_placeholders[f"{prefix}_WRONG"] = subj_wrong
        subject_placeholders[f"{prefix}_SCORE"] = subj_score
        stats["total_score"] += subj_score

    # Hardcoded date as requested
    display_date = "25-04-2026"
    
    html = template
    html = html.replace("{{STUDENT_NAME}}", student_name)
    html = html.replace("{{TOTAL_SCORE}}", str(stats["total_score"]))
    html = html.replace("{{ATTEMPTED}}", str(stats["total_attempted"]))
    html = html.replace("{{RIGHT}}", str(stats["total_correct"]))
    html = html.replace("{{WRONG}}", str(stats["total_wrong"]))
    html = html.replace("{{UNATTEMPTED}}", str(stats["total_skipped"]))
    html = html.replace("{{DATE}}", display_date)
    
    for key, val in subject_placeholders.items():
        html = html.replace(f"{{{{{key}}}}}", str(val))
        
    return html

def convert_to_pdf(html_path, pdf_path):
    cmd = [
        EDGE_PATH,
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={pdf_path}",
        "--no-margins",
        html_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except Exception as e:
        print(f"Error converting to PDF: {e}")
        return False

# Main
with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
    template_content = f.read()

with open(ANSWER_KEY_PATH, 'r') as f:
    answer_key = json.load(f)

print(f"Starting PDF generation for date: 25-04-2026...")
for filename in os.listdir(DATA_DIR):
    if filename.endswith(".json") and not filename.startswith("Image") and filename != "answer_key.json":
        student_name = filename.replace(".json", "")
        with open(os.path.join(DATA_DIR, filename), 'r') as f:
            student_data = json.load(f)
        
        print(f"Processing {student_name}...")
        html_content = generate_omr_html(student_name, student_data, answer_key, template_content)
        
        temp_html_path = os.path.join(HTML_DIR, f"temp_{student_name}.html")
        with open(temp_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        pdf_filename = f"{student_name}_Scorecard.pdf"
        pdf_path = os.path.join(PDF_DIR, pdf_filename)
        
        abs_html_path = os.path.abspath(temp_html_path)
        abs_pdf_path = os.path.abspath(pdf_path)
        
        if convert_to_pdf(abs_html_path, abs_pdf_path):
            print(f"  - Generated: {pdf_filename}")
        else:
            print(f"  - FAILED: {student_name}")

print(f"DONE! PDF reports are in {PDF_DIR}")
