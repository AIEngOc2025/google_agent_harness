# Tests unitaires pour le module des outils src/tools.py

from pathlib import Path
import pandas as pd
import pymupdf

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


def test_file_operations(tmp_path: Path) -> None:
    """
    @definition : valide les opérations de lecture, écriture et listage
    @args/params : tmp_path (Path) répertoire temporaire fourni par pytest
    @return : None
    """
    # écriture d'un fichier de test
    fichier_test = tmp_path / "test.txt"
    res_ecriture = write_workspace_file(str(fichier_test), "Bonjour ingénieur")
    assert "Succès" in res_ecriture

    # lecture du fichier
    contenu = read_workspace_file(str(fichier_test))
    assert "Bonjour ingénieur" in contenu

    # listage des fichiers
    liste = list_workspace_files(str(tmp_path))
    assert "test.txt" in liste


def test_execute_python_code() -> None:
    """
    @definition : vérifie l'exécution déterministe d'un script python
    @args/params : None
    @return : None
    """
    # exécution d'un calcul physique élémentaire
    code = "import math; print(f'M_max={0.125 * 10 * 6**2}')"
    res = execute_python_code(code)
    assert res["success"] is True
    assert "M_max=45.0" in res["stdout"]


def test_excel_tools(tmp_path: Path) -> None:
    """
    @definition : valide l'inspection et la lecture d'un classeur Excel
    @args/params : tmp_path (Path) répertoire temporaire fourni par pytest
    @return : None
    """
    # création d'un classeur Excel de test
    excel_path = tmp_path / "calculs.xlsx"
    df = pd.DataFrame(
        {
            "Poutre": ["P1", "P2"],
            "Portee_m": [5.0, 7.5],
            "Charge_kN": [12.0, 18.0],
        }
    )
    df.to_excel(excel_path, sheet_name="Dimensionnement", index=False)

    # inspection de la structure
    summary = inspect_excel_file(str(excel_path))
    assert "Dimensionnement" in summary["sheet_names"]
    assert "Portee_m" in summary["sheets"]["Dimensionnement"]["columns"]

    # lecture tabulaire markdown
    markdown_out = read_excel_sheet(str(excel_path), "Dimensionnement")
    assert "Portee_m" in markdown_out
    assert "P1" in markdown_out


def test_pdf_tools(tmp_path: Path) -> None:
    """
    @definition : valide l'inspection, l'extraction et la recherche dans un PDF
    @args/params : tmp_path (Path) répertoire temporaire fourni par pytest
    @return : None
    """
    # génération d'un document PDF synthétique
    pdf_path = tmp_path / "plan_structure.pdf"
    doc = pymupdf.open()
    page1 = doc.new_page()
    page1.insert_text(
        (50, 72), "Projet de Structure : Contrainte admissible = 250 MPa."
    )
    page2 = doc.new_page()
    page2.insert_text(
        (50, 72), "Spécification acier S355 et section IPE 300."
    )
    doc.save(str(pdf_path))
    doc.close()

    # inspection des métadonnées
    meta = inspect_pdf_file(str(pdf_path))
    assert meta["total_pages"] == 2

    # lecture des pages
    texte_pages = read_pdf_pages(str(pdf_path), 1, 2)
    assert "Contrainte admissible" in texte_pages
    assert "IPE 300" in texte_pages

    # recherche ciblée
    recherche = search_pdf_text(str(pdf_path), "S355")
    assert "Page 2" in recherche
