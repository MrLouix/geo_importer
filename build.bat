@echo off
:: Build script for GeoImporteur Windows executable
:: Output will be in dist/GeoImporteur.exe

pyinstaller --clean geo_importer.spec
