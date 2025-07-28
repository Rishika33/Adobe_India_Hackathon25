# Adobe India Hackathon 2025 - Round 1A: PDF Outline Extraction

## 🔍 Overview
This solution extracts structured headings (Title, H1, H2, H3, etc.) from PDFs and generates a JSON file per document.

## 📁 Directory Structure


## ⚙️ Requirements
- Python 3.10+
- Docker (for containerization)

## 📦 Build Docker Image
```bash
docker build --platform linux/amd64 -t adobe-parser .

## Run the container

docker run --rm -v "C:/Users/rishi/OneDrive/文件/adobe_hackathon/input:/app/input" -v "C:/Users/rishi/OneDrive/文件/adobe_hackathon/output:/app/output" adobe-parser

##📤 Output Format

## Each .pdf in input/ results in a .json file in output/ folder in this format:
{
  "title": "Document Title",
  "outline": [
    { "level": "H1", "text": "Heading", "page": 1 },
    ...
  ]
}

🧠 Approach
Used PyMuPDF (fitz) to extract fonts, text, and structure.

Determined heading levels using font size and font family.

Title is detected using the largest font on the first page.

📌 Constraints Met
✅ No internet access during runtime

✅ Execution < 10s for 50-page PDF

✅ Output matches schema

✅ Tested on AMD64 CPU architecture