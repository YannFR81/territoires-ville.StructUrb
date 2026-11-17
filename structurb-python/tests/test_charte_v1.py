"""Charte graphique de Struct-Urb V1 (VB6) : icône, couleurs de la coupe, DXF, page (sans effet sur les calculs)."""

import re
from pathlib import Path

import pytest

from structurb.catalogue import LigneEpaisseur, ouvrir_fichier_structures
from structurb.dxf import CALQUES
from structurb.page import generer_page
from structurb.rapport import COULEURS_COUCHES, _couches_detail, _svg_coupe

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSETS = REPO_ROOT / "structurb-python" / "structurb" / "assets"


@pytest.fixture(scope="module")
def page(tmp_path_factory):
    f = tmp_path_factory.mktemp("v1") / "structurb.html"
    generer_page(f, dossier_catalogue=REPO_ROOT)
    return f.read_text(encoding="utf-8")


def test_icone_v1():
    svg = (ASSETS / "structurb_icone_v1.svg").read_text(encoding="utf-8")
    assert 'shape-rendering="crispEdges"' in svg
    for c in ("#000000", "#00FFFF", "#0000FF", "#00FF00", "#FF0000"):  # 5 bandes de STRUCTUR.ICO
        assert c in svg
    for f in ("structurb_icone_v1.png", "logo_certu.png", "logo_cerema.png", "min_techno.png", "max_pratique.png"):
        assert (ASSETS / f).stat().st_size > 0


def test_couleurs_couches_v1():
    # ModuleMain.bas, mesOptionsGen : QBColor 11, 2, 10, 12, 13
    assert COULEURS_COUCHES["surface"] == "#00FFFF"
    assert COULEURS_COUCHES["base1"] == "#008000"
    assert COULEURS_COUCHES["base2"] == "#00FF00"
    assert COULEURS_COUCHES["fondation1"] == "#FF0000"
    assert COULEURS_COUCHES["fondation2"] == "#FF00FF"


def test_coupe_quatre_couches():
    s = ouvrir_fichier_structures(REPO_ROOT / "Certu.str").structures[12]  # Enrobés/GB3/GB3
    ligne = next(l for l in s.grilles_pf["PF1_Q2"] if l.epaisseur_base_2 and l.epaisseur_fondation_2)
    detail = _couches_detail(ligne, s)
    assert [(role, rang) for role, rang, _, _ in detail] == [
        ("surface", 1), ("base", 1), ("base", 2), ("fondation", 1), ("fondation", 2)]
    svg = _svg_coupe([(f"{r}{n}" if r in ("base", "fondation") else r, lib, ep) for r, n, lib, ep in detail])
    for c in ("#00FFFF", "#008000", "#00FF00", "#FF0000", "#FF00FF"):
        assert f'fill="{c}"' in svg


def test_calques_dxf_aci():
    aci = {k: v[1] for k, v in CALQUES.items()}
    assert (aci["surface"], aci["base1"], aci["base2"], aci["fondation1"], aci["fondation2"]) == (4, 94, 3, 1, 6)


def test_page_icone_et_entete(page):
    assert re.search(r'<link rel="icon" href="data:image/svg\+xml', page)
    entete = re.search(r'<header class="hero">.*?</header>', page, flags=re.S).group(0)
    assert 'class="logo-app"' in entete
    assert "data:image/png" not in entete and "<img" not in entete  # logos institutionnels hors en-tête


def test_page_codes_visuels_v1(page):
    assert re.search(r"input:out-of-range[^{]*\{[^}]*#FF0000", page)
    assert "#FFFFE1" in page


def test_page_origine(page):
    origine = re.search(r'<section id="origine".*?</section>', page, flags=re.S).group(0)
    assert "portage non officiel" in origine
    assert origine.count('src="data:image/png;base64,') == 2


def test_pictogrammes_embarques_identiques():
    import base64
    from structurb._images import PICTOGRAMMES
    for nom, b64 in PICTOGRAMMES.items():
        assert base64.b64decode(b64) == (ASSETS / nom).read_bytes()


def test_pictogramme_dans_la_note():
    from structurb.epaisseur import ResultatQualite
    from structurb.rapport import _pictogrammes
    import dataclasses
    champs = {f.name for f in dataclasses.fields(ResultatQualite)}
    assert {"min_technique", "max_pratique"} <= champs
    class Q:  # double minimal
        min_technique, max_pratique = "Oui", "Non"
    html = _pictogrammes(Q())
    assert "Minimum technologique atteint" in html and "Maximum pratique" not in html
    assert "src=" not in html  # aucune ressource externe dans la note
