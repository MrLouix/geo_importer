#!/bin/bash
# Build script for GeoImporteur Windows executable
# Useful for building in a Windows-targeted Docker/Wine CI environment
# Output will be in dist/GeoImporteur.exe

pyinstaller --clean geo_importer.spec
