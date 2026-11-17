"""Tests du lot 7 : lecture/écriture .urb et note de calcul (structurb.urb)."""

from pathlib import Path
import pytest

from structurb.catalogue import ouvrir_fichier_mat_surface, ouvrir_fichier_structures
from structurb.etude import dimensionner_etude
from structurb.urb import (
    ENTETE_URB_V1,
    ENTETE_URB_V2,
    EtudeUrb,
    ecrire_urb,
    formater_note_calcul,
    lire_urb,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_aller_retour_urb_v2_et_q2(tmp_path):
    etude = EtudeUrb(
        entete=ENTETE_URB_V2,
        titre="Giratoire RD 12 — Aménagement entrée Nord",
        type_voie="giratoire_distribution",
        qualite="Q2",
        variante="Variante 1",
        date="17/11/2026",
        trafic_initial="85",
        duree_service=20,
        croissance_pct=2,
        trafic_cumule="738370",
        combo_struct_idx=3,
        num_index_structure=50,
        util_fichier_perso=0,
        fichier_perso="",
        ind_mat_base=1,
        ind_mat_fondation=0,
        cam="0.5",
        indice_pf=2,
        ind_comp_q1=1,
        ind_comp_q2=0,
        hiver="HRNE",
        indice_station=26,  # Toulouse (base 1)
        altitude_agglo=150,
        taille_agglo=1,
        type_gel_sol=2,
        pente_sol="0.5",
        coef_a=0.12,
        epaisseur_non_gelive=20,
        format_version=2,
        indice_gel_perso=95,
        util_indice_gel_perso=1,
    )
    f = tmp_path / "test_etude.urb"
    ecrire_urb(f, etude)

    relue = lire_urb(f)
    assert relue.entete == ENTETE_URB_V2
    assert relue.titre == etude.titre
    assert relue.type_voie == "giratoire_distribution"
    assert relue.qualite == "Q2"
    assert relue.variante == "Variante 1"
    assert relue.duree_service == 20
    assert relue.croissance_pct == 2
    assert relue.num_index_structure == 50
    assert relue.cam == "0.5"
    assert relue.indice_pf == 2
    assert relue.hiver == "HRNE"
    assert relue.indice_station == 26
    assert relue.pente_sol == "0.5"
    assert relue.coef_a == pytest.approx(0.12, abs=1e-5)
    assert relue.indice_gel_perso == 95
    assert relue.util_indice_gel_perso == 1


def test_lire_urb_v1_beta_sans_derniere_ligne(tmp_path):
    contenu = "\n".join([
        f'"{ENTETE_URB_V1}"',
        '"Rue Principale"',
        '"###FinTitre###"',
        '2,"V1","01/01/2003"',
        '"50",20,2,"365000"',
        '0,2,0,""',
        '" 1 "," 0 "',
        '"0.1",2',
        '1,1',
        '2,26,148,0',
        '2,"0.5",0.12,20',
    ]) + "\n"
    f = tmp_path / "beta.urb"
    f.write_text(contenu, encoding="cp1252")
    relue = lire_urb(f)
    assert relue.entete == ENTETE_URB_V1
    assert relue.type_voie == "distribution"
    assert relue.qualite == "Q1"
    assert relue.format_version == 1
    assert relue.util_indice_gel_perso == 0


def test_lire_urb_entete_invalide(tmp_path):
    f = tmp_path / "bad.urb"
    f.write_text('"Pas un fichier urb"\n', encoding="cp1252")
    with pytest.raises(ValueError):
        lire_urb(f)
    with pytest.raises(FileNotFoundError):
        lire_urb(tmp_path / "absent.urb")


def test_formater_note_calcul():
    cat_str = ouvrir_fichier_structures(REPO_ROOT / "Certu.str")
    cat_mts = ouvrir_fichier_mat_surface(REPO_ROOT / "Certu.mts")
    s = cat_str.structures[49]  # Pavés/GNT
    res = dimensionner_etude(
        catalogue_structures=cat_str,
        catalogue_surfaces=cat_mts,
        structure=s,
        type_voie="desserte",
        trafic_initial_pl=12,
        croissance_pct=2,
        duree_ans=20,
        plate_forme="PF2",
        station="Toulouse",
        hiver="HRNE",
        taille_agglo="moyenne",
        pente_sol_pourcent=0.5,
    )
    etude = EtudeUrb(
        titre="Voirie lotissement",
        type_voie="desserte",
        qualite="Q1",
        variante="Base",
        date="17/11/2026",
    )
    md = formater_note_calcul(etude, res, structure=s)
    assert "Voirie lotissement" in md
    assert "Pavés/GNT" in md
    assert "20 849" in md or "20849" in md
    assert "30 000" in md or "30000" in md
    assert "Vérifiée" in md
