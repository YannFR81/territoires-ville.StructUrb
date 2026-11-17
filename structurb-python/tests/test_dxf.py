"""Tests de l’export DXF de la coupe de chaussée annotée (structurb.dxf)."""

from pathlib import Path

import pytest

from structurb.catalogue import ouvrir_fichier_mat_surface, ouvrir_fichier_structures
from structurb.dxf import coupe_dxf, ecrire_coupe_dxf
from structurb.etude import dimensionner_etude

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def catalogues():
    return (
        ouvrir_fichier_structures(REPO_ROOT / "Certu.str"),
        ouvrir_fichier_mat_surface(REPO_ROOT / "Certu.mts"),
    )


def _etude(catalogues, index, voie, trafic, pf="PF2"):
    cat_str, cat_mts = catalogues
    s = cat_str.structures[index]
    return s, dimensionner_etude(cat_str, cat_mts, s, type_voie=voie, trafic_initial_pl=trafic,
                                 croissance_pct=2, duree_ans=20, plate_forme=pf)


def _paires(texte):
    lignes = texte.splitlines()
    assert len(lignes) % 2 == 0
    return [(int(lignes[i].strip()), lignes[i + 1]) for i in range(0, len(lignes), 2)]


def _entites(paires):
    """Liste des entités : (type, {code: [valeurs]})."""
    ents, cour, dans = [], None, False
    for code, val in paires:
        if code == 2 and cour is None and val == "ENTITIES":
            dans = True
            continue
        if not dans:
            continue
        if code == 0:
            if cour:
                ents.append(cour)
            if val in ("ENDSEC", "EOF"):
                break
            cour = (val, {})
        elif cour is not None:
            cour[1].setdefault(code, []).append(val)
    return ents


def test_structure_du_fichier(catalogues):
    s, r = _etude(catalogues, 49, "desserte", 12)  # Pavés/GNT, NE théorique 30 000
    txt = coupe_dxf(r, s, titre="Rue des Lilas", plate_forme="PF2")
    p = _paires(txt)
    assert p[0] == (0, "SECTION") and p[-1] == (0, "EOF")
    valeurs = [v for _, v in p]
    assert "AC1009" in valeurs  # DXF R12
    assert "ANSI_1252" in valeurs
    for calque in ("STRUCTURB_SURFACE", "STRUCTURB_LIT_POSE", "STRUCTURB_BASE", "STRUCTURB_TEXTE", "STRUCTURB_PLATEFORME"):
        assert calque in valeurs
    # Chaque POLYLINE se termine par SEQEND
    types = [t for t, _ in _entites(p)]
    assert types.count("POLYLINE") == types.count("SEQEND") > 0


def test_epaisseurs_dessinees_et_annotees(catalogues):
    s, r = _etude(catalogues, 49, "desserte", 12)
    ents = _entites(_paires(coupe_dxf(r, s, plate_forme="PF2", unite="cm")))
    textes = [d[1][0] for t, d in ents if t == "TEXT"]
    # Q1 : pavés 8 cm, lit de pose 4 cm, GNT 15 cm ; total 27 cm
    assert any("Pavés" in t and "8 cm" in t for t in textes)
    assert any("lit de pose" in t and "4 cm" in t for t in textes)
    assert any("GNT" in t and "15 cm" in t for t in textes)
    assert any("27 cm" in t for t in textes)
    assert any("Q1" in t for t in textes) and any("Q2" in t for t in textes)
    assert any("30 000" in t.replace(" ", " ") for t in textes)
    # En centimètres, la coupe Q1 descend de 0 à -27 (remplissages SOLID des couches)
    ys = [float(y) for t, d in ents if t == "SOLID" for c in (20, 21, 22, 23) for y in d.get(c, [])]
    assert min(ys) == pytest.approx(-27.0) or min(ys) <= -27.0
    assert max(ys) == pytest.approx(0.0)


def test_unites(catalogues):
    s, r = _etude(catalogues, 49, "desserte", 12)
    def profondeur(unite):
        ents = _entites(_paires(coupe_dxf(r, s, plate_forme="PF2", unite=unite)))
        return min(float(y) for t, d in ents if t == "SOLID" for c in (20, 22) for y in d.get(c, []))
    assert profondeur("m") == pytest.approx(profondeur("cm") / 100)
    assert profondeur("mm") == pytest.approx(profondeur("cm") * 10)
    with pytest.raises(ValueError):
        coupe_dxf(r, s, plate_forme="PF2", unite="pouce")


def test_surface_sans_epaisseur_et_sans_epaisseur_trouvee(catalogues):
    # ES/GNT : enduit sans épaisseur → annoté, pas de 3 cm dessinés
    s, r = _etude(catalogues, 0, "desserte", 10)
    textes = [d[1][0] for t, d in _entites(_paires(coupe_dxf(r, s, plate_forme="PF2"))) if t == "TEXT"]
    assert any("ES" in t and "sans épaisseur" in t for t in textes)
    assert not any("3 cm" in t for t in textes)
    # Pas d’épaisseur trouvée : erreur explicite
    from dataclasses import replace
    with pytest.raises(ValueError):
        coupe_dxf(replace(r, epaisseur=None), s, plate_forme="PF2")


def test_ecriture_cp1252(tmp_path, catalogues):
    s, r = _etude(catalogues, 49, "desserte", 12)
    f = tmp_path / "coupe.dxf"
    ecrire_coupe_dxf(f, r, s, titre="Étude é", plate_forme="PF2")
    brut = f.read_bytes()
    assert "Pavés".encode("cp1252") in brut and b"\r\n" in brut
    assert b"?" not in brut  # aucun caractère perdu à l’encodage


def test_lecture_par_ezdxf(tmp_path, catalogues):
    ezdxf = pytest.importorskip("ezdxf")
    s, r = _etude(catalogues, 63, "desserte", 30)  # Dalles/BC5
    f = tmp_path / "coupe.dxf"
    ecrire_coupe_dxf(f, r, s, titre="Contrôle", plate_forme="PF2")
    doc = ezdxf.readfile(f)
    assert doc.dxfversion == "AC1009"
    assert len(list(doc.modelspace().query("TEXT"))) > 5


def test_caracteres_compatibles_txt_shx(catalogues):
    s, r = _etude(catalogues, 49, "desserte", 12)
    textes = [d[1][0] for t, d in _entites(_paires(coupe_dxf(r, s, titre="Rue", plate_forme="PF2"))) if t == "TEXT"]
    for t in textes:
        assert "–" not in t and "·" not in t and "\u202f" not in t
