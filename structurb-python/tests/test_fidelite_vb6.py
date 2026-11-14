"""Tests de fidélité au VB6 compilé de Struct-Urb (décision de YannFR81 : portage identique).

Écrits par Claude AVANT la correction. Chaque cas ci-dessous donne un résultat DIFFÉRENT
selon qu'on calcule en double précision (float64) ou comme le VB6 d'origine : ils servent
à vérifier que le portage reproduit bien Struct-Urb, pas la formule mathématique.

Modèle de calcul VB6 retenu (vérifié dans STRUCURB.VBP : CompilationType=0 → code natif,
UnroundedFP=0 → chaque résultat intermédiaire est arrondi à son type déclaré) :

- ``uneCA = DonnerCroissAn / 100`` est un ``Single`` (float32).
- ``uneCA * uneDS`` (Single × Byte) → Single ; ``* (uneDS - 1)`` (× Integer) → Single ;
  ``/ 2`` → Single ; ``uneDS + …`` → Single. Le facteur de durée est donc un float32,
  arrondi à chaque étape.
- ``365# * unTini`` → Double ; ``× facteur Single`` → Double ; puis ``CLng`` (arrondi au pair).
- Trafic initial : ``CLng(unTCum / 365# / facteur_Single)`` (divisions en Double).
- NE : ``CLng(CLng(TCum) * CSng(CAM))`` : le CAM est converti en Single (0,1 → 0,10000000149),
  puis ``Long × Single`` → **Double**, puis ``CLng``.
"""

import pytest

from structurb.trafic import ne_equivalent, trafic_cumule, trafic_initial


# (t_ini, croissance %, durée) → valeur VB6 ; entre parenthèses : valeur float64 (fausse)
@pytest.mark.parametrize(
    "t_ini, croissance_pct, duree, attendu",
    [
        (1, 2, 11, 4_417),    # exact 4 416,5 ; float64 4 416 ; VB6 4 416,50…→ 4 417
        (1, 3, 5, 1_935),     # float64 1 934
        (1, 2, 46, 24_345),   # float64 24 346
        (1, 1, 45, 20_039),   # float64 20 038
        (1, 3, 36, 20_038),   # float64 20 039
        (1, 1, 21, 8_432),    # cas cité par Gemini : VB6 = float64 = 8 432 (non-régression)
    ],
)
def test_trafic_cumule_fidele_vb6(t_ini, croissance_pct, duree, attendu):
    assert trafic_cumule(t_ini, croissance_pct, duree) == attendu


@pytest.mark.parametrize(
    "t_cum, croissance_pct, duree, attendu",
    [
        (24_528, 4, 15, 3),   # float64 4
        (35_259, 4, 20, 4),   # float64 3
        (105_777, 4, 20, 11), # float64 10
    ],
)
def test_trafic_initial_fidele_vb6(t_cum, croissance_pct, duree, attendu):
    assert trafic_initial(t_cum, croissance_pct, duree) == attendu


@pytest.mark.parametrize(
    "t_cum, cam, attendu",
    [
        (5, 0.1, 1),     # CSng(0,1) = 0,10000000149 → 0,50000001 → 1 ; float64 0
        (25, 0.1, 3),    # 2,5000000373 → 3 ; float64 2
        (10, 0.35, 3),   # CSng(0,35) = 0,34999999 → 3,4999999 → 3 ; float64 4
        (15, 0.3, 5),    # 4,5000002 → 5 ; float64 4
        (10, 0.95, 9),   # 9,4999998 → 9 ; float64 10
    ],
)
def test_ne_equivalent_fidele_vb6(t_cum, cam, attendu):
    assert ne_equivalent(t_cum, cam) == attendu
