import os
from pypdf import PdfWriter

# Paths
PDF_DIR = r"f:\Medjeex\Medjeex-OMR-Engine\reports\jee_pdfs"
OUTPUT_FILE = r"f:\Medjeex\Medjeex-OMR-Engine\reports\All_JEE_Scorecards_Consolidated.pdf"

def merge_jee_pdfs():
    merger = PdfWriter()
    
    # Get all PDF files and sort them alphabetically
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
    pdf_files.sort()
    
    if not pdf_files:
        print("No JEE PDF files found to merge.")
        return

    print(f"Merging {len(pdf_files)} JEE Scorecards...")
    
    for filename in pdf_files:
        filepath = os.path.join(PDF_DIR, filename)
        try:
            merger.append(filepath)
            print(f"  + Added: {filename}")
        except Exception as e:
            print(f"  [ERROR] Failed to add {filename}: {e}")
        
    with open(OUTPUT_FILE, "wb") as f:
        merger.write(f)
    
    merger.close()
    print(f"\n--- SUCCESS! Consolidated JEE PDF created at: {OUTPUT_FILE} ---")

if __name__ == "__main__":
    merge_jee_pdfs()
