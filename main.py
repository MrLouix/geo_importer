import os
import shutil
import datetime
from urllib.parse import urlparse


def validate_fields(source_file: str, target_folder: str, url: str, file_type: str) -> tuple:
    """Check that all required import fields are non-empty."""
    fields = {
        "fichier source": source_file,
        "dossier cible": target_folder,
        "URL source": url,
        "type de fichier": file_type,
    }
    for label, value in fields.items():
        if not value:
            return (False, f"Le champ '{label}' est requis.")
    return (True, "")


def validate_url(url: str) -> tuple:
    """Check that url has an http/https scheme and a non-empty netloc."""
    if not url:
        return (False, "L'URL ne peut pas être vide.")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return (False, f"Le protocole '{parsed.scheme}' est invalide. Utilisez http ou https.")
    if not parsed.netloc:
        return (False, "L'URL ne contient pas de nom de domaine valide.")
    return (True, "")


def main():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    root = tk.Tk()
    root.mainloop()


if __name__ == "__main__":
    main()
