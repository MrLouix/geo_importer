# PyInstaller spec file for GeoImporteur
# Build with: pyinstaller --clean geo_importer.spec

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('geo_importer.ico', '.')],
    hiddenimports=['osgeo.gdal', 'osgeo.osr', 'osgeo._gdal', 'osgeo._osr'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Add GDAL data files and DLLs via hooks
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

a.datas += collect_data_files('osgeo')
a.binaries = collect_dynamic_libs('osgeo')

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
