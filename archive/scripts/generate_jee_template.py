import json

def generate_perfect_template():
    # Exact Y-coordinates for all 20 rows (Average across subjects for stability)
    # Based on high-precision Hough Circle scan
    y_coords = [
        823.2, 899.5, 976.8, 1055.2, 1134.7, 1211.7, 1289.8, 1367.3, 1446.3, 1525.3,
        1602.0, 1678.8, 1757.0, 1836.0, 1914.5, 1990.3, 2069.5, 2149.3, 2226.3, 2303.0
    ]
    
    # Exact X-starts for each subject column
    x_starts = {
        "Physics": 404,
        "Chemistry": 1124,
        "Mathematics": 1848
    }
    
    bubble_gap = 88.0 # High precision gap
    
    template = {"page1": {}, "page2": {}}
    
    for subj, start_x in x_starts.items():
        subj_rows = []
        for q_idx, q_y in enumerate(y_coords):
            row_coords = []
            for opt in range(4):
                opt_x = start_x + (opt * bubble_gap)
                row_coords.append({"abs_x": round(opt_x, 2), "abs_y": round(q_y, 2)})
            subj_rows.append(row_coords)
        template["page1"][subj] = subj_rows

    template["page2"] = {}
    
    with open(r"f:\Medjeex\Medjeex-OMR-Engine\templates\jee_mains_template.json", "w") as f:
        json.dump(template, f, indent=2)
    print("Point-by-Point Perfect Template generated and saved.")

if __name__ == "__main__":
    generate_perfect_template()
