import os
import subprocess
import fitz

def run_cmd(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Command failed:\n{result.stderr}")
    else:
        print(result.stdout)
    return result.returncode == 0

def main():
    # 0. Setup
    original_pdf = "sample.pdf"
    recipients_csv = "tests/recipients.csv"
    out_dir = "tests/stamped"
    db_path = "tests/doctrace.db"
    
    # Clean previous runs
    os.makedirs(out_dir, exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print("=== Step 0: Generating sample PDF ===")
    run_cmd(".venv/bin/python3 tests/create_sample_pdf.py")
    
    # 1. Stamp
    print("\n=== Step 1: Stamping original PDF ===")
    stamp_cmd = f".venv/bin/doctrace stamp {original_pdf} -r {recipients_csv} -o {out_dir} --db {db_path} --bits 32"
    if not run_cmd(stamp_cmd):
        return
        
    stamped_pdf = os.path.join(out_dir, "recipient_001.pdf")
    if not os.path.exists(stamped_pdf):
        print(f"Error: {stamped_pdf} was not created.")
        return

    # 2. Verify Exact Same File
    print("\n=== Step 2: Verifying exact same file ===")
    run_cmd(f".venv/bin/doctrace verify {stamped_pdf} --db {db_path}")
    
    # 3. Verify PyMuPDF re-save
    print("\n=== Step 3: Verifying PyMuPDF re-save ===")
    pymupdf_pdf = os.path.join(out_dir, "recipient_001_pymupdf.pdf")
    doc = fitz.open(stamped_pdf)
    doc.save(pymupdf_pdf, clean=True)
    doc.close()
    run_cmd(f".venv/bin/doctrace verify {pymupdf_pdf} --db {db_path}")

    # 4. Verify Ghostscript "print to PDF"
    print("\n=== Step 4: Verifying Ghostscript print to PDF ===")
    gs_pdf = os.path.join(out_dir, "recipient_001_gs.pdf")
    gs_cmd = f"gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dNOPAUSE -dQUIET -dBATCH -sOutputFile={gs_pdf} {stamped_pdf}"
    if run_cmd(gs_cmd):
        run_cmd(f".venv/bin/doctrace verify {gs_pdf} --db {db_path}")
    else:
        print("Ghostscript command failed. Ensure ghostscript is installed.")

if __name__ == "__main__":
    main()
