import re
import pymupdf as fitz
from doctrace.stampers.base import BaseStamper

class ZeroWidthStamper(BaseStamper):
    def encode_string(self, bitstring: str) -> str:
        """Encodes the bitstring as a simple metadata tag."""
        return f"[DOCTRACE:{bitstring}]"

    def decode_string(self, text: str) -> str:
        """Decodes the bitstring from the metadata tag."""
        matches = re.findall(r'\[DOCTRACE:([01]+)\]', text)
        if not matches:
            return ""
        return matches[0]

    def stamp(self, input_pdf_path: str, output_pdf_path: str, bitstring: str) -> bool:
        """Stamps the PDF by inserting invisible text on each page."""
        try:
            doc = fitz.open(input_pdf_path)
            encoded_str = self.encode_string(bitstring)
            
            for page in doc:
                # Text rendering mode 3 means "Neither fill nor stroke text" (invisible text)
                page.insert_text(
                    (10, 10), 
                    encoded_str, 
                    fontname="helv", 
                    fontsize=4, 
                    render_mode=3
                )
            
            # Save incremental is not used to ensure we write a clean stream
            doc.save(output_pdf_path, clean=True)
            doc.close()
            return True
        except Exception as e:
            print(f"Error in ZeroWidthStamper.stamp: {e}")
            return False

    def extract(self, pdf_path: str) -> str:
        """Extracts zero-width characters from the text layer of the PDF."""
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text = page.get_text("text")
                bitstring = self.decode_string(text)
                if bitstring:
                    doc.close()
                    return bitstring
            doc.close()
            return ""
        except Exception as e:
            print(f"Error in ZeroWidthStamper.extract: {e}")
            return ""
