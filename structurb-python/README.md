# structurb-python

Portage Python fidèle du moteur de calcul de **Struct-Urb** (CERTU / CEREMA), logiciel de dimensionnement des structures de chaussées urbaines par catalogue.

## Modules disponibles

- `structurb.trafic` : trafic cumulé, trafic initial, bornes par type de voie, CAM préconisé et majorations, nombre d'essieux équivalents `NE` (`vb_clng`, `_vb_csng`).
- `structurb.gel` : 84 stations météo, indice de gel de référence (et `indice_personnel`), `Qng`, `Qg`, indice de gel admissible (mode VB6 `Kcr = 0.6` et option `norme_2019=True` NF P 98-086 `Kcr = 0.7`), vérification au gel.
- `structurb.catalogue` : lecture binaire des catalogues `Certu.str` (69 structures, 14 matériaux base/fondation) et `Certu.mts` (10 matériaux de surface).
- `structurb.epaisseur` : `ne_theorique_et_indice`, `epaisseur_possible`, `rechercher_epaisseur` (Q1/Q2), option `epaisseurs_pour_gel(..., fidele_vb6=True|False)`.
- `structurb.etude` : orchestrateur complet `dimensionner_etude`, filtrage `structures_compatibles`, `compositions_surface_compatibles`.
- `structurb.urb` : lecture/écriture des fichiers d'étude `*.urb` (`lire_urb`, `ecrire_urb`) et génération de note de calcul Markdown (`formater_note_calcul`).

## Exemple rapide

```python
from structurb import (
    dimensionner_etude,
    ouvrir_fichier_mat_surface,
    ouvrir_fichier_structures,
)

cat_str = ouvrir_fichier_structures("../Certu.str")
cat_mts = ouvrir_fichier_mat_surface("../Certu.mts")
paves_gnt = cat_str.structures[49]

res = dimensionner_etude(
    catalogue_structures=cat_str,
    catalogue_surfaces=cat_mts,
    structure=paves_gnt,
    type_voie="desserte",
    trafic_initial_pl=12,
    croissance_pct=2,
    duree_ans=20,
    plate_forme="PF2",
    station="Toulouse",
    hiver="HRNE",
    taille_agglo="moyenne",
    pente_sol_pourcent=0.5,
)
print(res.ne_equivalent, res.epaisseur.q1.epaisseurs, res.gel_q1)
```

## Lancer les tests

```bash
cd structurb-python
python -m pytest -q
```
