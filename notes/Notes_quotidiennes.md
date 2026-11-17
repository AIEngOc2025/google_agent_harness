# Note quotidienne – 16 novembre 2026

## Résumé de la journée

- **Mise à jour du projet** :
  - Ajout d’un `README.md` et correction du `pyproject.toml` pour que le build via `uv` fonctionne.
  - Installation des dépendances de développement (`pytest`, `black`, `flake8`).
- **Vérification de l’architecture minimale** :
  - Lancement du serveur `serve.py` avec succès, génération du `rapport_technique_livrable.txt`.
- **Création du notebook EDA** :
  - Génération du fichier `kaggle_eda.ipynb` contenant :
    - Installation des librairies nécessaires (`pandas`, `openpyxl`, `pymupdf`, `ifcopenshell`) via `uv`.
    - Fonction `list_files` pour lister les fichiers du dépôt.
    - Chargement et affichage d’un fichier Excel d’exemple.
    - Extraction de métadonnées PDF avec PyMuPDF.
    - Inspection optionnelle d’un fichier IFC.
  - Ajout de commentaires et de docstrings conformes aux conventions de l’utilisateur.
- **Prochaines étapes suggérées** :
  - Tester le notebook dans un kernel Kaggle.
  - Enrichir l’EDA (visualisations, nettoyage de données).
  - Commiter les changements dans le dépôt Git.

---

# Note quotidienne – 17 novembre 2026

## Résumé de la session

- **Enrichissement de l'outillage d'ingénierie (`src/tools.py`)** :
  - Ajout de solveurs et extracteurs ciblés :
    - `inspect_excel_file` et `read_excel_sheet` (avec pagination markdown).
    - `inspect_pdf_file`, `read_pdf_pages` et `search_pdf_text` (PyMuPDF).
    - Maintien des outils d'exécution déterministe Python et fichiers.
- **Mise à jour du prompt système (`src/prompt.py`)** :
  - Intégration du catalogue des 9 outils disponibles.
  - Formalisation du protocole en 4 phases : Inspection, Targeted Retrieval, Calculs Déterministes, Livrable & Audit.
- **Évolution du moteur de harnais (`harness.py`)** :
  - Ajout du routeur dynamique d'outils `dispatch_tool`.
  - Catégorisation automatique des fichiers (`classify_workspace_files`).
  - Boucle ReAct avancée avec inspections ciblées, calcul Python, rédaction de livrable et boucle d'audit déterministe (*code-gated audit loop*).
- **Contrôle qualité et conformité** :
  - 100 % conforme aux règles utilisateur : docstrings standardisées (`@definition`, `@args/params`, `@return`), commentaires explicatifs `#`.
  - Conformité PEP 8 / PyEPL validée avec `flake8` sur l'ensemble du projet (0 erreur).
  - 7 tests unitaires passés avec succès sous `pytest` (0.47s).
