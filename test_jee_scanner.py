import cv2
import json
import os
from src.jee_processor import JEEOMREngine

def test_scanner():
    engine = JEEOMREngine()
    
    # Path to the sample image
    image_path = r'f:\Medjeex\Medjeex-OMR-Engine\JEE_MAINS_SAMPLE_FILLED.jpg'
    
    if not os.path.exists(image_path):
        print(f"Error: {image_path} not found.")
        return

    # Load the long image and split it into two pages
    full_img = cv2.imread(image_path)
    h, w = full_img.shape[:2]
    mid = h // 2
    
    page1_img = full_img[0:mid, :]
    page2_img = full_img[mid:h, :]
    
    # Save temporary page images for the engine
    cv2.imwrite('page1_temp.jpg', page1_img)
    cv2.imwrite('page2_temp.jpg', page2_img)
    
    print("--- Processing Page 1 (MCQs) ---")
    mcq_results = engine.process_page1('page1_temp.jpg')
    
    print("--- Processing Page 2 (Numericals) ---")
    num_results = engine.process_page2('page2_temp.jpg')
    
    # Combine results
    student_answers = {}
    for subj in ["Physics", "Chemistry", "Mathematics"]:
        student_answers[subj] = {**mcq_results[subj], **num_results[subj]}
    
    # Load Answer Key
    key_path = r'f:\Medjeex\Medjeex-OMR-Engine\answer\jee_answer_key.json'
    with open(key_path, 'r') as f:
        answer_key = json.load(f)
        
    # Calculate Score
    report = engine.score_test(student_answers, answer_key)
    
    # Print Report
    print("\n" + "="*30)
    print("JEE MAINS SCAN REPORT")
    print("="*30)
    for subj, data in report["subjects"].items():
        print(f"\n[{subj}]")
        print(f"Score: {data['score']}")
        print(f"Correct: {data['correct']}")
        print(f"Incorrect: {data['incorrect']}")
        print(f"Skipped: {data['skipped']}")
    
    print("\n" + "="*30)
    print(f"TOTAL SCORE: {report['total_score']} / 300")
    print("="*30)

    # Cleanup
    if os.path.exists('page1_temp.jpg'): os.remove('page1_temp.jpg')
    if os.path.exists('page2_temp.jpg'): os.remove('page2_temp.jpg')

if __name__ == "__main__":
    test_scanner()
