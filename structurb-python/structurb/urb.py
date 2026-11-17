"""Lecture/écriture des fichiers d'étude ``*.urb`` et génération de note de calcul.

Références VB6 d'origine (CEREMA/territoires-ville.StructUrb) :
- ``ModuleFichier.bas`` : ``EcrireDansFichier`` (lignes 6-134), ``OuvrirEtude`` (lignes 136-308) ;
- ``ModuleMain.bas`` : ``EnteteFichUrbV1``, ``EnteteFichUrbV2``, ``ChantierDifficile = 100``,
  ``FinTitre = "###FinTitre###"``.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .catalogue import StructureChaussee
from .etude import ResultatEtude
from .trafic import TYPES_VOIE

ENTETE_URB_V1: str = "Fichier Struct-Urb 1.0"
ENTETE_URB_V2: str = "Fichier Struct-Urb 2.0"
FIN_TITRE: str = "###FinTitre###"
CHANTIER_DIFFICILE: int = 100

_CODE_VERS_VOIE: dict[int, str] = {i + 1: v for i, v in enumerate(TYPES_VOIE)}
_VOIE_VERS_CODE: dict[str, int] = {v: i + 1 for i, v in enumerate(TYPES_VOIE)}
_CODE_VERS_HIVER: dict[int, str] = {1: "HE", 2: "HRNE", 3: "HC"}
_HIVER_VERS_CODE: dict[str, int] = {"HE": 1, "HRNE": 2, "HC": 3}


@dataclass
class EtudeUrb:
    """Représentation d'une étude Struct-Urb stockée dans un fichier ``*.urb``."""

    entete: str = ENTETE_URB_V2
    titre: str = ""
    type_voie: str = "desserte"
    qualite: str = "Q1"
    variante: str = ""
    date: str = ""
    trafic_initial: str = "0"
    duree_service: int = 20
    croissance_pct: int = 2
    trafic_cumule: str = "0"
    combo_struct_idx: int = -1
    num_index_structure: int = 0
    util_fichier_perso: int = 0
    fichier_perso: str = ""
    ind_mat_base: int = 0
    ind_mat_fondation: int = 0
    cam: str = "0.1"
    indice_pf: int = 2
    ind_comp_q1: int = 0
    ind_comp_q2: int = 0
    hiver: str = "HRNE"
    indice_station: int = 1
    altitude_agglo: int = 0
    taille_agglo: int = 0
    type_gel_sol: int = 2
    pente_sol: str = "0.5"
    coef_a: float = 0.12
    epaisseur_non_gelive: int = 0
    format_version: int = 2
    indice_gel_perso: int = 0
    util_indice_gel_perso: int = 0


def _fmt_vb_quote(val: object) -> str:
    if isinstance(val, str):
        return f'"{val}"'
    if isinstance(val, float):
        return f"{val:g}"
    return str(val)


def _decoder_voie_qualite(code_brut: int) -> tuple[str, str]:
    if code_brut > CHANTIER_DIFFICILE:
        qualite = "Q2"
        code_voie = code_brut - CHANTIER_DIFFICILE
    else:
        qualite = "Q1"
        code_voie = code_brut
    if code_voie not in _CODE_VERS_VOIE:
        raise ValueError(f"Code de type de voie invalide dans .urb : {code_brut}")
    return _CODE_VERS_VOIE[code_voie], qualite


def lire_urb(chemin: str | Path) -> EtudeUrb:
    """Lit un fichier d'étude ``*.urb`` (v1.0 ou v2.0, format VB6 ``Write #``)."""
    path = Path(chemin)
    if not path.is_file():
        raise FileNotFoundError(f"Fichier .urb introuvable : {path}")

    lignes = [l for l in path.read_text(encoding="cp1252").splitlines() if l.strip()]
    if not lignes:
        raise ValueError(f"Fichier .urb vide : {path}")

    def parse_row(idx: int) -> list[str]:
        return next(csv.reader(io.StringIO(lignes[idx]), delimiter=",", quotechar='"'))

    entete = parse_row(0)[0]
    if entete not in (ENTETE_URB_V1, ENTETE_URB_V2):
        raise ValueError(f"En-tête .urb invalide : {entete!r}")

    # Titre multi-lignes jusqu'à FIN_TITRE
    titre_parts: list[str] = []
    pos = 1
    while pos < len(lignes):
        val = parse_row(pos)[0]
        pos += 1
        if val == FIN_TITRE:
            break
        titre_parts.append(val)
    titre = "\n".join(titre_parts)

    r_voie = parse_row(pos)
    type_voie, qualite = _decoder_voie_qualite(int(r_voie[0]))
    variante, date = r_voie[1], r_voie[2]
    pos += 1

    r_traf = parse_row(pos)
    traf_ini, duree, croiss, traf_cum = r_traf[0], int(r_traf[1]), int(r_traf[2]), r_traf[3]
    pos += 1

    r_str = parse_row(pos)
    combo_idx, num_idx, util_perso, fich_perso = int(r_str[0]), int(r_str[1]), int(r_str[2]), r_str[3]
    pos += 1

    r_mats = parse_row(pos)
    ind_base, ind_fond = int(r_mats[0].strip()), int(r_mats[1].strip())
    pos += 1

    r_campf = parse_row(pos)
    cam, ind_pf = r_campf[0], int(r_campf[1])
    pos += 1

    r_surf = parse_row(pos)
    comp_q1, comp_q2 = int(r_surf[0]), int(r_surf[1])
    pos += 1

    r_gel1 = parse_row(pos)
    hiver_code, ind_st, alt_agglo, taille_agglo = int(r_gel1[0]), int(r_gel1[1]), int(r_gel1[2]), int(r_gel1[3])
    hiver = _CODE_VERS_HIVER.get(hiver_code, "HRNE")
    pos += 1

    r_gel2 = parse_row(pos)
    type_gel_sol, pente_sol, coef_a, ep_ng = int(r_gel2[0]), r_gel2[1], float(r_gel2[2]), int(r_gel2[3])
    pos += 1

    if pos < len(lignes):
        r_perso = parse_row(pos)
        fmt_ver, ind_perso, util_perso_gel = int(r_perso[0]), int(r_perso[1]), int(r_perso[2])
    else:
        fmt_ver, ind_perso, util_perso_gel = 1, 0, 0

    return EtudeUrb(
        entete=entete,
        titre=titre,
        type_voie=type_voie,
        qualite=qualite,
        variante=variante,
        date=date,
        trafic_initial=traf_ini,
        duree_service=duree,
        croissance_pct=croiss,
        trafic_cumule=traf_cum,
        combo_struct_idx=combo_idx,
        num_index_structure=num_idx,
        util_fichier_perso=util_perso,
        fichier_perso=fich_perso,
        ind_mat_base=ind_base,
        ind_mat_fondation=ind_fond,
        cam=cam,
        indice_pf=ind_pf,
        ind_comp_q1=comp_q1,
        ind_comp_q2=comp_q2,
        hiver=hiver,
        indice_station=ind_st,
        altitude_agglo=alt_agglo,
        taille_agglo=taille_agglo,
        type_gel_sol=type_gel_sol,
        pente_sol=pente_sol,
        coef_a=coef_a,
        epaisseur_non_gelive=ep_ng,
        format_version=fmt_ver,
        indice_gel_perso=ind_perso,
        util_indice_gel_perso=util_perso_gel,
    )


def ecrire_urb(chemin: str | Path, etude: EtudeUrb) -> None:
    """Écrit une étude au format ``*.urb`` compatible Struct-Urb VB6."""
    if etude.type_voie not in _VOIE_VERS_CODE:
        raise ValueError(f"Type de voie inconnu : {etude.type_voie!r}")
    code_voie = _VOIE_VERS_CODE[etude.type_voie]
    if etude.qualite.upper() == "Q2":
        code_voie += CHANTIER_DIFFICILE
    hiver_code = _HIVER_VERS_CODE.get(etude.hiver.upper(), 2)

    lignes = [
        _fmt_vb_quote(etude.entete),
        _fmt_vb_quote(etude.titre),
        _fmt_vb_quote(FIN_TITRE),
        ",".join([_fmt_vb_quote(code_voie), _fmt_vb_quote(etude.variante), _fmt_vb_quote(etude.date)]),
        ",".join([
            _fmt_vb_quote(etude.trafic_initial),
            _fmt_vb_quote(etude.duree_service),
            _fmt_vb_quote(etude.croissance_pct),
            _fmt_vb_quote(etude.trafic_cumule),
        ]),
        ",".join([
            _fmt_vb_quote(etude.combo_struct_idx),
            _fmt_vb_quote(etude.num_index_structure),
            _fmt_vb_quote(etude.util_fichier_perso),
            _fmt_vb_quote(etude.fichier_perso),
        ]),
        ",".join([_fmt_vb_quote(f" {etude.ind_mat_base} "), _fmt_vb_quote(f" {etude.ind_mat_fondation} ")]),
        ",".join([_fmt_vb_quote(etude.cam), _fmt_vb_quote(etude.indice_pf)]),
        ",".join([_fmt_vb_quote(etude.ind_comp_q1), _fmt_vb_quote(etude.ind_comp_q2)]),
        ",".join([
            _fmt_vb_quote(hiver_code),
            _fmt_vb_quote(etude.indice_station),
            _fmt_vb_quote(etude.altitude_agglo),
            _fmt_vb_quote(etude.taille_agglo),
        ]),
        ",".join([
            _fmt_vb_quote(etude.type_gel_sol),
            _fmt_vb_quote(etude.pente_sol),
            _fmt_vb_quote(etude.coef_a),
            _fmt_vb_quote(etude.epaisseur_non_gelive),
        ]),
        ",".join([
            _fmt_vb_quote(etude.format_version),
            _fmt_vb_quote(etude.indice_gel_perso),
            _fmt_vb_quote(etude.util_indice_gel_perso),
        ]),
    ]
    Path(chemin).write_text("\n".join(lignes) + "\n", encoding="cp1252")


def formater_note_calcul(
    etude: EtudeUrb,
    resultat: ResultatEtude,
    structure: Optional[StructureChaussee] = None,
) -> str:
    """Génère une note de calcul structurée en Markdown pour un dossier de voirie."""
    lignes = [
        f"# Note de calcul Struct-Urb — {etude.titre or 'Étude sans titre'}",
        "",
        f"- **Variante** : {etude.variante or '—'} | **Date** : {etude.date or '—'}",
        f"- **Type de voie** : `{etude.type_voie}` | **Qualité de chantier** : `{etude.qualite}`",
    ]
    if structure is not None:
        lignes.append(
            f"- **Structure** : `{structure.abrege}` "
            f"(surface : {structure.couche_surface}, base : {structure.couche_base}, "
            f"fondation : {structure.couche_fondation})"
        )
    lignes += [
        "",
        "## 1. Trafic et nombre d'essieux équivalents",
        f"- Trafic cumulé : **{resultat.trafic_cumule:,} PL**".replace(",", " "),
        f"- CAM retenu : **{resultat.cam:g}**",
        f"- Nombre d'essieux équivalents (NE) : **{resultat.ne_equivalent:,}**".replace(",", " "),
        f"- Étude en laboratoire conseillée : **{'Oui' if resultat.etude_labo else 'Non'}**",
    ]
    if resultat.epaisseur is not None:
        ep = resultat.epaisseur
        lignes += [
            "",
            f"## 2. Dimensionnement mécanique (NE théorique : {ep.ne_theorique:,})".replace(",", " "),
            f"- **Q1** : épaisseurs `{' / '.join(str(x) for x in ep.q1.epaisseurs)}` cm "
            f"(trouvée : {'Oui' if ep.q1.trouvee else 'Non'})",
            f"- **Q2** : épaisseurs `{' / '.join(str(x) for x in ep.q2.epaisseurs)}` cm "
            f"(trouvée : {'Oui' if ep.q2.trouvee else 'Non'})",
        ]
    if resultat.indice_gel_ref is not None:
        lignes += [
            "",
            "## 3. Vérification au gel",
            f"- Indice de gel de référence corrigé ($I_{{\\text{{ref}}}}$) : **{resultat.indice_gel_ref} °C·j**",
        ]
        if resultat.gel_q1 is not None:
            st1 = "Vérifiée" if resultat.gel_q1.verifiee else "Non vérifiée"
            lignes.append(f"- **Q1** : $I_{{\\text{{adm}}}} = {resultat.gel_q1.indice_gel_adm}$ °C·j → **{st1}**")
        if resultat.gel_q2 is not None:
            st2 = "Vérifiée" if resultat.gel_q2.verifiee else "Non vérifiée"
            lignes.append(f"- **Q2** : $I_{{\\text{{adm}}}} = {resultat.gel_q2.indice_gel_adm}$ °C·j → **{st2}**")
    return "\n".join(lignes) + "\n"
