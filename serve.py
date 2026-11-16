# Point d'entrée serveur (serve.py) requis pour l'évaluation Kaggle PLE

import sys
import json
import argparse
from typing import Dict, Any
from harness import execute_harness


def process_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    @definition : traite une requête d'évaluation Kaggle en exécutant le harnais sur la tâche reçue
    @args/params : payload (Dict[str, Any]) dictionnaire contenant la tâche et le chemin du dossier
    @return : Dict[str, Any] résultat sérialisable retourné à la plateforme d'évaluation
    """
    # extraction des paramètres de la requête
    task = payload.get("task", "Tâche d'ingénierie physique non spécifiée")
    workspace = payload.get("workspace_dir", ".")

    # exécution du harnais
    resultat = execute_harness(task_description=task, workspace_dir=workspace)
    return {
        "status": "ok",
        "result": resultat,
    }


def main() -> None:
    """
    @definition : fonction principale pour le serveur d'inférence en ligne de commande
    @args/params : aucun (arguments récupérés via sys.argv)
    @return : None
    """
    # analyse des arguments CLI
    parser = argparse.ArgumentParser(description="Serveur du harnais d'agent Kaggle PLE")
    parser.add_argument("--task", type=str, default="Tâche test baseline d'ingénierie", help="Description de la tâche")
    parser.add_argument("--workspace", type=str, default=".", help="Répertoire de travail de la tâche")
    args = parser.parse_args()

    # exécution et affichage du résultat JSON
    response = process_request({"task": args.task, "workspace_dir": args.workspace})
    print(json.dumps(response, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
