import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.neet_dropper_processor import NEETDropperOMREngine

def test_all_scans():
    engine = NEETDropperOMREngine()
    folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "NEET Dropper 1.O (2)")
    
    files = [f for f in sorted(os.listdir(folder)) if f.endswith(".jpg")]
    print(f"Testing {len(files)} NEET Dropper scans...")
    
    total_marked = 0
    total_invalid = 0
    total_skipped = 0
    
    start_t = time.time()
    
    for f in files:
        img_path = os.path.join(folder, f)
        res, viz = engine.process_sheet(img_path)
        
        counts = {}
        file_marked = 0
        file_invalid = 0
        file_skipped = 0
        
        for subj, q_map in res.items():
            m = sum(1 for a in q_map.values() if a not in ["SKIPPED", "INVALID"])
            inv = sum(1 for a in q_map.values() if a == "INVALID")
            sk = sum(1 for a in q_map.values() if a == "SKIPPED")
            counts[subj] = m
            file_marked += m
            file_invalid += inv
            file_skipped += sk
            
        total_marked += file_marked
        total_invalid += file_invalid
        total_skipped += file_skipped
        
        print(f"  {f:18s} -> Total Marked: {file_marked:2d}, Invalid: {file_invalid:2d} | Physics: {counts.get('Physics', 0):2d}, Chem: {counts.get('Chemistry', 0):2d}, Bio1: {counts.get('Biology I', 0):2d}, Bio2: {counts.get('Biology II', 0):2d}")

    elapsed = time.time() - start_t
    print("\n" + "="*60)
    print(f"Processed {len(files)} sheets in {elapsed:.2f}s ({elapsed/len(files):.3f}s per sheet)")
    print(f"Total Marked Bubbles: {total_marked}")
    print(f"Total Invalid/Multi-marked: {total_invalid}")
    print(f"Total Skipped: {total_skipped}")
    print("="*60)

if __name__ == "__main__":
    test_all_scans()
