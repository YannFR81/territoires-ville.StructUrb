"""Tests du lot 5 : orchestrateur d'étude complète (structurb.etude)."""

from pathlib import Path
import pytest

from structurb.catalogue import ouvrir_fichier_mat_surface, ouvrir_fichier_structures
from structurb.etude import (
    TYPES_STRUCTURE,
    compositions_surface_compatibles,
    dimensionner_etude,
    structures_compatibles,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CERTU_STR = REPO_ROOT / "Certu.str"
CERTU_MTS = REPO_ROOT / "Certu.mts"


@pytest.fixture(scope="module")
def catalogues():
    return ouvrir_fichier_structures(CERTU_STR), ouvrir_fichier_mat_surface(CERTU_MTS)


def test_types_structure_et_filtrage_voie(catalogues):
    cat_str, _ = catalogues
    assert TYPES_STRUCTURE[1] == "souple"
    assert TYPES_STRUCTURE[6] == "paves_dalles"

    # En desserte : on doit retrouver ES/GNT (index 0) et Pavés/GNT
    comp_des = structures_compatibles(cat_str, "desserte")
    abreges_des = {s.abrege for _, s in comp_des}
    assert "ES/GNT" in abreges_des
    assert "Pavés/GNT" in abreges_des

    # Filtrage par type de structure (souple = 1) et exclusion de materiau
    comp_souple = structures_compatibles(cat_str, "desserte", type_structure="souple")
    assert all(s.type_structure == 1 for _, s in comp_souple)
    comp_sans_gnt = structures_compatibles(cat_str, "desserte", materiaux_exclus=("GNT",))
    assert all(s.couche_base != "GNT" and s.couche_fondation != "GNT" for _, s in comp_sans_gnt)

    # En giratoire_trafic_lourd : uniquement les structures giratoires PL
    comp_gpl = structures_compatibles(cat_str, "giratoire_trafic_lourd")
    assert len(comp_gpl) >= 1
    assert all(s.util_g_pl == 1 for _, s in comp_gpl)

    with pytest.raises(ValueError):
        structures_compatibles(cat_str, "voie_inconnue")
    with pytest.raises(ValueError):
        structures_compatibles(cat_str, "desserte", type_structure="inexistant")


def test_etude_complete_paves_gnt_avec_gel_et_option_vb6(catalogues):
    cat_str, cat_mts = catalogues
    paves_gnt = cat_str.structures[49]  # Pavés/GNT : 1 000 à 100 000 essieux

    # Trafic initial = 12 PL/j, 2%, 20 ans -> t_cum = 12 * 365 * 23.8 = 104244
    # CAM preconise Pavés/GNT (souple, desserte) = 0.1 * 2 = 0.2 -> NE = 20849
    res_vb6 = dimensionner_etude(
        catalogue_structures=cat_str,
        catalogue_surfaces=cat_mts,
        structure=paves_gnt,
        type_voie="desserte",
        trafic_initial_pl=12,
        croissance_pct=2,
        duree_ans=20,
        plate_forme="PF2",
        station="Toulouse",
        hiver="HRNE",
        taille_agglo="moyenne",
        epaisseur_non_gelive_cm=0.0,
        pente_sol_pourcent=0.5,
        fidele_vb6=True,
    )
    assert res_vb6.trafic_cumule == 104244
    assert res_vb6.cam == pytest.approx(0.2, abs=1e-6)
    assert res_vb6.ne_equivalent == 20849
    assert res_vb6.ne_hors_limite is False
    assert res_vb6.etude_labo is False
    assert res_vb6.epaisseur is not None
    assert res_vb6.epaisseur.ne_theorique == 30000
    assert res_vb6.epaisseur.q1.epaisseurs == (8, 4, 15, 0, 0, 0)
    assert res_vb6.indice_gel_ref == 36
    assert res_vb6.gel_q1 is not None
    assert res_vb6.gel_q1.verifiee is True

    # Comparaison avec fidele_vb6=False (sans lit de pose de 4 cm dans le calcul au gel)
    res_cat = dimensionner_etude(
        catalogue_structures=cat_str,
        catalogue_surfaces=cat_mts,
        structure=paves_gnt,
        type_voie="desserte",
        trafic_initial_pl=12,
        croissance_pct=2,
        duree_ans=20,
        plate_forme="PF2",
        station="Toulouse",
        hiver="HRNE",
        taille_agglo="moyenne",
        epaisseur_non_gelive_cm=0.0,
        pente_sol_pourcent=0.5,
        fidele_vb6=False,
    )
    assert res_vb6.gel_q1.indice_gel_adm > res_cat.gel_q1.indice_gel_adm


def test_etude_materiau_compose_et_hors_limite(catalogues):
    cat_str, cat_mts = catalogues
    # Structure Enrobés/GB3/GB3 (matériau de surface composé "Enrobés")
    s_enr = cat_str.structures_par_abrege["Enrobés/GNT"][0]
    mat_surf = cat_mts.obtenir(s_enr.couche_surface)
    comps = compositions_surface_compatibles(mat_surf, 6)
    assert len(comps) >= 1
    assert all(c.epaisseur_preconisee == 6 for c in comps)

    res = dimensionner_etude(
        catalogue_structures=cat_str,
        catalogue_surfaces=cat_mts,
        structure=s_enr,
        type_voie="distribution",
        trafic_initial_pl=30,
        croissance_pct=2,
        duree_ans=20,
        plate_forme="PF2",
    )
    assert res.epaisseur is not None
    assert len(res.compositions_q1) >= 1
    assert res.etude_labo is False

    # Cas NE hors plage de la structure (trafic énorme sur ES/GNT limité à 100 000)
    es_gnt = cat_str.structures[0]
    res_hl = dimensionner_etude(
        catalogue_structures=cat_str,
        catalogue_surfaces=cat_mts,
        structure=es_gnt,
        type_voie="trafic_lourd",
        trafic_initial_pl=500,
        croissance_pct=5,
        duree_ans=30,
        plate_forme="PF2",
    )
    assert res_hl.epaisseur is None
