# Générateur de dossier de tâche d'ingénierie type pour tests locaux

from pathlib import Path
import pandas as pd
import pymupdf


def generate_sample_task_data(output_dir: str = "data/dev_task_demo") -> None:
    """
    @definition : génère un jeu complet de fichiers (PDF, Excel, CSV)
    @args/params : output_dir (str) répertoire cible où créer les fichiers
    @return : None
    """
    # création du dossier cible
    task_dir = Path(output_dir)
    task_dir.mkdir(parents=True, exist_ok=True)

    # 1. génération du classeur Excel de dimensionnement
    excel_path = task_dir / "catalogue_profils_aciers.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df_profils = pd.DataFrame(
            {
                "Designation": ["IPE 180", "IPE 200", "IPE 240", "IPE 300"],
                "Hauteur_h_mm": [180, 200, 240, 300],
                "Largeur_b_mm": [91, 100, 120, 150],
                "Inertie_Iy_cm4": [1317, 1943, 3892, 8356],
                "Module_Wy_cm3": [146.3, 194.3, 324.3, 557.1],
                "Masse_kg_m": [18.8, 22.4, 30.7, 42.2],
            }
        )
        df_profils.to_excel(writer, sheet_name="Profils_IPE", index=False)

        df_charges = pd.DataFrame(
            {
                "Cas": ["G", "Q", "S"],
                "Charge_kN_m": [4.5, 12.0, 3.2],
                "Coef_ELS": [1.0, 1.0, 0.9],
                "Coef_ELU": [1.35, 1.5, 1.5],
            }
        )
        df_charges.to_excel(writer, sheet_name="Charges", index=False)

    # 2. génération de la note de calcul et spécifications PDF
    pdf_path = task_dir / "cahier_des_charges_structure.pdf"
    doc = pymupdf.open()

    # page 1 : données du projet et géométrie
    page1 = doc.new_page()
    page1.insert_text(
        (50, 72),
        "Cahier des Charges Techniques - Bâtiment Industriel Hall A\n"
        "Discipline : Structure Métallique & Génie Civil\n\n"
        "1. Géométrie de l'ouvrage :\n"
        "- Portée entre appuis (L) : 6.00 m\n"
        "- Entraxe des portiques : 5.00 m\n"
        "- Nuance d'acier spécifiée : S355 (fy = 355 MPa, E = 210000 MPa)\n",
    )

    # page 2 : critères d'admissibilité et normes
    page2 = doc.new_page()
    page2.insert_text(
        (50, 72),
        "2. Critères de performance Eurocode 3 :\n"
        "- Flèche maximale admissible à l'ELS : w_max = L / 300 = 20.0 mm\n"
        "- Moment fléchissant de calcul à l'ELU : M_Ed = 1.35*G + 1.5*Q\n"
        "- Résistance plastique minimale requise : M_pl_Rd >= M_Ed\n\n"
        "3. Livrables requis :\n"
        "- Sélection du profilé optimal (rapport poids/inertie)\n"
        "- Vérification ELS et ELU avec justifications numériques\n",
    )
    doc.save(str(pdf_path))
    doc.close()

    # 3. génération d'un relevé capteurs CSV
    csv_path = task_dir / "releve_charges_essais.csv"
    df_capteurs = pd.DataFrame(
        {
            "Capteur_ID": [f"CAPT_0{i}" for i in range(1, 6)],
            "Position_x_m": [1.0, 2.0, 3.0, 4.0, 5.0],
            "Deformation_micro_def": [120, 245, 310, 240, 115],
            "Statut": ["OK", "OK", "OK", "OK", "OK"],
        }
    )
    df_capteurs.to_csv(csv_path, index=False)


if __name__ == "__main__":
    generate_sample_task_data()
    print("Dossier data/dev_task_demo généré avec succès.")
