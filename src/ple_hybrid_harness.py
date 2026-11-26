"""Couches d'infrastructure du harnais hybride PLE (synchronisées avec harness.py)."""

import sys
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class PLEHarnessConfig:
    """Couche 1 : Configuration globale des répertoires et budgets du harnais PLE."""

    MAX_EXECUTION_TIME_SEC: int = 21600  # Budget strict de 6 heures d'agent
    STRICT_SAFETY_GATE_G: bool = True

    def __init__(
        self,
        work_dir: Optional[Path] = None,
        scratch_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
    ):
        base = Path(work_dir).resolve() if work_dir else Path("/workspace/knowledge")
        self.ENVIRONMENT_DIR: Path = base
        self.SCRATCH_DIR: Path = (
            Path(scratch_dir).resolve() if scratch_dir else (base / ".ple_scratch")
        )
        self.OUTPUT_DIR: Path = (
            Path(output_dir).resolve() if output_dir else base
        )


class DocumentMetadataIndexer:
    """Couche 2 : Indexation et détection des fichiers distracteurs de l'environnement."""

    DISTRACTOR_KEYWORDS = ("superseded", "old", "obsolete", "draft", "deprecated", "archive")

    def __init__(self, root_dir: Path):
        self.root_dir = Path(root_dir)
        self.inventory: Dict[str, Any] = {}

    def build_index(self) -> Dict[str, Any]:
        """Scanne récursivement le dossier de travail en ignorant les dossiers cachés."""
        file_list: List[Dict[str, Any]] = []
        if self.root_dir.exists():
            for path in sorted(self.root_dir.rglob("*")):
                if not path.is_file():
                    continue
                rel_parts = path.relative_to(self.root_dir).parts
                if any(part.startswith(".") or part == "__pycache__" for part in rel_parts):
                    continue

                lower_name = path.name.lower()
                is_distractor = any(kw in lower_name for kw in self.DISTRACTOR_KEYWORDS)
                file_list.append(
                    {
                        "rel_path": str(path.relative_to(self.root_dir)),
                        "extension": path.suffix.lower(),
                        "size_bytes": path.stat().st_size,
                        "is_distractor": is_distractor,
                    }
                )

        self.inventory = {
            "total_files": len(file_list),
            "formats": sorted({f["extension"] for f in file_list}),
            "files": file_list,
        }
        return self.inventory


class CodeAsActionExecutor:
    """Couche 3 : Moteur d'exécution de scripts Python dans le contexte de la tâche."""

    @staticmethod
    def run_script(
        script_path: Path,
        cwd: Optional[Path] = None,
        timeout_sec: int = 300,
    ) -> Dict[str, Any]:
        """Exécute un script Python et capture stdout/stderr de manière bornée."""
        run_cwd = str(cwd) if cwd else str(script_path.parent)
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=run_cwd,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                check=False,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout[-4000:],
                "stderr": result.stderr[-4000:],
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Timeout d'exécution dépassé ({timeout_sec}s).",
                "returncode": -1,
            }
        except Exception as exc:
            return {"success": False, "error": str(exc), "returncode": -1}


class HardConstraintGateVerifier:
    """Couche 4 : Vérificateur local garantissant la porte logique éliminatoire G = 1."""

    def __init__(self, scratch_dir: Path, requirements_file: Optional[Path] = None):
        self.scratch_dir = Path(scratch_dir)
        self.requirements_file = requirements_file

    def verify_hard_constraints(
        self, calculation_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Contrôle le bilan d'audit physique (.ple_scratch/gate_report.json) ou un dictionnaire fourni.
        Retourne {'passed': bool, 'reason': str, 'details': dict}.
        """
        data = calculation_results
        if data is None:
            report_path = self.scratch_dir / "gate_report.json"
            if not report_path.exists():
                return {
                    "passed": False,
                    "reason": (
                        "Fichier .ple_scratch/gate_report.json manquant. "
                        "Exécute un script de vérification physique et enregistre ce bilan JSON avant de conclure."
                    ),
                    "details": {},
                }
            try:
                data = json.loads(report_path.read_text(encoding="utf-8"))
            except Exception as exc:
                return {
                    "passed": False,
                    "reason": f"Erreur de lecture dans gate_report.json : {exc}",
                    "details": {},
                }

        if not isinstance(data, dict):
            return {
                "passed": False,
                "reason": "Le contenu de gate_report.json doit être un objet JSON.",
                "details": {},
            }

        clash_free = data.get("clash_count", 0) == 0
        schema_ok = data.get("schema_valid", True) is True
        code_limits_ok = data.get("all_code_limits_respected", True) is True
        voltage_drop_ok = data.get("max_voltage_drop_pct", 0.0) <= 3.0
        thermal_limit_ok = data.get("max_temperature_c", 0.0) <= 90.0

        gate_g = (
            clash_free
            and schema_ok
            and code_limits_ok
            and voltage_drop_ok
            and thermal_limit_ok
        )
        return {
            "passed": gate_g,
            "details": data,
            "reason": "OK"
            if gate_g
            else "Violation d'une contrainte physique ou normative stricte (G = 0).",
        }


class DeliverablePackager:
    """Couche 5 : Audit final des livrables générés dans le répertoire de sortie."""

    def __init__(self, output_dir: Path, initial_files: Optional[Set[str]] = None):
        self.output_dir = Path(output_dir)
        self.initial_files: Set[str] = set(initial_files) if initial_files else set()

    def validate_deliverables(
        self, expected_files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Vérifie la présence et la taille (> 0 octet) des livrables attendus,
        ou détecte automatiquement les nouveaux fichiers créés hors dossiers cachés.
        """
        if expected_files:
            status: Dict[str, Any] = {}
            all_valid = True
            for file_name in expected_files:
                target_path = self.output_dir / file_name
                exists = target_path.exists() and target_path.is_file()
                size = target_path.stat().st_size if exists else 0
                is_valid = exists and size > 0
                status[file_name] = {
                    "exists": exists,
                    "size_bytes": size,
                    "valid": is_valid,
                }
                if not is_valid:
                    all_valid = False
            return {"all_valid": all_valid, "details": status}

        created_files: List[str] = []
        if self.output_dir.exists():
            for path in sorted(self.output_dir.rglob("*")):
                if not path.is_file():
                    continue
                rel_parts = path.relative_to(self.output_dir).parts
                if any(part.startswith(".") or part == "__pycache__" for part in rel_parts):
                    continue
                rel_str = str(path.relative_to(self.output_dir))
                if rel_str not in self.initial_files and path.stat().st_size > 0:
                    created_files.append(rel_str)

        return {
            "all_valid": len(created_files) > 0,
            "created_files": created_files,
        }
