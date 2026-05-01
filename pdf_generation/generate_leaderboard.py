import json
import os
import subprocess
from datetime import datetime

# Paths
NEET_DATA = r"f:\Medjeex\Medjeex-OMR-Engine\data\neet"
JEE_DATA = r"f:\Medjeex\Medjeex-OMR-Engine\data\jee"
NEET_KEY = r"f:\Medjeex\Medjeex-OMR-Engine\answer\neet_answer_key.json"
JEE_KEY = r"f:\Medjeex\Medjeex-OMR-Engine\answer\jee_answer_key.json"
OUTPUT_DIR = r"f:\Medjeex\Medjeex-OMR-Engine\reports\leaderboards"
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)

def get_accuracy(correct, attempted):
    if attempted == 0: return 0.0
    return (correct / attempted) * 100

def convert_to_pdf(html_path, pdf_path):
    cmd = [EDGE_PATH, "--headless", "--disable-gpu", f"--print-to-pdf={pdf_path}", "--no-margins", html_path]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except: return False

def generate_leaderboard_data(data_dir, answer_key_path, is_neet=True):
    with open(answer_key_path, 'r') as f:
        master_key = json.load(f)
    
    leaderboard = []
    
    for filename in os.listdir(data_dir):
        if not filename.endswith(".json"): continue
        student_id = filename.replace(".json", "")
        with open(os.path.join(data_dir, filename), 'r') as f:
            student_data = json.load(f)
            
        stats = {"name": student_id, "total": 0, "correct": 0, "attempted": 0, "subjects": {}}
        
        # Calculate Scores
        for subj, q_data in student_data.items():
            subj_score = 0
            key_data = master_key.get(subj, {})
            
            for q_num, ans in q_data.items():
                correct_val = key_data.get(str(q_num))
                
                # Handle Multi-Choice
                if isinstance(correct_val, list):
                    correct_options = [str(x) for x in correct_val]
                elif isinstance(correct_val, str) and "," in correct_val:
                    correct_options = [x.strip() for x in correct_val.split(",")]
                else:
                    correct_options = [str(correct_val)]

                if ans != "SKIPPED":
                    stats["attempted"] += 1
                    if str(ans) in correct_options:
                        subj_score += 4
                        stats["correct"] += 1
                    else:
                        subj_score -= 1
            
            stats["subjects"][subj] = subj_score
            stats["total"] += subj_score
            
        stats["accuracy"] = get_accuracy(stats["correct"], stats["attempted"])
        leaderboard.append(stats)
        
    # Sort: Marks (Desc), then Accuracy (Desc)
    leaderboard.sort(key=lambda x: (x["total"], x["accuracy"]), reverse=True)
    return leaderboard

def generate_leaderboard_html(data, title):
    subject_names = list(data[0]["subjects"].keys())
    LOGO_PATH = r"f:\Medjeex\Medjeex-OMR-Engine\assets\Medjeex_Logo.png"
    
    table_headers = "".join([f"<th>{s}</th>" for s in subject_names])
    
    rows = ""
    for rank, s in enumerate(data, 1):
        subj_cells = "".join([f"<td>{s['subjects'][name]}</td>" for name in subject_names])
        acc_class = "acc-high" if s['accuracy'] > 80 else "acc-med" if s['accuracy'] > 50 else "acc-low"
        
        rows += f"""
        <tr class="rank-row">
            <td class="rank-cell">#{rank}</td>
            <td class="name-cell">{s['name']}</td>
            <td class="total-cell">{s['total']}</td>
            {subj_cells}
            <td><span class="accuracy-tag {acc_class}">{s['accuracy']:.1f}%</span></td>
        </tr>
        """
        
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --primary: #4F46E5;
                --success: #10B981;
                --danger: #EF4444;
                --slate-50: #f8fafc;
                --slate-200: #e2e8f0;
                --slate-700: #334155;
                --slate-900: #0f172a;
            }}
            body {{ 
                font-family: 'Outfit', sans-serif; 
                background: #f1f5f9; 
                margin: 0; 
                padding: 30px; 
                color: var(--slate-900);
            }}
            .container {{ 
                max-width: 850px; 
                margin: 0 auto; 
                background: white; 
                padding: 30px 45px; 
                border-radius: 20px; 
                box-shadow: 0 15px 40px rgba(0,0,0,0.05); 
                position: relative; 
                min-height: 250mm;
            }}
            .watermark {{
                position: absolute; 
                top: 50%; 
                left: 50%; 
                transform: translate(-50%, -50%);
                opacity: 0.035; 
                z-index: 0; 
                width: 500px; 
                pointer-events: none;
            }}
            .header-section {{
                text-align: center;
                margin-bottom: 25px;
                position: relative;
                z-index: 2;
            }}
            .header-logo {{ width: 100px; margin-bottom: 8px; }}
            h1 {{ font-size: 1.8rem; font-weight: 700; margin: 0; color: var(--primary); letter-spacing: -0.5px; }}
            p.subtitle {{ color: #64748b; margin-top: 2px; font-size: 0.9rem; }}

            table {{ 
                width: 100%; 
                border-collapse: separate; 
                border-spacing: 0 6px; 
                position: relative; 
                z-index: 1;
            }}
            th {{ 
                text-align: center; 
                padding: 8px 4px; 
                color: #64748b; 
                font-size: 0.7rem; 
                text-transform: uppercase; 
                letter-spacing: 1px;
                border-bottom: 1px solid var(--slate-200);
                white-space: nowrap;
            }}
            th:nth-child(2) {{ text-align: left; width: 30%; }}
            th:first-child {{ width: 45px; }}
            th:last-child {{ width: 85px; }}
            
            td {{ 
                padding: 12px 10px; 
                text-align: center;
                background: #fff;
                border-top: 1px solid #f1f5f9;
                border-bottom: 1px solid #f1f5f9;
                font-size: 0.95rem;
            }}
            
            tr.rank-row td {{ background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.01); }}
            tr.rank-row td:first-child {{ border-left: 1px solid #f1f5f9; border-radius: 10px 0 0 10px; }}
            tr.rank-row td:last-child {{ border-right: 1px solid #f1f5f9; border-radius: 0 10px 10px 0; }}

            .rank-cell {{ font-weight: 700; color: var(--primary); font-size: 1rem; }}
            .name-cell {{ text-align: left; font-weight: 600; color: var(--slate-900); font-size: 1rem; }}
            .total-cell {{ font-weight: 800; color: var(--slate-900); font-size: 1.1rem; }}
            
            .accuracy-tag {{ 
                display: inline-block;
                padding: 4px 10px; 
                border-radius: 15px; 
                font-size: 0.8rem; 
                font-weight: 700; 
                min-width: 55px;
            }}
            .acc-high {{ background: #dcfce7; color: #15803d; }}
            .acc-med {{ background: #fef9c3; color: #854d0e; }}
            .acc-low {{ background: #fee2e2; color: #b91c1c; }}

            /* Highlight Top 3 */
            tr:nth-child(1) td {{ background: #fffbeb; border-color: #fef3c7; }}
            tr:nth-child(1) .rank-cell {{ color: #d97706; font-size: 1.2rem; }}
            
            @media print {{
                body {{ background: white; padding: 0; }}
                .container {{ box-shadow: none; border: none; width: 100%; padding: 20px; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <img src="{LOGO_PATH}" class="watermark">
            <div class="header-section">
                <img src="{LOGO_PATH}" class="header-logo">
                <h1>{title}</h1>
                <p class="subtitle">Official Result Announcement &bull; {datetime.now().strftime('%d %b %Y')}</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Student Name</th>
                        <th>Total</th>
                        {table_headers}
                        <th>Accuracy</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return html

# Generate NEET
print("--- GENERATING NEET LEADERBOARD ---")
neet_data = generate_leaderboard_data(NEET_DATA, NEET_KEY, True)
neet_html = generate_leaderboard_html(neet_data, "NEET AITS Leaderboard")
neet_html_path = os.path.join(OUTPUT_DIR, "neet_leaderboard.html")
neet_pdf_path = os.path.join(OUTPUT_DIR, "NEET_Leaderboard.pdf")
with open(neet_html_path, 'w', encoding='utf-8') as f: f.write(neet_html)
convert_to_pdf(os.path.abspath(neet_html_path), os.path.abspath(neet_pdf_path))
print(f"  [SUCCESS] NEET Leaderboard: {neet_pdf_path}")

# Generate JEE
print("\n--- GENERATING JEE LEADERBOARD ---")
jee_data = generate_leaderboard_data(JEE_DATA, JEE_KEY, False)
jee_html = generate_leaderboard_html(jee_data, "JEE MAINS Leaderboard")
jee_html_path = os.path.join(OUTPUT_DIR, "jee_leaderboard.html")
jee_pdf_path = os.path.join(OUTPUT_DIR, "JEE_Leaderboard.pdf")
with open(jee_html_path, 'w', encoding='utf-8') as f: f.write(jee_html)
convert_to_pdf(os.path.abspath(jee_html_path), os.path.abspath(jee_pdf_path))
print(f"  [SUCCESS] JEE Leaderboard: {jee_pdf_path}")

print(f"\n--- ALL LEADERBOARDS GENERATED IN {OUTPUT_DIR} ---")
