# Medjeex OMR Engine & Reporting Studio

A professional-grade Optical Mark Recognition (OMR) system and reporting dashboard designed for high-accuracy processing of JEE and NEET assessment sheets.

## 🚀 Key Features

- **High-Accuracy OMR Processing**: Adaptive thresholding and dynamic block alignment handle variable scan quality and teacher annotations.
- **OMR Studio (Web Dashboard)**: A modern, real-time interface for uploading scans, manually overriding detected marks, and generating instant results.
- **Automated Reporting**: Generates premium, branded student scorecards and leaderboards in PDF format.
- **Dual Support**: Specialized processing engines for both **JEE Mains** (MCQ + Numerical) and **NEET** (AITS) formats.
- **Smart Scoring**: Supports multiple correct options (array-based keys), bonus marks, and subject-wise performance analytics.

## 📁 Project Structure

- `studio/`: The web interface (FastAPI + Vanilla JS) for real-time processing and manual verification.
- `src/`: Core engine logic for `JEEOMREngine` and `NEETOMREngine`.
- `scripts/`: Bulk generation tools for large-scale batch processing.
- `templates/`: HTML/CSS reporting templates and OMR calibration JSON files.
- `assets/`: Branding assets (logos) used for PDF embedding.
- `answer/`: Master answer keys for different exam sessions.

## 🛠 Setup & Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Launch the Studio**:
   ```bash
   cd studio
   python app.py
   ```
   Access the dashboard at `http://localhost:8000`.

3. **Bulk Processing**:
   For large datasets, use the scripts in the `scripts/` directory:
   ```bash
   python scripts/bulk_generate_jee.py
   ```

## 📋 Workflow

1. **Upload**: Drop OMR scans into the Studio or the corresponding `data/` folder.
2. **Process**: The engine detects bubbles and provides a visual verification overlay.
3. **Verify**: Use the Studio's answer panel to manually correct any "INVALID" or "SKIPPED" marks.
4. **Generate**: Export student scorecards and leaderboards directly to PDF with automated branding injection.

## 🎨 Customization

- **Logo**: Replace `assets/Medjeex_Logo.png` to update branding across all reports.
- **Templates**: Modify the HTML files in `templates/` to change report layouts or styles.

---
Built by Shiwang007 for Medjeex EdTech.
