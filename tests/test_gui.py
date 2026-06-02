"""
Tests for GeoImporterApp GUI logic.

tkinter is not available on the CI host, so we mock the entire tkinter
package family via patch.dict(sys.modules) before instantiating the class.
Widget references stored on self.app are then replaced with fresh MagicMocks
so each test has full control over .get() / .config() return values.
"""
import sys
import unittest
from unittest.mock import MagicMock, patch, call

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tk_mocks():
    """Return a sys.modules patch dict that stubs out tkinter completely."""
    mock_tk = MagicMock(name="tkinter")
    mock_ttk = MagicMock(name="tkinter.ttk")
    mock_filedialog = MagicMock(name="tkinter.filedialog")
    mock_messagebox = MagicMock(name="tkinter.messagebox")
    # Make tkinter.ttk reachable via both the submodule path and as an
    # attribute of the tkinter mock (Python resolves either way).
    mock_tk.ttk = mock_ttk
    mock_tk.filedialog = mock_filedialog
    mock_tk.messagebox = mock_messagebox
    return {
        "tkinter": mock_tk,
        "tkinter.ttk": mock_ttk,
        "tkinter.filedialog": mock_filedialog,
        "tkinter.messagebox": mock_messagebox,
    }


def _make_app(mocks):
    """Instantiate GeoImporterApp with a mocked Tk root under the given mocks."""
    # Import must happen here (inside the patch context) so the module-level
    # `import tkinter` inside __init__ picks up the mocks.
    sys.path.insert(0, ".")
    import importlib
    import main as m
    importlib.reload(m)  # ensure a clean slate if tests run in-process

    mock_root = MagicMock(name="Tk root")
    app = m.GeoImporterApp(mock_root)
    return app


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestOnTypeChange(unittest.TestCase):
    """_on_type_change enables / disables the custom entry correctly."""

    def setUp(self):
        self._mocks = _make_tk_mocks()
        with patch.dict(sys.modules, self._mocks):
            self.app = _make_app(self._mocks)
        # Replace widget refs with fresh, independent mocks for precise control
        self.app._type_combo = MagicMock(name="type_combo")
        self.app._custom_entry = MagicMock(name="custom_entry")

    def test_custom_selected_enables_entry(self):
        self.app._type_combo.get.return_value = "Custom..."
        self.app._on_type_change()
        self.app._custom_entry.config.assert_called_with(state="normal")

    def test_mnt_selected_disables_entry(self):
        self.app._type_combo.get.return_value = "MNT"
        self.app._on_type_change()
        self.app._custom_entry.config.assert_called_with(state="disabled")

    def test_mns_selected_disables_entry(self):
        self.app._type_combo.get.return_value = "MNS"
        self.app._on_type_change()
        self.app._custom_entry.config.assert_called_with(state="disabled")

    def test_orthophoto_selected_disables_entry(self):
        self.app._type_combo.get.return_value = "Orthophoto"
        self.app._on_type_change()
        self.app._custom_entry.config.assert_called_with(state="disabled")

    def test_non_custom_clears_custom_entry(self):
        """Switching away from Custom... must also clear the custom entry."""
        self.app._type_combo.get.return_value = "MNT"
        self.app._on_type_change()
        self.app._custom_entry.delete.assert_called_with(0, "end")

    def test_custom_does_not_clear_entry(self):
        """Switching TO Custom... must NOT clear whatever the user typed."""
        self.app._type_combo.get.return_value = "Custom..."
        self.app._on_type_change()
        self.app._custom_entry.delete.assert_not_called()

    def test_event_argument_is_optional(self):
        """_on_type_change must accept no event (called without binding)."""
        self.app._type_combo.get.return_value = "MNT"
        try:
            self.app._on_type_change()   # no event kwarg
            self.app._on_type_change(event=None)
        except TypeError:
            self.fail("_on_type_change raised TypeError with no event argument")


class TestGetFileType(unittest.TestCase):
    """get_file_type returns the correct resolved string."""

    def setUp(self):
        mocks = _make_tk_mocks()
        with patch.dict(sys.modules, mocks):
            self.app = _make_app(mocks)
        self.app._type_combo = MagicMock(name="type_combo")
        self.app._custom_entry = MagicMock(name="custom_entry")

    def test_returns_mnt(self):
        self.app._type_combo.get.return_value = "MNT"
        self.assertEqual(self.app.get_file_type(), "MNT")

    def test_returns_mns(self):
        self.app._type_combo.get.return_value = "MNS"
        self.assertEqual(self.app.get_file_type(), "MNS")

    def test_returns_orthophoto(self):
        self.app._type_combo.get.return_value = "Orthophoto"
        self.assertEqual(self.app.get_file_type(), "Orthophoto")

    def test_custom_returns_entry_text(self):
        self.app._type_combo.get.return_value = "Custom..."
        self.app._custom_entry.get.return_value = "LiDAR"
        self.assertEqual(self.app.get_file_type(), "LiDAR")

    def test_custom_empty_entry_returns_empty_string(self):
        self.app._type_combo.get.return_value = "Custom..."
        self.app._custom_entry.get.return_value = ""
        self.assertEqual(self.app.get_file_type(), "")

    def test_custom_whitespace_only_is_returned_as_is(self):
        """Whitespace is valid input; stripping is not our responsibility here."""
        self.app._type_combo.get.return_value = "Custom..."
        self.app._custom_entry.get.return_value = "   "
        self.assertEqual(self.app.get_file_type(), "   ")

    def test_no_selection_returns_empty_string(self):
        """Before user picks anything, combobox returns ''."""
        self.app._type_combo.get.return_value = ""
        self.assertEqual(self.app.get_file_type(), "")


class TestWindowSetup(unittest.TestCase):
    """The root window is configured correctly during __init__."""

    def test_window_title_and_geometry(self):
        mocks = _make_tk_mocks()
        with patch.dict(sys.modules, mocks):
            app = _make_app(mocks)
        app.root.title.assert_called_with("Géo-Importeur")
        app.root.geometry.assert_called_with("600x400")
        app.root.resizable.assert_called_with(False, False)


if __name__ == "__main__":
    unittest.main()
