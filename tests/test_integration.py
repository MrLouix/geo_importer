"""
Integration tests for GeoImporterApp._on_import().

Strategy:
- tkinter is not installed on CI, so the entire tkinter family is mocked in
  sys.modules before GeoImporterApp is instantiated (same technique as
  test_gui.py).
- IMPORTANT: 'main' is imported at module level (before any with patch.dict
  calls) so that patch.dict saves it in its snapshot and restores it on exit.
  Without this, 'main' would be removed from sys.modules after the context
  exits, causing patch('main.copy_file') to reimport a fresh module dict that
  _on_import.__globals__ doesn't reference.
- After construction, individual widget references are replaced with fresh
  MagicMocks that return predictable values.
- Module-level functions (copy_file, extract_gdal_metadata, generate_readme,
  rollback) are patched via unittest.mock.patch so no real I/O or GDAL is
  needed.
- Real validate_fields / validate_url logic runs (not mocked) so validation
  behaviour is exercised end-to-end.
"""
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, ".")
import main  # must be imported before any with patch.dict(sys.modules) call


# ---------------------------------------------------------------------------
# tkinter mock helpers
# ---------------------------------------------------------------------------

def _make_tk_mocks():
    mock_tk = MagicMock(name="tkinter")
    mock_ttk = MagicMock(name="tkinter.ttk")
    mock_filedialog = MagicMock(name="tkinter.filedialog")
    mock_messagebox = MagicMock(name="tkinter.messagebox")
    mock_tk.ttk = mock_ttk
    mock_tk.filedialog = mock_filedialog
    mock_tk.messagebox = mock_messagebox
    return {
        "tkinter": mock_tk,
        "tkinter.ttk": mock_ttk,
        "tkinter.filedialog": mock_filedialog,
        "tkinter.messagebox": mock_messagebox,
    }


def _make_app():
    """Instantiate GeoImporterApp with mocked tkinter (no reload needed)."""
    tk_mocks = _make_tk_mocks()
    with patch.dict(sys.modules, tk_mocks):
        mock_root = MagicMock(name="Tk root")
        app = main.GeoImporterApp(mock_root)
    return app


# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

SAMPLE_METADATA = {
    "srs": "EPSG:2154",
    "width": 1000,
    "height": 2000,
    "res_x": 0.5,
    "res_y": 0.5,
    "x_min": 700000.0,
    "y_min": 6599000.0,
    "x_max": 700500.0,
    "y_max": 6600000.0,
    "band_count": 1,
    "bands": ["Gray"],
}

COPIED_PATH = "/dst/folder/mnt.tif"
README_PATH = "/dst/folder/mnt.tif.readme.md"


# ---------------------------------------------------------------------------
# Base class: wires up a fully-mocked app ready for _on_import tests
# ---------------------------------------------------------------------------

class _AppTestBase(unittest.TestCase):
    """Create GeoImporterApp with controllable widget mocks per test."""

    SOURCE_FILE = "/src/mnt.tif"
    TARGET_FOLDER = "/dst/folder"
    URL = "https://data.example.com/mnt.tif"
    FILE_TYPE = "MNT"
    NOTES = "Test notes"

    def setUp(self):
        self.app = _make_app()

        self.app._source_entry = MagicMock(name="source_entry")
        self.app._source_entry.get.return_value = self.SOURCE_FILE

        self.app._target_entry = MagicMock(name="target_entry")
        self.app._target_entry.get.return_value = self.TARGET_FOLDER

        self.app._url_entry = MagicMock(name="url_entry")
        self.app._url_entry.get.return_value = self.URL

        self.app._type_combo = MagicMock(name="type_combo")
        self.app._type_combo.get.return_value = self.FILE_TYPE

        self.app._custom_entry = MagicMock(name="custom_entry")
        self.app._custom_entry.get.return_value = ""

        self.app._notes_text = MagicMock(name="notes_text")
        self.app._notes_text.get.return_value = self.NOTES

        self.app._messagebox = MagicMock(name="messagebox")

    def _run(self, copy_rv=COPIED_PATH, gdal_rv=SAMPLE_METADATA,
             readme_rv=README_PATH, copy_se=None, gdal_se=None, readme_se=None):
        """
        Call _on_import under standard module-level patches and return the mocks.
        Pass copy_se / gdal_se / readme_se to inject side_effect exceptions.
        """
        copy_kw = {"side_effect": copy_se} if copy_se else {"return_value": copy_rv}
        gdal_kw = {"side_effect": gdal_se} if gdal_se else {"return_value": gdal_rv}
        read_kw = {"side_effect": readme_se} if readme_se else {"return_value": readme_rv}

        with patch("main.copy_file", **copy_kw) as mock_copy, \
             patch("main.extract_gdal_metadata", **gdal_kw) as mock_gdal, \
             patch("main.generate_readme", **read_kw) as mock_readme, \
             patch("main.rollback") as mock_rollback:
            self.app._on_import()

        return {
            "copy": mock_copy,
            "gdal": mock_gdal,
            "readme": mock_readme,
            "rollback": mock_rollback,
        }


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------

class TestOnImportSuccess(_AppTestBase):

    def test_showinfo_called_once(self):
        self._run()
        self.app._messagebox.showinfo.assert_called_once()

    def test_showerror_not_called(self):
        self._run()
        self.app._messagebox.showerror.assert_not_called()

    def test_copy_file_called_with_correct_args(self):
        mocks = self._run()
        mocks["copy"].assert_called_once_with(self.SOURCE_FILE, self.TARGET_FOLDER)

    def test_extract_gdal_called_with_copied_path(self):
        mocks = self._run()
        mocks["gdal"].assert_called_once_with(COPIED_PATH)

    def test_generate_readme_called_with_correct_args(self):
        mocks = self._run()
        mocks["readme"].assert_called_once_with(
            COPIED_PATH, SAMPLE_METADATA, self.FILE_TYPE, self.URL, self.NOTES
        )

    def test_rollback_not_called_on_success(self):
        mocks = self._run()
        mocks["rollback"].assert_not_called()

    def test_notes_read_with_correct_text_widget_args(self):
        self._run()
        self.app._notes_text.get.assert_called_with("1.0", "end-1c")


# ---------------------------------------------------------------------------
# Validation failures — copy_file must never be called
# ---------------------------------------------------------------------------

class TestOnImportMissingField(_AppTestBase):

    def setUp(self):
        super().setUp()
        self.app._source_entry.get.return_value = ""

    def test_showerror_champ_manquant(self):
        mocks = self._run()
        self.app._messagebox.showerror.assert_called_once()
        title = self.app._messagebox.showerror.call_args[0][0]
        self.assertEqual(title, "Champ manquant")

    def test_copy_file_not_called(self):
        mocks = self._run()
        mocks["copy"].assert_not_called()

    def test_showinfo_not_called(self):
        self._run()
        self.app._messagebox.showinfo.assert_not_called()


class TestOnImportMissingTargetFolder(_AppTestBase):

    def setUp(self):
        super().setUp()
        self.app._target_entry.get.return_value = ""

    def test_showerror_called(self):
        self._run()
        self.app._messagebox.showerror.assert_called_once()

    def test_copy_file_not_called(self):
        mocks = self._run()
        mocks["copy"].assert_not_called()


class TestOnImportInvalidUrl(_AppTestBase):

    def setUp(self):
        super().setUp()
        self.app._url_entry.get.return_value = "ftp://example.com/mnt.tif"

    def test_showerror_url_invalide(self):
        self._run()
        title = self.app._messagebox.showerror.call_args[0][0]
        self.assertEqual(title, "URL invalide")

    def test_copy_file_not_called(self):
        mocks = self._run()
        mocks["copy"].assert_not_called()


class TestOnImportMalformedUrl(_AppTestBase):

    def setUp(self):
        super().setUp()
        self.app._url_entry.get.return_value = "not-a-url"

    def test_showerror_url_invalide(self):
        self._run()
        title = self.app._messagebox.showerror.call_args[0][0]
        self.assertEqual(title, "URL invalide")

    def test_copy_file_not_called(self):
        mocks = self._run()
        mocks["copy"].assert_not_called()


# ---------------------------------------------------------------------------
# Copy error — rollback must NOT be called (file was never written)
# ---------------------------------------------------------------------------

class TestOnImportCopyError(_AppTestBase):

    def test_showerror_erreur_de_copie(self):
        self._run(copy_se=OSError("disk full"))
        title = self.app._messagebox.showerror.call_args[0][0]
        self.assertEqual(title, "Erreur de copie")

    def test_error_message_contains_oserror_text(self):
        self._run(copy_se=OSError("disk full"))
        msg = self.app._messagebox.showerror.call_args[0][1]
        self.assertIn("disk full", msg)

    def test_rollback_not_called(self):
        mocks = self._run(copy_se=OSError("disk full"))
        mocks["rollback"].assert_not_called()

    def test_gdal_not_called(self):
        mocks = self._run(copy_se=OSError("disk full"))
        mocks["gdal"].assert_not_called()

    def test_showinfo_not_called(self):
        self._run(copy_se=OSError("disk full"))
        self.app._messagebox.showinfo.assert_not_called()


# ---------------------------------------------------------------------------
# GDAL error — rollback must be called with copied_path and None readme_path
# ---------------------------------------------------------------------------

class TestOnImportGdalError(_AppTestBase):

    def test_showerror_erreur_gdal(self):
        self._run(gdal_se=Exception("GDAL: not a raster"))
        title = self.app._messagebox.showerror.call_args[0][0]
        self.assertEqual(title, "Erreur GDAL")

    def test_error_message_contains_exception_text(self):
        self._run(gdal_se=Exception("GDAL: not a raster"))
        msg = self.app._messagebox.showerror.call_args[0][1]
        self.assertIn("GDAL: not a raster", msg)

    def test_rollback_called_with_copied_path_and_none_readme(self):
        # readme_path is None because generate_readme was never reached
        mocks = self._run(gdal_se=Exception("GDAL: not a raster"))
        mocks["rollback"].assert_called_once_with(COPIED_PATH, None)

    def test_generate_readme_not_called(self):
        mocks = self._run(gdal_se=Exception("GDAL: not a raster"))
        mocks["readme"].assert_not_called()

    def test_showinfo_not_called(self):
        self._run(gdal_se=Exception("GDAL: not a raster"))
        self.app._messagebox.showinfo.assert_not_called()


# ---------------------------------------------------------------------------
# Readme generation error — rollback called with both paths
# ---------------------------------------------------------------------------

class TestOnImportReadmeError(_AppTestBase):

    def test_showerror_called(self):
        self._run(readme_se=OSError("cannot write readme"))
        self.app._messagebox.showerror.assert_called_once()

    def test_rollback_called_with_correct_paths(self):
        # readme_path is None because generate_readme raised before returning
        mocks = self._run(readme_se=OSError("cannot write readme"))
        mocks["rollback"].assert_called_once_with(COPIED_PATH, None)

    def test_showinfo_not_called(self):
        self._run(readme_se=OSError("cannot write readme"))
        self.app._messagebox.showinfo.assert_not_called()


# ---------------------------------------------------------------------------
# Edge: empty custom type triggers field validation failure
# ---------------------------------------------------------------------------

class TestOnImportEmptyCustomType(_AppTestBase):

    def setUp(self):
        super().setUp()
        self.app._type_combo.get.return_value = "Custom..."
        self.app._custom_entry.get.return_value = ""

    def test_showerror_for_missing_file_type(self):
        self._run()
        title = self.app._messagebox.showerror.call_args[0][0]
        self.assertEqual(title, "Champ manquant")

    def test_copy_not_called(self):
        mocks = self._run()
        mocks["copy"].assert_not_called()


if __name__ == "__main__":
    unittest.main()
