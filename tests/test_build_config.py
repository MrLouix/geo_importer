"""
Tests for PyInstaller build configuration files.
"""
import os
import unittest


class TestSpecFile(unittest.TestCase):
    """Test geo_importer.spec file existence and content."""

    SPEC_PATH = os.path.join(os.path.dirname(__file__), "..", "geo_importer.spec")

    def test_spec_file_exists(self):
        self.assertTrue(os.path.exists(self.SPEC_PATH))

    def test_spec_contains_exe_name(self):
        with open(self.SPEC_PATH, "r") as f:
            content = f.read()
        self.assertIn("GeoImporteur", content)

    def test_spec_contains_console_false(self):
        with open(self.SPEC_PATH, "r") as f:
            content = f.read()
        self.assertIn("console=False", content)

    def test_spec_contains_onefile_true(self):
        with open(self.SPEC_PATH, "r") as f:
            content = f.read()
        self.assertIn("onefile=True", content)

    def test_spec_references_osgeo_for_gdal_bundling(self):
        with open(self.SPEC_PATH, "r") as f:
            content = f.read()
        self.assertIn("osgeo", content)
        self.assertIn("collect_data_files", content)
        self.assertIn("collect_dynamic_libs", content)

    def test_spec_contains_hidden_imports(self):
        with open(self.SPEC_PATH, "r") as f:
            content = f.read()
        self.assertIn("osgeo.gdal", content)
        self.assertIn("osgeo.osr", content)


class TestBuildScripts(unittest.TestCase):
    """Test build script existence and content."""

    BUILD_BAT_PATH = os.path.join(os.path.dirname(__file__), "..", "build.bat")
    BUILD_SH_PATH = os.path.join(os.path.dirname(__file__), "..", "build.sh")

    def test_build_bat_exists(self):
        self.assertTrue(os.path.exists(self.BUILD_BAT_PATH))

    def test_build_bat_contains_pyinstaller(self):
        with open(self.BUILD_BAT_PATH, "r") as f:
            content = f.read()
        self.assertIn("pyinstaller", content)

    def test_build_bat_has_comment_about_output(self):
        with open(self.BUILD_BAT_PATH, "r") as f:
            content = f.read()
        self.assertIn("dist", content)

    def test_build_sh_exists(self):
        self.assertTrue(os.path.exists(self.BUILD_SH_PATH))

    def test_build_sh_contains_pyinstaller(self):
        with open(self.BUILD_SH_PATH, "r") as f:
            content = f.read()
        self.assertIn("pyinstaller", content)


class TestRequirements(unittest.TestCase):
    """Test requirements.txt content."""

    REQ_PATH = os.path.join(os.path.dirname(__file__), "..", "requirements.txt")

    def test_requirements_contains_pyinstaller(self):
        with open(self.REQ_PATH, "r") as f:
            content = f.read()
        self.assertIn("pyinstaller", content)

    def test_requirements_contains_gdal(self):
        with open(self.REQ_PATH, "r") as f:
            content = f.read()
        self.assertIn("gdal", content)


if __name__ == "__main__":
    unittest.main()
