# Medjeex OMR Report Generation Guide

This guide outlines the steps to process student OMR data and generate professional PDF scorecards.

## Prerequisites

- **Python Environment**: Python 3.7 or higher.
- **Dependencies**: `pypdf`, `python-docx` (if parsing keys from docx).
- **Browser**: Microsoft Edge or Google Chrome (required for headless PDF rendering).

## Workflow Steps

### 1. Process OMR Scans (Image to JSON)
Run the OMR engine to detect bubbles and generate JSON data for each student.
```powershell
# Adjust script name as per your latest version (e.g., processor1.py)
python src/processor1.py
```
*Output: Student JSON files in the `/data` folder.*

### 2. Generate Individual PDF Reports
Converts student JSON data into stylized HTML and then into high-fidelity PDF scorecards.
```powershell
# Use the Python 3.7 environment if modules are missing in 3.12
& "C:\Users\shiwa\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.7_qbz5n2kfra8p0\python.exe" generate_pdf_reports.py
```
*Output: `.pdf` files in `/omr_pdfs` and temporary `.html` files in `/omr_reports`.*

### 3. Merge PDFs into a Single File
Combines all individual student PDFs into one consolidated document for bulk printing.
```powershell
& "C:\Users\shiwa\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.7_qbz5n2kfra8p0\python.exe" merge_reports.py
```
*Output: `All_Students_Scorecards.pdf` in the root folder.*

---

## Key Files & Folders

| File/Folder | Description |
| :--- | :--- |
| `/data` | Contains student response JSONs. |
| `/answer` | Contains the `answer_key.json`. |
| `/templates` | Contains `omr_report_template.html` (the visual design). |
| `generate_pdf_reports.py` | Main script for PDF generation. |
| `merge_reports.py` | Script for combining all PDFs. |
| `Medjeex_Logo.png` | The logo used as a watermark in reports. |

## Customizing the Report

- **Date**: To change the date shown on reports, edit the `display_date` variable in `generate_pdf_reports.py`.
- **Layout**: Modify `templates/omr_report_template.html` to change colors, fonts, or positioning.

## Troubleshooting

- **Missing `pypdf`**: Run `pip install pypdf`.
- **Edge Not Found**: Ensure Microsoft Edge is installed at `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe` or update the `EDGE_PATH` variable in the script.
