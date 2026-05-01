import os
import shutil

def cleanup_workspace():
    root = r"f:\Medjeex\Medjeex-OMR-Engine"
    archive_dir = os.path.join(root, "archive", "scripts")
    assets_dir = os.path.join(root, "assets")
    
    if not os.path.exists(archive_dir): os.makedirs(archive_dir)
    if not os.path.exists(assets_dir): os.makedirs(assets_dir)
    
    # Files to keep in root
    keep_root = [
        "scan_neet_batch.py",
        "scan_jee_batch.py",
        "requirements.txt",
        "README.md",
        "REPORT_GENERATION_GUIDE.md",
        ".gitignore"
    ]
    
    # Files to move to assets
    to_assets = [
        "Medjeex_Logo.png",
        "All_Students_Scorecards.pdf"
    ]
    
    for item in os.listdir(root):
        item_path = os.path.join(root, item)
        
        # Only process files in the root (ignore directories)
        if os.path.isfile(item_path):
            if item in keep_root:
                continue
            elif item in to_assets:
                shutil.move(item_path, os.path.join(assets_dir, item))
                print(f"Moved to assets: {item}")
            else:
                shutil.move(item_path, os.path.join(archive_dir, item))
                print(f"Archived: {item}")

if __name__ == "__main__":
    cleanup_workspace()
