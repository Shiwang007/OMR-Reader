import cv2, numpy as np, json

img = cv2.imread(r'f:\Medjeex\Medjeex-OMR-Engine\output\mock_filled_img4.jpg')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 51, 15)
t = json.load(open(r'f:\Medjeex\Medjeex-OMR-Engine\output\img4_template.json'))

def fill_ratio(x, y, r=9):
    mask = np.zeros(binary.shape, np.uint8)
    cv2.circle(mask, (int(x), int(y)), r, 255, -1)
    total = cv2.countNonZero(mask)
    dark = cv2.countNonZero(cv2.bitwise_and(binary, binary, mask=mask))
    return dark / max(total, 1)

# Q17 decimal
q17 = t['questions']['17']['bubbles']
dec = [b for b in q17 if b['opt'] == 'decimal']
print('Q17 decimal:', dec)
if dec:
    print(f'  fill ratio: {fill_ratio(dec[0]["x"], dec[0]["y"]):.3f}')
    for r in [6,7,8,9,10,11,12]:
        print(f'  r={r}: ratio={fill_ratio(dec[0]["x"], dec[0]["y"], r):.3f}')

# Q37 D bubble
q37 = t['questions']['37']['bubbles']
for b in q37:
    r = fill_ratio(b['x'], b['y'])
    print(f'Q37 {b["opt"]} at ({int(b["x"])},{int(b["y"])}): {r:.3f}')

# Q46 col 0 (digit 9 = val_i=9)
q46 = t['questions']['46']['bubbles']
col0_v9 = [b for b in q46 if b['opt'] == '0_9']
print('\nQ46 col0 val9:', col0_v9)
if col0_v9:
    print(f'  fill ratio: {fill_ratio(col0_v9[0]["x"], col0_v9[0]["y"]):.3f}')

# Show what Q46 col0 val0 looks like (template starting row)
col0_v0 = [b for b in q46 if b['opt'] == '0_0']
print('Q46 col0 val0:', col0_v0)
if col0_v0:
    print(f'  fill ratio: {fill_ratio(col0_v0[0]["x"], col0_v0[0]["y"]):.3f}')
