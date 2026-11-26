"""Outils déterministes généralistes pour le benchmark PLE."""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any

OBSOLETE_MARKERS = re.compile(r"(superseded|void|obsolete|archive|old_rev|deprecated)", re.I)

def scan_workspace(root: str = ".") -> dict[str, Any]:
    """Cartographie le workspace en séparant les documents actifs, les révisions périmées et les gabarits."""
    base = Path(root)
    active, superseded, templates = [], [], []
    for p in sorted(base.rglob("*")):
        if not p.is_file() or any(part.startswith(".") for part in p.parts):
            continue
        rel = str(p.relative_to(base))
        if OBSOLETE_MARKERS.search(rel):
            superseded.append(rel)
        elif any(k in p.name.lower() for k in ("example", "template", "contract", "schema")):
            templates.append(rel)
        else:
            active.append(rel)
    return {
        "active_files": active,
        "superseded_files_ignore": superseded,
        "reference_templates_and_contracts": templates,
    }

def audit_ifc(path: str) -> dict[str, Any]:
    """Vérifie la validité IFC4 et la tessellation 3D de chaque bâtiment."""
    import ifcopenshell
    import ifcopenshell.geom

    model = ifcopenshell.open(path)
    projects = model.by_type("IfcProject")
    buildings = model.by_type("IfcBuilding")
    if len(projects) != 1:
        return {"ok": False, "error": f"Expected 1 IfcProject, found {len(projects)}"}
    if not buildings:
        return {"ok": False, "error": "No IfcBuilding found"}

    settings = ifcopenshell.geom.settings()
    failed = []
    for b in buildings:
        try:
            ifcopenshell.geom.create_shape(settings, b)
        except Exception as exc:
            failed.append(f"{b.Name or b.GlobalId}: {exc}")

    if failed:
        return {"ok": False, "error": f"3D tessellation failed: {failed}"}
    return {"ok": True, "projects": 1, "buildings": len(buildings)}

def audit_xlsx(path: str) -> dict[str, Any]:
    """Vérifie qu'un classeur Excel ne contient aucune erreur de formule (#REF!, #VALUE!, etc.)."""
    import openpyxl

    wb = openpyxl.load_workbook(path, data_only=False)
    errors = []
    for name in wb.sheetnames:
        ws = wb[name]
        for row in ws.iter_rows(values_only=False):
            for cell in row:
                val = str(cell.value or "")
                if any(err in val for err in ("#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A", "#NUM!")):
                    errors.append(f"{name}!{cell.coordinate}={val}")
    if errors:
        return {"ok": False, "error": f"Excel formula errors: {errors[:10]}"}
    return {"ok": True, "sheets": wb.sheetnames}

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "scan"
    if cmd == "scan":
        print(json.dumps(scan_workspace(), indent=2))
    elif cmd == "audit_ifc" and len(sys.argv) > 2:
        print(json.dumps(audit_ifc(sys.argv[2]), indent=2))
    elif cmd == "audit_xlsx" and len(sys.argv) > 2:
        print(json.dumps(audit_xlsx(sys.argv[2]), indent=2))
