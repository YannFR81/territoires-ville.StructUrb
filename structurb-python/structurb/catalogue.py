"""Lecture des catalogues binaires Struct-Urb (``Certu.str`` et ``Certu.mts``).

Références VB6 d'origine (CEREMA/territoires-ville.StructUrb) :
- ``ModuleMain.bas`` : ``OuvrirFichierStructures`` (lignes 362-597),
  ``OuvrirFichierMatSurface`` (lignes 1846-1985) ;
- ``Utilitaires.bas`` : ``DonnerColPF`` (lignes 70-95), ``LireString`` (lignes 110-123) ;
- ``Structure.cls``, ``Matériau.cls``, ``MatSimple.cls``, ``MatComposé.cls``.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Dict, Tuple, Union

ENTETE_MTS: str = "Fichier de matériaux de surfaces"
ENTETE_STR_V100: str = "Fichier de structures de chaussées pour Struct-urb"
ENTETE_STR_V103: str = "Fichier de structures de chaussées pour Struct-urb version >= 1.03"
ENTETE_STR_V200: str = "Fichier de structures de chaussées pour Struct-urb version >= 2.0.0"
FIN_COMMENT: str = "###Fin commentaire###"

GRILLES_PF: Tuple[str, ...] = (
    "PF1_Q1",
    "PF1_Q2",
    "PF2_Q1",
    "PF2_Q2",
    "PF2+_Q1",
    "PF2+_Q2",
    "PF3_Q1",
    "PF3_Q2",
)


@dataclass(frozen=True)
class MateriauSimple:
    """Matériau de surface simple (``MatSimple.cls``)."""

    nom: str
    abrege: str
    norme: str
    qualite_gel: str
    a_gel: float
    b_gel: float
    commentaire: str


@dataclass(frozen=True)
class MateriauMecanique:
    """Matériau avec caractéristiques mécaniques (``Matériau.cls`` : composant surface ou base/fondation)."""

    nom: str
    abrege: str
    norme: str
    qualite_gel: str
    a_gel: float
    b_gel: float
    young: float
    poisson: float
    epsilon: float
    sigma: float
    commentaire: str


@dataclass(frozen=True)
class CompositionSurface:
    """Ligne de composition d'un matériau de surface composé (épaisseurs en cm)."""

    epaisseur_preconisee: int
    epaisseur_1: int
    materiau_1: str
    epaisseur_2: int
    materiau_2: str
    epaisseur_3: int
    materiau_3: str


@dataclass(frozen=True)
class MateriauCompose:
    """Matériau de surface composé (``MatComposé.cls``)."""

    nom: str
    abrege: str
    a_gel: float
    b_gel: float
    compositions: Tuple[CompositionSurface, ...]


@dataclass(frozen=True)
class CatalogueMatSurface:
    """Contenu complet d'un fichier ``*.mts``."""

    simples: Tuple[MateriauSimple, ...]
    mecaniques: Tuple[MateriauMecanique, ...]
    composes: Tuple[MateriauCompose, ...]
    par_abrege: Dict[str, Union[MateriauSimple, MateriauMecanique, MateriauCompose]]


@dataclass(frozen=True)
class LigneEpaisseur:
    """Une ligne de dimensionnement pour une plate-forme et une qualité donnée."""

    epaisseur_surface: int
    epaisseur_base_1: int
    epaisseur_base_2: int
    epaisseur_fondation_1: int
    epaisseur_fondation_2: int
    qm: float
    min_technique: str
    max_pratique: str


@dataclass(frozen=True)
class StructureChaussee:
    """Structure de chaussée du catalogue (``Structure.cls``)."""

    num_index: int
    abrege: str
    couche_surface: str
    couche_base: str
    couche_fondation: str
    couche_surf_sans_ep: int
    saisie_complete: bool
    util_v_des: int
    util_v_dis: int
    util_v_pl: int
    util_v_bus: int
    util_v_parking: int
    util_g_dis: int
    util_g_pl: int
    type_chaussee: int
    taux_risque: int
    type_cam: int
    type_structure: int
    nb_essieux_min: int
    nb_essieux_max: int
    commentaire: str
    grilles_pf: Dict[str, Tuple[LigneEpaisseur, ...]]


@dataclass(frozen=True)
class CatalogueStructures:
    """Contenu complet d'un fichier ``*.str`` (v2.0.0+)."""

    structures: Tuple[StructureChaussee, ...]
    materiaux_bf: Tuple[MateriauMecanique, ...]
    structures_par_abrege: Dict[str, StructureChaussee]
    materiaux_par_abrege: Dict[str, MateriauMecanique]


def _lire_string(f: BinaryIO) -> Optional[str]:
    """Lit une chaîne VB6 écrite par ``EcrireString`` (``Long`` 4 octets + octets cp1252).

    Retourne ``None`` en fin de fichier (EOF).
    Réf. VB6 : ``Utilitaires.bas :: LireString`` (lignes 110-123).
    """
    brut = f.read(4)
    if not brut:
        return None
    if len(brut) < 4:
        raise EOFError("Fin de fichier inattendue lors de la lecture de la longueur d'une chaîne.")
    (longueur,) = struct.unpack("<i", brut)
    if longueur < 0:
        raise ValueError(f"Longueur de chaîne binaire invalide : {longueur}")
    if longueur == 0:
        return ""
    data = f.read(longueur)
    if len(data) < longueur:
        raise EOFError(f"Fin de fichier inattendue ({len(data)}/{longueur} octets lus).")
    return data.decode("cp1252")


def _lire_exact(f: BinaryIO, fmt: str) -> Tuple:
    size = struct.calcsize(fmt)
    data = f.read(size)
    if len(data) < size:
        raise EOFError(f"Fin de fichier inattendue ({len(data)}/{size} octets lus).")
    return struct.unpack(fmt, data)


def _lire_commentaire(f: BinaryIO) -> str:
    """Lit un commentaire RTF multi-morceaux terminé par ``FIN_COMMENT``."""
    morceau = _lire_string(f)
    if morceau is None:
        raise EOFError("Fin de fichier inattendue dans un commentaire.")
    parties = [morceau]
    while True:
        suite = _lire_string(f)
        if suite is None:
            raise EOFError("Fin de fichier inattendue avant FIN_COMMENT.")
        if suite == FIN_COMMENT:
            break
        parties.append(suite)
    return "".join(parties)


def ouvrir_fichier_mat_surface(chemin: str | Path) -> CatalogueMatSurface:
    """Charge un fichier de matériaux de surface ``*.mts`` (ex. ``Certu.mts``).

    Réf. VB6 : ``ModuleMain.bas :: OuvrirFichierMatSurface`` (lignes 1846-1985).
    """
    path = Path(chemin)
    if not path.is_file():
        raise FileNotFoundError(f"Fichier matériaux de surface introuvable : {path}")

    simples: list[MateriauSimple] = []
    mecaniques: list[MateriauMecanique] = []
    composes: list[MateriauCompose] = []
    par_abrege: Dict[str, Union[MateriauSimple, MateriauMecanique, MateriauCompose]] = {}

    with path.open("rb") as f:
        entete = _lire_string(f)
        if entete != ENTETE_MTS:
            raise ValueError(f"En-tête .mts invalide : {entete!r} (attendu : {ENTETE_MTS!r}).")

        while True:
            type_mat = _lire_string(f)
            if type_mat is None:
                break
            if type_mat in ("MatériauSimple", "Matériau"):
                nom = _lire_string(f) or ""
                abrege = _lire_string(f) or ""
                norme = _lire_string(f) or ""
                qual = _lire_string(f) or ""
                a_gel, b_gel = _lire_exact(f, "<ff")
                if type_mat == "Matériau":
                    young, poisson, epsilon, sigma = _lire_exact(f, "<ffff")
                commentaire = _lire_commentaire(f)
                if type_mat == "MatériauSimple":
                    mat: Union[MateriauSimple, MateriauMecanique] = MateriauSimple(
                        nom=nom,
                        abrege=abrege,
                        norme=norme,
                        qualite_gel=qual,
                        a_gel=a_gel,
                        b_gel=b_gel,
                        commentaire=commentaire,
                    )
                    simples.append(mat)
                else:
                    mat = MateriauMecanique(
                        nom=nom,
                        abrege=abrege,
                        norme=norme,
                        qualite_gel=qual,
                        a_gel=a_gel,
                        b_gel=b_gel,
                        young=young,
                        poisson=poisson,
                        epsilon=epsilon,
                        sigma=sigma,
                        commentaire=commentaire,
                    )
                    mecaniques.append(mat)
                par_abrege[abrege] = mat
            elif type_mat == "MatériauComposé":
                nom = _lire_string(f) or ""
                abrege = _lire_string(f) or ""
                (nb_comp,) = _lire_exact(f, "<h")
                a_gel, b_gel = _lire_exact(f, "<ff")
                comps: list[CompositionSurface] = []
                for _ in range(nb_comp):
                    ep0, ep1 = _lire_exact(f, "<hh")
                    ab1 = _lire_string(f) or ""
                    (ep2,) = _lire_exact(f, "<h")
                    ab2 = _lire_string(f) or ""
                    (ep3,) = _lire_exact(f, "<h")
                    ab3 = _lire_string(f) or ""
                    comps.append(
                        CompositionSurface(
                            epaisseur_preconisee=ep0,
                            epaisseur_1=ep1,
                            materiau_1=ab1,
                            epaisseur_2=ep2,
                            materiau_2=ab2,
                            epaisseur_3=ep3,
                            materiau_3=ab3,
                        )
                    )
                mc = MateriauCompose(
                    nom=nom,
                    abrege=abrege,
                    a_gel=a_gel,
                    b_gel=b_gel,
                    compositions=tuple(comps),
                )
                composes.append(mc)
                par_abrege[abrege] = mc
            else:
                raise ValueError(f"Type de matériau de surface inconnu dans {path.name} : {type_mat!r}")

    return CatalogueMatSurface(
        simples=tuple(simples),
        mecaniques=tuple(mecaniques),
        composes=tuple(composes),
        par_abrege=par_abrege,
    )


def ouvrir_fichier_structures(chemin: str | Path) -> CatalogueStructures:
    """Charge un fichier catalogue de structures ``*.str`` (v2.0.0+, ex. ``Certu.str``).

    Réf. VB6 : ``ModuleMain.bas :: OuvrirFichierStructures`` (lignes 362-597).
    """
    path = Path(chemin)
    if not path.is_file():
        raise FileNotFoundError(f"Fichier structures introuvable : {path}")

    structures: list[StructureChaussee] = []
    materiaux_bf: list[MateriauMecanique] = []
    structures_par_abrege: Dict[str, StructureChaussee] = {}
    materiaux_par_abrege: Dict[str, MateriauMecanique] = {}

    with path.open("rb") as f:
        entete = _lire_string(f)
        if entete in (ENTETE_STR_V100, ENTETE_STR_V103):
            raise ValueError(f"Format .str v1.x non compatible : {entete!r}")
        if entete != ENTETE_STR_V200:
            raise ValueError(f"En-tête .str invalide : {entete!r} (attendu : {ENTETE_STR_V200!r}).")

        while True:
            type_elem = _lire_string(f)
            if type_elem is None:
                break
            if type_elem == "Structure":
                (num_index,) = _lire_exact(f, "<h")
                abrege = _lire_string(f) or ""
                couche_surface = _lire_string(f) or ""
                couche_base = _lire_string(f) or ""
                couche_fondation = _lire_string(f) or ""
                (
                    couche_surf_sans_ep,
                    saisie_complete_raw,
                    util_v_des,
                    util_v_dis,
                    util_v_pl,
                    util_v_bus,
                    util_v_parking,
                    util_g_dis,
                    util_g_pl,
                    type_chaussee,
                    taux_risque,
                    type_cam,
                    type_structure,
                    nb_essieux_min,
                    nb_essieux_max,
                ) = _lire_exact(f, "<hhhhhhhhhBhhBii")
                commentaire = _lire_commentaire(f)

                grilles_pf: Dict[str, Tuple[LigneEpaisseur, ...]] = {}
                for cle_pf in GRILLES_PF:
                    (nb_tot,) = _lire_exact(f, "<i")
                    nb_lignes = nb_tot // 8
                    lignes: list[LigneEpaisseur] = []
                    for _ in range(nb_lignes):
                        ep_s, ep_b1, ep_b2, ep_f1, ep_f2, qm = _lire_exact(f, "<hhhhhf")
                        min_tec = _lire_string(f) or ""
                        max_prat = _lire_string(f) or ""
                        lignes.append(
                            LigneEpaisseur(
                                epaisseur_surface=ep_s,
                                epaisseur_base_1=ep_b1,
                                epaisseur_base_2=ep_b2,
                                epaisseur_fondation_1=ep_f1,
                                epaisseur_fondation_2=ep_f2,
                                qm=qm,
                                min_technique=min_tec,
                                max_pratique=max_prat,
                            )
                        )
                    grilles_pf[cle_pf] = tuple(lignes)

                st = StructureChaussee(
                    num_index=num_index,
                    abrege=abrege,
                    couche_surface=couche_surface,
                    couche_base=couche_base,
                    couche_fondation=couche_fondation,
                    couche_surf_sans_ep=couche_surf_sans_ep,
                    saisie_complete=bool(saisie_complete_raw),
                    util_v_des=util_v_des,
                    util_v_dis=util_v_dis,
                    util_v_pl=util_v_pl,
                    util_v_bus=util_v_bus,
                    util_v_parking=util_v_parking,
                    util_g_dis=util_g_dis,
                    util_g_pl=util_g_pl,
                    type_chaussee=type_chaussee,
                    taux_risque=taux_risque,
                    type_cam=type_cam,
                    type_structure=type_structure,
                    nb_essieux_min=nb_essieux_min,
                    nb_essieux_max=nb_essieux_max,
                    commentaire=commentaire,
                    grilles_pf=grilles_pf,
                )
                structures.append(st)
                structures_par_abrege[abrege] = st

            elif type_elem == "MatériauFondBase":
                nom = _lire_string(f) or ""
                abrege = _lire_string(f) or ""
                norme = _lire_string(f) or ""
                qual = _lire_string(f) or ""
                a_gel, b_gel, young, poisson, epsilon, sigma = _lire_exact(f, "<ffffff")
                commentaire = _lire_commentaire(f)
                mat_bf = MateriauMecanique(
                    nom=nom,
                    abrege=abrege,
                    norme=norme,
                    qualite_gel=qual,
                    a_gel=a_gel,
                    b_gel=b_gel,
                    young=young,
                    poisson=poisson,
                    epsilon=epsilon,
                    sigma=sigma,
                    commentaire=commentaire,
                )
                materiaux_bf.append(mat_bf)
                materiaux_par_abrege[abrege] = mat_bf
            else:
                raise ValueError(f"Élément inconnu dans {path.name} : {type_elem!r}")

    return CatalogueStructures(
        structures=tuple(structures),
        materiaux_bf=tuple(materiaux_bf),
        structures_par_abrege=structures_par_abrege,
        materiaux_par_abrege=materiaux_par_abrege,
    )
