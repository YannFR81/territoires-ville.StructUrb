"""Tests de l’aide en ligne et de la documentation (structurb.aide)."""

import json
import re
from pathlib import Path

import pytest

from structurb.aide import DOCUMENTATION, SUJETS_CERTU, aide_certu, rtf_texte
from structurb.cli import main

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_rtf_texte_elementaire():
    rtf = rb"{\rtf1\ansi{\fonttbl{\f0 Arial;}}{\*\generator x;}D\'e9but\par {\pict 0123abcd}suite\tab fin}"
    assert rtf_texte(rtf) == "Début\nsuite fin"


@pytest.fixture(scope="module")
def aide():
    return aide_certu(REPO_ROOT)


def test_sept_rubriques_certu(aide):
    assert set(aide) == set(SUJETS_CERTU) == {"voie", "trafic", "cam", "structure", "surface", "plateforme", "gel"}
    for sujet, a in aide.items():
        assert a["titre"] and len(a["texte"]) > 500, sujet
        # Aucun reste de syntaxe RTF ni caractère de remplacement
        assert "\\" not in a["texte"] and "{" not in a["texte"] and "�" not in a["texte"], sujet
        assert not re.search(r"[-]", a["texte"]), sujet


def test_contenu_certu_fidele(aide):
    assert "Voie de desserte" in aide["voie"]["texte"]
    assert "NE" in aide["cam"]["texte"] and "CAM" in aide["cam"]["texte"]
    assert "hiver exceptionnel" in aide["gel"]["texte"]
    assert "Indice de gel personnel" in aide["gel"]["texte"]
    assert "PF2" in aide["plateforme"]["texte"]
    # Les tableaux qui étaient des images dans l’aide d’origine sont signalés
    assert "tableau" in aide["gel"]["texte"].lower() and "non repris" in aide["gel"]["texte"]


def test_documentation_maison():
    cles = {d["id"] for d in DOCUMENTATION}
    assert {"fonctionnement", "norme", "utilisation", "limites"} <= cles
    texte = " ".join(d["html"] for d in DOCUMENTATION)
    # Fonctionnement : les étapes et les formules du calcul
    for mot in ("365", "NE", "CAM", "palier", "Q1", "Q2", "indice de gel admissible", "0,6"):
        assert mot.lower() in texte.lower(), mot
    # Norme : expliquée sans extrait, avec ses différences
    assert "NF P98-086" in texte and "Kcr" in texte and "0,7" in texte
    assert "aucun extrait" in texte.lower()


def test_commande_aide(capsys):
    assert main(["aide"]) == 0
    sortie = capsys.readouterr().out
    for s in SUJETS_CERTU:
        assert s in sortie
    assert main(["aide", "gel"]) == 0
    assert "hiver exceptionnel" in capsys.readouterr().out
    assert main(["aide", "fonctionnement"]) == 0
    assert "NE" in capsys.readouterr().out
    assert main(["aide", "inconnu"]) == 2


def test_page_aide_integree(tmp_path):
    from structurb.page import generer_page

    f = tmp_path / "p.html"
    generer_page(f, dossier_catalogue=REPO_ROOT)
    page = f.read_text(encoding="utf-8")
    # Aide CERTU repliable dans chaque rubrique du formulaire
    for sujet in ("voie", "trafic", "gel", "structure", "plateforme"):
        assert f'id="aide-{sujet}"' in page, sujet
    # Documentation complète
    for ident in ("doc-fonctionnement", "doc-norme", "doc-utilisation", "doc-limites", "doc-aide-certu"):
        assert f'id="{ident}"' in page, ident
    # Données d’aide pour les agents
    m = re.search(r'<script type="application/json" id="structurb-aide">(.*?)</script>', page, re.S)
    donnees = json.loads(m.group(1))
    assert set(donnees["certu"]) == set(SUJETS_CERTU)
    assert "window.structurb" in page and "aide:" in page
    # Correction de l’aide rapide : étude labo entre 750 et 1 000 PL/j
    assert "750" in page and "1 000" in page.replace(" ", " ")
