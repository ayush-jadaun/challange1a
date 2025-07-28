# PDF Outline Extractor

**Team**: FrontanGrinders  
**Team Leader**: Ayush Jadaun  
**Team Members**: Ashish Singh, Shreeya Srivastava  
**Challenge**: Adobe Hackathon Challenge 1A - "Connecting the Dots"

A robust solution for extracting structured outlines from PDF documents, designed for the "Connecting the Dots" Challenge Round 1A.

## Overview

This tool automatically extracts document titles and hierarchical headings (H1, H2, H3) from PDF files, outputting clean JSON structures that can be used for semantic analysis, search, and document intelligence applications.

## Approach

### Core Methodology

Our solution uses a multi-stage approach to intelligently identify document structure:

1. **Title Extraction**: Analyzes the first page to identify large, centered text that likely represents the document title
2. **Font Analysis**: Extracts font characteristics (size, boldness) from all pages to identify potential headings
3. **Content Filtering**: Uses heuristics to distinguish headings from body text, tables, and metadata
4. **Hierarchical Classification**: Maps font sizes to heading levels (H1, H2, H3) based on relative sizing

### Key Features

- **Font-Size Agnostic**: Doesn't rely solely on absolute font sizes, instead uses relative sizing within each document
- **Multi-line Title Support**: Handles documents with titles spanning multiple lines
- **Noise Filtering**: Removes page numbers, URLs, copyright notices, and other non-content elements
- **Multilingual Ready**: Handles Unicode text and international characters
- **Robust Error Handling**: Gracefully processes malformed or complex PDFs

### Technical Implementation

- **PyMuPDF Integration**: Uses the fitz library for efficient PDF parsing and text extraction
- **Block-Level Analysis**: Processes text blocks rather than individual characters for better context
- **Positioning Analysis**: Considers text positioning for title identification
- **Duplicate Removal**: Prevents duplicate headings in the output

## Libraries Used

- **PyMuPDF (fitz)**: Primary PDF processing library, chosen for its speed and accuracy in text extraction
- **Python Standard Library**: json, os, typing for core functionality

## Architecture

```
PDFOutlineExtractor
├── extract_title()           # Identifies document title from first page
├── extract_font_info()       # Gathers font characteristics from all pages
├── _is_likely_body_text()    # Filters out non-heading content
├── determine_heading_levels() # Maps font sizes to H1/H2/H3 levels
├── extract_outline()         # Main extraction orchestrator
└── process_folder()          # Batch processing interface
```

## Build and Run Instructions

### Building the Docker Image

```bash
docker build --platform linux/amd64 -t pdf-extractor:latest .
```

### Running the Solution

The solution is designed to run with the exact command specified in the challenge requirements:

```bash
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-extractor:latest
```

**Note**: This command works on Linux/Unix systems (as used by the challenge evaluators). For local testing on different operating systems:

#### For Linux/macOS:
```bash
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-extractor:latest
```

#### For Windows Command Prompt:
```cmd
docker run --rm -v "%cd%\input":/app/input -v "%cd%\output":/app/output --network none pdf-extractor:latest
```

#### For Windows PowerShell:
```powershell
docker run --rm -v "${PWD}\input":/app/input -v "${PWD}\output":/app/output --network none pdf-extractor:latest
```

### Setup Instructions

1. **Create the required directory structure**:
   ```bash
   mkdir -p input output
   ```

2. **Place your PDF files** in the `input` directory

3. **Build the Docker image** using the command above

4. **Run the container** using the appropriate command for your operating system

### Challenge Compliance

This solution meets all Adobe Hackathon Challenge 1A requirements:
- ✅ Processes PDFs up to 50 pages
- ✅ Extracts titles and H1/H2/H3 headings with page numbers
- ✅ Outputs valid JSON in the specified format
- ✅ Runs on AMD64 architecture without GPU dependencies
- ✅ Model size < 200MB (no external models used)
- ✅ Works offline with no network calls
- ✅ Processing time < 10 seconds for 50-page PDFs

### Expected Output

For each `filename.pdf` in the input directory, the system generates `filename.json` in the output directory with the following structure:

```json
{
  "title": "Document Title Here",
  "outline": [
    { "level": "H1", "text": "Introduction", "page": 1 },
    { "level": "H2", "text": "Background", "page": 2 },
    { "level": "H3", "text": "Related Work", "page": 3 }
  ]
}
```

## Performance Characteristics

- **Processing Speed**: < 10 seconds for 50-page PDFs
- **Model Size**: No external models required (< 200MB total)
- **Memory Usage**: Optimized for 16GB RAM systems
- **CPU Architecture**: Compatible with AMD64/x86_64 systems

## Testing Strategy

The solution has been tested across various document types:
- Academic papers with complex formatting
- Technical reports with mixed font sizes
- Multi-language documents
- Documents with unusual layouts

## Limitations and Considerations

- Focuses on text-based PDFs (not scanned images)
- Prioritizes precision over recall for heading detection
- May miss headings that don't follow standard font size conventions
- Designed for documents with clear hierarchical structure

## File Structure

```
├── pdf_extractor.py    # Main application code
├── Dockerfile         # Container configuration
├── requirements.txt   # Python dependencies
└── README.md         # This documentation
```

## Troubleshooting

**No headings detected**: Check if the PDF uses consistent font sizing for headings
**Missing title**: Ensure the title is prominently displayed on the first page
**Processing errors**: Verify the PDF is not password-protected or corrupted