"""Signature et palette du fork (page autonome, note de calcul, README).

Mêmes couleurs que l’outil ``dimensionnement-burmister/web`` ; aucun nom de collectivité
(règle de confidentialité du fork, décision de YannFR81).
"""

from html import escape

PALETTE = {
    "orange": "#DD590A",
    "bleu": "#5E99C5",
    "vert": "#179D87",
    "lie_de_vin": "#7F0541",
}

DEVISE = "Pour une fonction publique augmentée, pas remplacée."

SIGNATURE_TEXTE = (
    "Développé par YannFR81, agent territorial au sein d’un conseil départemental, avec Claude, IA d’Anthropic, "
    "et Gemini Antigravity Hydrogen, IA de Google : l’agent a posé le besoin, piloté et tranché ; "
    "Claude et Gemini ont codé en binôme, chacun relisant le travail de l’autre. "
    "Portage du logiciel Struct-Urb (CERTU / Cerema), publié dans un fork du dépôt du Cerema "
    "(github.com/YannFR81/territoires-ville.StructUrb). Licence GNU GPL v3, comme l’original ; "
    "outil fourni sans garantie, résultats à vérifier par le projeteur."
)


def signature_html(classe: str = "signature") -> str:
    """Bloc HTML de la signature (devise en orange, puis le texte)."""
    return (
        f'<p class="{classe}"><b style="color:{PALETTE["orange"]}">{escape(DEVISE)}</b> '
        f"{escape(SIGNATURE_TEXTE)}</p>"
    )
