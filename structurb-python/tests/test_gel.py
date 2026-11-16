"""Tests du lot Gel (structurb.gel) — référence VB6."""

import math
import pytest

from structurb.gel import (
    HORS_GEL,
    STATIONS_METEO,
    chaussee_verifiee_au_gel,
    coef_couche_forme_non_gelive,
    indice_gel_admissible,
    indice_gel_reference,
    obtenir_station,
    quantite_gel_non_gelive,
    quantite_gel_sol_support,
)


def test_stations_meteo_completude():
    assert len(STATIONS_METEO) == 84
    assert STATIONS_METEO[0].nom == "Ambérieu"
    assert STATIONS_METEO[0].departement == "01"
    assert STATIONS_METEO[-1].nom == "Paris le Bourget"
    assert STATIONS_METEO[-1].departement == "93"


def test_obtenir_station():
    st = obtenir_station("  toulouse ")
    assert st.departement == "31"
    assert st.altitude == 148
    assert (st.hre, st.hrne, st.hc) == (115, 40, 10)

    mm = obtenir_station("Mont de Marsan")
    assert mm.departement == "40"
    assert (mm.hre, mm.hrne, mm.hc) == (100, 40, 10)

    with pytest.raises(ValueError):
        obtenir_station("")
    with pytest.raises(KeyError):
        obtenir_station("StationInexistante")


def test_indice_gel_reference():
    # Strasbourg (HRE=410, HRNE=165, HC=100)
    assert indice_gel_reference("Strasbourg", "HE", "petite") == 410
    assert indice_gel_reference("Strasbourg", "HRNE", 0) == 165
    assert indice_gel_reference("Strasbourg", "HC", "grande") == 80

    # Fidelite Integer * Single -> Single -> CInt :
    # 55 * CSng(0.9) = 49.5 en Single -> CInt = 50
    assert indice_gel_reference("Montpellier", "HE", "moyenne") == 50
    # 175 * CSng(0.9) = 157.5 en Single -> CInt = 158
    assert indice_gel_reference("Ambérieu", "HRNE", "moyenne") == 158
    # Nice : 0 dans tous les cas
    assert indice_gel_reference("Nice", "HE", "petite") == 0

    with pytest.raises(ValueError):
        indice_gel_reference("Toulouse", "HIVER_INCONNU", "petite")
    with pytest.raises(ValueError):
        indice_gel_reference("Toulouse", "HE", 3)


def test_coef_a_et_qng():
    assert coef_couche_forme_non_gelive(False) == pytest.approx(0.12, abs=1e-6)
    assert coef_couche_forme_non_gelive(True) == pytest.approx(0.14, abs=1e-6)

    assert quantite_gel_non_gelive(0.0, False) == 0.0
    # 0.12 * 30^2 / 40 = 2.7
    assert quantite_gel_non_gelive(30.0, False) == pytest.approx(2.7, abs=1e-5)
    # 0.14 * 20^2 / 30 = 1.866666...
    assert quantite_gel_non_gelive(20.0, True) == pytest.approx(0.14 * 400.0 / 30.0, abs=1e-5)

    with pytest.raises(ValueError):
        quantite_gel_non_gelive(-5.0)


def test_quantite_gel_sol_support():
    assert quantite_gel_sol_support(None) == 0.0
    assert quantite_gel_sol_support(math.inf) == 0.0
    assert quantite_gel_sol_support(0.10) == 4.0
    assert quantite_gel_sol_support(0.25) == 4.0
    assert quantite_gel_sol_support(0.50) == pytest.approx(2.0, abs=1e-6)
    assert quantite_gel_sol_support(1.0) == pytest.approx(1.0, abs=1e-6)
    assert quantite_gel_sol_support(1.5) == 0.0

    with pytest.raises(ValueError):
        quantite_gel_sol_support(-0.1)


def test_indice_gel_admissible_cas_limites():
    assert indice_gel_admissible((6, 0, 15, 0, 0, 0), (0.01, 0.01, 0.0), (0.1, 0.1, 0.0), 3.0, pente_sol_pourcent=None) == 0
    assert indice_gel_admissible((6, 0, 15, 0, 0, 0), (0.01, 0.01, 0.0), (0.1, 0.1, 0.0), 3.0, pente_sol_pourcent=0.05) == HORS_GEL
    assert indice_gel_admissible((6, 0, 15, 0, 0, 0), (0.01, 0.01, 0.0), (0.1, 0.1, 0.0), 3.0, pente_sol_pourcent=0.02) == HORS_GEL


def test_indice_gel_admissible_calcul():
    # Exemple : CS=6cm (a=0.01, b=0.05), CB=20cm (a=0.02, b=0.10), CF=0cm
    # AH = 1 + 0.01*6 + 0.02*20 = 1.46
    # BH = 0.05*6 + 0.10*20 = 2.30
    # Qm = 3.0, Hn = 20cm non traitee -> Qng = 0.12*400/30 = 1.60
    # Pente = 0.5 -> Qg = 2.0
    # Q_tot = 3.0 + 1.6 + 2.0 = 6.6
    # terme = 1.46 * 6.6 + 2.30 = 11.936
    # I_adm = 10 + 11.936^2 / 0.6 = 247.446826... -> CLng = 247
    i_adm = indice_gel_admissible(
        epaisseurs_cm=(6, 0, 20, 0, 0, 0),
        agel=(0.01, 0.02, 0.0),
        bgel=(0.05, 0.10, 0.0),
        qm=3.0,
        epaisseur_non_gelive_cm=20.0,
        couche_forme_traitee=False,
        pente_sol_pourcent=0.5,
    )
    assert i_adm == 247

    # Sol tres gelif (pente = inf -> Qg = 0)
    # Q_tot = 3.0 + 1.6 + 0 = 4.6 -> terme = 1.46*4.6 + 2.30 = 9.016
    # I_adm = 10 + 9.016^2 / 0.6 = 145.4804... -> 145
    i_adm_inf = indice_gel_admissible(
        epaisseurs_cm=(6, 0, 20, 0, 0, 0),
        agel=(0.01, 0.02, 0.0),
        bgel=(0.05, 0.10, 0.0),
        qm=3.0,
        epaisseur_non_gelive_cm=20.0,
        couche_forme_traitee=False,
        pente_sol_pourcent=math.inf,
    )
    assert i_adm_inf == 145


def test_chaussee_verifiee_au_gel():
    assert chaussee_verifiee_au_gel(100, 247) is True
    assert chaussee_verifiee_au_gel(247, 247) is True
    assert chaussee_verifiee_au_gel(248, 247) is False
    assert chaussee_verifiee_au_gel(-1, 247) is False
    assert chaussee_verifiee_au_gel(100, 0) is False


def test_indice_gel_personnel():
    # frmDocument.frm :: CheckIndGelPerso_Click / TextIndGelPerso_LostFocus :
    # l'indice personnel remplace l'indice de référence, sans coefficient d'agglomération.
    assert indice_gel_reference("Toulouse", "HRNE", "moyenne", indice_personnel=55) == 55
    assert indice_gel_reference("Toulouse", "HE", "grande", indice_personnel=0) == 0
    # Sans indice personnel : calcul normal depuis la station (40 x CSng(0,9) = 36)
    assert indice_gel_reference("Toulouse", "HRNE", "moyenne", indice_personnel=None) == 36

    with pytest.raises(ValueError):
        indice_gel_reference("Toulouse", "HRNE", "moyenne", indice_personnel=-5)
    with pytest.raises(ValueError):
        indice_gel_reference("Toulouse", "HRNE", "moyenne", indice_personnel=12.5)
    with pytest.raises(ValueError):
        indice_gel_reference("Toulouse", "HRNE", "moyenne", indice_personnel=True)
