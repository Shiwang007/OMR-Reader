import json
import os
from datetime import datetime

# Paths
DATA_DIR = r"f:\Medjeex\Medjeex-OMR-Engine\data"
ANSWER_KEY_PATH = r"f:\Medjeex\Medjeex-OMR-Engine\answer\answer_key.json"
TEMPLATE_PATH = r"f:\Medjeex\Docx-Parser\final_scorecard.html"
OUTPUT_DIR = r"f:\Medjeex\Medjeex-OMR-Engine\reports"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def generate_report(student_name, student_data, answer_key, template):
    total_correct = 0
    total_wrong = 0
    total_skipped = 0
    total_score = 0
    
    # We will map the 4 subjects from OMR to the 3 subjects in the template
    # Physics (1-45), Chemistry (46-90), Biology (91-180)
    
    report_subjects = {
        "Physics": {"correct": [], "wrong": [], "skipped": [], "score": 0, "range": "Q1–45", "icon": "✅"},
        "Chemistry": {"correct": [], "wrong": [], "skipped": [], "score": 0, "range": "Q46–90", "icon": "🧪"},
        "Biology": {"correct": [], "wrong": [], "skipped": [], "score": 0, "range": "Q91–180", "icon": "🧬"}
    }
    
    # Process OMR Subjects
    for subj_name, q_data in student_data.items():
        # Determine which report subject this belongs to
        if subj_name == "Physics":
            target = "Physics"
        elif subj_name == "Chemistry":
            target = "Chemistry"
        else: # Biology I or Biology II
            target = "Biology"
            
        key_data = answer_key.get(subj_name, {})
        
        for q_num, student_ans in q_data.items():
            correct_ans = key_data.get(q_num)
            
            if student_ans == "SKIPPED":
                report_subjects[target]["skipped"].append(f"{q_num} ({correct_ans})")
                total_skipped += 1
            elif student_ans == correct_ans:
                report_subjects[target]["correct"].append(f"{q_num} ({correct_ans})")
                report_subjects[target]["score"] += 4
                total_correct += 1
                total_score += 4
            else: # WRONG or INVALID
                # Use "X" for INVALID in the display
                disp_ans = "INV" if student_ans == "INVALID" else student_ans
                report_subjects[target]["wrong"].append(f"{q_num} ({disp_ans}&rarr;{correct_ans})")
                report_subjects[target]["score"] -= 1
                total_wrong += 1
                total_score -= 1

    # Generate HTML content
    html = template
    
    # Replace global stats
    html = html.replace("NEET performance Scorecard", f"NEET Scorecard - {student_name}")
    html = html.replace("230 / 720", f"{total_score} / 720")
    html = html.replace(">64<", f">{total_correct}<")
    html = html.replace(">26<", f">{total_wrong}<")
    html = html.replace(">90<", f">{total_skipped}<")
    
    # Current date
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")
    html = html.replace("23 Apr 2026, 01:20 PM", now)

    # We need to inject subject sections. 
    # The template has 3 subject-section blocks. I'll identify them and replace.
    # A better way is to rebuild the subject-section list.
    
    subject_html_list = []
    chart_scripts = []
    
    for i, (name, data) in enumerate(report_subjects.items()):
        total_q = len(data["correct"]) + len(data["wrong"]) + len(data["skipped"])
        max_marks = total_q * 4
        
        correct_tags = "".join([f'<span class="tag tag-correct">{t}</span>' for t in data["correct"]])
        wrong_tags = "".join([f'<span class="tag tag-wrong">{t}</span>' for t in data["wrong"]])
        skip_tags = "".join([f'<span class="tag tag-skip">{t}</span>' for t in data["skipped"]])
        
        subj_block = f"""
    <div class="subject-section">
        <div class="subject-header">
            <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 1.8rem;">{data['icon']}</span>
                    <h2>{name} <span style="font-size: 0.9rem; font-weight: 400; color: var(--slate-700);">({data['range']})</span></h2>
                </div>
                <div style="font-size: 1.4rem; font-weight: 700; color: var(--primary);">
                    {data['score']} / {max_marks} <span style="font-size: 0.8rem; font-weight: 400; color: var(--slate-700);">Marks</span>
                </div>
            </div>
        </div>
        <div class="card subject-grid">
            <div class="chart-box">
                <canvas id="chart-sub_{i}" width="180" height="180"></canvas>
            </div>
            <div class="details-box">
                <div style="display: flex; gap: 20px; margin-bottom: 5px;">
                    <div><span style="color: var(--success); font-weight: 700;">{len(data['correct'])}</span> Correct</div>
                    <div><span style="color: var(--danger); font-weight: 700;">{len(data['wrong'])}</span> Wrong</div>
                    <div><span style="color: var(--warning); font-weight: 700;">{len(data['skipped'])}</span> Skipped</div>
                </div>

                <div>
                   <div class="q-group-label" style="color: var(--success)">Correct Questions</div>
                   <div class="tag-list">{correct_tags}</div>
                </div>
                
                <div>
                   <div class="q-group-label" style="color: var(--danger)">Wrong (Marked &rarr; Correct)</div>
                   <div class="tag-list">{wrong_tags}</div>
                </div>
                
                <div>
                   <div class="q-group-label" style="color: var(--slate-700)">Skipped (Correct Key)</div>
                   <div class="tag-list">{skip_tags}</div>
                </div>
            </div>
        </div>
    </div>
"""
        subject_html_list.append(subj_block)
        
        # Chart script
        script = f"""
        new Chart(document.getElementById('chart-sub_{i}'), {{
            type: 'doughnut',
            data: {{
                labels: ['Correct', 'Wrong', 'Skipped'],
                datasets: [{{
                    data: [{len(data['correct'])}, {len(data['wrong'])}, {len(data['skipped'])}],
                    backgroundColor: ['#10B981', '#EF4444', '#E2E8F0'],
                    borderWidth: 0,
                    hoverOffset: 4
                }}]
            }},
            options: {{
                plugins: {{ legend: {{ display: false }} }},
                cutout: '70%'
            }}
        }});
"""
        chart_scripts.append(script)

    # Remove existing subject sections and script
    # This is a bit hacky with string manipulation, but should work for this specific template
    
    start_marker = '<div class="subject-section">'
    end_marker = '<!-- Subject Sections End -->' # I'll add this to template if needed or just replace everything between blocks
    
    # I'll just find the first subject section and the footer
    parts = html.split('<div class="subject-section">')
    header_part = parts[0]
    footer_part = parts[-1].split('<div class="footer">')[-1]
    
    final_html = header_part + "\n".join(subject_html_list) + '\n<div class="footer">' + footer_part
    
    # Handle scripts
    script_parts = final_html.split('<script>')
    base_html = script_parts[0]
    final_html = base_html + "<script>\n" + "\n".join(chart_scripts) + "\n</script>\n</body>\n</html>"

    return final_html

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
        
        print(f"Generating report for {student_name}...")
        report_html = generate_report(student_name, student_data, answer_key, template_content)
        
        output_path = os.path.join(OUTPUT_DIR, f"{student_name}_report.html")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_html)

print(f"DONE! Reports generated in {OUTPUT_DIR}")
