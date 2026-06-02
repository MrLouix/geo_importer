# PyInstaller spec file for GeoImporteur
# Build with: pyinstaller --clean geo_importer.spec

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('geo_importer.ico', '.')],
    hiddenimports=['osgeo', 'osgeo.gdal', 'osgeo.osr', 'osgeo._gdal', 'osgeo._osr'],
    hookspath=['hooks'],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

# GDAL data files and DLLs will be collected via hooks/hook-osgeo.py

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GeoImporteur',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='geo_importer.ico',
    onefile=True,
)
