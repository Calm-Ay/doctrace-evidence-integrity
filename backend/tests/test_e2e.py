import os
import fitz  # PyMuPDF
import subprocess

def main():
    print("Testing E2E CLI Stamp and Identify")
    base_dir = "/home/itchyfeet/.gemini/antigravity/scratch/doctrace"
    original_pdf = os.path.join(base_dir, "sample.pdf")
    recipients = os.path.join(base_dir, "tests/recipients.csv")
    out_dir = os.path.join(base_dir, "tests/out_e2e")
    db_path = os.path.join(base_dir, "tests/e2e.db")
    
    if os.path.exists(db_path):
        os.remove(db_path)
        
    doctrace_bin = os.path.join(base_dir, ".venv/bin/doctrace")
    
    print("Running Stamp...")
    res = subprocess.run([
        doctrace_bin, "stamp", original_pdf,
        "-r", recipients,
        "-o", out_dir,
        "--db", db_path,
        "-b", "16" # 16 bits so it's easier to find anchors in a short sample
    ], cwd=base_dir, capture_output=True, text=True)
    
    print(res.stdout)
    if res.returncode != 0:
        print("Stamp failed:", res.stderr)
        return
        
    # Render recipient_001 to an image
    stamped_pdf = os.path.join(out_dir, "recipient_001.pdf")
    print(f"Rendering {stamped_pdf} to image...")
    doc = fitz.open(stamped_pdf)
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=300)
    img_path = os.path.join(out_dir, "leaked_photo.jpg")
    pix.save(img_path)
    
    print(f"Running Identify on {img_path}...")
    res = subprocess.run([
        doctrace_bin, "identify", img_path,
        "--original", original_pdf,
        "--db", db_path,
        "-b", "16"
    ], cwd=base_dir, capture_output=True, text=True)
    
    print(res.stdout)
    if res.returncode != 0:
        print("Identify failed:", res.stderr)
        return
        
    if "Match Results" in res.stdout and "Alice" in res.stdout:
        print("E2E Test Passed!")
    else:
        print("E2E Test Failed to find Alice.")

if __name__ == "__main__":
    main()
