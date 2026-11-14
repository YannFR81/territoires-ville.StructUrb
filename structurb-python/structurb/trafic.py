"""Calculs du lot Trafic et CAM de Struct-Urb (portage fidèle du code VB6).

Références VB6 d'origine (CEREMA/territoires-ville.StructUrb) :
- ``ModuleMain.bas`` : ``CalculerTraficCum``, ``CalculerTraficIni``,
  ``DonnerCroissAn``, ``DonnerMinMaxTraficIni``, ``DonnerPrecMinMaxCAM`` ;
- ``ModuleSaisie.bas`` : ``VerifierMinMaxTraficIni``, ``VerifierMinMaxCAM`` ;
- ``frmDocument.frm`` : ``CalculerEtAfficherNE``.
"""

from __future__ import annotations

from typing import Optional, Tuple

# Types de voies gérés par Struct-Urb (ModuleMain.bas : constantes TypeVoie* / TypeGiratoire*)
TYPES_VOIE: Tuple[str, ...] = (
    "desserte",
    "distribution",
    "trafic_lourd",
    "bus",
    "parking",
    "giratoire_distribution",
    "giratoire_trafic_lourd",
)

# Bornes (min_tolere, min_valide, max_valide, max_tolere) en PL/j/sens/voie
# Réf. VB6 : ModuleMain.bas :: DonnerMinMaxTraficIni (lignes 2183-2210)
_BORNES_TRAFIC_INI: dict[str, Tuple[int, int, int, int]] = {
    "desserte": (0, 0, 25, 30),
    "distribution": (20, 25, 150, 170),
    "giratoire_distribution": (20, 25, 150, 170),
    "trafic_lourd": (120, 150, 750, 1000),
    "giratoire_trafic_lourd": (120, 150, 750, 1000),
    "bus": (0, 0, 750, 1000),
    "parking": (0, 0, 750, 1000),
}

# Valeurs (préconisé, min, max) de CAM par (type_voie, type_cam) avant majoration
# type_cam = 1 : souple ou bitumineuse ; type_cam = 2 : hydraulique ou béton
# Réf. VB6 : ModuleMain.bas :: DonnerPrecMinMaxCAM (lignes 2212-2296)
_TABLE_CAM: dict[Tuple[str, int], Tuple[float, float, float]] = {
    ("desserte", 1): (0.1, 0.05, 0.4),
    ("desserte", 2): (0.1, 0.05, 0.4),
    ("distribution", 1): (0.1, 0.05, 0.6),
    ("distribution", 2): (0.2, 0.1, 0.6),
    ("trafic_lourd", 1): (0.2, 0.1, 0.8),
    ("trafic_lourd", 2): (0.4, 0.2, 1.0),
    ("giratoire_distribution", 1): (0.5, 0.2, 1.0),
    ("giratoire_distribution", 2): (0.5, 0.2, 1.0),
    ("giratoire_trafic_lourd", 1): (1.0, 0.5, 1.5),
    ("giratoire_trafic_lourd", 2): (1.0, 0.5, 1.5),
    ("parking", 1): (0.1, 0.05, 0.4),
    ("parking", 2): (0.1, 0.05, 0.4),
    ("bus", 1): (0.5, 0.2, 1.0),
    ("bus", 2): (0.5, 0.2, 1.0),
}

# Limite supérieure de NE dans Struct-Urb (frmDocument.frm :: CalculerEtAfficherNE, ligne 3993)
NE_MAX_LIMITE: int = 10_000_000


def vb_clng(x: float | int) -> int:
    """Arrondit un nombre à l'entier pair le plus proche (comportement de ``CLng`` en VB6).

    Référence VB6 : fonction intrinsèque ``CLng`` (arrondi bancaire IEEE 754
    « round half to even » : ``CLng(2.5) == 2``, ``CLng(3.5) == 4``).
    """
    return int(round(x))


def _valider_croissance(croissance_pct: int) -> None:
    """Vérifie que le taux de croissance annuelle est un entier compris entre 0 et 5 %.

    Référence VB6 : ``ModuleMain.bas :: DonnerCroissAn`` (lignes 2170-2181),
    boutons radio ``OptionCA(0)`` à ``OptionCA(5)``.
    """
    if (
        isinstance(croissance_pct, bool)
        or not isinstance(croissance_pct, int)
        or not (0 <= croissance_pct <= 5)
    ):
        raise ValueError(
            f"La croissance annuelle doit être un entier entre 0 et 5 % (reçu : {croissance_pct!r})."
        )


def _valider_type_voie(type_voie: str) -> None:
    """Vérifie que l'identifiant du type de voie appartient à ``TYPES_VOIE``."""
    if type_voie not in _BORNES_TRAFIC_INI:
        raise ValueError(
            f"Type de voie inconnu : {type_voie!r}. Attendu parmi {TYPES_VOIE}."
        )


def trafic_cumule(t_ini: int, croissance_pct: int, duree: int) -> int:
    """Calcule le trafic cumulé poids lourds sur la durée de service (croissance linéaire).

    Formule VB6 :
        ``CLng(365# * unTini * (uneDS + (uneCA * uneDS * (uneDS - 1)) / 2))``
    où ``uneCA = croissance_pct / 100``.

    Référence VB6 : ``ModuleMain.bas :: CalculerTraficCum`` (lignes 2082-2097).
    """
    _valider_croissance(croissance_pct)
    if duree <= 0:
        raise ValueError(f"La durée de service doit être strictement positive (reçu : {duree!r}).")
    if t_ini < 0:
        raise ValueError(f"Le trafic initial doit être positif ou nul (reçu : {t_ini!r}).")
    une_ca = croissance_pct / 100.0
    return vb_clng(365.0 * t_ini * (duree + (une_ca * duree * (duree - 1)) / 2.0))


def trafic_initial(t_cum: int, croissance_pct: int, duree: int) -> int:
    """Calcule le trafic initial (PL/j/sens) à partir du trafic cumulé.

    Formule VB6 :
        ``CLng(unTCum / 365# / (uneDS + (uneCA * uneDS * (uneDS - 1)) / 2))``

    Référence VB6 : ``ModuleMain.bas :: CalculerTraficIni`` (lignes 2099-2168,
    en particulier ligne 2121).
    """
    _valider_croissance(croissance_pct)
    if duree <= 0:
        raise ValueError(f"La durée de service doit être strictement positive (reçu : {duree!r}).")
    if t_cum < 0:
        raise ValueError(f"Le trafic cumulé doit être positif ou nul (reçu : {t_cum!r}).")
    une_ca = croissance_pct / 100.0
    return vb_clng(t_cum / 365.0 / (duree + (une_ca * duree * (duree - 1)) / 2.0))


def bornes_trafic_initial(type_voie: str) -> Tuple[int, int, int, int]:
    """Retourne ``(min_tolere, min_valide, max_valide, max_tolere)`` du trafic initial.

    Référence VB6 : ``ModuleMain.bas :: DonnerMinMaxTraficIni`` (lignes 2183-2210).
    """
    _valider_type_voie(type_voie)
    return _BORNES_TRAFIC_INI[type_voie]


def statut_trafic_initial(t_ini: int, type_voie: str) -> str:
    """Détermine le statut du trafic initial par rapport au domaine de la voie.

    Retourne :
    - ``"valide"`` si ``min_valide <= t_ini <= max_valide`` ;
    - ``"tolere"`` si ``min_tolere <= t_ini < min_valide`` ou ``max_valide < t_ini <= max_tolere`` ;
    - ``"hors_domaine"`` si ``t_ini < min_tolere`` ou ``t_ini > max_tolere``.

    Référence VB6 : ``ModuleMain.bas :: CalculerTraficIni`` (lignes 2129-2164)
    et ``ModuleSaisie.bas :: VerifierMinMaxTraficIni`` (lignes 64-116).
    """
    min_tol, min_val, max_val, max_tol = bornes_trafic_initial(type_voie)
    if t_ini < min_tol or t_ini > max_tol:
        return "hors_domaine"
    if t_ini < min_val or t_ini > max_val:
        return "tolere"
    return "valide"


def etude_labo_conseillee(t_ini: int, type_voie: str) -> bool:
    """Indique si Struct-Urb conseille une étude en laboratoire pour ce trafic initial.

    Une étude en laboratoire est conseillée lorsque le trafic initial dépasse le maximum
    normal tout en restant dans la borne maximale tolérée (``max_valide < t_ini <= max_tolere``),
    uniquement pour les voies à fort trafic PL :
    - ``"trafic_lourd"`` (voie principale avec PL),
    - ``"bus"`` (voie réservée aux bus),
    - ``"giratoire_trafic_lourd"`` (giratoire sur voie principale PL).

    Référence VB6 : ``ModuleMain.bas :: CalculerTraficIni`` (lignes 2144-2153)
    et ``ModuleSaisie.bas :: VerifierMinMaxTraficIni`` (lignes 91-99).
    """
    _, _, max_val, max_tol = bornes_trafic_initial(type_voie)
    if not (max_val < t_ini <= max_tol):
        return False
    return type_voie in {"trafic_lourd", "bus", "giratoire_trafic_lourd"}


def ne_equivalent(t_cum: int, cam: float) -> int:
    """Calcule le nombre d'essieux équivalents ``NE = CLng(TCum * CAM)``.

    Référence VB6 : ``frmDocument.frm :: CalculerEtAfficherNE`` (ligne 3986 :
    ``unNEEquiv = CLng(CLng(TextTrafCUM.Text) * CSng(MaskCAM.Text))``).
    """
    return vb_clng(t_cum * cam)


def ne_hors_limite(ne: int) -> bool:
    """Indique si le nombre d'essieux équivalents dépasse la limite de 10 millions.

    Référence VB6 : ``frmDocument.frm :: CalculerEtAfficherNE`` (ligne 3993 :
    ``If monNEEquiv > 10000000 Then``).
    """
    return ne > NE_MAX_LIMITE


def cam_preconise(
    type_voie: str,
    type_cam: int,
    type_structure: Optional[str] = None,
    couche_base: str = "",
) -> Tuple[float, float, float]:
    """Retourne ``(cam_preconise, cam_min, cam_max)`` selon la voie et la structure.

    Paramètres :
    - ``type_voie`` : identifiant dans ``TYPES_VOIE`` ;
    - ``type_cam`` : ``1`` (souple ou bitumineuse) ou ``2`` (hydraulique ou béton) ;
    - ``type_structure`` : ``"souple"``, ``"bitumineuse"``, ``"paves_dalles"``, etc. ;
    - ``couche_base`` : matériau de la couche de base (comparé sans distinction de casse
      à ``"GNT"`` lorsque ``type_structure == "paves_dalles"``).

    Règle de majoration VB6 (lignes 2298-2305) :
    Pour une structure ``"souple"``, ou une structure ``"paves_dalles"`` avec couche de
    base ``"GNT"`` (``UCase(maCoucheBase) = "GNT"``), la valeur préconisée est multipliée
    par 2 (les bornes ``min`` et ``max`` restent inchangées).

    Référence VB6 : ``ModuleMain.bas :: DonnerPrecMinMaxCAM`` (lignes 2212-2306).
    """
    _valider_type_voie(type_voie)
    if type_cam not in (1, 2):
        raise ValueError(f"type_cam doit valoir 1 ou 2 (reçu : {type_cam!r}).")

    prec, mini, maxi = _TABLE_CAM[(type_voie, type_cam)]
    if type_structure == "souple":
        prec = prec * 2.0
    elif type_structure == "paves_dalles" and (couche_base or "").upper() == "GNT":
        prec = prec * 2.0
    return (prec, mini, maxi)
