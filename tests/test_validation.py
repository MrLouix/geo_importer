import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from main import validate_fields, validate_url


class TestValidateFields(unittest.TestCase):

    def test_all_fields_present(self):
        ok, msg = validate_fields("/src/file.tif", "/dst/", "https://example.com", "MNT")
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_missing_source_file(self):
        ok, msg = validate_fields("", "/dst/", "https://example.com", "MNT")
        self.assertFalse(ok)
        self.assertIn("fichier source", msg)

    def test_none_source_file(self):
        ok, msg = validate_fields(None, "/dst/", "https://example.com", "MNT")
        self.assertFalse(ok)
        self.assertIn("fichier source", msg)

    def test_missing_target_folder(self):
        ok, msg = validate_fields("/src/file.tif", "", "https://example.com", "MNT")
        self.assertFalse(ok)
        self.assertIn("dossier cible", msg)

    def test_none_target_folder(self):
        ok, msg = validate_fields("/src/file.tif", None, "https://example.com", "MNT")
        self.assertFalse(ok)
        self.assertIn("dossier cible", msg)

    def test_missing_url(self):
        ok, msg = validate_fields("/src/file.tif", "/dst/", "", "MNT")
        self.assertFalse(ok)
        self.assertIn("URL source", msg)

    def test_none_url(self):
        ok, msg = validate_fields("/src/file.tif", "/dst/", None, "MNT")
        self.assertFalse(ok)
        self.assertIn("URL source", msg)

    def test_missing_file_type(self):
        ok, msg = validate_fields("/src/file.tif", "/dst/", "https://example.com", "")
        self.assertFalse(ok)
        self.assertIn("type de fichier", msg)

    def test_none_file_type(self):
        ok, msg = validate_fields("/src/file.tif", "/dst/", "https://example.com", None)
        self.assertFalse(ok)
        self.assertIn("type de fichier", msg)

    def test_custom_file_type_accepted(self):
        ok, msg = validate_fields("/src/file.tif", "/dst/", "https://example.com", "LiDAR")
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_mns_type_accepted(self):
        ok, msg = validate_fields("/src/file.tif", "/dst/", "http://example.com", "MNS")
        self.assertTrue(ok)

    def test_orthophoto_type_accepted(self):
        ok, msg = validate_fields("/src/file.tif", "/dst/", "http://example.com", "Orthophoto")
        self.assertTrue(ok)


class TestValidateUrl(unittest.TestCase):

    def test_valid_https_url(self):
        ok, msg = validate_url("https://example.com/data/file.tif")
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_valid_http_url(self):
        ok, msg = validate_url("http://data.example.org/mnt.zip")
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_missing_scheme(self):
        ok, msg = validate_url("example.com/file.tif")
        self.assertFalse(ok)

    def test_empty_string(self):
        ok, msg = validate_url("")
        self.assertFalse(ok)
        self.assertIn("vide", msg.lower())

    def test_ftp_scheme_rejected(self):
        ok, msg = validate_url("ftp://example.com/file.tif")
        self.assertFalse(ok)
        self.assertIn("ftp", msg)

    def test_missing_netloc(self):
        ok, msg = validate_url("https:///no-domain/file.tif")
        self.assertFalse(ok)
        self.assertIn("domaine", msg)

    def test_completely_invalid_string(self):
        ok, msg = validate_url("not a url at all")
        self.assertFalse(ok)

    def test_https_with_path_and_query(self):
        ok, msg = validate_url("https://geoservices.ign.fr/download?layer=MNT&format=tif")
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_http_with_port(self):
        ok, msg = validate_url("http://internal.server:8080/data/orthophoto.tif")
        self.assertTrue(ok)
        self.assertEqual(msg, "")


if __name__ == "__main__":
    unittest.main()
