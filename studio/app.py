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
except ImportError as e:
    print(f"Error: {e}")
    sys.exit(1)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Directories
JEE_DIR = os.path.join(ENGINE_DIR, "omr_jee")
NEET_DIR = os.path.join(ENGINE_DIR, "omr_neet")
for d in [JEE_DIR, NEET_DIR]:
    if not os.path.exists(d): os.makedirs(d)

jee_engine = JEEOMREngine()
neet_engine = NEETOMREngine()

# Store engine defaults — UI offsets are added on top
JEE_DEFAULTS = {"x": jee_engine.X_SHIFT, "y": jee_engine.Y_SHIFT}
NEET_DEFAULTS = {"x": neet_engine.X_SHIFT, "y": neet_engine.Y_SHIFT}

@app.post("/upload")
async def upload_files(exam_type: str = Form(...), files: List[UploadFile] = File(...)):
    target_dir = JEE_DIR if exam_type == "JEE" else NEET_DIR
    results = []
    
    for file in files:
        file_path = os.path.join(target_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # Process immediately on upload
        if exam_type == "JEE":
            data, viz_img = jee_engine.process_page1(file_path)
        else:
            data, viz_img = neet_engine.process_sheet(file_path)
            
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
    target_dir = JEE_DIR if exam_type == "JEE" else NEET_DIR
    file_path = os.path.abspath(os.path.join(target_dir, filename))
    defaults = JEE_DEFAULTS if exam_type == "JEE" else NEET_DEFAULTS
    
    if exam_type == "JEE":
        jee_engine.X_SHIFT = defaults["x"] + x_shift
        jee_engine.Y_SHIFT = defaults["y"] + y_shift
        data, viz_img = jee_engine.process_page1(file_path)
    else:
        neet_engine.X_SHIFT = defaults["x"] + x_shift
        neet_engine.Y_SHIFT = defaults["y"] + y_shift
        data, viz_img = neet_engine.process_sheet(file_path)

    img_base64 = ""
    if viz_img is not None:
        _, buffer = cv2.imencode('.jpg', viz_img)
        img_base64 = base64.b64encode(buffer).decode('utf-8')

    return {
        "status": "success",
        "results": data,
        "processed_image": f"data:image/jpeg;base64,{img_base64}"
    }

@app.get("/template/{exam_type}")
async def get_template(exam_type: str):
    if exam_type.upper() == "JEE":
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
            key_section = answer_key.get(subject, {})
            
            for q_num, answer in questions.items():
                correct_ans = key_section.get(q_num, "")
                if answer == "SKIPPED" or answer == "":
                    skipped += 1
                elif answer == "INVALID":
                    skipped += 1
                elif str(answer) == str(correct_ans):
                    correct += 1
                else:
                    incorrect += 1
            
            score = (correct * 4) - (incorrect * 1)
            subject_scores[subject] = {
                "score": score,
                "correct": correct,
                "incorrect": incorrect,
                "skipped": skipped
            }
            total_score += score
        
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
app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
