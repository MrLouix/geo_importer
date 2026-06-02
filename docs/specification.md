# Spécification Fonctionnelle et Technique : Géo-Importeur
## 1. Présentation du Projet
L'objectif est de développer une mini-application de bureau dotée d'une interface graphique (GUI) en Python. Elle permet à l'utilisateur d'importer proprement un fichier de données géospatiales (MNT, MNS, Orthophoto), de documenter sa provenance via une URL valide, de le copier dans un répertoire cible, et de générer automatiquement un fichier de métadonnées complet au format Markdown (.readme.md) en exploitant la librairie **GDAL**.
## 2. Interface Utilisateur (UI)
L'interface graphique est développée avec la bibliothèque standard **Tkinter** de Python, en s'appuyant sur le module de composants graphiques ttk pour garantir un rendu visuel moderne et harmonieux.
Elle est constituée d'une fenêtre unique (600x400 pixels, de dimensions fixes et non redimensionnable) structurée selon les éléments suivants :
 * **Sélection du fichier source :**
   * Un champ d'affichage textuel (en lecture seule) présentant le chemin absolu du fichier local sélectionné.
   * Un bouton **"Parcourir..."** ouvrant le sélecteur de fichiers natif (filedialog.askopenfilename).
 * **Sélection du dossier cible :**
   * Un champ d'affichage textuel (en lecture seule) présentant le chemin du dossier de destination.
   * Un bouton **"Parcourir..."** ouvrant le sélecteur de dossiers natif (filedialog.askdirectory), qui offre à l'utilisateur la possibilité de naviguer et de créer directement un nouveau dossier.
 * **Informations complémentaires :**
   * **URL Source :** Un champ de saisie libre (Entry) destiné à accueillir le lien de téléchargement original du fichier.
   * **Type de fichier :** Une liste déroulante (Combobox) proposant des catégories prédéfinies : MNT, MNS, Orthophoto, Custom....
   * **Champ Custom :** Un champ texte adjacent, grisé et désactivé par défaut. Il s'active automatiquement si et seulement si l'option "Custom..." est sélectionnée dans la liste déroulante, permettant à l'utilisateur de saisir manuellement une autre catégorie.
   * Un champ **Notes** en texte libre sur plusieurs lignes, permettant à l'utilisateur de mentionner les détails qu'il souhaite
 * **Actions :**
   * Un bouton **"Importer"** lançant le processus de validation, de copie et d'analyse.
   * Un bouton **"Annuler"** fermant proprement l'application sans effectuer d'action.
## 3. Logique de Traitement (Workflow)
Dès que l'utilisateur clique sur le bouton **"Importer"**, l'application déroule de manière séquentielle les étapes suivantes :
### Étape 1 : Validations préalables
 1. **Contrôle de complétude :** L'application vérifie que le fichier source, le dossier cible, l'URL et le type de fichier (valeur de la liste ou valeur personnalisée "Custom") sont correctement renseignés. Si un champ requis est vide, une boîte de dialogue d'alerte bloque la suite de l'opération.
 2. **Validation technique de l'URL :** À l'aide de la fonction urlparse du module standard urllib.parse, l'application s'assure que la chaîne saisie constitue une URL syntaxiquement correcte, exigeant l'emploi d'un protocole web valide (http ou https) ainsi qu'un nom de domaine (netloc). Toute non-conformité interrompt immédiatement le processus.
### Étape 2 : Copie physique du fichier
 * Le fichier sélectionné à l'origine est copié vers le dossier de destination au moyen de la méthode shutil.copy2. Ce choix technique permet de préserver l'intégralité des métadonnées du fichier d'origine (notamment les dates de création et de modification).
 * Le fichier conserve strictement son nom et son extension d'origine au sein de sa nouvelle destination.
### Étape 3 : Extraction des métadonnées via GDAL
L'application charge le fichier nouvellement copié en mode lecture seule grâce au module Python de **GDAL** (osgeo.gdal). Elle procède alors à l'extraction des données techniques clés :
 1. **Système de projection (SRS) :** Lecture et analyse de la définition spatiale WKT afin d'extraire le code d'autorité (par exemple, EPSG:2154 pour le Lambert-93) ou, si indisponible, le nom explicite du système de projection.
 2. **Dimensions et Résolution :** Lecture des dimensions en pixels de l'image (nombre de colonnes et de lignes). Détermination de la taille physique des pixels (résolution sur l'axe X et sur l'axe Y) par le biais de la matrice de transformation géométrique (*GeoTransform*).
 3. **Emprise spatiale (Bounding Box) :** Calcul géométrique précis reposant sur les coordonnées d'origine et la taille des pixels pour obtenir les limites géographiques ou planaires extrêmes : XMin, YMin, XMax, YMax.
 4. **Analyse des Couches (Bandes) :** * Lecture du nombre total de couches (bandes raster) via la propriété RasterCount.
   * Pour chacune de ces couches, interrogation de sa nature et de sa désignation de couleur (GetColorInterpretation()). Ces données sont interprétées de façon intelligible pour l'utilisateur (ex. : *Gray* pour un MNT de niveaux de gris, ou *Red*, *Green*, *Blue*, *Alpha* pour une image aérienne de type Orthophoto).
### Étape 4 : Génération du fichier de métadonnées Markdown
Un fichier d'accompagnement nommé [Nom_Du_Fichier_D_Origine].readme.md est généré directement au côté du fichier importé dans le dossier cible. Ce document rassemble et met en forme l'intégralité des informations recueillies.
## 4. Structure attendue du fichier .readme.md
Le fichier de métadonnées généré est structuré selon le gabarit Markdown standardisé suivant :
```markdown
# Métadonnées - [Nom du Fichier + extension]

## Informations Générales
* **Type de donnée :** [MNT / MNS / Orthophoto / Valeur Custom]
* **Date d'import :** [Date et Heure au format JJ/MM/AAAA à HH:MM]
* **URL Source :** [Lien de téléchargement vérifié et validé]

## Informations Techniques (Extraites via GDAL)
* **Système de Projection (SRS) :** [Ex: EPSG:2154 - RGF93 / Lambert-93]
* **Nombre de couches / bandes :** [Ex: 1 ou 3]
* **Type des couches :** [Ex: Couche 1 : Red, Couche 2 : Green, Couche 3 : Blue]
* **Emprise Spatiale (Bounding Box) :**
  * XMin : [Valeur décimale à 3 chiffres après la virgule] | YMin : [Valeur décimale à 3 chiffres]
  * XMax : [Valeur décimale à 3 chiffres après la virgule] | YMax : [Valeur décimale à 3 chiffres]
* **Résolution :** [Ex: 0.500m x 0.500m]
* **Dimensions de l'image :** [Largeur] x [Hauteur] pixels

```
## 5. Spécifications Techniques & Dépendances
Afin de simplifier l'installation et de garantir une portabilité optimale, le projet s'appuie sur un ensemble restreint de modules :
 * **Langage cible :** Python 3.x
 * **Bibliothèques de la distribution standard Python (aucun prérequis d'installation) :**
   * tkinter & tkinter.filedialog (Conception de l'IHM et explorateur de fichiers).
   * urllib.parse (Validation et découpage d'URL).
   * shutil (Copie de fichiers de haut niveau).
   * os (Manipulations de chemins système et suppression de fichiers).
   * datetime (Récupération de la date et de l'heure locales).
 * **Bibliothèque tierce requise :**
   * GDAL (via son API Python osgeo.gdal et osgeo.osr indispensable à l'analyse de fichiers géospatiaux de type Raster).
## 6. Gestion des Erreurs et Robustesse (Mécanisme de Rollback)
La sécurité du stockage et la stabilité de l'environnement de l'utilisateur final sont garanties par des mécanismes de contrôle rigoureux :
 * **Mode d'exception GDAL :** Appel systématique à gdal.UseExceptions() en amont du traitement afin de capturer sous forme d'exceptions Python toute erreur interne de la bibliothèque GDAL (fichiers raster invalides ou corrompus).
 * **Rollback en cas d'erreur :** Si la copie physique du fichier se déroule normalement mais que l'analyse GDAL ou l'écriture du fichier de métadonnées échoue (par exemple, si l'utilisateur tente d'importer une image JPEG non géoréférencée à la place d'une Orthophoto), l'application exécute un nettoyage immédiat :
   * Suppression du fichier copié dans le répertoire cible.
   * Suppression du fichier .readme.md s'il a commencé à être rédigé sur le disque.
 * **Notifications utilisateur :** L'utilisateur est informé en temps réel par des boîtes de dialogue interactives (messagebox). Un message clair et détaillé s'affiche en cas d'anomalie critique, tandis qu'un pop-up de succès confirme la bonne exécution d'un import complet.
