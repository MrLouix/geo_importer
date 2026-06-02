# Geo-Importeur

**Geo-Importeur** est une application bureau simple pour importer des fichiers géospatiaux tout en générant automatiquement un fichier de métadonnées au format Markdown.

## Fonctionnalités

- Interface graphique intuitive pour sélectionner les fichiers sources et les dossiers de destination
- Validation des champs obligatoires (fichier source, dossier cible, URL, type de fichier)
- Validation de l'URL (protocole http/https requis)
- Copie du fichier géospatial vers le dossier de destination
- Extraction automatique des métadonnées techniques via GDAL
- Génération d'un fichier README.md contenant toutes les métadonnées
- Gestion des erreurs avec rollback automatique en cas d'échec

## Prérequis

### Python

- **Python 3.8 ou supérieur** est requis
- Vous pouvez télécharger Python depuis [python.org](https://www.python.org/downloads/)

### GDAL (Géospatial Data Abstraction Library)

Ce projet nécessite la bibliothèque GDAL pour lire les métadonnées des fichiers géospatiaux.

#### Installation de GDAL sur Windows

**Méthode recommandée (la plus simple) :**

1. Téléchargez le fichier Wheel correspondant à votre version de Python depuis :
   [https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal](https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal)

2. Installez GDAL avec pip :
   ```bash
   pip install GDAL-3.8.0-cp311-cp311-win_amd64.whl
   ```
   *(Remplacez le nom du fichier par celui que vous avez téléchargé)*

**Méthode alternative avec Conda :**

Si vous utilisez Anaconda ou Miniconda :
```bash
conda install -c conda-forge gdal
```

#### Installation de GDAL sur Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install gdal-bin libgdal-dev
pip install gdal
```

#### Installation de GDAL sur macOS

```bash
brew install gdal
pip install gdal
```

## Installation

1. Clonez ce dépôt :
   ```bash
   git clone https://github.com/MrLouix/geo_importer.git
   cd geo_importer
   ```

2. Créez un environnement virtuel (recommandé) :
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .\.venv\Scripts\activate   # Windows
   ```

3. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

## Utilisation

### Exécuter l'application en mode développement

```bash
python main.py
```

### Utiliser l'application

1. Cliquez sur "Parcourir..." pour sélectionner votre fichier source (ex: un GeoTIFF)
2. Cliquez sur "Parcourir..." pour sélectionner le dossier de destination
3. Saisissez l'URL source du fichier
4. Sélectionnez le type de fichier (MNT, MNS, Orthophoto, ou Custom...)
5. Ajoutez des notes si nécessaire
6. Cliquez sur "Importer"

L'application va :
- Copier le fichier vers le dossier de destination
- Extraire les métadonnées techniques (projection, résolution, étendue spatiale, etc.)
- Générer un fichier `.readme.md` avec toutes les informations

### Exemple de sortie

Un fichier nommé `nom_du_fichier.tif.readme.md` sera créé avec un contenu comme :

```markdown
# Métadonnées - nom_du_fichier.tif

## Informations Générales
* **Type de donnée :** MNT
* **Date d'import :** 02/06/2026 à 14:30
* **URL Source :** https://data.example.com/mnt.tif
* **Notes :** Test import

## Informations Techniques (Extraites via GDAL)
* **Système de Projection (SRS) :** EPSG:2154
* **Nombre de couches / bandes :** 1
* **Type des couches :** Gray
* **Emprise Spatiale (Bounding Box) :**
  * XMin : 700000.000 | YMin : 6599000.000
  * XMax : 700500.000 | YMax : 6600000.000
* **Résolution :** 0.500m x 0.500m
* **Dimensions de l'image :** 1000 x 2000 pixels
```

## Créer un exécutable Windows

Pour créer un exécutable standalone (fichier .exe unique) :

### Méthode 1 : Utiliser le script batch

Double-cliquez simplement sur `build.bat` ou exécutez :
```batch
build.bat
```

### Méthode 2 : Commande manuelle

```bash
pip install pyinstaller
pyinstaller --clean geo_importer.spec
```

L'exécutable sera généré dans le dossier `dist/GeoImporteur.exe`.

Vous pouvez ensuite distribuer ce fichier .exe qui contiendra tout ce dont il a besoin pour fonctionner.

## Exécuter les tests

```bash
python -m unittest discover tests
```

Ou pour un test spécifique :
```bash
python -m unittest tests.test_build_config
python -m unittest tests.test_integration
python -m unittest tests.test_validation
python -m unittest tests.test_gui
python -m unittest tests.test_file_ops
```

## Structure du projet

```
geo_importer/
├── main.py              # Code principal de l'application
├── geo_importer.spec    # Configuration PyInstaller
├── build.bat            # Script de build Windows
├── build.sh             # Script de build Linux/CI
├── requirements.txt     # Dépendances Python
├── README.md            # Ce fichier
└── tests/
    ├── test_build_config.py
    ├── test_file_ops.py
    ├── test_gdal_extraction.py
    ├── test_gui.py
    ├── test_integration.py
    └── test_validation.py
```

## Technologies utilisées

- **Python 3.8+** : Langage principal
- **Tkinter** : Interface graphique
- **GDAL/OGR** : Lecture des métadonnées géospatiales
- **PyInstaller** : Génération de l'exécutable Windows

## Contribution

Les contributions sont les bienvenues ! Ouvrez une issue ou soumettez une pull request.

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.
