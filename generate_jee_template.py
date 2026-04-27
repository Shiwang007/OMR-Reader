import json
import os

def generate_jee_template():
    # Constants for high-res A4 (2480 x 3508 @ 300dpi)
    # Actually, your previous engine used 2480x3442
    W_MM = 210
    H_MM = 296 # As set in HTML
    
    PX_PER_MM_X = 2480 / W_MM # 11.809
    PX_PER_MM_Y = 3442 / H_MM # 11.628
    
    def mm_to_px(mm_x, mm_y):
        return {
            "abs_x": round(mm_x * PX_PER_MM_X, 2),
            "abs_y": round(mm_y * PX_PER_MM_Y, 2)
        }

    template = {
        "page1": {
            "Physics": [],
            "Chemistry": [],
            "Mathematics": []
        },
        "page2": {
            "Physics": [],
            "Chemistry": [],
            "Mathematics": []
        }
    }

    # --- PAGE 1: MCQs ---
    # Based on HTML: padding 15mm, header/candidate boxes ~80mm top area
    # Subject blocks start around 95mm down
    start_y = 105 
    row_height = 6.2 # mm (approx row height in HTML)
    col_width = 60 # mm
    bubble_gap = 6 # mm
    
    subjects = ["Physics", "Chemistry", "Mathematics"]
    for s_idx, subj in enumerate(subjects):
        base_x = 15 + (s_idx * col_width) + 20 # Offset for q-num
        for q in range(20):
            q_y = start_y + (q * row_height)
            row_coords = []
            for opt in range(4):
                opt_x = base_x + (opt * bubble_gap)
                row_coords.append(mm_to_px(opt_x, q_y))
            template["page1"][subj].append(row_coords)

    # --- PAGE 2: NUMERICALS ---
    # padding 15mm, section title ~20mm
    # Grid starts around 40mm down
    num_start_y = 50
    num_block_h = 42 # mm
    num_block_w = 60 # mm
    
    for s_idx, subj in enumerate(subjects):
        base_x = 15 + (s_idx * num_block_w)
        for q in range(5):
            q_y_top = num_start_y + (q * num_block_h) + 12 # Start of bubbles
            
            q_data = {
                "digits": [], # 4 columns
                "special": [], # - and .
                "decimals": [] # 2 columns
            }
            
            # Digit Columns (4)
            # Each digit has 2 sub-columns (0-4 and 5-9)
            digit_w = 8.5
            for d in range(4):
                d_x_base = base_x + (d * digit_w) + 2
                col_coords = []
                for val in range(10):
                    row = val % 5
                    col = 0 if val < 5 else 1
                    b_x = d_x_base + (col * 4)
                    b_y = q_y_top + (row * 3.8)
                    col_coords.append(mm_to_px(b_x, b_y))
                q_data["digits"].append(col_coords)
            
            # Special Column (-, .)
            spec_x = base_x + (4 * digit_w) + 3
            q_data["special"] = [
                mm_to_px(spec_x, q_y_top + 5), # Minus
                mm_to_px(spec_x, q_y_top + 15) # Dot
            ]
            
            # Decimal Columns (2)
            dec_start_x = spec_x + 6
            for d in range(2):
                d_x_base = dec_start_x + (d * digit_w)
                col_coords = []
                for val in range(10):
                    row = val % 5
                    col = 0 if val < 5 else 1
                    b_x = d_x_base + (col * 4)
                    b_y = q_y_top + (row * 3.8)
                    col_coords.append(mm_to_px(b_x, b_y))
                q_data["decimals"].append(col_coords)
                
            template["page2"][subj].append(q_data)

    output_path = r"f:\Medjeex\Medjeex-OMR-Engine\templates\jee_mains_template.json"
    with open(output_path, 'w') as f:
        json.dump(template, f, indent=2)
    
    print(f"Template generated at {output_path}")

if __name__ == "__main__":
    generate_jee_template()
