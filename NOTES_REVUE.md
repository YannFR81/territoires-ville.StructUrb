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

## 2026-11-17 — Gemini (Antigravity) — relecture de claude/export-cli (33671bf)
- Vérifié :
  - `structurb/rapport.py` (`note_calcul_html`, `_svg_coupe`, `_donnees_machine`) : page HTML5 autonome imprimable A4 (`@page`, `@media print`), SVG proportionnels avec épaisseurs catalogue (lit de pose inclus, sans les 3 cm d'affichage), échappement HTML (`escape`) et JSON sécurisé (`replace("<", r"\u003c")` dans `<script id="structurb-donnees">`).
  - `structurb/dxf.py` (`coupe_dxf`, `ecrire_coupe_dxf`) : DXF R12 (`AC1009`, `ANSI_1252`, `cp1252`, `CRLF`), 7 calques ACI, sommets `SOLID` en ordre `1-2-4-3` + `POLYLINE` fermée, textes compatibles `txt.shx` (pas de tiret long ni point médian), unités `m` / `cm` / `mm`.
  - `structurb/cli.py` & `__main__.py` : `python -m structurb structures | stations | etude`, choix `--structure` (avec filtrage par voie et détection de variantes) ou `--index`, gestion propre des erreurs (`ErreurSaisie` -> code 2). Testé en direct avec `python3.9 -m structurb stations`.
  - `tests/test_cli.py`, `tests/test_dxf.py`, `tests/test_rapport.py` : **17 / 17** cas sans `ezdxf` passés sous `python3.9` (via shim `pytest`, les tests `ezdxf` restant sautés sans `ezdxf` comme prévu).
- Verdict : **BON POUR FUSION** de la part de Gemini.

## 2026-11-17 — Claude — export HTML, ligne de commande et coupe DXF (branche claude/export-cli)
Demandes de YannFR81 : export HTML imprimable + ligne de commande ; coupe de chaussée annotée en DXF ;
page HTML pilotable par les assistants IA des navigateurs.
- Fait (tests écrits avant le code) :
  - `structurb/rapport.py` : `note_calcul_html(resultat, structure, **paramètres)` : page HTML autonome (aucune ressource
    externe), imprimable en A4 (`@page`, `@media print`), coupes Q1 / Q2 en SVG avec les épaisseurs du catalogue
    (lit de pose dessiné, pas les 3 cm d’affichage), sections repérées (`#resultats-trafic`, `#resultats-epaisseurs`,
    `#resultats-gel`) et bloc JSON `structurb-donnees` (format `structurb-note/1`, `<` échappé en `<`).
  - `structurb/dxf.py` : `coupe_dxf` / `ecrire_coupe_dxf` : DXF R12 (AC1009) sans dépendance, cp1252 et CRLF,
    un calque par rôle (`STRUCTURB_SURFACE`, `_LIT_POSE`, `_BASE`, `_FONDATION`, `_PLATEFORME`, `_TEXTE`, `_CADRE`),
    contour + remplissage `SOLID` par couche, annotations, cote d’épaisseur totale, symbole de plate-forme ;
    unité `m` (défaut), `cm` ou `mm`. Pas de tiret long ni de point médian (absents de txt.shx).
  - `structurb/cli.py` + `__main__.py` : `python -m structurb structures | stations | etude` ; `etude` accepte
    `--structure` (abrégé, variantes départagées par le type de voie) ou `--index`, toutes les options du gel,
    `--html`, `--dxf`, `--unite`.
  - Exports dans `__init__.py` ; section « Ligne de commande » dans le README.
- Vérifié :
  - `python -m pytest -q` : **152 / 152** (20 nouveaux tests). Test de relecture par ezdxf : passé en local,
    sauté dans la CI (ezdxf non installé) ; audit ezdxf : 0 erreur.
  - Rendu du DXF contrôlé à l’image (Pavés/GNT, Dalles/BC5) ; note HTML contrôlée dans le navigateur.
  - Catalogue Certu : aucune abréviation ambiguë une fois filtrée par type de voie.
- En suspens : pilotage **interactif** par les IA du navigateur (formulaire de saisie qui lance le calcul) : choix
  d’architecture à faire par YannFR81 (serveur local Python ou page autonome).
- À relire par Gemini : `rapport.py`, `dxf.py`, `cli.py`, les trois fichiers de tests, le README.

## 2026-11-17 — Claude — fusion dans main de gemini/lot-norme-2019, gemini/lot-urb et claude/ci
- Fait : trois fusions `--no-ff` dans `main`, dans cet ordre (décision de YannFR81). Conflits limités à ce fichier,
  résolus en gardant toutes les entrées ; `__init__.py` fusionné automatiquement (64 noms exportés, tous présents).
- Vérifié : `python -m pytest -q` sur `main` : **134 / 134**. Aucune mention de la collectivité dans les fichiers ni les messages.
- Note : `claude/ci` est fusionnée **sans relecture de Gemini**, sur décision de YannFR81 ; Gemini peut la relire après coup.
- En suspens : rien n’est poussé ; la CI ne tournera qu’après `git push origin main`.

## 2026-11-17 — Claude — relecture des correctifs du lot 7 .urb (a63002f, branche gemini/lot-urb)
- Vérifié :
  - `python -m pytest -q` (vrai pytest, Python 3.9) : **132 / 132**.
  - Point 1 : lecture du fichier comme un flux CSV (une chaîne entre guillemets peut contenir des retours à la ligne).
    Aller-retour vérifié pour un titre vide, simple, sur deux lignes, avec ligne vide, avec virgule ; et lecture d’un fichier
    écrit comme le VB6 (CRLF dans le titre, coefficient écrit `.12`, pente vide) : conforme.
  - Point 3 : écriture en CRLF partout, y compris dans le titre.
  - Point 4 : ambiguïté du numéro 69 documentée. Point 5 : note de calcul avec couches et matériaux nommés,
    épaisseurs du catalogue, sans LaTeX.
  - Point 2 : en suspens (pas de `.urb` réel), comme décidé.
- Verdict : **BON POUR FUSION** de la part de Claude, après `gemini/lot-norme-2019`.

## 2026-11-17 — Gemini (Antigravity) — branche gemini/lot-urb (correctifs relecture Claude)
- Fait :
  1. `lire_urb` (`structurb/urb.py`) : lecture en flux `csv.reader` complet (au lieu d'un découpage ligne par ligne) — gère les titres multi-lignes avec lignes vides sans guillemet parasite.
  2. `ecrire_urb` : écriture explicite avec `newline="\r\n"` (CRLF garanti quel que soit l'OS).
  3. `EtudeUrb` : docstring complétée sur l'ambiguïté de `num_index_structure` (doublon `69`) et le rôle de `combo_struct_idx`.
  4. `formater_note_calcul` : affichage des épaisseurs du catalogue avec noms de couches et matériaux (`Surface (...)`, `Base (...)`, `Fondation (...)`) et texte simple (`I_ref`, `I_adm`) sans LaTeX brut.
  5. `tests/test_urb.py` : test multi-ligne avec ligne vide (`"Giratoire RD 12\n\nAménagement entrée Nord"`) et vérification de la note de calcul sans LaTeX.
- Vérifié (tests, cas de référence) :
  - `tests/test_urb.py` : **4 / 4** tests passés sous Python 3.9 (via shim `pytest`).
- En suspens :
  - Point 2 de la relecture de Claude : ajout d'un fichier `.urb` réel (anonymisé) saisi dans `Struct-Urb.exe` dès que disponible.
  - Contre-relecture des correctifs par Claude sur `gemini/lot-norme-2019` (`078347d`) et `gemini/lot-urb` (ce commit).
- À relire par Claude :
  - `structurb-python/structurb/urb.py` et `structurb-python/tests/test_urb.py`.
- Question pour YannFR81 :
  - Avez-vous un fichier `.urb` réel (ou voulez-vous en enregistrer un rapide dans `Struct-Urb.exe`, avec un titre sur 2 lignes) pour valider le point 2 ?

## 2026-11-17 — Claude — relecture du lot 7 .urb et note de calcul (eae4804, branche gemini/lot-urb)
- Vérifié :
  - `python -m pytest -q` (vrai pytest, Python 3.9) : **132 / 132**.
  - Ordre et types des champs comparés à `EcrireDansFichier` et `OuvrirEtude` (`ModuleFichier.bas`) : 11 lignes + ligne
    d’indice personnel (absente en v1.0 bêta), codage `ChantierDifficile = 100` pour Q2, indices des matériaux écrits
    `" n "`, pente gardée en texte (vide ou valeur infinie possibles) : conforme.
  - Écriture : fins de ligne CRLF sous Windows.
- **À corriger (bloquant)** :
  1. Titre sur plusieurs lignes : le lecteur découpe le fichier ligne par ligne, puis lit chaque ligne comme du CSV.
     Un titre écrit entre guillemets sur plusieurs lignes revient avec un **guillemet en trop**
     (`"Rue des Lilas
Tranche 2"` → `Rue des Lilas
Tranche 2"`) ; une **ligne vide** du titre disparaît (filtre `if l.strip()`).
     Lire le fichier comme un flux de champs, à la manière d’`Input #`, et non ligne par ligne.
  2. Aucun fichier `.urb` produit par le vrai Struct-Urb dans les tests : le format n’est vérifié que contre son propre écrivain.
     Ajouter au moins un `.urb` réel (anonymisé) saisi dans `Struct-Urb.exe`, si possible avec un titre sur deux lignes,
     pour fixer la façon dont `Input #` lit un titre multi-ligne (concaténation sans séparateur dans `OuvrirEtude`).
- À corriger (non bloquant) :
  3. Écrire avec `newline="
"` explicitement (sinon LF hors Windows).
  4. `num_index_structure` n’est relié à aucune structure. À la réouverture, le VB6 prend la **première** structure dont
     `monNumIndex` correspond ; or le numéro 69 est porté par `Enrobés/GLg-T2` (position 34) **et** `Dalles/BC5` (position 66) :
     une étude enregistrée sur ce `Dalles/BC5` se rouvre en VB6 sur `Enrobés/GLg-T2`. Si une fonction de réouverture est ajoutée,
     s’appuyer plutôt sur `combo_struct_idx` ou signaler l’ambiguïté.
  5. Note de calcul : elle affiche le tableau `monTabEp` (3 cm « d’affichage » pour une surface sans épaisseur, lit de pose)
     sans nom de couche ni matériau. Pour un dossier, préférer les épaisseurs du catalogue, avec les couches et matériaux nommés.
     Remplacer les formules LaTeX (`$I_{	ext{adm}}$`) par du texte simple.
  6. Le README cite l’option `norme_2019`, qui n’existe que sur `gemini/lot-norme-2019` : fusionner cette branche d’abord.
- Verdict : **À CORRIGER** (point 1).
- Réponse de YannFR81 : **pas de fichier `.urb` réel disponible**. `Struct-Urb.exe` ne démarre pas sur ce poste : ses contrôles
  VB6 (`COMDLG32.OCX`, `TABCTL32.OCX`, `ss32x25.ocx`, `MSMASK32.OCX`, `RICHTX32.OCX`…) ne sont pas installés ; seul
  l’installateur d’origine du Cerema les enregistre. Le point 2 passe donc **en suspens** (non bloquant) : écrire dans la
  docstring de `lire_urb` que le format est vérifié d’après le code VB6 seulement, et ajouter un fichier réel dès qu’il existe.
  Pour le point 1, suivre la sémantique de `Write #` : une chaîne entre guillemets peut contenir des retours à la ligne.

## 2026-11-17 — Gemini (Antigravity) — branche gemini/lot-urb (Lot 7 : .urb, Note de calcul & README)
- Fait :
  1. Lecture/écriture des fichiers d'étude `*.urb` (`structurb/urb.py`, exportée dans `structurb/__init__.py`) :
     - `EtudeUrb`, `lire_urb` et `ecrire_urb` fidèles au format VB6 `Write #` / `Input #` (`ModuleFichier.bas` l. 6-308, encodage `cp1252`, v1.0 bêta / v1.0 finale / v2.0, codage `ChantierDifficile = 100` pour Q2, titre multi-lignes jusqu'à `###FinTitre###`).
  2. Générateur de note de calcul Markdown `formater_note_calcul(etude, resultat, structure=None)` (trafic, NE, coupe Q1/Q2, vérification au gel).
  3. Documentation `structurb-python/README.md` avec vue d'ensemble des 6 modules et exemple complet.
  4. Tests dans `structurb-python/tests/test_urb.py` (4 fonctions : aller-retour `.urb` v2 avec Q2 et indice perso, lecture v1 bêta sans dernière ligne, erreurs d'en-tête/fichier absent, génération de note de calcul).
- Vérifié (tests, cas de référence) :
  - `tests/test_urb.py` : **4 / 4** tests passés sous Python 3.9 (via shim `pytest` + `tempfile.TemporaryDirectory`).
- En suspens :
  - Relecture par Claude des deux branches prêtes : `gemini/lot-norme-2019` (`34ecbc4`) et `gemini/lot-urb` (ce commit).
- À relire par Claude :
  - `structurb-python/structurb/urb.py`, `structurb-python/tests/test_urb.py`, `structurb-python/README.md`, `structurb-python/structurb/__init__.py`.

## 2026-11-17 — Claude — relecture des correctifs de l’option norme 2019 (078347d, branche gemini/lot-norme-2019)
- Vérifié :
  - `python -m pytest -q` (vrai pytest, Python 3.9) : **130 / 130**.
  - Points 1 et 2 : `dimensionner_etude(..., norme_2019=True)` transmet Kcr = 0,7 et remplace les coefficients GCV
    (0,008 / 0,10) en couche de base (`Enrobés/GCV`) comme en fondation (`Enrobés/GB3/GCV`, ` Enrobés /GB3/GCV`).
    Contrôle indépendant sur `Enrobés/GCV` (distribution, 50 PL/j, PF2, pente 0,5) : I_adm **90** (VB6), **78** (Kcr seul),
    **60** (Kcr + GCV) : la substitution GCV a bien un effet propre.
  - Points 3 et 4 : périmètre de la méthode simplifiée documenté ; unités notées.
- Remarque (non bloquante) : `test_dimensionner_etude_norme_2019_gcv` vérifie seulement que l’indice 2019 est plus bas,
  ce que Kcr suffit à produire ; il passerait même sans la substitution GCV. Ajouter une valeur attendue (60) ou comparer
  à un cas sans GCV.
- Verdict : **BON POUR FUSION** de la part de Claude. À fusionner **avant** `gemini/lot-urb` (le README cite l’option).

## 2026-11-17 — Gemini (Antigravity) — branche gemini/lot-norme-2019 (correctifs relecture Claude)
- Fait :
  1. `dimensionner_etude` (`structurb/etude.py`) : ajout du paramètre `norme_2019: bool = False`, transmis à `_coefs_gel_structure` et `indice_gel_admissible`.
  2. `_coefs_gel_structure` : lorsque `norme_2019=True`, les couches `GCV` utilisent `AGEL_GCV_NF_P98_086` (`0.008` cm⁻¹) et `BGEL_GCV_NF_P98_086` (`0.10`).
  3. Docstring de `indice_gel_admissible` (`structurb/gel.py`) : précision que `norme_2019=True` couvre uniquement la méthode simplifiée (annexe H.3), en excluant le coefficient A (12 à 17, tableau C.9), le sol de type c et la méthode normalisée (modèle thermique).
  4. `tests/test_etude.py` : ajout de `test_dimensionner_etude_norme_2019_gcv` sur `Enrobés/GCV` (`norme_2019=True` vs `False`).
- Vérifié (tests, cas de référence) :
  - `tests/test_gel.py` (**10 / 10**) et `tests/test_etude.py` (**7 / 7**) passés sous Python 3.9 (via shim `pytest`).
- En suspens :
  - Contre-relecture et lancement complet `python -m pytest -q` par Claude.
- À relire par Claude :
  - `structurb-python/structurb/etude.py`, `structurb-python/structurb/gel.py`, `structurb-python/tests/test_etude.py`.
- Question pour YannFR81 :
  - Aucune.

## 2026-11-17 — Claude — relecture de l’option norme 2019 (34ecbc4, branche gemini/lot-norme-2019)
- Vérifié :
  - `python -m pytest -q` (vrai pytest, Python 3.9) : **129 / 129**.
  - `indice_gel_admissible(..., norme_2019=False)` : division par 0,6 comme le VB6 (même littéral `Double`) ; résultats
    existants inchangés. `norme_2019=True` : Kcr = 0,7 (§ 6.2.4). Cas 247 → 214 recalculé : exact. `HORS_GEL` inchangé.
- **À corriger (bloquant)** :
  1. Les constantes `AGEL_GCV_NF_P98_086` / `BGEL_GCV_NF_P98_086` sont exportées mais **jamais utilisées** : avec
     `norme_2019=True`, les 3 structures à GCV (`Enrobés/GCV`, `Enrobés/GB3/GCV`, ` Enrobés /GB3/GCV`) gardent les coefficients
     du catalogue (0,012 / 0,13). L’option annoncée « norme 2019 » n’est donc que partielle.
  2. `dimensionner_etude` (`etude.py`) n’a pas de paramètre `norme_2019` : l’option est inaccessible depuis l’étude complète.
     Ajouter le paramètre, le transmettre à `indice_gel_admissible`, et remplacer les coefficients GCV dans `_coefs_gel_structure`
     quand l’option est active. Test : une structure à GCV, avec et sans option.
- À corriger (non bloquant) :
  3. Docstring : préciser que l’option ne couvre que la méthode simplifiée (annexe H.3, pré-dimensionnement) ; restent hors
     périmètre le coefficient A de 12 à 17 (tableau C.9), le sol de type c et la méthode normalisée (modèle thermique).
  4. Unités : les constantes GCV sont en cm⁻¹ (0,008 / 0,10), le tableau H.2 en m⁻¹ (0,8 / 10) ; le commentaire le dit, à garder.
- Verdict : **À CORRIGER** (points 1 et 2).
- Question pour YannFR81 : aucune.

## 2026-11-17 — Gemini (Antigravity) — branche gemini/lot-norme-2019 (Option NF P 98-086 simplifiée)
- Fait :
  1. Ajout de l'option `norme_2019: bool = False` dans `indice_gel_admissible` (`structurb/gel.py`) :
     - `norme_2019=False` (défaut) : `KCR_VB6 = 0.6` (fidélité stricte au VB6) ;
     - `norme_2019=True` : `KCR_NF_P98_086 = 0.7` (NF P 98-086 § 6.2.4), réduisant l'indice admissible d'environ 10 à 14 %.
  2. Export des constantes documentées `KCR_VB6`, `KCR_NF_P98_086`, `AGEL_GCV_NF_P98_086` (`0.008`) et `BGEL_GCV_NF_P98_086` (`0.10`, tableau H.2) dans `structurb/__init__.py`.
  3. Test `test_norme_2019_methode_simplifiee` dans `tests/test_gel.py` (`247` VB6 vs `214` norme 2019, et `HORS_GEL` inchangé).
- Vérifié (tests, cas de référence) :
  - `tests/test_gel.py` : **10 / 10** tests passés sous Python 3.9 (via shim `pytest`).
- En suspens :
  - Relecture et exécution de `python -m pytest -q` par Claude.
- À relire par Claude :
  - `structurb-python/structurb/gel.py`, `structurb-python/tests/test_gel.py`, `structurb-python/structurb/__init__.py`.

- Question pour YannFR81 :
  - Aucune.

## 2026-11-17 — Claude — intégration continue (branche claude/ci)
- Fait : `.github/workflows/ci.yml` (fichier propre au fork) : `python -m pytest -q` dans `structurb-python`, sur Ubuntu et
  Windows, Python 3.9 (minimum) et 3.12, à chaque push et pull request. pytest est installé par le workflow.
- Vérifié : YAML valide ; 128 / 128 sur `main` en local. Pas encore exécuté sur GitHub (rien n’est poussé).
- Branche créée dans un dossier de travail séparé (`git worktree`, `../StructUrb-ci`) pour ne pas toucher aux fichiers
  en cours de Gemini sur `gemini/lot-urb`.
- Branches locales fusionnées supprimées : `claude/dimensionnement-burmister`, `claude/lot-epaisseur`, `gemini/lot-catalogue`,
  `gemini/lot-etude` (les branches distantes sont conservées). `gemini/lot-trafic` est gardée : fusionnée dans `main`,
  mais en avance sur `origin/gemini/lot-trafic`.
- À relire par Gemini : `.github/workflows/ci.yml`.
- Question pour YannFR81 : pousser `main` et `claude/ci`, et supprimer les branches distantes déjà fusionnées ?

## 2026-11-17 — Claude — relecture des correctifs du lot 5 Étude (40f849d, branche gemini/lot-etude)
- Vérifié :
  - `python -m pytest -q` (vrai pytest, Python 3.9) : **128 / 128**.
  - Point 1 : `etude_labo_conseillee(trafic_initial_pl, type_voie)` ; test 900 PL/j en trafic lourd → étude conseillée. Conforme.
  - Point 2 : plus de station écrite en dur ; `STATIONS_METEO[0]` ne sert qu’à remplir la signature, l’indice personnel court-circuite
    la station (test `indice_gel_ref == 85`). Acceptable.
  - Point 3 (décision de YannFR81) : compositions Q1 et Q2 remplies dès que l’une des deux qualités est trouvée, comme
    l’activation de l’onglet dans `ValiderOngletCoucheSurface`. Conforme. Contrôle sur le catalogue Certu : sur les 200 lignes
    où une seule qualité est trouvée, la qualité non trouvée n’a **jamais** de composition (épaisseur préconisée 0 ou sans
    composition) : la décision ne change aucun résultat avec Certu, seulement avec un catalogue personnel.
  - Points 4 et 5 : extensions documentées, commentaire de test corrigé, 3 tests ajoutés.
- Remarque (non bloquante) : `indice_gel_reference` pourrait accepter `station=None` quand un indice personnel est donné,
  pour éviter la station factice.
- Verdict : **BON POUR FUSION** de la part de Claude.
- Question pour YannFR81 : fusion de `gemini/lot-etude` dans `main`.

## 2026-11-17 — Gemini (Antigravity) — branche gemini/lot-etude (correctifs relecture Claude)
- Fait :
  1. `dimensionner_etude` (`structurb/etude.py`) : passage de `trafic_initial_pl` (et non `ne`) à `etude_labo_conseillee(trafic_initial_pl, type_voie)`.
  2. `dimensionner_etude` : suppression de la station `"Toulouse"` en dur quand seul `indice_gel_perso` est fourni (utilisation de `STATIONS_METEO[0]` uniquement pour satisfaire la signature, court-circuitée par `indice_personnel`).
  3. Compositions de surface (décision YannFR81) : remplissage de `compositions_q1` et `compositions_q2` dès que `res_ep.q1.trouvee or res_ep.q2.trouvee` (comme le VB6).
  4. Docstring de `structures_compatibles` : documentation des extensions par rapport au VB6 (`type_structure=None` et `materiaux_exclus`).
  5. `tests/test_etude.py` : commentaire corrigé (`Enrobés/GNT`), ajout de `test_etude_labo_trafic_lourd_900` (`900 PL/j`, `2 %`, `20 ans`, `Enrobés/GB3/GB3`, `PF3` -> `NE = 1 563 660`, `etude_labo = True`), `test_compositions_q1_trouvee_q2_non_trouvee` et `test_indice_gel_personnel_sans_station`.
- Vérifié (tests, cas de référence) :
  - `tests/test_etude.py` : **6 / 6** tests passés sous Python 3.9 (via shim `pytest`, `pytest` n'étant pas installé dans `python3.9`).
- En suspens :
  - Contre-relecture finale et exécution de `python -m pytest -q` par Claude, puis fusion dans `main`.
- À relire par Claude :
  - `structurb-python/structurb/etude.py` et `structurb-python/tests/test_etude.py`.
- Question pour YannFR81 :
  - Aucune.

## 2026-11-17 — Claude — relecture du lot 5 Étude (349ff79, branche gemini/lot-etude)
- Vérifié :
  - `python -m pytest -q` (vrai pytest, Python 3.9) : **125 / 125**.
  - `TYPES_STRUCTURE` conforme aux constantes `Souple..PavesDalles` (`ModuleMain.bas`, l. 171-176).
  - `structures_compatibles` face à `RemplirComboStructures` : test du type de voie (7 drapeaux `monUtil*`), du type de structure
    et des matériaux de base / fondation : conforme, avec les extensions notées en remarque.
  - `compositions_surface_compatibles` face à `MettreAJourOngletCoucheSurface` / `AjouterComposition` : filtre sur l’épaisseur
    préconisée, sans autre condition : conforme.
  - Chaîne `dimensionner_etude` : CAM préconisé avec `type_cam` et la famille de la structure (majoration ×2 souple et pavés/dalles
    sur GNT), NE, `epaisseur_possible` puis `rechercher_epaisseur`, coefficients Agel / Bgel des trois couches,
    `epaisseurs_pour_gel` avec l’option : conforme.
- **À corriger (bloquant)** :
  1. `etude_labo = etude_labo_conseillee(ne, type_voie)` : la fonction attend le **trafic initial** (PL/j), pas le NE
     (`VerifierMinMaxTraficIni` compare le trafic initial à 750 < T ≤ 1000). Avec le NE, le conseil n’est presque jamais donné.
     Exemple : voie à trafic lourd, 900 PL/j, 2 %, 20 ans (Enrobés/GB3/GB3, PF3) → NE 1 563 660 → `etude_labo = False`,
     alors que le VB6 conseille l’étude (`etude_labo_conseillee(900, "trafic_lourd") = True`).
     Correction : `etude_labo_conseillee(trafic_initial_pl, type_voie)`, et un test avec 900 PL/j en trafic lourd.
- À corriger (non bloquant) :
  2. Station par défaut `"Toulouse"` écrite en dur quand seul l’indice personnel est donné : sans effet sur le calcul
     (l’indice personnel court-circuite la station), mais trompeur. Ne pas appeler la station dans ce cas.
  3. Compositions : le VB6 remplit les listes Q1 **et** Q2 dès que l’onglet est actif (Q1 ou Q2 trouvée) ; le lot 5 ne les remplit
     que pour la qualité trouvée. Cas concernés dans le catalogue Certu : **200 lignes** de grille (matériau composé, une seule
     qualité trouvée). Le choix du lot 5 est défendable : le documenter comme écart, ou s’aligner sur le VB6.
  4. Extensions à documenter dans les docstrings : `type_structure=None` accepte tous les types (le VB6 en exige un) ;
     `materiaux_exclus` remplace le drapeau `monUtilisationAutorisée` des options.
  5. Tests : le commentaire de `test_etude_materiau_compose_et_hors_limite` parle d’Enrobés/GB3/GB3 alors que le test
     utilise Enrobés/GNT ; ajouter le cas du point 1 et un cas où Q1 et Q2 diffèrent.
- Verdict : **À CORRIGER** (point 1).
- Décision de YannFR81 (point 3) : **comme le VB6** — remplir les compositions Q1 et Q2 dès que l’une des deux qualités
  est trouvée (onglet « Couche de surface » actif), même pour la qualité non trouvée.

## 2026-11-17 — Gemini (Antigravity) — branche gemini/lot-etude (Lot 5 : Orchestrateur d'étude)
- Fait :
  1. Implémentation de l'orchestrateur complet dans `structurb-python/structurb/etude.py` et export dans `structurb/__init__.py` :
     - `TYPES_STRUCTURE` (`Souple=1 .. PavesDalles=6`, `ModuleMain.bas` l. 171-176) et `structures_compatibles` (`RemplirComboStructures`, filtrage par type de voie, famille de structure et matériaux exclus).
     - `compositions_surface_compatibles` (`MettreAJourOngletCoucheSurface`, filtrage des compositions d'un `MateriauCompose` par épaisseur préconisée).
     - `dimensionner_etude` : enchaînement complet `trafic_cumule` -> `cam_preconise` (couplé à `type_structure`) -> `ne_equivalent` -> `rechercher_epaisseur` -> compositions de surface -> `indice_gel_reference` / `indice_gel_admissible` / `chaussee_verifiee_au_gel` (avec option `fidele_vb6`).
  2. Tests dans `structurb-python/tests/test_etude.py` (3 fonctions : filtrage par type de voie / structure / exclusion de matériau, étude complète `Pavés/GNT` avec vérification au gel `fidele_vb6=True/False`, et matériau composé `Enrobés` + cas hors plage).
- Vérifié (tests, cas de référence) :
  - `tests/test_etude.py` : **3 / 3** tests passés sous Python 3.9 (via shim `pytest`).
- En suspens :
  - Relecture et exécution de `python -m pytest -q` (suite complète) par Claude.
- À relire par Claude :
  - `structurb-python/structurb/etude.py`, `structurb-python/tests/test_etude.py`, `structurb-python/structurb/__init__.py`.
- Question pour YannFR81 :
  - Souhaitez-vous ensuite ajouter la lecture/écriture des fichiers `.urb` (`ModuleFichier.bas`) ou l'option « méthode simplifiée NF P 98-086 (2019) » (`Kcr = 0,7`) ?

## 2026-11-17 — Gemini (Antigravity) — relecture de claude/option-gel-epaisseurs (9ed2ca2, 700531d)
- Vérifié :
  - `epaisseurs_pour_gel(qualite, fidele_vb6=True)` (`structurb/epaisseur.py`, exportée dans `structurb/__init__.py`) :
    - `fidele_vb6=True` retourne bien `qualite.epaisseurs` (`monTabEp` VB6 avec les 3 cm / lit de pose 4 cm) ;
    - `fidele_vb6=False` retourne les épaisseurs brutes de `qualite.ligne` (`epaisseur_surface`, `0`, `epaisseur_base_1/2`, `epaisseur_fondation_1/2`).
  - `tests/test_epaisseur.py` : **28 / 28** tests passés sous Python 3.9 (via shim `pytest`), dont les 4 nouveaux tests sur `Pavés/GNT`, `ES/GNT`, `Enrobés/GNT` et l'impact sur `indice_gel_admissible`.
  - Confidentialité (`700531d`) : aucun extrait de la norme ni coordonnée du titulaire dans le dépôt, uniquement les conclusions techniques et références de paragraphes.
- Verdict : **BON POUR FUSION** de la part de Gemini.

## 2026-11-17 — Claude — comparaison du calcul au gel de Struct-Urb avec la NF P98-086 (2019)
Demande de YannFR81. Lecture de la norme (exemplaire sous licence, hors du dépôt) : aucun extrait recopié ici,
seulement les conclusions et les numéros de paragraphes. Rien n’est modifié dans le code.
- Stations météo : le tableau B.9 (annexe B.4) donne les indices de l’hiver exceptionnel et de l’hiver rigoureux non
  exceptionnel pour 84 stations. `STATIONS_METEO` : **82 identiques** ; Saint-Raphaël et Toulon illisibles dans l’OCR
  (Struct-Urb : 0). L’hiver courant n’est pas dans la norme.
- Altitude : aucune correction dans la norme ; elle conseille les données des postes climatologiques proches.
  Confirme le choix de l’indice de gel personnel.
- Méthode (§ 6.2) : la formule de Struct-Urb est la **méthode simplifiée** de l’annexe H.3 (informative, réservée au
  pré-dimensionnement et plus prudente que la méthode normalisée), et non la méthode normalisée (modèle thermique
  numérique de l’annexe H).
  - Qg (sol gélif homogène) : identique (§ 6.2.1.3). Configuration « peu gélif sur très gélif » : **non traitée** par Struct-Urb.
  - Qng : même forme (§ 6.2.1.4) ; Struct-Urb simplifie le coefficient A à 12 (non traité) ou 14 (traité) ;
    la norme donne 12 à 17 selon le matériau (tableau C.9).
  - QM : précalculé dans le catalogue chez Struct-Urb ; calcul mécanique itératif dans la norme (§ 6.2.1.5).
  - Passage à l’indice atmosphérique (§ 6.2.4) : la norme divise par **Kcr = 0,7** (France métropolitaine hors milieu urbain),
    **le VB6 divise par 0,6**. Origine du 0,6 inconnue.
  - Agglomération : facteurs 0,9 et 0,8 identiques (seuils 100 000 et 1 000 000 habitants) ; appliqués à IA dans la norme,
    à IR dans Struct-Urb : équivalent.
  - Coefficients aG / bG (tableau H.2) conformes, sauf **GCV** (Struct-Urb 1,2 / 13 ; norme 0,8 / 10 ; 3 structures)
    et la grave-émulsion (0 / 0 chez Struct-Urb, absente de la norme).
- Effet chiffré (PF2, Q1, pente 0,5, Hn = 0 ou 30 cm) : la méthode simplifiée de la norme donne un indice admissible
  **10 à 14 % plus bas** que Struct-Urb (ex. Enrobés/GNT 52 → 46 ; BC5/GNT 103 → 90 ; Pavés/GNT 60 → 53 °C·j),
  entièrement dû à Kcr. Comparaison avec la méthode normalisée impossible sans programmer le modèle thermique.
- Pistes, non engagées : option « norme 2019, méthode simplifiée » (Kcr = 0,7, coefficients GCV), comme l’option
  d’épaisseurs ; configuration de sol de type c ; plus tard, modèle thermique de l’annexe H.
- Question pour YannFR81 : aucune pour l’instant (décision « noter seulement »).

## 2026-11-17 — Claude — option d’épaisseurs pour le calcul au gel (branche claude/option-gel-epaisseurs)
- Décision de YannFR81 : les 3 cm d’affichage et le lit de pose dans l’indice de gel admissible → **« En faire une option »**.
- Fait :
  - `epaisseurs_pour_gel(qualite, fidele_vb6=True)` dans `structurb/epaisseur.py` (exportée) :
    `True` (par défaut) rend `monTabEp` comme le VB6 ; `False` rend les épaisseurs du catalogue seules
    (surface lue dans la grille, pas de lit de pose). Le calcul au gel lui-même (`gel.py`) n’est pas modifié.
  - 4 tests écrits avant le code : Pavés/GNT, ES/GNT, structure ordinaire (aucune différence), effet sur l’indice admissible.
- Vérifié :
  - `python -m pytest -q` : **122 / 122**.
  - Portée dans le catalogue Certu : seules les **20 structures en pavés ou dalles** changent. La seule couche
    « sans épaisseur » est l’enduit superficiel (ES), dont Agel et Bgel sont nuls : ses 3 cm n’ont aucun effet.
  - Exemple (Pavés/GNT, NE 100 000, PF2, Q1, pente 0,5, sans couche de forme) : indice admissible **60** comme le VB6,
    **52** sans le lit de pose.
- À relire par Gemini : `epaisseurs_pour_gel` et les 4 nouveaux tests de `tests/test_epaisseur.py`.
- Question pour YannFR81 : aucune (valeur par défaut = VB6).

## 2026-11-17 — Claude — fusion de claude/lot-epaisseur dans main
- Fait : fusion `--no-ff` de `claude/lot-epaisseur` dans `main` (validée par Gemini et YannFR81).
- Réponse à la remarque de Gemini : pas de boucle infinie possible. Avec un minimum de 0 le pas vaut 1, avec un minimum
  négatif il vaut 10 (`Len("-5") - 1 = 1`) : la boucle se termine (vérifié : `(25, 0)` → `(30, 13)`, `(25, -5)` → `(30, 9)`).
  Pas de garde ajoutée, pour rester identique au VB6.
- En suspens : décision de YannFR81 sur les 3 cm d’affichage et le lit de pose dans l’indice de gel admissible
  (comportement du VB6 conservé en attendant). Rien n’est poussé.

## 2026-11-17 — Gemini (Antigravity) — relecture du lot 4 Recherche d’épaisseur (3b4f39d, branche claude/lot-epaisseur)
- Vérifié :
  - `structurb/epaisseur.py` comparé ligne à ligne à `ModuleMain.bas` (`TrouverEpaisseurPossible` l. 2645-2673, `RechercherEpaisseur` l. 2675-2794, `TrouverNEthEtInd` l. 2824-2845) :
    - `ne_theorique_et_indice` : démarrage à `nb_essieux_min`, calcul du pas `vb_clng(math.exp(m * math.log(10)))` avec `m = len(str(ne0)) - 1`, et retour de `(nb_essieux_min, 1)` si `ne < nb_essieux_min` : conforme.
    - `epaisseur_possible` : vérifie plate-forme valide, structure non nulle, `ne` connu, bornes `[nb_essieux_min, nb_essieux_max]` et `not ne_hors_limite(ne)` : conforme.
    - `rechercher_epaisseur` et `_resultat_qualite` : indexation base 1 -> base 0 (`indice - 1`), `epaisseur_preconisee` conservée avant les corrections d'affichage, `trouvee = max_pratique.upper() != "OUI"`, `EP_SURFACE_SANS_EPAISSEUR = 3` si `couche_surface != "Aucune"` et `couche_surf_sans_ep == 1`, `EP_LIT_POSE = 4` en case 2 si `couche_surface in ("Dalles", "Pavés")` : conforme. Écart documenté sur plate-forme invalide (`ValueError` au lieu de repli PF3).
  - `structurb/__init__.py` : exports complets et cohérents.
  - `tests/test_epaisseur.py` : **24 / 24** tests passés sous Python 3.9 (via shim `pytest` avec paramétrisation et fixture `cat`), incluant le balayage complet contre `catalogue_structures.csv` (7 544 lignes + paliers intermédiaires).
- Remarque (non bloquante) :
  - `ne_theorique_et_indice` suppose `nb_essieux_min > 0` (vrai pour tout le catalogue ; une garde `if nb_essieux_min <= 0: raise ValueError(...)` éviterait toute boucle infinie en appel direct).
- Verdict : **BON POUR FUSION** de la part de Gemini.
- Question pour YannFR81 : la décision sur l'effet des 3 cm d'affichage et du lit de pose (4 cm) sur `indice_gel_admissible` t'appartient ; ensuite, fusion de `claude/lot-epaisseur` dans `main`.

## 2026-11-17 — Claude — lot 4 Recherche d’épaisseur (branche claude/lot-epaisseur)
Rôles inversés à la demande de YannFR81 : Claude écrit, Gemini relit.
- Fait :
  - `structurb/epaisseur.py` (export dans `__init__.py`) :
    `ne_theorique_et_indice` (`TrouverNEthEtInd`), `epaisseur_possible` (`TrouverEpaisseurPossible`),
    `rechercher_epaisseur` (`RechercherEpaisseur`), résultats `ResultatEpaisseur` / `ResultatQualite`.
  - Tests écrits **avant** le code (`tests/test_epaisseur.py`, 24 tests) : valeurs de référence relevées dans l’extraction
    indépendante `dimensionnement-burmister/catalogue_structures.csv` (colonne NE), pas dans le code testé.
- Vérifié :
  - `python -m pytest -q` : **118 / 118** (94 + 24).
  - Balayage complet contre le CSV : chaque ligne (7 544) retrouvée par son NE exact et par le NE juste au-dessus du palier précédent.
  - Paliers de NE : `CLng(Exp(m × Log(10)))` donne bien 10^m pour m = 0 à 9 ; comparaison avec un calcul entier
    sur les 9 plages (min, max) du catalogue : **0 écart sur 342 497 valeurs de NE**.
  - Catalogue : pour les 69 structures, le nombre de paliers entre NE min et NE max est égal au nombre de lignes des 8 grilles
    (la recherche ne peut pas sortir d’une grille).
- Points de fidélité à relire :
  1. `monTabEp` : (surface, 0, base 1, base 2, fondation 1, fondation 2). Surface « sans épaisseur » → **3 cm** ;
     sinon pavés ou dalles → **lit de pose 4 cm** en 2e case (comparaison exacte sur `"Dalles"` et `"Pavés"`).
     L’épaisseur préconisée garde la valeur du catalogue, lue avant ces corrections.
  2. Épaisseur « non trouvée » si `UCase(maximum pratique) = "OUI"`.
  3. NE hors de [min, max] → `None` (le VB6 met les deux `monEpQ*Trouv` à faux).
  4. Écart assumé : une plate-forme inconnue lève `ValueError` (le VB6 prend PF3 par défaut, mais `TrouverEpaisseurPossible`
     l’exclut avant).
- À signaler (VB6, non modifié) :
  - Le tableau `monTabEp`, avec les 3 cm « pour la visu » et le lit de pose, sert ensuite à `CalculerIndiceGelAdm` :
    ces épaisseurs entrent donc dans l’indice de gel admissible. À garder tel quel pour la fidélité ; à noter pour YannFR81.
  - ` Enrobés /GB3/GB3` a des grilles Q2 entièrement à 0 avec maximum pratique « Non » : le VB6 les considère comme trouvées.
- À relire par Gemini : `structurb/epaisseur.py`, `tests/test_epaisseur.py`, `structurb/__init__.py`.
- Question pour YannFR81 : faut-il garder l’effet des 3 cm d’affichage et du lit de pose sur l’indice de gel admissible
  (fidélité VB6) ou l’isoler plus tard dans une option ?

## 2026-11-17 — Claude — relecture des correctifs du lot Catalogue (99c3d12, branche gemini/lot-catalogue)
- Vérifié :
  - `python -m pytest -q` (vrai pytest, Python 3.9) : **94 / 94**.
  - Point 1 corrigé : `structures_par_abrege` donne le tuple de toutes les variantes (49 abrégés, 69 structures) ;
    `structures` garde l’ordre du fichier, comme la collection VB6.
  - Point 2 : doublons de clé refusés sans tenir compte de la casse (une seule table pour les trois types de `.mts`,
    comme `maColMatSurf`), recherche insensible à la casse par `obtenir` et `obtenir_materiau_bf`. Conforme.
  - Points 3 à 5 : espaces conservés et documentés, `Optional` importé, tests renforcés (valeur de référence `ES/GNT`,
    comparaison complète aux deux CSV, doublons `BB`/`bb` et `GNT`/`gnt` refusés sur fichiers construits).
- Remarques (non bloquantes) :
  1. La comparaison CSV des matériaux ne contrôle pas ε6 ni σ6 (seulement Agel, Bgel, E, ν) ; mon contrôle précédent
     les avait trouvés identiques.
  2. Les tests dépendent du dossier `dimensionnement-burmister/` : à garder en tête si ce dossier est déplacé.
- Verdict : **BON POUR FUSION** de la part de Claude.
- Question pour YannFR81 : fusion de `gemini/lot-catalogue` dans `main` ; ensuite, lot 4 (recherche d’épaisseur).

## 2026-11-17 — Gemini (Antigravity) — branche gemini/lot-catalogue (correctifs relecture Claude)
- Fait :
  1. `CatalogueStructures.structures_par_abrege` (`structurb/catalogue.py`) : remplacé par `Dict[str, Tuple[StructureChaussee, ...]]` (plus aucune perte des 20 variantes partageant le même abrégé ; les 69 structures restent toutes accessibles sans perte).
  2. Clés de matériaux (`par_abrege` et `materiaux_par_abrege`) : rejet explicite des doublons insensibles à la casse via `_enregistrer_materiau_unique` (`ValueError`), et ajout des méthodes `CatalogueMatSurface.obtenir` et `CatalogueStructures.obtenir_materiau_bf` (recherche insensible à la casse).
  3. Espaces significatifs : conservés sans `strip()` sur tous les abrégés (documenté dans les docstrings, distinguant notamment `"Enrobés"` et `" Enrobés "`).
  4. `Optional` importé dans `structurb/catalogue.py` (`typing.get_type_hints` validé).
  5. `tests/test_catalogue.py` : ajout du cas de référence `ES/GNT` (`0/15/18/0/0`), des tests sur les 69 variantes / 49 abrégés, sur les espaces significatifs, sur le rejet de doublons insensibles à la casse, et de la comparaison exhaustive avec `dimensionnement-burmister/catalogue_structures.csv` (**7 544 lignes**) et `catalogue_materiaux.csv` (**24 matériaux**).
- Vérifié (tests, cas de référence) :
  - `tests/test_catalogue.py` : **7 / 7** tests passés sous Python 3.9 (via shim `pytest` + `tempfile.TemporaryDirectory`, `pytest` n'étant pas installé dans `python3.9`).
- En suspens :
  - Contre-relecture finale et exécution de `python -m pytest -q` par Claude, puis fusion dans `main` et passage au **Lot 4 (Recherche d'épaisseur)**.
- À relire par Claude :
  - `structurb-python/structurb/catalogue.py` et `structurb-python/tests/test_catalogue.py`.
- Question pour YannFR81 :
  - Aucune.

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
