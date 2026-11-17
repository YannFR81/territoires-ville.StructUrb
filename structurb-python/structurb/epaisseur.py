"""Recherche d'épaisseur dans le catalogue Struct-Urb (portage fidèle du code VB6).

Références VB6 d'origine (CEREMA/territoires-ville.StructUrb) :
- ``ModuleMain.bas`` : ``TrouverEpaisseurPossible`` (lignes 2645-2673),
  ``RechercherEpaisseur`` (lignes 2675-2794), ``TrouverNEthEtInd`` (lignes 2824-2845),
  constantes ``EpParDefaut`` et ``EpLitPose`` (lignes 124 et 127) ;
- ``frmDocument.frm`` : ``monNEEquiv`` et ``monNEth`` (``Long``), ``monTabEp`` (``Variant``),
  ``monQmQ1/Q2`` (``Single``), ``monEpQ1Trouv/Q2Trouv`` (``Boolean``) (lignes 2140-2186).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple

from .catalogue import LigneEpaisseur, StructureChaussee
from .trafic import ne_hors_limite, vb_clng

# Classes de plate-forme dans l'ordre de l'onglet « Plate-forme »
PLATES_FORMES: Tuple[str, ...] = ("PF1", "PF2", "PF2+", "PF3")

# Épaisseur du lit de pose des pavés et dalles (ModuleMain.bas, ligne 127 : EpLitPose)
EP_LIT_POSE: int = 4

# Épaisseur affichée pour une couche de surface « sans épaisseur » (RechercherEpaisseur)
EP_SURFACE_SANS_EPAISSEUR: int = 3


@dataclass(frozen=True)
class ResultatQualite:
    """Résultat de la recherche pour une qualité de réalisation (Q1 ou Q2).

    ``epaisseurs`` reprend les 6 cases de ``monTabEp`` pour cette qualité, en cm :
    ``(surface, surface_2, base_1, base_2, fondation_1, fondation_2)``.
    ``surface_2`` vaut 0, sauf pour les pavés et dalles où elle porte le lit de pose (4 cm).
    Pour une couche de surface « sans épaisseur », ``surface`` vaut 3 cm.

    Attention : c'est ce tableau, avec le lit de pose et les 3 cm d'affichage, que le VB6
    passe ensuite à ``CalculerIndiceGelAdm`` (voir ``gel.indice_gel_admissible``).
    Pour choisir les épaisseurs du calcul au gel, utiliser ``epaisseurs_pour_gel``.
    """

    epaisseurs: Tuple[int, int, int, int, int, int]
    epaisseur_preconisee: int
    qm: float
    min_technique: str
    max_pratique: str
    trouvee: bool
    ligne: LigneEpaisseur


@dataclass(frozen=True)
class ResultatEpaisseur:
    """Résultat de ``rechercher_epaisseur`` pour une structure et une plate-forme."""

    ne_theorique: int
    indice: int
    q1: ResultatQualite
    q2: ResultatQualite


def ne_theorique_et_indice(ne: int, nb_essieux_min: int) -> Tuple[int, int]:
    """Retourne le NE théorique (palier immédiatement supérieur ou égal) et son indice (base 1).

    Les paliers partent de ``nb_essieux_min`` ; le pas vaut 10 puissance (nombre de chiffres - 1)
    du palier courant : 1 000, 2 000, …, 9 000, 10 000, 20 000, …
    Un NE inférieur au minimum donne le minimum et l'indice 1, comme en VB6.

    Réf. VB6 : ``ModuleMain.bas :: TrouverNEthEtInd`` (lignes 2824-2845).
    ``unPas = Exp(unM * Log(10))`` est un ``Double`` affecté à un ``Long`` (``CLng``).
    """
    indice = 0
    ne0 = int(nb_essieux_min)
    while True:
        indice += 1
        m = len(str(ne0)) - 1  # Len(Format(unNEth0)) - 1
        pas = vb_clng(math.exp(m * math.log(10)))
        if ne > ne0:
            ne0 += pas
        else:
            return ne0, indice


def epaisseur_possible(
    ne: Optional[int],
    structure: Optional[StructureChaussee],
    plate_forme: Optional[str],
) -> bool:
    """Indique si les épaisseurs peuvent être cherchées.

    Il faut une plate-forme, une structure, un NE connu, compris entre les NE min et max
    de la structure, et au plus égal à 10 000 000.

    Réf. VB6 : ``ModuleMain.bas :: TrouverEpaisseurPossible`` (lignes 2645-2673).
    ``ne is None`` correspond au NE « inconnu » du VB6.
    """
    if plate_forme not in PLATES_FORMES:
        return False
    if structure is None:
        return False
    if ne is None:
        return False
    if ne < structure.nb_essieux_min or ne > structure.nb_essieux_max:
        return False
    if ne_hors_limite(ne):
        return False
    return True


def _resultat_qualite(
    ligne: LigneEpaisseur, structure: StructureChaussee
) -> ResultatQualite:
    """Construit le résultat d'une qualité à partir d'une ligne du catalogue.

    Réf. VB6 : ``ModuleMain.bas :: RechercherEpaisseur`` (l. 2722-2779) et
    ``AfficherCarottes`` (l. 1750-1751 : pas de Q2 en étude giratoire).
    Les grilles Q2 des structures giratoires ont toutes leurs épaisseurs à 0
    dans ``Certu.str`` : ``trouvee`` vaut alors ``False``.
    """
    grille_vide = (
        ligne.epaisseur_surface == 0
        and ligne.epaisseur_base_1 == 0
        and ligne.epaisseur_base_2 == 0
        and ligne.epaisseur_fondation_1 == 0
        and ligne.epaisseur_fondation_2 == 0
    )
    if grille_vide:
        return ResultatQualite(
            epaisseurs=(0, 0, 0, 0, 0, 0),
            epaisseur_preconisee=0,
            qm=ligne.qm,
            min_technique=ligne.min_technique,
            max_pratique=ligne.max_pratique,
            trouvee=False,
            ligne=ligne,
        )
    ep = [
        ligne.epaisseur_surface,
        0,
        ligne.epaisseur_base_1,
        ligne.epaisseur_base_2,
        ligne.epaisseur_fondation_1,
        ligne.epaisseur_fondation_2,
    ]
    # Cas de couches de surface particulières (comparaisons exactes, Option Compare Binary)
    if structure.couche_surface != "Aucune" and structure.couche_surf_sans_ep == 1:
        ep[0] = EP_SURFACE_SANS_EPAISSEUR
    elif structure.couche_surface in ("Dalles", "Pavés"):
        ep[1] = EP_LIT_POSE
    return ResultatQualite(
        epaisseurs=tuple(ep),  # type: ignore[arg-type]
        epaisseur_preconisee=ligne.epaisseur_surface,
        qm=ligne.qm,
        min_technique=ligne.min_technique,
        max_pratique=ligne.max_pratique,
        trouvee=ligne.max_pratique.upper() != "OUI",
        ligne=ligne,
    )


def epaisseurs_pour_gel(
    qualite: ResultatQualite, fidele_vb6: bool = True
) -> Tuple[int, int, int, int, int, int]:
    """Épaisseurs (cm) à passer à ``gel.indice_gel_admissible`` pour une qualité.

    - ``fidele_vb6=True`` (par défaut) : comme le VB6, qui passe ``monTabEp`` tel quel à
      ``CalculerIndiceGelAdm``. Le lit de pose des pavés et dalles (4 cm) et les 3 cm
      d'affichage d'une couche de surface « sans épaisseur » entrent donc dans le calcul.
    - ``fidele_vb6=False`` : épaisseurs du catalogue seules (surface lue dans la grille,
      pas de lit de pose). Option ajoutée par décision de YannFR81 du 2026-11-17 ;
      ce n'est pas un comportement du VB6.

    Avec le catalogue Certu, seules les 20 structures en pavés ou dalles changent :
    la seule couche « sans épaisseur » est l'enduit superficiel (ES), dont Agel et Bgel
    sont nuls. Les 3 cm comptent seulement avec un catalogue personnel.

    Réf. VB6 : ``ModuleMain.bas :: RechercherEpaisseur`` (lignes 2675-2794) et
    ``CalculerIndiceGelAdm`` (lignes 2537-2642).
    """
    if fidele_vb6:
        return qualite.epaisseurs
    lig = qualite.ligne
    return (
        lig.epaisseur_surface,
        0,
        lig.epaisseur_base_1,
        lig.epaisseur_base_2,
        lig.epaisseur_fondation_1,
        lig.epaisseur_fondation_2,
    )


def rechercher_epaisseur(
    ne: int, structure: StructureChaussee, plate_forme: str
) -> Optional[ResultatEpaisseur]:
    """Cherche les épaisseurs Q1 et Q2 de la structure pour le NE et la plate-forme donnés.

    La ligne retenue est celle du NE théorique (palier immédiatement supérieur ou égal au NE).
    L'épaisseur est « non trouvée » quand le maximum pratique vaut « Oui ».
    Retourne ``None`` si le NE sort de la plage de la structure : le VB6 met alors
    ``monEpQ1Trouv`` et ``monEpQ2Trouv`` à faux (« normalement on ne passe jamais là »).

    Réf. VB6 : ``ModuleMain.bas :: RechercherEpaisseur`` (lignes 2675-2794).
    Écart : le VB6 prend PF3 pour toute plate-forme non reconnue ; ici, une plate-forme
    hors de ``PLATES_FORMES`` lève ``ValueError`` (``TrouverEpaisseurPossible`` l'exclut déjà).
    """
    if plate_forme not in PLATES_FORMES:
        raise ValueError(f"Plate-forme invalide : {plate_forme!r} (attendu : {PLATES_FORMES}).")
    if ne < structure.nb_essieux_min or ne > structure.nb_essieux_max:
        return None

    ne_th, indice = ne_theorique_et_indice(ne, structure.nb_essieux_min)
    ligne_q1 = structure.grilles_pf[f"{plate_forme}_Q1"][indice - 1]
    ligne_q2 = structure.grilles_pf[f"{plate_forme}_Q2"][indice - 1]
    return ResultatEpaisseur(
        ne_theorique=ne_th,
        indice=indice,
        q1=_resultat_qualite(ligne_q1, structure),
        q2=_resultat_qualite(ligne_q2, structure),
    )
