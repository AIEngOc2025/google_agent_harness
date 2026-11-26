# Module des outils d'interaction environnementale, d'extraction et de calcul

import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import pymupdf


def list_workspace_files(base_dir: str = ".") -> List[str]:
    """
    @definition : liste récursivement tous les fichiers du répertoire
    @args/params : base_dir (str) chemin du dossier racine à explorer
    @return : List[str] liste des chemins relatifs des fichiers trouvés
    """
    # exploration récursive des chemins
    fichiers = []
    base_path = Path(base_dir)
    for path in base_path.rglob("*"):
        # exclusion des fichiers cachés et environnements virtuels
        if path.is_file() and not any(p.startswith(".") for p in path.parts):
            fichiers.append(str(path.relative_to(base_path)))
    return sorted(fichiers)


def read_workspace_file(file_path: str, max_lines: int = 500) -> str:
    """
    @definition : lit et retourne le contenu textuel d'un fichier
    @args/params : file_path (str) chemin du fichier, max_lines (int) limite
    @return : str contenu textuel du fichier ou message d'erreur
    """
    # tentative de lecture sécurisée
    try:
        path = Path(file_path)
        if not path.exists():
            return f"Erreur : Le fichier {file_path} n'existe pas."
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = [f.readline() for _ in range(max_lines)]
        return "".join(lines)
    except Exception as exc:
        return f"Erreur lors de la lecture du fichier {file_path} : {exc}"


def write_workspace_file(file_path: str, content: str) -> str:
    """
    @definition : écrit ou met à jour le contenu d'un livrable
    @args/params : file_path (str) destination, content (str) contenu
    @return : str message confirmant l'écriture ou détaillant l'erreur
    """
    # création automatique des dossiers parents si nécessaire
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Succès : Le fichier {file_path} a été écrit avec succès."
    except Exception as exc:
        return f"Erreur lors de l'écriture du fichier {file_path} : {exc}"


def execute_python_code(
    code: str, timeout_seconds: int = 60
) -> Dict[str, Any]:
    """
    @definition : exécute un extrait Python pour des calculs d'ingénierie
    @args/params : code (str) code Python, timeout_seconds (int) durée limite
    @return : Dict[str, Any] statut de succès et flux de sortie
    """
    # exécution via l'interpréteur python du système
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Délai d'exécution dépassé ({timeout_seconds}s)",
            "returncode": -1,
        }
    except Exception as exc:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Erreur d'exécution : {exc}",
            "returncode": -1,
        }


def inspect_excel_file(file_path: str) -> Dict[str, Any]:
    """
    @definition : analyse la structure d'un classeur Excel
    @args/params : file_path (str) chemin du fichier Excel à inspecter
    @return : Dict[str, Any] résumé des feuilles et dimensions
    """
    # vérification de l'existence du fichier
    path = Path(file_path)
    if not path.exists():
        return {"error": f"Fichier non trouvé : {file_path}"}

    # inspection des métadonnées du classeur
    try:
        excel_file = pd.ExcelFile(path)
        summary = {"sheet_names": excel_file.sheet_names, "sheets": {}}

        # parcours des feuilles pour extraire les dimensions et colonnes
        for sheet in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet, nrows=5)
            summary["sheets"][sheet] = {
                "columns": [str(col) for col in df.columns],
                "sample_rows_count": len(df),
            }
        return summary
    except Exception as exc:
        return {"error": f"Erreur inspection {file_path} : {exc}"}


def read_excel_sheet(
    file_path: str,
    sheet_name: Optional[str] = None,
    max_rows: int = 50,
) -> str:
    """
    @definition : lit une feuille Excel et la formate en tableau markdown
    @args/params : file_path (str) chemin, sheet_name (str) feuille, max (int)
    @return : str contenu formaté en markdown ou message d'erreur
    """
    # chargement des données tabulaires
    try:
        path = Path(file_path)
        if not path.exists():
            return f"Erreur : Le fichier {file_path} n'existe pas."

        # lecture de la feuille spécifiée ou de la première feuille
        target_sheet = sheet_name if sheet_name else 0
        df = pd.read_excel(path, sheet_name=target_sheet, nrows=max_rows)

        # conversion des données en représentation markdown
        preview = df.to_markdown(index=False)
        total_rows = len(df)
        note = f"\n\n*(Affichage des {total_rows} premières lignes)*"
        return preview + note
    except Exception as exc:
        return f"Erreur lecture feuille {sheet_name} dans {file_path} : {exc}"


def inspect_pdf_file(file_path: str) -> Dict[str, Any]:
    """
    @definition : extrait les métadonnées et le nombre de pages d'un PDF
    @args/params : file_path (str) chemin du document PDF
    @return : Dict[str, Any] métadonnées descriptives et volume de pages
    """
    # ouverture du document PDF via PyMuPDF
    path = Path(file_path)
    if not path.exists():
        return {"error": f"Fichier introuvable : {file_path}"}

    try:
        doc = pymupdf.open(path)
        metadata = doc.metadata or {}
        page_count = len(doc)
        toc = doc.get_toc()
        doc.close()

        # structuration du rapport de synthèse
        return {
            "file_name": path.name,
            "total_pages": page_count,
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "table_of_contents_entries": len(toc),
        }
    except Exception as exc:
        msg = f"Erreur lors de l'inspection PDF {file_path} : {exc}"
        return {"error": msg}


def read_pdf_pages(
    file_path: str,
    start_page: int = 1,
    end_page: int = 5,
) -> str:
    """
    @definition : extrait le texte d'une plage de pages d'un PDF
    @args/params : file_path (str) chemin, start_page (int), end_page (int)
    @return : str texte extrait par page ou message d'erreur
    """
    # validation de l'existence du fichier
    path = Path(file_path)
    if not path.exists():
        return f"Erreur : Fichier non trouvé : {file_path}"

    try:
        doc = pymupdf.open(path)
        total_pages = len(doc)

        # ajustement des bornes de lecture
        start_idx = max(0, start_page - 1)
        end_idx = min(total_pages, end_page)

        # extraction du texte page par page
        extracted_sections = []
        for pno in range(start_idx, end_idx):
            page_text = doc[pno].get_text("text")
            header = f"--- Page {pno + 1} / {total_pages} ---"
            extracted_sections.append(f"{header}\n{page_text.strip()}")

        doc.close()
        return "\n\n".join(extracted_sections)
    except Exception as exc:
        return f"Erreur lecture pages PDF {file_path} : {exc}"


def search_pdf_text(
    file_path: str,
    query: str,
    max_matches: int = 10,
) -> str:
    """
    @definition : recherche des occurrences textuelles dans un PDF
    @args/params : file_path (str) chemin, query (str) motif, max_matches (int)
    @return : str résumé des occurrences trouvées avec numéros de page
    """
    # vérification du fichier PDF
    path = Path(file_path)
    if not path.exists():
        return f"Erreur : Fichier non trouvé : {file_path}"

    try:
        doc = pymupdf.open(path)
        matches = []

        # balayage de chaque page pour repérer le mot-clé
        for pno, page in enumerate(doc):
            text = page.get_text("text")
            if query.lower() in text.lower():
                # extraction d'un extrait de contexte
                start_pos = max(0, text.lower().find(query.lower()) - 80)
                end_pos = min(len(text), start_pos + 200)
                snippet = text[start_pos:end_pos].replace("\n", " ").strip()
                matches.append(f"Page {pno + 1} : ... {snippet} ...")

            if len(matches) >= max_matches:
                break

        doc.close()

        # mise en forme des résultats
        if not matches:
            return f"Aucune occurrence pour '{query}' dans {file_path}."
        title = f"Occurrences trouvées pour '{query}' ({len(matches)}) :"
        return title + "\n" + "\n".join(matches)
    except Exception as exc:
        return f"Erreur recherche dans {file_path} : {exc}"
