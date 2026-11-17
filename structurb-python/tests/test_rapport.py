"""Tests de la note de calcul HTML imprimable (structurb.rapport)."""

from pathlib import Path

import pytest

from structurb.catalogue import ouvrir_fichier_mat_surface, ouvrir_fichier_structures
from structurb.etude import dimensionner_etude
from structurb.rapport import note_calcul_html

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def cas_paves():
    cat_str = ouvrir_fichier_structures(REPO_ROOT / "Certu.str")
    cat_mts = ouvrir_fichier_mat_surface(REPO_ROOT / "Certu.mts")
    s = cat_str.structures[49]  # Pavés/GNT
    params = dict(
        type_voie="desserte",
        trafic_initial_pl=12,
        croissance_pct=2,
        duree_ans=20,
        plate_forme="PF2",
        station="Toulouse",
        hiver="HRNE",
        taille_agglo="moyenne",
        pente_sol_pourcent=0.5,
    )
    res = dimensionner_etude(cat_str, cat_mts, s, **params)
    return s, res, params


def test_note_html_contenu(cas_paves):
    s, res, p = cas_paves
    html = note_calcul_html(res, s, titre="Rue <des> Lilas & Co", variante="V1", date="17/11/2026", **p)
    html = html.replace(" ", " ")  # séparateur de milliers : espace fine insécable
    assert html.startswith("<!doctype html>")
    # Titre échappé
    assert "Rue &lt;des&gt; Lilas &amp; Co" in html
    assert "<des>" not in html
    # Trafic et NE (valeurs du lot 5)
    assert "104 244" in html and "20 849" in html and "30 000" in html
    # Couches nommées avec les épaisseurs du catalogue, lit de pose signalé
    assert "Pavés" in html and "GNT" in html
    assert "lit de pose" in html.lower()
    # Gel : indice de référence et verdict
    assert "36" in html and "Vérifiée" in html
    # Coupe dessinée en SVG, Q1 et Q2
    assert html.count('<svg role="img" aria-label="Coupe') == 2
    # Page autonome et imprimable : aucune ressource externe, styles d’impression
    for externe in ("<link", "<script src", "src=", "url(", "@import"):
        assert externe not in html


def test_donnees_lisibles_par_machine(cas_paves):
    import json
    import re

    s, res, p = cas_paves
    html = note_calcul_html(res, s, titre="Rue </script> test", **p)
    m = re.search(r'<script type="application/json" id="structurb-donnees">(.*?)</script>', html, re.S)
    assert m, "bloc JSON absent"
    d = json.loads(m.group(1))
    assert d["format"] == "structurb-note/1"
    assert d["titre"] == "Rue </script> test"  # pas de fin de bloc prématurée
    assert d["entrees"]["type_voie"] == "desserte" and d["entrees"]["plate_forme"] == "PF2"
    assert d["resultats"]["ne_equivalent"] == 20849
    assert d["resultats"]["ne_theorique"] == 30000
    q1 = d["resultats"]["q1"]
    assert q1["trouvee"] is True
    assert [(c["role"], c["epaisseur_cm"]) for c in q1["couches"]] == [("surface", 8), ("lit", 4), ("base", 15)]
    assert d["resultats"]["gel"]["indice_reference"] == 36
    assert d["resultats"]["gel"]["q1"]["verifiee"] is True
    # Repères stables pour les agents du navigateur
    for ident in ('id="resultats-trafic"', 'id="resultats-epaisseurs"', 'id="resultats-gel"'):
        assert ident in html
    assert "@media print" in html and "@page" in html


def test_note_html_sans_gel_ni_epaisseur(cas_paves):
    s, res, p = cas_paves
    from dataclasses import replace

    res_vide = replace(res, epaisseur=None, indice_gel_ref=None, gel_q1=None, gel_q2=None)
    html = note_calcul_html(res_vide, s, **p)
    assert "<svg" not in html
    assert "non trouvée" in html.lower() or "hors de la plage" in html.lower()


def test_note_html_options_mentionnees(cas_paves):
    s, res, p = cas_paves
    html = note_calcul_html(res, s, norme_2019=True, fidele_vb6=False, **p)
    assert "NF P98-086" in html
    assert "épaisseurs du catalogue" in html.lower()
