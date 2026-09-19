import os
import cv2
import json
import fitz
import numpy as np

from doctrace.stampers.microspacing import MicroSpacingStamper
from doctrace.stampers.structural import StructuralStamper
from doctrace.extractors.photo_extract import extract_from_photo

# Mock find_best_matches to calculate confidence
def calculate_confidence(extracted: str, original: str) -> float:
    if len(extracted) != len(original):
        return 0.0
    errors = sum(1 for e, o in zip(extracted, original) if e != o)
    return max(0.0, ((len(original) - errors) / len(original)) * 100)

def add_perspective(image, severity=0.08):
    h, w = image.shape[:2]
    pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
    dw = w * severity
    dh = h * severity
    pts2 = np.float32([[dw, dh], [w - dw, dh], [-dw, h - dh], [w + dw, h - dh]])
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    return cv2.warpPerspective(image, matrix, (w, h), borderValue=(255, 255, 255))

def add_lighting(image):
    h, w = image.shape[:2]
    gradient = np.linspace(0.6, 1.0, w)
    gradient = np.tile(gradient, (h, 1))
    gradient = np.stack([gradient]*3, axis=2)
    img_float = image.astype(np.float32) * gradient
    return np.clip(img_float, 0, 255).astype(np.uint8)

def add_blur_and_noise(image):
    img = cv2.GaussianBlur(image, (5, 5), 0)
    noise = np.random.normal(0, 15, img.shape).astype(np.float32)
    img_float = img.astype(np.float32) + noise
    return np.clip(img_float, 0, 255).astype(np.uint8)

def main():
    out_dir = "tests/out_sweep"
    os.makedirs(out_dir, exist_ok=True)
    
    # Pre-normalize
    ms_stamper = MicroSpacingStamper()
    norm_pdf = os.path.join(out_dir, "normalized.pdf")
    if not ms_stamper.stamp("sample.pdf", norm_pdf, ""):
        print("Failed to normalize.")
        return
        
    shifts = [50, 75, 100, 125, 150, 200]
    bitstring = "10101010101010101010101010101010"
    
    print("=== Phase 5: Shift Amount Sweep ===")
    
    for shift in shifts:
        print(f"\n=========================================")
        print(f"Testing shift_amount = {shift} (approx {shift/100:.2f}pt)")
        print(f"=========================================")
        
        struct_stamper = StructuralStamper(shift_amount=shift)
        layout_map_json = struct_stamper.generate_layout_map(norm_pdf, 32)
        if not layout_map_json:
            print("Failed to generate layout map.")
            continue
            
        layout_map = json.loads(layout_map_json)
        bits = layout_map.get('actual_bits', 32)
        target_bits = bitstring[:bits]
        
        out_pdf = os.path.join(out_dir, f"stamped_{shift}.pdf")
        struct_stamper.stamp_with_map(norm_pdf, out_pdf, target_bits, layout_map_json)
        
        doc = fitz.open(out_pdf)
        pix = doc[0].get_pixmap(dpi=150)
        img_path = os.path.join(out_dir, f"clean_{shift}.jpg")
        pix.save(img_path)
        doc.close()
        
        base_img = cv2.imread(img_path)
        
        # Pass 1: Clean (Keystone + Lighting only)
        img_clean = add_perspective(base_img.copy(), severity=0.06)
        img_clean = add_lighting(img_clean)
        
        clean_path = os.path.join(out_dir, f"clean_test_{shift}.jpg")
        cv2.imwrite(clean_path, img_clean)
        
        extracted_clean = extract_from_photo(clean_path, layout_map_json, bits)
        conf_clean = calculate_confidence(extracted_clean, target_bits)
        
        print(f"PASS 1 (Clean): Confidence: {conf_clean:.1f}%")
        print(f"  Target:    {target_bits}")
        print(f"  Extracted: {extracted_clean}")
        
        # Pass 2: Noisy (Keystone + Lighting + Blur + Sensor Noise)
        img_noisy = add_perspective(base_img.copy(), severity=0.08)
        img_noisy = add_lighting(img_noisy)
        img_noisy = add_blur_and_noise(img_noisy)
        
        noisy_path = os.path.join(out_dir, f"noisy_test_{shift}.jpg")
        cv2.imwrite(noisy_path, img_noisy)
        
        extracted_noisy = extract_from_photo(noisy_path, layout_map_json, bits)
        conf_noisy = calculate_confidence(extracted_noisy, target_bits)
        
        print(f"\nPASS 2 (Noisy): Confidence: {conf_noisy:.1f}%")
        print(f"  Target:    {target_bits}")
        print(f"  Extracted: {extracted_noisy}")

if __name__ == "__main__":
    main()
