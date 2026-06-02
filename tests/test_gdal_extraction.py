"""
Tests for extract_gdal_metadata().

osgeo / GDAL is not installed on the CI host, so the entire osgeo package is
mocked via patch.dict(sys.modules).  No real raster files are needed.
"""
import sys
import unittest
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, ".")
from main import extract_gdal_metadata


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_osgeo_mocks():
    """Return (mock_gdal, mock_osr, sys.modules patch-dict)."""
    mock_gdal = MagicMock(name="gdal")
    mock_osr = MagicMock(name="osr")
    mock_osgeo = MagicMock(name="osgeo")
    mock_osgeo.gdal = mock_gdal
    mock_osgeo.osr = mock_osr
    patches = {
        "osgeo": mock_osgeo,
        "osgeo.gdal": mock_gdal,
        "osgeo.osr": mock_osr,
    }
    return mock_gdal, mock_osr, patches


def _make_dataset(mock_gdal, *,
                  geo_transform=(700000.0, 0.5, 0.0, 6600000.0, 0.0, -0.5),
                  width=1000,
                  height=2000,
                  projection="PROJCS[dummy]",
                  band_count=1,
                  band_color_interps=None):
    """Build and wire a mock GDAL dataset on mock_gdal.Open."""
    if band_color_interps is None:
        band_color_interps = [1]  # GCI_GrayIndex

    dataset = MagicMock(name="dataset")
    mock_gdal.Open.return_value = dataset
    mock_gdal.GA_ReadOnly = 0

    dataset.GetGeoTransform.return_value = geo_transform
    dataset.RasterXSize = width
    dataset.RasterYSize = height
    dataset.GetProjection.return_value = projection
    dataset.RasterCount = band_count

    # Each GetRasterBand(i) returns a distinct mock
    band_mocks = []
    for ci in band_color_interps:
        b = MagicMock(name=f"band_ci{ci}")
        b.GetColorInterpretation.return_value = ci
        band_mocks.append(b)

    dataset.GetRasterBand.side_effect = lambda i: band_mocks[i - 1]
    return dataset


def _make_srs_mock(mock_osr, *, auth_name="EPSG", auth_code="2154",
                   projcs_name=None, geogcs_name=None):
    """Configure mock_osr.SpatialReference to return a controllable SRS."""
    srs = MagicMock(name="SpatialReference")
    mock_osr.SpatialReference.return_value = srs
    srs.GetAuthorityName.return_value = auth_name
    srs.GetAuthorityCode.return_value = auth_code

    def _get_attr(key):
        if key == "PROJCS":
            return projcs_name
        if key == "GEOGCS":
            return geogcs_name
        return None

    srs.GetAttrValue.side_effect = _get_attr
    return srs


# ---------------------------------------------------------------------------
# Test classes
# ---------------------------------------------------------------------------

class TestExtractGdalMetadataHappyPath(unittest.TestCase):
    """Full success path: single gray band, known EPSG, standard north-up raster."""

    def setUp(self):
        self.mock_gdal, self.mock_osr, self.patches = _make_osgeo_mocks()
        _make_dataset(self.mock_gdal)
        _make_srs_mock(self.mock_osr)
        self.mock_gdal.GetColorInterpretationName.return_value = "Gray"

    def _run(self):
        with patch.dict(sys.modules, self.patches):
            return extract_gdal_metadata("/fake/mnt.tif")

    def test_srs_epsg(self):
        result = self._run()
        self.assertEqual(result["srs"], "EPSG:2154")

    def test_width_and_height(self):
        result = self._run()
        self.assertEqual(result["width"], 1000)
        self.assertEqual(result["height"], 2000)

    def test_resolution(self):
        result = self._run()
        self.assertAlmostEqual(result["res_x"], 0.5)
        self.assertAlmostEqual(result["res_y"], 0.5)

    def test_bounding_box(self):
        result = self._run()
        # gt = (700000, 0.5, 0, 6600000, 0, -0.5)
        # x_max = 700000 + 1000*0.5 = 700500
        # y_min = 6600000 + 2000*(-0.5) = 6599000
        self.assertAlmostEqual(result["x_min"], 700000.0)
        self.assertAlmostEqual(result["y_max"], 6600000.0)
        self.assertAlmostEqual(result["x_max"], 700500.0)
        self.assertAlmostEqual(result["y_min"], 6599000.0)

    def test_band_count_and_names(self):
        result = self._run()
        self.assertEqual(result["band_count"], 1)
        self.assertEqual(result["bands"], ["Gray"])

    def test_use_exceptions_called(self):
        self._run()
        self.mock_gdal.UseExceptions.assert_called_once()

    def test_open_called_readonly(self):
        self._run()
        self.mock_gdal.Open.assert_called_once_with("/fake/mnt.tif", 0)


class TestExtractGdalMetadataOpenNone(unittest.TestCase):
    """gdal.Open returning None must raise ValueError."""

    def test_raises_value_error(self):
        mock_gdal, mock_osr, patches = _make_osgeo_mocks()
        mock_gdal.Open.return_value = None
        mock_gdal.GA_ReadOnly = 0

        with patch.dict(sys.modules, patches):
            with self.assertRaises(ValueError) as ctx:
                extract_gdal_metadata("/bad/file.tif")

        self.assertIn("/bad/file.tif", str(ctx.exception))


class TestBoundingBoxCalculation(unittest.TestCase):
    """Parametrised bounding-box arithmetic tests."""

    def _run(self, gt, width, height):
        mock_gdal, mock_osr, patches = _make_osgeo_mocks()
        _make_dataset(mock_gdal, geo_transform=gt, width=width, height=height)
        _make_srs_mock(mock_osr)
        mock_gdal.GetColorInterpretationName.return_value = "Gray"
        with patch.dict(sys.modules, patches):
            return extract_gdal_metadata("/fake/file.tif")

    def test_simple_bbox(self):
        # gt = (100, 10, 0, 500, 0, -10), 5 cols, 8 rows
        result = self._run((100.0, 10.0, 0.0, 500.0, 0.0, -10.0), 5, 8)
        self.assertAlmostEqual(result["x_min"], 100.0)
        self.assertAlmostEqual(result["y_max"], 500.0)
        self.assertAlmostEqual(result["x_max"], 150.0)   # 100 + 5*10
        self.assertAlmostEqual(result["y_min"], 420.0)   # 500 + 8*(-10)

    def test_resolution_always_positive(self):
        # GeoTransform pixel height is negative; res_y must be positive
        result = self._run((0.0, 2.0, 0.0, 1000.0, 0.0, -2.0), 100, 100)
        self.assertGreater(result["res_x"], 0)
        self.assertGreater(result["res_y"], 0)

    def test_decimal_resolution(self):
        result = self._run((600000.0, 0.25, 0.0, 7000000.0, 0.0, -0.25), 4000, 8000)
        self.assertAlmostEqual(result["res_x"], 0.25)
        self.assertAlmostEqual(result["res_y"], 0.25)
        self.assertAlmostEqual(result["x_max"], 601000.0)    # 600000 + 4000*0.25
        self.assertAlmostEqual(result["y_min"], 6998000.0)   # 7000000 + 8000*(-0.25)


class TestSrsExtraction(unittest.TestCase):
    """SRS extraction covers EPSG code, WKT name fallback, and Inconnue."""

    def _run(self, mock_gdal, mock_osr, patches):
        _make_dataset(mock_gdal)
        mock_gdal.GetColorInterpretationName.return_value = "Gray"
        with patch.dict(sys.modules, patches):
            return extract_gdal_metadata("/fake/file.tif")

    def test_epsg_authority_code(self):
        mock_gdal, mock_osr, patches = _make_osgeo_mocks()
        _make_srs_mock(mock_osr, auth_name="EPSG", auth_code="2154")
        result = self._run(mock_gdal, mock_osr, patches)
        self.assertEqual(result["srs"], "EPSG:2154")

    def test_non_epsg_authority(self):
        mock_gdal, mock_osr, patches = _make_osgeo_mocks()
        _make_srs_mock(mock_osr, auth_name="ESRI", auth_code="102100")
        result = self._run(mock_gdal, mock_osr, patches)
        self.assertEqual(result["srs"], "ESRI:102100")

    def test_fallback_projcs_name(self):
        """No authority code available → use PROJCS name."""
        mock_gdal, mock_osr, patches = _make_osgeo_mocks()
        _make_srs_mock(mock_osr, auth_name=None, auth_code=None,
                       projcs_name="RGF93 / Lambert-93")
        result = self._run(mock_gdal, mock_osr, patches)
        self.assertEqual(result["srs"], "RGF93 / Lambert-93")

    def test_fallback_geogcs_name_when_no_projcs(self):
        """No authority, no PROJCS → use GEOGCS name."""
        mock_gdal, mock_osr, patches = _make_osgeo_mocks()
        _make_srs_mock(mock_osr, auth_name=None, auth_code=None,
                       projcs_name=None, geogcs_name="WGS 84")
        result = self._run(mock_gdal, mock_osr, patches)
        self.assertEqual(result["srs"], "WGS 84")

    def test_inconnue_when_no_projection_wkt(self):
        """Empty projection string (no georeferencing) → 'Inconnue'."""
        mock_gdal, mock_osr, patches = _make_osgeo_mocks()
        # No SRS mock needed — GetProjection returns empty string
        ds = _make_dataset(mock_gdal, projection="")
        with patch.dict(sys.modules, patches):
            result = extract_gdal_metadata("/fake/file.tif")
        self.assertEqual(result["srs"], "Inconnue")
        # osr.SpatialReference must NOT have been instantiated
        mock_osr.SpatialReference.assert_not_called()

    def test_inconnue_when_authority_and_names_all_none(self):
        """WKT present but no authority and no PROJCS/GEOGCS names → 'Inconnue'."""
        mock_gdal, mock_osr, patches = _make_osgeo_mocks()
        _make_srs_mock(mock_osr, auth_name=None, auth_code=None,
                       projcs_name=None, geogcs_name=None)
        result = self._run(mock_gdal, mock_osr, patches)
        self.assertEqual(result["srs"], "Inconnue")


class TestBandColorInterpretation(unittest.TestCase):
    """Band list reflects GetColorInterpretationName for each band."""

    def _run_bands(self, color_interps, name_map):
        mock_gdal, mock_osr, patches = _make_osgeo_mocks()
        _make_dataset(mock_gdal, band_count=len(color_interps),
                      band_color_interps=color_interps)
        _make_srs_mock(mock_osr)
        mock_gdal.GetColorInterpretationName.side_effect = name_map.get
        with patch.dict(sys.modules, patches):
            return extract_gdal_metadata("/fake/file.tif")

    def test_single_gray_band(self):
        result = self._run_bands([1], {1: "Gray"})
        self.assertEqual(result["bands"], ["Gray"])
        self.assertEqual(result["band_count"], 1)

    def test_rgb_bands(self):
        result = self._run_bands([3, 4, 5], {3: "Red", 4: "Green", 5: "Blue"})
        self.assertEqual(result["bands"], ["Red", "Green", "Blue"])
        self.assertEqual(result["band_count"], 3)

    def test_rgba_bands(self):
        result = self._run_bands([3, 4, 5, 6], {3: "Red", 4: "Green", 5: "Blue", 6: "Alpha"})
        self.assertEqual(result["bands"], ["Red", "Green", "Blue", "Alpha"])
        self.assertEqual(result["band_count"], 4)

    def test_get_raster_band_called_for_each_band(self):
        mock_gdal, mock_osr, patches = _make_osgeo_mocks()
        ds = _make_dataset(mock_gdal, band_count=3, band_color_interps=[3, 4, 5])
        _make_srs_mock(mock_osr)
        mock_gdal.GetColorInterpretationName.side_effect = {3: "Red", 4: "Green", 5: "Blue"}.get
        with patch.dict(sys.modules, patches):
            extract_gdal_metadata("/fake/file.tif")
        ds.GetRasterBand.assert_any_call(1)
        ds.GetRasterBand.assert_any_call(2)
        ds.GetRasterBand.assert_any_call(3)


if __name__ == "__main__":
    unittest.main()
