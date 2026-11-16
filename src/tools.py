# Module des outils d'interaction environnementale et calculatoire pour l'agent

import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any


def list_workspace_files(base_dir: str = ".") -> List[str]:
    """
    @definition : liste récursivement tous les fichiers présents dans le répertoire de travail
    @args/params : base_dir (str) chemin du dossier racine à explorer
    @return : List[str] liste des chemins relatifs des fichiers trouvés
    """
    # exploration récursive des chemins
    fichiers = []
    base_path = Path(base_dir)
    for path in base_path.rglob("*"):
        # exclusion des fichiers cachés et environnements virtuels
        if path.is_file() and not any(part.startswith(".") for part in path.parts):
            fichiers.append(str(path.relative_to(base_path)))
    return sorted(fichiers)


def read_workspace_file(file_path: str, max_lines: int = 500) -> str:
    """
    @definition : lit et retourne le contenu textuel d'un fichier du workspace
    @args/params : file_path (str) chemin du fichier à lire, max_lines (int) nombre maximal de lignes
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
    @definition : écrit ou met à jour le contenu d'un fichier de livrable
    @args/params : file_path (str) chemin de destination, content (str) contenu à écrire
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


def execute_python_code(code: str, timeout_seconds: int = 60) -> Dict[str, Any]:
    """
    @definition : exécute un extrait de code Python dans un sous-processus isolé pour des calculs d'ingénierie
    @args/params : code (str) code Python à exécuter, timeout_seconds (int) durée limite d'exécution
    @return : Dict[str, Any] dictionnaire contenant le code de retour, la sortie stdout et stderr
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
