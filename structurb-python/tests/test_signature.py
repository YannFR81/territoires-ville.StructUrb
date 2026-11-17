"""Signature et charte graphique (couleurs du fork) de la page autonome et de la note de calcul."""

import re
from pathlib import Path

import pytest

from structurb.catalogue import ouvrir_fichier_mat_surface, ouvrir_fichier_structures
from structurb.etude import dimensionner_etude
from structurb.page import generer_page
from structurb.rapport import note_calcul_html
from structurb.signature import DEVISE, PALETTE, SIGNATURE_TEXTE

REPO_ROOT = Path(__file__).resolve().parents[2]
README = REPO_ROOT / "structurb-python" / "README.md"

# Palette commune avec dimensionnement-burmister/web (décision de YannFR81)
PALETTE_ATTENDUE = {"orange": "#DD590A", "bleu": "#5E99C5", "vert": "#179D87", "lie_de_vin": "#7F0541"}


@pytest.fixture(scope="module")
def page(tmp_path_factory):
    f = tmp_path_factory.mktemp("sig") / "structurb.html"
    generer_page(f, dossier_catalogue=REPO_ROOT)
    return f.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def note():
    cat_str = ouvrir_fichier_structures(REPO_ROOT / "Certu.str")
    cat_mts = ouvrir_fichier_mat_surface(REPO_ROOT / "Certu.mts")
    s = cat_str.structures[49]
    p = dict(type_voie="desserte", trafic_initial_pl=12, croissance_pct=2, duree_ans=20, plate_forme="PF2",
             station="Toulouse", hiver="HRNE", taille_agglo="moyenne", pente_sol_pourcent=0.5)
    r = dimensionner_etude(cat_str, cat_mts, s, **p)
    return note_calcul_html(r, s, **p)


def _texte(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html))


def test_palette():
    assert PALETTE == PALETTE_ATTENDUE


def test_signature_contenu():
    assert DEVISE == "Pour une fonction publique augmentée, pas remplacée."
    for morceau in ("YannFR81", "agent territorial au sein d’un conseil départemental", "Claude, IA d’Anthropic",
                    "Gemini Antigravity Hydrogen, IA de Google", "chacun relisant le travail de l’autre",
                    "Struct-Urb", "GPL v3", "sans garantie"):
        assert morceau in SIGNATURE_TEXTE


@pytest.mark.parametrize("quoi", ["page", "note", "readme"])
def test_signature_presente(quoi, page, note):
    html = {"page": page, "note": note, "readme": README.read_text(encoding="utf-8")}[quoi]
    texte = _texte(html)
    assert DEVISE in texte
    assert SIGNATURE_TEXTE in texte


@pytest.mark.parametrize("quoi", ["page", "note"])
def test_couleurs_appliquees(quoi, page, note):
    html = {"page": page, "note": note}[quoi].upper()
    for couleur in ("#DD590A", "#7F0541"):
        assert couleur in html
    assert "#1D4ED8" not in html  # ancien bleu de la page v2.0.0


@pytest.mark.parametrize("quoi", ["page", "note", "readme"])
def test_aucun_nom_de_collectivite(quoi, page, note):
    html = {"page": page, "note": note, "readme": README.read_text(encoding="utf-8")}[quoi]
    assert not re.search(r"\btarn\b|albi|castres|cd\s?81", html, flags=re.I)
