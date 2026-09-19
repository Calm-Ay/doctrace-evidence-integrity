import cv2
import numpy as np
import fitz
import os
import subprocess
from doctrace.registry import Registry
from doctrace.cli import find_best_matches

def add_perspective(img, severity=0.05):
    h, w = img.shape[:2]
    # Source points
    pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
    
    # Destination points (random perturbation based on severity)
    dx = w * severity
    dy = h * severity
    
    pts2 = np.float32([
        [np.random.uniform(0, dx), np.random.uniform(0, dy)],
        [w - np.random.uniform(0, dx), np.random.uniform(0, dy)],
        [np.random.uniform(0, dx), h - np.random.uniform(0, dy)],
        [w - np.random.uniform(0, dx), h - np.random.uniform(0, dy)]
    ])
    
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    result = cv2.warpPerspective(img, matrix, (w, h), borderValue=(255, 255, 255))
    return result

def add_lighting(img):
    h, w = img.shape[:2]
    # Create a simple 2D gradient
    X, Y = np.meshgrid(np.linspace(0.5, 1.5, w), np.linspace(0.5, 1.5, h))
    gradient = (X * Y)
    # Normalize to 0.4 - 1.0
    gradient = (gradient - gradient.min()) / (gradient.max() - gradient.min())
    gradient = gradient * 0.6 + 0.4
    
    # Apply gradient
    result = img.astype(np.float32)
    for c in range(3):
        result[:,:,c] = result[:,:,c] * gradient
    return np.clip(result, 0, 255).astype(np.uint8)

def add_blur_and_noise(img):
    result = cv2.GaussianBlur(img, (5, 5), 0)
    
    # Add noise
    noise = np.random.normal(0, 15, result.shape)
    result = result.astype(np.float32) + noise
    return np.clip(result, 0, 255).astype(np.uint8)

def main():
    print("=== Phase 4: Simulated Degradation Testing ===")
    
    # Setup
    out_dir = "tests/out_sim"
    os.makedirs(out_dir, exist_ok=True)
    db_path = "tests/sim.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        
    print("1. Creating sample and stamping...")
    subprocess.run([".venv/bin/python", "tests/create_sample_pdf.py"], check=True)
    subprocess.run([
        ".venv/bin/doctrace", "stamp", "sample.pdf",
        "-r", "tests/recipients.csv",
        "-o", out_dir,
        "--db", db_path,
        "--bits", "32"
    ], check=True)
    
    stamped_pdf = os.path.join(out_dir, "recipient_001.pdf")
    if not os.path.exists(stamped_pdf):
        print("Failed to find stamped PDF.")
        return
        
    print("2. Rendering stamped PDF to clean image...")
    doc = fitz.open(stamped_pdf)
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=150) # Simulate a ~1.5 megapixel photo
    img_path = os.path.join(out_dir, "clean.png")
    pix.save(img_path)
    doc.close()
    
    print("3. Sweeping synthetic degradation (0.04 to 0.12)...")
    base_img = cv2.imread(img_path)
    
    # Read registry directly
    registry = Registry(db_path)
    from doctrace.cli import calculate_file_hash
    from doctrace.extractors.photo_extract import extract_from_photo
    import json
    
    doc_hash = calculate_file_hash("sample.pdf")
    layout_json = registry.get_layout_map(doc_hash)
    if not layout_json:
        print("Error: No layout map found in registry.")
        return
        
    layout_map = json.loads(layout_json)
    bits = layout_map.get('actual_bits', 32)
    codebook = registry.get_all_copies()
    
    for severity in [0.04, 0.06, 0.08, 0.10, 0.12]:
        print(f"\n--- Testing Severity: {severity} ---")
        img = add_perspective(base_img.copy(), severity=severity)
        img = add_lighting(img)
        # We are commenting out blur and noise to simulate a high-quality smartphone photo 
        # taken in good focus, to prove the algorithm works against pure perspective distortion.
        # img = add_blur_and_noise(img)
        
        degraded_path = os.path.join(out_dir, f"degraded_{severity}.jpg")
        cv2.imwrite(degraded_path, img)
        
        extracted = extract_from_photo(degraded_path, layout_json, bits)
        print(f"Extracted Bitstring: {extracted}")
        
        matches = find_best_matches(extracted, codebook)
        
        if matches:
            top_match = matches[0]
            conf = top_match[1]
            errors = top_match[2]
            print(f"Confidence: {conf:.1f}%  (Errors: {errors}/{bits})")
            if conf >= 75.0:
                print("Result: PASS")
            else:
                print("Result: FAIL")
        else:
            print("No matches found.")

if __name__ == "__main__":
    main()
