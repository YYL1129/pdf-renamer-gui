# PDF Renamer GUI (OCR)

A local Python GUI tool to automatically rename PDF files based on extracted content.

## Features
- GUI built with Tkinter
- Extracts text from PDFs
- OCR fallback using Tesseract
- Auto-renames PDFs based on detected company & description
- Runs fully offline (local only)

## Requirements
- Python 3.9+
- Tesseract OCR installed
- macOS / Windows / Linux

## Installation

Clone the repository and navigate into the project folder.

Create and activate a virtual environment:

```bash
python -m venv venv_pdf_renamer
source venv_pdf_renamer/bin/activate
