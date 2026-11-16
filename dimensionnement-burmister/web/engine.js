/* Dimensionnement de chaussées — Burmister + Struct-Urb. Développé par YannPRO81, agent territorial, et Claude, IA d'Anthropic, 2026.
   Licence GNU GPL v3 (œuvre dérivée de Struct-Urb, CERTU/Cerema). Sans garantie. */
/* Moteur de dimensionnement — solveur multicouche de Burmister + méthode rationnelle française.
   Port JavaScript du solveur Python validé (Boussinesq exact, équilibre, catalogue CERTU).
   Unités : MPa, m. Traction positive. */
(function (root) {
  "use strict";

  // ---------------------------------------------------------------- Bessel J0, J1
  function j0(x) {
    const ax = Math.abs(x);
    if (ax < 8.0) {
      const y = x * x;
      const a1 = 57568490574.0 + y * (-13362590354.0 + y * (651619640.7 + y * (-11214424.18 + y * (77392.33017 + y * (-184.9052456)))));
      const a2 = 57568490411.0 + y * (1029532985.0 + y * (9494680.718 + y * (59272.64853 + y * (267.8532712 + y * 1.0))));
      return a1 / a2;
    }
    const z = 8.0 / ax, y = z * z, xx = ax - 0.785398164;
    const a1 = 1.0 + y * (-0.1098628627e-2 + y * (0.2734510407e-4 + y * (-0.2073370639e-5 + y * 0.2093887211e-6)));
    const a2 = -0.1562499995e-1 + y * (0.1430488765e-3 + y * (-0.6911147651e-5 + y * (0.7621095161e-6 - y * 0.934935152e-7)));
    return Math.sqrt(0.636619772 / ax) * (Math.cos(xx) * a1 - z * Math.sin(xx) * a2);
  }
  function j1(x) {
    const ax = Math.abs(x);
    if (ax < 8.0) {
      const y = x * x;
      const a1 = x * (72362614232.0 + y * (-7895059235.0 + y * (242396853.1 + y * (-2972611.439 + y * (15704.48260 + y * (-30.16036606))))));
      const a2 = 144725228442.0 + y * (2300535178.0 + y * (18583304.74 + y * (99447.43394 + y * (376.9991397 + y * 1.0))));
      return a1 / a2;
    }
    const z = 8.0 / ax, y = z * z, xx = ax - 2.356194491;
    const a1 = 1.0 + y * (0.183105e-2 + y * (-0.3516396496e-4 + y * (0.2457520174e-5 + y * (-0.240337019e-6))));
    const a2 = 0.04687499995 + y * (-0.2002690873e-3 + y * (0.8449199096e-5 + y * (-0.88228987e-6 + y * 0.105787412e-6)));
    const ans = Math.sqrt(0.636619772 / ax) * (Math.cos(xx) * a1 - z * Math.sin(xx) * a2);
    return x < 0 ? -ans : ans;
  }

  // ---------------------------------------------------------------- Gauss-Legendre
  function gaussLegendre(n) {
    const x = new Float64Array(n), w = new Float64Array(n);
    for (let i = 0; i < n; i++) {
      let z = Math.cos(Math.PI * (i + 0.75) / (n + 0.5)), pp = 0;
      for (let it = 0; it < 100; it++) {
        let p1 = 1, p2 = 0;
        for (let j = 1; j <= n; j++) { const p3 = p2; p2 = p1; p1 = ((2 * j - 1) * z * p2 - (j - 1) * p3) / j; }
        pp = n * (z * p1 - p2) / (z * z - 1);
        const z1 = z; z = z1 - p1 / pp;
        if (Math.abs(z - z1) < 1e-15) break;
      }
      x[i] = -z; w[i] = 2 / ((1 - z * z) * pp * pp);
    }
    return { x, w };
  }
  const GL = gaussLegendre(24);

  function quadrature(zmin, a, rmax) {
    const zeff = Math.max(zmin, 0.005);
    const mmax = Math.max(32 / zeff, 60 / a);
    const width = Math.PI / (a + rmax + 1e-9) / 2;
    const nint = Math.ceil(mmax / width);
    const M = nint * GL.x.length;
    const m = new Float64Array(M), w = new Float64Array(M);
    let k = 0;
    for (let i = 0; i < nint; i++) {
      const lo = i * width, hi = lo + width;
      for (let j = 0; j < GL.x.length; j++) {
        m[k] = 0.5 * (hi - lo) * GL.x[j] + 0.5 * (hi + lo); w[k] = 0.5 * (hi - lo) * GL.w[j]; k++;
      }
    }
    return { m, w };
  }

  // ---------------------------------------------------------------- lignes de transfert
  // renvoie [u, w, sz/m, trz/m, ez/m] en fonction de (A,B,C,D) — tableau 5x4
  function lignes(m, z, zt, zb, E, nu, out) {
    let ep = 0, s = 0;
    if (isFinite(zb)) { s = m * (z - zb); ep = Math.exp(s); }
    const t = m * (z - zt), em = Math.exp(-t), k = (1 + nu) / E, c2 = 2 * (1 - 2 * nu);
    out[0] = k * ep; out[1] = -k * em; out[2] = k * (s + 1) * ep; out[3] = k * (1 - t) * em;
    out[4] = -k * ep; out[5] = -k * em; out[6] = k * (c2 - s) * ep; out[7] = -k * (c2 + t) * em;
    out[8] = -ep; out[9] = em; out[10] = (1 - 2 * nu - s) * ep; out[11] = (1 - 2 * nu + t) * em;
    out[12] = ep; out[13] = em; out[14] = (s + 2 * nu) * ep; out[15] = (t - 2 * nu) * em;
    out[16] = -k * ep; out[17] = k * em; out[18] = k * (1 - 4 * nu - s) * ep; out[19] = k * (1 - 4 * nu + t) * em;
    return out;
  }

  function solveLin(K, F, N) { // élimination de Gauss avec pivot partiel, K NxN (row-major), F N
    for (let c = 0; c < N; c++) {
      let p = c, best = Math.abs(K[c * N + c]);
      for (let r = c + 1; r < N; r++) { const v = Math.abs(K[r * N + c]); if (v > best) { best = v; p = r; } }
      if (p !== c) {
        for (let j = 0; j < N; j++) { const tmp = K[c * N + j]; K[c * N + j] = K[p * N + j]; K[p * N + j] = tmp; }
        const tf = F[c]; F[c] = F[p]; F[p] = tf;
      }
      const d = K[c * N + c];
      for (let r = c + 1; r < N; r++) {
        const f = K[r * N + c] / d; if (f === 0) continue;
        for (let j = c; j < N; j++) K[r * N + j] -= f * K[c * N + j];
        F[r] -= f * F[c];
      }
    }
    for (let r = N - 1; r >= 0; r--) {
      let s = F[r];
      for (let j = r + 1; j < N; j++) s -= K[r * N + j] * F[j];
      F[r] = s / K[r * N + r];
    }
    return F;
  }

  // ---------------------------------------------------------------- structure
  // couches : [{E, nu, h (m, Infinity pour le sol), interface:'collee'|'glissante'}]
  function Modele(couches, zmin, opts) {
    opts = opts || {};
    const a = opts.a || 0.125, rmax = opts.rmax || 0.375;
    const n = couches.length;
    const zt = [0], zb = [];
    for (let i = 0; i < n - 1; i++) zt.push(zt[i] + couches[i].h);
    for (let i = 0; i < n; i++) zb.push(i < n - 1 ? zt[i + 1] : Infinity);
    const Q = quadrature(zmin, a, rmax);
    const M = Q.m.length, N = 4 * n - 2, Eref = couches[0].E;
    const coef = new Float64Array(M * n * 4);
    const K = new Float64Array(N * N), F = new Float64Array(N), L1 = new Float64Array(20), L2 = new Float64Array(20);
    const colOf = (i) => (i < n - 1 ? 4 * i : 4 * (n - 1));
    function put(row, i, L, q, sgn, sc) {
      const c0 = colOf(i);
      if (i < n - 1) for (let j = 0; j < 4; j++) K[row * N + c0 + j] += sgn * sc * L[q * 4 + j];
      else { K[row * N + c0] += sgn * sc * L[q * 4 + 1]; K[row * N + c0 + 1] += sgn * sc * L[q * 4 + 3]; }
    }
    for (let k = 0; k < M; k++) {
      const m = Q.m[k];
      K.fill(0); F.fill(0);
      let r = 0;
      lignes(m, 0, zt[0], zb[0], couches[0].E, couches[0].nu, L1);
      put(r, 0, L1, 2, 1, 1); F[r] = -1; r++;
      put(r, 0, L1, 3, 1, 1); r++;
      for (let i = 0; i < n - 1; i++) {
        const z = zb[i];
        lignes(m, z, zt[i], zb[i], couches[i].E, couches[i].nu, L1);
        lignes(m, z, zt[i + 1], zb[i + 1], couches[i + 1].E, couches[i + 1].nu, L2);
        if (couches[i].interface !== "glissante") {
          for (const [q, sc] of [[0, Eref], [1, Eref], [2, 1], [3, 1]]) { put(r, i, L1, q, 1, sc); put(r, i + 1, L2, q, -1, sc); r++; }
        } else {
          for (const [q, sc] of [[1, Eref], [2, 1]]) { put(r, i, L1, q, 1, sc); put(r, i + 1, L2, q, -1, sc); r++; }
          put(r, i, L1, 3, 1, 1); r++;
          put(r, i + 1, L2, 3, 1, 1); r++;
        }
      }
      solveLin(K, F, N);
      for (let i = 0; i < n - 1; i++) for (let j = 0; j < 4; j++) coef[(k * n + i) * 4 + j] = F[4 * i + j];
      coef[(k * n + n - 1) * 4 + 1] = F[4 * (n - 1)];
      coef[(k * n + n - 1) * 4 + 3] = F[4 * (n - 1) + 1];
    }
    this.couches = couches; this.n = n; this.zt = zt; this.zb = zb; this.Q = Q; this.coef = coef; this.a = a;
  }
  Modele.prototype.coucheDe = function (z, cote) {
    for (let i = 0; i < this.n; i++) {
      if ((cote === "dessus" && z <= this.zb[i] + 1e-12) || (cote === "dessous" && z < this.zb[i] - 1e-12)) return i;
    }
    return this.n - 1;
  };
  // réponse d'une charge circulaire q à la cote z, pour plusieurs rayons
  Modele.prototype.reponse = function (z, rayons, q, cote) {
    const i = this.coucheDe(z, cote || "dessus"), c = this.couches[i], a = this.a;
    const { m, w } = this.Q, M = m.length, n = this.n, L = new Float64Array(20);
    const res = rayons.map(() => ({ u: 0, w: 0, sz: 0, er: 0, et: 0, ez: 0 }));
    for (let k = 0; k < M; k++) {
      const mk = m[k];
      if (mk * Math.max(z, 0.005) > 40) break; // décroissance e^{-mz} négligeable
      lignes(mk, z, this.zt[i], this.zb[i], c.E, c.nu, L);
      const o = (k * n + i) * 4, A = this.coef[o], B = this.coef[o + 1], C = this.coef[o + 2], D = this.coef[o + 3];
      const U = L[0] * A + L[1] * B + L[2] * C + L[3] * D;
      const W = L[4] * A + L[5] * B + L[6] * C + L[7] * D;
      const Sz = (L[8] * A + L[9] * B + L[10] * C + L[11] * D) * mk;
      const Ez = (L[16] * A + L[17] * B + L[18] * C + L[19] * D) * mk;
      const g = w[k] * q * a * j1(mk * a) / mk;
      for (let p = 0; p < rayons.length; p++) {
        const r = rayons[p], J0 = j0(mk * r), J1 = j1(mk * r), J1r = r > 0 ? J1 / r : mk / 2, R = res[p];
        R.u += g * U * J1; R.w += g * W * J0; R.sz += g * Sz * J0;
        R.er += g * U * (mk * J0 - J1r); R.et += g * U * J1r; R.ez += g * Ez * J0;
      }
    }
    return { couche: i, res };
  };

  // ---------------------------------------------------------------- jumelage
  const CONF = { NX: 7 };
  const CHARGE = { q: 0.662, a: 0.125, d: 0.375 };
  function jumelage(mod, z, cote, nx) {
    nx = nx || CONF.NX;
    const d = CHARGE.d, xs = [], rs = [];
    for (let i = 0; i < nx; i++) xs.push(i * d / 2 / (nx - 1));
    for (const x of xs) { rs.push(x); rs.push(d - x); }
    const R = mod.reponse(z, rs, CHARGE.q, cote).res;
    return xs.map((x, i) => {
      const r1 = R[2 * i], r2 = R[2 * i + 1];
      return { x, exx: r1.er + r2.er, eyy: r1.et + r2.et, ezz: r1.ez + r2.ez };
    });
  }
  function sigH(c, exx, eyy, ezz) {
    const lam = c.E * c.nu / ((1 + c.nu) * (1 - 2 * c.nu)), mu = c.E / (2 * (1 + c.nu)), tr = exx + eyy + ezz;
    return Math.max(lam * tr + 2 * mu * exx, lam * tr + 2 * mu * eyy);
  }
  function sollicitationsSimple(couches) {
    const zmin = couches[0].h;
    const mod = new Modele(couches, Math.min(zmin, 0.04), { a: CHARGE.a, rmax: CHARGE.d });
    return couches.map((c, i) => {
      const o = { couche: i };
      if (i < mod.n - 1) {
        const P = jumelage(mod, mod.zb[i], "dessus");
        o.eps_t = Math.max(...P.map(p => Math.max(p.exx, p.eyy)));
        o.sigma_t = Math.max(...P.map(p => sigH(c, p.exx, p.eyy, p.ezz)));
      }
      if (i > 0) {
        const P = jumelage(mod, mod.zt[i], "dessous");
        o.eps_z = Math.max(...P.map(p => -p.ezz));
      }
      return o;
    });
  }
  // interfaces semi-collées : moyenne des calculs collé et glissant (convention Alizé)
  function sollicitations(couches) {
    const semi = couches.some(c => c.interface === "semi");
    if (!semi) return sollicitationsSimple(couches);
    const A = sollicitationsSimple(couches.map(c => Object.assign({}, c, { interface: c.interface === "semi" ? "collee" : c.interface })));
    const B = sollicitationsSimple(couches.map(c => Object.assign({}, c, { interface: c.interface === "semi" ? "glissante" : c.interface })));
    return A.map((a, i) => {
      const o = { couche: i };
      for (const k of ["eps_t", "sigma_t", "eps_z"]) if (k in a) o[k] = 0.5 * (a[k] + B[i][k]);
      return o;
    });
  }

  root.Burmister = { j0, j1, Modele, sollicitations, sollicitationsSimple, jumelage, CHARGE, CONF };
})(typeof module !== "undefined" ? module.exports : window);
