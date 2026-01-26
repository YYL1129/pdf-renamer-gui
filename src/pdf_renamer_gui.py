import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import fitz  # PyMuPDF
from PIL import Image
import pytesseract


def safe_filename(name: str) -> str:
    name = name.strip()
    name = re.sub(r"[\\/:\*\?\"<>\|]", "-", name)
    name = re.sub(r"\s+", " ", name)
    return name


def extract_text_from_pdf(pdf_path: str, max_pages: int = 2) -> str:
    """Try normal text extraction first (works for non-scanned PDFs)."""
    text_chunks = []
    try:
        doc = fitz.open(pdf_path)
        pages_to_read = min(len(doc), max_pages)
        for i in range(pages_to_read):
            page = doc.load_page(i)
            txt = page.get_text("text") or ""
            if txt.strip():
                text_chunks.append(txt)
        doc.close()
    except Exception:
        return ""

    return "\n".join(text_chunks).strip()


def ocr_first_pages(pdf_path: str, max_pages: int = 1) -> str:
    """
    OCR fallback for scanned PDFs.
    Render page as image using PyMuPDF, then run Tesseract OCR.
    """
    try:
        doc = fitz.open(pdf_path)
        pages_to_read = min(len(doc), max_pages)
        ocr_text = []

        for i in range(pages_to_read):
            page = doc.load_page(i)

            # Higher zoom = better OCR but slower
            mat = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            txt = pytesseract.image_to_string(img) or ""
            if txt.strip():
                ocr_text.append(txt)

        doc.close()
        return "\n".join(ocr_text).strip()
    except Exception:
        return ""


def propose_new_name(pdf_path: str) -> str:
    """
    Suggest rename:
    1) Extract selectable text
    2) If empty -> OCR page 1
    """
    base = os.path.splitext(os.path.basename(pdf_path))[0]

    text = extract_text_from_pdf(pdf_path)
    if not text:
        text = ocr_first_pages(pdf_path, max_pages=1)

    if not text:
        return safe_filename(base) + ".pdf"

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    lines = [ln for ln in lines if len(ln) >= 3]

    company = ""
    for ln in lines[:30]:
        letters = sum(ch.isalpha() for ch in ln)
        digits = sum(ch.isdigit() for ch in ln)
        if letters >= 6 and letters > digits:
            company = ln
            break

    desc = ""
    for ln in lines[:60]:
        if company and ln == company:
            continue
        if len(ln) >= 6:
            desc = ln
            break

    if not company and not desc:
        return safe_filename(base) + ".pdf"

    company = company[:60].strip()
    desc = desc[:80].strip()

    new_base = f"{company} - {desc}" if (company and desc) else (company or desc)
    return safe_filename(new_base) + ".pdf"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF Auto Renamer")
        self.geometry("980x560")

        self.selected_files = []
        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Folder").pack(side="left")

        self.folder_var = tk.StringVar()
        self.folder_entry = ttk.Entry(top, textvariable=self.folder_var, width=70)
        self.folder_entry.pack(side="left", padx=(8, 8))

        ttk.Button(top, text="Browse Folder", command=self.on_browse_folder).pack(side="left", padx=(0, 8))
        ttk.Button(top, text="Select PDFs", command=self.on_select_pdfs).pack(side="left", padx=(0, 8))
        ttk.Button(top, text="Rename", command=self.on_rename).pack(side="left")

        self.info_var = tk.StringVar(value="Tip: Choose folder or Select PDFs. Names will auto-preview.")
        ttk.Label(self, textvariable=self.info_var, padding=(10, 0, 10, 8)).pack(fill="x")

        table_frame = ttk.Frame(self, padding=(10, 0, 10, 10))
        table_frame.pack(fill="both", expand=True)

        columns = ("original", "new")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)
        self.tree.heading("original", text="Original filename")
        self.tree.heading("new", text="New filename")
        self.tree.column("original", width=450, anchor="w")
        self.tree.column("new", width=450, anchor="w")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def on_browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)
            self.selected_files = []
            self.info_var.set(f"Folder mode: {folder}")
            self.on_scan()  # ✅ auto preview

    def on_select_pdfs(self):
        paths = filedialog.askopenfilenames(
            title="Select PDF files",
            filetypes=[("PDF files", "*.pdf")],
        )
        if paths:
            self.selected_files = list(paths)
            self.info_var.set(f"Selected files mode: {len(self.selected_files)} PDF(s) selected")
            self.on_scan()  # ✅ auto preview

    def _get_input_pdfs(self):
        if self.selected_files:
            return self.selected_files

        folder = self.folder_var.get().strip()
        if not folder or not os.path.isdir(folder):
            return []

        pdfs = []
        for name in os.listdir(folder):
            if name.lower().endswith(".pdf"):
                pdfs.append(os.path.join(folder, name))
        pdfs.sort()
        return pdfs

    def on_scan(self):
        # Clear table
        self.tree.delete(*self.tree.get_children())

        pdfs = self._get_input_pdfs()
        if not pdfs:
            self.info_var.set("No input yet. Choose a folder OR click 'Select PDFs'.")
            return

        count = 0
        for pdf_path in pdfs:
            original = os.path.basename(pdf_path)
            new_name = propose_new_name(pdf_path)
            self.tree.insert("", "end", values=(original, new_name), tags=(pdf_path,))
            count += 1

        mode = "Selected files" if self.selected_files else "Folder"
        self.info_var.set(f"{mode}: scanned {count} PDF(s). Review names, then click Rename.")

    def on_rename(self):
        rows = self.tree.get_children()
        if not rows:
            messagebox.showinfo("Nothing to rename", "No files in the list yet. Choose a folder or Select PDFs first.")
            return

        renamed = 0
        skipped = 0
        errors = 0

        for row_id in rows:
            original_name, new_name = self.tree.item(row_id, "values")
            pdf_path = self.tree.item(row_id, "tags")[0]

            folder = os.path.dirname(pdf_path)
            new_path = os.path.join(folder, new_name)

            if os.path.abspath(pdf_path) == os.path.abspath(new_path):
                skipped += 1
                continue

            if os.path.exists(new_path):
                skipped += 1
                continue

            try:
                os.rename(pdf_path, new_path)
                renamed += 1
            except Exception:
                errors += 1

        messagebox.showinfo("Done", f"Renamed: {renamed}\nSkipped (same/exist): {skipped}\nErrors: {errors}")

        # Refresh the preview after rename
        self.on_scan()
