import os
import json
import subprocess
import tempfile
import base64
from datetime import datetime

# Paths
BASE_DIR = r"f:\Medjeex\Medjeex-OMR-Engine"
DATA_DIR = os.path.join(BASE_DIR, "data", "neet")
ANSWER_KEY_PATH = os.path.join(BASE_DIR, "answer", "11_neet.json")
REPORT_TEMPLATE_PATH = os.path.join(BASE_DIR, "templates", "omr_report_template.html")
LEADERBOARD_TEMPLATE_PATH = os.path.join(BASE_DIR, "templates", "leaderboard_template.html")
LOGO_PATH = os.path.join(BASE_DIR, "assets", "Medjeex_Logo.png")
OUTPUT_DIR = os.path.join(BASE_DIR, "output", "AKAAR_NEET")
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def get_base64_img(path):
    if not os.path.exists(path): return ""
    with open(path, "rb") as f:
        return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"

LOGO_B64 = get_base64_img(LOGO_PATH)

def check_answer(student_ans, correct_ans):
    if not correct_ans: return False
    
    # Handle wildcard/bonus (*)
    if correct_ans == "*" or (isinstance(correct_ans, list) and "*" in correct_ans):
        return True
        
    student_ans_clean = str(student_ans).strip().upper()
    if not student_ans_clean or student_ans_clean in ["SKIPPED", "INVALID"]:
        return False

    valid = []
    if isinstance(correct_ans, list):
        for item in correct_ans:
            parts = [p.strip().upper() for p in str(item).split(',')]
            valid.extend(parts)
    else:
        valid = [a.strip().upper() for a in str(correct_ans).split(',')]
        
    return student_ans_clean in valid

def html_to_pdf(html_content, output_path):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode='w', encoding='utf-8') as f:
        f.write(html_content)
        html_path = f.name
    
    cmd = [
        EDGE_PATH,
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={output_path}",
        "--no-margins",
        "--no-pdf-header-footer",
        html_path
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    finally:
        if os.path.exists(html_path):
            os.remove(html_path)

def generate_reports():
    # Load Answer Key
    with open(ANSWER_KEY_PATH, 'r') as f:
        answer_key = json.load(f)
    
    # Load Report Template
    with open(REPORT_TEMPLATE_PATH, 'r') as f:
        report_template = f.read()
    
    leaderboard_data = []
    today = datetime.now().strftime("%d %b %Y")
    
    # Process each student
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]
    print(f"Processing {len(files)} students...")
    
    for filename in files:
        student_name = filename.replace('.json', '').replace('_', ' ')
        with open(os.path.join(DATA_DIR, filename), 'r') as f:
            student_data = json.load(f)
        
        total_correct = 0
        total_wrong = 0
        total_skipped = 0
        total_score = 0
        
        subj_stats = {}
        
        for subj in ["Physics", "Chemistry", "Biology I", "Biology II"]:
            subj_correct = 0
            subj_wrong = 0
            subj_skipped = 0
            
            # Case insensitive subject match
            key_subj = next((k for k in answer_key.keys() if k.lower() == subj.lower()), None)
            subj_key = answer_key.get(key_subj, {}) if key_subj else {}
            
            rows_html = ""
            q_data = student_data.get(subj, {})
            sorted_qs = sorted(q_data.keys(), key=lambda x: int(x))
            
            for q_num in sorted_qs:
                ans = q_data[q_num]
                correct_ans = subj_key.get(q_num, "")
                
                status_class = "skipped"
                if ans in ["SKIPPED", "", "INVALID"]:
                    subj_skipped += 1
                elif check_answer(ans, correct_ans):
                    subj_correct += 1
                    status_class = "correct"
                else:
                    subj_wrong += 1
                    status_class = "wrong"
                
                display_ans = "—" if ans in ["SKIPPED", ""] else ("INV" if ans == "INVALID" else ans)
                rows_html += f"""<tr>
                    <td class="q-num">{q_num}</td>
                    <td class="ans-cell"><span class="status-dot {status_class}">{display_ans}</span></td>
                    <td class="ans-cell" style="font-weight: 600; color: #64748b;">{correct_ans or "—"}</td>
                </tr>"""
            
            subj_score = (subj_correct * 4) - (subj_wrong * 1)
            subj_stats[subj] = {
                "correct": subj_correct,
                "wrong": subj_wrong,
                "score": subj_score,
                "rows": rows_html
            }
            
            total_correct += subj_correct
            total_wrong += subj_wrong
            total_skipped += subj_skipped
            total_score += subj_score
            
        # Generate individual report
        html = report_template
        html = html.replace("{{LOGO_B64}}", LOGO_B64)
        html = html.replace("{{STUDENT_NAME}}", student_name.upper())
        html = html.replace("{{DATE}}", today)
        html = html.replace("{{TOTAL_SCORE}}", str(total_score))
        html = html.replace("{{ATTEMPTED}}", str(total_correct + total_wrong))
        html = html.replace("{{RIGHT}}", str(total_correct))
        html = html.replace("{{WRONG}}", str(total_wrong))
        html = html.replace("{{UNATTEMPTED}}", str(total_skipped))
        
        for subj in ["Physics", "Chemistry", "Biology I", "Biology II"]:
            key = subj.upper().replace(" ", "_")
            html = html.replace(f"{{{{{key}_ROWS}}}}", subj_stats[subj]["rows"])
            html = html.replace(f"{{{{{key}_RIGHT}}}}", str(subj_stats[subj]["correct"]))
            html = html.replace(f"{{{{{key}_WRONG}}}}", str(subj_stats[subj]["wrong"]))
            html = html.replace(f"{{{{{key}_SCORE}}}}", str(subj_stats[subj]["score"]))
            
        report_pdf_path = os.path.join(OUTPUT_DIR, f"{student_name.replace(' ', '_')}_Report.pdf")
        html_to_pdf(html, report_pdf_path)
        
        leaderboard_data.append({
            "name": student_name,
            "total_score": total_score,
            "physics": subj_stats["Physics"]["score"],
            "chemistry": subj_stats["Chemistry"]["score"],
            "biology": subj_stats["Biology I"]["score"] + subj_stats["Biology II"]["score"],
            "attempted": total_correct + total_wrong,
            "correct": total_correct,
            "wrong": total_wrong
        })
    
    # Generate Leaderboard
    leaderboard_data.sort(key=lambda x: x["total_score"], reverse=True)
    
    with open(LEADERBOARD_TEMPLATE_PATH, 'r') as f:
        lb_template = f.read()
    
    rows_html = ""
    for i, s in enumerate(leaderboard_data):
        pct = f"{(s['total_score']/720*100):.1f}%"
        rows_html += f"""<tr>
            <td class="rank-col">{i+1}</td>
            <td class="name-col">{s['name']}</td>
            <td class="score-col" style="font-weight: 700;">{s['total_score']}</td>
            <td class="pct-col">{pct}</td>
            <td class="subj-col">{s['physics']}</td>
            <td class="subj-col">{s['chemistry']}</td>
            <td class="subj-col">{s['biology']}</td>
            <td class="stat-col">{s['attempted']}</td>
            <td class="stat-col">{s['correct']}</td>
            <td class="stat-col">{s['wrong']}</td>
        </tr>"""
    
    lb_html = lb_template
    lb_html = lb_html.replace("{{LOGO_B64}}", LOGO_B64)
    lb_html = lb_html.replace("{{EXAM_NAME}}", "AKAAR NEET")
    lb_html = lb_html.replace("{{EXAM_TYPE}}", "NEET AITS")
    lb_html = lb_html.replace("{{DATE}}", today)
    lb_html = lb_html.replace("{{SUBJ1}}", "Physics")
    lb_html = lb_html.replace("{{SUBJ2}}", "Chemistry")
    lb_html = lb_html.replace("{{SUBJ3}}", "Biology")
    lb_html = lb_html.replace("{{ROWS}}", rows_html)
    
    leaderboard_pdf_path = os.path.join(OUTPUT_DIR, "AKAAR_NEET_Leaderboard.pdf")
    html_to_pdf(lb_html, leaderboard_pdf_path)
    print(f"Success! NEET Reports and leaderboard generated in {OUTPUT_DIR}")

if __name__ == "__main__":
    generate_reports()
