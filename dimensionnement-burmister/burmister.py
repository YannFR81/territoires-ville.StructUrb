# Dimensionnement de chaussées — Burmister + Struct-Urb. Développé par YannPRO81, agent territorial, et Claude, IA d'Anthropic, 2026.
# Licence GNU GPL v3 (œuvre dérivée de Struct-Urb, CERTU/Cerema). Sans garantie.
"""Solveur multicouche élastique linéaire de Burmister (axisymétrique).

Modèle : couches horizontales élastiques isotropes d'épaisseur finie sur un
massif semi-infini. Interfaces collées ou glissantes. Charge circulaire
uniforme (pression q, rayon a) ; superposition pour le jumelage.

Méthode : fonction de Love phi = J0(m r) f(z) dans chaque couche, résolution
dans l'espace de Hankel pour chaque m, puis intégration numérique.
f(z) = [(A + C m(z-zb)) e^{m(z-zb)} + (B + D m(z-zt)) e^{-m(z-zt)}] / m^2
Les exponentielles restent <= 1 dans la couche : pas de débordement.

Unités : MPa, m. Convention : traction positive.
"""
from dataclasses import dataclass, field
import numpy as np
from scipy.special import j0, j1, jn_zeros


@dataclass
class Couche:
    E: float               # module (MPa)
    nu: float              # coefficient de Poisson
    h: float = np.inf      # épaisseur (m), inf pour le sol support
    nom: str = ""
    interface: str = "collee"  # liaison avec la couche SOUS-jacente : "collee" | "glissante"


# ---------------------------------------------------------------- transferts
def _termes(m, z, zt, zb):
    """Exponentielles normalisées et variables s, t (vectorisées en m)."""
    if np.isinf(zb):
        ep = np.zeros_like(m); s = np.zeros_like(m)
    else:
        ep = np.exp(m * (z - zb)); s = m * (z - zb)
    em = np.exp(-m * (z - zt)); t = m * (z - zt)
    return ep, em, s, t


def _lignes(m, z, zt, zb, E, nu):
    """Lignes [u, w, sz/m, trz/m, ez/m] exprimées sur (A, B, C, D). Forme (M, 5, 4)."""
    ep, em, s, t = _termes(m, z, zt, zb)
    k = (1 + nu) / E
    L = np.empty(m.shape + (5, 4))
    # u (coef de J1)
    L[:, 0] = np.stack([k * ep, -k * em, k * (s + 1) * ep, k * (1 - t) * em], -1)
    # w (coef de J0)
    L[:, 1] = np.stack([-k * ep, -k * em, k * (2 * (1 - 2 * nu) - s) * ep,
                        -k * (2 * (1 - 2 * nu) + t) * em], -1)
    # sigma_z / m (coef de J0)
    L[:, 2] = np.stack([-ep, em, (1 - 2 * nu - s) * ep, (1 - 2 * nu + t) * em], -1)
    # tau_rz / m (coef de J1)
    L[:, 3] = np.stack([ep, em, (s + 2 * nu) * ep, (t - 2 * nu) * em], -1)
    # eps_z / m = (dw/dz)/m (coef de J0)
    L[:, 4] = np.stack([-k * ep, k * em, k * (1 - 4 * nu - s) * ep,
                        k * (1 - 4 * nu + t) * em], -1)
    return L


class Structure:
    def __init__(self, couches):
        assert np.isinf(couches[-1].h), "la dernière couche doit être semi-infinie"
        self.c = couches
        self.n = len(couches)
        z = np.concatenate([[0.0], np.cumsum([c.h for c in couches[:-1]])])
        self.zt = z                                   # cotes des toits
        self.zb = np.append(z[1:], np.inf)            # cotes des bases
        self.Eref = couches[0].E

    def couche_de(self, z, cote="dessus"):
        """Indice de la couche contenant z ; à une interface, 'dessus' = couche supérieure."""
        for i in range(self.n):
            if (cote == "dessus" and z <= self.zb[i] + 1e-12) or (cote == "dessous" and z < self.zb[i] - 1e-12):
                return i
        return self.n - 1

    def resoudre(self, m):
        """Coefficients (M, n, 4) pour un chargement sz(z=0) = -1 * m (soit sz/m = -1), trz=0."""
        n, M = self.n, m.size
        N = 4 * n - 2
        K = np.zeros((M, N, N)); F = np.zeros((M, N))
        col = lambda i: slice(4 * i, 4 * i + 4) if i < n - 1 else None
        sc = self.Eref  # mise à l'échelle des lignes en déplacement

        def blocs(i, z):
            c = self.c[i]
            L = _lignes(m, z, self.zt[i], self.zb[i], c.E, c.nu)
            if i == n - 1:  # demi-espace : seuls B et D (colonnes 1 et 3)
                L = L[..., [1, 3]]
            return L

        def place(row, i, vals):
            if i < n - 1:
                K[:, row, 4 * i:4 * i + 4] += vals
            else:
                K[:, row, 4 * (n - 1):4 * (n - 1) + 2] += vals

        r = 0
        L0 = blocs(0, 0.0)
        place(r, 0, L0[:, 2]); F[:, r] = -1.0; r += 1      # sz/m = -1
        place(r, 0, L0[:, 3]); r += 1                       # trz = 0
        for i in range(n - 1):
            z = self.zb[i]
            Lh, Lb = blocs(i, z), blocs(i + 1, z)
            if self.c[i].interface == "collee":
                for q, s_ in [(0, sc), (1, sc), (2, 1), (3, 1)]:
                    place(r, i, s_ * Lh[:, q]); place(r, i + 1, -s_ * Lb[:, q]); r += 1
            else:  # glissante
                for q, s_ in [(1, sc), (2, 1)]:
                    place(r, i, s_ * Lh[:, q]); place(r, i + 1, -s_ * Lb[:, q]); r += 1
                place(r, i, Lh[:, 3]); r += 1
                place(r, i + 1, Lb[:, 3]); r += 1
        assert r == N
        X = np.linalg.solve(K, F[..., None])[..., 0]
        coef = np.zeros((M, n, 4))
        for i in range(n - 1):
            coef[:, i] = X[:, 4 * i:4 * i + 4]
        coef[:, n - 1, [1, 3]] = X[:, 4 * (n - 1):]
        return coef

    # ------------------------------------------------------------ réponses
    def _noyaux(self, m, z, cote):
        """Noyaux unitaires U, W, Sz, Ez(=dw/dz) à la cote z, pour sz/m=-1 en surface."""
        i = self.couche_de(z, cote)
        coef = self.resoudre(m)[:, i]
        c = self.c[i]
        if i == self.n - 1:
            pass
        L = _lignes(m, z, self.zt[i], self.zb[i], c.E, c.nu)
        v = np.einsum('mkj,mj->mk', L, coef)
        U, W, Szm, Tm, Ezm = v.T
        return i, U, W, Szm * m, Ezm * m

    def reponse(self, z, rayons, q=0.662, a=0.125, cote="dessus", tol=1e-10):
        """Pour une charge circulaire unique : u, w, sz, eps_r, eps_t, eps_z aux distances 'rayons'."""
        rayons = np.atleast_1d(np.asarray(rayons, float))
        m, wgt = _quadrature(z, a, rayons.max())
        i, U, W, Sz, Ez = self._noyaux(m, z, cote)
        g = q * a * j1(m * a) / m     # transformée de la charge (sz/m = -g en surface)
        out = {k: [] for k in ("u", "w", "sz", "er", "et", "ez")}
        for r in rayons:
            J0, J1 = j0(m * r), j1(m * r)
            J1r = J1 / r if r > 0 else m / 2
            # sz/m = -1 unitaire -> multiplier par g ; sz réel = m * sz_hat
            out["u"].append(np.sum(wgt * g * U * J1))
            out["w"].append(np.sum(wgt * g * W * J0))
            out["sz"].append(np.sum(wgt * g * Sz * J0))
            out["er"].append(np.sum(wgt * g * U * (m * J0 - J1r)))
            out["et"].append(np.sum(wgt * g * U * J1r))
            out["ez"].append(np.sum(wgt * g * Ez * J0))
        out = {k: np.array(v) for k, v in out.items()}
        out["couche"] = i
        return out


def _quadrature(z, a, rmax, npts=24):
    """Gauss-Legendre par intervalles calés sur les zéros de J1(m a), tronqués là où e^{-mz} ~ 1e-13."""
    zeff = max(z, 0.005)
    mmax = max(32.0 / zeff, 60.0 / a)
    width = np.pi / (a + rmax + 1e-9) / 2
    bornes = np.arange(0.0, mmax + width, width)
    xg, wg = np.polynomial.legendre.leggauss(npts)
    lo, hi = bornes[:-1, None], bornes[1:, None]
    m = (0.5 * (hi - lo) * xg + 0.5 * (hi + lo)).ravel()
    w = (0.5 * (hi - lo) * wg).ravel()
    return m, w


# ---------------------------------------------------------------- jumelage
def jumelage(struct, z, q=0.662, a=0.125, d=0.375, cote="dessus", nx=7):
    """Déformations horizontales eps_xx, eps_yy et eps_z sur l'axe x de 0 (sous roue) à d/2 (entre roues)."""
    xs = np.linspace(0, d / 2, nx)
    # distances à la roue 1 (x=0) et à la roue 2 (x=d)
    rs = np.unique(np.concatenate([xs, d - xs]))
    R = struct.reponse(z, rs, q, a, cote)
    idx = {round(r, 9): k for k, r in enumerate(rs)}
    res = []
    for x in xs:
        k1, k2 = idx[round(x, 9)], idx[round(d - x, 9)]
        exx = R["er"][k1] + R["er"][k2]   # points sur l'axe x : radial = x
        eyy = R["et"][k1] + R["et"][k2]
        ezz = R["ez"][k1] + R["ez"][k2]
        szz = R["sz"][k1] + R["sz"][k2]
        res.append(dict(x=x, exx=exx, eyy=eyy, ezz=ezz, szz=szz))
    return res, R["couche"]


def contrainte_horizontale(c, exx, eyy, ezz):
    lam = c.E * c.nu / ((1 + c.nu) * (1 - 2 * c.nu)); mu = c.E / (2 * (1 + c.nu))
    tr = exx + eyy + ezz
    return lam * tr + 2 * mu * exx, lam * tr + 2 * mu * eyy


def sollicitations(struct, q=0.662, a=0.125, d=0.375):
    """Pour chaque couche : eps_t max à la base (liées), sigma_t max à la base, eps_z en tête des couches non liées / sol."""
    res = []
    for i, c in enumerate(struct.c):
        info = dict(couche=i, nom=c.nom, E=c.E)
        if i < struct.n - 1:
            pts, _ = jumelage(struct, struct.zb[i], q, a, d, cote="dessus")
            et = [max(p["exx"], p["eyy"]) for p in pts]
            k = int(np.argmax(et))
            sx = [max(contrainte_horizontale(c, p["exx"], p["eyy"], p["ezz"])) for p in pts]
            info.update(eps_t=et[k], x_eps_t=pts[k]["x"], sigma_t=max(sx))
        if i > 0:
            pts, _ = jumelage(struct, struct.zt[i], q, a, d, cote="dessous")
            ez = [-p["ezz"] for p in pts]   # compression positive
            info.update(eps_z=max(ez))
        res.append(info)
    return res
