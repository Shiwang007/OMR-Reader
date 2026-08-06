"""
Create a mock filled OMR image for Image 4 with known answers,
then run the processor on it and verify the output.

Known answers filled:
  MCQ: Q1=A, Q2=B, Q3=C, Q4=D, Q5=A, Q6=B, Q7=C, Q8=D, Q9=A
       Q19=A, Q20=B, Q21=A,B (multi), Q22=C, Q23=D, Q24=A, Q25=B, Q26=C, Q27=D, Q28=A
       Q37=B, Q38=C, Q39=D, Q40=A, Q41=B, Q42=A,C (multi), Q43=D, Q44=A, Q45=C

  NUM: Every question is 6 digits + optional minus sign (e.g. "-123456").
       Q10=123456, Q11=-123456, Q12=901234, etc.
"""
import cv2
import numpy as np
import json

# Load template
with open(r"f:\Medjeex\Medjeex-OMR-Engine\output\img4_template.json") as f:
    template = json.load(f)

# Load blank (unwarped) image
img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped_img4.jpg")

# Known answers
MCQ_ANSWERS = {
    "1": ["A"], "2": ["B"], "3": ["C"], "4": ["D"],
    "5": ["A"], "6": ["B"], "7": ["C"], "8": ["D"], "9": ["A"],
    "19": ["A"], "20": ["B"], "21": ["A", "B"], "22": ["C"],
    "23": ["D"], "24": ["A"], "25": ["B"], "26": ["C"], "27": ["D"],
    "37": ["B"], "38": ["C"], "39": ["D"], "40": ["A"],
    "41": ["B"], "42": ["A", "C"], "43": ["D"], "44": ["A"], "45": ["C"],
}
# Numerical: Up to 6 digits + optional minus sign
NUM_ANSWERS = {
    "10": "123456", "11": "-654321", "12": "901234",
    "13": "345678", "14": "-789012", "15": "111111",
    "16": "222222", "17": "-333333", "18": "444444",
    "28": "444444", "29": "555555", "30": "-666666",
    "31": "777777", "32": "888888", "33": "-999999",
    "34": "000000", "35": "123456", "36": "-567890",
    "46": "987654", "47": "-543210", "48": "109876",
    "49": "765432", "50": "-321098", "51": "987012",
    "52": "654321", "53": "-210987", "54": "876543",
}

def fill_bubble(img, x, y, r=12):
    cv2.circle(img, (int(x), int(y)), r, (0, 0, 0), -1)

questions = template["questions"]
filled = 0

for q_num, q_data in questions.items():
    if q_data["type"] == "mcq":
        if q_num in MCQ_ANSWERS:
            opts_to_fill = MCQ_ANSWERS[q_num]
            for b in q_data["bubbles"]:
                if b["opt"] in opts_to_fill:
                    fill_bubble(img, b["x"], b["y"])
                    filled += 1
    elif q_data["type"] == "numerical":
        if q_num in NUM_ANSWERS:
            ans_str = NUM_ANSWERS[q_num]
            if ans_str.startswith("-"):
                minus_b = next((b for b in q_data["bubbles"] if b["opt"] == "minus"), None)
                if minus_b: 
                    fill_bubble(img, minus_b["x"], minus_b["y"])
                    filled += 1
                ans_str = ans_str[1:]
                
            ans_str = ans_str.zfill(6) # pad to 6 digits if needed
            for i, digit in enumerate(ans_str):
                opt_key = f"{i}_{digit}"
                b = next((b for b in q_data["bubbles"] if b["opt"] == opt_key), None)
                if b: 
                    fill_bubble(img, b["x"], b["y"])
                    filled += 1

print(f"Filled {filled} bubbles")
cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\output\mock_filled_img4.jpg", img)
print("Saved mock_filled_img4.jpg")
