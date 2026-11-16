// Tests de la méthode (référentiel NF P98-086 : 2019) — points relevés par la relecture de Gemini du 16/11/2026.
const M = require('./methode.js').Methode;
const CAT = JSON.parse(require('fs').readFileSync(__dirname + '/catalogue_data.js', 'utf8').replace('window.CATALOGUE=', '').replace(/;\s*$/, ''));
let ok = 0, ko = 0;
const t = (nom, cond) => { cond ? ok++ : ko++; console.log((cond ? 'OK   ' : 'ÉCHEC') + ' ' + nom); };
const pres = (a, b) => Math.abs(a - b) < 1e-9;
const L = (m, h, itf) => ({ mat: m, h_cm: h, interface: itf || 'collee', verifier: M.MATERIAUX[m].fam !== 'non_lie' && !M.MATERIAUX[m].roulement });
const ctx = (pf) => ({ NE: 1e6, risque: 5, pf });
M.setReferentiel('nf2019');

// 1. ks (3.3.8 et tableau C.2) : seule la couche liée reposant sur une couche non liée ou sur la plate-forme est affectée
let r = M.verifier([L('BBSG', 6), L('GC3', 20, 'semi'), L('GC3', 20)], ctx('PF2')).crit.filter(k => k.type === 'σt base');
t('ks = 1 pour la base GC3 posée sur une fondation GC3', pres(r[0].ks, 1));
t('ks = 1/1,1 pour la fondation GC3 posée sur PF2', pres(r[1].ks, 1 / 1.1));
r = M.verifier([L('BC5', 22, 'glissante'), L('BC2', 15)], ctx('PF2')).crit.filter(k => k.type === 'σt base');
t('ks = 1 pour le BC5 posé sur une fondation en béton maigre', pres(r[0].ks, 1));
t('ks = 1/1,1 pour le béton maigre posé sur PF2', pres(r[1].ks, 1 / 1.1));
r = M.verifier([L('BBSG', 6), L('GB3', 20)], ctx('PF2+')).crit.find(k => k.type === 'εt base');
t('ks = 1/1,065 pour la GB3 posée sur PF2qs', pres(r.ks, 1 / 1.065));
r = M.verifier([L('BBSG', 6), L('GB3', 14), L('GNT', 25)], ctx('PF2')).crit.find(k => k.type === 'εt base');
t('ks = 1 pour la GB3 posée sur une GNT de 150 MPa', pres(r.ks, 1));
r = M.verifier([L('BBSG', 6), L('GB3', 20)], ctx('PF2'), { degel: 0.05 }).crit.find(k => k.type === 'εt base');
t('ks inchangé (1/1,1) quand une couche dégelée est insérée', pres(r.ks, 1 / 1.1));

// 2. 8.5.2 : couches traitées collées → critère à la base de l’assise seulement
r = M.verifier([L('BBSG', 6), L('GLg', 20, 'collee'), L('GLg', 20)], ctx('PF2')).crit.filter(k => k.type === 'σt base');
t('GLg collée sur GLg : un seul critère, à la base de l’assise', r.length === 1 && r[0].couche === 2);
r = M.verifier([L('BBSG', 6), L('GC3', 20, 'semi'), L('GC3', 20)], ctx('PF2')).crit.filter(k => k.type === 'σt base');
t('GC3 semi-collée sur GC3 : un critère par couche', r.length === 2);

// 3. GNT sous une couche traitée aux liants hydrauliques ou en béton : cas non prévu par le tableau D.1.
// Décision de YannFR81 (16/11/2026) : retenir le plus faible des deux jeux de valeurs,
// k = min(3 ; k de la catégorie) et Emax = min(360 MPa ; Emax de la catégorie) (tableaux D.1 et D.2).
const Egnt = (struct, pf) => M.modeleMeca(struct, pf).filter(c => c.src === struct.length - 1).map(c => c.E);
for (const [g, pf, E] of [['GNT', 'PF2', 150], ['GNT2', 'PF2', 125], ['GNT3', 'PF2', 100], ['GNT', 'PF3', 360], ['GNT2', 'PF3', 300], ['GNT3', 'PF3', 200], ['GNT2', 'PF4', 360], ['GNT3', 'PF4', 200]])
  t(`${g} de 20 cm sous BC5, sur ${pf} : E = ${E} MPa`, pres(Egnt([L('BC5', 22, 'glissante'), L(g, 20)], pf)[0], E));
t('GNT3 de 20 cm sous GC3, sur PF2 : E = 100 MPa', pres(Egnt([L('BBSG', 6), L('GC3', 22, 'semi'), L('GNT3', 20)], 'PF2')[0], 100));
t('GNT3 de 20 cm sous assise bitumineuse, sur PF2 : E = 150 MPa (tableau D.1, inchangé)', pres(Egnt([L('BBSG', 6), L('GB3', 14), L('GNT3', 20)], 'PF2')[0], 150));
t('GNT2 de 20 cm sous assise bitumineuse, sur PF3 : E = 360 MPa (tableau D.1, inchangé)', pres(Egnt([L('BBSG', 6), L('GB3', 14), L('GNT2', 20)], 'PF3')[0], 360));

// 6. tableau B.1 : bornes hautes incluses
for (const [T, c] of [[25, 'T5'], [26, 'T4'], [150, 'T3+'], [151, 'T2-'], [300, 'T2+'], [5000, 'TS+'], [5001, 'TEX']]) t(`classe de trafic de ${T} PL/j = ${c}`, M.classeTrafic(T) === c);

// 6. tableau H.2 : sols traités
t('sol fin traité : aG = 1,2 et bG = 14 par mètre', pres(M.MATERIAUX.SolT.ag, 0.012) && pres(M.MATERIAUX.SolT.bg, 0.14));
t('sol sableux traité : aG = 0,8 et bG = 10 par mètre', M.MATERIAUX.SolS && pres(M.MATERIAUX.SolS.ag, 0.008) && pres(M.MATERIAUX.SolS.bg, 0.10));
t('sol graveleux traité : aG = 0,8 et bG = 10 par mètre', pres(M.MATERIAUX.SolG.ag, 0.008) && pres(M.MATERIAUX.SolG.bg, 0.10));

// 4 et 5. catalogue
t('identifiants uniques dans le catalogue (champ uid)', new Set(CAT.map(s => s.uid)).size === CAT.length && CAT.every(s => s.uid !== undefined));
for (const v of ['gdis', 'gpl', 'rd', 'transit', 'des', 'dis', 'pl', 'bus', 'park']) {
  const cat = M.VOIES[v].cat || v;
  t(`voie « ${v} » : au moins une structure type proposée`, CAT.some(s => s.use.includes(cat)));
}
console.log(`${ok} réussis, ${ko} en échec`);
process.exit(ko ? 1 : 0);
