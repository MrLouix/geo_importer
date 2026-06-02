# PyInstaller spec file for GeoImporteur
# Build with: pyinstaller --clean geo_importer.spec

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None

# Convert collect_data_files tuples (src, dst) to (src, dst, type) format
raw_datas = collect_data_files('osgeo')
datas = [(src, dst, 'DATA') for src, dst in raw_datas]
# Add icon file
if 'geo_importer.ico' in [d[0] for d in datas]:
    pass  # already included
else:
    datas.append(('geo_importer.ico', '.', 'DATA'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
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
