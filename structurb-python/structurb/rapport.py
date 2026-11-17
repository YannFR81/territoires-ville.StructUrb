"""Note de calcul HTML imprimable (page autonome, sans ressource externe).

Ajout du portage Python : le VB6 imprimait la note directement (``frmImprimer.frm``).
La page reprend les mêmes rubriques (voie, trafic, structure, épaisseurs Q1/Q2, gel) et
dessine la coupe de chaussée de chaque qualité en SVG, avec les épaisseurs du catalogue
(le lit de pose des pavés et dalles est dessiné, les 3 cm « d’affichage » ne le sont pas).
"""

from __future__ import annotations

import json
from html import escape
from typing import List, Optional, Tuple, Union

from ._images import PICTOGRAMMES
from .catalogue import LigneEpaisseur, StructureChaussee
from .epaisseur import EP_LIT_POSE, ResultatQualite
from .etude import ResultatEtude
from .gel import HORS_GEL, StationMeteo
from .signature import signature_html

NOMS_VOIE = {
    "desserte": "Voie de desserte",
    "distribution": "Voie de distribution",
    "trafic_lourd": "Voie principale à trafic lourd",
    "bus": "Voie réservée aux bus",
    "parking": "Parking",
    "giratoire_distribution": "Giratoire sur voie de distribution",
    "giratoire_trafic_lourd": "Giratoire sur voie à trafic lourd",
}
NOMS_HIVER = {
    "HE": "hiver exceptionnel",
    "HRNE": "hiver rigoureux non exceptionnel",
    "HC": "hiver courant",
}

_ECHELLE_PX_CM = 5.0
_HAUTEUR_MIN_PX = 6.0
# Couleurs des couches de la coupe : valeurs par défaut de Struct-Urb V1
# (ModuleMain.bas, mesOptionsGen : maCoulSurf QBColor(11), maCoulBase1 QBColor(2), maCoulBase2 QBColor(10),
# maCoulFond1 QBColor(12), maCoulFond2 QBColor(13)). Lit de pose et plate-forme : sans équivalent en V1.
COULEURS_COUCHES = {
    "surface": "#00FFFF",
    "lit": "#e3c98f",
    "base1": "#008000",
    "base2": "#00FF00",
    "fondation1": "#FF0000",
    "fondation2": "#FF00FF",
    "plateforme": "#b08b5b",
}
_COULEURS = COULEURS_COUCHES

_CSS = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", Arial, sans-serif; color: #1d2330; background: #fff;
       margin: 0 auto; max-width: 820px; padding: 24px 16px; line-height: 1.45; font-size: 14px; }
h1 { font-size: 22px; margin: 0 0 4px; color: #7F0541; }
h2 { font-size: 16px; margin: 22px 0 8px; padding-bottom: 4px; border-bottom: 2px solid #DD590A; }
.sous-titre { color: #555d6e; margin: 0 0 12px; }
table { border-collapse: collapse; width: 100%; }
th, td { text-align: left; padding: 4px 8px; border-bottom: 1px solid #dde1e8; vertical-align: top; }
th { width: 45%; font-weight: 600; color: #39404f; }
.nombre { font-variant-numeric: tabular-nums; }
.coupes { display: flex; gap: 24px; flex-wrap: wrap; }
.coupe { flex: 1 1 340px; border: 1px solid #dde1e8; border-radius: 6px; padding: 10px 12px; break-inside: avoid; }
.coupe h3 { font-size: 14px; margin: 0 0 6px; }
.ok { color: #0e6b5b; font-weight: 600; }
.ko { color: #b42318; font-weight: 600; }
.note { color: #555d6e; font-size: 12px; }
.signature { margin-top: 18px; padding-top: 8px; border-top: 1px solid #dde1e8; color: #555d6e; font-size: 12px; }
.pictos { display: flex; gap: 8px; margin: 0 0 6px; }
.alerte { background: #fff4e5; border-left: 4px solid #DD590A; padding: 6px 10px; margin: 8px 0; }
svg text { font-family: inherit; font-size: 11px; }
@page { size: A4; margin: 15mm; }
@media print {
  body { max-width: none; padding: 0; font-size: 11pt; }
  h2 { break-after: avoid; }
  .coupe { border-color: #999; }
}
"""


def _nombre(n: Union[int, float]) -> str:
    """Nombre au format français, espace insécable fine entre milliers."""
    if isinstance(n, float) and not n.is_integer():
        return f"{n:g}".replace(".", ",")
    return f"{int(n):,}".replace(",", " ")


def _couches(ligne: LigneEpaisseur, structure: StructureChaussee) -> List[Tuple[str, str, int]]:
    """Couches de la coupe (rôle, libellé, épaisseur en cm), de la surface vers la plate-forme."""
    return [(role, lib, ep) for role, _, lib, ep in _couches_detail(ligne, structure)]


def cle_couleur(role: str, rang: int) -> str:
    """Clé de ``COULEURS_COUCHES`` : base et fondation ont une couleur par couche (1 ou 2), comme en V1."""
    return f"{role}{rang}" if role in ("base", "fondation") else role


def _couches_detail(ligne: LigneEpaisseur, structure: StructureChaussee) -> List[Tuple[str, int, str, int]]:
    """Couches de la coupe (rôle, rang 1 ou 2, libellé, épaisseur en cm), de la surface vers la plate-forme."""
    couches: List[Tuple[str, int, str, int]] = []
    surf = structure.couche_surface
    if surf != "Aucune":
        couches.append(("surface", 1, surf.strip(), ligne.epaisseur_surface))
        if surf in ("Dalles", "Pavés"):
            couches.append(("lit", 1, "lit de pose", EP_LIT_POSE))
    for role, mat, eps in (
        ("base", structure.couche_base, (ligne.epaisseur_base_1, ligne.epaisseur_base_2)),
        ("fondation", structure.couche_fondation, (ligne.epaisseur_fondation_1, ligne.epaisseur_fondation_2)),
    ):
        eps_non_nulles = [(rang, e) for rang, e in enumerate(eps, start=1) if e > 0]
        for k, (rang, e) in enumerate(eps_non_nulles, start=1):
            suffixe = f" ({k}/{len(eps_non_nulles)})" if len(eps_non_nulles) > 1 else ""
            couches.append((role, rang, f"{mat.strip()}{suffixe}", e))
    return couches


def _svg_coupe(couches: List[Tuple[str, str, int]]) -> str:
    largeur, x0, l_couche = 320, 10, 120
    y = 10.0
    elems = []
    for role, libelle, ep in couches:
        h = max(ep * _ECHELLE_PX_CM, _HAUTEUR_MIN_PX)
        elems.append(
            f'<rect x="{x0}" y="{y:.1f}" width="{l_couche}" height="{h:.1f}" '
            f'fill="{_COULEURS[role]}" stroke="#1d2330" stroke-width="0.6"/>'
        )
        texte = f"{escape(libelle)} : {ep} cm" if ep > 0 else f"{escape(libelle)} (sans épaisseur)"
        elems.append(f'<text x="{x0 + l_couche + 10}" y="{y + h / 2 + 4:.1f}">{texte}</text>')
        y += h
    total = sum(ep for _, _, ep in couches)
    elems.append(
        f'<rect x="{x0}" y="{y:.1f}" width="{l_couche}" height="14" fill="{_COULEURS["plateforme"]}" '
        f'opacity="0.55" stroke="#1d2330" stroke-width="0.6"/>'
    )
    elems.append(f'<text x="{x0 + l_couche + 10}" y="{y + 11:.1f}">plate-forme</text>')
    hauteur = y + 24
    titre = f"Coupe de chaussée, épaisseur totale {total} cm"
    return (
        f'<svg role="img" aria-label="{escape(titre)}" viewBox="0 0 {largeur} {hauteur:.0f}" '
        f'width="100%" style="max-width:{largeur}px" xmlns="http://www.w3.org/2000/svg">'
        f"<title>{escape(titre)}</title>{''.join(elems)}</svg>"
    )


def _bloc_qualite(nom: str, q: ResultatQualite, structure: StructureChaussee) -> str:
    if not q.trouvee:
        return (
            f'<div class="coupe"><h3>{nom}</h3>'
            f'<p class="ko">Épaisseur non trouvée (maximum pratique atteint).</p></div>'
        )
    detail = _couches_detail(q.ligne, structure)
    couches = [(cle_couleur(role, rang), lib, ep) for role, rang, lib, ep in detail]
    lignes = "".join(
        f"<tr><td>{escape(lib)}</td><td class=\"nombre\">{ep} cm</td></tr>" for _, lib, ep in couches
    )
    infos = []
    if q.min_technique.strip().upper() == "OUI":
        infos.append("épaisseur au minimum technologique")
    infos.append(f"Qm = {_nombre(round(q.qm, 2))}")
    pictos = _pictogrammes(q)
    return (
        f'<div class="coupe"><h3>{nom}</h3>{pictos}{_svg_coupe(couches)}'
        f"<table>{lignes}</table><p class=\"note\">{escape(' · '.join(infos))}</p></div>"
    )


def _pictogrammes(q: ResultatQualite) -> str:
    """Pictogrammes de Struct-Urb V1 (ImageMinTec.bmp, ImageMaxPra.bmp), en SVG pour rester sans ressource externe."""
    elems = []
    for actif, fichier, (l, h), texte in (
        (q.min_technique.strip().upper() == "OUI", "min_techno.png", (75, 31), "Minimum technologique atteint"),
        (q.max_pratique.strip().upper() == "OUI", "max_pratique.png", (56, 49), "Maximum pratique atteint"),
    ):
        if actif:
            elems.append(
                f'<svg class="picto" role="img" aria-label="{texte}" width="{l}" height="{h}" viewBox="0 0 {l} {h}" '
                f'xmlns="http://www.w3.org/2000/svg"><title>{texte}</title>'
                f'<image width="{l}" height="{h}" href="data:image/png;base64,{PICTOGRAMMES[fichier]}"/></svg>'
            )
    return f'<div class="pictos">{"".join(elems)}</div>' if elems else ""


def _json_script(d: object) -> str:
    """JSON à placer dans un bloc <script> : « < » remplacé par la séquence \u003c."""
    return json.dumps(d, ensure_ascii=False, indent=1).replace("<", r"\u003c")


def _est_giratoire(type_voie: str) -> bool:
    """Indique si la voie est un giratoire (une seule qualité, pas de Q2 ; ``frmDocument.frm``, l. 4127)."""
    return type_voie in ("giratoire_distribution", "giratoire_trafic_lourd")


def donnees_note(
    r: ResultatEtude, structure: StructureChaussee, *, titre: str, variante: str, date: str, entrees: dict
) -> dict:
    """Bloc JSON (format ``structurb-note/1``) : entrées et résultats, pour les outils et les agents du navigateur."""
    giratoire = _est_giratoire(str(entrees.get("type_voie") or ""))

    def qualite(q: ResultatQualite, sans_objet: bool = False) -> dict:
        couches = (
            []
            if sans_objet and not q.trouvee
            else [
                {"role": role, "rang": rang, "materiau": lib, "epaisseur_cm": ep}
                for role, rang, lib, ep in _couches_detail(q.ligne, structure)
            ]
        )
        return {
            "trouvee": q.trouvee,
            "couches": couches,
            "qm": round(q.qm, 4),
            "minimum_technologique": q.min_technique.strip().upper() == "OUI",
            "maximum_pratique": q.max_pratique.strip().upper() == "OUI",
        }

    ep = r.epaisseur
    gel = {
        "indice_reference": r.indice_gel_ref,
        **{
            nom: (None if g is None else {
                "indice_admissible": None if g.indice_gel_adm == HORS_GEL else g.indice_gel_adm,
                "hors_gel": g.indice_gel_adm == HORS_GEL,
                "verifiee": g.verifiee,
            })
            for nom, g in (("q1", r.gel_q1), ("q2", r.gel_q2))
        },
    }
    d = {
        "format": "structurb-note/1",
        "titre": titre,
        "variante": variante,
        "date": date,
        "structure": {
            "abrege": structure.abrege,
            "surface": structure.couche_surface,
            "base": structure.couche_base,
            "fondation": structure.couche_fondation,
        },
        "entrees": entrees,
        "resultats": {
            "trafic_cumule": r.trafic_cumule,
            "cam": r.cam,
            "ne_equivalent": r.ne_equivalent,
            "ne_hors_limite": r.ne_hors_limite,
            "etude_labo_conseillee": r.etude_labo,
            "ne_theorique": None if ep is None else ep.ne_theorique,
            "q1": None if ep is None else qualite(ep.q1),
            "q2": None if ep is None else qualite(ep.q2, sans_objet=giratoire),
            "gel": gel,
        },
    }
    return d



def note_calcul_html(
    resultat: ResultatEtude,
    structure: StructureChaussee,
    *,
    type_voie: str,
    trafic_initial_pl: int,
    croissance_pct: Union[int, float],
    duree_ans: int,
    plate_forme: str,
    titre: str = "",
    variante: str = "",
    date: str = "",
    station: Optional[Union[StationMeteo, str]] = None,
    hiver: str = "HRNE",
    taille_agglo: Union[str, int] = "petite",
    indice_gel_perso: Optional[int] = None,
    pente_sol_pourcent: Optional[float] = None,
    epaisseur_non_gelive_cm: float = 0.0,
    couche_forme_traitee: bool = False,
    norme_2019: bool = False,
    fidele_vb6: bool = True,
    **_ignores: object,
) -> str:
    """Retourne la note de calcul d'une étude sous forme de page HTML autonome et imprimable.

    Les paramètres sont ceux passés à ``etude.dimensionner_etude`` (les autres sont ignorés),
    plus ``titre``, ``variante`` et ``date`` pour l'en-tête.
    """
    r = resultat
    titre_aff = titre.strip() or "Étude sans titre"
    sous = " · ".join(x for x in (f"Variante {variante}" if variante else "", date) if x)

    voie = [
        ("Type de voie", NOMS_VOIE.get(type_voie, type_voie)),
        ("Structure", f"{structure.abrege.strip()} (surface : {structure.couche_surface.strip()}, "
                      f"base : {structure.couche_base}, fondation : {structure.couche_fondation})"),
        ("Classe de plate-forme", plate_forme),
    ]
    trafic = [
        ("Trafic initial", f"{_nombre(trafic_initial_pl)} PL/j"),
        ("Taux de croissance annuel", f"{_nombre(croissance_pct)} %"),
        ("Durée de service", f"{duree_ans} ans"),
        ("Trafic cumulé", f"{_nombre(r.trafic_cumule)} PL"),
        ("Coefficient d’agressivité moyen (CAM)", _nombre(round(r.cam, 4))),
        ("Nombre d’essieux équivalents (NE)", _nombre(r.ne_equivalent)),
    ]
    alertes = []
    if r.ne_hors_limite:
        alertes.append("NE supérieur au maximum de la structure ou à 10 000 000 : hors du domaine de Struct-Urb.")
    if r.etude_labo:
        alertes.append("Trafic élevé : une étude en laboratoire est conseillée.")

    def table(lignes: List[Tuple[str, str]]) -> str:
        return "<table>" + "".join(
            f"<tr><th>{escape(k)}</th><td class=\"nombre\">{escape(v)}</td></tr>" for k, v in lignes
        ) + "</table>"

    parties = [
        "<!doctype html>",
        '<html lang="fr"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>Note de calcul – {escape(titre_aff)}</title><style>{_CSS}</style></head><body>",
        f"<h1>Note de calcul Struct-Urb – {escape(titre_aff)}</h1>",
        f'<p class="sous-titre">{escape(sous)}</p>' if sous else "",
        '<section id="donnees-voie"><h2>1. Voie et structure</h2>',
        table(voie),
        "</section>",
        '<section id="resultats-trafic"><h2>2. Trafic</h2>',
        table(trafic),
        "".join(f'<p class="alerte">{escape(a)}</p>' for a in alertes),
        "</section>",
        '<section id="resultats-epaisseurs"><h2>3. Épaisseurs</h2>',
    ]
    ep = r.epaisseur
    if ep is None:
        parties.append(
            '<p class="ko">Épaisseurs non trouvées : NE hors de la plage de la structure, '
            "plate-forme absente ou NE inconnu.</p>"
        )
    else:
        parties.append(
            f"<p>Ligne du catalogue retenue : NE théorique <strong class=\"nombre\">"
            f"{_nombre(ep.ne_theorique)}</strong> (palier immédiatement supérieur ou égal au NE).</p>"
        )
        parties.append('<div class="coupes">')
        if _est_giratoire(type_voie):
            # Réf. VB6 : frmDocument.frm (l. 4127) et frmImprimer.frm (l. 653) : pas de choix Q1/Q2 en giratoire
            parties.append(_bloc_qualite("Structure retenue (giratoire)", ep.q1, structure))
            parties.append('<div class="coupe"><h3>Qualité Q2</h3><p class="note">Q2 : sans objet (giratoire).</p></div>')
        else:
            parties.append(_bloc_qualite("Qualité Q1 (chantier courant)", ep.q1, structure))
            parties.append(_bloc_qualite("Qualité Q2 (chantier difficile)", ep.q2, structure))
        parties.append("</div>")

    parties.append("</section>")
    parties.append('<section id="resultats-gel"><h2>4. Vérification au gel / dégel</h2>')
    if r.indice_gel_ref is None and r.gel_q1 is None and r.gel_q2 is None:
        parties.append("<p>Vérification au gel non demandée (station ou indice de référence, ou pente du sol, absents).</p>")
    else:
        gel: List[Tuple[str, str]] = []
        if indice_gel_perso is not None:
            gel.append(("Indice de gel de référence", "indice personnel (relevés locaux)"))
        elif station is not None:
            nom_st = station if isinstance(station, str) else station.nom
            gel.append(("Station météo", str(nom_st)))
            gel.append(("Hiver de référence", NOMS_HIVER.get(hiver.upper(), hiver)))
            gel.append(("Taille de l’agglomération", str(taille_agglo)))
        if r.indice_gel_ref is not None:
            gel.append(("Indice de gel de référence corrigé", f"{r.indice_gel_ref} °C·j"))
        if pente_sol_pourcent is not None:
            gel.append(("Pente du sol support (essai de gonflement)", _nombre(pente_sol_pourcent)))
        gel.append(("Couche de forme non gélive", f"{_nombre(epaisseur_non_gelive_cm)} cm"
                    + (" (traitée)" if couche_forme_traitee else "")))
        for nom, g in (("Q1", r.gel_q1), ("Q2", r.gel_q2)):
            if g is None:
                continue
            adm = "hors gel" if g.indice_gel_adm == HORS_GEL else f"{g.indice_gel_adm} °C·j"
            gel.append((f"Indice de gel admissible {nom}", adm))
        parties.append(table(gel))
        verdicts = []
        for nom, g in (("Q1", r.gel_q1), ("Q2", r.gel_q2)):
            if g is not None:
                cls, txt = ("ok", "Vérifiée") if g.verifiee else ("ko", "Non vérifiée")
                verdicts.append(f'{nom} : <span class="{cls}">{txt}</span>')
        if verdicts:
            parties.append(f"<p>Chaussée protégée au gel — {' · '.join(verdicts)}</p>")
        methode = (
            "Méthode simplifiée de la NF P98-086 (2019), annexe H.3 (Kcr = 0,7, coefficients GCV de la norme)."
            if norme_2019 else "Méthode de Struct-Urb (VB6, Kcr = 0,6)."
        )
        epais = (
            "Épaisseurs du calcul au gel : comme le VB6 (lit de pose et 3 cm d’affichage compris)."
            if fidele_vb6 else "Épaisseurs du calcul au gel : épaisseurs du catalogue seules."
        )
        parties.append(f'<p class="note">{escape(methode)} {escape(epais)}</p>')

    parties.append("</section>")
    donnees = _json_script(donnees_note(
        r, structure, titre=titre, variante=variante, date=date,
        entrees=dict(
            type_voie=type_voie, trafic_initial_pl=trafic_initial_pl, croissance_pct=croissance_pct,
            duree_ans=duree_ans, plate_forme=plate_forme,
            station=(station if isinstance(station, str) or station is None else station.nom),
            hiver=hiver, taille_agglo=taille_agglo, indice_gel_perso=indice_gel_perso,
            pente_sol_pourcent=pente_sol_pourcent, epaisseur_non_gelive_cm=epaisseur_non_gelive_cm,
            couche_forme_traitee=couche_forme_traitee, norme_2019=norme_2019, fidele_vb6=fidele_vb6,
        ),
    ))
    parties.append(f'<script type="application/json" id="structurb-donnees">{donnees}</script>')
    parties.append(
        '<p class="note">Note produite par structurb (portage Python de Struct-Urb, CERTU / Cerema, '
        "licence GPL v3). Résultats à vérifier par le projeteur.</p>"
    )
    parties.append(signature_html() + "</body></html>")
    return "\n".join(p for p in parties if p)
