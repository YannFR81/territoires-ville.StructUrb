"""Orchestrateur d'étude complète Struct-Urb (Trafic -> Catalogue -> Épaisseurs -> Gel).

Références VB6 d'origine (CEREMA/territoires-ville.StructUrb) :
- ``ModuleMain.bas`` : constantes ``Souple..PavesDalles`` (lignes 171-176),
  ``RemplirComboStructures`` (lignes 1593-1670), ``MettreAJourOngletCoucheSurface``
  (lignes 1408-1485), enchaînement ``CalculerEtAfficherNE`` -> ``RechercherEpaisseur``
  -> ``CalculerIndiceGelRef`` / ``CalculerIndiceGelAdm``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Tuple, Union

from .catalogue import (
    CatalogueMatSurface,
    CatalogueStructures,
    CompositionSurface,
    MateriauCompose,
    StructureChaussee,
)
from .epaisseur import (
    ResultatEpaisseur,
    epaisseur_possible,
    epaisseurs_pour_gel,
    rechercher_epaisseur,
)
from .gel import (
    AGEL_GCV_NF_P98_086,
    BGEL_GCV_NF_P98_086,
    STATIONS_METEO,
    StationMeteo,
    chaussee_verifiee_au_gel,
    indice_gel_admissible,
    indice_gel_reference,
)
from .trafic import (
    TYPES_VOIE,
    bornes_trafic_initial,
    cam_preconise,
    etude_labo_conseillee,
    ne_equivalent,
    ne_hors_limite,
    statut_trafic_initial,
    trafic_cumule,
)

# Familles de structures (ModuleMain.bas, lignes 171-176)
TYPES_STRUCTURE: dict[int, str] = {
    1: "souple",
    2: "bitumineuse",
    3: "gtlh",
    4: "beton",
    5: "mixte",
    6: "paves_dalles",
}
_TYPES_STRUCTURE_PAR_NOM: dict[str, int] = {v: k for k, v in TYPES_STRUCTURE.items()}

_ATTR_VOIE_STRUCTURE: dict[str, str] = {
    "desserte": "util_v_des",
    "distribution": "util_v_dis",
    "trafic_lourd": "util_v_pl",
    "bus": "util_v_bus",
    "parking": "util_v_parking",
    "giratoire_distribution": "util_g_dis",
    "giratoire_trafic_lourd": "util_g_pl",
}


@dataclass(frozen=True)
class ResultatGelQualite:
    """Résultat de la vérification au gel pour une qualité (Q1 ou Q2)."""

    epaisseurs_gel: Tuple[int, int, int, int, int, int]
    indice_gel_adm: int
    verifiee: bool


@dataclass(frozen=True)
class ResultatEtude:
    """Résultat complet d'un dimensionnement Struct-Urb."""

    trafic_cumule: int
    cam: float
    ne_equivalent: int
    ne_hors_limite: bool
    etude_labo: bool
    epaisseur: Optional[ResultatEpaisseur]
    compositions_q1: Tuple[CompositionSurface, ...]
    compositions_q2: Tuple[CompositionSurface, ...]
    indice_gel_ref: Optional[int]
    gel_q1: Optional[ResultatGelQualite]
    gel_q2: Optional[ResultatGelQualite]


def structures_compatibles(
    catalogue: CatalogueStructures,
    type_voie: str,
    type_structure: Optional[Union[int, str]] = None,
    materiaux_exclus: Iterable[str] = (),
) -> Tuple[Tuple[int, StructureChaussee], ...]:
    """Retourne les couples ``(index, structure)`` compatibles avec le type de voie.

    Extensions par rapport au VB6 (``ModuleMain.bas :: RemplirComboStructures``, l. 1593-1670) :
    - ``type_structure=None`` accepte tous les types de structures (le VB6 en exige un) ;
    - ``materiaux_exclus`` remplace le drapeau ``monUtilisationAutorisée`` des options générales.
    """
    if type_voie not in _ATTR_VOIE_STRUCTURE:
        raise ValueError(f"Type de voie inconnu : {type_voie!r} (attendu : {TYPES_VOIE}).")

    code_struct: Optional[int] = None
    if type_structure is not None:
        if isinstance(type_structure, int) and not isinstance(type_structure, bool):
            if type_structure not in TYPES_STRUCTURE:
                raise ValueError(f"Code de type de structure invalide : {type_structure} (1..6).")
            code_struct = type_structure
        elif isinstance(type_structure, str):
            cle = type_structure.strip().lower()
            if cle not in _TYPES_STRUCTURE_PAR_NOM:
                raise ValueError(
                    f"Type de structure inconnu : {type_structure!r} "
                    f"(attendu : {tuple(_TYPES_STRUCTURE_PAR_NOM)})."
                )
            code_struct = _TYPES_STRUCTURE_PAR_NOM[cle]
        else:
            raise ValueError(f"Type invalide pour type_structure : {type(type_structure).__name__}")

    exclus_min = {m.lower() for m in materiaux_exclus}
    attr_voie = _ATTR_VOIE_STRUCTURE[type_voie]

    resultat: list[Tuple[int, StructureChaussee]] = []
    for idx, st in enumerate(catalogue.structures):
        if getattr(st, attr_voie) != 1:
            continue
        if code_struct is not None and st.type_structure != code_struct:
            continue
        if st.couche_base != "Aucune" and st.couche_base.lower() in exclus_min:
            continue
        if st.couche_fondation != "Aucune" and st.couche_fondation.lower() in exclus_min:
            continue
        resultat.append((idx, st))
    return tuple(resultat)


def compositions_surface_compatibles(
    materiau_surface: object, epaisseur_preconisee: int
) -> Tuple[CompositionSurface, ...]:
    """Retourne les compositions possibles d'un ``MateriauCompose`` pour une épaisseur préconisée.

    Réf. VB6 : ``ModuleMain.bas :: MettreAJourOngletCoucheSurface`` (lignes 1457-1469).
    """
    if not isinstance(materiau_surface, MateriauCompose):
        return ()
    return tuple(
        c for c in materiau_surface.compositions if c.epaisseur_preconisee == epaisseur_preconisee
    )


def _coefs_gel_structure(
    structure: StructureChaussee,
    catalogue_structures: CatalogueStructures,
    catalogue_surfaces: CatalogueMatSurface,
    norme_2019: bool = False,
) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    if structure.couche_surface == "Aucune":
        a_cs, b_cs = 0.0, 0.0
    else:
        ms = catalogue_surfaces.obtenir(structure.couche_surface)
        a_cs, b_cs = ms.a_gel, ms.b_gel

    mb = catalogue_structures.obtenir_materiau_bf(structure.couche_base)
    if norme_2019 and structure.couche_base.upper() == "GCV":
        a_cb, b_cb = AGEL_GCV_NF_P98_086, BGEL_GCV_NF_P98_086
    else:
        a_cb, b_cb = mb.a_gel, mb.b_gel

    if structure.couche_fondation == "Aucune":
        a_cf, b_cf = 0.0, 0.0
    elif norme_2019 and structure.couche_fondation.upper() == "GCV":
        a_cf, b_cf = AGEL_GCV_NF_P98_086, BGEL_GCV_NF_P98_086
    else:
        mf = catalogue_structures.obtenir_materiau_bf(structure.couche_fondation)
        a_cf, b_cf = mf.a_gel, mf.b_gel

    return (a_cs, a_cb, a_cf), (b_cs, b_cb, b_cf)


def dimensionner_etude(
    catalogue_structures: CatalogueStructures,
    catalogue_surfaces: CatalogueMatSurface,
    structure: StructureChaussee,
    type_voie: str,
    trafic_initial_pl: int,
    croissance_pct: int,
    duree_ans: int,
    plate_forme: str,
    cam: Optional[float] = None,
    station: Optional[Union[StationMeteo, str]] = None,
    hiver: str = "HRNE",
    taille_agglo: Union[str, int] = "petite",
    indice_gel_perso: Optional[int] = None,
    epaisseur_non_gelive_cm: float = 0.0,
    couche_forme_traitee: bool = False,
    pente_sol_pourcent: Optional[float] = None,
    fidele_vb6: bool = True,
    norme_2019: bool = False,
) -> ResultatEtude:
    """Exécute un dimensionnement complet (Trafic -> NE -> Épaisseurs -> Surface -> Gel).

    Réf. VB6 : ``frmDocument.frm`` (l. 2985-2989 : PF1 interdite en giratoire) ;
    ``ModuleSaisie.bas :: VerifierMinMaxTraficIni`` (l. 51-103 : plage tolérée de trafic initial).
    """
    if type_voie in ("giratoire_distribution", "giratoire_trafic_lourd") and plate_forme == "PF1":
        raise ValueError(
            "La plate-forme PF1 n’est pas admise pour un giratoire (choisir PF2, PF2+ ou PF3)."
        )
    if statut_trafic_initial(trafic_initial_pl, type_voie) == "hors_domaine":
        min_tol, _, _, max_tol = bornes_trafic_initial(type_voie)
        raise ValueError(
            f"Trafic initial hors domaine pour {type_voie} : "
            f"{trafic_initial_pl} PL/j (plage tolérée : {min_tol} à {max_tol} PL/j)."
        )
    t_cum = trafic_cumule(trafic_initial_pl, croissance_pct, duree_ans)
    famille = TYPES_STRUCTURE.get(structure.type_structure, "")
    cam_val = (
        float(cam)
        if cam is not None
        else cam_preconise(
            type_voie,
            structure.type_cam,
            type_structure=famille,
            couche_base=structure.couche_base,
        )[0]
    )
    ne = ne_equivalent(t_cum, cam_val)
    hors_lim = ne_hors_limite(ne) or ne > structure.nb_essieux_max
    labo = etude_labo_conseillee(trafic_initial_pl, type_voie)

    res_ep: Optional[ResultatEpaisseur] = None
    if epaisseur_possible(ne, structure, plate_forme):
        res_ep = rechercher_epaisseur(ne, structure, plate_forme)

    comps_q1: Tuple[CompositionSurface, ...] = ()
    comps_q2: Tuple[CompositionSurface, ...] = ()
    if res_ep is not None and structure.couche_surface != "Aucune":
        if res_ep.q1.trouvee or res_ep.q2.trouvee:
            mat_surf = catalogue_surfaces.obtenir(structure.couche_surface)
            comps_q1 = compositions_surface_compatibles(mat_surf, res_ep.q1.epaisseur_preconisee)
            comps_q2 = compositions_surface_compatibles(mat_surf, res_ep.q2.epaisseur_preconisee)

    i_ref: Optional[int] = None
    if indice_gel_perso is not None:
        i_ref = indice_gel_reference(
            STATIONS_METEO[0],
            hiver=hiver,
            taille_agglo=taille_agglo,
            indice_personnel=indice_gel_perso,
        )
    elif station is not None:
        i_ref = indice_gel_reference(
            station,
            hiver=hiver,
            taille_agglo=taille_agglo,
        )

    gel_q1: Optional[ResultatGelQualite] = None
    gel_q2: Optional[ResultatGelQualite] = None
    if res_ep is not None and pente_sol_pourcent is not None:
        agel, bgel = _coefs_gel_structure(
            structure, catalogue_structures, catalogue_surfaces, norme_2019=norme_2019
        )
        if res_ep.q1.trouvee:
            ep_g1 = epaisseurs_pour_gel(res_ep.q1, fidele_vb6=fidele_vb6)
            adm1 = indice_gel_admissible(
                ep_g1,
                agel,
                bgel,
                res_ep.q1.qm,
                epaisseur_non_gelive_cm=epaisseur_non_gelive_cm,
                couche_forme_traitee=couche_forme_traitee,
                pente_sol_pourcent=pente_sol_pourcent,
                norme_2019=norme_2019,
            )
            ok1 = chaussee_verifiee_au_gel(i_ref, adm1) if i_ref is not None else False
            gel_q1 = ResultatGelQualite(epaisseurs_gel=ep_g1, indice_gel_adm=adm1, verifiee=ok1)
        if res_ep.q2.trouvee:
            ep_g2 = epaisseurs_pour_gel(res_ep.q2, fidele_vb6=fidele_vb6)
            adm2 = indice_gel_admissible(
                ep_g2,
                agel,
                bgel,
                res_ep.q2.qm,
                epaisseur_non_gelive_cm=epaisseur_non_gelive_cm,
                couche_forme_traitee=couche_forme_traitee,
                pente_sol_pourcent=pente_sol_pourcent,
                norme_2019=norme_2019,
            )
            ok2 = chaussee_verifiee_au_gel(i_ref, adm2) if i_ref is not None else False
            gel_q2 = ResultatGelQualite(epaisseurs_gel=ep_g2, indice_gel_adm=adm2, verifiee=ok2)

    return ResultatEtude(
        trafic_cumule=t_cum,
        cam=cam_val,
        ne_equivalent=ne,
        ne_hors_limite=hors_lim,
        etude_labo=labo,
        epaisseur=res_ep,
        compositions_q1=comps_q1,
        compositions_q2=comps_q2,
        indice_gel_ref=i_ref,
        gel_q1=gel_q1,
        gel_q2=gel_q2,
    )
