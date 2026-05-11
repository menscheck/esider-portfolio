import os
import json
import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path):
    """Extract text from all pages of a PDF."""
    doc = fitz.open(pdf_path)
    pages_text = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        pages_text.append(text)
    doc.close()
    return pages_text

def chunk_text(text, chunk_size=500, overlap=50):
    """Split text into chunks with overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
        if start >= len(text):
            break
    return chunks

def process_pdf(pdf_path, base_dir):
    """Process a single PDF: extract text, chunk it, and return data."""
    # Extract company name from filename (assuming format: {company}_ESG_2024.pdf)
    filename = os.path.basename(pdf_path)
    if not filename.endswith('_ESG_2024.pdf'):
        return None
    company = filename.replace('_ESG_2024.pdf', '')

    # Extract text from all pages
    pages_text = extract_text_from_pdf(pdf_path)

    # Prepare output data
    chunks_data = []
    total_chunks = 0

    for page_num, page_text in enumerate(pages_text, start=1):
        # Chunk the page text
        chunks = chunk_text(page_text, chunk_size=500, overlap=50)
        for chunk_idx, chunk in enumerate(chunks, start=1):
            chunk_id = f"{company}_p{page_num}_c{chunk_idx}"
            chunk_data = {
                "company": company,
                "source": filename,
                "page": page_num,
                "chunk_id": chunk_id,
                "text": chunk
            }
            chunks_data.append(chunk_data)
            total_chunks += 1

    return company, pages_text, chunks_data, total_chunks

def main():
    base_dir = r"C:\Users\Sam Joseph\esg-agent"
    reports_dir = os.path.join(base_dir, "data", "reports")
    chunks_dir = os.path.join(base_dir, "data", "chunks")

    # Ensure chunks directory exists
    os.makedirs(chunks_dir, exist_ok=True)

    # Find all *_ESG_2024.pdf files recursively
    pdf_files = []
    for root, dirs, files in os.walk(reports_dir):
        for file in files:
            if file.endswith('_ESG_2024.pdf'):
                pdf_files.append(os.path.join(root, file))

    # Process all PDFs
    success_count = 0
    fail_count = 0
    total_chunks = 0
    company_chunks = {}

    for pdf_path in pdf_files:
        result = process_pdf(pdf_path, base_dir)
        if result:
            company, pages_text, chunks_data, chunks_count = result
            success_count += 1
            total_chunks += chunks_count
            company_chunks[company] = chunks_count

            # Save to JSON
            output_path = os.path.join(chunks_dir, f"{company}.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(chunks_data, f, ensure_ascii=False, indent=2)
        else:
            fail_count += 1

    # Print statistics
    print(f"成功幾家: {success_count}")
    print(f"失敗幾家: {fail_count}")
    print(f"總 chunk 數: {total_chunks}")
    print("各公司 chunk 數:")
    for company, chunks in company_chunks.items():
        print(f"  {company}: {chunks} chunks")

if __name__ == "__main__":
    main()