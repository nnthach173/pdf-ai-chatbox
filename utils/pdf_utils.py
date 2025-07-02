import fitz  # PyMuPDF

def extract_text_from_pdf(uploaded_file):
    text = ""
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    print("📄 Total pages:", len(doc))

    for i, page in enumerate(doc):
        page_text = page.get_text()
        print(f"📄 Page {i + 1} length:", len(page_text or ""))
        text += page_text or ""

    print("📄 Total text length:", len(text))
    return text