import os
from pypdf import PdfWriter

PDF_DIR = r"f:\Medjeex\Medjeex-OMR-Engine\omr_pdfs"
OUTPUT_FILE = r"f:\Medjeex\Medjeex-OMR-Engine\All_Students_Scorecards.pdf"

def merge_pdfs():
    merger = PdfWriter()
    
    # Get all PDF files and sort them alphabetically
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
    pdf_files.sort()
    
    if not pdf_files:
        print("No PDF files found to merge.")
        return

    print(f"Merging {len(pdf_files)} reports...")
    for filename in pdf_files:
        filepath = os.path.join(PDF_DIR, filename)
        merger.append(filepath)
        print(f"  + Added {filename}")

    with open(OUTPUT_FILE, "wb") as f:
        merger.write(f)
    
    merger.close()
    print(f"\nSUCCESS! Consolidated PDF created at: {OUTPUT_FILE}")

if __name__ == "__main__":
    merge_pdfs()
