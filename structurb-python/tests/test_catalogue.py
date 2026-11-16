"""Tests du lot Catalogue (structurb.catalogue) — référence Certu.mts et Certu.str."""

import csv
import struct
import typing
from pathlib import Path
import pytest

import structurb.catalogue as cat_mod
from structurb.catalogue import (
    ENTETE_MTS,
    ENTETE_STR_V200,
    GRILLES_PF,
    CatalogueMatSurface,
    CatalogueStructures,
    ouvrir_fichier_mat_surface,
    ouvrir_fichier_structures,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CERTU_MTS = REPO_ROOT / "Certu.mts"
CERTU_STR = REPO_ROOT / "Certu.str"
CSV_MATERIAUX = REPO_ROOT / "dimensionnement-burmister" / "catalogue_materiaux.csv"
CSV_STRUCTURES = REPO_ROOT / "dimensionnement-burmister" / "catalogue_structures.csv"


def _vb_str(s: str) -> bytes:
    raw = s.encode("cp1252")
    return struct.pack("<i", len(raw)) + raw


def test_type_hints_valides():
    # Verifie que Optional et toutes les annotations sont resolues sans erreur
    hints = typing.get_type_hints(cat_mod._lire_string)
    assert "return" in hints


def test_ouvrir_certu_mts():
    cat = ouvrir_fichier_mat_surface(CERTU_MTS)
    assert isinstance(cat, CatalogueMatSurface)
    assert len(cat.simples) == 3
    assert len(cat.mecaniques) == 5
    assert len(cat.composes) == 2
    assert len(cat.par_abrege) == 10

    for m in cat.mecaniques:
        assert m.abrege
        assert m.nom
        assert m.young > 0

    for mc in cat.composes:
        assert mc.abrege
        assert len(mc.compositions) >= 1
        for comp in mc.compositions:
            assert comp.epaisseur_preconisee >= 0


def test_ouvrir_certu_str_et_variantes_sans_perte():
    cat = ouvrir_fichier_structures(CERTU_STR)
    assert isinstance(cat, CatalogueStructures)
    assert len(cat.materiaux_bf) == 14
    assert len(cat.structures) == 69

    # 49 abreges distincts mais 69 structures au total (aucune structure perdue)
    assert len(cat.structures_par_abrege) == 49
    assert sum(len(v) for v in cat.structures_par_abrege.values()) == 69

    # Exemple concret : Enrobés/GNT a 2 variantes avec plages de NE distinctes
    variantes_enr = cat.structures_par_abrege["Enrobés/GNT"]
    assert len(variantes_enr) == 2
    plages = {(v.nb_essieux_min, v.nb_essieux_max) for v in variantes_enr}
    assert plages == {(1000, 100000), (10000, 20000)}

    for s in cat.structures:
        assert s.abrege
        assert set(s.grilles_pf.keys()) == set(GRILLES_PF)
        assert s.nb_essieux_min <= s.nb_essieux_max
        for cle, lignes in s.grilles_pf.items():
            assert len(lignes) >= 1


def test_espaces_significatifs_et_casse():
    mts = ouvrir_fichier_mat_surface(CERTU_MTS)
    cat = ouvrir_fichier_structures(CERTU_STR)

    # Espaces significatifs preserves : "Enrobés" != " Enrobés " (giratoires)
    assert "Enrobés" in mts.par_abrege
    assert " Enrobés " in mts.par_abrege
    assert mts.obtenir("Enrobés") is not mts.obtenir(" Enrobés ")

    # Recherche insensible a la casse
    assert mts.obtenir("bbtm").abrege == "BBTM"
    assert cat.obtenir_materiau_bf("gnt").abrege == "GNT"

    for s in cat.structures:
        if s.couche_surface != "Aucune":
            assert mts.obtenir(s.couche_surface) is not None
        assert cat.obtenir_materiau_bf(s.couche_base) is not None
        if s.couche_fondation != "Aucune":
            assert cat.obtenir_materiau_bf(s.couche_fondation) is not None


def test_valeur_reference_et_comparaison_csv():
    mts = ouvrir_fichier_mat_surface(CERTU_MTS)
    cat = ouvrir_fichier_structures(CERTU_STR)

    # Cas de reference explicite : ES/GNT, PF1 Q1, 1re ligne
    es_gnt = cat.structures[0]
    assert es_gnt.abrege == "ES/GNT"
    lig0 = es_gnt.grilles_pf["PF1_Q1"][0]
    assert (
        lig0.epaisseur_surface,
        lig0.epaisseur_base_1,
        lig0.epaisseur_base_2,
        lig0.epaisseur_fondation_1,
        lig0.epaisseur_fondation_2,
    ) == (0, 15, 18, 0, 0)
    assert lig0.qm == pytest.approx(0.0)
    assert lig0.min_technique == "Non"
    assert lig0.max_pratique == "Non"

    # Comparaison complete avec les CSV de reference de dimensionnement-burmister (24 materiaux, 7 544 lignes)
    with CSV_MATERIAUX.open("r", encoding="utf-8-sig") as f:
        rows_mat = list(csv.DictReader(f, delimiter=";"))
    assert len(rows_mat) == 24
    for r in rows_mat:
        abr = " Enrobés " if r["nom"] == "Enrobés pour giratoires" else r["abrege"]
        if r["couche"] == "base/fondation":
            m = cat.obtenir_materiau_bf(abr)
        else:
            m = mts.obtenir(abr)
        assert m.nom == r["nom"]
        assert m.a_gel == pytest.approx(float(r["a_gel"]), abs=1e-5)
        assert m.b_gel == pytest.approx(float(r["b_gel"]), abs=1e-5)
        if hasattr(m, "young"):
            assert m.young == pytest.approx(float(r["E_MPa"]), abs=1e-2)
            assert m.poisson == pytest.approx(float(r["nu"]), abs=1e-5)

    with CSV_STRUCTURES.open("r", encoding="utf-8-sig") as f:
        rows_str = list(csv.DictReader(f, delimiter=";"))
    assert len(rows_str) == 7544
    lignes_lues = []
    for s in cat.structures:
        for cle in GRILLES_PF:
            pf, qual = cle.split("_")
            for lig in s.grilles_pf[cle]:
                lignes_lues.append((
                    s.abrege, pf, qual,
                    lig.epaisseur_surface, lig.epaisseur_base_1, lig.epaisseur_base_2,
                    lig.epaisseur_fondation_1, lig.epaisseur_fondation_2,
                    lig.qm, lig.min_technique, lig.max_pratique,
                ))
    assert len(lignes_lues) == len(rows_str)
    for lu, ref in zip(lignes_lues, rows_str):
        # Le CSV d'export a applique strip() sur le nom de structure (ex: " Enrobés /GB3/GB3")
        assert lu[0].strip() == ref["structure"]
        assert lu[1] == ref["PF"]
        assert lu[2] == ref["qualite"]
        assert lu[3] == int(ref["ep_surf_cm"])
        assert lu[4] == int(ref["ep_base1_cm"])
        assert lu[5] == int(ref["ep_base2_cm"])
        assert lu[6] == int(ref["ep_fond1_cm"])
        assert lu[7] == int(ref["ep_fond2_cm"])
        assert lu[8] == pytest.approx(float(ref["Qm"].replace(",", ".")), abs=1e-4)
        assert lu[9] == ref["min_techno"]
        assert lu[10] == ref["max_pratique"]


def test_doublon_abrege_materiau_refuse(tmp_path):
    # Deux matériaux simples avec le même abrégé à la casse près ("BB" et "bb") -> ValueError
    blob = bytearray(_vb_str(ENTETE_MTS))
    for abr in ("BB", "bb"):
        blob += _vb_str("MatériauSimple")
        blob += _vb_str("Nom") + _vb_str(abr) + _vb_str("Norme") + _vb_str("1")
        blob += struct.pack("<ff", 0.0, 0.0)
        blob += _vb_str("") + _vb_str("###Fin commentaire###")
    f_mts = tmp_path / "doublon.mts"
    f_mts.write_bytes(bytes(blob))
    with pytest.raises(ValueError):
        ouvrir_fichier_mat_surface(f_mts)

    # Deux matériaux base/fondation avec le même abrégé à la casse près -> ValueError
    blob_str = bytearray(_vb_str(ENTETE_STR_V200))
    for abr in ("GNT", "gnt"):
        blob_str += _vb_str("MatériauFondBase")
        blob_str += _vb_str("Nom") + _vb_str(abr) + _vb_str("Norme") + _vb_str("1")
        blob_str += struct.pack("<ffffff", 0.0, 0.0, 600.0, 0.35, 0.0, 0.0)
        blob_str += _vb_str("") + _vb_str("###Fin commentaire###")
    f_str = tmp_path / "doublon.str"
    f_str.write_bytes(bytes(blob_str))
    with pytest.raises(ValueError):
        ouvrir_fichier_structures(f_str)


def test_erreurs_fichiers_invalides(tmp_path):
    with pytest.raises(FileNotFoundError):
        ouvrir_fichier_mat_surface(tmp_path / "inexistant.mts")
    with pytest.raises(FileNotFoundError):
        ouvrir_fichier_structures(tmp_path / "inexistant.str")

    bad = tmp_path / "bad.str"
    bad.write_bytes(_vb_str("Mauvais entete"))
    with pytest.raises(ValueError):
        ouvrir_fichier_structures(bad)

    bad_mts = tmp_path / "bad.mts"
    bad_mts.write_bytes(_vb_str("Mauvais entete"))
    with pytest.raises(ValueError):
        ouvrir_fichier_mat_surface(bad_mts)
