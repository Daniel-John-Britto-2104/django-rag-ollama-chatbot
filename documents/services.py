import fitz  # PyMuPDF


def extract_text(uploaded_file):
    """
    Extract text from an uploaded PDF file.
    """

    # Check if the uploaded file is a PDF
    if not uploaded_file.name.lower().endswith(".pdf"):
        raise ValueError("Only PDF files are supported.")

    # Read the uploaded file into bytes
    pdf_bytes = uploaded_file.read()

    # Check if the file is empty
    if not pdf_bytes:
        raise ValueError("The uploaded PDF is empty.")

    try:
        # Open PDF from memory
        pdf = fitz.open(stream=pdf_bytes, filetype="pdf")

        text = ""

        # Extract text from each page
        for page in pdf:
            text += page.get_text()

        pdf.close()

        return text

    except Exception as e:
        raise ValueError(f"Invalid or corrupted PDF file: {e}")