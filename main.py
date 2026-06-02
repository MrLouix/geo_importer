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


def extract_gdal_metadata(file_path: str) -> dict:
    """Open a raster with GDAL and return a dict of technical metadata."""
    from osgeo import gdal, osr

    gdal.UseExceptions()

    dataset = gdal.Open(file_path, gdal.GA_ReadOnly)
    if dataset is None:
        raise ValueError(f"Impossible d'ouvrir le fichier raster : {file_path}")

    try:
        # --- Spatial reference system ---
        wkt = dataset.GetProjection()
        srs_str = "Inconnue"
        if wkt:
            srs = osr.SpatialReference()
            srs.ImportFromWkt(wkt)
            auth_name = srs.GetAuthorityName(None)
            auth_code = srs.GetAuthorityCode(None)
            if auth_name and auth_code:
                srs_str = f"{auth_name}:{auth_code}"
            else:
                name = srs.GetAttrValue("PROJCS") or srs.GetAttrValue("GEOGCS")
                srs_str = name if name else "Inconnue"

        # --- Dimensions ---
        width = dataset.RasterXSize
        height = dataset.RasterYSize

        # --- GeoTransform ---
        gt = dataset.GetGeoTransform()
        res_x = abs(gt[1])
        res_y = abs(gt[5])
        x_min = gt[0]
        y_max = gt[3]
        x_max = gt[0] + width * gt[1]
        y_min = gt[3] + height * gt[5]

        # --- Bands ---
        band_count = dataset.RasterCount
        bands = []
        for i in range(1, band_count + 1):
            band = dataset.GetRasterBand(i)
            ci = band.GetColorInterpretation()
            bands.append(gdal.GetColorInterpretationName(ci))

        return {
            "srs": srs_str,
            "width": width,
            "height": height,
            "res_x": res_x,
            "res_y": res_y,
            "x_min": x_min,
            "y_max": y_max,
            "x_max": x_max,
            "y_min": y_min,
            "band_count": band_count,
            "bands": bands,
        }
    finally:
        dataset = None  # dereference / close GDAL dataset


def copy_file(source_path: str, target_folder: str) -> str:
    """Copy source_path into target_folder using shutil.copy2 (preserves metadata)."""
    shutil.copy2(source_path, target_folder)
    return os.path.join(target_folder, os.path.basename(source_path))


def generate_readme(
    copied_file_path: str,
    metadata: dict,
    file_type: str,
    url: str,
    notes: str,
) -> str:
    """Write a Markdown metadata file alongside the copied raster and return its path."""
    basename = os.path.basename(copied_file_path)
    target_dir = os.path.dirname(copied_file_path)
    readme_path = os.path.join(target_dir, basename + ".readme.md")

    bands_str = ", ".join(
        f"Couche {i + 1} : {name}"
        for i, name in enumerate(metadata["bands"])
    )
    date_str = datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")

    content = (
        f"# Métadonnées - {basename}\n"
        "\n"
        "## Informations Générales\n"
        f"* **Type de donnée :** {file_type}\n"
        f"* **Date d'import :** {date_str}\n"
        f"* **URL Source :** {url}\n"
        f"* **Notes :** {notes}\n"
        "\n"
        "## Informations Techniques (Extraites via GDAL)\n"
        f"* **Système de Projection (SRS) :** {metadata['srs']}\n"
        f"* **Nombre de couches / bandes :** {metadata['band_count']}\n"
        f"* **Type des couches :** {bands_str}\n"
        "* **Emprise Spatiale (Bounding Box) :**\n"
        f"  * XMin : {metadata['x_min']:.3f} | YMin : {metadata['y_min']:.3f}\n"
        f"  * XMax : {metadata['x_max']:.3f} | YMax : {metadata['y_max']:.3f}\n"
        f"* **Résolution :** {metadata['res_x']:.3f}m x {metadata['res_y']:.3f}m\n"
        f"* **Dimensions de l'image :** {metadata['width']} x {metadata['height']} pixels\n"
    )

    with open(readme_path, "w", encoding="utf-8") as fh:
        fh.write(content)

    return readme_path


def rollback(copied_file_path, readme_path) -> None:
    """Delete copied file and/or readme if they exist (best-effort cleanup)."""
    if copied_file_path is not None and os.path.exists(copied_file_path):
        os.remove(copied_file_path)
    if readme_path is not None and os.path.exists(readme_path):
        os.remove(readme_path)


class GeoImporterApp:

    FILE_TYPES = ["MNT", "MNS", "Orthophoto", "Custom..."]

    def __init__(self, root):
        import tkinter as tk
        import tkinter.ttk as ttk
        import tkinter.filedialog as filedialog
        import tkinter.messagebox as messagebox

        self.root = root
        self._tk = tk
        self._ttk = ttk
        self._filedialog = filedialog
        self._messagebox = messagebox

        self._setup_window()
        self._build_ui()

    def _setup_window(self):
        self.root.title("Géo-Importeur")
        self.root.geometry("600x400")
        self.root.resizable(False, False)

    def _build_ui(self):
        tk = self._tk
        ttk = self._ttk
        pad = {"padx": 8, "pady": 4}

        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Source file row
        ttk.Label(main_frame, text="Fichier source :").grid(
            row=0, column=0, sticky="w", **pad
        )
        self._source_entry = ttk.Entry(main_frame, state="readonly")
        self._source_entry.grid(row=0, column=1, sticky="ew", **pad)
        ttk.Button(
            main_frame, text="Parcourir...", command=self._browse_source
        ).grid(row=0, column=2, **pad)

        # Target folder row
        ttk.Label(main_frame, text="Dossier cible :").grid(
            row=1, column=0, sticky="w", **pad
        )
        self._target_entry = ttk.Entry(main_frame, state="readonly")
        self._target_entry.grid(row=1, column=1, sticky="ew", **pad)
        ttk.Button(
            main_frame, text="Parcourir...", command=self._browse_target
        ).grid(row=1, column=2, **pad)

        # URL row
        ttk.Label(main_frame, text="URL Source :").grid(
            row=2, column=0, sticky="w", **pad
        )
        self._url_entry = ttk.Entry(main_frame)
        self._url_entry.grid(row=2, column=1, columnspan=2, sticky="ew", **pad)

        # File type row
        ttk.Label(main_frame, text="Type de fichier :").grid(
            row=3, column=0, sticky="w", **pad
        )
        type_frame = ttk.Frame(main_frame)
        type_frame.grid(row=3, column=1, columnspan=2, sticky="ew", **pad)
        type_frame.columnconfigure(1, weight=1)

        self._type_combo = ttk.Combobox(
            type_frame,
            values=self.FILE_TYPES,
            state="readonly",
            width=14,
        )
        self._type_combo.grid(row=0, column=0, padx=(0, 6))
        self._type_combo.bind("<<ComboboxSelected>>", self._on_type_change)

        self._custom_entry = ttk.Entry(type_frame, state="disabled")
        self._custom_entry.grid(row=0, column=1, sticky="ew")

        # Notes row
        ttk.Label(main_frame, text="Notes :").grid(
            row=4, column=0, sticky="nw", **pad
        )
        self._notes_text = tk.Text(main_frame, height=4, wrap="word")
        self._notes_text.grid(row=4, column=1, columnspan=2, sticky="ew", **pad)

        # Action buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=5, column=0, columnspan=3, pady=8)
        ttk.Button(btn_frame, text="Importer", command=self._on_import).grid(
            row=0, column=0, padx=12
        )
        ttk.Button(btn_frame, text="Annuler", command=self.root.destroy).grid(
            row=0, column=1, padx=12
        )

    def _browse_source(self):
        path = self._filedialog.askopenfilename(title="Sélectionner le fichier source")
        if path:
            self._source_entry.config(state="normal")
            self._source_entry.delete(0, "end")
            self._source_entry.insert(0, path)
            self._source_entry.config(state="readonly")

    def _browse_target(self):
        path = self._filedialog.askdirectory(title="Sélectionner le dossier cible")
        if path:
            self._target_entry.config(state="normal")
            self._target_entry.delete(0, "end")
            self._target_entry.insert(0, path)
            self._target_entry.config(state="readonly")

    def _on_type_change(self, event=None):
        if self._type_combo.get() == "Custom...":
            self._custom_entry.config(state="normal")
        else:
            self._custom_entry.config(state="disabled")
            self._custom_entry.delete(0, "end")

    def get_file_type(self) -> str:
        value = self._type_combo.get()
        if value == "Custom...":
            return self._custom_entry.get()
        return value

    def _on_import(self):
        # 1. Gather inputs
        source_file = self._source_entry.get()
        target_folder = self._target_entry.get()
        url = self._url_entry.get()
        file_type = self.get_file_type()
        notes = self._notes_text.get("1.0", "end-1c")

        # 2. Validate completeness
        ok, msg = validate_fields(source_file, target_folder, url, file_type)
        if not ok:
            self._messagebox.showerror("Champ manquant", msg)
            return

        # 3. Validate URL syntax
        ok, msg = validate_url(url)
        if not ok:
            self._messagebox.showerror("URL invalide", msg)
            return

        # 4. Copy file
        try:
            copied_path = copy_file(source_file, target_folder)
        except OSError as exc:
            self._messagebox.showerror("Erreur de copie", str(exc))
            return

        # 5. Extract metadata and generate readme (rollback on any failure)
        readme_path = None
        try:
            metadata = extract_gdal_metadata(copied_path)
            readme_path = generate_readme(copied_path, metadata, file_type, url, notes)
        except Exception as exc:
            rollback(copied_path, readme_path)
            self._messagebox.showerror("Erreur GDAL", str(exc))
            return

        # 6. Report success
        self._messagebox.showinfo(
            "Import réussi",
            "Le fichier a été importé avec succès et ses métadonnées ont été générées.",
        )


def main():
    import tkinter as tk
    root = tk.Tk()
    GeoImporterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
