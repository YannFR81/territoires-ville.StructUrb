"""Tests de la page autonome (structurb.page) : moteur appelé depuis le navigateur et page générée."""

import base64
import json
import re
from pathlib import Path

import pytest

from structurb.cli import main
from structurb.page import PYODIDE_VERSION, calculer_depuis_json, generer_page

REPO_ROOT = Path(__file__).resolve().parents[2]

PARAMS_PAVES = {
    "index": 49,
    "type_voie": "desserte",
    "trafic_initial_pl": 12,
    "croissance_pct": 2,
    "duree_ans": 20,
    "plate_forme": "PF2",
    "station": "Toulouse",
    "hiver": "HRNE",
    "taille_agglo": "moyenne",
    "pente_sol_pourcent": 0.5,
    "titre": "Rue des Lilas",
}


def _calc(params, **kw):
    return json.loads(calculer_depuis_json(json.dumps(params), **kw))


# --- Moteur appelé par la page --------------------------------------------------

def test_calcul_complet():
    r = _calc(PARAMS_PAVES, dossier_catalogue=REPO_ROOT)
    assert r["ok"] is True
    d = r["donnees"]
    assert d["resultats"]["ne_equivalent"] == 20849
    assert d["resultats"]["ne_theorique"] == 30000
    assert d["resultats"]["gel"]["indice_reference"] == 36
    assert d["structure"]["abrege"] == "Pavés/GNT"
    assert r["html"].startswith("<!doctype html>")
    assert r["dxf"].startswith("0\nSECTION")
    assert "20 849" in r["resume"].replace(" ", " ")


def test_calcul_par_abrege_et_options():
    p = {k: v for k, v in PARAMS_PAVES.items() if k != "index"}
    p["structure"] = "Pavés/GNT"
    p["norme_2019"] = True
    p["fidele_vb6"] = False
    r = _calc(p, dossier_catalogue=REPO_ROOT)
    assert r["ok"] is True
    assert r["donnees"]["entrees"]["norme_2019"] is True
    assert r["donnees"]["entrees"]["fidele_vb6"] is False


@pytest.mark.parametrize(
    "modif, motif",
    [
        ({"index": 999}, "index"),
        ({"index": 16}, "type de voie"),          # Enrobés/GB3/GB3 non prévue en desserte
        ({"type_voie": "autoroute"}, "voie"),
        ({"plate_forme": "PF9"}, "plate-forme"),
        ({"trafic_initial_pl": "beaucoup"}, "trafic"),
        ({"croissance_pct": 9}, "croissance"),
        ({"station": "Atlantide"}, "station"),
    ],
)
def test_erreurs_de_saisie_lisibles(modif, motif):
    r = _calc({**PARAMS_PAVES, **modif}, dossier_catalogue=REPO_ROOT)
    assert r["ok"] is False
    assert motif in r["erreur"].lower()


def test_json_invalide():
    r = json.loads(calculer_depuis_json("{pas du json", dossier_catalogue=REPO_ROOT))
    assert r["ok"] is False


# --- Page générée ------------------------------------------------------------

@pytest.fixture(scope="module")
def page(tmp_path_factory):
    f = tmp_path_factory.mktemp("page") / "structurb.html"
    generer_page(f, dossier_catalogue=REPO_ROOT)
    return f.read_text(encoding="utf-8")


def test_page_autonome(page):
    assert page.startswith("<!doctype html>")
    # Seule ressource externe : Pyodide, version figée (hors sources Python embarquées)
    sans_sources = re.sub(r'<script type="application/json" id="structurb-fichiers">.*?</script>', "", page, flags=re.S)
    externes = set(re.findall(r'https://[^"\'\s)]+', sans_sources))
    assert externes and all(u.startswith(f"https://cdn.jsdelivr.net/pyodide/v{PYODIDE_VERSION}/full/") for u in externes)
    assert re.fullmatch(r"\d+\.\d+\.\d+", PYODIDE_VERSION)


def test_page_embarque_moteur_et_catalogue(page):
    m = re.search(r'<script type="application/json" id="structurb-fichiers">(.*?)</script>', page, re.S)
    fichiers = json.loads(m.group(1))
    for module in ("__init__.py", "trafic.py", "gel.py", "catalogue.py", "epaisseur.py", "etude.py",
                   "rapport.py", "dxf.py", "page.py"):
        assert f"structurb/{module}" in fichiers["sources"]
    assert base64.b64decode(fichiers["catalogue"]["Certu.str"]) == (REPO_ROOT / "Certu.str").read_bytes()
    assert base64.b64decode(fichiers["catalogue"]["Certu.mts"]) == (REPO_ROOT / "Certu.mts").read_bytes()


def test_page_formulaire_accessible(page):
    assert '<form id="formulaire-etude"' in page
    champs = ["type_voie", "index", "trafic_initial_pl", "croissance_pct", "duree_ans", "plate_forme",
              "station", "hiver", "taille_agglo", "indice_gel_perso", "pente_sol_pourcent",
              "epaisseur_non_gelive_cm", "couche_forme_traitee", "norme_2019", "fidele_vb6", "titre"]
    for c in champs:
        assert f'name="{c}"' in page, c
        assert f'<label for="champ-{c}"' in page, c
        assert f'id="champ-{c}"' in page, c
    assert 'aria-live="polite"' in page
    # Listes de choix préremplies sans attendre Pyodide
    m = re.search(r'<script type="application/json" id="structurb-listes">(.*?)</script>', page, re.S)
    listes = json.loads(m.group(1))
    assert len(listes["structures"]) == 69 and len(listes["stations"]) == 84


def test_page_interface_pour_les_ia(page):
    assert "window.structurb" in page
    assert "dimensionner_chaussee" in page  # nom de l’outil exposé
    assert "navigator.modelContext" in page  # WebMCP, si le navigateur le propose
    m = re.search(r'<script type="application/json" id="structurb-outil">(.*?)</script>', page, re.S)
    outil = json.loads(m.group(1))
    assert outil["name"] == "dimensionner_chaussee"
    props = outil["inputSchema"]["properties"]
    assert {"index", "type_voie", "trafic_initial_pl", "plate_forme"} <= set(props)
    assert set(outil["inputSchema"]["required"]) >= {"type_voie", "trafic_initial_pl", "plate_forme"}


def test_commande_page(tmp_path, capsys):
    f = tmp_path / "p.html"
    assert main(["page", "--sortie", str(f)]) == 0
    assert f.stat().st_size > 300_000  # moteur + catalogue embarqués


def test_page_aide_en_ligne(page):
    assert 'id="aide-en-ligne"' in page
    for mot in ("PF1", "PF2+", "Q1", "Q2", "Kcr", "DXF", "window.structurb"):
        assert mot in page, mot
