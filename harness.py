"""Orchestrateur principal compatible avec taskbridge.Session (RPC distant) et src/."""

import os
import sys
import json
import time
import base64
import inspect
import tempfile
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import openai
import taskbridge

from src.prompt import SYSTEM_PROMPT
from src.tools import (
    list_workspace_files,
    read_workspace_file,
    write_workspace_file,
    execute_python_code,
    inspect_excel_file,
    read_excel_sheet,
    inspect_pdf_file,
    read_pdf_pages,
    search_pdf_text,
)
from src.ple_hybrid_harness import (
    PLEHarnessConfig,
    DocumentMetadataIndexer,
    HardConstraintGateVerifier,
    DeliverablePackager,
)


class AgentError(RuntimeError):
    """Exception levée en cas d'échec ou de dépassement des limites de l'agent."""


TOOL_FUNCTIONS: Dict[str, Callable[..., Any]] = {
    "list_workspace_files": list_workspace_files,
    "read_workspace_file": read_workspace_file,
    "write_workspace_file": write_workspace_file,
    "execute_python_code": execute_python_code,
    "inspect_excel_file": inspect_excel_file,
    "read_excel_sheet": read_excel_sheet,
    "inspect_pdf_file": inspect_pdf_file,
    "read_pdf_pages": read_pdf_pages,
    "search_pdf_text": search_pdf_text,
}


def get_openai_tools_schema() -> List[Dict[str, Any]]:
    """Définit le schéma Function Calling pour taskbridge et src/tools.py."""
    return [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Lit un fichier texte dans l'espace de travail de la tâche.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Chemin relatif du fichier"}
                    },
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Écrit un fichier dans l'espace de travail de la tâche.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Chemin relatif du fichier"},
                        "content": {"type": "string", "description": "Contenu textuel à écrire"},
                    },
                    "required": ["path", "content"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_workspace_files",
                "description": "Liste récursivement tous les fichiers du répertoire de travail.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "base_dir": {"type": "string", "description": "Dossier racine (défaut: '.')"}
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read_workspace_file",
                "description": "Lit le contenu textuel d'un fichier.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Chemin du fichier"},
                        "max_lines": {"type": "integer", "description": "Nombre max de lignes"},
                    },
                    "required": ["file_path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "write_workspace_file",
                "description": "Écrit ou met à jour le contenu d'un fichier livrable.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Chemin de destination"},
                        "content": {"type": "string", "description": "Contenu à écrire"},
                    },
                    "required": ["file_path", "content"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "execute_python_code",
                "description": "Exécute du code Python pour des calculs physiques ou la génération de livrables.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code Python complet"},
                        "timeout_seconds": {"type": "integer", "description": "Délai limite en secondes"},
                    },
                    "required": ["code"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "inspect_excel_file",
                "description": "Analyse les onglets et colonnes d'un classeur Excel.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Chemin du fichier Excel"},
                    },
                    "required": ["file_path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read_excel_sheet",
                "description": "Lit une feuille Excel au format markdown.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Chemin du fichier Excel"},
                        "sheet_name": {"type": "string", "description": "Nom de la feuille"},
                        "max_rows": {"type": "integer", "description": "Nombre max de lignes"},
                    },
                    "required": ["file_path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "inspect_pdf_file",
                "description": "Extrait les métadonnées et le nombre de pages d'un PDF.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Chemin du document PDF"},
                    },
                    "required": ["file_path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read_pdf_pages",
                "description": "Extrait le texte d'une plage de pages d'un PDF.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Chemin du PDF"},
                        "start_page": {"type": "integer", "description": "Page de début"},
                        "end_page": {"type": "integer", "description": "Page de fin"},
                    },
                    "required": ["file_path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_pdf_text",
                "description": "Recherche des occurrences textuelles dans un PDF.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Chemin du PDF"},
                        "query": {"type": "string", "description": "Mot-clé recherché"},
                        "max_matches": {"type": "integer", "description": "Nombre max de résultats"},
                    },
                    "required": ["file_path", "query"],
                },
            },
        },
    ]


def _resolve_path(raw_path: str, work_dir: Path) -> Path:
    p = Path(raw_path)
    return p if p.is_absolute() else (work_dir / p)


async def run_tool(
    session: Any,
    name: str,
    raw_arguments: str,
    work_dir: Optional[Path] = None,
) -> str:
    """
    Exécute un outil (natif taskbridge ou src/tools.py) et retourne toujours une chaîne,
    préfixée par 'Tool error:' en cas d'exception ou d'arguments invalides.
    """
    try:
        args = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
        if not isinstance(args, dict):
            return "Tool error: arguments must be a JSON object."
    except Exception as exc:
        return f"Tool error: invalid JSON arguments ({exc})."

    base_dir = Path(work_dir) if work_dir else Path(getattr(session, "workdir", None) or os.getcwd())

    # 1. Outils natifs du protocole taskbridge (read_file / write_file / bash)
    if name == "read_file":
        rel_path = args.get("path")
        if not rel_path:
            return "Tool error: 'path' is required."
        try:
            if hasattr(session, "read_file"):
                res = await session.read_file(rel_path)
                if isinstance(res, bytes):
                    return res.decode("utf-8", errors="replace")
                if isinstance(res, dict) and "content_b64" in res:
                    return base64.b64decode(res["content_b64"]).decode("utf-8", errors="replace")
                return str(res)
            target = _resolve_path(rel_path, base_dir)
            return target.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            return f"Tool error: {exc}"

    if name == "write_file":
        rel_path = args.get("path")
        content = args.get("content", "")
        if not rel_path:
            return "Tool error: 'path' is required."
        try:
            if hasattr(session, "write_file"):
                data = content.encode("utf-8") if isinstance(content, str) else content
                await session.write_file(rel_path, data)
                return f"Wrote {rel_path} ({len(data)} bytes)."
            target = _resolve_path(rel_path, base_dir)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return f"Wrote {rel_path}."
        except Exception as exc:
            return f"Tool error: {exc}"

    # 2. Outils spécialisés de src/tools.py
    func = TOOL_FUNCTIONS.get(name)
    if func is None:
        return f"Tool error: unknown tool '{name}'."

    if "file_path" in args and isinstance(args["file_path"], str):
        args["file_path"] = str(_resolve_path(args["file_path"], base_dir))
    if name == "list_workspace_files":
        args["base_dir"] = str(_resolve_path(args.get("base_dir", "."), base_dir))

    prev_cwd = os.getcwd()
    try:
        if base_dir.exists():
            os.chdir(base_dir)
        sig = inspect.signature(func)
        valid_args = {k: v for k, v in args.items() if k in sig.parameters}
        result = func(**valid_args)
    except Exception as exc:
        return f"Tool error: {exc}"
    finally:
        if Path(prev_cwd).exists():
            os.chdir(prev_cwd)

    if isinstance(result, str):
        return result[:12000]
    return json.dumps(result, ensure_ascii=False)[:12000]


async def run_agent(
    session: Any,
    client: Any,
    model: str,
    max_turns: int = 120,
) -> str:
    """Boucle d'exécution principale compatible avec taskbridge et les tests synthétiques."""
    if hasattr(session, "time_left"):
        remaining = session.time_left()
        if remaining is not None and remaining <= 0:
            raise AgentError("Execution deadline expired before start.")

    raw_workdir = getattr(session, "workdir", None) or os.getcwd()
    work_dir = Path(raw_workdir)
    local_exists = work_dir.exists()

    instruction = (
        getattr(session, "instruction", None)
        or getattr(session, "prompt", None)
        or ""
    )

    # Initialisation de l'architecture hybride PLE (Couches 1 à 5)
    config = PLEHarnessConfig(work_dir=work_dir)
    if not local_exists:
        # Cas d'une session RPC distante pure (sans système de fichiers local partagé)
        tmp_scratch = Path(tempfile.mkdtemp(prefix="ple_scratch_"))
        config.SCRATCH_DIR = tmp_scratch

    config.SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    indexer = DocumentMetadataIndexer(config.ENVIRONMENT_DIR)
    project_index = indexer.build_index() if local_exists else {"total_files": 0, "files": []}
    initial_files = {f["rel_path"] for f in project_index.get("files", [])}

    verifier = HardConstraintGateVerifier(config.SCRATCH_DIR)
    packager = DeliverablePackager(config.OUTPUT_DIR, initial_files)

    resolved_str = str(work_dir.resolve()) if local_exists else str(work_dir)
    enriched_system_prompt = f"""{SYSTEM_PROMPT}

--- ENVIRONNEMENT ET CARTOGRAPHIE (Couche 2) ---
Répertoire de travail : {resolved_str}
Inventaire des fichiers locaux :
{json.dumps(project_index, indent=2)}

--- PROTOCOLE DE VALIDATION (Couches 4 & 5) ---
Avant de conclure, assure-toi que tous les livrables demandés ont été générés et validés."""

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": enriched_system_prompt},
        {"role": "user", "content": instruction},
    ]

    tools_schema = get_openai_tools_schema()
    start_time = time.time()
    max_duration = config.MAX_EXECUTION_TIME_SEC - 600

    for turn in range(max_turns):
        if turn in (7, 13):  # Tours 8 et 14 (0-indexed)
            _sub_files = list((Path(session.workdir) / "submission").glob("*")) if (Path(session.workdir) / "submission").is_dir() else []
            if not any(f.is_file() and f.stat().st_size > 50 for f in _sub_files):
                messages.append({
                    "role": "user",
                    "content": (
                        f"[MILESTONE PACING CHECK - Turn {turn + 1}]: Stop exploratory snippets now. "
                        "Write and run a complete Python script that solves all constraints and generates the required deliverable file(s) on disk immediately, so you have time to run deterministic verification and refine."
                    ),
                })
        if hasattr(session, "time_left"):
            remaining = session.time_left()
            if remaining is not None and remaining <= 0:
                raise AgentError("Execution deadline exceeded.")
        if (time.time() - start_time) >= max_duration:
            raise AgentError("Maximum execution time budget exceeded.")

        if len(messages) > 28:
            messages = (
                messages[:2]
                + [
                    {
                        "role": "user",
                        "content": "[NOTE SYSTÈME] Historique compacté. Poursuis à partir des fichiers de l'espace de travail.",
                    }
                ]
                + messages[-22:]
            )

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools_schema,
            tool_choice="auto",
        )
        choice = response.choices[0]
        msg = choice.message
        finish_reason = getattr(choice, "finish_reason", "stop")

        tool_calls = getattr(msg, "tool_calls", None)
        content = getattr(msg, "content", None)

        assistant_record: Dict[str, Any] = {"role": "assistant"}
        if content is not None:
            assistant_record["content"] = content
        if tool_calls:
            assistant_record["tool_calls"] = [
                tc.model_dump() if hasattr(tc, "model_dump") else {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in tool_calls
            ]
        messages.append(assistant_record)

        if tool_calls:
            for tc in tool_calls:
                tool_output = await run_tool(
                    session,
                    tc.function.name,
                    tc.function.arguments,
                    work_dir=work_dir,
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_output,
                    }
                )
            continue

        # Validation stricte de la réponse finale (exigée par test_harness.py)
        if finish_reason not in ("stop", None):
            raise AgentError(f"Unexpected finish_reason: {finish_reason}")
        if not content or not str(content).strip():
            raise AgentError("Empty final response from model.")

        # Vérification locale des livrables et de la porte G = 1 si le dossier local existe
        if local_exists and config.STRICT_SAFETY_GATE_G:
            audit = packager.validate_deliverables()
            if not audit["all_valid"]:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "[BLOCAGE LIVRABLES] Aucun nouveau fichier livrable non vide détecté. "
                            "Génère les fichiers demandés avant de conclure."
                        ),
                    }
                )
                continue

            gate_report = config.SCRATCH_DIR / "gate_report.json"
            if gate_report.exists():
                gate = verifier.verify_hard_constraints()
                if not gate["passed"]:
                    messages.append(
                        {
                            "role": "user",
                            "content": f"[BLOCAGE SÉCURITÉ G=0] {gate['reason']} Corrige avant de conclure.",
                        }
                    )
                    continue

        return str(content)

    raise AgentError(f"Agent exceeded turn limit ({max_turns}).")
