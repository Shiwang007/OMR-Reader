import os
import subprocess

possible_paths = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Users\{}\AppData\Local\Microsoft\Edge\Application\msedge.exe".format(os.getlogin()),
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]

found_path = None
for path in possible_paths:
    if os.path.exists(path):
        found_path = path
        break

if found_path:
    print(f"FOUND: {found_path}")
    try:
        # Test command
        res = subprocess.run([found_path, "--version"], capture_output=True, text=True)
        print(f"VERSION: {res.stdout.strip()}")
    except Exception as e:
        print(f"ERROR: {e}")
else:
    print("No browser executable found for PDF generation.")
