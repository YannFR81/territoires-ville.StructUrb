/* Dimensionnement de chaussées — Burmister + Struct-Urb. Développé par YannFR81, agent territorial, et Claude, IA d’Anthropic, 2026.
   Licence GNU GPL v3 (œuvre dérivée de Struct-Urb, CERTU/Cerema). Sans garantie. */
/* Méthode rationnelle française — deux référentiels :
   « nf2019 » : NF P98-086 (mai 2019), paramètres des annexes B, C, D et H lus dans le texte de la norme ;
   « certu »  : méthode 1994 recalée sur le catalogue Struct-Urb (CERTU). */
(function (root) {
  "use strict";
  const B = root.Burmister || (typeof require !== "undefined" ? require("./engine.js").Burmister : null);
  const bit = (nom, E, ratio, eps6, SN, kc, x) => Object.assign({ nom, fam: "bitumineux", E, E10: Math.round(E * ratio), nu: 0.35, eps6, invb: 5, SN, kc, ag: 0.008, bg: 0.06 }, x || {});
  const hyd = (nom, E, sig6, invb, SN, kc, x) => Object.assign({ nom, fam: "hydraulique", E, nu: 0.25, sig6, invb, SN, kc, kd: 1, Sh: 0.03, ag: 0.008, bg: 0.10 }, x || {});
  const R = { roulement: true };

  // ---------------- NF P98-086 : 2019 (tableaux D.1 à D.14, H.2)
  const NF = {
    BBSG:  bit("EB-BBSG classe 2 ou 3", 7000, 1.33, 100, 0.25, 1.1, R),
    BBSG1: bit("EB-BBSG classe 1", 5500, 1.33, 100, 0.25, 1.1, R),
    BBME:  bit("EB-BBME classe 2 ou 3", 11000, 1.33, 100, 0.25, 1.1, R),
    BBME1: bit("EB-BBME classe 1", 9000, 1.33, 100, 0.25, 1.1, R),
    BBM:   bit("BB mince", 5500, 1.33, 100, 0.25, 1.1, R),
    BBTM:  bit("BB très mince", 3000, 1.33, 100, 0.25, 1.1, R),
    BBDr:  bit("BB drainant", 3000, 1.33, 100, 0.25, 1.1, R),
    GB2:   bit("Grave-bitume classe 2", 9000, 1.32, 80, 0.30, 1.3),
    GB3:   bit("Grave-bitume classe 3", 9000, 1.32, 90, 0.30, 1.3),
    GB4:   bit("Grave-bitume classe 4", 11000, 1.30, 100, 0.30, 1.3),
    EME1:  bit("EME classe 1", 14000, 1.21, 100, 0.30, 1.0),
    EME:   bit("EME classe 2", 14000, 1.21, 130, 0.25, 1.0),
    GNT:   { nom: "GNT catégorie CG1", fam: "non_lie", E: 600, nu: 0.35, kGNT: 3, EmaxGNT: 600, ag: 0.008, bg: 0.10 },
    GNT2:  { nom: "GNT catégorie CG2", fam: "non_lie", E: 400, nu: 0.35, kGNT: 2.5, EmaxGNT: 400, ag: 0.008, bg: 0.10 },
    GNT3:  { nom: "GNT catégorie CG3", fam: "non_lie", E: 200, nu: 0.35, kGNT: 2, EmaxGNT: 200, ag: 0.008, bg: 0.10 },
    GC3:   hyd("Grave-ciment / GLHR / GCVH T3", 23000, 0.75, 15, 1, 1.4),
    GC4:   hyd("Grave-ciment / GLHR T4", 25000, 1.20, 15, 1, 1.4, { kdBase: 1 / 1.25, T4: true, glisse: true }),
    GLg:   hyd("Grave-laitier granulé ou prébroyé T2", 15000, 0.60, 12, 1, 1.5, { laitier: true }),
    "GLg-T2": hyd("Grave-laitier granulé ou prébroyé T2", 15000, 0.60, 12, 1, 1.5, { laitier: true }),
    GLp3:  hyd("Grave-laitier prébroyé T3", 20000, 0.70, 14, 1, 1.5, { laitier: true }),
    GLCV:  hyd("Grave-laitier-cendres volantes-chaux T3", 22000, 0.80, 13, 1, 1.5),
    GCV:   hyd("Grave-cendres volantes silicoalumineuses-chaux T4", 30000, 1.40, 16, 1, 1.5, { kdBase: 1 / 1.25, T4: true, glisse: true }),
    GPz:   hyd("Grave-pouzzolanes-chaux T2", 15000, 0.60, 12, 1, 1.5),
    BCR4:  hyd("Béton compacté routier T4", 25000, 1.20, 15, 1, 1.5, { kdBase: 1 / 1.25, T4: true }),
    BCR5:  hyd("Béton compacté routier T5", 28000, 1.85, 15, 1, 1.5, { kdBase: 1 / 1.25, T4: true }),
    SC:    hyd("Sable-ciment / SCV-chaux / SLHR T3", 17200, 0.75, 12, 0.8, 1.5, { Sh: 0.025, ag: 0.012, bg: 0.15 }),
    SC2:   hyd("Sable-ciment / SCV-chaux / SLHR T2", 12000, 0.50, 12, 0.8, 1.5, { Sh: 0.025, ag: 0.012, bg: 0.15 }),
    SL:    hyd("Sable-laitier T3", 12500, 0.65, 10, 0.8, 1.5, { Sh: 0.025, ag: 0.012, bg: 0.15 }),
    SL2:   hyd("Sable-laitier T2", 8500, 0.43, 10, 0.8, 1.5, { Sh: 0.025, ag: 0.012, bg: 0.15 }),
    SolT:  hyd("Sol fin traité (E et σ6 d’étude)", 12000, 0.50, 11, 0.8, 1.4, { Sh: 0.04, ag: 0.012, bg: 0.14, sol: true, saisie: true }),
    SolS:  hyd("Sol sableux traité (E et σ6 d’étude)", 12000, 0.50, 11, 0.8, 1.4, { Sh: 0.04, ag: 0.008, bg: 0.10, sol: true, saisie: true }),
    SolG:  hyd("Sol graveleux traité (E et σ6 d’étude)", 12000, 0.50, 11, 1, 1.4, { Sh: 0.05, ag: 0.008, bg: 0.10, sol: true, saisie: true }),
    BC5:   hyd("Béton BC5, dalles non goujonnées", 35000, 2.15, 16, 1, 1.5, { beton: "ng" }),
    BC5g:  hyd("Béton BC5, dalles goujonnées", 35000, 2.15, 16, 1, 1.5, { beton: "g" }),
    BAC:   hyd("Béton armé continu (BC5)", 35000, 2.15, 16, 1, 1.5, { beton: "bac" }),
    BC6g:  hyd("Béton BC6, dalles goujonnées", 40000, 2.60, 16, 1, 1.5, { beton: "g" }),
    BC4:   hyd("Béton BC4, dalles non goujonnées", 30000, 1.95, 15, 1, 1.5, { beton: "ng" }),
    BC3:   hyd("Béton maigre BC3 (fondation)", 24000, 1.63, 15, 1, 1.5, { beton: "fond" }),
    BC2:   hyd("Béton maigre BC2 (fondation)", 20000, 1.37, 14, 1, 1.5, { beton: "fond" }),
  };
  // ---------------- CERTU / méthode 1994, recalé sur le catalogue Struct-Urb
  const C94 = "CERTU / 1994";
  const CERTU = {
    BBSG: bit("Béton bitumineux semi-grenu", 5400, 7200 / 5400, 100, 0.25, 1.1, R),
    BBME: bit("Béton bitumineux à module élevé", 9000, 11000 / 9000, 100, 0.25, 1.0, R),
    BBM:  bit("Béton bitumineux mince", 5400, 7200 / 5400, 100, 0.25, 1.1, R),
    GB2:  bit("Grave-bitume classe 2", 9000, 12300 / 9000, 80, 0.30, 1.3),
    GB3:  bit("Grave-bitume classe 3", 9000, 12300 / 9000, 90, 0.30, 1.3),
    EME:  bit("Enrobé à module élevé classe 2", 14000, 16900 / 14000, 130, 0.25, 1.0),
    GNT:  { nom: "Grave non traitée", fam: "non_lie", E: 600, nu: 0.35, ag: 0.008, bg: 0.10, kGNT: 3, EmaxGNT: 600 },
    GC3:  hyd("Grave-ciment T3", 23000, 0.75, 15, 1.0, 1.4),
    SC:   hyd("Sable-ciment", 17200, 0.75, 12, 0.8, 1.5, { ag: 0.012, bg: 0.15 }),
    SL:   hyd("Sable-laitier", 12500, 0.65, 12.5, 0.8, 1.5, { ag: 0.012, bg: 0.15, nonCale: true }),
    GLg:  hyd("Grave-laitier granulé", 15000, 0.50, 12.5, 1.0, 1.5),
    "GLg-T2": hyd("Grave-laitier granulé T2", 15000, 0.60, 12.5, 1.0, 1.5),
    GCV:  hyd("Grave-cendres volantes", 30000, 1.15, 13.5, 1.0, 1.2, { ag: 0.012, bg: 0.13, cale: "kc·kd = 1,2 (calé sur le catalogue CERTU)" }),
    BC5:  hyd("Béton de ciment BC5", 35000, 2.15, 16, 1.0, 1.5, { kd: 1 / 1.47, beton: "certu" }),
    BC5g: hyd("Béton de ciment BC5 goujonné", 35000, 2.15, 16, 1.0, 1.5, { kd: 0.82, beton: "certu", cale: "kc·kd = 1,23 (calé sur le catalogue CERTU)" }),
    BC3:  hyd("Béton maigre BC3", 24000, 1.63, 15, 1.0, 1.5, { kd: 1 / 1.47, beton: "certu" }),
  };
  const REFERENTIELS = {
    nf2019: { nom: "NF P98-086 : 2019 (paramètres des annexes de la norme)", court: "NF P98-086 : 2019" },
    certu: { nom: "CERTU / méthode 1994 (recalé sur le catalogue Struct-Urb)", court: C94 },
  };
  const MATERIAUX = {};
  const PLATEFORMES = { PF1: { E: 20, ks: 1 / 1.2 }, PF2: { E: 50, ks: 1 / 1.1 }, "PF2+": { E: 80, ks: 1.0 }, PF3: { E: 120, ks: 1.0 }, PF4: { E: 200, ks: 1.0 } };
  const REF = { cle: "nf2019" };
  const estNF = () => REF.cle === "nf2019";
  function setReferentiel(cle) {
    REF.cle = cle;
    const src = cle === "nf2019" ? NF : CERTU;
    for (const k of Object.keys(MATERIAUX)) delete MATERIAUX[k];
    for (const [k, v] of Object.entries(src)) MATERIAUX[k] = Object.assign({ origine: REFERENTIELS[cle].court }, v);
    PLATEFORMES["PF2+"].ks = cle === "nf2019" ? 1 / 1.065 : 1.0;
    B.CONF.NX = cle === "nf2019" ? 2 : 7;   // norme : axe de roue et centre du jumelage uniquement (5.3)
  }
  setReferentiel("nf2019");
  const ksNorme = (E) => (E < 50 ? 1 / 1.2 : E < 80 ? 1 / 1.1 : E < 120 ? 1 / 1.065 : 1); // tableau C.2

  function normInv(p) {
    const a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02, 1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00];
    const b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02, 6.680131188771972e+01, -1.328068155288572e+01];
    const c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00, -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00];
    const d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00];
    const pl = 0.02425;
    if (p < pl) { const q = Math.sqrt(-2 * Math.log(p)); return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1); }
    if (p > 1 - pl) return -normInv(1 - p);
    const q = p - 0.5, r = q * q;
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
  }
  const uRisque = (r) => (r > 0 ? normInv(r / 100) : -Infinity);
  function kr(r, invb, SN, Sh) {
    if (!(r > 0)) return 1;
    const b = -1 / invb, delta = Math.sqrt(SN * SN + (2 / b) * (2 / b) * Sh * Sh); // c = 2 m⁻¹
    return Math.pow(10, -uRisque(r) * b * delta);
  }
  function ShBitumineux(h) { return h <= 0.10 ? 0.01 : h >= 0.15 ? 0.025 : 0.01 + (h - 0.10) * 0.3; } // équation D.3

  function interfaceDefaut(haut, bas) {
    if (!bas) return "collee";
    const H = MATERIAUX[haut], L = MATERIAUX[bas];
    if (!H || !L) return "collee";
    if (!estNF()) {
      if (H.beton) return "glissante";
      if (H.fam === "hydraulique" && L.fam === "hydraulique") return "semi";
      return "collee";
    }
    if (H.beton && H.beton !== "fond") {                       // 8.8.1.1
      if (L.fam === "bitumineux") return (H.beton === "bac" && L.roulement) ? "glissante" : "semi";
      if (L.fam === "hydraulique") return "glissante";
      return "collee";
    }
    if (H.fam === "hydraulique" && L.fam === "hydraulique") {  // 8.5.1.3
      if (H.glisse || L.glisse) return "glissante";
      if (H.laitier && L.laitier) return "collee";
      return "semi";
    }
    if (H.fam === "bitumineux" && L.sol) return "semi";        // 8.5.1.3 et 8.6.1
    return "collee";
  }

  const estAssiseLiee = (c) => { const M = MATERIAUX[c.mat]; return c.h_cm > 0 && (M.fam === "hydraulique" || (M.fam === "bitumineux" && !M.roulement)); };
  const estSouple = (couches) => !couches.some(estAssiseLiee);

  /* Modèle mécanique. couches : [{mat, h_cm, interface, verifier}] de haut en bas.
     opt.degel : épaisseur (m) d’une couche dégelée de module E_PF/10 insérée sous la plate-forme (6.2.1.5). */
  function modeleMeca(couches, pf, opt) {
    opt = opt || {};
    const Epf = PLATEFORMES[pf].E, tmp = [], souple = estSouple(couches);
    const actives = couches.map((c, i) => ({ c, i })).filter(x => x.c.h_cm > 0);
    let Esous = Epf;
    for (let a = actives.length - 1; a >= 0; a--) {
      const { c, i } = actives[a], M = MATERIAUX[c.mat], h = c.h_cm / 100;
      if (M.fam === "non_lie") {
        let k = M.kGNT, Emax = M.EmaxGNT, base = false;
        if (estNF()) {
          if (!souple) { k = 3; Emax = 360; }                  // tableau D.1 : fondation de chaussée bitumineuse
          else {                                               // couche de base de chaussée souple : E = Emax
            const dessus = actives.slice(0, a).some(x => MATERIAUX[x.c.mat].fam === "non_lie");
            const dessous = actives.slice(a + 1).some(x => MATERIAUX[x.c.mat].fam === "non_lie");
            base = !dessus && dessous;
          }
        }
        if (base) { tmp.push({ E: Emax, nu: M.nu, h, src: i }); Esous = Emax; continue; }
        // sous-couches de 25 cm à partir du bas, la dernière (en haut) pouvant être plus mince
        const n = Math.max(1, Math.ceil(h / 0.25 - 1e-9));
        for (let s = 0; s < n; s++) {
          const hs = estNF() ? (s < n - 1 ? 0.25 : h - 0.25 * (n - 1)) : h / n;
          Esous = Math.min(k * Esous, Emax);
          tmp.push({ E: Esous, nu: M.nu, h: hs, src: i });
        }
      } else { tmp.push({ E: M.E, nu: M.nu, h, src: i }); Esous = M.E; }
    }
    tmp.reverse();
    const mod = tmp.map((m, k) => Object.assign({}, m, { interface: (k + 1 < tmp.length && tmp[k + 1].src === m.src) ? "collee" : couches[m.src].interface }));
    if (opt.degel > 0) mod.push({ E: Epf / 10, nu: 0.35, h: opt.degel, interface: "collee", src: -2 });
    mod.push({ E: Epf, nu: 0.35, h: Infinity, interface: "collee", src: -1 });
    return mod;
  }

  const val = (x, fam) => (typeof x === "object" ? x[fam] : x);
  /* ctx = {NE, risque, pf, Afatigue}. NE et risque : nombre, ou objet {bitumineux, hydraulique, sol, pf}. */
  function verifier(couches, ctx, opt) {
    const mod = modeleMeca(couches, ctx.pf, opt);
    const sol = B.sollicitations(mod), crit = [], nf = estNF();
    const NEpf = val(ctx.NE, "pf"), A = nf ? (NEpf > 250000 ? 0.012 : 0.016) : ctx.Afatigue;
    const souple = estSouple(couches);
    const ksDe = (k) => {              // module de la première couche non liée sous la couche modèle k (annexe C.2)
      if (!nf) return PLATEFORMES[ctx.pf].ks;
      // 3.3.8 : ks ne dépend que de la couche immédiatement sous-jacente, et vaut 1 si elle est liée
      const dessous = mod[k + 1];
      if (dessous.src < 0) return ksNorme(PLATEFORMES[ctx.pf].E);          // plate-forme (une couche dégelée ne change pas ks)
      return MATERIAUX[couches[dessous.src].mat].fam === "non_lie" ? ksNorme(dessous.E) : 1;
    };
    couches.forEach((c, i) => {
      if (c.h_cm <= 0) return;
      const M = MATERIAUX[c.mat];
      const idx = mod.map((m, k) => (m.src === i ? k : -1)).filter(k => k >= 0);
      const bas = idx[idx.length - 1], haut = idx[0];
      if (M.fam === "bitumineux" && c.verifier) {
        let h = c.h_cm;                // Sh : épaisseur totale de l’assise bitumineuse (D.3.1.1)
        for (let j = i - 1; j >= 0 && MATERIAUX[couches[j].mat].fam === "bitumineux" && !MATERIAUX[couches[j].mat].roulement; j--) h += couches[j].h_cm;
        for (let j = i + 1; j < couches.length && MATERIAUX[couches[j].mat].fam === "bitumineux" && !MATERIAUX[couches[j].mat].roulement; j++) h += couches[j].h_cm;
        const NE = val(ctx.NE, "bitumineux"), ks = ksDe(bas);
        const adm = 1e-6 * M.eps6 * Math.sqrt(M.E10 / M.E) * Math.pow(NE / 1e6, -1 / M.invb) * M.kc * kr(val(ctx.risque, "bitumineux"), M.invb, M.SN, ShBitumineux(h / 100)) * ks;
        crit.push({ couche: i, mat: c.mat, type: "εt base", calc: sol[bas].eps_t, adm, unite: "µdef", f: 1e6, fatigue: true, k: bas, g: "eps_t", NE, ks });
      } else if (M.fam === "hydraulique" && c.verifier) {
        // 8.5.2 : couches traitées collées entre elles → critère à la base de l’assise seulement
        const suiv = couches.slice(i + 1).find(x => x.h_cm > 0), Ms = suiv && MATERIAUX[suiv.mat];
        if (nf && !M.beton && c.interface === "collee" && Ms && Ms.fam === "hydraulique" && !Ms.beton) return;
        const audessus = couches.slice(0, i).filter(x => x.h_cm > 0);
        const hydDessus = audessus.some(x => MATERIAUX[x.mat].fam === "hydraulique");
        let kd = M.kd, fam = M.sol ? "sol" : "hydraulique";
        if (nf && M.beton) {           // tableau D.12
          if (M.beton === "fond" || hydDessus) kd = 1;
          else {
            const dessous = couches.slice(i + 1).find(x => x.h_cm > 0), Md = dessous && MATERIAUX[dessous.mat];
            const surGB = Md && Md.fam === "bitumineux" && !Md.roulement, surHyd = Md && Md.fam === "hydraulique";
            kd = M.beton === "g" ? (surGB ? 1 / 1.37 : surHyd ? 1 / 1.47 : 1 / 1.7) : M.beton === "bac" ? (surGB ? 1 / 1.07 : surHyd ? 1 / 1.37 : 1 / 1.7) : 1 / 1.7;
          }
        } else if (nf && M.kdBase !== undefined) {   // 5.2.5.3 : couche de base, ou les deux couches si interface collée
          const prec = audessus[audessus.length - 1];
          const colleeSousT4 = prec && MATERIAUX[prec.mat].T4 && prec.interface === "collee";
          if (!hydDessus || colleeSousT4) kd = M.kdBase;
        }
        const NE = val(ctx.NE, fam), ks = ksDe(bas);
        const adm = M.sig6 * Math.pow(NE / 1e6, -1 / M.invb) * M.kc * kd * kr(val(ctx.risque, "hydraulique"), M.invb, M.SN, M.Sh || 0.03) * ks;
        crit.push({ couche: i, mat: c.mat, type: "σt base", calc: sol[bas].sigma_t, adm, unite: "MPa", f: 1, kd, fatigue: true, k: bas, g: "sigma_t", NE, ks });
      } else if (M.fam === "non_lie" && haut > 0 && !(nf && souple && NEpf <= 250000)) {   // 8.2
        crit.push({ couche: i, mat: c.mat, type: "εz sommet", calc: sol[haut].eps_z, adm: A * Math.pow(NEpf, -0.222), unite: "µdef", f: 1e6, NE: NEpf });
      }
    });
    const kpf = mod.length - 1 - (opt && opt.degel > 0 ? 1 : 0);
    crit.push({ couche: -1, mat: ctx.pf, type: "εz plate-forme", calc: sol[kpf].eps_z, adm: A * Math.pow(NEpf, -0.222), unite: "µdef", f: 1e6, NE: NEpf });
    crit.forEach(k => { k.ratio = k.calc / k.adm; k.ok = k.ratio <= 1.0; });
    return { crit, ok: crit.every(k => k.ok), ratioMax: Math.max(...crit.map(k => k.ratio)), mod, sol };
  }

  function rechercherEpaisseur(couches, iVar, ctx, hmin, hmax) {
    hmin = hmin || 5; hmax = hmax || 60;
    const essai = (h) => verifier(couches.map((c, i) => (i === iVar ? Object.assign({}, c, { h_cm: h }) : c)), ctx);
    const rHi = essai(hmax);
    if (!rHi.ok) return { trouve: false, h: hmax, res: rHi, nEval: 1 };
    const rLo = essai(hmin); let n = 2;
    if (rLo.ok) return { trouve: true, h: hmin, res: rLo, nEval: n, minTechno: true };
    let lo = hmin, hi = hmax, best = rHi;
    while (hi - lo > 1) { const mid = Math.floor((lo + hi) / 2), r = essai(mid); n++; if (r.ok) { hi = mid; best = r; } else lo = mid; }
    return { trouve: true, h: hi, res: best, nEval: n };
  }

  /* Quantité de gel mécanique QM (6.2.1.5) : épaisseur e de couche dégelée (E_PF/10) majorant de 5 %
     la sollicitation du critère dimensionnant ; QM = e / 0,1. Nulle si couches liées <= 0,20 m. */
  function quantiteGelMecanique(couches, ctx) {
    const lie = couches.reduce((a, c) => a + (c.h_cm > 0 && MATERIAUX[c.mat].fam !== "non_lie" ? c.h_cm : 0), 0);
    if (lie <= 20) return { QM: 0, e: 0, motif: "couches liées ≤ 0,20 m" };
    const r0 = verifier(couches, ctx), F = r0.crit.filter(k => k.fatigue);
    if (!F.length) return { QM: 0, e: 0, motif: "pas de critère de fatigue" };
    const d = F.reduce((a, k) => (k.ratio > a.ratio ? k : a));
    const f = (e) => { const r = verifier(couches, ctx, { degel: e }); return r.crit.find(k => k.couche === d.couche && k.type === d.type).calc / d.calc; };
    const emax = 1.0;
    if (f(emax) < 1.05) return { QM: emax / 0.1, e: emax, critere: d.mat + " " + d.type, borne: true };
    let lo = 0, hi = emax;
    for (let it = 0; it < 14; it++) { const mid = (lo + hi) / 2; if (f(mid) < 1.05) lo = mid; else hi = mid; }
    return { QM: lo / 0.1, e: lo, critere: d.mat + " " + d.type };
  }

  // ---------------------------------------------------------------- TRAFIC
  const VOIES = {
    rd:  { nom: "Route hors agglomération à caractère de desserte (section courante)", nf: "desserte", cat: "pl" },
    transit: { nom: "Chaussée de transit (2 × 2 voies, autoroute)", nf: "transit", cat: "pl" },
    des: { nom: "Urbain — zone résidentielle, voie de desserte", nf: "resid", tmin: 0, tmax: 25, tminT: 0, tmaxT: 30, cam: [[0.1, 0.05, 0.4], [0.1, 0.05, 0.4]], risque: 25, A: 0.016 },
    dis: { nom: "Urbain — avenue, boulevard, voie de distribution", nf: "avenue", tmin: 25, tmax: 150, tminT: 20, tmaxT: 170, cam: [[0.1, 0.05, 0.6], [0.2, 0.1, 0.6]], risque: 25, A: 0.012 },
    pl:  { nom: "Urbain — voie principale à trafic lourd", nf: "lourd", tmin: 150, tmax: 750, tminT: 120, tmaxT: 1000, cam: [[0.2, 0.1, 0.8], [0.4, 0.2, 1.0]], risque: 5, A: 0.012 },
    bus: { nom: "Urbain — voie réservée aux bus", nf: "lourd", tmin: 0, tmax: 750, tminT: 0, tmaxT: 1000, cam: [[0.5, 0.2, 1.0], [0.5, 0.2, 1.0]], risque: 5, A: 0.012 },
    gdis:{ nom: "Giratoire sur voie de distribution", nf: "giratoire", cat: "dis", tmin: 25, tmax: 150, tminT: 20, tmaxT: 170, cam: [[0.5, 0.2, 1.0], [0.5, 0.2, 1.0]], risque: 5, A: 0.012 },
    gpl: { nom: "Giratoire sur voie principale ou route départementale", nf: "giratoire", cat: "pl", tmin: 150, tmax: 750, tminT: 120, tmaxT: 1000, cam: [[1.0, 0.5, 1.5], [1.0, 0.5, 1.5]], risque: 5, A: 0.012 },
    park:{ nom: "Parking, aire de stationnement", nf: "resid", tmin: 0, tmax: 750, tminT: 0, tmaxT: 1000, cam: [[0.1, 0.05, 0.4], [0.1, 0.05, 0.4]], risque: 25, A: 0.016 },
  };
  for (const k of ["rd", "transit"]) Object.assign(VOIES[k], { tmin: 0, tmax: 1e9, tminT: 0, tmaxT: 1e9, cam: VOIES.pl.cam, risque: 5, A: 0.012 });
  const CLASSES = [["T5", 25], ["T4", 50], ["T3-", 85], ["T3+", 150], ["T2-", 200], ["T2+", 300], ["T1-", 500], ["T1+", 750], ["T0-", 1200], ["T0+", 2000], ["TS-", 3000], ["TS+", 5000], ["TEX", Infinity]]; // tableau B.1
  const classeTrafic = (T) => CLASSES.find(c => T <= c[1])[0];   // bornes hautes incluses : 5 000 PL/j = TS+, TEX au-delà
  function camNorme(ctxVoie, T) {      // tableaux B.2, B.3, B.4
    if (ctxVoie === "transit") return { bitumineux: 0.8, hydraulique: 1.3, sol: 1.3, pf: 1, source: "tableau B.2" };
    if (ctxVoie === "resid") return { bitumineux: 0.1, hydraulique: 0.1, sol: 0.1, pf: 0.1, source: "tableau B.4" };
    if (ctxVoie === "avenue") return { bitumineux: 0.1, hydraulique: 0.2, sol: 0.2, pf: 0.2, source: "tableau B.4" };
    const cl = classeTrafic(T), j = cl === "T5" ? 0 : cl === "T4" ? 1 : cl === "T3-" ? 2 : cl === "T3+" ? 3 : 4;
    return { bitumineux: [0.3, 0.3, 0.4, 0.5, 0.5][j], hydraulique: [0.4, 0.5, 0.6, 0.6, 0.8][j], sol: [0.4, 0.5, 0.7, 0.7, 0.8][j], pf: [0.4, 0.5, 0.6, 0.75, 1][j], source: "tableau B.3" };
  }
  function risqueNorme(ctxVoie, T, beton) {   // tableaux B.7 et B.8, B.3.3.2.5
    if (ctxVoie === "resid") return { bitumineux: 25, hydraulique: 25, source: "tableau B.8" };
    if (ctxVoie === "avenue") return { bitumineux: 15, hydraulique: 15, source: "tableau B.8 (15 à 20 %)" };
    if (ctxVoie === "lourd") return { bitumineux: 5, hydraulique: 5, source: "tableau B.8" };
    if (ctxVoie === "giratoire") return { bitumineux: 5, hydraulique: 5, source: "B.3.3.2.5 (5 % maximum)" };
    const g = classeTrafic(T).replace(/[+-]/, ""), j = ["TEX", "TS", "T0", "T1", "T2", "T3", "T4", "T5"].indexOf(g);
    return { bitumineux: [1, 1, 2, 5, 12, 25, 30, 30][j], hydraulique: beton ? [1, 1, 2.8, 5, 7.5, 15, 25, 25][j] : [1, 1, 2.5, 5, 7.5, 12, 25, 25][j], source: "tableau B.7" };
  }
  const majorationGiratoire = (mat) => { const M = MATERIAUX[mat]; return M.fam === "bitumineux" ? 0.15 : (M.sol || /^S[CL]/.test(mat)) ? 0.15 : 0.10; }; // tableau B.5
  function traficCumule(T, n, tau) { return Math.round(365 * T * (n + tau * n * (n - 1) / 2)); }
  function NEarrondi(NE) { if (NE <= 0) return 0; const p = Math.pow(10, Math.floor(Math.log10(NE))); return Math.ceil(NE / p - 1e-9) * p; }

  // ---------------------------------------------------------------- GEL
  const STATIONS = [["Ambérieu","01",253,270,175,65],["Saint Quentin","02",98,225,110,45],["Vichy","03",249,250,115,45],["St-Auban","04",459,80,35,10],["Embrun","05",871,165,95,60],["Nice","06",5,0,0,0],["St-Girons","09",411,120,35,15],["Romilly sur Seine","10",77,210,110,35],["Carcassonne","11",126,85,35,10],["Millau","12",715,140,65,40],["Marignane","13",4,70,15,0],["Caen","14",64,115,60,25],["Cognac","16",30,100,35,15],["La Rochelle","17",4,75,30,10],["Bourges","18",161,160,70,30],["Ajaccio","20",4,0,0,0],["Dijon","21",222,200,130,65],["Rostrenen","22",262,85,50,10],["Besançon","25",307,220,120,70],["Lus-la-Croix-Haute","26",1059,420,275,160],["Montélimar","26",73,105,40,10],["Evreux","27",133,195,115,60],["Chartres","28",155,190,100,35],["Brest","29",96,20,10,0],["Nîmes","30",59,60,20,0],["Toulouse","31",148,115,40,10],["Bordeaux","33",46,95,40,10],["Montpellier","34",5,55,35,0],["Dinard","35",58,65,25,5],["Rennes","35",36,80,35,10],["Châteauroux","36",156,155,75,30],["Tours","37",108,120,75,35],["Grenoble","38",384,170,145,60],["Mont de Marsan","40",59,100,40,10],["Romorantin","41",84,135,100,30],["St-Etienne","42",400,220,110,60],["Le Puy","43",714,240,130,65],["Nantes","44",26,75,55,10],["Orléans","45",125,170,85,45],["Gourdon","46",259,120,45,20],["Agen","47",59,110,40,15],["Angers","49",57,100,70,15],["Cap de la Hague","50",3,15,5,0],["Reims","51",94,235,105,80],["Langres","52",464,325,170,110],["St-Dizier","52",139,235,100,65],["Nancy","54",212,320,155,90],["Bar le Duc","55",279,340,290,130],["Lorient","56",43,40,25,10],["Metz","57",190,290,135,75],["Château-Chinon","58",598,225,115,80],["Nevers","58",175,190,110,60],["Dunkerque","59",11,165,65,20],["Lille","59",47,250,90,55],["Beauvais","60",106,215,95,40],["Alençon","61",144,165,70,35],["Boulogne sur Mer","62",73,165,70,30],["Clermont-Ferrand","63",320,225,115,45],["Biarritz","64",69,40,10,0],["Pau","64",183,80,30,10],["Tarbes","65",360,95,35,10],["Perpignan","66",42,25,0,0],["Strasbourg","67",150,410,165,100],["Mulhouse-Bâle","68",267,415,155,105],["Lyon","69",200,220,110,45],["Tarare","69",831,275,155,95],["Luxeuil","70",272,335,165,110],["Mâcon","71",216,200,115,60],["Mont-St-Vincent","71",602,270,150,95],["Le Mans","72",51,120,70,25],["Bourg-St-Maurice","73",865,220,190,110],["Challes les Eaux","73",291,225,150,60],["Cap de la Hève","76",100,95,60,20],["Rouen","76",155,130,90,30],["Melun","77",91,185,90,50],["Abbeville","80",70,165,90,50],["Saint-Raphaël","83",2,25,0,0],["Toulon","83",24,15,0,0],["Orange","84",83,80,45,10],["Poitiers","86",117,130,65,25],["Limoges","87",403,160,80,30],["Auxerre","89",207,200,95,55],["Belfort","90",422,370,175,115],["Paris le Bourget","93",59,160,85,35]];

  const Q13 = (p) => (p <= 0.05 ? Infinity : p <= 0.25 ? 4 : p <= 1 ? 1 / p : 0);   // équation 13
  /* Méthode simplifiée de l’annexe H.3 (prédimensionnement, plus exigeante que le modèle thermique normalisé).
     g = {IR, kAgglo (1 | 0.9 | 0.8), hn_cm, An, hp_cm, pp, Ap, pg (pente du sol gélif ; Infinity = très gélif ; 0 = non gélif), QM} */
  function verifierGelNorme(couches, g) {
    const hn = (g.hn_cm || 0) / 100, hp = (g.hp_cm || 0) / 100;
    let Qg, config;
    if (hp > 0) {
      const X = g.Ap * hp * hp / (hp + 0.1), Qp = Math.min(4, 1 / g.pp);
      if (g.pg <= 0.05) { Qg = Q13(g.pp); config = "b (peu gélif seul)"; }
      else if (X >= Qp) { Qg = Qp; config = "c"; }
      else { Qg = g.pg > 1 ? X : Math.min(4, 1 / g.pg + (g.pg - g.pp) / g.pg * X); config = "c"; }   // équation 14
    } else { Qg = Q13(g.pg); config = Qg === Infinity ? "a" : "b"; }
    if (Qg === Infinity) return { horsGel: true, protege: true, config: "a" };
    const Qng = g.An * hn * hn / (hn + 0.1);                                           // équation 15
    const QPF = Qng + Qg + (g.QM || 0);                                                // équation 17
    let ah = 0, bh = 0;
    couches.forEach(c => { if (c.h_cm > 0) { const M = MATERIAUX[c.mat]; ah += M.ag * c.h_cm; bh += M.bg * c.h_cm; } });
    const IS = Math.pow((1 + ah) * QPF + bh, 2);                                       // équation H.9
    const IA = (IS / 0.7 + 10) / (g.kAgglo || 1);                                      // équations 21 à 23
    return { horsGel: false, config, Qg, Qng, QM: g.QM || 0, QPF, aH: 1 + ah, bH: bh, IS, IA, IR: g.IR, protege: g.IR <= IA };
  }
  /* Méthode Struct-Urb (référentiel CERTU) */
  function verifierGel(couches, g) {
    if (isFinite(g.pente) && g.pente <= 0.05) return { horsGel: true, protege: true };
    let aH = 1, bH = 0;
    couches.forEach(c => { const M = MATERIAUX[c.mat]; if (c.h_cm > 0) { aH += M.ag * c.h_cm; bH += M.bg * c.h_cm; } });
    const Qng = g.A * g.hn_cm * g.hn_cm / (g.hn_cm + 10);
    const p = isFinite(g.pente) ? g.pente : 2, Qg = p <= 0.25 ? 4 : p <= 1 ? 1 / p : 0;
    const Q = g.Qm + Qng + Qg, IA = 10 + Math.pow(aH * Q + bH, 2) / 0.6;
    return { horsGel: false, aH, bH, Qng, Qg, Qm: g.Qm, Q, IA, IR: g.IR, protege: g.IR <= IA };
  }

  root.Methode = { MATERIAUX, PLATEFORMES, REFERENTIELS, REF, setReferentiel, estNF, VOIES, STATIONS, CLASSES, classeTrafic, camNorme, risqueNorme, majorationGiratoire, kr, normInv, ShBitumineux, ksNorme, interfaceDefaut, estSouple, modeleMeca, verifier, rechercherEpaisseur, quantiteGelMecanique, traficCumule, NEarrondi, verifierGel, verifierGelNorme };
})(typeof module !== "undefined" ? (global.Burmister = require("./engine.js").Burmister, module.exports) : window);
