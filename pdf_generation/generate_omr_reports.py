import json
import os
from datetime import datetime

# Paths
DATA_DIR = r"f:\Medjeex\Medjeex-OMR-Engine\data"
ANSWER_KEY_PATH = r"f:\Medjeex\Medjeex-OMR-Engine\answer\answer_key.json"
TEMPLATE_PATH = r"f:\Medjeex\Medjeex-OMR-Engine\templates\omr_report_template.html"
OUTPUT_DIR = r"f:\Medjeex\Medjeex-OMR-Engine\omr_reports"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def generate_omr_report(student_name, student_data, answer_key, template):
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
        
        # Sort keys numerically
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

    # Final replacement
    html = template
    html = html.replace("{{STUDENT_NAME}}", student_name)
    html = html.replace("{{TOTAL_SCORE}}", str(stats["total_score"]))
    html = html.replace("{{ATTEMPTED}}", str(stats["total_attempted"]))
    html = html.replace("{{RIGHT}}", str(stats["total_correct"]))
    html = html.replace("{{WRONG}}", str(stats["total_wrong"]))
    html = html.replace("{{UNATTEMPTED}}", str(stats["total_skipped"]))
    
    for key, val in subject_placeholders.items():
        html = html.replace(f"{{{{{key}}}}}", str(val))
        
    return html

# Main execution
with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
    template_content = f.read()

with open(ANSWER_KEY_PATH, 'r') as f:
    answer_key = json.load(f)

for filename in os.listdir(DATA_DIR):
    if filename.endswith(".json") and filename != "answer_key.json":
        student_name = filename.replace(".json", "")
        with open(os.path.join(DATA_DIR, filename), 'r') as f:
            student_data = json.load(f)
        
        print(f"Generating 4-Column OMR report for {student_name}...")
        report_html = generate_omr_report(student_name, student_data, answer_key, template_content)
        
        output_path = os.path.join(OUTPUT_DIR, f"{student_name}_omr_report.html")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_html)

print(f"DONE! 4-Column OMR Reports generated in {OUTPUT_DIR}")
