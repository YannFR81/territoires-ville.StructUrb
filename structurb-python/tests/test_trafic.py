"""Tests de référence du module trafic de Struct-Urb (portage Python).

Écrits par Claude AVANT l'implémentation, à partir du code VB6 d'origine
(CEREMA/territoires-ville.StructUrb) :
- ModuleMain.bas : CalculerTraficCum, CalculerTraficIni, DonnerMinMaxTraficIni,
  DonnerPrecMinMaxCAM ;
- frmDocument.frm : CalculerEtAfficherNE.

L'implémentation (structurb/trafic.py) est à écrire par Gemini SANS modifier
ces tests. Si un test paraît faux, le signaler dans NOTES_REVUE.md au lieu de
le corriger.

Point clé : VB6 `CLng` arrondit au pair le plus proche (« arrondi bancaire ») :
CLng(2.5) = 2, CLng(3.5) = 4. Ce n'est pas une troncature ni un arrondi
« au-dessus ».
"""

import pytest

from structurb.trafic import (
    TYPES_VOIE,
    bornes_trafic_initial,
    cam_preconise,
    etude_labo_conseillee,
    ne_equivalent,
    ne_hors_limite,
    statut_trafic_initial,
    trafic_cumule,
    trafic_initial,
    vb_clng,
)


# --- Arrondi VB6 -----------------------------------------------------------

@pytest.mark.parametrize(
    "x, attendu",
    [(2.5, 2), (3.5, 4), (-2.5, -2), (2.4, 2), (2.6, 3), (0.5, 0), (1.5, 2), (7336.5, 7336)],
)
def test_vb_clng_arrondi_bancaire(x, attendu):
    assert vb_clng(x) == attendu


# --- Trafic cumulé : TCum = CLng(365 * T * (n + a*n*(n-1)/2)) ---------------

@pytest.mark.parametrize(
    "t_ini, croissance_pct, duree, attendu",
    [
        (100, 0, 20, 730_000),      # 365 * 100 * 20
        (100, 2, 20, 868_700),      # 36 500 * (20 + 0,02*20*19/2) = 36 500 * 23,8
        (50, 4, 10, 215_350),       # 18 250 * (10 + 0,04*10*9/2) = 18 250 * 11,8
        (1, 0, 1, 365),
        (10, 1, 2, 7_336),          # 3 650 * 2,01 = 7 336,4999… → 7 336
        (0, 3, 15, 0),
    ],
)
def test_trafic_cumule(t_ini, croissance_pct, duree, attendu):
    assert trafic_cumule(t_ini, croissance_pct, duree) == attendu


def test_trafic_cumule_croissance_hors_domaine():
    # Struct-Urb ne propose que 0 à 5 % (boutons OptionCA(0..5)).
    with pytest.raises(ValueError):
        trafic_cumule(100, 6, 20)
    with pytest.raises(ValueError):
        trafic_cumule(100, -1, 20)


# --- Trafic initial (calcul inverse) -----------------------------------------

@pytest.mark.parametrize(
    "t_cum, croissance_pct, duree, attendu",
    [
        (730_000, 0, 20, 100),
        (868_700, 2, 20, 100),
        (1_825, 0, 2, 2),   # 1 825 / 730 = 2,5 → arrondi au pair : 2
        (2_555, 0, 2, 4),   # 2 555 / 730 = 3,5 → arrondi au pair : 4
    ],
)
def test_trafic_initial(t_cum, croissance_pct, duree, attendu):
    assert trafic_initial(t_cum, croissance_pct, duree) == attendu


# --- Domaine de validité du trafic initial (DonnerMinMaxTraficIni) ----------

def test_types_voie():
    assert set(TYPES_VOIE) == {
        "desserte", "distribution", "trafic_lourd", "bus", "parking",
        "giratoire_distribution", "giratoire_trafic_lourd",
    }


@pytest.mark.parametrize(
    "type_voie, attendu",  # (min toléré, min, max, max toléré)
    [
        ("desserte", (0, 0, 25, 30)),
        ("distribution", (20, 25, 150, 170)),
        ("giratoire_distribution", (20, 25, 150, 170)),
        ("trafic_lourd", (120, 150, 750, 1000)),
        ("giratoire_trafic_lourd", (120, 150, 750, 1000)),
        ("bus", (0, 0, 750, 1000)),
        ("parking", (0, 0, 750, 1000)),
    ],
)
def test_bornes_trafic_initial(type_voie, attendu):
    assert bornes_trafic_initial(type_voie) == attendu


@pytest.mark.parametrize(
    "t_ini, type_voie, attendu",
    [
        (25, "desserte", "valide"),          # = max : valide
        (26, "desserte", "tolere"),
        (30, "desserte", "tolere"),          # = max toléré : toléré
        (31, "desserte", "hors_domaine"),
        (25, "distribution", "valide"),      # = min : valide
        (24, "distribution", "tolere"),
        (20, "distribution", "tolere"),
        (19, "distribution", "hors_domaine"),
        (150, "trafic_lourd", "valide"),
        (119, "trafic_lourd", "hors_domaine"),
        (1000, "bus", "tolere"),
        (1001, "parking", "hors_domaine"),
    ],
)
def test_statut_trafic_initial(t_ini, type_voie, attendu):
    assert statut_trafic_initial(t_ini, type_voie) == attendu


@pytest.mark.parametrize(
    "t_ini, type_voie, attendu",
    [
        (800, "trafic_lourd", True),          # > max et ≤ max toléré, voie PL
        (800, "bus", True),
        (800, "giratoire_trafic_lourd", True),
        (800, "parking", False),              # parking : pas de conseil labo
        (750, "trafic_lourd", False),         # = max : pas de conseil
        (1001, "trafic_lourd", False),        # hors domaine : pas de conseil (erreur)
        (160, "distribution", False),
    ],
)
def test_etude_labo_conseillee(t_ini, type_voie, attendu):
    assert etude_labo_conseillee(t_ini, type_voie) is attendu


# --- Nombre d'essieux équivalents : NE = CLng(TCum * CAM) --------------------

@pytest.mark.parametrize(
    "t_cum, cam, attendu",
    [
        (868_700, 0.2, 173_740),
        (730_000, 0.5, 365_000),
        (1_000_000, 1.0, 1_000_000),
        (5, 0.5, 2),   # 2,5 → arrondi au pair : 2
    ],
)
def test_ne_equivalent(t_cum, cam, attendu):
    assert ne_equivalent(t_cum, cam) == attendu


def test_ne_hors_limite():
    assert ne_hors_limite(10_000_000) is False
    assert ne_hors_limite(10_000_001) is True


# --- CAM préconisé / min / max (DonnerPrecMinMaxCAM) ------------------------
# type_cam : 1 = souple ou bitumineuse, 2 = hydraulique ou béton

@pytest.mark.parametrize(
    "type_voie, type_cam, attendu",  # (préconisé, min, max) avant majoration
    [
        ("desserte", 1, (0.1, 0.05, 0.4)),
        ("desserte", 2, (0.1, 0.05, 0.4)),
        ("distribution", 1, (0.1, 0.05, 0.6)),
        ("distribution", 2, (0.2, 0.1, 0.6)),
        ("trafic_lourd", 1, (0.2, 0.1, 0.8)),
        ("trafic_lourd", 2, (0.4, 0.2, 1.0)),
        ("giratoire_distribution", 1, (0.5, 0.2, 1.0)),
        ("giratoire_trafic_lourd", 2, (1.0, 0.5, 1.5)),
        ("parking", 1, (0.1, 0.05, 0.4)),
        ("bus", 2, (0.5, 0.2, 1.0)),
    ],
)
def test_cam_preconise_sans_majoration(type_voie, type_cam, attendu):
    prec, mini, maxi = cam_preconise(type_voie, type_cam, type_structure="bitumineuse")
    assert (prec, mini, maxi) == pytest.approx(attendu)


def test_cam_majore_structure_souple():
    # Structure souple : CAM préconisé × 2 (min et max inchangés).
    assert cam_preconise("trafic_lourd", 1, type_structure="souple") == pytest.approx((0.4, 0.1, 0.8))


def test_cam_majore_paves_sur_gnt():
    assert cam_preconise("distribution", 1, type_structure="paves_dalles", couche_base="gnt") == pytest.approx((0.2, 0.05, 0.6))
    # La comparaison de la couche de base ignore la casse (UCase en VB).
    assert cam_preconise("distribution", 1, type_structure="paves_dalles", couche_base="GNT") == pytest.approx((0.2, 0.05, 0.6))


def test_cam_paves_sans_gnt_non_majore():
    assert cam_preconise("distribution", 1, type_structure="paves_dalles", couche_base="GB") == pytest.approx((0.1, 0.05, 0.6))
