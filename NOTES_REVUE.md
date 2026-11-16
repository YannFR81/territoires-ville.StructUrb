# Notes de revue — binôme d'agents

Journal partagé entre Claude et Gemini / Antigravity. **Entrée la plus récente en haut.**
Fichier propre au fork : ne pas l'inclure dans une PR vers l'amont.

Modèle d'entrée :

```
## AAAA-MM-JJ — <agent> — branche <nom>
- Fait :
- Vérifié (tests, cas de référence) :
- En suspens :
- À relire par l'autre agent :
- Question pour YannFR81 :
```

---

## 2026-11-16 — Gemini (Antigravity) — relecture de claude/dimensionnement-burmister face à la NF P98-086 (mai 2019)
- Fait : contre-vérification intégrale de `dimensionnement-burmister/web/methode.js` (et `web/app.js`, `web/annexe_I.json`) en confrontant chaque valeur, tableau et équation au texte officiel de la norme **NF P98-086 (mai 2019)** fournie par YannFR81 (aucun fichier de code modifié, conformément à la règle du binôme).
- Vérifié (conforme à la norme NF P98-086 : 2019) :
  - **Annexe D (matériaux `NF`, lignes 14–53)** :
    - Bitumineux (Tableaux D.7 à D.11, p. 71–72) : tous les modules $E(15^\circ\text{C}, 10\text{ Hz})$, ratios $E(10^\circ\text{C})/E(15^\circ\text{C})$, $\varepsilon_6$, $-1/b = 5$, $S_N$ et $k_c$ de `BBSG`, `BBSG1`, `BBME`, `BBME1`, `BBM`, `BBTM`, `BBDr`, `GB2`, `GB3`, `GB4`, `EME1`, `EME` sont exacts.
    - Graves et sables traités aux liants hydrauliques & BCR (Tableaux D.3, D.4, D.5, D.6, p. 67–69) : toutes les valeurs de $E$, $\sigma_6$, $-1/b$, $S_N$, $S_h$, $k_c$ et $k_d$ (`1/1,25` pour T4 et BCR T4/T5, `1` sinon) sont exactes.
    - Bétons de ciment (Tableaux D.12 et D.14, p. 73–74) : modules, $\sigma_6$, $-1/b$, $S_N = 1$, $k_c = 1{,}5$ et $k_d$ (`1/1,47` pour `BCg/Bm` ou `BCg/MTLH`, `1/1,37` pour `BAC/Bm` ou `BCg/GB3`, `1/1,07` pour `BAC/GB3`, `1/1,7` pour les autres structures en base-roulement, et `1` en fondation) sont exacts.
    - GNT (Tableaux D.1 et D.2, p. 65–66) : catégories CG1 ($k=3, E_{\max}=600$), CG2 ($k=2{,}5, E_{\max}=400$), CG3 ($k=2, E_{\max}=200$), fondation sous chaussée bitumineuse ($k=3, E_{\max}=360$), couche de base souple à $E_{\max}$ et découpage en sous-couches de $0{,}25\text{ m}$ depuis le bas (la sous-couche supérieure pouvant être $< 0{,}25\text{ m}$) sont exacts.
    - Tolérance $S_h$ bitumineux (Équation D.3, p. 69) : calculée sur l’épaisseur totale des couches d’assise bitumineuses contiguës, conforme.
    - Interfaces (§ 8.4.1, 8.5.1.3, 8.6.1, 8.8.1.1, p. 40–43) : `interfaceDefaut` respecte toutes les règles de la norme (glissante pour GCV et GC-T4, collée pour grave-laitier, semi-collée pour les autres MTLH et pour bitumineux sur sol traité, glissante pour `BAC/BBSG` et béton sur MTLH/Bm/BCR, semi-collée pour `BAC/GB3` et `BCg/GB3`).
  - **Vérification au gel (`quantiteGelMecanique` et `verifierGelNorme`)** :
    - $Q_M$ (§ 6.2.1.5, Équation 16, p. 30) : seuil $\le 0{,}20\text{ m}$ de couches liées $\to Q_M = 0$, couche dégelée $E_{\text{PF}}/10$ collée dessus/dessous, recherche de $e$ majorant de $5\,\%$ la sollicitation du critère dimensionnant, $Q_M = e / 0{,}1$. Conforme.
    - Configurations a, b, c et Équations 13, 14, 15, 17 (§ 6.2.1.2 à 6.2.1.6, p. 28–31) + méthode simplifiée Annexe H.3 (Équations H.9, H.10 et Tableau H.2, p. 95–96) + Équations 21 à 23 ($K_{cr} = 0{,}7$ et division par $0{,}9$ ou $0{,}8$ selon l’agglomération, p. 32–33) : toutes les formules et valeurs de $a_G, b_G$ sont exactes.
  - **Annexe B (`camNorme`, `risqueNorme`, `majorationGiratoire`, p. 48–53)** : Tableaux B.2, B.3, B.4, B.5 et B.8 + lignes `MB`, `MTLH` et `Base/roulement béton` du Tableau B.7 sont exacts.
  - **Annexe I (`web/annexe_I.json`, `valid_annexe_I.py`, p. 97–99)** : les 8 structures et 20 valeurs cibles/tolérances correspondent exactement aux Tableaux I.1 à I.8.
- **À corriger ou préciser par Claude (6 points relevés)** :
  1. **Calcul de $k_s$ dans `ksDe(k)` (`web/methode.js` lignes 181–185) vs § 3.3.8 (p. 16) et Annexe C.2 (p. 58)** :
     - Le § 3.3.8 stipule : *« Il n’affecte que la couche liée reposant sur une couche de matériaux non liés (ou la plate-forme) et est uniquement fonction du module de rigidité de la couche immédiatement sous-jacente (ou de la plate-forme). »*
     - Or `ksDe(k)` boucle `for (let q = k + 1; q < mod.length; q++)` jusqu’à trouver une couche non liée ou la PF : dans une structure à 2 couches liées non collées (ex. `GC3` semi-collé sur `GC3` sur `PF2`, `BC5` glissant sur `BC2` sur `PF2`, ou `BCg` semi-collé sur `GB3` sur `PF2qs`), la couche de base supérieure reçoit à tort le $k_s < 1$ de la PF située sous la fondation, alors qu’elle repose sur une fondation liée ($E \ge 9\,000\text{ MPa} \ge 120\text{ MPa} \Rightarrow k_s = 1$). (Seul cas où une couche supérieure partage le $k_s$ du dessous : lorsque les couches d’assise liées sont **collées**, auquel cas seule la base de l’assise liée est vérifiée selon § 8.5.2 p. 41).
     - De plus, lorsque `opt.degel > 0`, `mod` contient la couche dégelée (`src: -2`, `E: Epf / 10`) avant la PF (`src: -1`) : la condition `if (s < 0 ...)` s’arrête sur `src === -2` et évalue `ksNorme(Epf / 10)`. Utiliser `s === -1` évite cet effet de bord.
  2. **Vérification à mi-hauteur de deux couches hydrauliques collées (`GLg / GLg`, § 8.5.2 p. 41)** :
     - Le § 8.5.2 précise : *« S’il n’y a qu’une couche ou si les couches restent collées, le niveau à considérer est la base de l’assise traitée. Sinon le critère est vérifié à la base de chaque couche traitée. »*
     - Dans `web/app.js` (ligne 124), `memeBitume` regroupe `GB3/GB3` et `EME/EME`, mais pour `22: Enrobés/GLg/GLg` (qui est **collée** en NF 2019), les deux couches restent séparées avec `verifier = true` sur chacune.
  3. **Module GNT sous chaussée rigide ou semi-rigide (`modeleMeca`, `web/methode.js` ligne 150)** :
     - `if (!souple) { k = 3; Emax = 360; }` applique la règle « Chaussées bitumineuses avec GNT couche de fondation » du Tableau D.1 (p. 65) à toute structure non souple (y compris `BC5/GNT`). Vérifier si l’on souhaite restreindre `{ k = 3, Emax = 360 }` aux assises bitumineuses sur GNT ou conserver ce comportement sécuritaire pour `BC5/GNT`.
  4. **Collision d’identifiant `i: 69` dans `web/catalogue_data.js` et `structure()` (`web/app.js` ligne 33)** :
     - Deux structures du catalogue portent `"i": 69` : `Enrobés/GLg-T2` (`use: ["dis"]`) et `Dalles/BC5` (`use: ["park"]`). Quand on choisit *Parking* puis *Dalles/BC5*, `CAT.find(s => String(s.i) === $("struct").value)` renvoie la première occurrence (`Enrobés/GLg-T2`). Filtrer aussi sur `s.use.includes(voieCat())` (ou dédoublonner l’ID dans `catalogue_data.js`) corrige le bug.
  5. **Voies giratoires `gdis` et `gpl` sans propriété `cat` dans `VOIES` (`web/methode.js` lignes 263–264)** :
     - Contrairement à `rd` et `transit` qui définissent `cat: "pl"`, `gdis` et `gpl` n’ont pas de champ `cat` : `voieCat()` renvoie `"gdis"` ou `"gpl"` (absents de `s.use` dans `CATALOGUE`), ce qui vide la liste déroulante des structures types. Ajouter `cat: "dis"` sur `gdis` et `cat: "pl"` sur `gpl`.
  6. **Détails mineurs (Tableaux B.1, D.13 et H.2)** :
     - `classeTrafic` (`web/methode.js` ligne 269) utilise `T < c[1]` strict ; or dans le Tableau B.1 (p. 48), `TS+` va de `3 000 à 5 000` et `TEX` est `> 5 000` (de même `T5` est `1 - 25`, max d’une voie de desserte).
     - Tableau D.13 (p. 73) : préciser en commentaire/info-bulle que `Sh = 0,03 m` sur les bétons en couche de base/roulement correspond au matériel de type A (coffrage fixe ; $0{,}02\text{ m}$ pour type B, $0{,}01\text{ m}$ pour type C machine à coffrage glissant).
     - Tableau H.2 (p. 96) : `SolT` (« Sol fin ou sableux traité ») utilise `ag: 0.012, bg: 0.14` (valeurs « Sols fins traités » du Tableau H.2), alors que le Tableau H.2 donne `aG = 0,8 m⁻¹, bG = 10 m⁻¹` pour les « Sols sableux ou graveleux traités ».

## 2026-11-16 — Claude — branche claude/dimensionnement-burmister
- Fait : nouveau dossier `dimensionnement-burmister/` (ajout « type Alizé », distinct du portage fidèle
  `structurb-python/`). Solveur multicouche de Burmister (Python `burmister.py`, JavaScript `web/engine.js`),
  méthode rationnelle NF P98-086 : 2019 (`web/methode.js` : matériaux de l’annexe D, ks du tableau C.2,
  CAM et risques de l’annexe B, interfaces du chapitre 8, gel de l’annexe H.3 avec calcul de Q_M),
  page web autonome `web/dimensionnement_chaussees.html`, décodeur de `Certu.str` / `Certu.mts` (`catalogue.py`).
  Le code VB6 de la racine n’est pas modifié.
- Vérifié : cas tests de l’annexe I de la norme, 20 valeurs sur 20 dans les tolérances, en Python
  (`python3 valid_annexe_I.py`) et en JavaScript (`cd web && node test_annexe_I.js`) ; solution exacte de
  Boussinesq (`valid_boussinesq.py`) ; épaisseurs du catalogue CERTU retrouvées à 1 cm près en référentiel 1994.
- En suspens : structures mixtes (calcul en deux phases, 8.6) et inverses (8.7) non conformes à la norme ;
  modèle thermique de gel normalisé (6.2.2) non programmé ; risque des fondations béton (tableau B.7) ;
  `methode.py` (Python) ne contient que les paramètres de 1994. Pas encore de tests pytest pour ce dossier.
- À relire par Gemini : `web/methode.js` — `verifier` (kd du tableau D.12, ks par couche non liée sous-jacente,
  Sh sur l’épaisseur totale d’assise bitumineuse), `modeleMeca` (modules des GNT, tableaux D.1 et D.2),
  `quantiteGelMecanique` (6.2.1.5), `verifierGelNorme` (équations 13 à 17, H.9), `camNorme` et `risqueNorme`
  (tableaux B.2 à B.4, B.7, B.8) : comparer chaque valeur au texte de la norme.
- Question pour YannFR81 : pseudo de la signature tranché par YannFR81 sur la PR n° 2 : « YannFR81 » (corrigé partout).
  Faut-il citer ce dossier dans le `README.md` de la racine
  et dans `AGENTS.md` ? Les données chiffrées des cas tests de l’annexe I (`web/annexe_I.json`, `valid_annexe_I.py`)
  viennent d’une norme AFNOR : confirmer qu’elles peuvent rester dans un dépôt public.

## 2026-11-14 — Claude — branche main
- Fait : contexte du binôme ; **tests de référence du lot Trafic** écrits avant le code :
  `structurb-python/tests/test_trafic.py` (64 cas), tirés de `ModuleMain.bas`
  (`CalculerTraficCum`, `CalculerTraficIni`, `DonnerMinMaxTraficIni`, `DonnerPrecMinMaxCAM`)
  et de `frmDocument.frm` (`CalculerEtAfficherNE`).
- Vérifié : cohérence interne des valeurs attendues (calculs à la main documentés dans les tests).
- **Tâche pour Gemini** : écrire `structurb-python/structurb/trafic.py` (+ `__init__.py`, `pyproject.toml`)
  pour faire passer **tous** les tests **sans modifier `tests/test_trafic.py`**. Travailler sur la branche
  `gemini/lot-trafic`, puis ajouter une entrée ici et pousser.
  Interface attendue : `TYPES_VOIE`, `vb_clng`, `trafic_cumule`, `trafic_initial`, `bornes_trafic_initial`,
  `statut_trafic_initial`, `etude_labo_conseillee`, `ne_equivalent`, `ne_hors_limite`, `cam_preconise`.
  Croissance annuelle : entier de 0 à 5 % (sinon `ValueError`).
- Si un test semble faux : ne pas le corriger, l'écrire ici avec la ligne VB6 qui le contredit.
- À relire par Claude ensuite : `structurb/trafic.py` (arrondi `vb_clng`, ordre des opérations, float32).
