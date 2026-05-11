"""
PDF Handling and Text Chunking Service (Uses PyMuPDF).
Handles reading text from PDF files and dividing them into manageable chunks.
"""
import fitz  # PyMuPDF
from typing import List

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts all text content from a given PDF file path.
    Uses PyMuPDF (fitz).
    
    Args:
        file_path: The absolute or relative path to the PDF file.

    Returns:
        The aggregated text content of the document.
    """
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF {file_path}: {e}")
        return ""


def chunk_text(text: str, chunk_size: int = 500) -> List[str]:
    """
    Splits a large string of text into smaller, overlapping chunks.

    Args:
        text: The full text content to be chunked.
        chunk_size: The maximum size of each resulting chunk.

    Returns:
        A list of text chunks (strings).
    """
    if not text:
        return []

    # Basic fixed-size chunking as per requirement
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    return chunks


if __name__ == '__main__':
    # Example usage (requires a dummy PDF file to exist)
    print("--- Testing PDF Service ---")
    # Note: For real testing, replace 'dummy.pdf' with an actual path.
    # try:
    #     dummy_text = extract_text_from_pdf("path/to/your/document.pdf")
    #     chunks = chunk_text(dummy_text)
    #     print(f"Extracted text length: {len(dummy_text)}")
    #     print(f"Generated {len(chunks)} chunks.")
    # except FileNotFoundError:
    #     print("Test skipped: PDF file not found.")
    pass