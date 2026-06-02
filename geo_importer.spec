# PyInstaller spec file for GeoImporteur
# Build with: pyinstaller --clean geo_importer.spec

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=collect_data_files('osgeo') + [('geo_importer.ico', '.', 'DATA')],
    hiddenimports=['osgeo.gdal', 'osgeo.osr', 'osgeo._gdal', 'osgeo._osr'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries + collect_dynamic_libs('osgeo'),
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
