"""Présentation commune des tableaux des pages annexes (« Prérequis », « Glossaire »).

Plomberie : les tableaux ne portent que des classes (`AnnexTableClass`,
`SectionRowClass`) ; la feuille de style qui les met en forme est tirée de
la palette de la fenêtre. Elle suit donc le thème du système, clair ou
sombre, sans couleur propre : un rehaussement modeste, par des nuances du
texte sur le fond.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette

# The class of an annex table, and of a section row inside it.
AnnexTableClass = "annex"
SectionRowClass = "section"


def annexStyleSheet(palette: QPalette) -> str:
    """La feuille de style des tableaux annexes, en bloc `<style>`, pour cette palette.

    L'en-tête est en gras, souligné d'un trait marqué ; une rangée de
    section a un fond à peine teinté ; chaque rangée est séparée de la
    suivante par un trait léger. Un espace sépare le tableau du texte qui
    le précède.
    """
    text = palette.color(QPalette.ColorRole.WindowText)
    background = palette.color(QPalette.ColorRole.Window)
    strongLine = _blend(text, background, 0.45).name()
    lightLine = _blend(text, background, 0.15).name()
    sectionFill = _blend(text, background, 0.07).name()
    return (
        "<style>"
        f"table.{AnnexTableClass} {{ margin-top: 10px; margin-bottom: 6px; }}"
        f"table.{AnnexTableClass} th {{ text-align: left; font-weight: bold; padding: 5px; "
        f"border-bottom: 2px solid {strongLine}; }}"
        f"table.{AnnexTableClass} td {{ padding: 5px; vertical-align: top; "
        f"border-bottom: 1px solid {lightLine}; }}"
        f"tr.{SectionRowClass} td {{ background-color: {sectionFill}; font-weight: bold; }}"
        "</style>"
    )


# ====== Private ======

def _blend(foreground: QColor, background: QColor, fraction: float) -> QColor:
    """La couleur `foreground` posée sur `background` avec l'opacité `fraction`, de 0 à 1."""
    return QColor(round(background.red() + (foreground.red() - background.red()) * fraction),
                  round(background.green() + (foreground.green() - background.green()) * fraction),
                  round(background.blue() + (foreground.blue() - background.blue()) * fraction))
