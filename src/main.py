from fastapi import FastAPI, UploadFile, File, HTTPException
from processor import OMREngine
import shutil
import os
import uuid

app = FastAPI(title="Medjeex OMR Engine")
engine = OMREngine()

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/health")
def health():
    return {"status": "ready", "engine": "Medjeex OMR 1.0"}

@app.post("/process")
async def process_omr(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only images and PDFs are supported.")
    
    # Save the file temporarily
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Process the image
        # Note: If it's a PDF, we'd need to convert it first. For now, assuming image.
        results = engine.process_full_sheet(file_path)
        
        if "error" in results:
            raise HTTPException(status_code=422, detail=results["error"])
            
        return {
            "file_id": file_id,
            "filename": file.filename,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup can be done here or via a background task
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
