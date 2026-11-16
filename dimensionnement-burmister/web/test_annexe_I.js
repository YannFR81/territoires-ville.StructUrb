// Cas tests de l'annexe I de la NF P98-086:2019 rejoués avec le moteur JavaScript de la page.
const B = require('./engine.js').Burmister, D = require('./annexe_I.json');
function une(L, i, g, pos) {
  const c = L.map(l => ({ E: l[2], nu: l[3], h: l[1] === null ? Infinity : l[1], interface: l[4] || 'collee' }));
  const mod = new B.Modele(c, 0.02, { a: 0.125, rmax: 0.375 }), k = pos === 'roue' ? 0 : 1;
  if (g === 'ez') return -B.jumelage(mod, mod.zt[i], 'dessous', 2)[k].ezz * 1e6;
  const p = B.jumelage(mod, mod.zb[i], 'dessus', 2)[k];
  if (g === 'et') return Math.max(p.exx, p.eyy) * 1e6;
  const lam = c[i].E * c[i].nu / ((1 + c[i].nu) * (1 - 2 * c[i].nu)), mu = c[i].E / (2 * (1 + c[i].nu)), tr = p.exx + p.eyy + p.ezz;
  return Math.max(lam * tr + 2 * mu * p.exx, lam * tr + 2 * mu * p.eyy);
}
let ok = 0;
for (const [cas, i, g, pos, ref, tol] of D.REQ) {
  const L = D.CAS[cas]; let v;
  if (L.some(l => l[4] === 'semi')) v = ['collee', 'glissante'].map(m => une(L.map(l => l[4] === 'semi' ? [l[0], l[1], l[2], l[3], m] : l), i, g, pos)).reduce((a, b) => a + b) / 2;
  else v = une(L, i, g, pos);
  const good = Math.abs(v - ref) <= tol; ok += good;
  console.log((good ? 'OK  ' : 'HORS') + ' ' + cas.padEnd(18) + L[i][0].padEnd(7) + g + ' ' + pos.padEnd(7) + v.toFixed(3).padStart(9) + '  norme ' + ref + ' ± ' + tol);
}
console.log(ok + '/' + D.REQ.length + ' dans la tolérance (moteur JavaScript)');
