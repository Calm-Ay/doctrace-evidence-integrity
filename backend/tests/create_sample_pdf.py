import fitz

def create_sample(filename="sample.pdf"):
    doc = fitz.open()
    page = doc.new_page()
    # Insert some lines
    lines = [
        "DocTrace is a command-line tool that stamps a unique, invisible",
        "fingerprint into every copy of a document before you hand it out.",
        "This allows you to trace leaks back to the original recipient,",
        "even if the leak is just a photo of a printed page. We are",
        "testing zero-width characters and micro-spacing glyph offsets",
        "in this PDF file.",
        "",
        "To test photo-resistant watermarking, we need a document with",
        "multiple pages or at least multiple lines of text that can serve",
        "as anchor words. Spacing ratio measurements will be calculated",
        "by analyzing the physical layout coordinates of these words",
        "after camera rectification. Let us verify if our pipeline works",
        "end-to-end."
    ]
    
    y = 50
    for line in lines:
        if line:
            page.insert_text((50, y), line, fontsize=11, fontname="helv")
        y += 15
    
    doc.save(filename)
    print(f"Created sample PDF: {filename}")

if __name__ == "__main__":
    create_sample()
