"""
Reads a filled Image 4 OMR sheet (already warped to canonical_warped_img4.jpg dimensions)
and returns the detected answers using the img4_template.json.

Usage:
    processor = Img4Processor("path/to/img4_template.json")
    results = processor.read("path/to/filled_img.jpg", align=False)
"""
import cv2
import numpy as np
import json


class Img4Processor:
    def __init__(self, template_path):
        with open(template_path) as f:
            self.template = json.load(f)

    def read(self, img_path, align=False, fill_thresh=0.60):
        img = cv2.imread(img_path)
        if img is None:
            raise FileNotFoundError(f"Cannot read: {img_path}")

        if align:
            img = self._align(img)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 51, 15
        )

        vis = img.copy()
        results = {}

        def bubble_filled(x, y, r=9):
            mask = np.zeros(binary.shape, np.uint8)
            cv2.circle(mask, (int(x), int(y)), r, 255, -1)
            total = cv2.countNonZero(mask)
            dark  = cv2.countNonZero(cv2.bitwise_and(binary, binary, mask=mask))
            ratio = dark / max(total, 1)
            return ratio > fill_thresh, ratio

        for q_num, q_data in self.template["questions"].items():
            if int(q_num) > 54:
                continue  # skip any extras

            bubbles = q_data["bubbles"]

            if q_data["type"] == "mcq":
                selected = []
                for b in bubbles:
                    filled, ratio = bubble_filled(b["x"], b["y"])
                    color = (0, 200, 0) if filled else (0, 0, 200)
                    cv2.circle(vis, (int(b["x"]), int(b["y"])), 9, color, 2)
                    if filled:
                        selected.append(b["opt"])
                        cv2.circle(vis, (int(b["x"]), int(b["y"])), 6, (0, 200, 0), -1)
                results[q_num] = selected

            else:  # numerical
                digits = {}   # col_i -> val_i
                is_negative = False
                for b in bubbles:
                    filled, ratio = bubble_filled(b["x"], b["y"])
                    color = (0, 200, 0) if filled else (0, 0, 200)
                    cv2.circle(vis, (int(b["x"]), int(b["y"])), 9, color, 2)
                    if filled:
                        cv2.circle(vis, (int(b["x"]), int(b["y"])), 6, (0, 200, 0), -1)
                        if b["opt"] == "minus":
                            is_negative = True
                        else:
                            col_i, val_i = map(int, b["opt"].split("_"))
                            digits[col_i] = val_i
                            
                # Determine number of digit columns from template bubbles
                num_cols = max(
                    (int(b["opt"].split("_")[0]) for b in bubbles if b["opt"] != "minus"),
                    default=-1
                ) + 1
                digit_str = "".join(str(digits.get(c, "?")) for c in range(num_cols))
                if len(digit_str) >= 2:
                    digit_str = digit_str[:-2] + "." + digit_str[-2:]
                
                final_str = ("-" if is_negative else "") + digit_str
                results[q_num] = final_str

        return results, vis

    def _align(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 80, 255, cv2.THRESH_BINARY_INV)
        cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        corners = []
        h, w = img.shape[:2]
        for c in cnts:
            x, y, cw, ch = cv2.boundingRect(c)
            ar = cw / float(ch)
            area = cv2.contourArea(c)
            if 10 < cw < 110 and 10 < ch < 110 and 0.7 < ar < 1.3 and area > 200:
                cx, cy = x + cw/2.0, y + ch/2.0
                if (cx < 200 or cx > w - 200) and (cy < 200 or cy > h - 200):
                    corners.append((cx, cy))
        if len(corners) != 4:
            raise ValueError(f"Expected 4 corner markers, found {len(corners)}")
        corners = sorted(corners, key=lambda p: p[1])
        tl, tr = sorted(corners[:2], key=lambda p: p[0])
        bl, br = sorted(corners[-2:], key=lambda p: p[0])
        W, H = 2480, 3442
        M = cv2.getPerspectiveTransform(
            np.array([tl, tr, br, bl], dtype="float32"),
            np.array([[66,211],[2365,220],[2357,3205],[57,3194]], dtype="float32")
        )
        return cv2.warpPerspective(img, M, (W, H))


# ── Self-test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    TEMPLATE = r"f:\Medjeex\Medjeex-OMR-Engine\output\img4_template.json"
    MOCK     = r"f:\Medjeex\Medjeex-OMR-Engine\output\mock_filled_img4.jpg"
    VIS_OUT  = r"f:\Medjeex\Medjeex-OMR-Engine\output\mock_read_vis_img4.jpg"

    EXPECTED_MCQ = {
        "1": ["A"], "2": ["B"], "3": ["C"], "4": ["D"],
        "5": ["A"], "6": ["B"], "7": ["C"], "8": ["D"], "9": ["A"],
        "19": ["A"], "20": ["B"], "21": ["A", "B"], "22": ["C"],
        "23": ["D"], "24": ["A"], "25": ["B"], "26": ["C"], "27": ["D"],
        "37": ["B"], "38": ["C"], "39": ["D"], "40": ["A"],
        "41": ["B"], "42": ["A", "C"], "43": ["D"], "44": ["A"], "45": ["C"],
    }
    EXPECTED_NUM = {
        "10": "1234.56", "11": "-6543.21", "12": "9012.34",
        "13": "3456.78", "14": "-7890.12", "15": "1111.11",
        "16": "2222.22", "17": "-3333.33", "18": "4444.44",
        "28": "4444.44", "29": "5555.55", "30": "-6666.66", "31": "7777.77",
        "32": "8888.88", "33": "-9999.99", "34": "0000.00",
        "35": "1234.56", "36": "-5678.90",
        "46": "9876.54", "47": "-5432.10", "48": "1098.76",
        "49": "7654.32", "50": "-3210.98", "51": "9870.12",
        "52": "6543.21", "53": "-2109.87", "54": "8765.43",
    }

    processor = Img4Processor(TEMPLATE)
    results, vis = processor.read(MOCK, align=False)

    cv2.imwrite(VIS_OUT, vis)
    print(f"Visualisation saved -> {VIS_OUT}\n")

    # ── Verify ─────────────────────────────────────────────────────────────
    ok = fail = 0
    for q_num, res in sorted(results.items(), key=lambda x: int(x[0])):
        q = int(q_num)
        if isinstance(res, list):
            exp = EXPECTED_MCQ.get(q_num, [])
            correct = sorted(res) == sorted(exp)
            status = "+" if correct else "-"
            if correct: ok += 1
            else: fail += 1
            if not correct:
                print(f"  Q{q_num:2s} MCQ  {status}  got={res}  exp={exp}")
        else:
            exp_val = EXPECTED_NUM.get(q_num, "??????")
            got_val = res
            correct = (got_val == exp_val)
            status = "+" if correct else "-"
            if correct: ok += 1
            else: fail += 1
            if not correct:
                print(f"  Q{q_num:2s} NUM  {status}  got={got_val}  exp={exp_val}")

    total = ok + fail
    print(f"\nResult: {ok}/{total} correct ({100*ok//total}%)")
    if fail == 0:
        print("ALL QUESTIONS READ CORRECTLY")
