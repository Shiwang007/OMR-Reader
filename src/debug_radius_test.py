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

print('Testing different radii for Q1 (A filled, B-D should be empty):')
for r in [8, 9, 10, 11, 12]:
    q1 = t['questions']['1']['bubbles']
    ratios = {b['opt']: fill_ratio(b['x'], b['y'], r) for b in q1}
    print(f'  r={r}: A={ratios["A"]:.3f} B={ratios["B"]:.3f} C={ratios["C"]:.3f} D={ratios["D"]:.3f}')

# Also check Q2 (B filled)
print('Q2 (B filled):')
for r in [8, 9, 10]:
    q2 = t['questions']['2']['bubbles']
    ratios = {b['opt']: fill_ratio(b['x'], b['y'], r) for b in q2}
    print(f'  r={r}: A={ratios["A"]:.3f} B={ratios["B"]:.3f} C={ratios["C"]:.3f} D={ratios["D"]:.3f}')
