import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import fitz
from PIL import Image
import pytesseract


COMPANY_SHORT_MAP = {
    "AQ PACK (M) SDN BHD": "AQP",
    "AQ PACK (PENANG) SDN BHD": "AQPP",
    "TENAGA NASIONAL": "TNB",
    "MAXIS": "MAXIS",
}

MAX_COMPANY_LEN = 20
MAX_DESC_LEN = 60


def clean(s):
    s = s.upper()
    s = re.sub(r"[\\/:*?\"<>|]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def extract_text(pdf):
    try:
        doc = fitz.open(pdf)
        text = ""
        for i in range(min(2, doc.page_count)):
            text += doc.load_page(i).get_text()
        doc.close()
        return text.strip()
    except:
        return ""


def extract_ocr(pdf):
    try:
        doc = fitz.open(pdf)
        text = ""
        for i in range(min(2, doc.page_count)):
            pix = doc.load_page(i).get_pixmap(matrix=fitz.Matrix(2, 2))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text += pytesseract.image_to_string(img)
        doc.close()
        return text.strip()
    except:
        return ""


def guess_company(text):
    text_u = clean(text)
    for k, v in COMPANY_SHORT_MAP.items():
        if k in text_u:
            return v
    words = re.findall(r"[A-Z]{3,}", text_u)
    return words[0] if words else "UNKNOWN"


def guess_desc(text):
    lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 8]
    if not lines:
        return "DOCUMENT"
    s = clean(lines[0])
    return s[:MAX_DESC_LEN].rsplit(" ", 1)[0] if len(s) > MAX_DESC_LEN else s


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("PDF Auto Renamer")
        self.geometry("900x500")

        # macOS focus fix
        self.lift()
        self.attributes("-topmost", True)
        self.after(300, lambda: self.attributes("-topmost", False))
        self.after(100, self.focus_force)

        self.folder = tk.StringVar()
        self.rows = []

        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Folder").pack(side="left")
        ttk.Entry(top, textvariable=self.folder, width=60).pack(side="left", padx=8)
        ttk.Button(top, text="Browse", command=self.pick).pack(side="left")
        ttk.Button(top, text="Scan", command=self.scan).pack(side="left", padx=8)
        ttk.Button(top, text="Rename", command=self.rename).pack(side="left")

        self.tree = ttk.Treeview(self, columns=("old", "new"), show="headings")
        self.tree.heading("old", text="Original filename")
        self.tree.heading("new", text="New filename")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def pick(self):
        d = filedialog.askdirectory()
        if d:
            self.folder.set(d)

    def scan(self):
        self.tree.delete(*self.tree.get_children())
        self.rows.clear()

        folder = self.folder.get()
        if not os.path.isdir(folder):
            messagebox.showerror("Error", "Invalid folder")
            return

        for f in os.listdir(folder):
            if not f.lower().endswith(".pdf"):
                continue

            path = os.path.join(folder, f)
            text = extract_text(path)
            if len(text) < 50:
                text = extract_ocr(path)

            company = guess_company(text)[:MAX_COMPANY_LEN]
            desc = guess_desc(text)
            new = f"{company} - {desc}.pdf"

            self.rows.append((path, new))
            self.tree.insert("", "end", values=(f, new))

    def rename(self):
        if not self.rows:
            messagebox.showinfo("Info", "Nothing to rename. Scan first.")
            return

        if not messagebox.askyesno("Confirm", "Rename all files?"):
            return

        folder = self.folder.get()
        for old, new in self.rows:
            new_path = os.path.join(folder, new)
            if os.path.exists(new_path):
                continue
            os.rename(old, new_path)

        messagebox.showinfo("Done", "Renaming complete")
        self.scan()


if __name__ == "__main__":
    App().mainloop()
