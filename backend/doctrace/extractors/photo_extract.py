import cv2
import numpy as np
import pytesseract
from pytesseract import Output
import json

def _clean_word(w: str) -> str:
    return ''.join(c for c in w.lower() if c.isalpha())

def deskew_image(img):
    """
    Attempts to find a document contour and apply a perspective transform.
    Falls back to simple rotation if no 4-point contour is found.
    """
    # Resize for faster edge detection and contour finding
    ratio = img.shape[0] / 500.0
    orig = img.copy()
    image = cv2.resize(img, (int(img.shape[1] / ratio), 500))
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(gray, 75, 200)
    
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    
    screenCnt = None
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4 and cv2.contourArea(c) > (img.shape[0]*img.shape[1] * 0.1):
            screenCnt = approx
            break
            
    if screenCnt is not None:
        pts = screenCnt.reshape(4, 2) * ratio
        # Sort points: top-left, top-right, bottom-right, bottom-left
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        
        (tl, tr, br, bl) = rect
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]], dtype="float32")
            
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(orig, M, (maxWidth, maxHeight))
        return warped
    
    # Fallback: Just return original if no clear page boundary found
    return orig

def extract_from_photo(image_path: str, layout_map_json: str, num_bits: int) -> str:
    """
    Extracts Layer 2 physical watermark bits from a photo of a document.
    Uses the pre-computed layout map to find anchor triplets.
    """
    layout_map = json.loads(layout_map_json)
    anchors = layout_map['anchors']
    
    # Sort anchors by bit_idx
    anchors.sort(key=lambda x: x['bit_idx'])
    
    img = cv2.imread(image_path)
    if img is None:
        print(f"Failed to load image: {image_path}")
        return "_" * num_bits
        
    # Restoring deskew but the function will now be safe
    img = deskew_image(img)
    
    # Pre-processing for better OCR
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Denoise to remove sensor noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # More robust adaptive thresholding
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 12)
    
    # DEBUG: Save the thresholded image so the user can see what Tesseract is seeing
    import os
    cv2.imwrite("tests/out_sim/debug_thresh.jpg", thresh)
    
    # Run OCR
    try:
        ocr_data = pytesseract.image_to_data(thresh, output_type=Output.DICT)
    except Exception as e:
        print(f"Tesseract failed: {e}")
        return "_" * num_bits
    
    extracted_bits = ['_'] * num_bits
    
    # Group OCR results by block, paragraph, and line
    lines = {}
    n_boxes = len(ocr_data['level'])
    for i in range(n_boxes):
        text = ocr_data['text'][i].strip()
        if not text:
            continue
            
        b = ocr_data['block_num'][i]
        p = ocr_data['par_num'][i]
        l = ocr_data['line_num'][i]
        
        w = {
            'text': text,
            'clean': _clean_word(text),
            'left': ocr_data['left'][i],
            'width': ocr_data['width'][i],
            'conf': float(ocr_data['conf'][i])
        }
        
        if b not in lines: lines[b] = {}
        if p not in lines[b]: lines[b][p] = {}
        if l not in lines[b][p]: lines[b][p][l] = []
        lines[b][p][l].append(w)
        
    anchors_found_count = 0
    for anchor in anchors:
        bit_idx = anchor['bit_idx']
        w1_target, w2_target, w3_target = anchor['words']
        
        found = False
        for b in lines:
            if found: break
            for p in lines[b]:
                if found: break
                for l in lines[b][p]:
                    line_words = lines[b][p][l]
                    for i in range(len(line_words) - 2):
                        if (line_words[i]['clean'] == w1_target and 
                            line_words[i+1]['clean'] == w2_target and 
                            line_words[i+2]['clean'] == w3_target):
                            
                            w1 = line_words[i]
                            w2 = line_words[i+1]
                            w3 = line_words[i+2]
                            
                            D1 = w2['left'] - (w1['left'] + w1['width'])
                            D2 = w3['left'] - (w2['left'] + w2['width'])
                            
                            # Bit 0 means D1 > D2
                            # Bit 1 means D1 < D2
                            if D1 > D2:
                                extracted_bits[bit_idx] = '0'
                            elif D1 < D2:
                                extracted_bits[bit_idx] = '1'
                            
                            found = True
                            anchors_found_count += 1
                            break
                            
    print(f"DEBUG: Found {anchors_found_count} out of {len(anchors)} anchors in OCR text.")
    if anchors_found_count == 0:
        print("DEBUG: Dumping first few lines of OCR to see why nothing matched:")
        count = 0
        for b in lines:
            for p in lines[b]:
                for l in lines[b][p]:
                    text = " ".join([w['clean'] for w in lines[b][p][l]])
                    print(f"OCR Line: {text}")
                    count += 1
                    if count > 10: break
            if count > 10: break

    return "".join(extracted_bits)
