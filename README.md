# OMR Reader

Advanced Optical Mark Recognition (OMR) engine designed for high-accuracy processing of assessment sheets, even with heavy teacher annotations and variable scan quality.

## Features
- **Dynamic Block Alignment**: Automatically calculates X/Y physical shifts per subject block using contour moments.
- **Noise Filtering**: Uses circular ROI masking to ignore corner annotations (like teacher ticks).
- **Smart Winner Logic**: Resolves multi-mark conflicts by comparing fill densities.
- **Adaptive Thresholding**: Optimizes contrast for both pencil and ink marks.
- **Verification Layer**: Generates annotated images showing exactly where the engine detected marks.

## Structure
- `src/`: Core engine logic (`processor.py`) and utility scripts.
- `templates/`: OMR sheet calibration files (`template.json`).
- `data/`: Results and verification audits.

## Usage
1. **Calibrate**: Run `src/calibrate.py` on a blank or master sheet to generate `template.json`.
2. **Scan**:
   ```python
   from src.processor import OMREngine
   engine = OMREngine()
   results = engine.process_full_sheet("path/to/scan.jpg")
   ```

## Requirements
- Python 3.7+
- OpenCV
- NumPy
- imutils

---
Built by Shiwang007.
