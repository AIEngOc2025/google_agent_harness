# Point d'entrée serveur (serve.py) requis pour l'évaluation Kaggle PLE

import argparse
import json
import os
from typing import Any, Dict
from harness import execute_harness

try:
    import taskbridge
except ImportError:
    taskbridge = None


async def solve(session: Any) -> str:
    """
    @definition : résout une tâche d'ingénierie physique reçue via le protocole PLEBench
    @args/params : session (taskbridge.Session) session WebSocket de la tâche
    @return : str message final de synthèse pour l'évaluateur
    """
    # extraction de la tâche et du répertoire de travail
    task_desc = getattr(session, "task", None) or "Tâche d'ingénierie physique"
    workdir = getattr(session, "workdir", None) or "/app"

    # exécution du harnais d'ingénierie
    resultat = execute_harness(task_description=task_desc, workspace_dir=workdir)

    # journalisation dans la session
    if hasattr(session, "log"):
        await session.log("Harnais exécuté avec succès.")

    # retour de la synthèse finale
    return f"Tâche terminée: {resultat.get('status', 'ok')}"


def process_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    @definition : traite une requête locale en exécutant le harnais sur la tâche
    @args/params : payload (Dict[str, Any]) tâche et chemin du dossier
    @return : Dict[str, Any] résultat sérialisable pour la plateforme
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
    @definition : fonction principale pour le serveur WebSocket ou la CLI
    @args/params : aucun
    @return : None
    """
    # si la variable d'environnement PORT est définie, démarrer le serveur WebSocket
    if "PORT" in os.environ and taskbridge is not None:
        taskbridge.run(solve)
        return

    # analyse des arguments CLI pour exécution hors conteneur
    parser = argparse.ArgumentParser(
        description="Serveur du harnais d'agent Kaggle PLE"
    )
    parser.add_argument(
        "--task",
        type=str,
        default="Tâche test baseline d'ingénierie",
        help="Description de la tâche",
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default=".",
        help="Répertoire de travail de la tâche",
    )
    args = parser.parse_args()

    # exécution et affichage du résultat JSON
    req = {"task": args.task, "workspace_dir": args.workspace}
    response = process_request(req)
    print(json.dumps(response, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
