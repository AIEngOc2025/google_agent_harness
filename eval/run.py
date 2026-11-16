# Script d'évaluation locale et de génération du dossier artifacts/

import os
import sys
import json
import time
from pathlib import Path

# ajout du dossier racine au chemin de résolution des modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import Dict, Any, List
from harness import execute_harness


def generate_task_artifact(task_id: str, discipline: str, result: Dict[str, Any], duration: float) -> Dict[str, Any]:
    """
    @definition : formate et structure l'artefact d'exécution d'une tâche pour l'archive artifacts/
    @args/params : task_id (str) identifiant unique de la tâche, discipline (str) domaine d'ingénierie, result (Dict[str, Any]) bilan d'exécution, duration (float) temps d'exécution en secondes
    @return : Dict[str, Any] métadonnées complètes de la tâche évaluée
    """
    # création du dictionnaire d'artefact
    return {
        "task_id": task_id,
        "discipline": discipline,
        "duration_seconds": round(duration, 3),
        "status": result.get("status", "INCONNU"),
        "iterations": result.get("iterations_used", 0),
        "deliverables": result.get("deliverables", []),
        "timestamp": time.time(),
    }


def run_evaluation(output_dir: str = "artifacts") -> Dict[str, Any]:
    """
    @definition : exécute le banc d'essai sur les tâches de développement et génère les artefacts requis
    @args/params : output_dir (str) chemin du répertoire où sauvegarder les artefacts
    @return : Dict[str, Any] synthèse statistique globale de l'évaluation
    """
    # création du dossier d'artefacts
    artifacts_path = Path(output_dir)
    artifacts_path.mkdir(parents=True, exist_ok=True)

    # liste représentative des disciplines de la compétition
    taches_dev = [
        {"id": "dev_task_01", "discipline": "Structure", "desc": "Calcul de charge et vérification de flexion d'une poutre IPE."},
        {"id": "dev_task_02", "discipline": "Civil", "desc": "Vérification des pertes de charge et dimensionnement d'un réseau hydraulique."},
        {"id": "dev_task_03", "discipline": "Électrique", "desc": "Bilan de puissance et calcul de chute de tension sur tableau basse tension."},
        {"id": "dev_task_04", "discipline": "Mécanique", "desc": "Analyse cinématique et choix d'un réducteur à engrenages."},
    ]

    resultats: List[Dict[str, Any]] = []
    temps_debut = time.time()

    # boucle d'évaluation des tâches
    for tache in taches_dev:
        t0 = time.time()
        res = execute_harness(task_description=tache["desc"])
        t1 = time.time()
        art = generate_task_artifact(
            task_id=tache["id"],
            discipline=tache["discipline"],
            result=res,
            duration=t1 - t0,
        )
        resultats.append(art)
        # sauvegarde individuelle par tâche dans artifacts/
        task_file = artifacts_path / f"{tache['id']}.json"
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(art, f, indent=2, ensure_ascii=False)

    temps_total = time.time() - temps_debut

    # calcul des métriques globales
    succes = sum(1 for r in resultats if r["status"] == "SUCCES")
    synthese = {
        "total_tasks": len(taches_dev),
        "successful_tasks": succes,
        "success_rate": round(succes / len(taches_dev), 3),
        "total_duration_seconds": round(temps_total, 3),
        "tasks": resultats,
    }

    # sauvegarde du fichier récapitulatif
    summary_file = artifacts_path / "summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(synthese, f, indent=2, ensure_ascii=False)

    return synthese


def main() -> None:
    """
    @definition : point d'entrée pour lancer le script d'évaluation en CLI
    @args/params : aucun
    @return : None
    """
    # exécution de l'évaluation
    print("Démarrage de l'évaluation baseline sur le dev set...")
    resume = run_evaluation(output_dir="artifacts")
    print(f"Évaluation terminée : {resume['successful_tasks']}/{resume['total_tasks']} succès.")
    print(f"Rapport sauvegardé dans le dossier 'artifacts/summary.json'.")


if __name__ == "__main__":
    main()
