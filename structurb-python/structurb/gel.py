"""Calculs du lot Gel de Struct-Urb (portage fidèle du code VB6 compilé).

Références VB6 d'origine (CEREMA/territoires-ville.StructUrb) :
- ``ModuleMain.bas`` : ``HorsGel`` (ligne 167), ``CalculerIndiceGelRef`` (lignes 2309-2345),
  ``RemplirLesStationsMétéo`` (lignes 2415-2506), ``CalculerIndiceGelAdm`` (lignes 2537-2642),
  ``CalculerQng`` (lignes 2912-2916), ``CalculerQg`` (lignes 2918-2933) ;
- ``ModuleFichier.bas`` : ``DonnerTypeGelSol`` (lignes 477-480), ``DonnerCoefA`` (lignes 482-490) ;
- ``frmDocument.frm`` : ``monIndiceGelRefQ1/Q2`` (Integer) et ``monIndiceGelAdmQ1/Q2`` (Long) (lignes 2143-2146) ;
- ``frmImprimer.frm`` : comparaison ``monIndiceGelRef <= monIndiceGelAdm`` (lignes 675, 710).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple

from .trafic import _vb_csng, vb_clng

# Valeur sentinelle d'indice de gel admissible infini (ModuleMain.bas, ligne 167)
HORS_GEL: int = 1_000_000_000

# Hivers de référence gérés par Struct-Urb (OptionHE, OptionHRNE, OptionHC)
HIVERS_REFERENCE: Tuple[str, ...] = ("HE", "HRNE", "HC")

# Coefficients de taille d'agglomération (ModuleMain.bas :: CalculerIndiceGelRef, lignes 2331-2337)
# Clés : "petite" (index 0), "moyenne" (index 1), "grande" (index 2)
COEFFICIENTS_AGGLO: dict[str, float] = {
    "petite": 1.0,
    "moyenne": 0.9,
    "grande": 0.8,
}

# Coefficients A de la couche de forme non gélive (ModuleFichier.bas :: DonnerCoefA, lignes 482-490)
COEF_A_NON_TRAITEE: float = 0.12
COEF_A_TRAITEE: float = 0.14


@dataclass(frozen=True)
class StationMeteo:
    """Station météorologique de référence pour le calcul au gel."""

    nom: str
    departement: str
    altitude: int
    hre: int
    hrne: int
    hc: int


# Table des 84 stations météo d'origine (ModuleMain.bas :: RemplirLesStationsMétéo, lignes 2422-2505)
STATIONS_METEO: Tuple[StationMeteo, ...] = (
    StationMeteo("Ambérieu", "01", 253, 270, 175, 65),
    StationMeteo("Saint Quentin", "02", 98, 225, 110, 45),
    StationMeteo("Vichy", "03", 249, 250, 115, 45),
    StationMeteo("St-Auban", "04", 459, 80, 35, 10),
    StationMeteo("Embrun", "05", 871, 165, 95, 60),
    StationMeteo("Nice", "06", 5, 0, 0, 0),
    StationMeteo("St-Girons", "09", 411, 120, 35, 15),
    StationMeteo("Romilly sur Seine", "10", 77, 210, 110, 35),
    StationMeteo("Carcassone", "11", 126, 85, 35, 10),
    StationMeteo("Millau", "12", 715, 140, 65, 40),
    StationMeteo("Marignane", "13", 4, 70, 15, 0),
    StationMeteo("Caen", "14", 64, 115, 60, 25),
    StationMeteo("Cognac", "16", 30, 100, 35, 15),
    StationMeteo("la Rochelle", "17", 4, 75, 30, 10),
    StationMeteo("Bourges", "18", 161, 160, 70, 30),
    StationMeteo("Ajaccio", "20", 4, 0, 0, 0),
    StationMeteo("Dijon", "21", 222, 200, 130, 65),
    StationMeteo("Rostrenen", "22", 262, 85, 50, 10),
    StationMeteo("Besançon", "25", 307, 220, 120, 70),
    StationMeteo("Lus-la-Croix-Haute", "26", 1059, 420, 275, 160),
    StationMeteo("Montélimar", "26", 73, 105, 40, 10),
    StationMeteo("Evreux", "27", 133, 195, 115, 60),
    StationMeteo("Chartres", "28", 155, 190, 100, 35),
    StationMeteo("Brest", "29", 96, 20, 10, 0),
    StationMeteo("Nîmes", "30", 59, 60, 20, 0),
    StationMeteo("Toulouse", "31", 148, 115, 40, 10),
    StationMeteo("Bordeaux", "33", 46, 95, 40, 10),
    StationMeteo("Montpellier", "34", 5, 55, 35, 0),
    StationMeteo("Dinard", "35", 58, 65, 25, 5),
    StationMeteo("Rennes", "35", 36, 80, 35, 10),
    StationMeteo("Chateauroux", "36", 156, 155, 75, 30),
    StationMeteo("Tours", "37", 108, 120, 75, 35),
    StationMeteo("Grenoble", "38", 384, 170, 145, 60),
    StationMeteo("Mont de Marsan", "40", 59, 100, 40, 10),
    StationMeteo("Romorantin", "41", 84, 135, 100, 30),
    StationMeteo("St-Etienne", "42", 400, 220, 110, 60),
    StationMeteo("le Puy", "43", 714, 240, 130, 65),
    StationMeteo("Nantes", "44", 26, 75, 55, 10),
    StationMeteo("Orléans", "45", 125, 170, 85, 45),
    StationMeteo("Gourdon", "46", 259, 120, 45, 20),
    StationMeteo("Agen", "47", 59, 110, 40, 15),
    StationMeteo("Angers", "49", 57, 100, 70, 15),
    StationMeteo("Cap de la Hague", "50", 3, 15, 5, 0),
    StationMeteo("Reims", "51", 94, 235, 105, 80),
    StationMeteo("Langres", "52", 464, 325, 170, 110),
    StationMeteo("St-Dizier", "52", 139, 235, 100, 65),
    StationMeteo("Nancy", "54", 212, 320, 155, 90),
    StationMeteo("Bar le Duc", "55", 279, 340, 290, 130),
    StationMeteo("Lorient", "56", 43, 40, 25, 10),
    StationMeteo("Metz", "57", 190, 290, 135, 75),
    StationMeteo("Château-Chinon", "58", 598, 225, 115, 80),
    StationMeteo("Nevers", "58", 175, 190, 110, 60),
    StationMeteo("Dunkerque", "59", 11, 165, 65, 20),
    StationMeteo("Lille", "59", 47, 250, 90, 55),
    StationMeteo("Beauvais", "60", 106, 215, 95, 40),
    StationMeteo("Alençon", "61", 144, 165, 70, 35),
    StationMeteo("Boulogne sur Mer", "62", 73, 165, 70, 30),
    StationMeteo("Clermont-Ferrand", "63", 320, 225, 115, 45),
    StationMeteo("Biarritz", "64", 69, 40, 10, 0),
    StationMeteo("Pau", "64", 183, 80, 30, 10),
    StationMeteo("Tarbes", "65", 360, 95, 35, 10),
    StationMeteo("Perpignan", "66", 42, 25, 0, 0),
    StationMeteo("Strasbourg", "67", 150, 410, 165, 100),
    StationMeteo("Mulhouse-Bâle", "68", 267, 415, 155, 105),
    StationMeteo("Lyon", "69", 200, 220, 110, 45),
    StationMeteo("Tarare", "69", 831, 275, 155, 95),
    StationMeteo("Luxeuil", "70", 272, 335, 165, 110),
    StationMeteo("Mâcon", "71", 216, 200, 115, 60),
    StationMeteo("Mont-St-Vincent", "71", 602, 270, 150, 95),
    StationMeteo("le Mans", "72", 51, 120, 70, 25),
    StationMeteo("Bourg-St-Maurice", "73", 865, 220, 190, 110),
    StationMeteo("Challes les Eaux", "73", 291, 225, 150, 60),
    StationMeteo("Cap de la Hève", "76", 100, 95, 60, 20),
    StationMeteo("Rouen", "76", 155, 130, 90, 30),
    StationMeteo("Melun", "77", 91, 185, 90, 50),
    StationMeteo("Abbeville", "80", 70, 165, 90, 50),
    StationMeteo("Saint-Raphaël", "83", 2, 25, 0, 0),
    StationMeteo("Toulon", "83", 24, 15, 0, 0),
    StationMeteo("Orange", "84", 83, 80, 45, 10),
    StationMeteo("Poitiers", "86", 117, 130, 65, 25),
    StationMeteo("Limoges", "87", 403, 160, 80, 30),
    StationMeteo("Auxerre", "89", 207, 200, 95, 55),
    StationMeteo("Belfort", "90", 422, 370, 175, 115),
    StationMeteo("Paris le Bourget", "93", 59, 160, 85, 35),
)

_STATIONS_PAR_NOM: dict[str, StationMeteo] = {s.nom.lower(): s for s in STATIONS_METEO}


def obtenir_station(nom: str) -> StationMeteo:
    """Retourne la station météo par son nom (insensible à la casse).

    Réf. VB6 : ``ModuleMain.bas :: RemplirLesStationsMétéo`` (lignes 2415-2506).
    """
    if not isinstance(nom, str) or not nom.strip():
        raise ValueError("Le nom de station doit être une chaîne non vide.")
    cle = nom.strip().lower()
    if cle not in _STATIONS_PAR_NOM:
        raise KeyError(f"Station météo inconnue : {nom!r}")
    return _STATIONS_PAR_NOM[cle]


def coef_couche_forme_non_gelive(traitee: bool = False) -> float:
    """Retourne le coefficient ``A`` (en ``Single``) de la couche de forme non gélive.

    - ``traitee=False`` (``OptionANT``) -> ``0.12``
    - ``traitee=True``  (``OptionAT``)  -> ``0.14``

    Réf. VB6 : ``ModuleFichier.bas :: DonnerCoefA`` (lignes 482-490).
    """
    return _vb_csng(COEF_A_TRAITEE if traitee else COEF_A_NON_TRAITEE)


def indice_gel_reference(
    station: StationMeteo | str,
    hiver: str = "HRNE",
    taille_agglo: str | int = "petite",
    indice_personnel: Optional[int] = None,
) -> int:
    """Calcule l'indice de gel de référence corrigé (en °C·j).

    Réf. VB6 : ``ModuleMain.bas :: CalculerIndiceGelRef`` (lignes 2309-2345).
    Note : dans le code VB6 d'origine, la correction d'altitude est commentée
    (ligne 2342) ; seul le coefficient d'agglomération (``1.0``, ``0.9``, ``0.8``
    en ``Single``) est appliqué avant arrondi ``CInt`` (bancaire).
    La formule commentée (``1 - Abs(HStation - HAgglo) / HStation``) n'est pas portée :
    elle fait baisser l'indice quand l'altitude augmente et le rend négatif dès que
    l'agglomération est à plus de deux fois l'altitude de la station.

    ``indice_personnel`` : indice de gel issu de relevés locaux (case « Indice de gel
    personnel », ``frmDocument.frm :: CheckIndGelPerso_Click`` et
    ``TextIndGelPerso_LostFocus``). Il remplace l'indice de la station **sans**
    coefficient d'agglomération. C'est le moyen prévu par Struct-Urb pour tenir compte
    d'un site dont l'altitude ou le climat diffère de la station de référence.
    """
    if indice_personnel is not None:
        if isinstance(indice_personnel, bool) or not isinstance(indice_personnel, int):
            raise ValueError(f"L'indice de gel personnel doit être un entier (reçu : {indice_personnel!r}).")
        if indice_personnel < 0:
            raise ValueError(f"L'indice de gel personnel doit être >= 0 (reçu : {indice_personnel}).")
        return indice_personnel

    st = obtenir_station(station) if isinstance(station, str) else station
    h_key = hiver.strip().upper()
    if h_key == "HE":
        ind_brut = st.hre
    elif h_key == "HRNE":
        ind_brut = st.hrne
    elif h_key == "HC":
        ind_brut = st.hc
    else:
        raise ValueError(f"Hiver de référence invalide : {hiver!r} (attendu : {HIVERS_REFERENCE}).")

    if isinstance(taille_agglo, int) and not isinstance(taille_agglo, bool):
        noms = ("petite", "moyenne", "grande")
        if not 0 <= taille_agglo <= 2:
            raise ValueError(f"Index de taille d'agglomération invalide : {taille_agglo} (0, 1 ou 2).")
        agglo_key = noms[taille_agglo]
    elif isinstance(taille_agglo, str):
        agglo_key = taille_agglo.strip().lower()
        if agglo_key not in COEFFICIENTS_AGGLO:
            raise ValueError(
                f"Taille d'agglomération invalide : {taille_agglo!r} "
                f"(attendu : {tuple(COEFFICIENTS_AGGLO)})."
            )
    else:
        raise ValueError(f"Type invalide pour taille_agglo : {type(taille_agglo).__name__}")

    coef = _vb_csng(COEFFICIENTS_AGGLO[agglo_key])
    # En VB6 : Integer * Single -> Single, puis CInt (arrondi bancaire)
    return vb_clng(_vb_csng(ind_brut * coef))


def quantite_gel_non_gelive(epaisseur_cm: float, traitee: bool = False) -> float:
    """Calcule ``Qng`` de la couche de forme non gélive (en ``Single``).

    Formule VB6 : ``DonnerCoefA * (Hn * Hn) / (Hn + 10)``.
    ``unHn`` est un ``Variant`` en VB6 : le calcul s'effectue en ``Double``,
    avec une seule conversion en ``Single`` au retour de la fonction.
    Réf. VB6 : ``ModuleMain.bas :: CalculerQng`` (lignes 2912-2916).
    """
    hn = float(epaisseur_cm)
    if hn < 0.0:
        raise ValueError(f"L'épaisseur non gélive doit être >= 0 cm (reçu : {epaisseur_cm}).")
    a = coef_couche_forme_non_gelive(traitee)
    return _vb_csng(a * (hn * hn) / (hn + 10.0))


def quantite_gel_sol_support(pente_pourcent: Optional[float]) -> float:
    """Calcule ``Qg`` du sol support en fonction de sa pente de sensibilité au gel.

    ``uneP`` est un ``Variant`` en VB6 : les comparaisons et la division
    s'effectuent en ``Double``, avec une seule conversion en ``Single`` au retour :
    - ``pente_pourcent is None`` ou infinie (sol non gélif) : ``uneP = 2 -> 0.0``
    - ``pente <= 0.25`` : ``4.0``
    - ``0.25 < pente <= 1.0`` : ``1 / pente`` (en ``Single``)
    - ``pente > 1.0`` : ``0.0``

    Réf. VB6 : ``ModuleMain.bas :: CalculerQg`` (lignes 2918-2933).
    """
    if pente_pourcent is None or math.isinf(pente_pourcent):
        return 0.0
    p = float(pente_pourcent)
    if p < 0.0:
        raise ValueError(f"La pente doit être >= 0 (reçu : {pente_pourcent}).")
    if p <= 0.25:
        return 4.0
    if p <= 1.0:
        return _vb_csng(1.0 / p)
    return 0.0


def indice_gel_admissible(
    epaisseurs_cm: Tuple[float, float, float, float, float, float],
    agel: Tuple[float, float, float],
    bgel: Tuple[float, float, float],
    qm: float,
    epaisseur_non_gelive_cm: float = 0.0,
    couche_forme_traitee: bool = False,
    pente_sol_pourcent: Optional[float] = None,
) -> int:
    """Calcule l'indice de gel admissible (en °C·j) pour une qualité de chaussée.

    Paramètres :
    - ``epaisseurs_cm`` : ``(e_cs1, e_cs2, e_cb1, e_cb2, e_cf1, e_cf2)`` en cm.
      Note : dans le VB6 d'origine, ``monTabEp`` contient des ``CInt`` (épaisseurs entières).
    - ``agel`` : ``(a_cs, a_cb, a_cf)`` coefficients ``Agel`` des couches.
    - ``bgel`` : ``(b_cs, b_cb, b_cf)`` coefficients ``Bgel`` des couches.
    - ``qm`` : quantité de chaleur mécanique ``monQmQ1`` ou ``monQmQ2``.
    - ``epaisseur_non_gelive_cm`` : épaisseur ``Hn`` de la couche de forme non gélive (cm).
    - ``couche_forme_traitee`` : ``False`` (ANT, 0.12) ou ``True`` (AT, 0.14).
    - ``pente_sol_pourcent`` : pente de gélivité du sol support ; si ``<= 0.05`` (en ``Double``,
      et finie), retourne ``HORS_GEL`` (1 000 000 000). Si ``None``, retourne ``0`` (inconnu).
      Si ``math.inf`` (``MsgInfinie``, très gélif), le calcul utilise ``Qg = 0``.

    Réf. VB6 : ``ModuleMain.bas :: CalculerIndiceGelAdm`` (lignes 2537-2642).
    """
    if pente_sol_pourcent is None:
        return 0
    if not math.isinf(pente_sol_pourcent) and float(pente_sol_pourcent) <= 0.05:
        return HORS_GEL

    e1, e2, e3, e4, e5, e6 = (_vb_csng(x) for x in epaisseurs_cm)
    acs, acb, acf = (_vb_csng(x) for x in agel)
    bcs, bcb, bcf = (_vb_csng(x) for x in bgel)

    ecs = _vb_csng(e1 + e2)
    ecb = _vb_csng(e3 + e4)
    ecf = _vb_csng(e5 + e6)

    ah = _vb_csng(1.0 + _vb_csng(_vb_csng(acs * ecs) + _vb_csng(acb * ecb) + _vb_csng(acf * ecf)))
    bh = _vb_csng(_vb_csng(bcs * ecs) + _vb_csng(bcb * ecb) + _vb_csng(bcf * ecf))

    qng = quantite_gel_non_gelive(epaisseur_non_gelive_cm, couche_forme_traitee)
    qg = quantite_gel_sol_support(pente_sol_pourcent)
    q_tot = _vb_csng(_vb_csng(qm) + qng + qg)

    terme = _vb_csng(_vb_csng(ah * q_tot) + bh)
    i_adm = 10.0 + _vb_csng(terme * terme) / 0.6
    return vb_clng(i_adm)


def chaussee_verifiee_au_gel(indice_gel_ref: int, indice_gel_adm: int) -> bool:
    """Retourne ``True`` si la chaussée résiste au gel (``I_ref <= I_adm``).

    Écart assumé par rapport au VB6 (``frmImprimer.frm``, lignes 675 et 710) :
    en VB6, seule la condition ``monIndiceGelRef > monIndiceGelAdm`` entraîne
    l'état non protégé (sans garde pour ``I_ref = -1`` inconnu ni ``I_adm = 0``).
    Ici, ``I_ref < 0`` ou ``I_adm <= 0`` retournent ``False`` par sécurité
    (décision de YannFR81 du 2026-11-17 : écart conservé).
    """
    if indice_gel_ref < 0 or indice_gel_adm <= 0:
        return False
    return indice_gel_ref <= indice_gel_adm
