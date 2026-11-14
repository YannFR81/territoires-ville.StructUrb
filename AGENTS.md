# Struct-Urb — portage Python (fork YannFR81)

Instructions pour les agents d'IA travaillant sur ce dépôt.
Lu par Gemini / Antigravity (`AGENTS.md`) et par Claude (via `CLAUDE.md`).

Amont : CEREMA/territoires-ville.StructUrb (code VB6 de Struct-Urb, CERTU, GPL v3, plus maintenu).

## Le projet

Portage Python de **Struct-Urb** : dimensionnement des structures de chaussées urbaines.
Struct-Urb fonctionne **par catalogue** : les structures et leurs trafics admissibles sont précalculés
dans `Certu.str` (fichier binaire), le logiciel calcule le trafic, le NE, puis cherche l'épaisseur
et vérifie le gel. **Il n'y a pas de solveur Burmister dans le code d'origine** : un module de type Alizé
serait un ajout ultérieur, à valider séparément.

- Code d'origine VB6 à la racine : **ne pas le modifier**, il sert de spécification.
- Portage Python : dossier **`structurb-python/`** (paquet `structurb`, tests dans `tests/`).
- Lancer les tests : `cd structurb-python && python -m pytest -q`.

## Ordre des lots
1. **Trafic** (`structurb/trafic.py`) : trafic cumulé / initial, domaine de validité, NE, CAM. ← test de binôme en cours
2. Gel : indice de gel de référence et admissible (`CalculerIndiceGelRef`, `CalculerIndiceGelAdm`, stations météo).
3. Lecture du catalogue `Certu.str` et des matériaux `Certu.mts` (`OuvrirFichierStructures`, `OuvrirFichierMatSurface`).
4. Recherche d'épaisseur (`RechercherEpaisseur`, `TrouverNEthEtInd`).

## Fidélité au VB6
- `CLng` arrondit **au pair le plus proche** (2,5 → 2 ; 3,5 → 4).
- `Single` (float32) est utilisé pour certains coefficients (CAM, croissance) : signaler tout écart dû à la précision.
- Garder la référence de la fonction VB d'origine dans la docstring de chaque fonction Python.

## Règles communes à tous les agents (Claude, Gemini / Antigravity, autres)

- **Propriétaire du fork :** YannFR81, projeteur routier (conception routière, AutoCAD / COVADIS).
  C'est lui qui tranche les choix métier et de terminologie.
- **Crédit :** uniquement sous le pseudo **YannFR81**, jamais de nom réel (commits, README, feuilles de route, PR).
- **Langue :** français pour la documentation, les messages de commit et les échanges ; apostrophe typographique ’ dans les textes d'interface.
- **Relations avec le dépôt d'origine (amont) :** proposer d'abord par une *issue* ; n'ouvrir une PR qu'après
  réponse des mainteneurs. Ne jamais pousser ni ouvrir de PR vers l'amont sans accord explicite de YannFR81.
- **Fichiers propres au fork :** `AGENTS.md`, `CLAUDE.md`, `NOTES_REVUE.md` (et `CONTEXTE_YANNFR81.md` le cas échéant)
  ne doivent **jamais** figurer dans une branche proposée à l'amont. Créer les branches destinées à l'amont
  à partir de la branche de l'amont (`upstream/<branche>`), ou retirer ces fichiers avant la PR.
- **Pas de force-push** sur une branche dont une PR est ouverte.

## Travail en binôme

1. Un agent écrit, **l'autre relit** : aucun agent ne valide seul son propre travail.
2. Calculs normatifs ou moteur de calcul : écrire ou compléter d'abord les **tests sur cas de référence**
   (guides, abaques, exemples publiés), puis modifier le code. Un résultat de référence qui change = arrêt et signalement.
3. À la fin de chaque session, ajouter une entrée en tête de `NOTES_REVUE.md`
   (date, agent, branche, fait / vérifié / en suspens / question pour YannFR81).
4. Avant de commencer, lire `NOTES_REVUE.md` pour reprendre là où l'autre agent s'est arrêté.
