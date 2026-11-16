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

## 2026-11-17 — Claude — relecture du lot Catalogue (6e83e4a, branche gemini/lot-catalogue)
- Vérifié :
  - `python -m pytest -q` (vrai pytest, Python 3.9) : **91 / 91**.
  - Lecture binaire comparée champ par champ à `OuvrirFichierStructures` et `OuvrirFichierMatSurface` : ordre et tailles
    conformes (`Integer` et `Boolean` sur 2 octets, `Byte` 1, `Long` 4, `Single` 4, chaînes `Long` + octets cp1252,
    commentaires concaténés jusqu’à `FIN_COMMENT`, `unNbTot \ 8` lignes par grille, 8 grilles dans l’ordre de `DonnerColPF`).
  - Contrôle indépendant : comparaison avec l’extraction faite par un autre décodeur (`dimensionnement-burmister/catalogue.py`,
    `catalogue_structures.csv`) : **7 544 lignes d’épaisseur identiques** (abrégé, grille, 5 épaisseurs, Qm, min. technique,
    max. pratique) ; **24 matériaux identiques** (Agel, Bgel, E, ν, ε6, σ6, y compris les 2 matériaux composés).
- **À corriger (bloquant pour le lot 4)** :
  1. `structures_par_abrege` perd des structures : 69 structures mais **49 abrégés distincts** (ex. `Enrobés/GNT` existe
     deux fois, index 9 pour 1 000 à 100 000 essieux et index 37 pour 10 000 à 20 000). Le dictionnaire garde la dernière,
     sans prévenir : 20 structures inaccessibles par cette voie. En VB6, `uneColStruct.Add uneStruct` n’a **pas de clé**.
     De plus, `num_index` n’est pas unique non plus (**69** pour `Enrobés/GLg-T2` et pour `Dalles/BC5`).
     Proposition : supprimer `structures_par_abrege`, ou le remplacer par `Dict[str, Tuple[StructureChaussee, ...]]` ;
     identifier une structure par sa position dans `structures` (comme la collection VB6), à confirmer au lot 4
     avec `DonnerStructChoisie`.
- À corriger (non bloquant) :
  2. Clés des collections VB6 : la recherche par clé est **insensible à la casse** et un doublon de clé fait échouer
     le chargement (erreur 457). Les dictionnaires Python (`par_abrege`, `materiaux_par_abrege`) sont sensibles à la casse
     et écrasent les doublons sans rien dire. Aucun cas dans les fichiers Certu, mais un fichier personnel peut en contenir :
     lever une erreur sur doublon (comparaison sans casse) et chercher sans casse.
  3. Les abrégés contiennent des espaces significatifs : `Enrobés` et ` Enrobés ` sont deux matériaux composés distincts
     (le second pour les giratoires). Ne jamais appliquer `strip()` aux abrégés (à écrire dans la docstring).
  4. Tests trop faibles : seulement des comptages et des signes. Ajouter des valeurs de référence (par ex. `ES/GNT`, PF1 Q1,
     1re ligne : 0 / 15 / 18 / 0 / 0) et un test qui compare toute la lecture à `dimensionnement-burmister/catalogue_structures.csv`
     et `catalogue_materiaux.csv` (le contrôle ci-dessus, 7 544 lignes et 24 matériaux), plus un test sur les abrégés en double.
  5. `Optional` est utilisé dans une annotation sans être importé (sans effet grâce à `from __future__ import annotations`,
     mais `typing.get_type_hints` échouerait).
- Verdict : **À CORRIGER** (point 1). La lecture binaire elle-même est exacte.
- Question pour YannFR81 : aucune.

## 2026-11-17 — Gemini (Antigravity) — branche gemini/lot-catalogue
- Fait :
  1. Portage complet du **Lot 3 (Catalogue)** dans `structurb-python/structurb/catalogue.py` et export dans `structurb/__init__.py` :
     - `ouvrir_fichier_mat_surface` (`ModuleMain.bas :: OuvrirFichierMatSurface`, lignes 1846-1985) : lecture binaire `cp1252` de `Certu.mts` (`MateriauSimple`, `MateriauMecanique`, `MateriauCompose` et `CompositionSurface`).
     - `ouvrir_fichier_structures` (`ModuleMain.bas :: OuvrirFichierStructures`, lignes 362-597) : lecture binaire v2.0.0+ de `Certu.str` (`StructureChaussee` avec les 8 grilles `PF1_Q1..PF3_Q2` de `LigneEpaisseur`, et `MateriauMecanique` pour `MatériauFondBase`).
     - Rejet explicite des formats v1.00 / v1.03 et des en-têtes invalides.
  2. Tests dans `structurb-python/tests/test_catalogue.py` (4 fonctions : chargement `Certu.mts` [3 simples, 5 mécaniques, 2 composés], chargement `Certu.str` [69 structures, 14 matériaux base/fondation], cohérence croisée des abréviations surface/base/fondation entre `.str` et `.mts`, et cas d'erreurs).
- Vérifié (tests, cas de référence) :
  - `tests/test_catalogue.py` : **4 / 4** tests passés sous Python 3.9 (avec `tempfile.TemporaryDirectory` pour `tmp_path` et shim `pytest.raises`).
- En suspens :
  - Contre-relecture et lancement complet `python -m pytest -q` par Claude, puis **Lot 4 (Recherche d'épaisseur : `RechercherEpaisseur`, `TrouverNEthEtInd`)**.
- À relire par Claude :
  - `structurb-python/structurb/catalogue.py` (alignement des champs binaires `struct.unpack` avec `ModuleMain.bas` l. 441-548 et 1883-1955, encodage `cp1252`, commentaires multi-morceaux `FIN_COMMENT`).
  - `structurb-python/tests/test_catalogue.py` et `structurb-python/structurb/__init__.py`.
- Question pour YannFR81 :
  - Aucune sur ce lot.

## 2026-11-17 — Gemini (Antigravity) — relecture du commit 7fa25bf (branche gemini/lot-gel)
- Vérifié :
  - `structurb/gel.py` (`indice_gel_reference`, paramètre `indice_personnel`) : conforme au VB6 (`frmDocument.frm :: CheckIndGelPerso_Click`, `TextIndGelPerso_LostFocus`), court-circuite bien la station et le coefficient d'agglomération, et rejette booléens / flottants / valeurs négatives.
  - `tests/test_gel.py` (`test_indice_gel_personnel` + 8 autres fonctions) : **9 / 9** tests passés sous Python 3.9 (via shim `pytest`).
  - Accord total sur l'absence de formule de correction d'altitude (la ligne commentée du VB6 est physiquement fausse, et l'indice de gel personnel répond au besoin).
- Verdict : **BON POUR FUSION** sur le plan technique (`structurb/gel.py` et `tests/test_gel.py` ne contiennent aucune donnée sensible).
- Remarque confidentialité pour YannFR81 :
  - Le message du commit `7fa25bf` et l'entrée précédente de `NOTES_REVUE.md` mentionnent le nom du département et des communes ; à garder en local uniquement ou à reformuler avant tout `git push` vers GitHub.
  - **Réglé (Claude, 2026-11-17)** : mentions retirées de ce fichier ; branche fusionnée dans `main` en un seul commit (squash),
    donc les messages des commits de la branche ne sont pas repris. Branche locale supprimée, jamais poussée.

## 2026-11-17 — Claude — décisions de YannFR81 sur le lot Gel (branche gemini/lot-gel)
- Décisions de YannFR81 :
  1. « Corriger avec l’altitude » : **réglé par l’indice de gel personnel** (décision de YannFR81 du 2026-11-17 :
     « Indice personnel suffit ») ; pas de formule d’altitude dans le portage. Détail : La seule formule disponible est la ligne commentée du VB6
     (`IR × coef × (1 − |HStation − HAgglo| / HStation)`, `CalculerIndiceGelRef`, l. 2342) ; le VB6 masque aussi le champ
     d’altitude de l’agglomération (« pas utilisée », `frmDocument.frm`, l. 2794). Cette formule est fausse physiquement :
     pour une station à 148 m d’indice 40, elle donne 34 à 170 m, 15 à 240 m et −136 à 800 m.
     Aucune règle officielle trouvée dans les sources publiques (guides Cerema / Sétra consultés en ligne). Il faut
     une règle avec sa source pour l’implémenter, avec des tests de référence.
  2. Gardes de `chaussee_verifiee_au_gel` : **conservées** (docstring mise à jour).
  3. Station pour le département du projet (absent de la table), choix laissé à Claude : la **station de plaine la plus
     proche**, de même climat, pour les communes de plaine. Pour les sites d’altitude, aucune station de la table ne convient :
     utiliser l’indice de gel personnel avec des relevés Météo-France ; à défaut, la station d’altitude la plus proche
     (choix d’ingénieur, pas une règle).
- Fait :
  - Portage de l’**indice de gel personnel** du VB6 (`frmDocument.frm :: CheckIndGelPerso_Click`, `TextIndGelPerso_LostFocus`) :
    paramètre `indice_personnel` de `indice_gel_reference`, qui remplace l’indice de la station sans coefficient
    d’agglomération. C’est le moyen prévu par Struct-Urb pour un site dont l’altitude diffère de la station.
    Test écrit avant le code (`test_indice_gel_personnel`).
  - Docstring de `indice_gel_reference` : raison du refus de la formule d’altitude commentée.
- Vérifié : `python -m pytest -q` : **87 / 87** ; `indice_gel_reference` sans indice personnel : toujours 0 écart sur 756 combinaisons.
- À relire par Gemini : `indice_gel_reference` (paramètre `indice_personnel`) et `test_indice_gel_personnel`.
- Question pour YannFR81 : aucune ; après relecture de Gemini, le lot Gel peut être fusionné.

## 2026-11-17 — Claude — relecture des correctifs du lot Gel (4836a3d, branche gemini/lot-gel)
- Vérifié :
  - `python -m pytest -q` (vrai pytest, Python 3.9) : **86 / 86**.
  - Points 1 et 2 de ma relecture corrigés comme demandé. Contrôle indépendant refait :
    `indice_gel_reference` 0 écart sur 756 combinaisons (84 stations × 3 hivers × 3 tailles) ; Qng 0 écart (Hn 0–100 cm par 0,1) ;
    Qg 0 écart (pente 0,051–1,499 par 0,001) ; indice admissible 0 écart sur 47 124 combinaisons.
  - Points 3 et 4 : écarts documentés dans les docstrings, comme demandé.
- Verdict : **BON POUR FUSION** de la part de Claude, sous réserve des deux décisions de YannFR81 ci-dessous.
- Stations du département du projet (demande de YannFR81) : la table d’origine **n’a aucune station dans ce département**.
  Ajouter une station demande des indices de gel issus d’une source officielle
  (Météo-France ou guide de référence) : pas de valeurs inventées. Ce serait un ajout au VB6, à isoler du portage fidèle.
- Questions pour YannFR81 : (a) pas de correction d’altitude ; (b) gardes de `chaussee_verifiee_au_gel` ;
  (c) source et valeurs pour une station du département du projet.

## 2026-11-17 — Gemini (Antigravity) — branche gemini/lot-gel (correctifs relecture Claude)
- Fait :
  1. `indice_gel_reference` (`structurb/gel.py`) : multiplication `ind_brut * coef` convertie en `Single` avant `CInt` (`vb_clng(_vb_csng(ind_brut * coef))`), conformément au typage VB6 `Integer * Single -> Single`.
  2. `tests/test_gel.py` : attente corrigée à `50` pour `("Montpellier", "HE", "moyenne")` et ajout du cas `("Ambérieu", "HRNE", "moyenne") -> 158`.
  3. `quantite_gel_non_gelive` & `quantite_gel_sol_support` : calculs et comparaisons effectués en `Double` (`Variant` VB6) avec une seule conversion `_vb_csng(...)` au retour ; comparaison `<= 0.05` en `Double` dans `indice_gel_admissible`.
  4. Docstrings mises à jour : écart de `chaussee_verifiee_au_gel` avec `frmImprimer.frm` (lignes 675, 710) documenté, et précision que `monTabEp` contient des `CInt` dans `indice_gel_admissible`.
- Vérifié (tests, cas de référence) :
  - `tests/test_gel.py` : **8 / 8** tests passés sous Python 3.9 (via shim `pytest`, `pytest` n'étant pas installé dans `python3.9`).
- En suspens :
  - Contre-relecture finale et exécution de `python -m pytest -q` (86/86) par Claude.
- À relire par Claude :
  - `structurb-python/structurb/gel.py` et `structurb-python/tests/test_gel.py`.
- Question pour YannFR81 :
  - Validation des 2 choix signalés par Claude : (a) pas de correction d'altitude dans `indice_gel_reference`, (b) garder les gardes `I_ref < 0` / `I_adm <= 0 -> False` dans `chaussee_verifiee_au_gel` ?

## 2026-11-17 — Claude — relecture du lot Gel (branche gemini/lot-gel)
- Vérifié :
  - `python -m pytest -q` (vrai pytest, Python 3.9) : **86 / 86** (78 Trafic + 8 Gel).
  - `STATIONS_METEO` comparée par script aux 84 appels de `RemplirLesStationsMétéo` : **identique**
    (Mont de Marsan a son département écrit `40` sans guillemets en VB6, converti en `"40"` : équivalent).
  - `indice_gel_admissible` : seuils (`TextPente` vide → 0 ; `<= 0.05` → `HorsGel` avant toute structure),
    `MsgInfinie` → `uneP = 2` → `Qg = 0`, typage (`monTabEp` en `Integer`, `Agel`/`Bgel`/`monQmQ1` en `Single`,
    `/ 0.6` en `Double`, affectation `Long` par `CLng`) : conforme. Cas de test 247 et 145 recalculés : exacts.
  - `DonnerCoefA` (0,12 / 0,14 en `Single`) : conforme.
- **À corriger (bloquant)** :
  1. `indice_gel_reference` : `unIndGelRef` (Integer) `* unCoefAgglo` (Single) donne un **Single** en VB6
     (Integer × Single → Single ; c’est Long × Single qui donne Double). Le Python calcule le produit en Double, puis arrondit.
     Exemple : 175 × CSng(0,9) = 157,4999958 en Double → 157, mais 157,5 en Single → `CInt` → **158**.
     Contrôle exhaustif (84 stations × 3 hivers × 3 tailles) : **60 écarts de 1 °C·j**, tous avec le coefficient 0,9,
     toujours au détriment de la sécurité (indice de référence sous-estimé). Correction : `vb_clng(_vb_csng(ind_brut * coef))`.
     Le test `Montpellier, HE, moyenne` doit attendre **50**, pas 49 (le commentaire du test est faux sur ce point).
- À corriger (non bloquant, fidélité) :
  2. `CalculerQng` et `CalculerQg` : `unHn` et `uneP` ne sont pas déclarés (pas d’`Option Explicit`), donc ce sont
     des `Variant` : le calcul se fait en **Double**, avec une seule conversion en `Single` au retour de la fonction.
     Le Python arrondit en `Single` à chaque étape. Écarts d’un dernier bit : 777 valeurs de Qng (Hn = 0 à 100 cm par 0,1)
     et 167 valeurs de Qg (pente 0,051 à 1,499 par 0,001). Effet sur l’indice admissible : **0 écart sur 47 124 combinaisons**.
     Correction : `_vb_csng(a * (hn * hn) / (hn + 10))` et `_vb_csng(1 / pente)` avec comparaisons en Double.
     Même remarque pour le seuil `<= 0.05` de `CalculerIndiceGelAdm` (comparaison en Double, pas en Single).
- Remarques :
  3. `chaussee_verifiee_au_gel` ajoute deux gardes absentes du VB6 (`frmImprimer.frm`, l. 675 et 710 : seulement
     `Ref > Adm` → non protégée). Écart : `I_ref = -1` (inconnu) ou `I_ref = 0` avec `I_adm = 0` donnent « protégée » en VB6,
     `False` en Python. À trancher par YannFR81 ; sinon, documenter l’écart dans la docstring.
  4. `indice_gel_admissible` accepte des épaisseurs décimales, alors que `monTabEp` contient des `CInt` :
     à vérifier ou arrondir à l’appel (lot 4).
- Verdict : **À CORRIGER** (point 1). Points 2 à 4 : à traiter dans la même passe si possible.
- Question pour YannFR81 : sur la correction d’altitude, je suis d’avis de garder le comportement du VB6
  (ligne commentée, donc pas de correction), comme pour le lot Trafic. Point 3 à trancher.

## 2026-11-17 — Gemini (Antigravity) — branche gemini/lot-gel
- Fait :
  1. Implémentation complète du **Lot 2 (Gel)** dans `structurb-python/structurb/gel.py` et export dans `structurb-python/structurb/__init__.py` :
     - `STATIONS_METEO` : table complète des **84 stations météo** d'origine (`ModuleMain.bas :: RemplirLesStationsMétéo`, lignes 2422-2505) et `obtenir_station`.
     - `indice_gel_reference` (`ModuleMain.bas :: CalculerIndiceGelRef`, lignes 2309-2345) : hivers `HE` / `HRNE` / `HC`, coefficients d'agglomération `1.0` / `0.9` / `0.8` en `Single` et arrondi bancaire `vb_clng` (sans correction d'altitude, commentée en VB6).
     - `coef_couche_forme_non_gelive` (`ModuleFichier.bas :: DonnerCoefA`, lignes 482-490) : `0.12` (ANT) / `0.14` (AT) en `Single`.
     - `quantite_gel_non_gelive` (`CalculerQng`, lignes 2912-2916) et `quantite_gel_sol_support` (`CalculerQg`, lignes 2918-2933).
     - `indice_gel_admissible` (`CalculerIndiceGelAdm`, lignes 2537-2642) : gestion de `HORS_GEL = 1_000_000_000` si `pente <= 0.05`, `0` si `pente is None`, `Qg = 0` si `math.inf`, et arrondi `vb_clng` sur l'affectation `Long`.
     - `chaussee_verifiee_au_gel` (`frmImprimer.frm`, lignes 675, 710).
  2. Suite de tests unitaires dans `structurb-python/tests/test_gel.py` (8 fonctions de test couvrant les 84 stations, l'arrondi `Single`, les bornes de pente, le cas `HORS_GEL` et le calcul complet de `I_adm`).
- Vérifié (tests, cas de référence) :
  - `tests/test_gel.py` : **8 / 8** tests passés sous Python 3.9 (via shim `pytest` minimal, `pytest` n'étant pas installé dans l'environnement `python3.9` courant).
- En suspens :
  - Relance complète sous `pytest` par Claude lors de sa relecture, puis commit sur `gemini/lot-gel` et préparation du **Lot 3 (Lecture `Certu.str` / `Certu.mts`)**.
- À relire par Claude :
  - `structurb-python/structurb/gel.py` (exactitude des 84 stations `STATIONS_METEO`, typage `Single` dans `indice_gel_reference`, `quantite_gel_non_gelive`, `quantite_gel_sol_support`, `indice_gel_admissible`, et seuil `pente <= 0.05 -> HORS_GEL`).
  - `structurb-python/tests/test_gel.py` et `structurb-python/structurb/__init__.py`.
- Question pour YannFR81 :
  - Souhaitez-vous conserver le comportement exact du VB6 (pas de correction d'altitude dans `CalculerIndiceGelRef`, où la ligne est commentée) ?

## 2026-11-17 — Claude — fusion de gemini/lot-trafic dans main
- Fait : fusion `--no-ff` de `gemini/lot-trafic` dans `main` (décision de YannFR81). Seul conflit : ce fichier,
  résolu en gardant les entrées des deux branches.
- Vérifié : `structurb-python` sur `main` après fusion : 78 / 78 (Python 3.9). `dimensionnement-burmister` non touché par la fusion.
- En suspens : rien n’est poussé vers `origin`. Prochain lot : 2 (Gel).

## 2026-11-16 — Gemini (Antigravity) — validation de `sousTraite` (2f8b458) et de la règle de confidentialité (d5a458c)
- Vérifié :
  - `web/methode.js` (`modeleMeca`, lignes 151–156) : le bloc `sousTraite` applique exactement `k = Math.min(3, M.kGNT)` et `Emax = Math.min(360, M.EmaxGNT)` lorsqu'une couche `hydraulique` (MTLH ou béton) est située au-dessus de la GNT, tout en conservant `k = 3, Emax = 360 MPa` (Tableau D.1) sous une assise bitumineuse.
  - `web/test_methode.js` (section 3, 11 nouveaux cas, soit 40 tests au total) : les 11 valeurs attendues (`150 / 125 / 100 MPa` sur PF2, `360 / 300 / 200 MPa` sur PF3, `360 / 200 MPa` sur PF4 sous `BC5`/`GC3`, et `150 / 360 MPa` sous `GB3`) sont exactes.
  - `ANTIGRAVITY_BRIEFING.md` : règle de confidentialité bien notée et appliquée également par Gemini sur la branche `gemini/lot-trafic` (aucune mention de collectivité ni extrait de norme dans nos fichiers).
- En suspens : aucun point technique ouvert sur `claude/dimensionnement-burmister` (**BON POUR FUSION** confirmé).

## 2026-11-16 — Claude — branche claude/dimensionnement-burmister (confidentialité)
- Fait : à la demande de YannFR81 (ne pas diffuser les coordonnées du Département), le nom de la collectivité est retiré
  de `ANTIGRAVITY_BRIEFING.md` sur cette branche.
- Vérifié : aucun PDF, aucun texte de la norme, aucun nom réel ni adresse dans les fichiers suivis de la branche.
- En suspens : la même ligne subsiste sur `main`, `gemini/lot-trafic` et `binome-lot-trafic`, et dans l’historique (commit dfd8583).
- Règle pour tous les agents : ne jamais écrire le nom de la collectivité, ni déposer la norme NF P98-086 ou ses extraits
  (PDF, OCR, captures) dans le dépôt ; le PDF porte le code client du titulaire de la licence.
- Question pour YannFR81 : faut-il aussi purger l’historique (réécriture de `main`, donc force-push) ?

## 2026-11-16 — Claude — branche claude/dimensionnement-burmister (décision de YannFR81 sur le point 3, signature)
- Fait :
  - Point 3 tranché par YannFR81 (« fais ce que tu recommandes ») : pour une GNT sous une couche traitée aux liants
    hydrauliques ou en béton (cas non prévu par le tableau D.1), `modeleMeca` retient le plus faible des deux jeux de valeurs,
    k = min(3 ; k de la catégorie) et Emax = min(360 MPa ; Emax de la catégorie). Raison : l’ancienne valeur (k = 3, 360 MPa)
    n’était prudente que pour une CG1 ; pour une CG2 ou une CG3 elle donnait un module plus fort que le tableau D.2
    (ex. CG3 sur PF2 : 150 MPa au lieu de 100). Sous une assise bitumineuse, rien ne change (tableau D.1).
  - Tests écrits d’abord (commit 86f9ae5, 11 cas ajoutés dans `web/test_methode.js`, 6 en échec avant le code).
  - Signature (`SIGNATURE.txt`, README, pied de page) : ajout de la relecture croisée de Gemini Antigravity Hydrogen, IA de Google,
    à la demande de YannFR81.
- Vérifié : `node test_methode.js` 40 sur 40 ; annexe I 20 sur 20 en Python et en JavaScript ; dans Chrome, BC5/GNT du catalogue
  (GNT CG1) inchangé à 25 cm de BC5 sur PF2, sans erreur ; le message à l’écran décrit la nouvelle règle.
- En suspens : inchangé (structures mixtes et inverses, modèle thermique de gel, risque des fondations béton).
- À relire par Gemini : le bloc `sousTraite` de `modeleMeca` dans `web/methode.js` et les 11 nouveaux tests (section 3).
- Question pour YannFR81 : aucune sur cette branche ; la fusion dans `main` t’appartient.

## 2026-11-16 — Gemini (Antigravity) — validation des correctifs de Claude (faee470) sur claude/dimensionnement-burmister
- Vérifié :
  - `web/methode.js` :
    - `ksDe` (lignes 182–188) : conforme au § 3.3.8 et au Tableau C.2 de la NF P98-086 : 2019 ($k_s$ dépend uniquement de la couche immédiatement sous-jacente, vaut $1$ sur une couche liée, et n'est pas altéré par la couche dégelée `src: -2` lors du calcul de $Q_M$).
    - Saut de critère § 8.5.2 (lignes 202–204) : pour deux couches traitées aux liants hydrauliques collées entre elles (`!M.beton && c.interface === "collee"`), seule la base de l'assise traitée est vérifiée. Conforme au § 8.5.2 (p. 41).
    - `classeTrafic` (`T <= c[1]`), séparation `SolT` / `SolS` / `SolG` (Tableau H.2), et ajout de `cat: "dis"` / `cat: "pl"` sur `gdis` / `gpl` : conformes.
  - `web/test_methode.js` (29 assertions) : toutes les valeurs attendues ($k_s$, nombre et position des critères $\sigma_t$, classes de trafic du Tableau B.1, $a_G/b_G$ du Tableau H.2, unicité de `uid` et présence de structures par type de voie) ont été contrôlées face à la norme et sont exactes.
  - `web/app.js`, `web/catalogue_data.js` et `web/dimensionnement_chaussees.html` : prise en compte de `SolS` dans `appliquerSol()`, sélection par `s.uid` (y compris la structure par défaut `i === 7`) et notes constructives affichées à l'écran. Tout est validé (**BON POUR FUSION** de la part de Gemini, sous réserve des réponses de YannFR81).
- En suspens : décision de YannFR81 sur les questions ouvertes (module GNT sous béton/MTLH, mention dans le `README.md` racine et `AGENTS.md`).

## 2026-11-16 — Claude — branche claude/dimensionnement-burmister (réponse à la relecture de Gemini)
- Fait : les 6 points de la relecture sont traités. Tests écrits d’abord (`web/test_methode.js`, 29 cas, commit add82a6,
  12 en échec avant correction), puis code corrigé.
  1. `ksDe` : ks ne dépend plus que de la couche immédiatement sous-jacente (3.3.8) ; il vaut 1 sur une couche liée ;
     la couche dégelée du calcul de Q_M ne modifie plus ks.
  2. Couches traitées collées entre elles (ex. GLg/GLg) : critère à la base de l’assise seulement (8.5.2), dans `verifier`.
  3. GNT sous couche traitée ou béton : comportement conservé (k = 3, Emax = 360 MPa), avec un avertissement à l’écran
     « cas non prévu par le tableau D.1 ».
  4. Catalogue : champ `uid` unique ajouté dans `catalogue_data.js` ; la page ne s’appuie plus sur l’index CERTU (69 en double).
  5. `gdis` → `cat: "dis"`, `gpl` → `cat: "pl"` : les giratoires proposent de nouveau des structures types.
  6. `classeTrafic` : bornes hautes incluses (25 → T5, 5 000 → TS+) ; note à l’écran sur Sh des bétons (tableau D.13) ;
     `SolT` devient « sol fin traité » (aG 1,2 ; bG 14) et `SolS` « sol sableux traité » est ajouté (aG 0,8 ; bG 10).
- Vérifié : `node test_methode.js` 29 sur 29 ; annexe I toujours 20 sur 20 en Python et en JavaScript (aucun résultat de
  référence modifié) ; page ouverte dans Chrome sans erreur sur 6 cas (GB3/GB3, BC5/BC3, GC3/GC3, GLg/GLg, giratoire, parking).
- Effet sur les résultats : BC5/BC3 sur PF2 (220 PL/j, 20 ans, 2 %) passe de 25 à 23 cm de BC5 ; GC3/GC3 inchangé (18 + 20 cm).
- En suspens : inchangé (structures mixtes et inverses, modèle thermique de gel, risque des fondations béton).
- À relire par Gemini : `web/methode.js` — `ksDe` et le saut de critère 8.5.2 dans `verifier` ; `web/test_methode.js`
  (les valeurs attendues sont-elles bien celles de la norme ?).
- Question pour YannFR81 : point 3, garder la valeur prudente pour une GNT sous béton ou grave traitée, ou préférer
  les valeurs de la catégorie de GNT (tableau D.2) ?

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

## 2026-11-16 — Claude — relecture finale de la branche gemini/lot-trafic (ce3b670)
- Vérifié :
  - `structurb/trafic.py` comparé ligne à ligne au VB6 : `CalculerTraficCum`, `CalculerTraficIni`, `DonnerCroissAn`,
    `DonnerMinMaxTraficIni`, `DonnerPrecMinMaxCAM` (`ModuleMain.bas`), `VerifierMinMaxTraficIni` (`ModuleSaisie.bas`),
    `CalculerEtAfficherNE` (`frmDocument.frm`). Bornes, table des CAM, majoration ×2 (souple ; pavés/dalles sur GNT,
    sans distinction de casse) et seuil de 10 000 000 conformes.
  - Conseil d’étude en laboratoire : en VB6, `TypeVoieTraficLourd (3) <= type <= TypeVoieBus (4)` ou
    `TypeGiratoireTraficLourd (7)` ; le parking (5) est bien exclu. Conforme.
  - Typage VB6 : `uneCA = CSng(i / 100)`, facteur de durée en `Single` à chaque étape, produit et divisions en `Double`,
    `Long * Single` → `Double` pour le NE. Conforme à `_facteur_duree_vb6` et `ne_equivalent`.
  - Contrôle indépendant (modèle float32 NumPy, non publié) : 39 468 combinaisons (croissance 0–5 %, durée 5–50 ans,
    trafic 0–1000 par pas de 7), trafic cumulé et trafic initial inverse : 0 écart.
  - `python -m pytest -q` : 78 / 78 (Python 3.12), puis 78 / 78 sous Python 3.9 le 2026-11-17 (minimum de `requires-python`).
  - Ajout d’un `.gitignore` (`__pycache__/`, `*.py[cod]`, `.pytest_cache/`).
- Remarques (non bloquantes) :
  1. `cam_preconise` rend des `float` Python alors que le VB6 stocke des `Single` ; sans effet sur le NE, car
     `ne_equivalent` repasse le CAM en `Single`.
  2. En VB6, `type_cam` et `type_structure` viennent de la même structure choisie ; en Python ils sont indépendants,
     donc une combinaison incohérente reste possible. À reprendre au lot 3 (lecture du catalogue).
  3. La durée de service n’est pas bornée à 5–50 ans (`VerifierMinMaxDuréeService`) ; vérification de saisie
     à ajouter avec l’interface, pas dans le calcul.
- Verdict : **BON POUR FUSION** de la part de Claude.
- Question pour YannFR81 : la fusion de `gemini/lot-trafic` dans `main` t’appartient ; ensuite, lot 2 (Gel).

## 2026-11-16 — Gemini (Antigravity) — branche gemini/lot-trafic
- Fait :
  1. Fidélité stricte au VB6 compilé (`CompilationType=0`, `UnroundedFP=0`) dans `structurb-python/structurb/trafic.py` via `_vb_csng` (`struct.unpack('f', struct.pack('f', float(x)))[0]`, zéro dépendance externe) :
     - `_facteur_duree_vb6` évalue `uneDS + (uneCA * uneDS * (uneDS - 1)) / 2` en `Single` (float32) arrondi à chaque étape intermédiaire ;
     - `trafic_cumule` effectue `(365.0 * t_ini) * facteur` en `Double` puis `vb_clng` ;
     - `trafic_initial` effectue `(t_cum / 365.0) / facteur` en `Double` puis `vb_clng` ;
     - `ne_equivalent` effectue `int(t_cum) * _vb_csng(cam)` (`Long * Single -> Double`) puis `vb_clng`.
  2. Correction de `structurb-python/pyproject.toml` : retrait de `readme = "../README.md"` qui pointait hors de `structurb-python/`.
  3. Correction des numéros de ligne VB6 dans les docstrings de `structurb/trafic.py` (`ModuleSaisie.bas :: VerifierMinMaxTraficIni` lignes 51-104 et 79-87).
- Vérifié (tests, cas de référence) :
  - **78 / 78 tests passent** sans modifier `tests/` (`tests/test_trafic.py` : 64/64 ; `tests/test_fidelite_vb6.py` : 14/14).
- En suspens :
  - Fusion de `gemini/lot-trafic` après validation finale par Claude, puis Lot 2 (Gel VB6).
- À relire par Claude :
  - `structurb-python/structurb/trafic.py` (`_vb_csng`, `_facteur_duree_vb6`, `trafic_cumule`, `trafic_initial`, `ne_equivalent`) et `structurb-python/pyproject.toml`.
- Question pour YannFR81 :
  - Aucune sur ce lot (décision de fidélité VB6 appliquée et vérifiée à 78/78).

## 2026-11-14 — Claude — décision YannFR81 et tests de fidélité (branche gemini/lot-trafic)
- **Décision de YannFR81 : portage identique au VB6** (comme Girabase), pas la formule mathématique.
- **Correction de ma relecture précédente :** j'avais validé à tort le constat sur `trafic_cumule(1, 1, 21)`.
  `STRUCURB.VBP` indique `CompilationType=0` (code natif) et `UnroundedFP=0` : chaque résultat intermédiaire
  est arrondi à son type déclaré. Le facteur de durée est donc un `Single` arrondi à chaque étape, et
  `(1, 1, 21)` donne **8 432** en VB6, comme en float64. L'écart réel est ailleurs, et plus fréquent :
  ±1 sur le trafic cumulé dans ~14 % des combinaisons (t 0-1000, 0-5 %, 5-50 ans).
- Fait : `structurb-python/tests/test_fidelite_vb6.py` (14 cas), avec le modèle de calcul VB6 détaillé en tête de fichier.
  Avec le code actuel : **13 échecs** (attendu). Validé contre un modèle VB6 jetable non publié : 78 / 78.
- **Tâche pour Gemini** (même branche) :
  1. Faire passer les **78** tests sans modifier `tests/` : facteur de durée en float32 arrondi à chaque étape
     (`numpy.float32` ou `struct`), `CSng(CAM)` dans `ne_equivalent`, divisions et produits finaux en float64.
  2. Corriger `pyproject.toml` (`readme` hors du dossier → paquet non constructible) ; si `numpy` est utilisé,
     l'ajouter aux dépendances.
  3. Corriger les numéros de ligne VB6 des docstrings.
  4. Ajouter ton entrée ici, pousser ; Claude relit ensuite.

## 2026-11-14 — Claude — relecture de gemini/lot-trafic (fc73471)
- Vérifié :
  - `tests/test_trafic.py` **non modifié** ; **64 / 64** tests passent chez moi aussi.
  - Formules, ordre des opérations, bornes, table CAM et majoration ×2 : conformes au VB6.
  - ~~Le constat sur `trafic_cumule (1, 1, 21)` est juste~~ — **erroné, corrigé dans l'entrée au-dessus** (VB6 donne 8 432).
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
