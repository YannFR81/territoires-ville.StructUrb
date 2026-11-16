"""Tests du lot Catalogue (structurb.catalogue) — référence Certu.mts et Certu.str."""

from pathlib import Path
import struct
import pytest

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


def test_ouvrir_certu_mts():
    cat = ouvrir_fichier_mat_surface(CERTU_MTS)
    assert isinstance(cat, CatalogueMatSurface)
    assert len(cat.simples) == 3
    assert len(cat.mecaniques) == 5
    assert len(cat.composes) == 2
    assert len(cat.par_abrege) == 10

    # Verification d'un materiau mecanique connu (BBTM ou BBSG)
    for m in cat.mecaniques:
        assert m.abrege
        assert m.nom
        assert m.young > 0

    for mc in cat.composes:
        assert mc.abrege
        assert len(mc.compositions) >= 1
        for comp in mc.compositions:
            assert comp.epaisseur_preconisee >= 0


def test_ouvrir_certu_str():
    cat = ouvrir_fichier_structures(CERTU_STR)
    assert isinstance(cat, CatalogueStructures)
    assert len(cat.materiaux_bf) == 14
    assert len(cat.structures) == 69

    # Chaque structure possede les 8 grilles (PF1..PF3 x Q1/Q2)
    for s in cat.structures:
        assert s.abrege
        assert set(s.grilles_pf.keys()) == set(GRILLES_PF)
        assert s.nb_essieux_min <= s.nb_essieux_max
        for cle, lignes in s.grilles_pf.items():
            assert len(lignes) >= 1
            for lig in lignes:
                assert lig.epaisseur_surface >= 0
                assert lig.epaisseur_base_1 >= 0


def test_coherence_materiaux_structures():
    mts = ouvrir_fichier_mat_surface(CERTU_MTS)
    cat = ouvrir_fichier_structures(CERTU_STR)

    for s in cat.structures:
        if s.couche_surface != "Aucune":
            assert s.couche_surface in mts.par_abrege
        assert s.couche_base in cat.materiaux_par_abrege
        if s.couche_fondation != "Aucune":
            assert s.couche_fondation in cat.materiaux_par_abrege


def test_erreurs_fichiers_invalides(tmp_path):
    with pytest.raises(FileNotFoundError):
        ouvrir_fichier_mat_surface(tmp_path / "inexistant.mts")
    with pytest.raises(FileNotFoundError):
        ouvrir_fichier_structures(tmp_path / "inexistant.str")

    bad = tmp_path / "bad.str"
    s = b"Mauvais entete"
    bad.write_bytes(struct.pack("<i", len(s)) + s)
    with pytest.raises(ValueError):
        ouvrir_fichier_structures(bad)

    bad_mts = tmp_path / "bad.mts"
    bad_mts.write_bytes(struct.pack("<i", len(s)) + s)
    with pytest.raises(ValueError):
        ouvrir_fichier_mat_surface(bad_mts)
