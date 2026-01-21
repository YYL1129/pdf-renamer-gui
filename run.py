"""
Entry point for PDF Renamer GUI.

Run with:
    python run.py
"""

import sys
from pathlib import Path

# Ensure project root is on PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from src.pdf_renamer_gui import App


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
