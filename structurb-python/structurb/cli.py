"""Ligne de commande : ``python -m structurb …``.

Sous-commandes :
- ``structures`` : structures du catalogue utilisables pour un type de voie ;
- ``stations`` : stations météo et indices de gel ;
- ``etude`` : dimensionnement complet, résumé à l’écran, note HTML et coupe DXF en option ;
- ``page`` : page HTML autonome (calcul dans le navigateur avec Pyodide).

Ajout du portage Python (pas d’équivalent dans le VB6, qui n’avait qu’une interface graphique).
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import List, Optional, Sequence

from .catalogue import (
    CatalogueStructures,
    StructureChaussee,
    ouvrir_fichier_mat_surface,
    ouvrir_fichier_structures,
)
from .epaisseur import PLATES_FORMES
from .etude import TYPES_STRUCTURE, dimensionner_etude, structures_compatibles
from .gel import HIVERS_REFERENCE, HORS_GEL, STATIONS_METEO
from .trafic import TYPES_VOIE

_RACINE_DEPOT = Path(__file__).resolve().parents[2]


class ErreurSaisie(Exception):
    """Erreur de saisie de l’utilisateur (code de sortie 2)."""


def _nombre(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def _dossier_catalogue(arg: Optional[str]) -> Path:
    if arg:
        return Path(arg)
    for d in (Path.cwd(), *Path.cwd().parents, _RACINE_DEPOT):
        if (d / "Certu.str").is_file() and (d / "Certu.mts").is_file():
            return d
    raise ErreurSaisie("Certu.str et Certu.mts introuvables : préciser --catalogue <dossier>.")


def _charger(arg: Optional[str]):
    d = _dossier_catalogue(arg)
    return ouvrir_fichier_structures(d / "Certu.str"), ouvrir_fichier_mat_surface(d / "Certu.mts")


def _choisir_structure(cat: CatalogueStructures, abrege: Optional[str], index: Optional[int], voie: str):
    """Retourne (index, structure). L’abrégé est cherché tel quel, puis sans espaces ni casse."""
    if index is not None:
        if not 0 <= index < len(cat.structures):
            raise ErreurSaisie(f"Index de structure hors limites : {index} (0 à {len(cat.structures) - 1}).")
        return index, cat.structures[index]
    if not abrege:
        raise ErreurSaisie("Préciser --structure <abrégé> ou --index <n>.")
    candidats = [(i, s) for i, s in enumerate(cat.structures) if s.abrege == abrege]
    if not candidats:
        cle = abrege.strip().lower()
        candidats = [(i, s) for i, s in enumerate(cat.structures) if s.abrege.strip().lower() == cle]
    if not candidats:
        raise ErreurSaisie(f"Structure inconnue : {abrege!r} (voir « python -m structurb structures »).")
    compatibles = {i for i, _ in structures_compatibles(cat, voie)}
    retenus = [(i, s) for i, s in candidats if i in compatibles]
    if not retenus:
        raise ErreurSaisie(
            f"La structure {abrege!r} n’est pas prévue pour ce type de voie ({voie}). "
            f"Variantes : {', '.join(f'index {i}' for i, _ in candidats)}."
        )
    if len(retenus) > 1:
        liste = ", ".join(
            f"index {i} ({_nombre(s.nb_essieux_min)} à {_nombre(s.nb_essieux_max)} essieux)" for i, s in retenus
        )
        raise ErreurSaisie(f"Plusieurs variantes de {abrege!r} pour ce type de voie : {liste}. Préciser --index.")
    return retenus[0]


def _cmd_structures(a: argparse.Namespace) -> int:
    cat, _ = _charger(a.catalogue)
    print(f"Structures utilisables en {a.voie} :")
    for i, s in structures_compatibles(cat, a.voie, type_structure=a.type):
        famille = TYPES_STRUCTURE.get(s.type_structure, "?")
        print(f"  index {i:2d}  {s.abrege.strip():22s} {famille:13s} "
              f"NE {_nombre(s.nb_essieux_min)} à {_nombre(s.nb_essieux_max)}")
    return 0


def _cmd_stations(a: argparse.Namespace) -> int:
    print(f"{'Station':22s} Dép.  Alt.   HE  HRNE   HC")
    for s in STATIONS_METEO:
        print(f"{s.nom:22s} {s.departement:>4s} {s.altitude:5d} {s.hre:4d} {s.hrne:5d} {s.hc:4d}")
    return 0


def _cmd_etude(a: argparse.Namespace) -> int:
    cat, mts = _charger(a.catalogue)
    idx, s = _choisir_structure(cat, a.structure, a.index, a.voie)
    params = dict(
        type_voie=a.voie,
        trafic_initial_pl=a.trafic,
        croissance_pct=a.croissance,
        duree_ans=a.duree,
        plate_forme=a.pf,
        cam=a.cam,
        station=a.station,
        hiver=a.hiver,
        taille_agglo=a.agglo,
        indice_gel_perso=a.indice_perso,
        epaisseur_non_gelive_cm=a.hn,
        couche_forme_traitee=a.forme_traitee,
        pente_sol_pourcent=a.pente,
        fidele_vb6=not a.epaisseurs_catalogue,
        norme_2019=a.norme_2019,
    )
    r = dimensionner_etude(cat, mts, s, **params)

    print(f"Structure : {s.abrege.strip()} (index {idx}) — plate-forme {a.pf}")
    print(f"Trafic cumulé : {_nombre(r.trafic_cumule)} PL · CAM {r.cam:g} · NE {_nombre(r.ne_equivalent)}")
    if r.ne_hors_limite:
        print("Attention : NE supérieur à 10 000 000, hors du domaine de Struct-Urb.")
    if r.etude_labo:
        print("Étude en laboratoire conseillée.")
    ep = r.epaisseur
    if ep is None:
        print("Épaisseurs non trouvées (NE hors de la plage de la structure).")
    else:
        print(f"NE théorique : {_nombre(ep.ne_theorique)}")
        for nom, q in (("Q1", ep.q1), ("Q2", ep.q2)):
            l = q.ligne
            if not q.trouvee:
                print(f"  {nom} : non trouvée")
                continue
            print(f"  {nom} : surface {l.epaisseur_surface} · base {l.epaisseur_base_1}+{l.epaisseur_base_2}"
                  f" · fondation {l.epaisseur_fondation_1}+{l.epaisseur_fondation_2} cm")
    if r.indice_gel_ref is not None:
        print(f"Indice de gel de référence : {r.indice_gel_ref} °C·j")
    for nom, g in (("Q1", r.gel_q1), ("Q2", r.gel_q2)):
        if g is not None:
            adm = "hors gel" if g.indice_gel_adm == HORS_GEL else f"{g.indice_gel_adm} °C·j"
            print(f"  Gel {nom} : admissible {adm} → {'vérifiée' if g.verifiee else 'NON vérifiée'}")

    jour = a.date or date.today().strftime("%d/%m/%Y")
    if a.html:
        from .rapport import note_calcul_html

        html = note_calcul_html(r, s, titre=a.titre, variante=a.variante, date=jour, **params)
        Path(a.html).write_text(html, encoding="utf-8")
        print(f"Note de calcul HTML : {a.html}")
    if a.dxf:
        from .dxf import ecrire_coupe_dxf

        if ep is None:
            raise ErreurSaisie("Pas de coupe à dessiner : épaisseurs non trouvées.")
        ecrire_coupe_dxf(a.dxf, r, s, titre=a.titre, plate_forme=a.pf, unite=a.unite)
        print(f"Coupe DXF : {a.dxf}")
    return 0


def _cmd_page(a: argparse.Namespace) -> int:
    from .page import generer_page

    generer_page(a.sortie, dossier_catalogue=_dossier_catalogue(a.catalogue))
    print(f"Page autonome : {a.sortie} (ouvrir dans un navigateur ; Internet requis pour charger Pyodide)")
    return 0


def construire_analyseur() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m structurb",
        description="Struct-Urb en Python : dimensionnement des structures de chaussées urbaines (catalogue CERTU).",
    )
    p.add_argument("--catalogue", help="dossier contenant Certu.str et Certu.mts (par défaut : recherché)")
    sp = p.add_subparsers(dest="commande", required=True)

    ps = sp.add_parser("structures", help="structures utilisables pour un type de voie")
    ps.add_argument("--voie", required=True, choices=TYPES_VOIE)
    ps.add_argument("--type", choices=list(TYPES_STRUCTURE.values()), help="famille de structure")
    ps.set_defaults(func=_cmd_structures)

    pt = sp.add_parser("stations", help="stations météo et indices de gel")
    pt.set_defaults(func=_cmd_stations)

    pp = sp.add_parser("page", help="page HTML autonome (calcul dans le navigateur, pilotable par les IA)")
    pp.add_argument("--sortie", default="structurb.html", help="fichier HTML à écrire")
    pp.set_defaults(func=_cmd_page)

    pe = sp.add_parser("etude", help="dimensionnement complet d’une structure")
    g = pe.add_mutually_exclusive_group(required=True)
    g.add_argument("--structure", help="abrégé de la structure, ex. « Pavés/GNT »")
    g.add_argument("--index", type=int, help="position de la structure dans le catalogue")
    pe.add_argument("--voie", required=True, choices=TYPES_VOIE)
    pe.add_argument("--trafic", required=True, type=int, help="trafic initial en PL/j")
    pe.add_argument("--croissance", required=True, type=int, help="taux de croissance annuel en %% (0 à 5)")
    pe.add_argument("--duree", required=True, type=int, help="durée de service en années")
    pe.add_argument("--pf", required=True, choices=PLATES_FORMES, help="classe de plate-forme")
    pe.add_argument("--cam", type=float, help="CAM imposé (sinon CAM préconisé)")
    gel = pe.add_argument_group("vérification au gel")
    gel.add_argument("--station", help="station météo, ex. « Toulouse »")
    gel.add_argument("--hiver", default="HRNE", choices=HIVERS_REFERENCE)
    gel.add_argument("--agglo", default="petite", choices=("petite", "moyenne", "grande"))
    gel.add_argument("--indice-perso", type=int, help="indice de gel de référence personnel (°C·j)")
    gel.add_argument("--pente", type=float, help="pente de l’essai de gonflement du sol support")
    gel.add_argument("--hn", type=float, default=0.0, help="épaisseur de couche de forme non gélive (cm)")
    gel.add_argument("--forme-traitee", action="store_true", help="couche de forme traitée")
    gel.add_argument("--norme-2019", action="store_true", help="méthode simplifiée NF P98-086 (Kcr 0,7)")
    gel.add_argument("--epaisseurs-catalogue", action="store_true",
                     help="calcul au gel sans lit de pose ni 3 cm d’affichage")
    sortie = pe.add_argument_group("sorties")
    sortie.add_argument("--html", help="fichier de note de calcul HTML à écrire")
    sortie.add_argument("--dxf", help="fichier DXF de la coupe annotée à écrire")
    sortie.add_argument("--unite", default="m", choices=("m", "cm", "mm"), help="unité du dessin DXF")
    sortie.add_argument("--titre", default="", help="titre de l’étude")
    sortie.add_argument("--variante", default="")
    sortie.add_argument("--date", default="", help="date affichée (par défaut : aujourd’hui)")
    pe.set_defaults(func=_cmd_etude)
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    a = construire_analyseur().parse_args(argv)
    try:
        return a.func(a)
    except ErreurSaisie as e:
        print(f"Erreur : {e}", file=sys.stderr)
        return 2
    except (ValueError, KeyError) as e:
        print(f"Erreur : {e}", file=sys.stderr)
        return 2
