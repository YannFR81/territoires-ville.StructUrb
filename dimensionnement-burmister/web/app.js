/* Dimensionnement de chaussées — Burmister + Struct-Urb. Développé par YannFR81, agent territorial, et Claude, IA d’Anthropic, relu par Gemini Antigravity Hydrogen, IA de Google, 2026.
   Licence GNU GPL v3 (œuvre dérivée de Struct-Urb, CERTU/Cerema). Sans garantie. */
(function () {
  "use strict";
  const M = window.Methode, CAT = window.CATALOGUE;
  const $ = (id) => document.getElementById(id);
  const fmt = (x, d = 0) => (x == null || !isFinite(x) ? "—" : x.toLocaleString("fr-FR", { minimumFractionDigits: d, maximumFractionDigits: d }));
  const NON_STRUCT = ["ES", "Pavés", "Dalles"];
  const nf = () => M.estNF();
  const matOK = (s) => (s.base in M.MATERIAUX) && (s.fond === "Aucune" || s.fond in M.MATERIAUX);
  const voie = () => M.VOIES[$("voie").value];
  const voieCat = () => voie().cat || $("voie").value;        // type de voie Struct-Urb servant au filtre du catalogue
  const ctxNF = () => (["lourd", "giratoire"].includes(voie().nf) ? "desserte" : voie().nf);

  let couches = [], dernier = null, cleNF = "";

  // ------------------------------------------------------------ listes
  for (const [k, v] of Object.entries(M.VOIES)) $("voie").add(new Option(v.nom, k));
  $("voie").value = "rd";
  M.STATIONS.forEach((s, i) => $("station").add(new Option(`${s[0]} (${s[1]}) — ${s[2]} m`, i)));
  $("station").value = String(M.STATIONS.findIndex(s => s[0] === "Toulouse"));

  function remplirStructures() {
    const v = voieCat(), sel = $("struct"), prev = sel.value;
    sel.innerHTML = "";
    CAT.filter(s => s.use.includes(v) && matOK(s)).forEach(s => {
      const fam = { 1: "souple", 2: "bitumineuse épaisse", 3: "semi-rigide", 4: "béton", 5: "mixte", 6: "pavés/dalles" }[s.typ] || "";
      sel.add(new Option(`${s.nom} — ${fam} (NE ${fmt(s.NEmin)} à ${fmt(s.NEmax)})`, s.uid));
    });
    sel.add(new Option("Structure libre (sans référence catalogue)", "libre"));
    if ([...sel.options].some(o => o.value === prev)) sel.value = prev;
  }
  const structure = () => CAT.find(s => String(s.uid) === $("struct").value) || null;   // uid : l’index du catalogue CERTU n’est pas unique

  // ------------------------------------------------------------ trafic / NE
  function etatTrafic() {
    const v = voie(), T = +$("T").value, n = +$("n").value, tau = +$("tau").value / 100;
    const TC = $("loi").value === "geom" ? Math.round(365 * T * (tau > 0 ? (Math.pow(1 + tau, n) - 1) / tau : n)) : M.traficCumule(T, n, tau);
    $("TC").textContent = fmt(TC);
    $("classe").textContent = `Classe de trafic ${M.classeTrafic(T)} (tableau B.1)`;
    let msg = "";
    if (v.tmax < 1e9) {
      if (T < v.tminT || T > v.tmaxT) msg = `<div class="msg warn">Trafic hors du domaine du catalogue Struct-Urb pour ce type de voie (${v.tmin} à ${v.tmax} PL/j, toléré ${v.tminT} à ${v.tmaxT}).</div>`;
      else if (T < v.tmin || T > v.tmax) msg = `<div class="msg info">Trafic dans la zone de tolérance du catalogue Struct-Urb (${v.tmin} à ${v.tmax} PL/j).</div>`;
    }
    $("msgT").innerHTML = msg;
    return { TC, T, n, tau };
  }
  function camPreco() {
    const s = structure(), v = M.VOIES[voieCat()];
    if (!s) return null;
    let [p, mn, mx] = v.cam[s.cam - 1];
    if (s.typ === 1 || (s.typ === 6 && s.base === "GNT")) p *= 2;
    return { p, mn, mx };
  }
  const aBeton = () => couches.some(x => M.MATERIAUX[x.mat] && M.MATERIAUX[x.mat].beton);
  function remplirNF(force) {              // CAM et risques de l’annexe B, mis à jour quand la voie ou la classe change
    if (!nf()) return;
    const T = +$("T").value, cle = [$("voie").value, M.classeTrafic(T), aBeton()].join("|");
    if (cle === cleNF && !force) return;
    cleNF = cle;
    const c = M.camNorme(ctxNF(), T), r = M.risqueNorme(voie().nf, T, aBeton());
    $("camB").value = c.bitumineux; $("camH").value = c.hydraulique; $("camS").value = c.sol; $("camP").value = c.pf;
    $("camNFHint").textContent = `Valeurs du ${c.source}${ctxNF() === "desserte" && voie().nf !== "desserte" ? " (CAM des chaussées à caractère de desserte)" : ""} pour la classe ${M.classeTrafic(T)} — indicatives, modifiables.`;
    $("rB").value = r.bitumineux; $("rH").value = r.hydraulique;
    $("rHint").textContent = `${r.source}, classe ${M.classeTrafic(T)} — choix du maître d’ouvrage.`;
  }
  function etatNE() {
    const { TC } = etatTrafic();
    remplirNF(false);
    const s = structure();
    let msg = "", out;
    if (nf()) {
      const NE = { bitumineux: TC * +$("camB").value, hydraulique: TC * +$("camH").value, sol: TC * +$("camS").value, pf: TC * +$("camP").value };
      $("NE").textContent = `bitumineux ${fmt(NE.bitumineux)} · MTLH et béton ${fmt(NE.hydraulique)} · plate-forme et GNT ${fmt(NE.pf)}`;
      out = { NE, NEr: NE };
      if (voie().nf === "giratoire") msg += `<div class="msg info">Giratoire : trafic = demi-somme des trafics entrants (au moins celui de la branche la plus chargée), CAM de la section courante, risque de 5 % au plus, puis majoration des épaisseurs d’assise (B.1.2.2, B.2.4, B.3.3.2.5).</div>`;
    } else {
      const NE = TC * +$("cam").value, NEr = $("arrondi").checked ? M.NEarrondi(NE) : Math.round(NE);
      $("NE").textContent = `${fmt(NE)} calculé · ${fmt(NEr)} retenu`;
      out = { NE, NEr };
      if (NEr > 1e7) msg += `<div class="msg err">NE supérieur à 10 millions : hors domaine Struct-Urb.</div>`;
      if (s && s.typ === 1) msg += `<div class="msg warn">Chaussée souple : le catalogue CERTU est en partie empirique pour ces structures ; le calcul donne des épaisseurs plus fortes.</div>`;
      if ($("Q").value === "Q2") msg += `<div class="msg info">Chantier difficile (Q2) : Struct-Urb majore ses épaisseurs d’après des tables, sans formule publiée. Le calcul est fait en conditions standard ; comparer à l’épaisseur catalogue Q2 affichée.</div>`;
    }
    const nr = neRef(out);
    if (s && (nr < s.NEmin || nr > s.NEmax)) msg += `<div class="msg info">NE hors du domaine de la structure type du catalogue (${fmt(s.NEmin)} à ${fmt(s.NEmax)}) : pas d’épaisseur catalogue de référence.</div>`;
    if (s && NON_STRUCT.includes(s.surf)) msg += `<div class="msg info">Revêtement ${s.surf} : non pris en compte dans le calcul mécanique.</div>`;
    $("msgS").innerHTML = msg;
    return out;
  }
  function neRef(ne) {                       // NE servant à lire l’épaisseur de référence du catalogue
    if (!nf()) return ne.NEr;
    const s = structure(), Mb = s && M.MATERIAUX[s.base];
    return Math.round(ne.NE[!Mb ? "bitumineux" : Mb.fam === "non_lie" ? "pf" : Mb.fam]);
  }
  function ligneCatalogue(s, NEr, Q) {
    if (!s) return null;
    const k = s.NE.findIndex(x => x >= NEr);
    if (k < 0 || NEr < s.NEmin) return null;
    const t = s.T[$("pf").value + (Q || $("Q").value)];
    if (!t) return null;
    const r = t[k];
    if (!r || r.slice(0, 5).every(x => x === 0)) return null;
    return { NE: s.NE[k], surf: r[0], base: r[1] + r[2], base1: r[1], base2: r[2], fond: r[3] + r[4], Qm: r[5] };
  }

  // ------------------------------------------------------------ couches
  function c(mat, h, variable) {
    const Mx = M.MATERIAUX[mat];
    return { mat, h_cm: h, verifier: Mx.fam !== "non_lie" && !Mx.roulement, variable: !!variable, interface: "collee" };
  }
  const interfacesDefaut = (arr) => arr.forEach((x, i) => x.interface = M.interfaceDefaut(x.mat, arr[i + 1] && arr[i + 1].mat));
  function chargerDepuisCatalogue() {
    const s = structure();
    if (!s) {
      couches = couches.filter(x => x.mat in M.MATERIAUX);
      if (!couches.length) couches = [c("BBSG", 6), c("GB3", 20, true)];
      if (!couches.some(x => x.variable)) couches[Math.min(1, couches.length - 1)].variable = true;
      dessinerCouches(); return;
    }
    const L = ligneCatalogue(s, neRef(etatNE()), "Q1"), arr = [];
    if (s.surf === "Enrobés") arr.push(c("BBSG", L ? L.surf : 6));
    const memeBitume = s.fond === s.base && M.MATERIAUX[s.base].fam === "bitumineux";   // base + fondation bitumineuses : une seule assise collée
    arr.push(c(s.base, L ? L.base + (memeBitume ? L.fond : 0) : 20, true));
    if (s.fond !== "Aucune" && !memeBitume) arr.push(c(s.fond, L && L.fond ? L.fond : (s.fond === "GNT" ? 25 : 18)));
    interfacesDefaut(arr);
    couches = arr;
    if (L) $("Qm").value = L.Qm;
    dessinerCouches();
  }
  function dessinerCouches() {
    const tb = $("couches").querySelector("tbody");
    tb.innerHTML = "";
    couches.forEach((x, i) => {
      const tr = document.createElement("tr"), Mx = M.MATERIAUX[x.mat];
      const opts = Object.entries(M.MATERIAUX).map(([k, m]) => `<option value="${k}" title="${m.nom}"${k === x.mat ? " selected" : ""}>${k} — ${m.nom}</option>`).join("");
      const itf = [["collee", "collée"], ["semi", "semi-collée"], ["glissante", "glissante"]].map(([k, l]) => `<option value="${k}"${k === x.interface ? " selected" : ""}>${l}</option>`).join("");
      const sansVerif = Mx.fam === "non_lie" || (nf() && Mx.roulement);
      tr.innerHTML = `<td><select data-k="mat" style="max-width:150px">${opts}</select></td>
        <td class="num"><input data-k="h_cm" type="number" min="1" max="80" value="${x.h_cm}" style="width:58px"></td>
        <td><select data-k="interface">${itf}</select></td>
        <td style="text-align:center"><input data-k="verifier" type="checkbox"${x.verifier && !sansVerif ? " checked" : ""}${sansVerif ? " disabled" : ""}></td>
        <td style="text-align:center"><input name="var" data-k="variable" type="radio"${x.variable ? " checked" : ""}></td>
        <td><button class="small" data-del="${i}" title="Supprimer">×</button></td>`;
      tr.querySelectorAll("[data-k]").forEach(el => el.addEventListener("change", () => {
        const k = el.dataset.k;
        if (k === "variable") couches.forEach((y, j) => y.variable = j === i);
        else if (k === "verifier") x.verifier = el.checked;
        else if (k === "h_cm") x.h_cm = Math.max(0, Math.round(+el.value));
        else if (k === "mat") { x.mat = el.value; const m = M.MATERIAUX[x.mat]; x.verifier = m.fam !== "non_lie" && !m.roulement; interfacesDefaut(couches); dessinerCouches(); remplirNF(false); etatNE(); }
        else x[k] = el.value;
      }));
      tr.querySelector("[data-del]").addEventListener("click", () => { couches.splice(i, 1); if (!couches.some(y => y.variable) && couches[0]) couches[couches.length > 1 ? 1 : 0].variable = true; interfacesDefaut(couches); dessinerCouches(); });
      tb.appendChild(tr);
    });
    $("solBox").style.display = nf() && couches.some(x => M.MATERIAUX[x.mat].saisie) ? "" : "none";
    $("gntHint").textContent = nf()
      ? "Plate-forme sous la dernière couche, interface collée. GNT (tableaux D.1 et D.2) : sous une assise bitumineuse, E = min(3 × E dessous ; 360 MPa) ; en chaussée souple, couche de base à Emax et fondation en sous-couches de 25 cm selon la catégorie CG1 à CG3. Les couches de roulement et de liaison ne sont pas vérifiées en fatigue (D.3.4)."
      : "Plate-forme sous la dernière couche, interface collée. GNT découpée en sous-couches de 25 cm au plus, E = min(3 × E dessous ; 600 MPa).";
  }

  // ------------------------------------------------------------ calcul
  function contexte() {
    const ne = etatNE();
    return nf() ? { NE: ne.NE, risque: { bitumineux: +$("rB").value, hydraulique: +$("rH").value }, pf: $("pf").value }
      : { NE: ne.NEr, risque: +$("risque").value, pf: $("pf").value, Afatigue: +$("A").value };
  }
  function lancer(recherche) {
    if (!couches.length) return;
    const ctx = contexte(), nepf = typeof ctx.NE === "object" ? ctx.NE.pf : ctx.NE;
    if (!(nepf > 0)) { $("res").innerHTML = `<div class="msg err">NE nul : vérifier le trafic et le CAM.</div>`; return; }
    ["go", "check"].forEach(id => $(id).disabled = true);
    $("res").innerHTML = `<div class="msg info">Calcul en cours…</div>`;
    setTimeout(() => {
      const t0 = performance.now();
      try {
        let out;
        if (recherche) {
          const iv = couches.findIndex(x => x.variable);
          if (iv < 0) throw new Error("Aucune couche variable sélectionnée (colonne Var.).");
          const Mv = M.MATERIAUX[couches[iv].mat];
          const hmin = Mv.fam === "bitumineux" ? 6 : Mv.fam === "non_lie" ? 10 : Mv.beton ? 12 : Mv.sol ? 20 : 15;
          const r = M.rechercherEpaisseur(couches, iv, ctx, hmin, 60);
          if (r.trouve) couches[iv].h_cm = r.h;
          out = { recherche: true, iv, r, res: r.res };
          dessinerCouches();
        } else out = { recherche: false, res: M.verifier(couches, ctx) };
        if (nf()) out.gelM = M.quantiteGelMecanique(couches, ctx);
        out.ms = performance.now() - t0; out.ctx = ctx;
        dernier = out;
        afficherResultat(out);
        calculerGel();
      } catch (e) { $("res").innerHTML = `<div class="msg err">${e.message}</div>`; }
      ["go", "check"].forEach(id => $(id).disabled = false);
    }, 30);
  }

  const COUL = { bitumineux: "#3b3b3b", hydraulique: "#9aa5ad", non_lie: "#c9a46b", beton: "#bfc6cc" };
  function carotte(cs, pf) {
    const tot = cs.reduce((a, x) => a + x.h_cm, 0), k = Math.min(6, 220 / Math.max(tot, 1));
    let y = 10, g = "";
    cs.forEach(x => {
      const Mx = M.MATERIAUX[x.mat], h = x.h_cm * k, col = Mx.beton ? COUL.beton : COUL[Mx.fam];
      g += `<rect x="10" y="${y}" width="110" height="${h}" fill="${col}" stroke="#fff"/>`;
      if (h >= 11) g += `<text x="65" y="${y + h / 2 + 4}" text-anchor="middle" font-size="11" fill="${Mx.fam === "bitumineux" ? "#fff" : "#1f2328"}">${x.mat} ${x.h_cm} cm</text>`;
      else g += `<text x="128" y="${y + h / 2 + 4}" font-size="11" fill="#1f2328">${x.mat} ${x.h_cm} cm</text>`;
      y += h;
    });
    g += `<rect x="10" y="${y}" width="110" height="22" fill="#e9dcc6"/><text x="65" y="${y + 15}" text-anchor="middle" font-size="11">${pf === "PF2+" ? "PF2qs" : pf} (${M.PLATEFORMES[pf].E} MPa)</text>`;
    return `<svg width="210" height="${y + 34}" viewBox="0 0 210 ${y + 34}" role="img" aria-label="Coupe de la structure">${g}<text x="10" y="${y + 33}" font-size="10" fill="#8a929a">Total : ${tot} cm</text></svg>`;
  }
  function notesStructure(o) {
    const notes = [], fams = couches.filter(x => x.h_cm > 0).map(x => M.MATERIAUX[x.mat]);
    const iBit = fams.findIndex(m => m.fam === "bitumineux" && !m.roulement), iHyd = fams.findIndex(m => m.fam === "hydraulique" && !m.beton), iGnt = fams.findIndex(m => m.fam === "non_lie");
    if (iBit >= 0 && iHyd > iBit && !(iGnt > iBit && iGnt < iHyd)) notes.push("<b>Structure mixte</b> : la norme impose un calcul en deux phases (8.6 : couche traitée intacte, puis module divisé par 5 et interface glissante). L’outil ne fait que la première phase : résultat indicatif.");
    if (iGnt >= 0 && iHyd > iGnt && iBit >= 0 && iBit < iGnt) notes.push("<b>Structure inverse</b> : la valeur admissible majorée de 20 % sur la GNT (8.7) et son module Emax ne sont pas appliqués : résultat indicatif.");
    if (nf() && voie().nf === "giratoire") {
      const liste = couches.filter(x => x.h_cm > 0 && x.verifier).map(x => `${x.mat} ${x.h_cm} → ${Math.ceil(x.h_cm * (1 + M.majorationGiratoire(x.mat)) - 1e-9)} cm`);
      if (liste.length) notes.push(`<b>Giratoire</b> — majoration des épaisseurs d’assise (tableau B.5) : ${liste.join(" ; ")}.`);
    }
    couches.forEach(x => {
      const Mx = M.MATERIAUX[x.mat];
      if (Mx.fam === "bitumineux" && !Mx.roulement && x.h_cm > 16) notes.push(`${x.mat} ${x.h_cm} cm : à mettre en œuvre en ${Math.ceil(x.h_cm / 16)} couches collées (F.1.3 : 8 à 16 cm par couche de GB, 6 à 15 cm pour l’EME).`);
      if (Mx.fam === "hydraulique" && !Mx.beton && x.h_cm > 32) notes.push(`${x.mat} ${x.h_cm} cm : plus de 32 cm, donc deux couches (F.1.2) ; recalculer avec base + fondation et leur interface.`);
      if (Mx.fam === "hydraulique" && !Mx.beton && x.h_cm > 0 && x.h_cm < (Mx.sol ? 20 : 15)) notes.push(`${x.mat} ${x.h_cm} cm : sous l’épaisseur minimale de ${Mx.sol ? 20 : 15} cm (F.1.2).`);
      if (Mx.nonCale) notes.push(`${x.mat} : paramètres de fatigue non recalés sur le catalogue.`);
      if (Mx.cale) notes.push(`${x.mat} : ${Mx.cale}.`);
      if (Mx.saisie) notes.push(`${x.mat} : E = ${fmt(Mx.E)} MPa et σ6 = ${fmt(Mx.sig6, 2)} MPa saisis (pas de valeur de référence dans la norme).`);
    });
    if (nf() && iGnt >= 0 && fams.slice(0, iGnt).some(m => m.fam === "hydraulique")) notes.push("GNT sous une couche traitée aux liants hydrauliques ou en béton : cas non prévu par le tableau D.1 ; module pris au plus faible des tableaux D.1 et D.2, soit k = min(3 ; k de la catégorie) et Emax = min(360 MPa ; Emax de la catégorie).");
    if (nf() && fams.some(m => m.beton && m.beton !== "fond")) notes.push("Béton en couche de base-roulement : Sh = 0,03 m retenu ; le tableau D.13 admet 0,02 ou 0,01 m selon le matériel de mise en œuvre.");
    if (nf() && couches.some((x, i) => x.h_cm > 0 && x.interface === "collee" && M.MATERIAUX[x.mat].fam === "hydraulique" && !M.MATERIAUX[x.mat].beton && couches[i + 1] && M.MATERIAUX[couches[i + 1].mat].fam === "hydraulique" && !M.MATERIAUX[couches[i + 1].mat].beton)) notes.push("Couches traitées collées entre elles : critère vérifié à la base de l’assise seulement (8.5.2).");
    const kdB = o.res.crit.find(k => k.kd !== undefined && Math.abs(k.kd - 1) > 1e-9);
    if (kdB) notes.push(`kd = 1/${fmt(1 / kdB.kd, 2)} appliqué à ${kdB.mat}${nf() ? " (tableau D.12 ou D.2.4), sous réserve des surlargeurs de l’annexe F" : ""}.`);
    return [...new Set(notes)];
  }
  function afficherResultat(o) {
    const r = o.res, s = structure(), nr = neRef({ NE: o.ctx.NE, NEr: o.ctx.NE });
    const L1 = ligneCatalogue(s, nr, "Q1"), L2 = ligneCatalogue(s, nr, "Q2");
    let h = "";
    if (o.recherche) {
      const cv = couches[o.iv];
      h += o.r.trouve
        ? `<div class="verdict ok">Épaisseur minimale de ${cv.mat} : ${o.r.h} cm${o.r.minTechno ? " (minimum imposé par la recherche)" : ""}</div>`
        : `<div class="verdict ko">Aucune épaisseur ≤ 60 cm de ${cv.mat} ne suffit : changer de structure ou de plate-forme.</div>`;
    } else h += `<div class="verdict ${r.ok ? "ok" : "ko"}">${r.ok ? "Structure vérifiée" : "Structure insuffisante"} — taux de travail maximal ${fmt(r.ratioMax * 100)} %</div>`;
    h += `<div class="flex"><div>${carotte(couches, o.ctx.pf)}</div><div style="flex:1;min-width:300px">`;
    h += `<table><thead><tr><th>Couche</th><th>Critère</th><th class="num">Calculé</th><th class="num">Admissible</th><th class="num">NE</th><th class="num">Taux</th><th></th></tr></thead><tbody>`;
    r.crit.forEach(k => {
      const d = k.f > 1 ? 1 : 3, pc = Math.min(k.ratio, 1.5) / 1.5 * 100, col = k.ok ? "var(--vt)" : "var(--ko)";
      h += `<tr><td>${k.mat === "PF2+" ? "PF2qs" : k.mat}</td><td>${k.type}</td><td class="num">${fmt(k.calc * k.f, d)}</td><td class="num">${fmt(k.adm * k.f, d)} ${k.unite}</td><td class="num">${fmt(k.NE / 1e6, 2)} M</td>
        <td class="num ${k.ok ? "ok" : "ko"}">${fmt(k.ratio * 100)} %</td><td><div class="bar"><i style="width:${pc}%;background:${col}"></i></div></td></tr>`;
    });
    h += `</tbody></table>`;
    const rq = typeof o.ctx.risque === "object" ? `risque ${o.ctx.risque.bitumineux} % (bitumineux) et ${o.ctx.risque.hydraulique} % (MTLH, béton)` : `risque ${o.ctx.risque} %`;
    h += `<div class="hint">${M.REFERENTIELS[M.REF.cle].court} · ${rq} · ${o.ctx.pf === "PF2+" ? "PF2qs" : o.ctx.pf} · modules du modèle (MPa) : ${r.mod.map(m => fmt(m.E)).join(" / ")} · ${fmt(o.ms)} ms</div>`;
    if (s) {
      const f = (L) => L ? `surface ${L.surf} cm · ${s.base} ${L.base2 ? L.base1 + " + " + L.base2 : L.base} cm${L.fond ? " · " + s.fond + " " + L.fond + " cm" : ""}` : "pas de valeur pour ce NE / cette plate-forme";
      h += `<h3 style="font-size:13px;margin:12px 0 4px">Pour comparaison : catalogue Struct-Urb (${s.nom}, NE ${L1 ? fmt(L1.NE) : "—"})</h3>
        <table><tr><td>Q1 standard</td><td>${f(L1)}</td></tr><tr><td>Q2 difficile</td><td>${f(L2)}</td></tr></table>`;
    }
    const notes = notesStructure(o);
    if (notes.length) h += `<div class="msg info" style="margin-top:8px">${notes.join("<br>")}</div>`;
    h += `</div></div>`;
    $("res").innerHTML = h;
  }

  // ------------------------------------------------------------ gel
  function IRstation() {
    if ($("IRperso").checked) return +$("IRval").value;
    return M.STATIONS[+$("station").value][+$("hiver").value];
  }
  function lirePente() {
    const t = $("pente").value.trim().replace(",", ".");
    if (t === "" || t === "∞" || /inf/i.test(t)) return Infinity;
    return +t;
  }
  function calculerGel() {
    const IR0 = IRstation(), kA = +$("agglo").value;
    $("IR").textContent = nf() ? fmt(IR0) : fmt(Math.round(IR0 * kA));
    $("gelBanner").innerHTML = nf()
      ? "Méthode simplifiée de l’annexe H.3 de la norme, prévue pour le prédimensionnement : elle est plus exigeante que le modèle thermique normalisé (6.2.2), qui n’est pas programmé ici. La quantité de gel mécanique Q<sub>M</sub> est calculée (6.2.1.5)."
      : "Méthode du logiciel Struct-Urb : Qm tabulé par le CERTU, correction d’agglomération appliquée à IR.";
    if (!dernier) return;
    let h;
    if (nf()) {
      const sol = $("sol").value, pg = sol === "ng" ? 0 : sol === "tg" ? Infinity : lirePente();
      const gm = dernier.gelM || { QM: 0 };
      const g = M.verifierGelNorme(couches, { IR: IR0, kAgglo: kA, hn_cm: +$("hn").value || 0, An: +$("An").value, hp_cm: +$("hp").value || 0, pp: +$("pp").value || 0.4, Ap: +$("Ap").value, pg, QM: gm.QM });
      if (g.horsGel) h = `<div class="verdict ok">Support non gélif (configuration a) : vérification au gel acquise.</div>`;
      else {
        h = `<div class="verdict ${g.protege ? "ok" : "ko"}">${g.protege ? "Chaussée protégée au gel" : "Chaussée non protégée au gel"} — IR ${fmt(IR0)} ${g.protege ? "≤" : ">"} IA ${fmt(g.IA)} °C·j</div>
        <table><tr><td>Qg (sol gélif, éq. 13-14)</td><td class="num">${fmt(g.Qg, 2)}</td><td>Qng (non gélif, éq. 15)</td><td class="num">${fmt(g.Qng, 2)}</td></tr>
        <tr><td>Q<sub>M</sub> (mécanique, éq. 16)</td><td class="num">${fmt(g.QM, 2)}</td><td>Q<sub>PF</sub> (éq. 17)</td><td class="num">${fmt(g.QPF, 2)}</td></tr>
        <tr><td>IS (éq. H.9)</td><td class="num">${fmt(g.IS)}</td><td>IA = (IS / 0,7 + 10)${kA < 1 ? " / " + fmt(kA, 1) : ""}</td><td class="num">${fmt(g.IA)}</td></tr></table>
        <div class="hint">Configuration ${g.config} du support. Q<sub>M</sub> : ${gm.motif ? gm.motif + ", donc nul" : `couche dégelée e = ${fmt(gm.e * 100, 1)} cm majorant de 5 % le critère « ${gm.critere} »${gm.borne ? " (bornée à 1 m)" : ""}`}.</div>`;
        if (!g.protege) h += `<div class="msg warn">Pistes : épaissir la couche de forme non gélive ou la chaussée, ou retenir un autre hiver de référence si le maître d’ouvrage l’accepte (barrières de dégel).</div>`;
      }
    } else {
      const IR = Math.round(IR0 * kA);
      const g = M.verifierGel(couches, { IR, Qm: +$("Qm").value || 0, hn_cm: +$("hn").value || 0, A: +$("Acf").value, pente: lirePente() });
      if (g.horsGel) h = `<div class="verdict ok">Sol support non gélif : chaussée hors gel.</div>`;
      else h = `<div class="verdict ${g.protege ? "ok" : "ko"}">${g.protege ? "Chaussée protégée au gel" : "Chaussée non protégée au gel"} — IR ${fmt(IR)} ${g.protege ? "≤" : ">"} IA ${fmt(g.IA)} °C·j</div>
        <table><tr><td>Qm (mécanique)</td><td class="num">${fmt(g.Qm, 2)}</td><td>Qng (couche de forme non gélive)</td><td class="num">${fmt(g.Qng, 2)}</td></tr>
        <tr><td>Qg (sol support)</td><td class="num">${fmt(g.Qg, 2)}</td><td>Q total</td><td class="num">${fmt(g.Q, 2)}</td></tr></table>`;
    }
    $("gel").innerHTML = h;
  }

  // ------------------------------------------------------------ note de calcul
  function note() {
    if (!dernier) return "Aucun calcul.";
    const o = dernier, s = structure(), tr = etatTrafic();
    const lignes = [
      "NOTE DE CALCUL — PRÉDIMENSIONNEMENT DE CHAUSSÉE (solveur de Burmister vérifié sur les cas tests de l’annexe I de la NF P98-086 ; outil non certifié)",
      `Référentiel : ${M.REFERENTIELS[M.REF.cle].nom}`,
      `Voie : ${voie().nom} — TMJA ${tr.T} PL/j (classe ${M.classeTrafic(tr.T)}), ${tr.n} ans, ${tr.tau * 100} %/an (croissance ${$("loi").value === "geom" ? "géométrique" : "arithmétique"}) → ${fmt(tr.TC)} PL cumulés`,
      nf() ? `CAM : bitumineux ${$("camB").value}, MTLH et béton ${$("camH").value}, sols traités ${$("camS").value}, plate-forme et GNT ${$("camP").value} — risque : bitumineux ${$("rB").value} %, MTLH et béton ${$("rH").value} %`
           : `CAM ${$("cam").value} → NE retenu ${fmt(o.ctx.NE)} — risque ${o.ctx.risque} % — A = ${o.ctx.Afatigue}`,
      `Plate-forme ${o.ctx.pf === "PF2+" ? "PF2qs" : o.ctx.pf} (${M.PLATEFORMES[o.ctx.pf].E} MPa) — structure type : ${s ? s.nom : "libre"}`,
      "Couches : " + couches.map(x => `${x.mat} ${x.h_cm} cm (E ${fmt(M.MATERIAUX[x.mat].E)} MPa, interface ${x.interface})`).join(" / "),
      ...o.res.crit.map(k => `  ${k.mat} ${k.type} : ${fmt(k.calc * k.f, k.f > 1 ? 1 : 3)} / ${fmt(k.adm * k.f, k.f > 1 ? 1 : 3)} ${k.unite} (NE ${fmt(k.NE)}) → ${fmt(k.ratio * 100)} % ${k.ok ? "OK" : "NON"}`),
      ...notesStructure(o).map(t => "  Remarque : " + t.replace(/<[^>]+>/g, "")),
    ];
    const gel = $("gel").innerText.replace(/\s*\n+\s*/g, " ").trim();
    if (gel) lignes.push(`Gel (${nf() ? "annexe H.3, méthode simplifiée" : "méthode Struct-Urb"}) : ` + gel);
    return lignes.join("\n");
  }

  // ------------------------------------------------------------ évènements
  const REF_HINT = {
    nf2019: "Matériaux de l’annexe D (BBSG 2-3 : 7 000 MPa ; GB3 : 9 000 MPa, ε6 90 ; GC3 : b = −1/15, kd = 1…), ks du tableau C.2, CAM et risques de l’annexe B, interfaces du chapitre 8, points de calcul à l’axe de roue et au centre du jumelage.",
    certu: "Paramètres de la méthode de 1994 recalés sur le catalogue Struct-Urb (BBSG 5 400 MPa, PF2qs : ks = 1, CAM et risques du logiciel). Sert à retrouver les épaisseurs du catalogue.",
  };
  function appliquerSol() {
    for (const k of ["SolT", "SolS", "SolG"]) if (M.MATERIAUX[k]) { M.MATERIAUX[k].E = +$("solE").value || 12000; M.MATERIAUX[k].sig6 = +$("solS6").value || 0.5; }
  }
  function surVoieOuStructure(rechargeCouches) {
    const v = M.VOIES[voieCat()], s = structure();
    $("A").value = String(v.A);
    $("risque").value = s && s.risque > 0 ? s.risque : v.risque;
    const cp = camPreco();
    if (cp) { $("cam").value = cp.p; $("camHint").textContent = `Préconisé ${fmt(cp.p, 2)} (plage ${fmt(cp.mn, 2)} à ${fmt(cp.mx, 2)})`; }
    else { if (!$("cam").value) $("cam").value = 0.5; $("camHint").textContent = "Structure libre : CAM à choisir"; }
    if (rechargeCouches) chargerDepuisCatalogue();
    remplirNF(true);
    etatNE();
  }
  function changerReferentiel() {
    const cle = $("ref").value;
    M.setReferentiel(cle); appliquerSol();
    document.body.dataset.ref = cle;
    $("refHint").textContent = REF_HINT[cle];
    $("loi").value = cle === "nf2019" ? "geom" : "arith"; $("arrondi").checked = cle !== "nf2019";
    remplirStructures();
    dernier = null;
    surVoieOuStructure(true);
    $("res").innerHTML = `<div class="msg info">Renseigne le trafic et la structure, puis lance le calcul.</div>`;
    $("gel").innerHTML = `<div class="msg info">Le gel est vérifié après le calcul mécanique, avec les épaisseurs retenues.</div>`;
    calculerGel();
  }
  $("ref").addEventListener("change", changerReferentiel);
  $("voie").addEventListener("change", () => { remplirStructures(); surVoieOuStructure(true); });
  $("struct").addEventListener("change", () => surVoieOuStructure(true));
  ["T", "n", "tau", "cam", "Q", "loi", "arrondi", "camB", "camH", "camS", "camP"].forEach(id => { $(id).addEventListener("input", etatNE); $(id).addEventListener("change", etatNE); });
  $("Q").addEventListener("change", () => { const L = ligneCatalogue(structure(), neRef(etatNE())); if (L) $("Qm").value = L.Qm; calculerGel(); });
  $("pf").addEventListener("change", () => { chargerDepuisCatalogue(); etatNE(); });
  ["solE", "solS6"].forEach(id => $(id).addEventListener("input", appliquerSol));
  $("reload").addEventListener("click", chargerDepuisCatalogue);
  $("add").addEventListener("click", () => { couches.push(c("GNT", 25)); interfacesDefaut(couches); dessinerCouches(); });
  $("go").addEventListener("click", () => lancer(true));
  $("check").addEventListener("click", () => lancer(false));
  $("copy").addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(note()); $("copy").textContent = "Note copiée ✓"; }
    catch (e) { $("copy").textContent = "Copie refusée par le navigateur"; }
    setTimeout(() => $("copy").textContent = "Copier la note de calcul", 2000);
  });
  $("IRperso").addEventListener("change", () => { $("IRval").disabled = !$("IRperso").checked; if ($("IRperso").checked && !$("IRval").value) $("IRval").value = IRstation(); calculerGel(); });
  $("sol").addEventListener("change", () => { $("pente").value = { tg: "∞", pg: "0.4", ng: "0" }[$("sol").value]; calculerGel(); });
  ["station", "hiver", "agglo", "IRval", "hn", "Acf", "pente", "Qm", "An", "hp", "pp", "Ap"].forEach(id => { $(id).addEventListener("input", calculerGel); $(id).addEventListener("change", calculerGel); });

  $("ref").value = "nf2019";
  changerReferentiel();
  const defaut = CAT.find(s => s.i === 7);                    // Enrobés/GB3/GB3
  if (defaut && [...$("struct").options].some(o => o.value === String(defaut.uid))) { $("struct").value = String(defaut.uid); surVoieOuStructure(true); }
  window.__app = { lancer, couches: () => couches, note, dessiner: dessinerCouches };
})();
