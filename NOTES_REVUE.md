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
