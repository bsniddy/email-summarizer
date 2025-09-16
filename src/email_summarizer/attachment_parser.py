import io
import csv
from typing import List, Tuple, Optional
import chardet
import pypdf
import docx2txt
from bs4 import BeautifulSoup


def parse_attachment(filename: str, content: bytes, mime_type: str) -> Optional[str]:
    """Parse attachment content into text based on file type.
    
    Returns None if parsing fails or content is not text-extractable.
    """
    if not content:
        return None
    
    # Try to detect encoding for text files
    if mime_type.startswith('text/') or filename.lower().endswith(('.txt', '.csv', '.html', '.htm')):
        try:
            # Detect encoding
            detected = chardet.detect(content)
            encoding = detected.get('encoding', 'utf-8')
            if not encoding:
                encoding = 'utf-8'
            
            text = content.decode(encoding, errors='ignore')
            
            # Special handling for HTML
            if mime_type.startswith('text/html') or filename.lower().endswith(('.html', '.htm')):
                soup = BeautifulSoup(text, 'html.parser')
                return soup.get_text(separator=' ', strip=True)
            
            # Special handling for CSV
            if mime_type == 'text/csv' or filename.lower().endswith('.csv'):
                try:
                    csv_reader = csv.reader(io.StringIO(text))
                    rows = list(csv_reader)
                    if rows:
                        # Convert to readable format
                        csv_text = '\n'.join([', '.join(row) for row in rows])
                        return f"CSV Data:\n{csv_text}"
                except Exception:
                    pass
            
            return text.strip()
        except Exception:
            return None
    
    # PDF parsing
    elif mime_type == 'application/pdf' or filename.lower().endswith('.pdf'):
        try:
            pdf_file = io.BytesIO(content)
            pdf_reader = pypdf.PdfReader(pdf_file)
            text_parts = []
            for page in pdf_reader.pages:
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_parts.append(page_text.strip())
                except Exception:
                    continue
            if text_parts:
                return '\n\n'.join(text_parts)
        except Exception:
            pass
    
    # DOCX parsing
    elif (mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' or 
          filename.lower().endswith('.docx')):
        try:
            docx_file = io.BytesIO(content)
            text = docx2txt.process(docx_file)
            if text and text.strip():
                return text.strip()
        except Exception:
            pass
    
    return None


def parse_all_attachments(attachments: List[Tuple[str, bytes, str]]) -> List[Tuple[str, str]]:
    """Parse all attachments and return list of (filename, parsed_text) tuples.
    
    Only returns attachments that were successfully parsed.
    """
    parsed_attachments = []
    for filename, content, mime_type in attachments:
        parsed_text = parse_attachment(filename, content, mime_type)
        if parsed_text:
            parsed_attachments.append((filename, parsed_text))
    return parsed_attachments
