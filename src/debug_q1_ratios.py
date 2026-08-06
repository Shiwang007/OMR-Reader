import cv2, numpy as np, json

img = cv2.imread(r'f:\Medjeex\Medjeex-OMR-Engine\output\mock_filled_img4.jpg')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 51, 15)
t = json.load(open(r'f:\Medjeex\Medjeex-OMR-Engine\output\img4_template.json'))

def fill_ratio(x, y, r=12):
    mask = np.zeros(binary.shape, np.uint8)
    cv2.circle(mask, (int(x), int(y)), r, 255, -1)
    total = cv2.countNonZero(mask)
    dark = cv2.countNonZero(cv2.bitwise_and(binary, binary, mask=mask))
    return dark / max(total, 1)

# Check Q1, Q19, Q37 (first MCQ of each subject) fill ratios
for qn in ['1', '19', '37']:
    q = t['questions'][qn]
    print(f'Q{qn} MCQ bubbles:')
    for b in q['bubbles']:
        r = fill_ratio(b['x'], b['y'])
        print(f'  opt={b["opt"]} at ({int(b["x"])},{int(b["y"])}): ratio={r:.3f}')

# Also check what the template stored for Q1 - is it pointing to the section header?
print('\nQ1 coordinates vs Section header area:')
q1b = t['questions']['1']['bubbles']
for b in q1b:
    print(f'  {b["opt"]} x={b["x"]:.0f} y={b["y"]:.0f}')
