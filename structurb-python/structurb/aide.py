"""Aide en ligne et documentation.

- Aide d’origine du logiciel (CERTU, licence GPL v3) : fichiers ``Onglet*.rtf`` à la racine du dépôt,
  affichés par le VB6 dans chaque onglet ; convertis ici en texte (les images ne sont pas reprises).
- Documentation propre au portage Python : fonctionnement du calcul, place de la norme NF P98-086,
  utilisation (page, ligne de commande, assistants IA) et limites. La partie « norme » est un résumé
  rédigé : aucun extrait de la norme n’est reproduit.
"""

from __future__ import annotations

import re
from html import escape
from pathlib import Path
from typing import Dict, List, Optional, Union

# Rubrique → (fichier RTF du VB6, titre)
SUJETS_CERTU: Dict[str, tuple] = {
    "voie": ("OngletVoie.rtf", "Type d’aménagement et type de voie"),
    "trafic": ("OngletTrafic.rtf", "Trafic poids lourds"),
    "cam": ("OngletCAM.rtf", "Coefficient d’agressivité moyen (CAM)"),
    "structure": ("OngletStructure.rtf", "Structures de chaussée"),
    "surface": ("OngletCouche de Surface.rtf", "Couche de surface"),
    "plateforme": ("OngletPlateforme.rtf", "Plate-forme support de chaussée"),
    "gel": ("OngletGel.rtf", "Vérification au gel-dégel"),
}

# Tableaux qui étaient des images dans l’aide d’origine
_IMAGES_NON_REPRISES = {
    "plateforme": "les tableaux de classe de portance selon les essais et selon la déflexion",
    "gel": "le tableau de classement de la gélivité des sols selon leur nature",
}

_IGNORER = {
    "fonttbl", "colortbl", "stylesheet", "listtable", "listoverridetable", "info", "pict", "object",
    "objdata", "themedata", "colorschememapping", "latentstyles", "datastore", "xmlnstbl", "rsidtbl",
    "generator", "mmathPr", "pgdsctbl", "filetbl", "revtbl", "pntext", "pntxta", "pntxtb", "header",
    "footer", "fldinst",
}
_JETON = re.compile(r"\\([a-zA-Z]+)(-?\d+)? ?|\\'([0-9a-fA-F]{2})|\\(.)", re.S)


def rtf_texte(data: bytes) -> str:
    """Convertit un document RTF (cp1252) en texte simple : paragraphes, puces, accents.

    Les groupes de mise en forme, les polices et les images sont ignorés.
    """
    s = data.decode("latin-1")
    out: List[str] = []
    pile: List[bool] = []
    ignorer, i, n = False, 0, len(s)
    while i < n:
        c = s[i]
        if c == "{":
            pile.append(ignorer)
            i += 1
            if s.startswith("\\*", i):
                ignorer = True
        elif c == "}":
            ignorer = pile.pop() if pile else False
            i += 1
        elif c == "\\":
            m = _JETON.match(s, i)
            i = m.end()
            if m.group(3):
                if not ignorer:
                    out.append(bytes([int(m.group(3), 16)]).decode("cp1252", "replace"))
                continue
            if m.group(4):
                if not ignorer and m.group(4) in "\\{}":
                    out.append(m.group(4))
                elif not ignorer and m.group(4) == "~":
                    out.append("\u00a0")
                continue
            mot, arg = m.group(1), m.group(2)
            if mot in _IGNORER:
                ignorer = True
            elif ignorer:
                pass
            elif mot in ("par", "line", "sect"):
                out.append("\n")
            elif mot == "tab":
                out.append("\t")
            elif mot == "u" and arg is not None:
                v = int(arg)
                out.append(chr(v + 65536 if v < 0 else v))
                if i < n and s[i] == "?":
                    i += 1
            elif mot == "bullet":
                out.append("•")
            elif mot in ("lquote", "rquote"):
                out.append("’")
        elif c in "\r\n":
            i += 1
        else:
            if not ignorer:
                out.append(c)
            i += 1
    t = "".join(out)
    # Puces de la police Symbol (« · ») et caractères privés de Wingdings / Symbol
    t = re.sub(r"[\uf000-\uf0ff]+", "•", t)
    t = t.replace("\u00b7\t", "• ").replace("\t", " ").replace("\ufffd", "")
    t = re.sub(r"•\s*•+", "•", t)
    t = re.sub(r"(?m)^[  ]*[·•][  ]*", "• ", t)
    t = re.sub(r"[ \u00a0]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def aide_certu(dossier: Union[str, Path]) -> Dict[str, Dict[str, str]]:
    """Aide d’origine par rubrique : ``{sujet: {"titre", "texte"}}`` (fichiers RTF du dossier donné)."""
    d = Path(dossier)
    res: Dict[str, Dict[str, str]] = {}
    for sujet, (fichier, titre) in SUJETS_CERTU.items():
        texte = rtf_texte((d / fichier).read_bytes())
        if sujet in _IMAGES_NON_REPRISES:
            texte += (
                f"\n\n(Note du portage : {_IMAGES_NON_REPRISES[sujet]} figurai(en)t en image dans l’aide d’origine ; "
                "tableau non repris ici, voir l’aide du logiciel Struct-Urb ou le guide de référence.)"
            )
        res[sujet] = {"titre": titre, "texte": texte}
    return res


def texte_vers_html(texte: str) -> str:
    """Paragraphes et listes à puces HTML à partir du texte converti."""
    blocs: List[str] = []
    puces: List[str] = []

    def vider() -> None:
        if puces:
            blocs.append("<ul>" + "".join(f"<li>{escape(p)}</li>" for p in puces) + "</ul>")
            puces.clear()

    for ligne in texte.split("\n"):
        l = ligne.strip()
        if not l:
            vider()
            continue
        if l.startswith("•"):
            puces.append(l.lstrip("• ").strip())
        else:
            vider()
            blocs.append(f"<p>{escape(l)}</p>")
    vider()
    return "\n".join(blocs)


# --- Documentation propre au portage -------------------------------------------------------------

DOCUMENTATION: List[Dict[str, str]] = [
    {
        "id": "fonctionnement",
        "titre": "Fonctionnement du logiciel",
        "html": """
<p>Struct-Urb dimensionne une chaussée urbaine <strong>par catalogue</strong> : il ne fait pas de calcul mécanique.
Les épaisseurs ont été calculées à l’avance par le CERTU pour chaque structure, chaque classe de plate-forme
et chaque niveau de trafic ; le logiciel calcule le trafic, choisit la bonne ligne du catalogue, puis vérifie le gel.</p>
<ol>
<li><strong>Trafic cumulé.</strong> À partir du trafic initial T (poids lourds par jour et par sens à la mise en service),
du taux de croissance annuel τ (0 à 5 %, croissance <em>linéaire</em>) et de la durée de service n (années) :
<br><code>Tcum = 365 × T × [ n + τ × n × (n − 1) / 2 ]</code>.
Chaque type de voie a une plage de trafic normale et une plage tolérée ; entre 750 et 1 000 PL/j, sur les voies à
trafic lourd, les voies bus et les giratoires à trafic lourd, une étude en laboratoire est conseillée.</li>
<li><strong>Nombre d’essieux équivalents.</strong> <code>NE = Tcum × CAM</code>. Le CAM préconisé dépend du type de voie
et de la famille de structure ; il est doublé pour les structures souples et pour les pavés ou dalles sur GNT.
Au-delà de 10 000 000, le NE sort du domaine de Struct-Urb.</li>
<li><strong>Choix de la ligne du catalogue.</strong> Chaque structure a 8 grilles (PF1, PF2, PF2+, PF3, chacune en Q1 et Q2)
et une ligne par <em>palier</em> de NE : 1 000, 2 000 … 9 000, 10 000, 20 000 … depuis le NE minimum de la structure.
Le logiciel retient le palier immédiatement supérieur ou égal au NE calculé (le « NE théorique »).
La ligne donne les épaisseurs (surface, base en une ou deux couches, fondation en une ou deux couches), la quantité
de gel mécanique Qm, et deux indicateurs : minimum technologique et maximum pratique. Si le maximum pratique vaut
« Oui », l’épaisseur est considérée comme non trouvée.</li>
<li><strong>Qualités Q1 et Q2.</strong> Q1 correspond à un chantier courant, Q2 à un chantier difficile, où la mise en œuvre est
moins bien maîtrisée : les épaisseurs Q2 sont égales ou plus fortes.</li>
<li><strong>Couche de surface.</strong> Pour les enrobés, l’épaisseur préconisée est déclinée en compositions possibles
(BBSG, BBM, BBTM…). Pour les pavés et dalles, un lit de pose de 4 cm est ajouté ; un enduit superficiel n’a pas d’épaisseur.</li>
<li><strong>Vérification au gel-dégel.</strong>
<br>Indice de référence <code>IR</code> : indice de la station météo pour l’hiver choisi (exceptionnel, rigoureux non exceptionnel
ou courant), multiplié par 1 ; 0,9 ou 0,8 selon la taille de l’agglomération — ou indice personnel issu de relevés locaux.
<br>Indice de gel admissible : <code>IA = 10 + (AH × Q + BH)² / 0,6</code>, avec <code>AH = 1 + Σ a × e</code> et <code>BH = Σ b × e</code>
(e : épaisseurs des couches en cm, a et b : coefficients de gel des matériaux) et <code>Q = Qm + Qng + Qg</code> :
Qng, protection apportée par la couche de forme non gélive, <code>A × Hn² / (Hn + 10)</code> avec A = 0,12 (non traitée) ou 0,14 (traitée) ;
Qg, selon la pente p de l’essai de gonflement du sol : hors gel si p ≤ 0,05 ; 4 si p ≤ 0,25 ; 1/p si p ≤ 1 ; 0 au-delà.
<br>La chaussée est protégée si <code>IR ≤ IA</code>. Le calcul est fait séparément pour Q1 et pour Q2.</li>
</ol>
<p>Ce portage reproduit le logiciel d’origine à l’identique, y compris ses arrondis (calculs en simple précision et
arrondi « au pair » de Visual Basic). Chaque étape est vérifiée par des tests automatiques, contrôlés contre le code VB6
et contre une extraction indépendante du catalogue.</p>
""",
    },
    {
        "id": "norme",
        "titre": "La norme NF P98-086 et Struct-Urb",
        "html": """
<p>La <strong>NF P98-086</strong> (AFNOR, version de 2019) est la norme française de dimensionnement structurel des chaussées
routières. Elle reprend la méthode rationnelle française : calcul des contraintes et déformations dans un modèle
multicouche élastique, critères de tenue propres à chaque famille de matériaux, prise en compte d’un risque de calcul,
puis vérification au gel-dégel.</p>
<p><strong>Ce que fait Struct-Urb.</strong> Il ne fait pas ce calcul mécanique : il lit un catalogue d’épaisseurs calculé à
l’avance par le CERTU pour le milieu urbain, avant la version de 2019 de la norme. Les épaisseurs du catalogue ne sont
donc pas recalculées selon la norme de 2019. Le module séparé <code>dimensionnement-burmister</code> du dépôt permet,
lui, un calcul mécanique.</p>
<p><strong>Vérification au gel.</strong> La formule de Struct-Urb a la même forme que la <em>méthode simplifiée</em> de l’annexe H
de la norme (annexe informative, prévue pour le pré-dimensionnement et plus prudente que la méthode normalisée, qui utilise
un modèle thermique numérique). Points communs et différences :</p>
<ul>
<li>sensibilité au gel du sol homogène (pente de gonflement), protection de la couche de forme et somme des quantités de gel :
même principe ;</li>
<li>passage à l’indice atmosphérique : Struct-Urb divise par <strong>0,6</strong>, la norme par <strong>Kcr = 0,7</strong>
(France métropolitaine, hors milieu urbain) ; l’indice admissible de la norme est donc plus bas de 10 à 14 % environ ;</li>
<li>agglomérations : mêmes facteurs 0,9 et 0,8 (au-delà de 100 000 et de 1 000 000 d’habitants) ; la norme les applique à
l’indice admissible, Struct-Urb à l’indice de référence, ce qui revient au même ;</li>
<li>coefficients de gel des matériaux : identiques, sauf pour la grave-cendres volantes (GCV) ;</li>
<li>non repris par Struct-Urb : sol peu gélif sur sol très gélif, coefficient de protection propre à chaque matériau de couche
de forme, calcul mécanique de la quantité de gel Qm, méthode normalisée (modèle thermique).</li>
</ul>
<p><strong>Option « norme 2019 ».</strong> Cochée, elle applique Kcr = 0,7 et les coefficients GCV de la norme (méthode simplifiée).
Sans elle, le calcul est celui du logiciel d’origine.</p>
<p><strong>Stations météo.</strong> La table des 84 stations de Struct-Urb a été comparée à celle de l’annexe B de la norme :
82 valeurs identiques, 2 illisibles dans la copie consultée. La norme recommande de préférer les relevés des postes
climatologiques proches du projet : c’est le rôle de l’indice de gel personnel, en particulier en altitude.</p>
<p class="note">Résumé rédigé pour cette documentation : aucun extrait de la norme n’est reproduit. Se reporter au texte
officiel (AFNOR) pour toute application réglementaire.</p>
""",
    },
    {
        "id": "utilisation",
        "titre": "Utilisation",
        "html": """
<p><strong>Dans cette page.</strong> Choisir le type de voie (la liste des structures s’adapte), la structure, la plate-forme
et le trafic, puis, pour vérifier le gel, une station (ou un indice personnel) et la pente du sol. « Calculer » affiche le
résumé, la note de calcul et les boutons de téléchargement (note HTML imprimable, coupe DXF pour AutoCAD ou COVADIS).
Le calcul se fait dans le navigateur : aucune donnée n’est envoyée.</p>
<p><strong>En ligne de commande.</strong> <code>python -m structurb etude …</code>, <code>structures</code>, <code>stations</code>,
<code>aide [sujet]</code>, <code>page</code> ; voir <code>python -m structurb --help</code>.</p>
<p><strong>Pour un assistant IA du navigateur.</strong> Remplir le formulaire (chaque champ a une étiquette et un nom stables),
ou appeler <code>await window.structurb.calculer({…})</code> ; <code>window.structurb.structures(type_voie)</code>,
<code>stations()</code> et <code>aide(sujet)</code> donnent les listes et l’aide ; l’outil <code>dimensionner_chaussee</code>
est décrit en JSON Schema et déclaré via WebMCP quand le navigateur le propose.</p>
""",
    },
    {
        "id": "limites",
        "titre": "Limites",
        "html": """
<ul>
<li>Catalogue CERTU seul : les fichiers de structures personnels ne sont pas chargés dans la page.</li>
<li>Pas de calcul mécanique : les épaisseurs sont celles du catalogue (voir « La norme NF P98-086 et Struct-Urb »).</li>
<li>Correction d’altitude non appliquée (comme dans le logiciel d’origine) : utiliser l’indice de gel personnel.</li>
<li>Connexion Internet nécessaire au premier chargement du moteur de calcul (Pyodide).</li>
<li>Les tableaux de l’aide d’origine qui étaient des images (portance, déflexion, gélivité des sols) ne sont pas repris.</li>
<li>Résultats à vérifier par le projeteur ; outil fourni sans garantie (licence GPL v3).</li>
</ul>
""",
    },
]


def documentation(identifiant: Optional[str] = None):
    """Liste de la documentation, ou une entrée par son identifiant."""
    if identifiant is None:
        return DOCUMENTATION
    for d in DOCUMENTATION:
        if d["id"] == identifiant:
            return d
    raise KeyError(identifiant)


def html_vers_texte(html: str) -> str:
    """Texte lisible en console à partir d’un fragment HTML de la documentation."""
    t = re.sub(r"<li>", "\n  • ", html)
    t = re.sub(r"</?(p|ul|ol|br)[^>]*>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n\n", t)
    return t.strip()
