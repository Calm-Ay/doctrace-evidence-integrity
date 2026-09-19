import json
import pikepdf
from typing import List, Tuple, Dict
from doctrace.stampers.base import BaseStamper
from doctrace.utils.pdfutils import tokenize_stream, tokens_to_bytes

COMMON_WORDS = {"the", "and", "of", "to", "in", "a", "is", "for", "on", "it", "with", "as", "by", "that"}

class StructuralStamper(BaseStamper):
    def __init__(self, shift_amount: int = 50):
        # 50 units in 1000-unit text space is about 0.5pt for a 10pt font.
        # This is enough to be measurable by OCR on high-res photos but visually subtle.
        self.shift_amount = shift_amount

    def _clean_word(self, word_bytes: bytes) -> str:
        # Check if it's a hex string (e.g., b'<446f...>')
        if word_bytes.startswith(b'<') and word_bytes.endswith(b'>'):
            try:
                hex_content = word_bytes[1:-1].decode('ascii', errors='ignore')
                # decode hex pairs to bytes
                decoded_bytes = bytes.fromhex(hex_content)
                w = decoded_bytes.decode('utf-8', errors='ignore').lower()
                return ''.join(c for c in w if c.isalpha())
            except:
                pass
        
        # Otherwise, treat as regular string (e.g., b'(Word)')
        try:
            if word_bytes.startswith(b'(') and word_bytes.endswith(b')'):
                w = word_bytes[1:-1].decode('utf-8', errors='ignore').lower()
            else:
                w = word_bytes.decode('utf-8', errors='ignore').lower()
            return ''.join(c for c in w if c.isalpha())
        except:
            return ""

    def _score_triplet(self, w1: bytes, w2: bytes, w3: bytes) -> int:
        score = 0
        for w in [w1, w2, w3]:
            cw = self._clean_word(w)
            if cw in COMMON_WORDS:
                score += 5
            elif len(cw) <= 5 and cw:
                score += 2
            elif len(cw) > 8:
                score -= 1 # Penalize very long words
        return score

    def generate_layout_map(self, input_pdf_path: str, num_bits: int) -> str:
        """Finds anchor triplets in the original PDF and returns a JSON layout map."""
        with pikepdf.Pdf.open(input_pdf_path) as pdf:
            all_candidates = []
            
            for page_idx, page in enumerate(pdf.pages):
                if isinstance(page.Contents, pikepdf.Array):
                    contents = b"".join(stream.read_bytes() for stream in page.Contents)
                else:
                    contents = page.Contents.read_bytes()
                    
                tokens = tokenize_stream(contents)
                
                in_array = False
                for i in range(len(tokens) - 4):
                    if tokens[i][0] == 'ARRAY_START':
                        in_array = True
                    elif tokens[i][0] == 'ARRAY_END':
                        in_array = False
                        
                    if in_array:
                        t1, t2, t3, t4, t5 = tokens[i], tokens[i+1], tokens[i+2], tokens[i+3], tokens[i+4]
                        if (t1[0] in ('STRING', 'HEX_STRING') and 
                            t2[0] == 'OTHER' and 
                            t3[0] in ('STRING', 'HEX_STRING') and 
                            t4[0] == 'OTHER' and 
                            t5[0] in ('STRING', 'HEX_STRING')):
                            
                            try:
                                v1 = float(t2[1])
                                v2 = float(t4[1])
                                if v1 < 0 and v2 < 0:
                                    if i < 100:
                                        continue
                                        
                                    score = self._score_triplet(t1[1], t3[1], t5[1])
                                    all_candidates.append({
                                        'page': page_idx,
                                        'idx': i,
                                        'score': score,
                                        'w1': t1[1].decode('ascii', errors='ignore'),
                                        'w2': t3[1].decode('ascii', errors='ignore'),
                                        'w3': t5[1].decode('ascii', errors='ignore'),
                                        'orig_v1': v1,
                                        'orig_v2': v2
                                    })
                            except ValueError:
                                pass

            all_candidates.sort(key=lambda x: (-x['score'], x['page'], x['idx']))
            
            actual_bits = num_bits
            if len(all_candidates) < num_bits:
                actual_bits = len(all_candidates)
                
            selected_anchors = all_candidates[:actual_bits]
            selected_anchors.sort(key=lambda x: (x['page'], x['idx']))
            
            layout_map = {
                'version': 1,
                'requested_bits': num_bits,
                'actual_bits': actual_bits,
                'anchors': []
            }
            
            for bit_idx, anchor in enumerate(selected_anchors):
                layout_map['anchors'].append({
                    'bit_idx': bit_idx,
                    'page': anchor['page'],
                    'idx': anchor['idx'],
                    'words': [self._clean_word(anchor['w1'].encode()), 
                              self._clean_word(anchor['w2'].encode()), 
                              self._clean_word(anchor['w3'].encode())],
                    'orig_v1': anchor['orig_v1'],
                    'orig_v2': anchor['orig_v2']
                })
                
            return json.dumps(layout_map)

    def stamp_with_map(self, input_pdf_path: str, output_pdf_path: str, bitstring: str, layout_map_json: str) -> bool:
        """Stamps the PDF using a pre-computed layout map."""
        try:
            layout_map = json.loads(layout_map_json)
            with pikepdf.Pdf.open(input_pdf_path) as pdf:
                page_tokens = []
                for page in pdf.pages:
                    if isinstance(page.Contents, pikepdf.Array):
                        contents = b"".join(stream.read_bytes() for stream in page.Contents)
                    else:
                        contents = page.Contents.read_bytes()
                    page_tokens.append(tokenize_stream(contents))
                
                for anchor in layout_map['anchors']:
                    bit_idx = anchor['bit_idx']
                    if bit_idx >= len(bitstring):
                        continue
                        
                    page_idx = anchor['page']
                    token_idx = anchor['idx']
                    bit = bitstring[bit_idx]
                    
                    tokens = page_tokens[page_idx]
                    
                    v1 = anchor['orig_v1']
                    v2 = anchor['orig_v2']
                    
                    if bit == '0':
                        new_v1 = v1 - self.shift_amount
                        new_v2 = v2 + self.shift_amount
                    else:
                        new_v1 = v1 + self.shift_amount
                        new_v2 = v2 - self.shift_amount
                        
                    tokens[token_idx+1] = ('OTHER', f"{int(round(new_v1))}".encode('ascii'))
                    tokens[token_idx+3] = ('OTHER', f"{int(round(new_v2))}".encode('ascii'))
                    
                for page_idx, page in enumerate(pdf.pages):
                    new_contents = tokens_to_bytes(page_tokens[page_idx])
                    page.Contents = pdf.make_stream(new_contents)
                    
                pdf.save(output_pdf_path)
                return True
        except Exception as e:
            print(f"Error in StructuralStamper.stamp_with_map: {e}")
            return False

    def stamp(self, input_pdf_path: str, output_pdf_path: str, bitstring: str) -> bool:
        """Legacy interface for BaseStamper. Generates a map on the fly."""
        layout_map = self.generate_layout_map(input_pdf_path, len(bitstring))
        if not layout_map:
            return False
        return self.stamp_with_map(input_pdf_path, output_pdf_path, bitstring, layout_map)

    def extract(self, pdf_path: str) -> str:
        """Layer 2 extraction is not supported natively via BaseStamper interface."""
        return ""
