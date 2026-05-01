import cv2
import numpy as np

def measure_all_bubbles():
    image = cv2.imread(r'f:\Medjeex\Medjeex-OMR-Engine\omr\Image.jpg')
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Target columns
    cols = {
        "Physics": (300, 700),
        "Chemistry": (1000, 1450),
        "Mathematics": (1750, 2200)
    }
    
    results = {}
    for subj, (x1, x2) in cols.items():
        roi = blurred[750:2350, x1:x2]
        circles = cv2.HoughCircles(
            roi, cv2.HOUGH_GRADIENT, dp=1, minDist=50,
            param1=50, param2=25, minRadius=15, maxRadius=30
        )
        
        found = []
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                found.append((i[0] + x1, i[1] + 750))
        
        # Sort by Y then X
        found = sorted(found, key=lambda p: (p[1], p[0]))
        results[subj] = found
        print(f"{subj}: found {len(found)} bubbles")
        
        # Cluster into rows
        if found:
            rows = []
            curr_row = [found[0]]
            for p in found[1:]:
                if p[1] - curr_row[-1][1] < 30: # Same row
                    curr_row.append(p)
                else:
                    rows.append(curr_row)
                    curr_row = [p]
            rows.append(curr_row)
            print(f"  Mapped to {len(rows)} rows")
            
            # Print row Y averages
            for r_idx, r in enumerate(rows):
                avg_y = sum(p[1] for p in r) / len(r)
                avg_x_start = min(p[0] for p in r)
                print(f"    Row {r_idx+1}: Y={avg_y:.1f}, X_start={avg_x_start}")

    return results

if __name__ == "__main__":
    measure_all_bubbles()
