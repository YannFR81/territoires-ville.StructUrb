"""Tests du lot « § 6 de CHARTE_V1.md » (notice Struct-Urb 2.1 et code VB6)."""

import json
from pathlib import Path

import pytest

from structurb.catalogue import ouvrir_fichier_mat_surface, ouvrir_fichier_structures
from structurb.dxf import coupe_dxf
from structurb.etude import dimensionner_etude
from structurb.page import calculer_depuis_json
from structurb.rapport import note_calcul_html

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def catalogues():
    return (
        ouvrir_fichier_structures(REPO_ROOT / "Certu.str"),
        ouvrir_fichier_mat_surface(REPO_ROOT / "Certu.mts"),
    )


# --- 1. Giratoires : pas de choix Q1/Q2, Q2 sans objet, JSON corrigé ----------

def test_giratoire_q2_sans_objet_etude_et_json(catalogues):
    cat_str, cat_mts = catalogues
    s_gir = cat_str.structures[16]  # ' Enrobés /GB3/GB3' (giratoire)
    res = dimensionner_etude(
        cat_str, cat_mts, s_gir,
        type_voie="giratoire_distribution",
        trafic_initial_pl=80,
        croissance_pct=1,
        duree_ans=20,
        plate_forme="PF2",
        station="Toulouse",
        pente_sol_pourcent=0.5,
    )
    assert res.epaisseur is not None
    assert res.epaisseur.q1.trouvee is True
    assert res.epaisseur.q2.trouvee is False
    assert res.gel_q2 is None

    r = json.loads(calculer_depuis_json(json.dumps({
        "index": 16,
        "type_voie": "giratoire_distribution",
        "trafic_initial_pl": 80,
        "croissance_pct": 1,
        "duree_ans": 20,
        "plate_forme": "PF2",
        "station": "Toulouse",
        "pente_sol_pourcent": 0.5,
    }), dossier_catalogue=REPO_ROOT))
    assert r["ok"] is True
    q2 = r["donnees"]["resultats"]["q2"]
    assert q2["trouvee"] is False
    assert q2["couches"] == []
    assert "Q2 : sans objet (giratoire)" in r["resume"]
    assert "Q2 : sans objet (giratoire)" in r["html"]
    assert "Q2 : sans objet (giratoire)" in r["dxf"]


# --- 2. PF1 non admise en giratoire ------------------------------------------

@pytest.mark.parametrize("voie, idx", [
    ("giratoire_distribution", 16),
    ("giratoire_trafic_lourd", 16),
])
def test_pf1_refusee_en_giratoire(catalogues, voie, idx):
    cat_str, cat_mts = catalogues
    with pytest.raises(ValueError, match="PF1"):
        dimensionner_etude(
            cat_str, cat_mts, cat_str.structures[idx],
            type_voie=voie,
            trafic_initial_pl=150,
            croissance_pct=1,
            duree_ans=20,
            plate_forme="PF1",
        )


def test_pf1_refusee_en_giratoire_api_page():
    r = json.loads(calculer_depuis_json(json.dumps({
        "index": 16,
        "type_voie": "giratoire_distribution",
        "trafic_initial_pl": 80,
        "croissance_pct": 1,
        "duree_ans": 20,
        "plate_forme": "PF1",
    }), dossier_catalogue=REPO_ROOT))
    assert r["ok"] is False
    assert "PF1" in r["erreur"]
    assert "giratoire" in r["erreur"].lower()
