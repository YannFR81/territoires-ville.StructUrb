"""Export DXF de la coupe de chaussée annotée (Q1 et Q2).

Ajout du portage Python (le VB6 ne dessinait les « carottes » qu’à l’écran).
Format DXF R12 (AC1009) en texte, sans dépendance, lisible par AutoCAD, COVADIS, LibreCAD, QCAD.
Encodage cp1252 (``$DWGCODEPAGE = ANSI_1252``) pour les accents ; pas de tiret long ni de point
médian dans les textes (absents de la police txt.shx).

Dessin (origine en surface de chaussée, axe Y vers le haut, épaisseurs vers le bas) :
- une coupe par qualité (Q1 à gauche, Q2 à droite) de 1 m de large ;
- une couche = un contour fermé (POLYLINE) et un remplissage (SOLID) sur le calque de son rôle ;
- annotations (matériau et épaisseur, épaisseur totale, titre, NE théorique) sur ``STRUCTURB_TEXTE`` ;
- plate-forme : trait et symbole de terrain sur ``STRUCTURB_PLATEFORME``.
Les épaisseurs sont celles du catalogue ; le lit de pose des pavés et dalles (4 cm) est dessiné,
les 3 cm « d’affichage » d’une surface sans épaisseur ne le sont pas (couche annotée « sans épaisseur »).
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple, Union

from .catalogue import StructureChaussee
from .epaisseur import ResultatQualite
from .etude import ResultatEtude
from .rapport import _couches_detail, cle_couleur

# Facteur de conversion des centimètres vers l’unité du dessin
UNITES = {"m": 0.01, "cm": 1.0, "mm": 10.0}

# Calques : (nom, couleur AutoCAD ACI). Couleurs des couches : charte de Struct-Urb V1
# (ModuleMain.bas, mesOptionsGen), ramenées aux couleurs ACI les plus proches :
# surface cyan 4, base 1 vert foncé 94, base 2 vert 3, fondation 1 rouge 1, fondation 2 magenta 6.
CALQUES = {
    "surface": ("STRUCTURB_SURFACE", 4),
    "lit": ("STRUCTURB_LIT_POSE", 42),
    "base1": ("STRUCTURB_BASE", 94),
    "base2": ("STRUCTURB_BASE_2", 3),
    "fondation1": ("STRUCTURB_FONDATION", 1),
    "fondation2": ("STRUCTURB_FONDATION_2", 6),
    "texte": ("STRUCTURB_TEXTE", 7),
    "plateforme": ("STRUCTURB_PLATEFORME", 34),
    "cadre": ("STRUCTURB_CADRE", 7),
}

_LARGEUR_CM = 100.0      # largeur d’une coupe
_ECART_CM = 220.0        # décalage horizontal entre Q1 et Q2
_TEXTE_CM = 2.5          # hauteur des textes courants
_TITRE_CM = 4.0          # hauteur des titres


class _Dxf:
    def __init__(self, k: float) -> None:
        self.k = k
        self.ents: List[str] = []

    def _xy(self, code: int, x: float, y: float) -> List[str]:
        return [str(code), f"{x * self.k:.4f}", str(code + 10), f"{y * self.k:.4f}", str(code + 20), "0.0"]

    def _ajouter(self, *lignes: str) -> None:
        self.ents.extend(lignes)

    def polyligne(self, calque: str, pts: List[Tuple[float, float]], fermee: bool = True) -> None:
        self._ajouter("0", "POLYLINE", "8", calque, "66", "1", "70", "1" if fermee else "0",
                      *self._xy(10, 0.0, 0.0))
        for x, y in pts:
            self._ajouter("0", "VERTEX", "8", calque, *self._xy(10, x, y))
        self._ajouter("0", "SEQEND", "8", calque)

    def ligne(self, calque: str, x1: float, y1: float, x2: float, y2: float) -> None:
        self._ajouter("0", "LINE", "8", calque, *self._xy(10, x1, y1), *self._xy(11, x2, y2))

    def solide(self, calque: str, x0: float, y0: float, x1: float, y1: float) -> None:
        # Ordre des sommets d’un SOLID : 1-2-4-3 (en « Z »)
        self._ajouter("0", "SOLID", "8", calque, *self._xy(10, x0, y0), *self._xy(11, x1, y0),
                      *self._xy(12, x0, y1), *self._xy(13, x1, y1))

    def texte(self, calque: str, x: float, y: float, h: float, txt: str, centre_v: bool = True) -> None:
        if centre_v:
            # Justification : gauche (72 = 0), milieu vertical (73 = 2), point d’alignement 11/21
            self._ajouter("0", "TEXT", "8", calque, *self._xy(10, x, y), "40", f"{h * self.k:.4f}",
                          "1", txt, "72", "0", *self._xy(11, x, y), "73", "2")
        else:
            self._ajouter("0", "TEXT", "8", calque, *self._xy(10, x, y), "40", f"{h * self.k:.4f}", "1", txt)


def _nombre(n: int) -> str:
    # Espace ordinaire : l’espace fine insécable n’existe pas en cp1252
    return f"{int(n):,}".replace(",", " ")


def _dessiner_qualite(d: _Dxf, x0: float, nom: str, q: ResultatQualite, s: StructureChaussee,
                      plate_forme: str) -> None:
    t = CALQUES["texte"][0]
    d.texte(t, x0, 2 * _TITRE_CM, _TITRE_CM, f"{nom} - {s.abrege.strip()} - {plate_forme}", centre_v=False)
    if not q.trouvee:
        msg = (
            f"{nom} : sans objet (giratoire)"
            if nom == "Q2" and all(e == 0 for e in q.epaisseurs)
            else "Épaisseur non trouvée (maximum pratique atteint)"
        )
        d.texte(t, x0, -_TEXTE_CM * 2, _TEXTE_CM, msg)
        return
    y = 0.0
    x1 = x0 + _LARGEUR_CM
    for role, rang, libelle, ep in _couches_detail(q.ligne, s):
        calque = CALQUES[cle_couleur(role, rang)][0]
        if ep > 0:
            y1 = y - ep
            d.solide(calque, x0, y, x1, y1)
            d.polyligne(calque, [(x0, y), (x1, y), (x1, y1), (x0, y1)])
            d.texte(t, x1 + 5, (y + y1) / 2, _TEXTE_CM, f"{libelle} : {ep} cm")
            y = y1
        else:
            d.ligne(calque, x0, y, x1, y)
            d.texte(t, x1 + 5, y, _TEXTE_CM, f"{libelle} (sans épaisseur)")
    total = -y
    # Plate-forme et symbole de terrain
    pf = CALQUES["plateforme"][0]
    d.ligne(pf, x0 - 10, y, x1 + 10, y)
    for i in range(12):
        xa = x0 - 10 + i * 10
        d.ligne(pf, xa, y, xa - 4, y - 4)
    d.texte(t, x1 + 5, y - 3, _TEXTE_CM, f"Plate-forme {plate_forme}")
    # Cote verticale de l’épaisseur totale (côté gauche)
    c = CALQUES["cadre"][0]
    xc = x0 - 15
    d.ligne(c, xc, 0.0, xc, y)
    d.ligne(c, xc - 2, 0.0, xc + 2, 0.0)
    d.ligne(c, xc - 2, y, xc + 2, y)
    d.texte(t, x0, y - 12, _TEXTE_CM, f"Épaisseur totale : {total:g} cm", centre_v=False)


def coupe_dxf(
    resultat: ResultatEtude,
    structure: StructureChaussee,
    *,
    plate_forme: str,
    titre: str = "",
    unite: str = "m",
) -> str:
    """Retourne le contenu DXF (R12) de la coupe annotée Q1 / Q2 d’une étude."""
    if unite not in UNITES:
        raise ValueError(f"Unité inconnue : {unite!r} (attendu : {tuple(UNITES)}).")
    ep = resultat.epaisseur
    if ep is None:
        raise ValueError("Épaisseurs non trouvées : pas de coupe à dessiner.")
    d = _Dxf(UNITES[unite])
    t = CALQUES["texte"][0]
    entete = titre.strip() or "Coupe de chaussée"
    d.texte(t, 0.0, 6 * _TITRE_CM, _TITRE_CM * 1.25, f"{entete} - Struct-Urb", centre_v=False)
    d.texte(t, 0.0, 4.5 * _TITRE_CM, _TEXTE_CM,
            f"NE {_nombre(resultat.ne_equivalent)} - NE théorique {_nombre(ep.ne_theorique)} - "
            f"épaisseurs en cm (catalogue CERTU) - dessin en {unite}", centre_v=False)
    _dessiner_qualite(d, 0.0, "Q1", ep.q1, structure, plate_forme)
    _dessiner_qualite(d, _ECART_CM, "Q2", ep.q2, structure, plate_forme)

    calques = sorted({v for v in CALQUES.values()})
    sortie: List[str] = [
        "0", "SECTION", "2", "HEADER",
        "9", "$ACADVER", "1", "AC1009",
        "9", "$DWGCODEPAGE", "3", "ANSI_1252",
        "0", "ENDSEC",
        "0", "SECTION", "2", "TABLES",
        "0", "TABLE", "2", "LTYPE", "70", "1",
        "0", "LTYPE", "2", "CONTINUOUS", "70", "0", "3", "Continu", "72", "65", "73", "0", "40", "0.0",
        "0", "ENDTAB",
        "0", "TABLE", "2", "LAYER", "70", str(len(calques) + 1),
        "0", "LAYER", "2", "0", "70", "0", "62", "7", "6", "CONTINUOUS",
    ]
    for nom, couleur in calques:
        sortie += ["0", "LAYER", "2", nom, "70", "0", "62", str(couleur), "6", "CONTINUOUS"]
    sortie += [
        "0", "ENDTAB",
        "0", "TABLE", "2", "STYLE", "70", "1",
        "0", "STYLE", "2", "STANDARD", "70", "0", "40", "0.0", "41", "1.0", "50", "0.0",
        "71", "0", "42", "2.5", "3", "txt", "4", "",
        "0", "ENDTAB",
        "0", "ENDSEC",
        "0", "SECTION", "2", "ENTITIES",
        *d.ents,
        "0", "ENDSEC",
        "0", "EOF",
    ]
    return "\n".join(sortie) + "\n"


def ecrire_coupe_dxf(
    chemin: Union[str, Path],
    resultat: ResultatEtude,
    structure: StructureChaussee,
    *,
    plate_forme: str,
    titre: str = "",
    unite: str = "m",
) -> None:
    """Écrit la coupe annotée au format DXF R12 (cp1252, fins de ligne CRLF)."""
    contenu = coupe_dxf(resultat, structure, plate_forme=plate_forme, titre=titre, unite=unite)
    with Path(chemin).open("w", encoding="cp1252", errors="replace", newline="\r\n") as f:
        f.write(contenu)
