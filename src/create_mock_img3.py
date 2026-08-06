import cv2
import json
import numpy as np

def create_mock():
    # Read the canonical blank image
    vis_img = cv2.imread(r"f:\Medjeex\Medjeex-OMR-Engine\output\canonical_warped.jpg")
    if vis_img is None:
        print("Canonical image not found!")
        return

    # Load template
    with open(r"f:\Medjeex\Medjeex-OMR-Engine\templates\jee_advanced_template.json") as f:
        template = json.load(f)

    # Mock answers
    mock_answers = {
        "1": "A,B", "2": "C", "3": "A,C", "4": "B,D",
        "5": "A", "6": "D", "7": "B", "8": "C",
        "9": "-1234.56", "10": "9999.00", "11": "-0005.50", "12": "0000.12",
        "13": "A,B,C,D", "14": "A,C", "15": "B,D", "16": "A",

        "17": "A", "18": "B", "19": "C", "20": "D",
        "21": "A,C", "22": "B,D", "23": "A,B,C", "24": "D",
        "25": "-7777.77", "26": "8888.88", "27": "-9999.99", "28": "1000.00",
        "29": "A", "30": "B", "31": "C", "32": "D",

        "33": "A,C", "34": "B,D", "35": "A", "36": "B",
        "37": "C", "38": "D", "39": "A,B", "40": "C,D",
        "41": "-3314.15", "42": "2718.28", "43": "-1414.21", "44": "1732.05",
        "45": "A", "46": "B", "47": "C", "48": "D"
    }

    r = 10 # Bubble radius

    for q_num, ans in mock_answers.items():
        if q_num not in template["questions"]:
            continue
            
        q_data = template["questions"][q_num]
        
        if q_data["type"] == "mcq":
            opts = ans.split(",")
            for opt in opts:
                b = next((b for b in q_data["bubbles"] if b["opt"] == opt), None)
                if b:
                    cv2.circle(vis_img, (int(b["x"]), int(b["y"])), r, (0, 0, 0), -1)
                    
        elif q_data["type"] == "numerical":
            cols = q_data["columns"]
            has_minus = (ans[0] == '-')
            if has_minus and len(cols) > 0 and len(cols[0]) > 0:
                b = cols[0][0]
                cv2.circle(vis_img, (int(b["x"]), int(b["y"])), r, (0, 0, 0), -1)
                
            digit_idx = 1
            for char in ans:
                if char in '-.':
                    continue
                if digit_idx < len(cols):
                    col = cols[digit_idx]
                    b = next((b for b in col if str(b.get("val")) == char), None)
                    if b:
                        cv2.circle(vis_img, (int(b["x"]), int(b["y"])), r, (0, 0, 0), -1)
                digit_idx += 1

    # Save visualization
    cv2.imwrite(r"f:\Medjeex\Medjeex-OMR-Engine\output\mock_read_vis_img3.jpg", vis_img)
    
    # Save JSON result
    with open(r"f:\Medjeex\Medjeex-OMR-Engine\output\mock_result_img3.json", "w") as f:
        json.dump(mock_answers, f, indent=2)
        
    print("Successfully generated mock_read_vis_img3.jpg and mock_result_img3.json")

if __name__ == "__main__":
    create_mock()
