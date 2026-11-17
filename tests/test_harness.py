# Tests unitaires pour le moteur du harnais (harness.py)

from pathlib import Path
import pandas as pd
import pymupdf

from harness import (
    dispatch_tool,
    classify_workspace_files,
    execute_harness,
)


def test_dispatch_tool_execution() -> None:
    """
    @definition : valide le routage dynamique et l'exécution d'un outil
    @args/params : None
    @return : None
    """
    # test d'un outil enregistré
    res = dispatch_tool("execute_python_code", code="print(2 + 2)")
    assert res["success"] is True
    assert "4" in res["stdout"]

    # test d'un outil inexistant
    err = dispatch_tool("outil_inconnu")
    assert "Erreur" in err


def test_classify_workspace_files() -> None:
    """
    @definition : vérifie la catégorisation des fichiers d'ingénierie
    @args/params : None
    @return : None
    """
    # simulation d'un ensemble de fichiers hétérogènes
    fichiers = ["plan.pdf", "data.xlsx", "calcul.py", "notes.txt"]
    categories = classify_workspace_files(fichiers)
    assert "plan.pdf" in categories["pdf"]
    assert "data.xlsx" in categories["excel"]
    assert "calcul.py" in categories["code"]
    assert "notes.txt" in categories["other"]


def test_harness_full_pipeline(tmp_path: Path) -> None:
    """
    @definition : valide le cycle ReAct complet avec inspection PDF et Excel
    @args/params : tmp_path (Path) dossier temporaire pour la simulation
    @return : None
    """
    # création d'un document PDF dans le dossier de travail
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Note de calcul préliminaire")
    doc.save(str(tmp_path / "plan.pdf"))
    doc.close()

    # création d'un fichier Excel dans le dossier de travail
    df = pd.DataFrame({"Section": ["HEA 200"], "Poids": [42.3]})
    df.to_excel(tmp_path / "profils.xlsx", index=False)

    # exécution du harnais d'agent
    res = execute_harness(
        task_description="Dimensionner la structure métallique",
        workspace_dir=str(tmp_path),
    )

    # vérification des statuts et livrables
    assert res["status"] == "SUCCES"
    assert "rapport_technique_livrable.txt" in res["deliverables"]
    assert res["observations_count"] >= 3

    # vérification du contenu du rapport généré
    rapport = (tmp_path / "rapport_technique_livrable.txt").read_text()
    assert "plan.pdf" in rapport
    assert "profils.xlsx" in rapport
    assert "Moment_max=45.0 kNm" in rapport
