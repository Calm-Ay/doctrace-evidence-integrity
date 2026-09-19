import pikepdf
from doctrace.utils.pdfutils import tokenize_stream
import sys

def main():
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "sample.pdf"
    with pikepdf.Pdf.open(pdf_path) as pdf:
        for page in pdf.pages:
            if isinstance(page.Contents, pikepdf.Array):
                contents = b"".join(stream.read_bytes() for stream in page.Contents)
            else:
                contents = page.Contents.read_bytes()
                
            tokens = tokenize_stream(contents)
            in_array = False
            arrays = []
            current = []
            for t in tokens:
                if t[0] == 'ARRAY_START':
                    in_array = True
                    current = []
                elif t[0] == 'ARRAY_END':
                    in_array = False
                    arrays.append(current)
                elif in_array:
                    current.append(t)
                    
            print(f"Found {len(arrays)} arrays in page.")
            for i, a in enumerate(arrays[:5]):
                print(f"Array {i}: {a}")
                
if __name__ == "__main__":
    main()
