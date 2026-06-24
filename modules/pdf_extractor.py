import os
import re
import pdfplumber
import PyPDF2
from datetime import datetime

class PDFExtractor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.raw_text = ""
        self.total_pages = 0
        self._extract_raw_text()

    def _extract_raw_text(self):
        """Extracts text using a hybrid approach (pdfplumber -> PyPDF2 fallback)."""
        try:
            with pdfplumber.open(self.file_path) as pdf:
                self.total_pages = len(pdf.pages)
                full_text = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text.append(text)
                self.raw_text = "\n".join(full_text)
        except Exception as e:
            # Fallback to PyPDF2 if layout extraction fails
            print(f"pdfplumber failed, trying PyPDF2: {str(e)}")
            try:
                with open(self.file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    self.total_pages = len(reader.pages)
                    full_text = []
                    for page in reader.pages:
                        text = page.extract_text()
                        if text:
                            full_text.append(text)
                    self.raw_text = "\n".join(full_text)
            except Exception as fallback_error:
                print(f"All PDF text extractors failed: {str(fallback_error)}")
                self.raw_text = ""

    def extract_metadata(self):
        """Parses structure out of raw text using regex heuristics."""
        text = self.raw_text
        
        # Heuristics for Title (Usually the first few non-empty lines)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        title = lines[0] if len(lines) > 0 else "Unknown Title"
        if len(title) < 10 and len(lines) > 1: 
            title = title + " " + lines[1]

        # Extract Abstract
        abstract = "Not Found"
        abstract_match = re.search(r'(?i)(abstract|summary)[:\s\n]+(.*?)(?=\n\s*(1\.?\s+)?(introduction|keywords|key words|background))', text, re.DOTALL)
        if abstract_match:
            abstract = abstract_match.group(2).strip()
        else:
            # Fallback strategy: pick text up to introduction
            intro_match = re.search(r'(?i)\n(introduction)\b', text)
            if intro_match:
                abstract = text[:intro_match.start()].strip()[:1500]

        # Extract Conclusion
        conclusion = "Not Found"
        conclusion_match = re.search(r'(?i)(conclusion|concluding remarks|summary and conclusion)[:\s\n]+(.*?)(?=\n\s*(acknowledgements|references|appendix))', text, re.DOTALL)
        if conclusion_match:
            conclusion = conclusion_match.group(2).strip()

        # Extract Publication Year
        year = None
        year_matches = re.findall(r'\b(19\d{2}|20\d{2})\b', text[:2000]) # Look at header metadata space
        if year_matches:
            # Pick most common or logical year from front matter
            year = int(max(set(year_matches), key=year_matches.count))
        else:
            year = datetime.now().year # Fallback default

        # Extract References
        references = "Not Found"
        ref_match = re.search(r'(?i)\n(references|bibliography|works cited)\n(.*)', text, re.DOTALL)
        if ref_match:
            references = ref_match.group(2).strip()

        # Rough Extraction for Authors
        authors = "Unknown Authors"
        if len(lines) > 1:
            authors = lines[1][:150] # Captures line right below title

        return {
            "title": title[:255],
            "authors": authors,
            "abstract": abstract,
            "publication_year": year,
            "conclusion": conclusion,
            "references": references[:2000], # Slice to fit database constraints cleanly
            "total_pages": self.total_pages,
            "raw_text": text
        }