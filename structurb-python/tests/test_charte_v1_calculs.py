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


# --- 3. Plages de trafic et ne_hors_limite > ne_max de la structure ----------

@pytest.mark.parametrize("voie, trafic", [
    ("desserte", 31),
    ("distribution", 19),
    ("distribution", 171),
    ("trafic_lourd", 119),
    ("trafic_lourd", 1001),
    ("bus", 1001),
    ("giratoire_distribution", 19),
    ("giratoire_trafic_lourd", 119),
])
def test_trafic_hors_plage_refuse(catalogues, voie, trafic):
    cat_str, cat_mts = catalogues
    idx = 16 if voie.startswith("giratoire_") else 1
    with pytest.raises(ValueError, match="domaine|plage|tolér"):
        dimensionner_etude(
            cat_str, cat_mts, cat_str.structures[idx],
            type_voie=voie,
            trafic_initial_pl=trafic,
            croissance_pct=1,
            duree_ans=20,
            plate_forme="PF2",
        )


def test_ne_hors_limite_si_superieur_ne_max_structure(catalogues):
    cat_str, cat_mts = catalogues
    es_gnt = cat_str.structures[0]  # nb_essieux_max = 100_000
    res = dimensionner_etude(
        cat_str, cat_mts, es_gnt,
        type_voie="trafic_lourd",
        trafic_initial_pl=500,
        croissance_pct=5,
        duree_ans=30,
        plate_forme="PF2",
    )
    assert res.ne_equivalent > es_gnt.nb_essieux_max
    assert res.ne_hors_limite is True
    assert res.epaisseur is None

    r = json.loads(calculer_depuis_json(json.dumps({
        "index": 0,
        "type_voie": "desserte",
        "trafic_initial_pl": 30,
        "croissance_pct": 5,
        "duree_ans": 50,
        "plate_forme": "PF2",
    }), dossier_catalogue=REPO_ROOT))
    assert r["ok"] is True
    assert r["donnees"]["resultats"]["ne_equivalent"] > es_gnt.nb_essieux_max
    assert r["donnees"]["resultats"]["ne_hors_limite"] is True


# --- 4. Durée de service : 5 à 50 ans (VerifierMinMaxDuréeService) ----------

@pytest.mark.parametrize("duree", [0, 4, 51, 100])
def test_duree_service_hors_limites_refusee(catalogues, duree):
    cat_str, cat_mts = catalogues
    with pytest.raises(ValueError, match="5.*50"):
        dimensionner_etude(
            cat_str, cat_mts, cat_str.structures[49],
            type_voie="desserte",
            trafic_initial_pl=12,
            croissance_pct=1,
            duree_ans=duree,
            plate_forme="PF2",
        )
    r = json.loads(calculer_depuis_json(json.dumps({
        "index": 49,
        "type_voie": "desserte",
        "trafic_initial_pl": 12,
        "croissance_pct": 1,
        "duree_ans": duree,
        "plate_forme": "PF2",
    }), dossier_catalogue=REPO_ROOT))
    assert r["ok"] is False
    assert "5 à 50" in r["erreur"]


def test_duree_service_bornes_5_50_acceptees(catalogues, tmp_path):
    from structurb.page import OUTIL, generer_page
    cat_str, cat_mts = catalogues
    for d in (5, 50):
        res = dimensionner_etude(
            cat_str, cat_mts, cat_str.structures[49],
            type_voie="desserte",
            trafic_initial_pl=12,
            croissance_pct=1,
            duree_ans=d,
            plate_forme="PF2",
        )
        assert res.trafic_cumule > 0
    schema_d = OUTIL["inputSchema"]["properties"]["duree_ans"]
    assert schema_d["minimum"] == 5 and schema_d["maximum"] == 50
    f = tmp_path / "page.html"
    generer_page(f, dossier_catalogue=REPO_ROOT)
    html = f.read_text(encoding="utf-8")
    assert 'id="champ-duree_ans" name="duree_ans" type="number" min="5" max="50"' in html


# --- 5. Valeurs par défaut : croissance 1 %, Kcr 0,7 décochée ---------------

def test_valeurs_par_defaut_croissance_1_et_norme_2019_false(tmp_path):
    from structurb.page import OUTIL, generer_page
    assert OUTIL["inputSchema"]["properties"]["croissance_pct"]["default"] == 1
    assert OUTIL["inputSchema"]["properties"]["norme_2019"]["default"] is False

    r = json.loads(calculer_depuis_json(json.dumps({
        "index": 49,
        "type_voie": "desserte",
        "trafic_initial_pl": 12,
        "plate_forme": "PF2",
    }), dossier_catalogue=REPO_ROOT))
    assert r["ok"] is True
    assert r["donnees"]["entrees"]["croissance_pct"] == 1
    assert r["donnees"]["entrees"]["norme_2019"] is False

    f = tmp_path / "page.html"
    generer_page(f, dossier_catalogue=REPO_ROOT)
    html = f.read_text(encoding="utf-8")
    assert 'id="champ-croissance_pct" name="croissance_pct" type="number" min="0" max="5" step="1" value="1"' in html
    assert '<input id="champ-norme_2019" name="norme_2019" type="checkbox">' in html


# --- 6. Grave-émulsion (GE) au gel : fidélité VB6 (IA = 17 sur ES/GE) -------

def test_grave_emulsion_gel_fidele_vb6(catalogues):
    """Dans le VB6 (CalculerIndiceGelAdm, l. 2589-2625), GE a a_gel=0 et b_gel=0 dans Certu.str.
    Pour ES/GE avec pente=0,5 (et qm=0, sans couche de forme), IA = 17 °C·j."""
    cat_str, cat_mts = catalogues
    ge = cat_str.obtenir_materiau_bf("GE")
    assert (ge.a_gel, ge.b_gel) == (0.0, 0.0)

    es_ge = cat_str.structures[2]
    assert es_ge.abrege.strip() == "ES/GE"
    res = dimensionner_etude(
        cat_str, cat_mts, es_ge,
        type_voie="desserte",
        trafic_initial_pl=12,
        croissance_pct=1,
        duree_ans=20,
        plate_forme="PF2",
        station="Toulouse",
        pente_sol_pourcent=0.5,
    )
    assert res.gel_q1 is not None
    assert res.gel_q1.indice_gel_adm == 17
