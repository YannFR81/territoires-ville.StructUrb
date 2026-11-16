# Dimensionnement de chaussées — solveur de Burmister + catalogue Struct-Urb

Outil de prédimensionnement des chaussées neuves selon la méthode rationnelle française (NF P98-086, mai 2019) : trafic → NE → structure → vérification mécanique → vérification au gel. Il tient en une page web autonome, sans serveur ni installation.

Version 1.0 — 16 novembre 2026.

## Signature

**Pour une fonction publique augmentée, pas remplacée.**

Développé par YannFR81, agent territorial au sein d'un conseil départemental, et Claude, IA d'Anthropic, du 12 au 16 novembre 2026. L'agent a posé le besoin, piloté et vérifié. L'IA a codé, calculé et testé.

Données et méthode d'origine : logiciel Struct-Urb du CERTU, publié par le Cerema sous licence GPL v3 (https://github.com/CEREMA/territoires-ville.StructUrb).

Ce dossier est un ajout au fork : le code VB6 d’origine, à la racine, n’est pas modifié. Il est distinct du portage Python fidèle de Struct-Urb (`structurb-python/`).

## Licence

GNU GPL v3 (fichier `LICENSE` à la racine du dépôt), comme Struct-Urb dont cet outil reprend le catalogue de structures, les stations météo et la méthode de vérification au gel. Fourni sans garantie.

## Contenu du dossier

| Fichier | Rôle |
|---|---|
| `web/dimensionnement_chaussees.html` | La page complète, à ouvrir dans un navigateur |
| `web/engine.js` | Solveur multicouche de Burmister (JavaScript) |
| `web/methode.js` | Valeurs admissibles, matériaux, trafic, gel, recherche d'épaisseur |
| `web/app.js`, `web/app.src.html`, `web/build.py` | Interface et assemblage de la page |
| `web/catalogue_data.js` | Catalogue Struct-Urb (57 structures) |
| `web/test_annexe_I.js`, `web/annexe_I.json` | Cas tests de l'annexe I rejoués sur le moteur JavaScript |
| `burmister.py` | Solveur de référence en Python |
| `valid_annexe_I.py`, `valid_boussinesq.py`, `valid_multicouche.py` | Scripts de validation |
| `catalogue.py`, `catalogue_*.csv` | Décodeur des fichiers binaires Struct-Urb et catalogue exporté |
| `calage.py`, `compare_catalogue.py`, `methode.py` | Recalage sur le catalogue CERTU (paramètres de 1994) |

## Validation

- **Annexe I de la NF P98-086 : 2019** : les 8 cas tests (souple, bitumineux, semi-rigide, rigide ; interfaces collées, semi-collées et glissantes) sont reproduits, 20 valeurs sur 20 dans les tolérances de la norme, par le solveur Python et par le moteur JavaScript.
  - `python3 valid_annexe_I.py`
  - `cd web && node test_annexe_I.js`
- **Solution exacte de Boussinesq** : écart relatif de l’ordre de 10⁻¹² (2,3·10⁻¹² au plus) (`valid_boussinesq.py`).
- **Catalogue Struct-Urb** : en référentiel « CERTU / 1994 », les épaisseurs du catalogue sont retrouvées à 1 cm près pour les structures bitumineuses, semi-rigides et béton.

## Référentiels de la page

- **NF P98-086 : 2019** : matériaux de l'annexe D, ks du tableau C.2, CAM et risques de l'annexe B (indicatifs, modifiables), interfaces du chapitre 8, points de calcul à l'axe de roue et au centre du jumelage, gel selon l'annexe H.3 avec calcul de la quantité de gel mécanique.
- **CERTU / méthode 1994** : paramètres recalés sur le catalogue Struct-Urb, pour retrouver ses épaisseurs.

## Limites

- Outil de prédimensionnement, non certifié : il ne remplace ni Alizé-LCPC ni une étude de dimensionnement.
- Structures mixtes : seule la première phase du calcul en deux phases (8.6) est faite. Structures inverses : la majoration de la valeur admissible sur la GNT (8.7) n'est pas appliquée.
- Gel : méthode simplifiée de l'annexe H.3, plus sévère que le modèle thermique normalisé (6.2.2), qui n'est pas programmé.
- Risque de calcul des fondations en béton : la ligne spécifique du tableau B.7 n'est pas appliquée.
- Sols traités : la norme ne donne pas de valeurs de référence ; E et σ6 sont à saisir d'après l'étude de laboratoire.
- Le code Python `methode.py` ne contient que les paramètres de 1994 ; le référentiel 2019 est dans `web/methode.js`.
- Le texte de la norme NF P98-086 n'est pas joint : il est soumis au droit d'auteur de l'AFNOR.
