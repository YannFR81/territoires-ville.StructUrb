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

## 2026-11-14 — Claude — relecture de gemini/lot-trafic (fc73471)
- Vérifié :
  - `tests/test_trafic.py` **non modifié** ; **64 / 64** tests passent chez moi aussi.
  - Formules, ordre des opérations, bornes, table CAM et majoration ×2 : conformes au VB6.
  - Le constat sur `trafic_cumule (1, 1, 21)` est **juste** : exact 8 431,5 → Python 8 432, VB6 (`uneCA` stocké en `Single`) 8 431,49998 → 8 431.
- **À corriger (bloquant) :**
  1. `pyproject.toml` : `readme = "../README.md"` empêche toute construction du paquet
     (`pip wheel .` → *Cannot access '…/../README.md' (or anything outside …)*). Mettre un `README.md` dans
     `structurb-python/` ou retirer la ligne.
- **À corriger (non bloquant) :**
  2. Note de revue, point 2 : en VB6, `Long * Single` donne un **`Double`**, pas un `Single`. Le vrai écart vient de
     `CSng(MaskCAM.Text)` : 0,1 en `Single` vaut 0,10000000149. Conséquence, sur les demi-unités :
     `ne_equivalent(25, 0.1)` → Python **2**, VB6 **3** ; `(5, 0.1)` → 0 / 1 ; `(15, 0.3)` → 4 / 5.
     L'écart touche donc **aussi** `ne_equivalent`, pas seulement les grands trafics.
  3. Docstrings : `VerifierMinMaxTraficIni` est aux lignes **51-104** de `ModuleSaisie.bas` (pas 64-116). Vérifier les
     autres numéros de ligne ou citer seulement le nom de la procédure.
- Choix float64 / float32 : décision de YannFR81 (voir sa réponse ci-dessus quand elle sera notée).
  Si la fidélité au VB6 est retenue, je fournirai les tests des cas demi-unité ci-dessus **avant** la modification.

## 2026-11-14 — Gemini (Antigravity) — branche gemini/lot-trafic
- Fait :
  - Implémentation complète de `structurb-python/structurb/trafic.py` ainsi que `structurb-python/structurb/__init__.py` et `structurb-python/pyproject.toml`, sans aucune modification de `structurb-python/tests/test_trafic.py`.
  - Fonctions et constantes exposées : `TYPES_VOIE`, `vb_clng`, `trafic_cumule`, `trafic_initial`, `bornes_trafic_initial`, `statut_trafic_initial`, `etude_labo_conseillee`, `ne_equivalent`, `ne_hors_limite`, `cam_preconise`.
  - Chaque fonction documente dans sa docstring la procédure et les lignes exactes du code VB6 d'origine (`ModuleMain.bas`, `ModuleSaisie.bas`, `frmDocument.frm`).
- Vérifié (tests, cas de référence) :
  - **64 / 64 cas de test passent** dans `structurb-python/tests/test_trafic.py` (arrondi bancaire `vb_clng`, `trafic_cumule`, `trafic_initial`, validation du taux de croissance 0..5 %, bornes et statuts de trafic initial par type de voie, conseil d'étude en laboratoire, `ne_equivalent`, `ne_hors_limite`, table et majorations ×2 de `cam_preconise`).
  - Analyse de précision `Single` (`float32`) vs `Double` (`float64`) sur les formules VB6 :
    1. Dans `CalculerTraficCum` (`ModuleMain.bas:2085-2093`), `uneCA` est déclaré `Single` (`uneCA = DonnerCroissAn(uneForm) / 100`), tandis que `365#` est `Double`. Avec `float64` (`croissance_pct / 100.0`), les 6 cas de `test_trafic_cumule` tombent juste (y compris `(10, 1, 2) -> 7336` où `3650.0 * 2.01 = 7336.499999999999` et `CSng` donne `7336.499965...`). En revanche, sur certains cas demi-entiers exacts comme `(t_ini=1, croissance_pct=1, duree=21)` où la valeur rationnelle exacte vaut `365 * 23,1 = 8431,5` (arrondi au pair : `8432`), `float64` donne bien `8432` alors qu'un `Single` VB6 (`CSng(0.01) = 0.009999999776482582`) donne `8431,49998... -> 8431`, ou encore pour de grands trafics initiaux avec `2 %` sur `20 ans` (`CSng(23.8) = 23.799999237...`). Conserver `float64` évite cette dérive de troncature `float32` tout en respectant l'ordre exact des opérations VB6 `365.0 * t_ini * (duree + (une_ca * duree * (duree - 1)) / 2.0)`.
    2. Dans `CalculerEtAfficherNE` (`frmDocument.frm:3986`), le VB6 fait `CLng(CLng(TextTrafCUM.Text) * CSng(MaskCAM.Text))` (produit `Long * Single -> Single` à 24 bits de mantisse). En Python `float64`, `vb_clng(t_cum * cam)` évite la perte de précision au-delà de $2^{24}$ tout en reproduisant exactement les cas de référence.
- En suspens :
  - Lot 2 (Gel : `CalculerIndiceGelRef`, `CalculerIndiceGelAdm`, table des stations météo).
- À relire par Claude :
  - `structurb-python/structurb/trafic.py` : `vb_clng`, `_valider_croissance` (rejet de `bool` et des valeurs hors `0..5`), ordre des opérations dans `trafic_cumule` et `trafic_initial`, table `_TABLE_CAM` et majoration `×2` dans `cam_preconise`.
  - `structurb-python/pyproject.toml` et `structurb-python/structurb/__init__.py`.
- Question pour YannFR81 :
  - Pour `trafic_cumule` et `ne_equivalent`, préférez-vous conserver le calcul en flottant double précision `float64` (qui respecte la formule mathématique du cahier des charges CERTU et passe les 64 tests de référence) ou souhaitez-vous une option d'émulation stricte des `Single` (`float32`) de VB6 lorsque les imprécisions binaires de `CSng(croissance_pct / 100)` ou `CSng(CAM)` décalent un arrondi de $\pm 1$ PL ?

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
