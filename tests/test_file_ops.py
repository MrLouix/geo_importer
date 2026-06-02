"""
Tests for copy_file(), generate_readme(), and rollback().
No real raster files or GDAL needed — metadata is supplied as plain dicts.
"""
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, call, MagicMock

sys.path.insert(0, ".")
from main import copy_file, generate_readme, rollback


# ---------------------------------------------------------------------------
# Sample metadata shared across generate_readme tests
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

SAMPLE_METADATA_RGB = {
    **SAMPLE_METADATA,
    "band_count": 3,
    "bands": ["Red", "Green", "Blue"],
}


# ---------------------------------------------------------------------------
# copy_file
# ---------------------------------------------------------------------------

class TestCopyFile(unittest.TestCase):

    def test_shutil_copy2_called_with_correct_args(self):
        with patch("main.shutil.copy2") as mock_copy:
            copy_file("/src/data/mnt.tif", "/dst/folder")
            mock_copy.assert_called_once_with("/src/data/mnt.tif", "/dst/folder")

    def test_returns_destination_path(self):
        with patch("main.shutil.copy2"):
            result = copy_file("/src/data/mnt.tif", "/dst/folder")
        self.assertEqual(result, os.path.join("/dst/folder", "mnt.tif"))

    def test_returns_correct_path_for_nested_source(self):
        with patch("main.shutil.copy2"):
            result = copy_file("/a/b/c/ortho_2023.tiff", "/output")
        self.assertEqual(result, os.path.join("/output", "ortho_2023.tiff"))

    def test_copy2_propagates_oserror(self):
        with patch("main.shutil.copy2", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                copy_file("/src/file.tif", "/dst")


# ---------------------------------------------------------------------------
# generate_readme
# ---------------------------------------------------------------------------

class TestGenerateReadme(unittest.TestCase):

    def _call(self, metadata=None, file_type="MNT", url="https://example.com",
              notes="Test notes", filename="mnt_zone.tif", tmpdir=None):
        if metadata is None:
            metadata = SAMPLE_METADATA
        copied = os.path.join(tmpdir, filename)
        # The copied file doesn't have to exist for generate_readme to work
        return generate_readme(copied, metadata, file_type, url, notes), copied

    def test_readme_file_is_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = self._call(tmpdir=tmpdir)
            self.assertTrue(os.path.isfile(path))

    def test_readme_filename_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = self._call(tmpdir=tmpdir, filename="mnt_zone.tif")
            self.assertEqual(os.path.basename(path), "mnt_zone.tif.readme.md")

    def test_readme_is_in_same_folder_as_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path, copied = self._call(tmpdir=tmpdir)
            self.assertEqual(os.path.dirname(path), os.path.dirname(copied))

    def test_contains_file_type(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = self._call(file_type="Orthophoto", tmpdir=tmpdir)
            self.assertIn("Orthophoto", open(path, encoding="utf-8").read())

    def test_contains_url(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = self._call(url="https://data.geopf.fr/mnt.tif", tmpdir=tmpdir)
            self.assertIn("https://data.geopf.fr/mnt.tif",
                          open(path, encoding="utf-8").read())

    def test_contains_srs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = self._call(tmpdir=tmpdir)
            self.assertIn("EPSG:2154", open(path, encoding="utf-8").read())

    def test_contains_notes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = self._call(notes="Données IGN 2023", tmpdir=tmpdir)
            self.assertIn("Données IGN 2023", open(path, encoding="utf-8").read())

    def test_bounding_box_three_decimal_places(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = self._call(tmpdir=tmpdir)
            content = open(path, encoding="utf-8").read()
            self.assertIn("700000.000", content)
            self.assertIn("6599000.000", content)
            self.assertIn("700500.000", content)
            self.assertIn("6600000.000", content)

    def test_resolution_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = self._call(tmpdir=tmpdir)
            self.assertIn("0.500m x 0.500m", open(path, encoding="utf-8").read())

    def test_image_dimensions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = self._call(tmpdir=tmpdir)
            self.assertIn("1000 x 2000 pixels", open(path, encoding="utf-8").read())

    def test_band_string_single_gray(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = self._call(tmpdir=tmpdir)
            self.assertIn("Couche 1 : Gray", open(path, encoding="utf-8").read())

    def test_band_string_rgb(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = self._call(metadata=SAMPLE_METADATA_RGB, tmpdir=tmpdir)
            content = open(path, encoding="utf-8").read()
            self.assertIn("Couche 1 : Red", content)
            self.assertIn("Couche 2 : Green", content)
            self.assertIn("Couche 3 : Blue", content)

    def test_band_count_in_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = self._call(metadata=SAMPLE_METADATA_RGB, tmpdir=tmpdir)
            self.assertIn("3", open(path, encoding="utf-8").read())

    def test_filename_in_title(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = self._call(filename="ortho_2023.tif", tmpdir=tmpdir)
            self.assertIn("ortho_2023.tif", open(path, encoding="utf-8").read())

    def test_custom_file_type(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = self._call(file_type="LiDAR", tmpdir=tmpdir)
            self.assertIn("LiDAR", open(path, encoding="utf-8").read())

    def test_returns_readme_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = self._call(tmpdir=tmpdir)
            self.assertTrue(path.endswith(".readme.md"))

    def test_date_format_present(self):
        """Date must appear in DD/MM/YYYY à HH:MM format."""
        import re
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = self._call(tmpdir=tmpdir)
            content = open(path, encoding="utf-8").read()
            self.assertRegex(content, r"\d{2}/\d{2}/\d{4} à \d{2}:\d{2}")


# ---------------------------------------------------------------------------
# rollback
# ---------------------------------------------------------------------------

class TestRollback(unittest.TestCase):

    def test_removes_both_files_when_both_exist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f1 = os.path.join(tmpdir, "file.tif")
            f2 = os.path.join(tmpdir, "file.tif.readme.md")
            open(f1, "w").close()
            open(f2, "w").close()
            rollback(f1, f2)
            self.assertFalse(os.path.exists(f1))
            self.assertFalse(os.path.exists(f2))

    def test_removes_only_copied_file_when_readme_is_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f1 = os.path.join(tmpdir, "file.tif")
            open(f1, "w").close()
            rollback(f1, None)
            self.assertFalse(os.path.exists(f1))

    def test_removes_only_readme_when_copied_path_is_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f2 = os.path.join(tmpdir, "file.tif.readme.md")
            open(f2, "w").close()
            rollback(None, f2)
            self.assertFalse(os.path.exists(f2))

    def test_does_not_raise_when_both_paths_are_none(self):
        try:
            rollback(None, None)
        except Exception as exc:
            self.fail(f"rollback(None, None) raised unexpectedly: {exc}")

    def test_does_not_raise_when_copied_file_missing(self):
        """Path given but file was never written — must not raise."""
        try:
            rollback("/nonexistent/path/file.tif", None)
        except Exception as exc:
            self.fail(f"rollback raised for missing file: {exc}")

    def test_does_not_raise_when_readme_missing(self):
        try:
            rollback(None, "/nonexistent/path/file.readme.md")
        except Exception as exc:
            self.fail(f"rollback raised for missing readme: {exc}")

    def test_does_not_raise_when_both_missing(self):
        try:
            rollback("/gone/file.tif", "/gone/file.tif.readme.md")
        except Exception as exc:
            self.fail(f"rollback raised for both missing: {exc}")

    def test_partial_rollback_readme_exists_copied_does_not(self):
        """Copied file already gone; only readme should be removed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f2 = os.path.join(tmpdir, "file.tif.readme.md")
            open(f2, "w").close()
            rollback("/gone/file.tif", f2)
            self.assertFalse(os.path.exists(f2))

    def test_partial_rollback_copied_exists_readme_does_not(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f1 = os.path.join(tmpdir, "file.tif")
            open(f1, "w").close()
            rollback(f1, "/gone/readme.md")
            self.assertFalse(os.path.exists(f1))


if __name__ == "__main__":
    unittest.main()
