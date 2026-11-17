# Plan POC : Soumission Baseline pour Google Agent Harness (PLE)

Ce document consigne le plan d'expérimentation et d'implémentation de la baseline pour la compétition **Google - Agent Harness on Physical-Engineering's Last Exam (PLE)** sur Kaggle.

---

## 1. Objectifs du POC Baseline

1. **Conformité stricte aux exigences Kaggle / PLE** :
   - Mise en place des fichiers obligatoires à la racine : `submission.yaml`, `serve.py`, `harness.py`, `LICENSE` (Apache-2.0).
   - Création du répertoire `artifacts/` pour stocker les traces d'évaluation du *dev set*.
   - Validation via le vérificateur officiel (`uv run python -m kit check`).
2. **Architecture Agent ReAct Minimaliste** :
   - Boucle de décision avec sélection d'outils (lecture de plans et fichiers, exécution Python pour calculs déterministes, écriture de livrables).
   - Découplage propre : serveur (`serve.py`), moteur d'agent (`harness.py`), outils (`src/tools.py`), prompts (`src/prompt.py`).
3. **Respect des conventions de développement** :
   - Gestion d'environnement via `uv` (`/Users/mpaga/.local/bin/uv run ...`).
   - Normes PEP 8 et docstrings standardisées avec définition, args/params, et return.

---

## 2. Structure du Projet

```text
google_agent_harness/
├── pyproject.toml         # Gestion des dépendances du projet uv
├── LICENSE                # Licence Apache-2.0 obligatoire
├── submission.yaml        # Configuration du modèle et du point d'entrée
├── serve.py               # Serveur d'inférence requis pour l'évaluation Kaggle
├── harness.py             # Harnais d'agent et boucle de raisonnement
├── plan_baseline.md       # Consignation du plan et suivi d'exécution
├── src/
│   ├── __init__.py
│   ├── prompt.py          # Instructions système de la baseline
│   ├── tools.py           # Outils d'interaction environnement & calcul
│   └── agent.py           # Logique ReAct et orchestration de l'agent
├── artifacts/             # Traces d'exécution précalculées sur le dev set (< 512 Mio)
└── eval/
    ├── __init__.py
    └── run.py             # Script local d'évaluation sur les tâches de test
```

---

## 3. Étapes d'Exécution du Plan

- [x] **Étape 1 : Initialisation de l'environnement et métadonnées**
  - Création du `pyproject.toml` compatible Python 3.13.
  - Rédaction de la licence `LICENSE` (Apache-2.0).
  - Création des répertoires `src/`, `artifacts/`, `eval/`.
- [x] **Étape 2 : Configuration de la soumission (`submission.yaml`)**
  - Spécification du proxy et modèle autorisé : `google-cloud/gemini-3.8-flash`.
  - Configuration des timeouts (6 heures / tâche max).
- [x] **Étape 3 : Implémentation des briques de l'Agent Baseline**
  - `src/tools.py` : outillage de fichier et solveur Python avec docstrings conformes.
  - `src/prompt.py` : prompt système guidant l'agent dans la production de livrables d'ingénierie.
  - `harness.py` : implémentation de la boucle d'exécution de l'agent.
  - `serve.py` : écoute et point d'entrée officiel pour le harness runner de Kaggle.
- [x] **Étape 4 : Script d'évaluation locale et validation**
  - `eval/run.py` : exécution de scénarios de test avec génération d'artefacts.
  - Test unitaire et vérification de conformité via `uv run`.
- [x] **Étape 5 : Préparation du livrable Writeup**
  - Mesure du point d'ancrage baseline (temps, structure des traces, coût prévisionnel).

---

## 4. Résultats et Bilan de l'Exécution du POC

L'ensemble des étapes a été exécuté avec succès :

| Composant | Fichier / Répertoire | Statut | Détails |
|---|---|---|---|
| **Licence Open Source** | `LICENSE` | Validé | Apache-2.0 conforme aux règles de la compétition |
| **Config Soumission** | `submission.yaml` | Validé | Modèle proxy `google-cloud/gemini-3.8-flash` configuré |
| **Harnais d'Agent** | `harness.py` | Validé | Boucle ReAct avec observation, outils et génération de livrables |
| **Point d'Entrée Serveur** | `serve.py` | Validé | Interface CLI/JSON testée via `uv run` |
| **Outils de l'Agent** | `src/tools.py` | Validé | Primitives de lecture/écriture et solveur Python (docstrings PyEPL) |
| **Banc d'Évaluation** | `eval/run.py` | Validé | Évaluation de 4 tâches modèles exécutée avec succès (100% de succès baseline) |
| **Archive des Traces** | `artifacts/` | Validé | Traces JSON individuelles et `summary.json` générés (< 512 Mio) |

### Commande de test du serveur :
```bash
/Users/mpaga/.local/bin/uv run --no-sync python serve.py --task "Dimensionnement poutre métallique"
```

### Commande d'évaluation baseline :
```bash
/Users/mpaga/.local/bin/uv run --no-sync python eval/run.py
```

