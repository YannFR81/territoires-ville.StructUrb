"""Vérification rationnelle à la française (méthode LCPC-SETRA 1994 / NF P98-086).

ATTENTION : les paramètres ci-dessous sont des valeurs par défaut issues de la
méthode de 1994 et du catalogue CERTU ; ils sont à confronter au référentiel
en vigueur avant toute utilisation en étude.
"""
import math
from scipy.stats import norm

# Paramètres de fatigue par défaut (à vérifier)
#   E15 : module à 15 °C / 10 Hz (MPa) ; E10 : module à 10 °C / 10 Hz
#   eps6 (µdef, 10 °C, 25 Hz) ; sigma6 (MPa) ; inv_b = -1/b ; SN ; kc
MATERIAUX = {
    "BBSG": dict(fam="bitumineux", E15=5400, E10=7200, nu=0.35, eps6=100, inv_b=5, SN=0.25, kc=1.1),
    "GB3":  dict(fam="bitumineux", E15=9000, E10=12300, nu=0.35, eps6=90, inv_b=5, SN=0.30, kc=1.3),
    "GB2":  dict(fam="bitumineux", E15=9000, E10=12300, nu=0.35, eps6=80, inv_b=5, SN=0.30, kc=1.3),
    "EME":  dict(fam="bitumineux", E15=14000, E10=16900, nu=0.35, eps6=130, inv_b=5, SN=0.25, kc=1.0),
    "GC3":  dict(fam="hydraulique", E15=23000, nu=0.25, sigma6=0.75, inv_b=15, SN=1.0, kc=1.4, kd=1.0),  # kd=1 : retrouvé par calage sur le catalogue CERTU
    "GNT":  dict(fam="non_lie", E15=None, nu=0.35),
}
PLATEFORMES = {"PF1": 20, "PF2": 50, "PF2+": 80, "PF3": 120}
KS = {"PF1": 1/1.2, "PF2": 1/1.1, "PF2+": 1.0, "PF3": 1.0}


def u_risque(r_pct):
    return norm.ppf(r_pct / 100.0)          # 5 % -> -1.645


def Sh_bitumineux(h_m, Q="Q1"):
    """Dispersion d'épaisseur (m) : 0,01 si h<=0,10 ; 0,025 si h>=0,15 ; interpolation.
    Q2 (chantier difficile) : hypothèse à confirmer."""
    if h_m <= 0.10: s = 0.01
    elif h_m >= 0.15: s = 0.025
    else: s = 0.01 + (h_m - 0.10) * (0.015 / 0.05)
    return s


def kr(r_pct, inv_b, SN, Sh_m, c=2.0):
    """kr = 10^(-u b delta), delta = sqrt(SN² + (c/b)² Sh²), c = 0,02 cm⁻¹ = 2 m⁻¹."""
    b = -1.0 / inv_b
    delta = math.sqrt(SN ** 2 + (c / b) ** 2 * Sh_m ** 2)
    return 10 ** (-u_risque(r_pct) * b * delta)


def eps_t_adm(mat, NE, r_pct, Sh_m, pf, theta_eq=15):
    p = MATERIAUX[mat]
    keth = math.sqrt(p["E10"] / p["E15"])     # ε6(θeq) = ε6(10°C)·sqrt(E10/Eθ) pour θeq = 15 °C
    return 1e-6 * p["eps6"] * keth * (NE / 1e6) ** (-1 / p["inv_b"]) * p["kc"] * \
        kr(r_pct, p["inv_b"], p["SN"], Sh_m) * KS[pf]


def sigma_t_adm(mat, NE, r_pct, Sh_m, pf):
    p = MATERIAUX[mat]
    return p["sigma6"] * (NE / 1e6) ** (-1 / p["inv_b"]) * p["kc"] * p["kd"] * \
        kr(r_pct, p["inv_b"], p["SN"], Sh_m) * KS[pf]


def eps_z_adm(NE, trafic_fort=True):
    A = 0.012 if trafic_fort else 0.016
    return A * NE ** (-0.222)
