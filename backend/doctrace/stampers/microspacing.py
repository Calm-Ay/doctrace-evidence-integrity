import re
import pikepdf
from typing import List, Tuple, Dict, Any, Optional

from doctrace.stampers.base import BaseStamper
from doctrace.utils.pdfutils import tokenize_stream, tokens_to_bytes

DEFAULT_SPACE_WIDTH = -275.0

def split_literal_string(s_bytes: bytes) -> List[Tuple[str, bytes]]:
    """
    Splits a literal string b'(content)' at space characters.
    Returns a list of ('TEXT', bytes) and ('SPACE', b' ') tuples.
    """
    content = s_bytes[1:-1]
    parts = []
    curr = bytearray()
    i = 0
    n = len(content)
    while i < n:
        if content[i:i+1] == b'\\':
            # Copy escape sequence character
            curr.extend(content[i:i+2])
            i += 2
        elif content[i:i+1] == b' ':
            if curr:
                parts.append(('TEXT', bytes(curr)))
            parts.append(('SPACE', b' '))
            curr = bytearray()
            i += 1
        else:
            curr.extend(content[i:i+1])
            i += 1
    if curr:
        parts.append(('TEXT', bytes(curr)))
    return parts

def split_hex_string(h_bytes: bytes) -> List[Tuple[str, bytes]]:
    """
    Splits a hex string b'<hex>' at space characters (0020 for UTF-16BE or 20 for simple).
    Returns a list of ('TEXT-HEX', bytes) and ('SPACE', space_hex_bytes) tuples.
    """
    hex_content = h_bytes[1:-1]
    hex_content = b''.join(hex_content.split())  # Clean formatting whitespace
    parts = []
    
    n = len(hex_content)
    is_utf16 = False
    if n % 4 == 0:
        for j in range(0, n, 4):
            if hex_content[j:j+4].upper() == b'0020':
                is_utf16 = True
                break
                
    glyph_size = 4 if is_utf16 else 2
    space_hex = b'0020' if is_utf16 else b'20'
    
    curr = bytearray()
    for j in range(0, n, glyph_size):
        glyph = hex_content[j:j+glyph_size]
        if glyph.upper() == space_hex.upper():
            if curr:
                parts.append(('TEXT-HEX', bytes(curr)))
            parts.append(('SPACE', space_hex))
            curr = bytearray()
        else:
            curr.extend(glyph)
    if curr:
        parts.append(('TEXT-HEX', bytes(curr)))
    return parts

class MicroSpacingStamper(BaseStamper):
    def _process_tokens(self, tokens: List[Tuple[str, bytes]], bitstring: str, space_counter: int, stamp_mode: bool) -> Tuple[List[Tuple[str, bytes]], int, List[str]]:
        """
        Processes stream tokens to either stamp bits (if stamp_mode=True) or extract bits.
        Returns the modified tokens (or original tokens), the updated space_counter, and extracted bits list.
        """
        new_tokens = []
        extracted_bits = []
        i = 0
        n = len(tokens)
        
        while i < n:
            t_type, t_bytes = tokens[i]
            
            # Case 1: [ ... ] TJ operator
            if t_type == 'ARRAY_START':
                # Parse array tokens until ARRAY_END
                array_tokens = []
                i += 1
                while i < n and tokens[i][0] != 'ARRAY_END':
                    array_tokens.append(tokens[i])
                    i += 1
                
                # Check if it is followed by TJ
                is_tj = False
                if i + 1 < n and tokens[i+1][1] == b'TJ':
                    is_tj = True
                
                if is_tj:
                    new_array_tokens = []
                    for at_type, at_bytes in array_tokens:
                        # If it is a string inside TJ, search for spaces inside it
                        if at_type in ('STRING', 'HEX_STRING'):
                            parts = split_literal_string(at_bytes) if at_type == 'STRING' else split_hex_string(at_bytes)
                            
                            # Reconstruct array elements, turning space into TJ displacement
                            for p_type, p_bytes in parts:
                                if p_type == 'SPACE':
                                    # We found a space location!
                                    if stamp_mode:
                                        if space_counter < len(bitstring):
                                            bit = bitstring[space_counter]
                                            disp = -270 if bit == '0' else -280
                                            new_array_tokens.append(('OTHER', f"{disp}".encode('ascii')))
                                            space_counter += 1
                                        else:
                                            # No more bits, write standard space displacement
                                            new_array_tokens.append(('OTHER', b'-275'))
                                    else:
                                        # Decode mode: space character in string does not have modulation
                                        # But let's keep space_counter aligned
                                        space_counter += 1
                                else:
                                    # Normal text part
                                    if at_type == 'STRING':
                                        new_array_tokens.append(('STRING', b'(' + p_bytes + b')'))
                                    else:
                                        new_array_tokens.append(('HEX_STRING', b'<' + p_bytes + b'>'))
                        elif at_type == 'OTHER':
                            # Check if this token is a number representing displacement
                            try:
                                val = float(at_bytes)
                                # Spacing adjustments are usually negative and in range [-400, -150]
                                if -400 <= val <= -150:
                                    if stamp_mode:
                                        if space_counter < len(bitstring):
                                            bit = bitstring[space_counter]
                                            modulated = -270 if bit == '0' else -280
                                            new_array_tokens.append(('OTHER', f"{modulated}".encode('ascii')))
                                            space_counter += 1
                                        else:
                                            new_array_tokens.append(('OTHER', at_bytes))
                                    else:
                                        # Decode mode: check absolute distance to -270 and -280
                                        if abs(val - (-270)) <= 2.0:
                                            extracted_bits.append('0')
                                            space_counter += 1
                                        elif abs(val - (-280)) <= 2.0:
                                            extracted_bits.append('1')
                                            space_counter += 1
                                        else:
                                            # Not modulated
                                            pass
                                        new_array_tokens.append(('OTHER', at_bytes))
                                else:
                                    new_array_tokens.append(('OTHER', at_bytes))
                            except ValueError:
                                new_array_tokens.append(('OTHER', at_bytes))
                        else:
                            new_array_tokens.append((at_type, at_bytes))
                    
                    new_tokens.append(('ARRAY_START', b'['))
                    new_tokens.extend(new_array_tokens)
                    new_tokens.append(('ARRAY_END', b']'))
                    new_tokens.append(tokens[i+1])  # TJ operator
                    i += 2
                    continue
                else:
                    # Not a TJ, just restore the array
                    new_tokens.append(('ARRAY_START', b'['))
                    new_tokens.extend(array_tokens)
                    new_tokens.append(('ARRAY_END', b']'))
                    # i is at ARRAY_END, increment to process next token
                    i += 1
                    continue
            
            # Case 2: ( ... ) Tj operator
            elif t_type in ('STRING', 'HEX_STRING') and i + 1 < n and tokens[i+1][1] == b'Tj':
                # Convert Tj to TJ to support displacement insertion
                parts = split_literal_string(t_bytes) if t_type == 'STRING' else split_hex_string(t_bytes)
                
                # Check if it has spaces
                has_spaces = any(p_type == 'SPACE' for p_type, _ in parts)
                
                if has_spaces:
                    new_array_tokens = []
                    for p_type, p_bytes in parts:
                        if p_type == 'SPACE':
                            if stamp_mode:
                                if space_counter < len(bitstring):
                                    bit = bitstring[space_counter]
                                    disp = -275.1 if bit == '0' else -275.2
                                    new_array_tokens.append(('OTHER', f"{disp}".encode('ascii')))
                                    space_counter += 1
                                else:
                                    new_array_tokens.append(('OTHER', b'-275'))
                            else:
                                space_counter += 1
                        else:
                            if t_type == 'STRING':
                                new_array_tokens.append(('STRING', b'(' + p_bytes + b')'))
                            else:
                                new_array_tokens.append(('HEX_STRING', b'<' + p_bytes + b'>'))
                                
                    new_tokens.append(('ARRAY_START', b'['))
                    new_tokens.extend(new_array_tokens)
                    new_tokens.append(('ARRAY_END', b']'))
                    new_tokens.append(('OTHER', b'TJ'))
                else:
                    new_tokens.append((t_type, t_bytes))
                    new_tokens.append(tokens[i+1])
                i += 2
                continue
            
            else:
                new_tokens.append((t_type, t_bytes))
                i += 1
                
        return new_tokens, space_counter, extracted_bits

    def stamp(self, input_pdf_path: str, output_pdf_path: str, bitstring: str) -> bool:
        """Stamps the PDF using glyph micro-spacing modulation."""
        try:
            with pikepdf.Pdf.open(input_pdf_path) as pdf:
                space_counter = 0
                for page in pdf.pages:
                    # Decompress and read content stream
                    if isinstance(page.Contents, pikepdf.Array):
                        contents = b"".join(stream.read_bytes() for stream in page.Contents)
                    else:
                        contents = page.Contents.read_bytes()
                        
                    tokens = tokenize_stream(contents)
                    
                    # Modulate spaces in stream tokens
                    new_tokens, space_counter, _ = self._process_tokens(tokens, bitstring, space_counter, stamp_mode=True)
                    
                    # Write modified content stream back
                    new_contents = tokens_to_bytes(new_tokens)
                    page.Contents = pdf.make_stream(new_contents)
                    
                # Save the updated PDF
                pdf.save(output_pdf_path)
            return True
        except Exception as e:
            print(f"Error in MicroSpacingStamper.stamp: {e}")
            return False

    def extract(self, pdf_path: str) -> str:
        """Extracts micro-spacing bits from the PDF's content streams."""
        try:
            with pikepdf.Pdf.open(pdf_path) as pdf:
                space_counter = 0
                all_extracted_bits = []
                for page in pdf.pages:
                    if isinstance(page.Contents, pikepdf.Array):
                        contents = b"".join(stream.read_bytes() for stream in page.Contents)
                    else:
                        contents = page.Contents.read_bytes()
                        
                    tokens = tokenize_stream(contents)
                    _, space_counter, extracted_bits = self._process_tokens(tokens, "", space_counter, stamp_mode=False)
                    all_extracted_bits.extend(extracted_bits)
                
                return "".join(all_extracted_bits)
        except Exception as e:
            print(f"Error in MicroSpacingStamper.extract: {e}")
            return ""
