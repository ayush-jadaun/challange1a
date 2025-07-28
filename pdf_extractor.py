#!/usr/bin/env python3
import os
import json
import fitz  # PyMuPDF
from typing import List, Dict, Tuple


class PDFOutlineExtractor:
    """
    A class to extract structured outlines from PDF documents.
    Identifies document titles and hierarchical headings (H1, H2, H3) based on
    font characteristics and text positioning.
    """
    
    def __init__(self, min_font_size: float = 10.0, min_text_length: int = 3):
        """
        Initialize the PDF outline extractor.
        
        Args:
            min_font_size: Minimum font size to consider for headings
            min_text_length: Minimum text length to consider valid
        """
        self.min_font_size = min_font_size
        self.min_text_length = min_text_length

    def extract_title(self, doc: fitz.Document) -> str:
        """
        Extract the document title from the first page.
        Looks for large, centered text that likely represents the title.
        
        Args:
            doc: PyMuPDF document object
            
        Returns:
            Extracted title as string
        """
        try:
            if len(doc) == 0:
                return ""

            first_page = doc[0]
            page_width = first_page.rect.width
            blocks = first_page.get_text("dict").get("blocks", [])
            title_lines = []

            # Analyze each text block for potential title content
            for block in blocks:
                if 'lines' not in block:
                    continue
                    
                for line in block['lines']:
                    line_text = ""
                    line_centered = False
                    max_font_size = 0

                    # Check each text span in the line
                    for span in line.get("spans", []):
                        text = span['text'].strip()
                        font_size = span['size']
                        bbox = span['bbox']
                        
                        # Calculate if text is centered on the page
                        center = (bbox[0] + bbox[2]) / 2
                        page_center = page_width / 2
                        centered = abs(center - page_center) < page_width * 0.25
                        
                        if centered and font_size >= self.min_font_size:
                            line_centered = True
                            max_font_size = max(max_font_size, font_size)
                            line_text += text + " "

                    # Add valid title lines
                    if line_centered and len(line_text.strip()) >= self.min_text_length:
                        title_lines.append((max_font_size, line_text.strip()))

            if title_lines:
                # Sort by font size and combine top lines for multi-line titles
                title_lines.sort(key=lambda x: x[0], reverse=True)
                top_lines = [line for _, line in title_lines[:2]]
                return " ".join(top_lines).strip()

            return ""
        except Exception:
            return ""

    def extract_font_info(self, doc: fitz.Document) -> List[Tuple[str, float, bool, int]]:
        """
        Extract font information from all pages to identify potential headings.
        
        Args:
            doc: PyMuPDF document object
            
        Returns:
            List of tuples containing (text, font_size, is_bold, page_number)
        """
        font_info = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict").get('blocks', [])
            
            for block in blocks:
                if 'lines' not in block:
                    continue
                    
                block_lines = []
                
                # Process each line in the block
                for line in block['lines']:
                    line_text = ""
                    font_size = 0
                    is_bold = False
                    
                    # Combine spans within a line
                    for span in line.get("spans", []):
                        text = span['text'].strip()
                        size = span['size']
                        flags = span['flags']
                        
                        if text:
                            line_text += text + " "
                            font_size = max(font_size, size)
                            is_bold = is_bold or bool(flags & 16)  # Bold flag check
                    
                    line_text = line_text.strip()
                    if line_text and font_size >= self.min_font_size:
                        block_lines.append((line_text, font_size, is_bold))
                
                # Combine lines within a block for complete headings
                if block_lines:
                    combined_text = " ".join([line[0] for line in block_lines]).strip()
                    max_font_size = max(line[1] for line in block_lines)
                    bold = any(line[2] for line in block_lines)
                    
                    # Filter out body text and keep potential headings
                    if (len(combined_text) >= self.min_text_length and 
                        not self._is_likely_body_text(combined_text)):
                        if max_font_size > 12 or bold:
                            font_info.append((combined_text, max_font_size, bold, page_num + 1))
        
        return font_info

    def _is_likely_body_text(self, text: str) -> bool:
        """
        Determine if text is likely body content rather than a heading.
        Uses various heuristics to filter out non-heading content.
        
        Args:
            text: Text to analyze
            
        Returns:
            True if text appears to be body content, False if potential heading
        """
        # Long paragraphs are likely body text
        if len(text) > 400 and not text.isupper():
            return True
        
        # Pure numbers or very short numbers
        if text.isdigit() or (len(text) <= 3 and text.isdigit()):
            return True
        
        text_lower = text.lower()
        
        # Common non-heading patterns
        noise_patterns = ['www.', 'http', '.com', 'appendix', 'copyright', '©', 'table', 'figure']
        for pattern in noise_patterns:
            if pattern in text_lower:
                return True
        
        # Very short or empty text
        if len(text.strip()) <= 1:
            return True
        
        # URLs and emails
        if '@' in text or 'http' in text_lower:
            return True
        
        # Short all-caps might be headers, but could also be noise
        if text.isupper() and len(text) < 15:
            return True
        
        # Text with many separators is likely formatting
        if '-' in text or ':' in text:
            if text.count('-') > 3 or text.count(':') > 2:
                return True
        
        return False

    def determine_heading_levels(self, font_info: List[Tuple[str, float, bool, int]]) -> List[Dict[str, any]]:
        """
        Assign heading levels (H1, H2, H3) based on font characteristics.
        
        Args:
            font_info: List of font information tuples
            
        Returns:
            List of heading dictionaries with level, text, and page
        """
        if not font_info:
            return []

        # Sort by page and font size for consistent processing
        font_info.sort(key=lambda x: (x[3], x[1]), reverse=True)
        
        # Get unique font sizes and map them to heading levels
        font_sizes = list({font_size for _, font_size, _, _ in font_info})
        font_sizes.sort(reverse=True)
        
        heading_levels = ['H1', 'H2', 'H3']
        size_to_level = {}

        # Assign levels based on font size hierarchy
        for i, size in enumerate(font_sizes[:len(heading_levels)]):
            size_to_level[size] = heading_levels[i]

        headings = []
        seen = set()  # Avoid duplicate headings
        
        # Sort by page order and font size
        font_info.sort(key=lambda x: (x[3], -x[1]))

        for text, font_size, is_bold, page_num in font_info:
            if font_size in size_to_level:
                cleaned = text.strip()
                
                # Skip duplicates (case-insensitive)
                if cleaned.lower() in seen:
                    continue
                seen.add(cleaned.lower())
                
                headings.append({
                    "level": size_to_level[font_size],
                    "text": cleaned,
                    "page": page_num
                })

        return headings

    def extract_outline(self, pdf_path: str) -> Dict[str, any]:
        """
        Main method to extract complete outline from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing title and outline structure
        """
        try:
            doc = fitz.open(pdf_path)
            
            # Extract title and headings
            title = self.extract_title(doc)
            font_info = self.extract_font_info(doc)
            headings = self.determine_heading_levels(font_info)
            
            # Remove title from headings to avoid duplication
            filtered_outline = [
                h for h in headings 
                if h['text'].strip().lower() != title.strip().lower()
            ]
            
            doc.close()
            
            return {
                "title": title.strip(),
                "outline": filtered_outline
            }
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")
            return {
                "title": "",
                "outline": []
            }

    def process_folder(self, input_folder: str, output_folder: str):
        """
        Process all PDF files in a folder and generate JSON outlines.
        
        Args:
            input_folder: Directory containing PDF files
            output_folder: Directory to save JSON output files
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Find all PDF files
        pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            print(f"No PDF files found in {input_folder}")
            return
        
        print(f"Found {len(pdf_files)} PDF files to process")
        
        # Process each PDF file
        for filename in pdf_files:
            input_path = os.path.join(input_folder, filename)
            base_name = os.path.splitext(filename)[0]
            output_path = os.path.join(output_folder, f"{base_name}.json")
            
            print(f"Processing: {filename}")
            result = self.extract_outline(input_path)
            
            # Save the extracted outline as JSON
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"  → Saved: {base_name}.json (found {len(result['outline'])} headings)")
            except Exception as e:
                print(f"  → Error saving {base_name}.json: {e}")


def main():
    """Main function to run the PDF outline extraction process."""
    input_folder = './input'
    output_folder = './output'
    
    print("PDF Outline Extractor")
    print("=" * 50)
    
    extractor = PDFOutlineExtractor()
    extractor.process_folder(input_folder, output_folder)
    
    print("\nDone!")


if __name__ == '__main__':
    main()