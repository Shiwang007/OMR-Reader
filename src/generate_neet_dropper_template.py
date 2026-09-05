import cv2
import numpy as np
import json
import os

def generate_template(reference_image_path: str, output_template_path: str, debug_image_path: str = None):
    image = cv2.imread(reference_image_path)
    if image is None:
        raise FileNotFoundError(f"Cannot open image: {reference_image_path}")

    h_img, w_img = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # Subject Column Bounds & Configurations
    # 45 questions per subject, 4 options each (A, B, C, D)
    subj_configs = {
        "Physics": {
            "x_bounds": (220, 540),
            "q_start": 1,
            "q_count": 45
        },
        "Chemistry": {
            "x_bounds": (760, 1080),
            "q_start": 46,
            "q_count": 45
        },
        "Biology I": {
            "x_bounds": (1300, 1630),
            "q_start": 91,
            "q_count": 45
        },
        "Biology II": {
            "x_bounds": (1850, 2200),
            "q_start": 136,
            "q_count": 45
        }
    }

    template = {}

    for subj, config in subj_configs.items():
        x_min, x_max = config["x_bounds"]
        roi = thresh[950:3020, x_min:x_max]
        cnts, _ = cv2.findContours(roi, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        xs = []
        ys = []
        for c in cnts:
            (cx, cy), r = cv2.minEnclosingCircle(c)
            area = cv2.contourArea(c)
            if 8 < r < 18 and (area > 80 or cv2.arcLength(c, True) > 40):
                xs.append(cx + x_min)
                ys.append(cy + 950)

        # Cluster X into 4 options (A, B, C, D)
        xs = sorted(xs)
        x_clusters = []
        for x in xs:
            if not x_clusters or abs(x - np.mean(x_clusters[-1])) > 25:
                x_clusters.append([x])
            else:
                x_clusters[-1].append(x)

        opt_xs = [float(np.mean(cl)) for cl in x_clusters if len(cl) > 10]
        opt_xs = sorted(opt_xs)

        # Fallback if an option had fewer detections
        if len(opt_xs) < 4:
            base_x = opt_xs[0]
            pitch = 81.0
            opt_xs = [base_x + i * pitch for i in range(4)]

        # Cluster Y into 45 rows
        ys = sorted(ys)
        y_clusters = []
        for y in ys:
            if not y_clusters or abs(y - np.mean(y_clusters[-1])) > 15:
                y_clusters.append([y])
            else:
                y_clusters[-1].append(y)

        row_ys = [float(np.mean(cl)) for cl in y_clusters if len(cl) > 1]
        row_ys = sorted(row_ys)

        # If exactly 45 rows or close, fit linear regression for sub-pixel accuracy
        if len(row_ys) >= 35:
            # Linear fit: row_y = y0 + i * pitch_y
            indices = np.arange(len(row_ys))
            poly = np.polyfit(indices, row_ys, 1)
            pitch_y = poly[0]
            start_y = poly[1]
            fitted_row_ys = [float(start_y + i * pitch_y) for i in range(45)]
        else:
            fitted_row_ys = row_ys

        subj_rows = []
        for row_y in fitted_row_ys:
            row_bubbles = []
            for opt_x in opt_xs[:4]:
                row_bubbles.append({
                    "abs_x": round(opt_x, 1),
                    "abs_y": round(row_y, 1)
                })
            subj_rows.append(row_bubbles)

        template[subj] = subj_rows

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_template_path), exist_ok=True)
    with open(output_template_path, "w") as f:
        json.dump(template, f, indent=2)

    print(f"Saved NEET Dropper template to: {output_template_path}")
    for subj, rows in template.items():
        print(f"  {subj}: {len(rows)} questions | Row 1 Y={rows[0][0]['abs_y']} | Row 45 Y={rows[-1][0]['abs_y']}")

    # Debug visual verification overlay
    if debug_image_path:
        vis = image.copy()
        colors = [(0, 0, 255), (0, 200, 0), (255, 0, 0), (0, 165, 255)]
        for si, (subj, rows) in enumerate(template.items()):
            color = colors[si % len(colors)]
            for row in rows:
                for b in row:
                    cx, cy = int(b["abs_x"]), int(b["abs_y"])
                    cv2.circle(vis, (cx, cy), 13, color, 2)
                    cv2.circle(vis, (cx, cy), 2, color, -1)
        os.makedirs(os.path.dirname(debug_image_path), exist_ok=True)
        cv2.imwrite(debug_image_path, vis)
        print(f"Saved debug overlay to: {debug_image_path}")

    return template

if __name__ == "__main__":
    ref_img = r"f:\Medjeex\Medjeex-OMR-Engine\NEET Dropper 1.O (2)\Image (2).jpg"
    out_tpl = r"f:\Medjeex\Medjeex-OMR-Engine\templates\neet_dropper_template.json"
    dbg_img = r"f:\Medjeex\Medjeex-OMR-Engine\data\debug_neet_dropper_overlay.jpg"
    generate_template(ref_img, out_tpl, dbg_img)
