# PyInstaller hook for GDAL/osgeo
# This hook ensures GDAL data files and DLLs are properly bundled

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

# Collect GDAL data files
datas = collect_data_files('osgeo')

# Collect GDAL dynamic libraries (DLLs)
binaries = collect_dynamic_libs('osgeo')
