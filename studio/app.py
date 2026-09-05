import os
import sys
import cv2
import numpy as np
import subprocess
import tempfile
import time
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.background import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uvicorn
import base64

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_DIR = os.path.dirname(BASE_DIR)
sys.path.append(ENGINE_DIR) 

try:
    from src.jee_processor import JEEOMREngine
    from src.neet_processor import NEETOMREngine
    from src.neet_dropper_processor import NEETDropperOMREngine
    from src.jee_advanced_processor import JEEAdvancedOMREngine
    from src.jee_advanced_processor_img4 import Img4Processor
except ImportError as e:
    print(f"Error: {e}")
    sys.exit(1)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Directories
JEE_DIR = os.path.join(ENGINE_DIR, "omr_jee")
NEET_DIR = os.path.join(ENGINE_DIR, "omr_neet")
NEW_NEET_DIR = os.path.join(ENGINE_DIR, "omr_new_neet")
JEE_ADV_1_DIR = os.path.join(ENGINE_DIR, "omr_jee_adv_1")
JEE_ADV_2_DIR = os.path.join(ENGINE_DIR, "omr_jee_adv_2")
for d in [JEE_DIR, NEET_DIR, NEW_NEET_DIR, JEE_ADV_1_DIR, JEE_ADV_2_DIR]:
    if not os.path.exists(d): os.makedirs(d)

jee_engine = JEEOMREngine()
neet_engine = NEETOMREngine()
new_neet_engine = NEETDropperOMREngine()
jee_adv_1_engine = JEEAdvancedOMREngine(os.path.join(ENGINE_DIR, "templates", "jee_advanced_template.json"))
adv2_template_path = os.path.join(ENGINE_DIR, "templates", "jee_advanced_template_img4.json")
if not os.path.exists(adv2_template_path):
    adv2_template_path = os.path.join(ENGINE_DIR, "output", "img4_template.json")
jee_adv_2_engine = Img4Processor(adv2_template_path)

# Store engine defaults — UI offsets are added on top
JEE_DEFAULTS = {"x": jee_engine.X_SHIFT, "y": jee_engine.Y_SHIFT}
NEET_DEFAULTS = {"x": neet_engine.X_SHIFT, "y": neet_engine.Y_SHIFT}
NEW_NEET_DEFAULTS = {"x": new_neet_engine.X_SHIFT, "y": new_neet_engine.Y_SHIFT}

@app.post("/clear-session")
async def clear_session():
    import shutil
    for d in [JEE_DIR, NEET_DIR, NEW_NEET_DIR, JEE_ADV_1_DIR, JEE_ADV_2_DIR]:
        if os.path.exists(d):
            for filename in os.listdir(d):
                file_path = os.path.join(d, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.is_dir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'Failed to delete {file_path}. Reason: {e}')
    return {"status": "success"}

@app.post("/upload")
async def upload_files(exam_type: str = Form(...), files: List[UploadFile] = File(...)):
    if exam_type == "JEE": target_dir = JEE_DIR
    elif exam_type == "NEET": target_dir = NEET_DIR
    elif exam_type == "NEW_NEET": target_dir = NEW_NEET_DIR
    elif exam_type == "JEE_ADV_1": target_dir = JEE_ADV_1_DIR
    elif exam_type == "JEE_ADV_2": target_dir = JEE_ADV_2_DIR
    else: target_dir = NEET_DIR
    results = []
    
    for file in files:
        file_path = os.path.join(target_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # Process immediately on upload
        if exam_type == "JEE":
            data, viz_img = jee_engine.process_page1(file_path)
        elif exam_type == "NEET":
            data, viz_img = neet_engine.process_sheet(file_path)
        elif exam_type == "NEW_NEET":
            data, viz_img = new_neet_engine.process_sheet(file_path)
        elif exam_type == "JEE_ADV_1":
            if hasattr(jee_adv_1_engine, 'read'):
                raw_data, viz_img = jee_adv_1_engine.read(file_path)
            else:
                raw_res, _, viz_img = jee_adv_1_engine.process_omr(file_path)
                raw_data = raw_res.get("questions", raw_res)
            
            data = {"Physics": {}, "Chemistry": {}, "Mathematics": {}}
            for q_num, ans in raw_data.items():
                try:
                    q_int = int(str(q_num).replace('Q', ''))
                except:
                    continue
                clean_q = str(q_int)
                if 1 <= q_int <= 16: data["Physics"][clean_q] = ans
                elif 17 <= q_int <= 32: data["Chemistry"][clean_q] = ans
                elif 33 <= q_int <= 48: data["Mathematics"][clean_q] = ans

        elif exam_type == "JEE_ADV_2":
            raw_data, viz_img = jee_adv_2_engine.read(file_path)
            data = {"Physics": {}, "Chemistry": {}, "Mathematics": {}}
            for q_num, ans in raw_data.items():
                try:
                    q_int = int(str(q_num).replace('Q', ''))
                except:
                    continue
                clean_q = str(q_int)
                if 1 <= q_int <= 18: data["Physics"][clean_q] = ans
                elif 19 <= q_int <= 36: data["Chemistry"][clean_q] = ans
                elif 37 <= q_int <= 54: data["Mathematics"][clean_q] = ans
            
        img_base64 = ""
        if viz_img is not None:
            _, buffer = cv2.imencode('.jpg', viz_img)
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            
        results.append({
            "filename": file.filename,
            "data": data,
            "image": f"data:image/jpeg;base64,{img_base64}"
        })
        
    return {"status": "success", "results": results}

@app.post("/process")
async def process_omr(
    filename: str = Form(...),
    exam_type: str = Form(...),
    x_shift: int = Form(0),
    y_shift: int = Form(0)
):
    if exam_type == "JEE": target_dir = JEE_DIR
    elif exam_type == "NEET": target_dir = NEET_DIR
    elif exam_type == "NEW_NEET": target_dir = NEW_NEET_DIR
    elif exam_type == "JEE_ADV_1": target_dir = JEE_ADV_1_DIR
    elif exam_type == "JEE_ADV_2": target_dir = JEE_ADV_2_DIR
    else: target_dir = NEET_DIR
    
    file_path = os.path.abspath(os.path.join(target_dir, filename))
    if exam_type == "JEE": defaults = JEE_DEFAULTS
    elif exam_type == "NEW_NEET": defaults = NEW_NEET_DEFAULTS
    else: defaults = NEET_DEFAULTS
    
    if exam_type == "JEE":
        jee_engine.X_SHIFT = defaults["x"] + x_shift
        jee_engine.Y_SHIFT = defaults["y"] + y_shift
        data, viz_img = jee_engine.process_page1(file_path)
    elif exam_type == "NEET":
        neet_engine.X_SHIFT = defaults["x"] + x_shift
        neet_engine.Y_SHIFT = defaults["y"] + y_shift
        data, viz_img = neet_engine.process_sheet(file_path)
    elif exam_type == "NEW_NEET":
        new_neet_engine.X_SHIFT = defaults["x"] + x_shift
        new_neet_engine.Y_SHIFT = defaults["y"] + y_shift
        data, viz_img = new_neet_engine.process_sheet(file_path)
    elif exam_type == "JEE_ADV_1":
        # Advanced engines don't use UI offsets yet, pass them in the future if added
        if hasattr(jee_adv_1_engine, 'read'):
            raw_data, viz_img = jee_adv_1_engine.read(file_path)
        else:
            raw_res, _, viz_img = jee_adv_1_engine.process_omr(file_path)
            raw_data = raw_res.get("questions", raw_res)
        data = {"Physics": {}, "Chemistry": {}, "Mathematics": {}}
        for q_num, ans in raw_data.items():
            try:
                q_int = int(str(q_num).replace('Q', ''))
            except:
                continue
            clean_q = str(q_int)
            if 1 <= q_int <= 16: data["Physics"][clean_q] = ans
            elif 17 <= q_int <= 32: data["Chemistry"][clean_q] = ans
            elif 33 <= q_int <= 48: data["Mathematics"][clean_q] = ans

    elif exam_type == "JEE_ADV_2":
        raw_data, viz_img = jee_adv_2_engine.read(file_path)
        data = {"Physics": {}, "Chemistry": {}, "Mathematics": {}}
        for q_num, ans in raw_data.items():
            try:
                q_int = int(str(q_num).replace('Q', ''))
            except:
                continue
            clean_q = str(q_int)
            if 1 <= q_int <= 18: data["Physics"][clean_q] = ans
            elif 19 <= q_int <= 36: data["Chemistry"][clean_q] = ans
            elif 37 <= q_int <= 54: data["Mathematics"][clean_q] = ans

    img_base64 = ""
    if viz_img is not None:
        _, buffer = cv2.imencode('.jpg', viz_img)
        img_base64 = base64.b64encode(buffer).decode('utf-8')

    return {
        "status": "success",
        "results": data,
        "processed_image": f"data:image/jpeg;base64,{img_base64}"
    }

@app.get("/template/leaderboard")
async def get_leaderboard_template():
    path = os.path.join(ENGINE_DIR, "templates", "leaderboard_template.html")
    with open(path, "r") as f:
        return {"template": f.read()}

@app.get("/template/comparison")
async def get_comparison_template():
    path = os.path.join(ENGINE_DIR, "templates", "comparison_report_template.html")
    with open(path, "r") as f:
        return {"template": f.read()}

@app.get("/template/topper")
async def get_topper_template():
    path = os.path.join(ENGINE_DIR, "templates", "topper_report_template.html")
    with open(path, "r") as f:
        return {"template": f.read()}

@app.get("/template/{exam_type}")
async def get_template(exam_type: str):
    if exam_type.upper().startswith("JEE_ADV"):
        path = os.path.join(ENGINE_DIR, "templates", "jee_advanced_report_template.html")
    elif exam_type.upper() == "JEE":
        path = os.path.join(ENGINE_DIR, "templates", "jee_report_template.html")
    else:
        path = os.path.join(ENGINE_DIR, "templates", "omr_report_template.html")
    with open(path, 'r', encoding='utf-8') as f:
        return {"template": f.read()}

@app.post("/generate-pdf")
async def generate_pdf(request: dict, background_tasks: BackgroundTasks):
    html_content = request.get("html", "")
    exam_name = request.get("exam_name", "Report")
    
    # Create temp files
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode='w', encoding='utf-8') as f:
        f.write(html_content)
        html_path = f.name
        
    pdf_path = html_path.replace(".html", ".pdf")
    
    # Run headless edge to convert
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    cmd = [
        edge_path,
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={pdf_path}",
        "--no-margins",
        "--no-pdf-header-footer",
        html_path
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except Exception as e:
        if os.path.exists(html_path): os.remove(html_path)
        return {"status": "error", "message": str(e)}

    # Cleanup temp files after response is sent
    def cleanup():
        if os.path.exists(html_path): os.remove(html_path)
        if os.path.exists(pdf_path): os.remove(pdf_path)
        
    background_tasks.add_task(cleanup)
    
    return FileResponse(
        pdf_path, 
        media_type='application/pdf', 
        filename=f"{exam_name}_Scorecards.pdf"
    )

@app.post("/generate")
def score_question(exam_type, q_num_raw, student_ans_raw, correct_ans_raw):
    """
    Scores a single question based on exam_type and question specifications.
    Returns (points_earned, status) where status is 'correct', 'partial', 'wrong', or 'skipped'.
    """
    if isinstance(correct_ans_raw, list):
        correct_parts = []
        for item in correct_ans_raw:
            correct_parts.extend([p.strip().upper() for p in str(item).split(",") if p.strip()])
    else:
        correct_parts = [p.strip().upper() for p in str(correct_ans_raw).split(",") if p.strip()]

    is_grace = "*" in correct_parts
    ans_str = str(student_ans_raw).strip().upper()
    is_skipped = ans_str in ("SKIPPED", "", "—", "-")
    is_invalid = ans_str == "INVALID"

    if exam_type == "JEE_ADV_1":
        try:
            q_int = int(q_num_raw)
        except:
            q_int = 1
        rel_q = ((q_int - 1) % 16) + 1

        # Section 1: Single Correct MCQ (Rel Q1-4) -> +3 / -1 / 0
        if 1 <= rel_q <= 4:
            if is_grace:
                return 3, "correct"
            if is_skipped:
                return 0, "skipped"
            if is_invalid or "," in ans_str:
                return -1, "wrong"
            if ans_str in correct_parts:
                return 3, "correct"
            return -1, "wrong"

        # Section 2: Multi-Correct MCQ (Rel Q5-8) -> +4 / (+3, +2, +1) / -1 / 0
        elif 5 <= rel_q <= 8:
            if is_grace:
                return 4, "correct"
            if is_skipped:
                return 0, "skipped"
            if is_invalid:
                return -1, "wrong"
            student_opts = set([p.strip().upper() for p in ans_str.split(",") if p.strip()])
            correct_opts = set([p for p in correct_parts if p != "*"])

            if not student_opts.issubset(correct_opts):
                return -1, "wrong"
            if student_opts == correct_opts:
                return 4, "correct"

            num_selected = len(student_opts)
            num_correct = len(correct_opts)
            if num_selected == 3 and num_correct == 4:
                return 3, "partial"
            elif num_selected == 2 and num_correct >= 3:
                return 2, "partial"
            elif num_selected == 1 and num_correct >= 2:
                return 1, "partial"
            else:
                return 1, "partial"

        # Section 3: Numerical Value (Rel Q9-12) -> +4 / 0 (no negative)
        elif 9 <= rel_q <= 12:
            if is_grace:
                return 4, "correct"
            if is_skipped:
                return 0, "skipped"
            if is_invalid:
                return 0, "wrong"
            matched = False
            for c in correct_parts:
                try:
                    if abs(float(ans_str) - float(c)) < 1e-4:
                        matched = True
                        break
                except:
                    if ans_str == c:
                        matched = True
                        break
            return (4, "correct") if matched else (0, "wrong")

        # Section 4: Matching List MCQ (Rel Q13-16) -> +4 / -1 / 0
        elif 13 <= rel_q <= 16:
            if is_grace:
                return 4, "correct"
            if is_skipped:
                return 0, "skipped"
            if is_invalid or "," in ans_str:
                return -1, "wrong"
            if ans_str in correct_parts:
                return 4, "correct"
            return -1, "wrong"

    elif exam_type == "JEE_ADV_2":
        try:
            q_int = int(q_num_raw)
        except:
            q_int = 1
        rel_q = ((q_int - 1) % 18) + 1

        # Section 1: Single Correct MCQ (Rel Q1-4) -> +3 / -1 / 0
        if 1 <= rel_q <= 4:
            if is_grace:
                return 3, "correct"
            if is_skipped:
                return 0, "skipped"
            if is_invalid or "," in ans_str:
                return -1, "wrong"
            if ans_str in correct_parts:
                return 3, "correct"
            return -1, "wrong"

        # Section 2: Multi-Correct MCQ (Rel Q5-9) -> +4 / (+3, +2, +1) / -1 / 0
        elif 5 <= rel_q <= 9:
            if is_grace:
                return 4, "correct"
            if is_skipped:
                return 0, "skipped"
            if is_invalid:
                return -1, "wrong"
            student_opts = set([p.strip().upper() for p in ans_str.split(",") if p.strip()])
            correct_opts = set([p for p in correct_parts if p != "*"])

            if not student_opts.issubset(correct_opts):
                return -1, "wrong"
            if student_opts == correct_opts:
                return 4, "correct"

            num_selected = len(student_opts)
            num_correct = len(correct_opts)
            if num_selected == 3 and num_correct == 4:
                return 3, "partial"
            elif num_selected == 2 and num_correct >= 3:
                return 2, "partial"
            elif num_selected == 1 and num_correct >= 2:
                return 1, "partial"
            else:
                return 1, "partial"

        # Section 3: Numerical (Rel Q10-14) -> +4 / 0 (no negative)
        elif 10 <= rel_q <= 14:
            if is_grace:
                return 4, "correct"
            if is_skipped:
                return 0, "skipped"
            if is_invalid:
                return 0, "wrong"
            matched = False
            for c in correct_parts:
                try:
                    if abs(float(ans_str) - float(c)) < 1e-4:
                        matched = True
                        break
                except:
                    if ans_str == c:
                        matched = True
                        break
            return (4, "correct") if matched else (0, "wrong")

        # Section 4: Numerical Stem (Rel Q15-18) -> +2 / 0 (no negative)
        elif 15 <= rel_q <= 18:
            if is_grace:
                return 2, "correct"
            if is_skipped:
                return 0, "skipped"
            if is_invalid or "," in ans_str:
                return 0, "wrong"
            matched = False
            for c in correct_parts:
                try:
                    if abs(float(ans_str) - float(c)) < 1e-4:
                        matched = True
                        break
                except:
                    if ans_str == c:
                        matched = True
                        break
            return (2, "correct") if matched else (0, "wrong")

    # Default Standard Scoring (JEE Mains / NEET): +4 / -1 / 0
    if is_grace:
        return 4, "correct"
    if is_skipped:
        return 0, "skipped"
    if is_invalid or "," in ans_str:
        return -1, "wrong"
    if ans_str in correct_parts:
        return 4, "correct"
    return -1, "wrong"


@app.post("/generate")
async def generate_results(request: dict):
    answer_key = request.get("answer_key", {})
    students = request.get("students", [])
    exam_type = request.get("exam_type", "JEE")
    exam_name = request.get("exam_name", "Exam")
    
    results = []
    for student in students:
        name = student.get("name", "Unknown")
        data = student.get("data", {})
        total_score = 0
        subject_scores = {}
        
        for subject, questions in data.items():
            correct = 0
            incorrect = 0
            skipped = 0
            subj_score = 0
            key_section = answer_key.get(subject, {})
            
            for q_num, answer in questions.items():
                correct_ans = key_section.get(q_num, "")
                pts, status = score_question(exam_type, q_num, answer, correct_ans)
                
                if status in ("correct", "partial"):
                    correct += 1
                elif status == "wrong":
                    incorrect += 1
                else:
                    skipped += 1
                subj_score += pts
            
            subject_scores[subject] = {
                "score": subj_score,
                "correct": correct,
                "incorrect": incorrect,
                "skipped": skipped
            }
            total_score += subj_score
        
        results.append({
            "name": name,
            "total_score": total_score,
            "subjects": subject_scores
        })
    
    # Sort by total score descending
    results.sort(key=lambda x: x["total_score"], reverse=True)
    
    scores = [r["total_score"] for r in results]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    top_score = max(scores) if scores else 0
    
    return {
        "status": "success",
        "exam_name": exam_name,
        "total_students": len(results),
        "average": avg_score,
        "top_score": top_score,
        "leaderboard": results
    }

app.mount("/omr_jee", StaticFiles(directory=JEE_DIR), name="jee_images")
app.mount("/omr_neet", StaticFiles(directory=NEET_DIR), name="neet_images")
app.mount("/omr_new_neet", StaticFiles(directory=NEW_NEET_DIR), name="new_neet_images")
app.mount("/omr_jee_adv_1", StaticFiles(directory=JEE_ADV_1_DIR), name="jee_adv_1_images")
app.mount("/omr_jee_adv_2", StaticFiles(directory=JEE_ADV_2_DIR), name="jee_adv_2_images")
app.mount("/assets", StaticFiles(directory=os.path.join(ENGINE_DIR, "assets")), name="assets")
app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
