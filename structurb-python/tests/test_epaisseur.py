"""Tests du lot Recherche d'épaisseur (structurb.epaisseur).

Valeurs de référence : extraction indépendante du catalogue Certu.str
(``dimensionnement-burmister/catalogue_structures.csv``, colonne NE comprise),
et non le code testé.
"""

import csv
import itertools
from pathlib import Path

import pytest

from structurb.catalogue import GRILLES_PF, ouvrir_fichier_structures
from structurb.epaisseur import (
    EP_LIT_POSE,
    EP_SURFACE_SANS_EPAISSEUR,
    PLATES_FORMES,
    epaisseur_possible,
    ne_theorique_et_indice,
    rechercher_epaisseur,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CERTU_STR = REPO_ROOT / "Certu.str"
CSV_STRUCTURES = REPO_ROOT / "dimensionnement-burmister" / "catalogue_structures.csv"


@pytest.fixture(scope="module")
def cat():
    return ouvrir_fichier_structures(CERTU_STR)


# --- TrouverNEthEtInd -------------------------------------------------------

@pytest.mark.parametrize(
    "ne, ne_min, attendu",
    [
        (1000, 1000, (1000, 1)),
        (1001, 1000, (2000, 2)),
        (9000, 1000, (9000, 9)),
        (9001, 1000, (10000, 10)),
        (10001, 1000, (20000, 11)),
        (100000, 1000, (100000, 19)),
        (100000, 100000, (100000, 1)),
        (100001, 100000, (200000, 2)),
        (10000000, 100000, (10000000, 19)),
        (1000000, 10000, (1000000, 19)),
        (9000, 9000, (9000, 1)),
        (9001, 9000, (10000, 2)),
        # NE inférieur au minimum : le VB6 rend le minimum et l'indice 1
        (500, 1000, (1000, 1)),
    ],
)
def test_ne_theorique_et_indice(ne, ne_min, attendu):
    assert ne_theorique_et_indice(ne, ne_min) == attendu


# --- TrouverEpaisseurPossible -----------------------------------------------

def test_epaisseur_possible(cat):
    es_gnt = cat.structures[0]  # 1 000 à 100 000 essieux
    assert epaisseur_possible(15000, es_gnt, "PF2") is True
    assert epaisseur_possible(1000, es_gnt, "PF2") is True
    assert epaisseur_possible(100000, es_gnt, "PF2") is True
    assert epaisseur_possible(999, es_gnt, "PF2") is False
    assert epaisseur_possible(100001, es_gnt, "PF2") is False
    assert epaisseur_possible(None, es_gnt, "PF2") is False  # NE inconnu
    assert epaisseur_possible(15000, None, "PF2") is False  # pas de structure
    assert epaisseur_possible(15000, es_gnt, None) is False  # pas de plate-forme
    assert epaisseur_possible(15000, es_gnt, "PF4") is False

    gb3 = cat.structures[16]  # 100 000 à 10 000 000 essieux
    assert epaisseur_possible(10_000_000, gb3, "PF3") is True
    assert epaisseur_possible(10_000_001, gb3, "PF3") is False  # NE hors limite


# --- RechercherEpaisseur : cas de référence ---------------------------------

def _q(res, qualite):
    q = res.q1 if qualite == 1 else res.q2
    return q.epaisseurs, q.qm, q.min_technique, q.max_pratique, q.trouvee


def test_es_gnt_couche_sans_epaisseur(cat):
    # ES/GNT : couche de surface sans épaisseur -> 3 cm pour l'affichage (Q1 et Q2)
    s = cat.structures[0]
    assert s.abrege == "ES/GNT" and s.couche_surf_sans_ep == 1
    res = rechercher_epaisseur(15000, s, "PF2")
    assert (res.ne_theorique, res.indice) == (20000, 11)
    assert _q(res, 1) == ((3, 0, 15, 17, 0, 0), 0.0, "Non", "Non", True)
    assert _q(res, 2) == ((3, 0, 15, 20, 0, 0), 0.0, "Non", "Non", True)
    # L'épaisseur préconisée garde la valeur du catalogue (avant les 3 cm)
    assert res.q1.epaisseur_preconisee == 0
    assert EP_SURFACE_SANS_EPAISSEUR == 3


def test_max_pratique_oui_donne_non_trouvee(cat):
    # ES/GNT, PF1 Q1, NE 20 000 : maximum pratique « Oui » -> épaisseur non trouvée
    res = rechercher_epaisseur(15000, cat.structures[0], "PF1")
    assert res.q1.max_pratique == "Oui"
    assert res.q1.trouvee is False


def test_enrobes_gnt(cat):
    s = cat.structures[1]
    assert s.abrege == "Enrobés/GNT"
    res = rechercher_epaisseur(9000, s, "PF2")
    assert (res.ne_theorique, res.indice) == (9000, 9)
    assert _q(res, 1) == ((4, 0, 15, 0, 0, 0), 0.0, "Oui", "Non", True)
    assert _q(res, 2) == ((5, 0, 15, 0, 0, 0), 0.0, "Oui", "Non", True)
    assert res.q1.epaisseur_preconisee == 4
    assert res.q2.epaisseur_preconisee == 5


def test_paves_lit_de_pose(cat):
    s = cat.structures[49]
    assert s.abrege == "Pavés/GNT"
    res = rechercher_epaisseur(100000, s, "PF2")
    assert _q(res, 1) == ((8, EP_LIT_POSE, 18, 0, 0, 0), 0.0, "Non", "Non", True)
    assert _q(res, 2) == ((8, EP_LIT_POSE, 23, 0, 0, 0), 0.0, "Non", "Non", True)
    assert EP_LIT_POSE == 4


def test_dalles_lit_de_pose_et_qm(cat):
    s = cat.structures[63]
    assert s.abrege == "Dalles/BC5"
    res = rechercher_epaisseur(1_000_000, s, "PF2")
    assert res.q1.epaisseurs == (12, 4, 22, 0, 0, 0)
    assert res.q2.epaisseurs == (12, 4, 23, 0, 0, 0)
    assert res.q1.qm == pytest.approx(0.7, abs=1e-6)
    assert res.q2.qm == pytest.approx(0.5, abs=1e-6)


def test_sans_couche_de_surface(cat):
    s = cat.structures[22]
    assert s.abrege == "BC5/GNT" and s.couche_surface == "Aucune"
    res = rechercher_epaisseur(20000, s, "PF2")
    assert res.q1.epaisseurs == (0, 0, 16, 0, 10, 0)
    assert res.q2.epaisseurs == (0, 0, 18, 0, 10, 0)


def test_enrobes_giratoire_espaces(cat):
    # « Enrobés » avec espaces (giratoires) : ni Dalles ni Pavés, pas de lit de pose
    s = cat.structures[16]
    assert s.couche_surface == " Enrobés "
    res = rechercher_epaisseur(10_000_000, s, "PF2")
    assert (res.ne_theorique, res.indice) == (10_000_000, 19)
    assert res.q1.epaisseurs == (6, 0, 10, 11, 11, 0)
    assert res.q1.qm == pytest.approx(0.6, abs=1e-6)


def test_hors_plage_et_plate_forme_invalide(cat):
    s = cat.structures[0]
    assert rechercher_epaisseur(999, s, "PF2") is None
    assert rechercher_epaisseur(100001, s, "PF2") is None
    with pytest.raises(ValueError):
        rechercher_epaisseur(15000, s, "PF4")


# --- Balayage complet contre l'extraction indépendante ----------------------

def test_balayage_complet_contre_csv(cat):
    with CSV_STRUCTURES.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    groupes = [list(g) for _, g in itertools.groupby(rows, key=lambda r: (r["index"], r["structure"], r["risque_%"]))]
    assert len(groupes) == len(cat.structures) == 69

    nb = 0
    for s, groupe in zip(cat.structures, groupes):
        ne_precedent = {}
        for r in groupe:
            ne = int(r["NE"])
            pf = r["PF"]
            attendu = (
                int(r["ep_surf_cm"]),
                int(r["ep_base1_cm"]),
                int(r["ep_base2_cm"]),
                int(r["ep_fond1_cm"]),
                int(r["ep_fond2_cm"]),
                r["min_techno"],
                r["max_pratique"],
            )
            # NE exactement sur le palier, et NE juste au-dessus du palier précédent
            essais = [ne]
            cle = (pf, r["qualite"])
            if cle in ne_precedent:
                essais.append(ne_precedent[cle] + 1)
            ne_precedent[cle] = ne
            for ne_essai in essais:
                res = rechercher_epaisseur(ne_essai, s, pf)
                assert res.ne_theorique == ne
                lig = (res.q1 if r["qualite"] == "Q1" else res.q2).ligne
                obtenu = (
                    lig.epaisseur_surface,
                    lig.epaisseur_base_1,
                    lig.epaisseur_base_2,
                    lig.epaisseur_fondation_1,
                    lig.epaisseur_fondation_2,
                    lig.min_technique,
                    lig.max_pratique,
                )
                assert obtenu == attendu, (s.abrege, pf, r["qualite"], ne_essai)
                nb += 1
    assert nb > 7544  # toutes les lignes + les NE intermédiaires


def test_plates_formes():
    assert PLATES_FORMES == ("PF1", "PF2", "PF2+", "PF3")
    assert len(GRILLES_PF) == 2 * len(PLATES_FORMES)
