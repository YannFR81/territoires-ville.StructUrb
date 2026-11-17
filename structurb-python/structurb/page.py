"""Page autonome : un seul fichier HTML qui exécute ce moteur Python dans le navigateur (Pyodide).

Ajout du portage Python. La page embarque les sources du paquet ``structurb`` et les catalogues
``Certu.str`` / ``Certu.mts`` ; seule Pyodide est chargée depuis Internet (version figée).

Elle est utilisable par une personne (formulaire) et par un assistant IA du navigateur :
- formulaire balisé (``<label for>``, ``name``, ``id`` stables, zone de résultat ``aria-live``) ;
- interface JavaScript ``window.structurb.calculer(paramètres)`` ;
- outil ``dimensionner_chaussee`` décrit en JSON Schema (bloc ``#structurb-outil``) et déclaré via
  ``navigator.modelContext`` (WebMCP, expérimental) quand le navigateur le propose.

``calculer_depuis_json`` est le point d’entrée appelé par la page ; il est testé ici en Python.
"""

from __future__ import annotations

import base64
from html import escape
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .catalogue import ouvrir_fichier_mat_surface, ouvrir_fichier_structures
from .epaisseur import PLATES_FORMES
from .etude import TYPES_STRUCTURE, dimensionner_etude, structures_compatibles
from .gel import HIVERS_REFERENCE, STATIONS_METEO, obtenir_station
from .rapport import NOMS_VOIE, _json_script, donnees_note, note_calcul_html
from .signature import signature_html
from .trafic import TYPES_VOIE

PYODIDE_VERSION = "0.26.4"
PYODIDE_URL = f"https://cdn.jsdelivr.net/pyodide/v{PYODIDE_VERSION}/full/"

_DOSSIER_PAQUET = Path(__file__).resolve().parent
_RACINE_DEPOT = _DOSSIER_PAQUET.parents[1]
_AGGLOS = ("petite", "moyenne", "grande")
_UNITES = ("m", "cm", "mm")

OUTIL: Dict[str, Any] = {
    "name": "dimensionner_chaussee",
    "description": (
        "Dimensionne une structure de chaussée urbaine avec le catalogue CERTU de Struct-Urb : "
        "trafic cumulé, nombre d’essieux équivalents (NE), épaisseurs des couches pour les qualités "
        "de chantier Q1 et Q2, et vérification au gel si une station (ou un indice personnel) et la pente "
        "du sol sont fournies. Choisir la structure par son index (voir window.structurb.structures(type_voie))."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "index": {"type": "integer", "description": "position de la structure dans le catalogue"},
            "structure": {"type": "string", "description": "abrégé de la structure, si index absent (ex. « Pavés/GNT »)"},
            "type_voie": {"type": "string", "enum": list(TYPES_VOIE)},
            "trafic_initial_pl": {"type": "integer", "minimum": 0, "description": "poids lourds par jour"},
            "croissance_pct": {"type": "integer", "minimum": 0, "maximum": 5, "default": 2},
            "duree_ans": {"type": "integer", "minimum": 1, "default": 20},
            "plate_forme": {"type": "string", "enum": list(PLATES_FORMES)},
            "station": {"type": "string", "description": "station météo (voir window.structurb.stations())"},
            "hiver": {"type": "string", "enum": list(HIVERS_REFERENCE), "default": "HRNE"},
            "taille_agglo": {"type": "string", "enum": list(_AGGLOS), "default": "petite"},
            "indice_gel_perso": {"type": "integer", "minimum": 0, "description": "indice de gel de référence local (°C·j)"},
            "pente_sol_pourcent": {"type": "number", "minimum": 0, "description": "pente de l’essai de gonflement du sol"},
            "epaisseur_non_gelive_cm": {"type": "number", "minimum": 0, "default": 0},
            "couche_forme_traitee": {"type": "boolean", "default": False},
            "norme_2019": {"type": "boolean", "default": False, "description": "méthode simplifiée NF P98-086 (Kcr 0,7)"},
            "fidele_vb6": {"type": "boolean", "default": True, "description": "épaisseurs du gel comme le VB6"},
            "titre": {"type": "string"},
            "variante": {"type": "string"},
            "unite_dxf": {"type": "string", "enum": list(_UNITES), "default": "m"},
        },
        "required": ["type_voie", "trafic_initial_pl", "plate_forme"],
    },
}


class _ErreurSaisie(ValueError):
    pass


@lru_cache(maxsize=4)
def _catalogues(dossier: str):
    d = Path(dossier)
    return ouvrir_fichier_structures(d / "Certu.str"), ouvrir_fichier_mat_surface(d / "Certu.mts")


def _dossier(dossier_catalogue: Optional[Union[str, Path]]) -> Path:
    if dossier_catalogue is not None:
        return Path(dossier_catalogue)
    for d in (Path.cwd(), _RACINE_DEPOT):
        if (d / "Certu.str").is_file() and (d / "Certu.mts").is_file():
            return d
    raise _ErreurSaisie("Catalogues Certu.str et Certu.mts introuvables.")


def _entier(p: dict, cle: str, nom: str, defaut=None, mini=None, maxi=None) -> Optional[int]:
    v = p.get(cle, defaut)
    if v is None or v == "":
        return defaut
    try:
        if isinstance(v, bool) or (isinstance(v, float) and not v.is_integer()):
            raise ValueError
        n = int(v)
    except (TypeError, ValueError):
        raise _ErreurSaisie(f"{nom} : nombre entier attendu (reçu : {v!r}).") from None
    if (mini is not None and n < mini) or (maxi is not None and n > maxi):
        bornes = f"{mini} à {maxi}" if maxi is not None else f"au moins {mini}"
        raise _ErreurSaisie(f"{nom} : valeur hors limites ({n}, attendu {bornes}).")
    return n


def _reel(p: dict, cle: str, nom: str, defaut=None, mini=None) -> Optional[float]:
    v = p.get(cle, defaut)
    if v is None or v == "":
        return defaut
    try:
        if isinstance(v, bool):
            raise ValueError
        x = float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        raise _ErreurSaisie(f"{nom} : nombre attendu (reçu : {v!r}).") from None
    if mini is not None and x < mini:
        raise _ErreurSaisie(f"{nom} : valeur négative non admise ({x}).")
    return x


def _choix(p: dict, cle: str, nom: str, valeurs, defaut=None) -> Optional[str]:
    v = p.get(cle, defaut)
    if v is None or v == "":
        return defaut
    if v not in valeurs:
        raise _ErreurSaisie(f"{nom} : valeur inconnue {v!r} (attendu : {', '.join(valeurs)}).")
    return v


def _booleen(p: dict, cle: str, defaut: bool) -> bool:
    v = p.get(cle, defaut)
    if isinstance(v, str):
        return v.strip().lower() in ("1", "true", "oui", "on")
    return bool(v)


def calculer_depuis_json(params_json: str, dossier_catalogue: Optional[Union[str, Path]] = None) -> str:
    """Point d’entrée de la page : paramètres JSON → résultat JSON.

    Retour : ``{"ok": true, "donnees": …, "resume": texte, "html": note, "dxf": coupe ou null}``
    ou ``{"ok": false, "erreur": message}`` (message en français, lisible par une personne ou une IA).
    """
    try:
        p = json.loads(params_json)
        if not isinstance(p, dict):
            raise _ErreurSaisie("Paramètres : objet JSON attendu.")
        return json.dumps(_calculer(p, _dossier(dossier_catalogue)), ensure_ascii=False)
    except json.JSONDecodeError as e:
        return json.dumps({"ok": False, "erreur": f"JSON invalide : {e}"}, ensure_ascii=False)
    except (ValueError, KeyError) as e:
        msg = e.args[0] if e.args else str(e)
        return json.dumps({"ok": False, "erreur": str(msg)}, ensure_ascii=False)


def _calculer(p: dict, dossier: Path) -> dict:
    cat, mts = _catalogues(str(dossier))
    voie = _choix(p, "type_voie", "Type de voie", TYPES_VOIE)
    if voie is None:
        raise _ErreurSaisie("Type de voie obligatoire.")
    pf = _choix(p, "plate_forme", "Classe de plate-forme", PLATES_FORMES)
    if pf is None:
        raise _ErreurSaisie("Classe de plate-forme obligatoire.")

    idx = _entier(p, "index", "Index de structure")
    compatibles = {i for i, _ in structures_compatibles(cat, voie)}
    if idx is None:
        abrege = p.get("structure")
        if not abrege:
            raise _ErreurSaisie("Structure obligatoire : préciser « index » ou « structure ».")
        cand = [i for i, s in enumerate(cat.structures) if s.abrege == abrege] or [
            i for i, s in enumerate(cat.structures) if s.abrege.strip().lower() == str(abrege).strip().lower()
        ]
        if not cand:
            raise _ErreurSaisie(f"Structure inconnue : {abrege!r}.")
        cand = [i for i in cand if i in compatibles] or cand
        idx = cand[0]
    if not 0 <= idx < len(cat.structures):
        raise _ErreurSaisie(f"Index de structure hors limites : {idx} (0 à {len(cat.structures) - 1}).")
    if idx not in compatibles:
        raise _ErreurSaisie(
            f"La structure {cat.structures[idx].abrege.strip()!r} (index {idx}) n’est pas prévue pour ce type de voie."
        )
    s = cat.structures[idx]

    station = p.get("station") or None
    if station is not None:
        try:
            obtenir_station(station)
        except (KeyError, ValueError):
            raise _ErreurSaisie(f"Station météo inconnue : {station!r}.") from None

    params = dict(
        type_voie=voie,
        trafic_initial_pl=_entier(p, "trafic_initial_pl", "Trafic initial", mini=0),
        croissance_pct=_entier(p, "croissance_pct", "Taux de croissance", defaut=2, mini=0, maxi=5),
        duree_ans=_entier(p, "duree_ans", "Durée de service", defaut=20, mini=1),
        plate_forme=pf,
        station=station,
        hiver=_choix(p, "hiver", "Hiver de référence", HIVERS_REFERENCE, defaut="HRNE"),
        taille_agglo=_choix(p, "taille_agglo", "Taille de l’agglomération", _AGGLOS, defaut="petite"),
        indice_gel_perso=_entier(p, "indice_gel_perso", "Indice de gel personnel", mini=0),
        pente_sol_pourcent=_reel(p, "pente_sol_pourcent", "Pente du sol", mini=0),
        epaisseur_non_gelive_cm=_reel(p, "epaisseur_non_gelive_cm", "Couche de forme non gélive", defaut=0.0, mini=0),
        couche_forme_traitee=_booleen(p, "couche_forme_traitee", False),
        norme_2019=_booleen(p, "norme_2019", False),
        fidele_vb6=_booleen(p, "fidele_vb6", True),
    )
    if params["trafic_initial_pl"] is None:
        raise _ErreurSaisie("Trafic initial obligatoire.")
    unite = _choix(p, "unite_dxf", "Unité du DXF", _UNITES, defaut="m")
    titre, variante, date = str(p.get("titre") or ""), str(p.get("variante") or ""), str(p.get("date") or "")

    r = dimensionner_etude(cat, mts, s, **params)
    html = note_calcul_html(r, s, titre=titre, variante=variante, date=date, **params)
    donnees = donnees_note(r, s, titre=titre, variante=variante, date=date, entrees={**params, "index": idx})
    dxf = None
    if r.epaisseur is not None:
        from .dxf import coupe_dxf

        dxf = coupe_dxf(r, s, plate_forme=pf, titre=titre, unite=unite)
    return {"ok": True, "donnees": donnees, "resume": _resume(donnees), "html": html, "dxf": dxf}


def _nb(n) -> str:
    return f"{int(n):,}".replace(",", " ")


def _resume(d: dict) -> str:
    r = d["resultats"]
    lignes = [
        f"{d['structure']['abrege'].strip()} – NE {_nb(r['ne_equivalent'])}"
        + (f" (NE théorique {_nb(r['ne_theorique'])})" if r["ne_theorique"] else " – épaisseurs non trouvées"),
    ]
    for nom in ("q1", "q2"):
        q = r[nom]
        if q is None:
            continue
        couches = " + ".join(f"{c['materiau']} {c['epaisseur_cm']}" for c in q["couches"] if c["epaisseur_cm"])
        lignes.append(f"{nom.upper()} : {couches} cm" if q["trouvee"] else f"{nom.upper()} : non trouvée")
    g = r["gel"]
    if g["indice_reference"] is not None:
        lignes.append(f"Gel : indice de référence {g['indice_reference']} °C·j")
    for nom in ("q1", "q2"):
        if g.get(nom):
            v = g[nom]
            adm = "hors gel" if v["hors_gel"] else f"{v['indice_admissible']} °C·j"
            lignes.append(f"  {nom.upper()} : admissible {adm} → {'vérifiée' if v['verifiee'] else 'NON vérifiée'}")
    if r["etude_labo_conseillee"]:
        lignes.append("Étude en laboratoire conseillée.")
    return "\n".join(lignes)


def listes(dossier_catalogue: Optional[Union[str, Path]] = None) -> dict:
    """Listes de choix de la page (structures avec leurs types de voie, stations), sans Pyodide."""
    cat, _ = _catalogues(str(_dossier(dossier_catalogue)))
    voies_par_index: Dict[int, list] = {}
    for v in TYPES_VOIE:
        for i, _ in structures_compatibles(cat, v):
            voies_par_index.setdefault(i, []).append(v)
    return {
        "voies": [{"code": v, "nom": NOMS_VOIE.get(v, v)} for v in TYPES_VOIE],
        "structures": [
            {
                "index": i,
                "abrege": s.abrege,
                "famille": TYPES_STRUCTURE.get(s.type_structure, ""),
                "ne_min": s.nb_essieux_min,
                "ne_max": s.nb_essieux_max,
                "voies": voies_par_index.get(i, []),
            }
            for i, s in enumerate(cat.structures)
        ],
        "stations": [
            {"nom": st.nom, "departement": st.departement, "altitude": st.altitude} for st in STATIONS_METEO
        ],
    }


def _fragments_aide(d: Path) -> Dict[str, str]:
    """Fragments HTML et JSON de l’aide pour le gabarit de la page."""
    from .aide import DOCUMENTATION, aide_certu, html_vers_texte, texte_vers_html

    certu = aide_certu(d)

    def bloc(sujet: str) -> str:
        a = certu[sujet]
        return (
            f'<details class="aide-rubrique" id="aide-{sujet}"><summary>Aide : {escape(a["titre"])}</summary>'
            f"{texte_vers_html(a['texte'])}</details>"
        )

    docs = "".join(
        f'<details class="doc" id="doc-{x["id"]}"><summary>{escape(x["titre"])}</summary>{x["html"]}</details>'
        for x in DOCUMENTATION
    )
    toute_aide = "".join(
        f"<h3>{escape(a['titre'])}</h3>{texte_vers_html(a['texte'])}" for a in certu.values()
    )
    documentation = (
        '<section id="documentation" aria-label="Documentation"><h2>Documentation</h2>' + docs
        + '<details class="doc" id="doc-aide-certu"><summary>Aide du logiciel d’origine (CERTU)</summary>'
        + toute_aide + "</details></section>"
    )
    donnees = {
        "certu": certu,
        "documentation": {x["id"]: {"titre": x["titre"], "texte": html_vers_texte(x["html"])} for x in DOCUMENTATION},
    }
    return {
        "AIDE_VOIE": bloc("voie") + bloc("structure") + bloc("plateforme") + bloc("surface"),
        "AIDE_TRAFIC": bloc("trafic") + bloc("cam"),
        "AIDE_GEL": bloc("gel"),
        "DOCUMENTATION": documentation,
        "AIDE_JSON": _json_script(donnees),
    }


_ASSETS = Path(__file__).resolve().parent / "assets"


def _b64_asset(nom: str) -> str:
    return base64.b64encode((_ASSETS / nom).read_bytes()).decode("ascii")


def generer_page(chemin: Union[str, Path], dossier_catalogue: Optional[Union[str, Path]] = None) -> None:
    """Écrit la page autonome (UTF-8)."""
    d = _dossier(dossier_catalogue)
    icone = (_ASSETS / "structurb_icone_v1.svg").read_text(encoding="utf-8")
    sources = {
        f"structurb/{f.name}": f.read_text(encoding="utf-8")
        for f in sorted(_DOSSIER_PAQUET.glob("*.py"))
    }
    fichiers = {
        "sources": sources,
        "catalogue": {
            nom: base64.b64encode((d / nom).read_bytes()).decode("ascii") for nom in ("Certu.str", "Certu.mts")
        },
    }
    valeurs = {
        "PYODIDE_URL": PYODIDE_URL,
        "FICHIERS": _json_script(fichiers),
        "LISTES": _json_script(listes(d)),
        "OUTIL": _json_script(OUTIL),
        **_fragments_aide(d),
        "SIGNATURE": signature_html(),
        "FAVICON": "data:image/svg+xml;base64," + base64.b64encode(icone.encode("utf-8")).decode("ascii"),
        "ICONE": icone,
        "LOGO_CERTU": _b64_asset("logo_certu.png"),
        "LOGO_CEREMA": _b64_asset("logo_cerema.png"),
    }
    # Une seule passe : le texte inséré (dont les sources de ce module) n’est pas relu
    html = re.sub(r"__(PYODIDE_URL|FICHIERS|LISTES|OUTIL|AIDE_VOIE|AIDE_TRAFIC|AIDE_GEL|DOCUMENTATION|AIDE_JSON|SIGNATURE|FAVICON|ICONE|LOGO_CERTU|LOGO_CEREMA)__", lambda m: valeurs[m.group(1)], _GABARIT)
    Path(chemin).write_text(html, encoding="utf-8")


_GABARIT = r"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Struct-Urb Python</title>
<link rel="icon" href="__FAVICON__">
<meta name="description" content="Dimensionnement des structures de chaussées urbaines (catalogue CERTU), calcul dans le navigateur.">
<style>
:root {
  color-scheme: light dark;
  --fond: #f1f5f9;
  --carte: #ffffff;
  --texte: #0f172a;
  --doux: #475569;
  --bord: #cbd5e1;
  --bord-doux: #e2e8f0;
  /* Palette du fork (identique à dimensionnement-burmister/web) : orange, bleu, vert, lie-de-vin */
  --orange: #DD590A;
  --bleu: #5E99C5;
  --vert: #179D87;
  --lie-de-vin: #7F0541;
  --accent: var(--orange);
  --accent-fonce: #b8480a;
  --accent-texte: #a8430a;
  --accent-doux: rgba(221, 89, 10, .10);
  --ok: var(--vert);
  --ok-fond: #e6f5f2;
  --ko: #b91c1c;
  --ko-fond: #fee2e2;
  --zone: #f8fafc;
  --aide-fond: #FFFFE1; /* info-bulle système de la V1 (&H80000018) */
  --ombre: 0 1px 3px rgba(15, 23, 42, .06), 0 8px 24px rgba(15, 23, 42, .05);
}
@media (prefers-color-scheme: dark) {
  :root {
    --fond: #0b1120;
    --carte: #131c31;
    --texte: #e2e8f0;
    --doux: #94a3b8;
    --bord: #334155;
    --bord-doux: #1e293b;
    --accent: #e8702a;
    --accent-fonce: #DD590A;
    --accent-texte: #f5a26b;
    --accent-doux: rgba(232, 112, 42, .16);
    --bleu: #8bb8dc;
    --ok: #3cc4ac;
    --ok-fond: rgba(23, 157, 135, .16);
    --ko: #f87171;
    --ko-fond: rgba(239, 68, 68, .14);
    --zone: #0f172a;
    --aide-fond: #2a2814;
    --ombre: 0 2px 6px rgba(0, 0, 0, .35), 0 10px 28px rgba(0, 0, 0, .28);
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--fond); color: var(--texte); font: 15px/1.5 "Segoe UI", system-ui, -apple-system, Arial, sans-serif; }
main { max-width: 1140px; margin: 0 auto; padding: 24px 18px 56px; }
.hero {
  background: linear-gradient(135deg, var(--lie-de-vin) 0%, var(--orange) 72%);
  color: #fff;
  border-radius: 14px;
  padding: 22px 24px 20px;
  margin-bottom: 18px;
  box-shadow: 0 10px 28px rgba(127, 5, 65, .22);
}
.hero-haut { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px; }
.badge {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .02em;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, .16);
  border: 1px solid rgba(255, 255, 255, .28);
  color: #f8fafc;
}
h1 { font-size: 25px; margin: 0; letter-spacing: -.01em; display: flex; align-items: center; gap: 12px; }
.logo-app { display: inline-flex; background: #fff; border-radius: 8px; padding: 4px; box-shadow: 0 1px 4px rgba(0, 0, 0, .25); }
.logo-app svg { width: 32px; height: 32px; display: block; }
.hero p.sous-titre { margin: 8px 0 14px; color: rgba(255, 255, 255, .88); max-width: 78ch; font-size: 14px; }
.doux { color: var(--doux); }
#etat {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(60, 0, 30, .30);
  border: 1px solid rgba(255, 255, 255, .22);
  color: #f8fafc;
  font-size: 13px;
  font-weight: 500;
  margin: 0;
}
#etat::before {
  content: "";
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #fbbf24;
  box-shadow: 0 0 0 3px rgba(251, 191, 36, .28);
  flex: none;
}
#etat[data-etat="pret"]::before { background: #4ade80; box-shadow: 0 0 0 3px rgba(74, 222, 128, .28); }
#etat[data-etat="erreur"]::before { background: #f87171; box-shadow: 0 0 0 3px rgba(248, 113, 113, .28); }
form { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; }
fieldset {
  background: var(--carte);
  border: 1px solid var(--bord-doux);
  border-radius: 12px;
  padding: 14px 18px 18px;
  margin: 0;
  box-shadow: var(--ombre);
}
legend {
  font-weight: 700;
  font-size: 14px;
  color: var(--accent-texte);
  background: var(--carte);
  border: 1px solid var(--bord-doux);
  border-radius: 999px;
  padding: 2px 12px;
}
.champ { display: grid; grid-template-columns: 1fr 1.2fr; gap: 10px; align-items: center; margin: 8px 0; }
.champ.case { grid-template-columns: auto 1fr; }
label { font-size: 13.5px; font-weight: 500; color: var(--texte); }
input, select {
  font: inherit;
  font-size: 14px;
  padding: 7px 10px;
  border: 1px solid var(--bord);
  border-radius: 8px;
  background: var(--zone);
  color: var(--texte);
  width: 100%;
  transition: border-color .15s ease, box-shadow .15s ease, background-color .15s ease;
}
input:focus, select:focus {
  outline: none;
  border-color: var(--accent-texte);
  background: var(--carte);
  box-shadow: 0 0 0 3px var(--accent-doux);
}
/* Valeur hors limites : texte rouge QBColor(12), comme la V1 */
input:out-of-range, input:invalid { color: #FF0000; border-color: #FF0000; }
input[type=checkbox] { width: 16px; height: 16px; accent-color: var(--accent-texte); cursor: pointer; }
.actions {
  grid-column: 1 / -1;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
  padding: 14px 18px;
  background: var(--carte);
  border: 1px solid var(--bord-doux);
  border-radius: 12px;
  box-shadow: var(--ombre);
}
button, .bouton {
  font: inherit;
  font-weight: 600;
  padding: 9px 18px;
  border-radius: 8px;
  border: 1px solid var(--accent);
  background: linear-gradient(135deg, var(--accent), var(--accent-fonce));
  color: #fff;
  cursor: pointer;
  text-decoration: none;
  transition: transform .12s ease, box-shadow .15s ease, opacity .15s ease;
}
button:hover:not(:disabled), .bouton:hover { transform: translateY(-1px); box-shadow: 0 4px 12px var(--accent-doux); }
.bouton.second { background: var(--carte); color: var(--accent-texte); }
.bouton.second:hover { background: var(--accent-doux); }
button:disabled { opacity: .55; cursor: wait; transform: none; }
#resultat { margin-top: 22px; }
#resultat-resume {
  white-space: pre-wrap;
  background: var(--carte);
  border: 1px solid var(--bord-doux);
  border-left: 4px solid var(--ok);
  border-radius: 10px;
  padding: 14px 16px;
  box-shadow: var(--ombre);
  font-family: ui-monospace, "Cascadia Mono", Consolas, monospace;
  font-size: 13.5px;
}
#resultat-erreur {
  color: var(--ko);
  background: var(--ko-fond);
  border-left: 4px solid var(--ko);
  border-radius: 8px;
  padding: 12px 14px;
  font-weight: 600;
}
iframe { width: 100%; height: 920px; border: 1px solid var(--bord-doux); border-radius: 12px; background: #fff; margin-top: 14px; box-shadow: var(--ombre); }
details pre { white-space: pre-wrap; font-size: 12px; max-height: 360px; overflow: auto; background: var(--zone); padding: 10px 12px; border-radius: 8px; border: 1px solid var(--bord-doux); }
details.aide {
  margin: 0 0 18px;
  border: 1px solid var(--bord-doux);
  border-left: 4px solid var(--bleu);
  border-radius: 12px;
  background: var(--aide-fond);
  padding: 12px 16px;
  box-shadow: var(--ombre);
}
details.aide summary { cursor: pointer; font-weight: 700; color: var(--accent-texte); }
.aide-grille { display: grid; grid-template-columns: repeat(auto-fit, minmax(235px, 1fr)); gap: 12px; margin-top: 12px; font-size: 13px; }
.aide-grille > div { background: var(--zone); border: 1px solid var(--bord-doux); border-radius: 8px; padding: 10px 12px; }
.aide-grille h3 { font-size: 13.5px; margin: 0 0 6px; color: var(--accent-texte); border-bottom: 1px solid var(--bord-doux); padding-bottom: 4px; }
.aide-grille ul { margin: 0; padding-left: 18px; }
.aide-grille li { margin-bottom: 4px; }
.aide-rubrique { grid-column: 1 / -1; margin-top: 8px; font-size: 12.5px; background: var(--zone); border: 1px solid var(--bord-doux); border-radius: 8px; padding: 6px 10px; }
.aide-rubrique summary { cursor: pointer; font-weight: 600; color: var(--accent-texte); }
.aide-rubrique p, .doc p { margin: 6px 0; }
#documentation { margin-top: 30px; }
#documentation h2 { font-size: 18px; border-bottom: 2px solid var(--bord); padding-bottom: 6px; margin-bottom: 12px; }
details.doc {
  background: var(--carte);
  border: 1px solid var(--bord-doux);
  border-radius: 10px;
  padding: 10px 16px;
  margin: 10px 0;
  box-shadow: var(--ombre);
}
details.doc summary { cursor: pointer; font-weight: 600; color: var(--texte); }
details.doc code, details.aide code { background: var(--accent-doux); color: var(--accent-texte); padding: 1px 5px; border-radius: 4px; font-size: .92em; }
.aide-champ { grid-column: 1 / -1; font-size: 12px; color: var(--doux); margin: 6px 0 0; }
#origine { margin-top: 30px; background: var(--carte); border: 1px solid var(--bord-doux); border-radius: 12px; padding: 14px 18px; box-shadow: var(--ombre); font-size: 13px; }
#origine h2 { font-size: 16px; margin: 0 0 10px; }
#origine .logos { display: flex; flex-wrap: wrap; align-items: center; gap: 22px; margin-bottom: 10px; }
#origine .logos img { background: #fff; border-radius: 6px; padding: 4px; }
#origine ul { margin: 4px 0 8px; padding-left: 18px; }
footer.pied { margin-top: 34px; padding-top: 12px; border-top: 2px solid var(--orange); font-size: 12.5px; color: var(--doux); }
footer.pied p { margin: 0; }
@media (max-width: 600px) {
  .champ { grid-template-columns: 1fr; gap: 4px; }
  .hero { padding: 18px 16px; }
}
</style>
</head>
<body>
<main>
<header class="hero">
  <div class="hero-haut">
    <h1><span class="logo-app" aria-hidden="true">__ICONE__</span>Struct-Urb Python</h1>
    <span class="badge">Catalogue CERTU · Calcul 100 % local</span>
  </div>
  <p class="sous-titre">Dimensionnement des structures de chaussées urbaines par le catalogue CERTU. Le calcul s’exécute dans ce navigateur ; aucune donnée n’est envoyée.</p>
  <p id="etat" role="status" data-etat="chargement">Chargement du moteur de calcul (Pyodide, environ 10 Mo la première fois)…</p>
</header>

<details id="aide-en-ligne" class="aide">
  <summary>Aide en ligne &amp; documentation rapide</summary>
  <div class="aide-grille">
    <div>
      <h3>1. Voie &amp; Plate-forme</h3>
      <ul>
        <li><strong>Type de voie</strong> : filtre les structures autorisées par le catalogue CERTU et détermine le CAM préconisé.</li>
        <li><strong>Plate-forme</strong> : portance à long terme — <code>PF1</code> (20–50 MPa), <code>PF2</code> (50–80 MPa), <code>PF2+</code> (80–120 MPa), <code>PF3</code> (&gt; 120 MPa).</li>
        <li><strong>Q1 / Q2</strong> : qualité de réalisation courante (<code>Q1</code>) ou chantier difficile (<code>Q2</code>).</li>
      </ul>
    </div>
    <div>
      <h3>2. Trafic &amp; Durée</h3>
      <ul>
        <li><strong>Trafic initial</strong> : nombre moyen de poids lourds par jour, par sens et par voie la plus chargée (PL/j).</li>
        <li><strong>Croissance</strong> : taux annuel linéaire entre <code>0 %</code> et <code>5 %</code> (calculé sur 5 à 50 ans en usage courant).</li>
        <li><strong>Étude labo</strong> : conseillée pour un trafic initial de <code>750</code> à <code>1 000 PL/j</code> sur les voies à trafic lourd, les voies bus et les giratoires à trafic lourd (au-delà de 1 000 PL/j : hors domaine).</li>
      </ul>
    </div>
    <div>
      <h3>3. Vérification au gel</h3>
      <ul>
        <li><strong>Station ou indice perso</strong> : choisissez une des 84 stations (facteur agglo : <code>1,0</code> / <code>0,9</code> / <code>0,8</code>) ou saisissez un indice local Météo-France (notamment en altitude).</li>
        <li><strong>Pente de gonflement</strong> : sol non gélif si <code>&lt;= 0,05</code> (chaussée hors gel).</li>
        <li><strong>Norme 2019</strong> : applique <code>Kcr = 0,7</code> (NF P 98-086 § 6.2.4, méthode simplifiée) et les coefficients GCV du tableau H.2 au lieu de <code>0,6</code> (VB6).</li>
      </ul>
    </div>
    <div>
      <h3>4. Exports &amp; Pilotage IA</h3>
      <ul>
        <li><strong>Note HTML</strong> : page autonome imprimable en A4 (<code>Ctrl+P</code>) avec coupes SVG et données JSON.</li>
        <li><strong>Coupe DXF</strong> : dessin R12 prêt pour AutoCAD / COVADIS (calques séparés par couche, unité m/cm/mm).</li>
        <li><strong>Interface IA</strong> : API JavaScript <code>window.structurb.calculer(params)</code> et outil WebMCP <code>dimensionner_chaussee</code>.</li>
      </ul>
    </div>
  </div>
</details>

<form id="formulaire-etude" novalidate>
  <fieldset>
    <legend>Voie et structure</legend>
    <div class="champ"><label for="champ-titre">Titre de l’étude</label><input id="champ-titre" name="titre" type="text" placeholder="Rue des Lilas"></div>
    <div class="champ"><label for="champ-type_voie">Type de voie</label><select id="champ-type_voie" name="type_voie" required></select></div>
    <div class="champ"><label for="champ-index">Structure</label><select id="champ-index" name="index" required></select></div>
    <div class="champ"><label for="champ-plate_forme">Classe de plate-forme</label>
      <select id="champ-plate_forme" name="plate_forme" required><option>PF1</option><option selected>PF2</option><option>PF2+</option><option>PF3</option></select></div>
    __AIDE_VOIE__
  </fieldset>
  <fieldset>
    <legend>Trafic</legend>
    <div class="champ"><label for="champ-trafic_initial_pl">Trafic initial (PL/j)</label><input id="champ-trafic_initial_pl" name="trafic_initial_pl" type="number" min="0" step="1" required value="12"></div>
    <div class="champ"><label for="champ-croissance_pct">Taux de croissance (%)</label><input id="champ-croissance_pct" name="croissance_pct" type="number" min="0" max="5" step="1" value="2"></div>
    <div class="champ"><label for="champ-duree_ans">Durée de service (ans)</label><input id="champ-duree_ans" name="duree_ans" type="number" min="1" step="1" value="20"></div>
    __AIDE_TRAFIC__
  </fieldset>
  <fieldset>
    <legend>Vérification au gel</legend>
    <div class="champ"><label for="champ-station">Station météo</label><select id="champ-station" name="station"></select></div>
    <div class="champ"><label for="champ-hiver">Hiver de référence</label>
      <select id="champ-hiver" name="hiver"><option value="HE">Hiver exceptionnel</option><option value="HRNE" selected>Hiver rigoureux non exceptionnel</option><option value="HC">Hiver courant</option></select></div>
    <div class="champ"><label for="champ-taille_agglo">Taille de l’agglomération</label>
      <select id="champ-taille_agglo" name="taille_agglo"><option value="petite">moins de 100 000 hab.</option><option value="moyenne">100 000 à 1 000 000 hab.</option><option value="grande">plus de 1 000 000 hab.</option></select></div>
    <div class="champ"><label for="champ-indice_gel_perso">Indice de gel personnel (°C·j)</label><input id="champ-indice_gel_perso" name="indice_gel_perso" type="number" min="0" step="1" placeholder="facultatif"></div>
    <div class="champ"><label for="champ-pente_sol_pourcent">Pente de l’essai de gonflement</label><input id="champ-pente_sol_pourcent" name="pente_sol_pourcent" type="number" min="0" step="0.01" placeholder="ex. 0,5"></div>
    <div class="champ"><label for="champ-epaisseur_non_gelive_cm">Couche de forme non gélive (cm)</label><input id="champ-epaisseur_non_gelive_cm" name="epaisseur_non_gelive_cm" type="number" min="0" step="1" value="0"></div>
    <div class="champ case"><input id="champ-couche_forme_traitee" name="couche_forme_traitee" type="checkbox"><label for="champ-couche_forme_traitee">Couche de forme traitée</label></div>
    <p class="aide-champ">Laissez la station vide pour ne pas vérifier au gel. En secteur d’altitude, préférez l’indice personnel.</p>
    __AIDE_GEL__
  </fieldset>
  <fieldset>
    <legend>Options</legend>
    <div class="champ case"><input id="champ-norme_2019" name="norme_2019" type="checkbox"><label for="champ-norme_2019">Gel : méthode simplifiée NF P98-086 (Kcr 0,7)</label></div>
    <div class="champ case"><input id="champ-fidele_vb6" name="fidele_vb6" type="checkbox" checked><label for="champ-fidele_vb6">Gel : épaisseurs comme le VB6 (lit de pose compris)</label></div>
    <div class="champ"><label for="champ-unite_dxf">Unité du DXF</label><select id="champ-unite_dxf" name="unite_dxf"><option value="m">mètre</option><option value="cm">centimètre</option><option value="mm">millimètre</option></select></div>
    <div class="champ"><label for="champ-variante">Variante</label><input id="champ-variante" name="variante" type="text"></div>
    <p class="aide-champ">Par défaut, le calcul reproduit exactement Struct-Urb VB6 (Kcr = 0,6 et lit de pose inclus).</p>
  </fieldset>
  <div class="actions">
    <button id="bouton-calculer" type="submit" disabled>Calculer</button>
    <a id="lien-note" class="bouton second" hidden download="note-structurb.html">Télécharger la note HTML</a>
    <a id="lien-dxf" class="bouton second" hidden download="coupe-structurb.dxf">Télécharger la coupe DXF</a>
  </div>
</form>

<section id="resultat" aria-live="polite" aria-label="Résultat du calcul">
  <p id="resultat-erreur" role="alert" hidden></p>
  <pre id="resultat-resume" hidden></pre>
  <details id="resultat-details" hidden><summary>Données du calcul (JSON)</summary><pre id="resultat-json"></pre></details>
  <iframe id="resultat-note" title="Note de calcul" sandbox="" hidden></iframe>
</section>
__DOCUMENTATION__
<section id="origine" aria-labelledby="origine-titre">
  <h2 id="origine-titre">Origine</h2>
  <div class="logos">
    <img src="data:image/png;base64,__LOGO_CERTU__" width="72" height="72" alt="Logo du CERTU">
    <img src="data:image/png;base64,__LOGO_CEREMA__" width="170" height="60" alt="Logo du Cerema">
  </div>
  <p><strong>D’après Struct-Urb, logiciel du CERTU / Cerema (GPL v3) — portage non officiel.</strong>
  Ce portage n’est ni produit ni validé par le Cerema ; les logos ci-dessus désignent le logiciel d’origine.</p>
  <p>Équipes du logiciel d’origine (fenêtre « À propos » de Struct-Urb) :</p>
  <ul>
    <li>Cahier des charges : CEREMA / TV / VOI / CGR ; CERTU / Département Systèmes / Groupe Génie urbain ; CERTU / Département Systèmes / Groupe Informatique technique et scientifique.</li>
    <li>Développement : CERTU / Département Systèmes / Groupe Informatique technique et scientifique.</li>
    <li>Diffusion et assistance : CEREMA / TV / EREN / Digit@l ; CERTU / Département Systèmes / Groupe Informatique technique et scientifique.</li>
  </ul>
</section>
<footer class="pied">__SIGNATURE__</footer>
</main>

<script type="application/json" id="structurb-fichiers">__FICHIERS__</script>
<script type="application/json" id="structurb-listes">__LISTES__</script>
<script type="application/json" id="structurb-outil">__OUTIL__</script>
<script type="application/json" id="structurb-aide">__AIDE_JSON__</script>
<script>
(function () {
  "use strict";
  const PYODIDE_URL = "__PYODIDE_URL__";
  const lire = (id) => JSON.parse(document.getElementById(id).textContent);
  const LISTES = lire("structurb-listes");
  const AIDE = lire("structurb-aide");
  const OUTIL = lire("structurb-outil");
  const $ = (id) => document.getElementById(id);
  const nb = (n) => Number(n).toLocaleString("fr-FR");

  // --- Listes de choix -------------------------------------------------------
  const selVoie = $("champ-type_voie"), selStruct = $("champ-index"), selStation = $("champ-station");
  for (const v of LISTES.voies) selVoie.add(new Option(v.nom, v.code));
  selStation.add(new Option("— aucune (pas de vérification au gel) —", ""));
  for (const s of LISTES.stations) selStation.add(new Option(`${s.nom} (${s.departement}, ${s.altitude} m)`, s.nom));
  function structures(voie) {
    return LISTES.structures.filter((s) => s.voies.includes(voie));
  }
  function remplirStructures() {
    const avant = selStruct.value;
    selStruct.length = 0;
    for (const s of structures(selVoie.value)) {
      selStruct.add(new Option(`${s.abrege.trim()} — ${s.famille}, NE ${nb(s.ne_min)} à ${nb(s.ne_max)}`, String(s.index)));
    }
    if ([...selStruct.options].some((o) => o.value === avant)) selStruct.value = avant;
  }
  selVoie.addEventListener("change", remplirStructures);
  remplirStructures();

  // --- Moteur Python (Pyodide) -------------------------------------------------
  function chargerScript(url) {
    return new Promise((ok, ko) => {
      const s = document.createElement("script");
      s.src = url; s.onload = ok; s.onerror = () => ko(new Error("Pyodide inaccessible : connexion Internet requise."));
      document.head.appendChild(s);
    });
  }
  const pret = (async () => {
    await chargerScript(PYODIDE_URL + "pyodide.js");
    const py = await loadPyodide({ indexURL: PYODIDE_URL });
    const f = lire("structurb-fichiers");
    py.FS.mkdirTree("/home/pyodide/structurb");
    for (const [chemin, texte] of Object.entries(f.sources)) py.FS.writeFile("/home/pyodide/" + chemin, texte);
    for (const [nom, b64] of Object.entries(f.catalogue)) {
      py.FS.writeFile("/home/pyodide/" + nom, Uint8Array.from(atob(b64), (c) => c.charCodeAt(0)));
    }
    py.runPython("import os, sys, importlib; os.chdir('/home/pyodide'); sys.path.insert(0, '/home/pyodide'); importlib.invalidate_caches()");
    return py.pyimport("structurb.page");
  })();
  pret.then(() => {
    $("etat").dataset.etat = "pret";
    $("etat").textContent = "Moteur de calcul prêt.";
    $("bouton-calculer").disabled = false;
  }, (e) => {
    $("etat").dataset.etat = "erreur";
    $("etat").textContent = "Erreur : " + e.message;
  });

  async function calculer(params) {
    const module = await pret;
    const p = Object.assign({ date: new Date().toLocaleDateString("fr-FR") }, params || {});
    return JSON.parse(module.calculer_depuis_json(JSON.stringify(p)));
  }

  // --- Formulaire --------------------------------------------------------------
  function lireFormulaire() {
    const form = $("formulaire-etude"), p = {};
    for (const el of form.elements) {
      if (!el.name) continue;
      if (el.type === "checkbox") p[el.name] = el.checked;
      else if (el.value !== "") p[el.name] = el.type === "number" || el.name === "index" ? Number(el.value) : el.value;
    }
    return p;
  }
  const urls = [];
  function lien(id, contenu, type) {
    const a = $(id);
    const url = URL.createObjectURL(new Blob([contenu], { type }));
    urls.push(url); a.href = url; a.hidden = false;
  }
  function afficher(r) {
    while (urls.length) URL.revokeObjectURL(urls.pop());
    $("resultat-erreur").hidden = r.ok;
    $("resultat-resume").hidden = !r.ok;
    $("resultat-details").hidden = !r.ok;
    $("resultat-note").hidden = !r.ok;
    $("lien-note").hidden = true; $("lien-dxf").hidden = true;
    if (!r.ok) { $("resultat-erreur").textContent = r.erreur; return; }
    $("resultat-resume").textContent = r.resume;
    $("resultat-json").textContent = JSON.stringify(r.donnees, null, 1);
    $("resultat-note").srcdoc = r.html;
    lien("lien-note", r.html, "text/html");
    if (r.dxf) lien("lien-dxf", r.dxf, "application/dxf");
  }
  $("formulaire-etude").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const b = $("bouton-calculer"); b.disabled = true;
    try { afficher(await calculer(lireFormulaire())); }
    catch (e) { afficher({ ok: false, erreur: String(e.message || e) }); }
    finally { b.disabled = false; }
  });

  // --- Interface pour les scripts et les assistants IA du navigateur ----------
  window.structurb = {
    pret: pret.then(() => true),
    calculer,
    structures: (voie) => structures(voie).map((s) => ({ ...s })),
    stations: () => LISTES.stations.map((s) => ({ ...s })),
    outil: OUTIL,
    // Aide : sans argument, liste des rubriques ; sinon texte de la rubrique (aide CERTU ou documentation)
    aide: (sujet) => {
      if (!sujet) return { certu: Object.keys(AIDE.certu), documentation: Object.keys(AIDE.documentation) };
      const r = AIDE.certu[sujet] || AIDE.documentation[sujet];
      return r ? { titre: r.titre, texte: r.texte } : null;
    },
  };
  // WebMCP (expérimental) : déclarer l’outil si le navigateur le permet
  const mc = navigator.modelContext;
  if (mc) {
    const outil = {
      name: OUTIL.name, description: OUTIL.description, inputSchema: OUTIL.inputSchema,
      async execute(args) {
        const r = await calculer(args);
        afficher(r);
        const texte = r.ok ? r.resume + "\n\n" + JSON.stringify(r.donnees) : "Erreur : " + r.erreur;
        return { content: [{ type: "text", text: texte }] };
      },
    };
    try {
      if (typeof mc.registerTool === "function") mc.registerTool(outil);
      else if (typeof mc.provideContext === "function") mc.provideContext({ tools: [outil] });
    } catch (e) { console.warn("WebMCP indisponible :", e); }
  }
})();
</script>
</body>
</html>
"""
