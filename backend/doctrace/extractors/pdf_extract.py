from doctrace.stampers.zerowidth import ZeroWidthStamper
from doctrace.stampers.microspacing import MicroSpacingStamper

def extract_digital_watermarks(pdf_path: str) -> dict:
    """
    Extracts both Layer 1a (zero-width characters) and Layer 1b (micro-spacing)
    digital watermarks from a PDF file.
    Returns a dictionary with 'zerowidth' and 'microspacing' keys.
    """
    zw_stamper = ZeroWidthStamper()
    ms_stamper = MicroSpacingStamper()
    
    zw_bits = zw_stamper.extract(pdf_path)
    ms_bits = ms_stamper.extract(pdf_path)
    
    return {
        "zerowidth": zw_bits,
        "microspacing": ms_bits
    }
