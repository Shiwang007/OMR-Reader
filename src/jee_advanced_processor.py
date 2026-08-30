import cv2
import numpy as np
import json
import os

class JEEAdvancedOMREngine:
    def __init__(self, template_path="templates/jee_advanced_template.json", canonical_size=(2480, 3442)):
        self.template_path = template_path
        self.canonical_width, self.canonical_height = canonical_size
        self.template_data = None
        if os.path.exists(template_path):
            with open(template_path, "r") as f:
                self.template_data = json.load(f)

    def align_image(self, img):
        """Align input image to standard canonical size 2480x3442 using top-left, top-right, bottom-left, bottom-right black corner marker blocks."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
        h, w = gray.shape[:2]
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 80, 255, cv2.THRESH_BINARY_INV)

        cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        corners = []
        # Margin from edges (corner markers are within 300px from corners)
        x_margin = max(150, int(w * 0.15))
        y_margin = max(150, int(h * 0.15))

        for c in cnts:
            x, y, cw, ch = cv2.boundingRect(c)
            aspect_ratio = cw / float(ch)
            area = cv2.contourArea(c)
            
            # Corner markers in Image 3 are solid black squares ~21x21 px (area ~370..400)
            if 14 < cw < 50 and 14 < ch < 50 and 0.70 < aspect_ratio < 1.35 and 180 < area < 1500:
                cx, cy = x + cw / 2.0, y + ch / 2.0
                # Must be located in outer corner zones
                if (cx < x_margin or cx > w - x_margin) and (cy < y_margin or cy > h - y_margin):
                    corners.append((cx, cy))

        if len(corners) < 4:
            # Fallback: simple resize if fiducials aren't detected
            resized = cv2.resize(img, (self.canonical_width, self.canonical_height))
            return resized, None

        # Sort into 4 distinct quadrants: Top-Left, Top-Right, Bottom-Left, Bottom-Right
        tl = min(corners, key=lambda p: p[0]**2 + p[1]**2)
        tr = min(corners, key=lambda p: (p[0] - w)**2 + p[1]**2)
        bl = min(corners, key=lambda p: p[0]**2 + (p[1] - h)**2)
        br = min(corners, key=lambda p: (p[0] - w)**2 + (p[1] - h)**2)

        pts_src = np.array([tl, tr, br, bl], dtype="float32")
        
        pts_dst = np.array([
            [66, 211],
            [2365, 220],
            [2357, 3205],
            [57, 3194]
        ], dtype="float32")

        M = cv2.getPerspectiveTransform(pts_src, pts_dst)
        warped = cv2.warpPerspective(img, M, (self.canonical_width, self.canonical_height))
        return warped, M

    def get_fill_density(self, img_gray, center_x, center_y, radius=12):
        """Measure average pixel darkness inside a circular mask at (center_x, center_y). Returns density [0.0..1.0] where 1.0 is pure black (filled)."""
        x, y = int(center_x), int(center_y)
        h, w = img_gray.shape[:2]
        
        y1, y2 = max(0, y - radius), min(h, y + radius + 1)
        x1, x2 = max(0, x - radius), min(w, x + radius + 1)
        
        roi = img_gray[y1:y2, x1:x2]
        if roi.size == 0:
            return 0.0
            
        mask = np.zeros_like(roi, dtype=np.uint8)
        cv2.circle(mask, (x - x1, y - y1), radius, 255, -1)
        
        inv_roi = 255 - roi
        mean_darkness = cv2.mean(inv_roi, mask=mask)[0]
        return mean_darkness / 255.0

    def process_omr(self, image_path):
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Could not load image at {image_path}")

        warped, M = self.align_image(img)
        gray_warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)

        template = self.template_data

        results = {
            "roll_number": "",
            "questions": {},
            "subjects": {"Maths": {}, "Physics": {}, "Chemistry": {}}
        }

        vis_img = warped.copy()

        # 1. Process Roll Number Grid
        roll_digits = []
        if "roll_number_grid" in template:
            for col_i, col in enumerate(template["roll_number_grid"]):
                densities = []
                for b in col:
                    d = self.get_fill_density(gray_warped, b["x"], b["y"])
                    densities.append((d, b["val"], b["x"], b["y"]))

                densities.sort(key=lambda item: item[0], reverse=True)
                top_d, top_val, bx, by = densities[0]
                
                # Dark filled mark threshold > 0.55
                if top_d > 0.55:
                    roll_digits.append(top_val)
                    cv2.circle(vis_img, (int(bx), int(by)), 14, (255, 0, 0), -1)
                else:
                    roll_digits.append("?")
        results["roll_number"] = "".join(roll_digits)

        # 2. Process Questions
        if "questions" in template:
            for q_str, q_info in template["questions"].items():
                q_num = int(q_str)
                q_type = q_info["type"]
                subject = q_info["subject"]
                
                if q_type == "mcq":
                    densities = []
                    bubble_coords = []
                    for b in q_info["bubbles"]:
                        d = self.get_fill_density(gray_warped, b["x"], b["y"])
                        densities.append(d)
                        bubble_coords.append((b["opt"], b["x"], b["y"]))
                    
                    dens_arr = np.array(densities)
                    min_d = np.min(dens_arr)
                    max_d = np.max(dens_arr)
                    
                    marked_opts = []
                    for i, d in enumerate(densities):
                        opt, bx, by = bubble_coords[i]
                        # Dark filled mark threshold > 0.55 or > min_d + 0.25
                        if d > 0.55 or (d > min_d + 0.25 and d > 0.50):
                            marked_opts.append(opt)
                            cv2.circle(vis_img, (int(bx), int(by)), 14, (0, 255, 0), -1)
                        else:
                            cv2.circle(vis_img, (int(bx), int(by)), 12, (0, 180, 0), 1)
                            
                    rel_q = ((q_num - 1) % 16) + 1
                    if len(marked_opts) == 0:
                        res_val = "SKIPPED"
                    elif (1 <= rel_q <= 4) or (13 <= rel_q <= 16):
                        res_val = marked_opts[0] if len(marked_opts) == 1 else "INVALID"
                    else:
                        res_val = ",".join(marked_opts)

                    results["questions"][q_str] = res_val
                    results["subjects"][subject][f"Q{q_str}"] = res_val

                elif q_type == "numerical":
                    digit_str = ""
                    for col_i, col in enumerate(q_info["columns"]):
                        densities = []
                        for b in col:
                            d = self.get_fill_density(gray_warped, b["x"], b["y"])
                            densities.append((d, b["val"], b["x"], b["y"]))
                        
                        densities.sort(key=lambda item: item[0], reverse=True)
                        top_d, top_val, bx, by = densities[0]
                        
                        for _, _, c_bx, c_by in densities[1:]:
                            cv2.circle(vis_img, (int(c_bx), int(c_by)), 12, (0, 0, 255), 1)

                        if top_d > 0.55:
                            if top_val == "-":
                                digit_str += "-"
                            else:
                                digit_str += top_val
                            cv2.circle(vis_img, (int(bx), int(by)), 14, (0, 0, 255), -1)
                        else:
                            if col_i == 0 and len(col) == 1 and col[0]["val"] == "-":
                                # It's just a minus sign column that wasn't filled -> positive number
                                pass
                            else:
                                digit_str += "?"
                            
                    # Add decimal point before last two digits if there are at least 3 digits
                    actual_digits = digit_str.replace("-", "")
                    if len(actual_digits) >= 3:
                        if digit_str.startswith("-"):
                            digit_str = digit_str[:-2] + "." + digit_str[-2:]
                        else:
                            digit_str = digit_str[:-2] + "." + digit_str[-2:]

                    res_val = digit_str if "?" not in digit_str else "SKIPPED"
                    results["questions"][q_str] = res_val
                    results["subjects"][subject][f"Q{q_str}"] = res_val

        return results, warped, vis_img
