"""Mise en page commune du glossaire des applications d'apprentissage.

Plomberie : chaque application ne fournit que ses termes. Ce module fixe la
structure, la même partout : trois familles, chacune sous un titre qui dit
sa nature, avec une phrase d'en-tête pour les deux dernières.

1. **Le sujet** : les termes de la bibliothèque enseignée, en une ou
   plusieurs sections.
2. **Les outils de ce guide** : les classes écrites pour ce guide
   seulement. La phrase d'en-tête dit qu'elles ne font partie ni de la
   bibliothèque du sujet ni de Qt (`toolsIntroduction`).
3. **Le guide et Qt** : l'organisation du guide, la même pour toutes les
   applications (`GuideRows`), puis les notions de Qt que l'application
   emploie sans les enseigner. Celles-ci viennent d'une base commune
   (`QtRows`), une seule définition par terme ; chaque application choisit
   celles qu'elle emploie, et peut en ajouter qui lui sont propres.
"""

from __future__ import annotations

from collections.abc import Sequence

from .annex_style import AnnexTableClass

# A glossary row: the term, the class or notation (HTML, may be empty), the definition (HTML).
GlossaryRow = tuple[str, str, str]

GuideIntroduction = (
    "L'organisation du guide, et les notions de Qt qu'il emploie sans les enseigner (voir aussi "
    "la page « Prérequis »)."
)

# The organisation of the guide: the same rows, in the same order, for every application.
GuideRows: tuple[GlossaryRow, ...] = (
    ("chapitre, notion, étape", "", "un chapitre regroupe des notions (numérotées 1.1, 1.2…) ; "
     "une notion se suit étape par étape"),
    ("page de la notion", "", "ce qu'occupe une notion : à gauche la zone de contenu, ce que "
     "produit le code ; à droite le panneau des étapes, avec l'explication et le code"),
    ("vue d'ensemble", "", "la première étape d'une notion : son objectif, ses concepts clés, ses "
     "classes et méthodes clés"),
    ("récapitulatif", "", "la deuxième étape d'une notion : elle reprend les gestes déjà vus dont "
     "la notion a besoin, avant d'en ajouter un"),
    ("« À vous : … »", "", "une étape où l'on manipule soi-même des contrôles, ou le contenu à la "
     "souris"),
    ("<i>Essai</i>", "", "un court paragraphe qui propose un geste facultatif, dans une étape qui "
     "n'est pas « À vous »"),
    ("<i>Pour l'exemple</i>", "", "un court paragraphe qui décrit ce qui sert seulement à "
     "construire l'exemple, et non le sujet"),
    ("code affiché", "", "le code réel qui s'exécute à l'étape"),
    ("synthèse du chapitre", "", "la dernière page d'un chapitre : ses notions résumées, et vues "
     "d'ensemble"),
)

# The Qt terms an application may use without teaching them: one definition per term.
QtRows: dict[str, GlossaryRow] = {row[0]: row for row in (
    ("widget, fenêtre", "<code>QWidget</code>", "un élément d'interface ; une fenêtre est un widget "
     "de haut niveau, sans parent, affiché dans son propre cadre"),
    ("parent, enfant", "", "un enfant s'affiche dans son parent, et disparaît avec lui"),
    ("signal, slot", "<code>connect()</code>", "un signal est émis ; un slot est connecté au signal "
     "et appelé à chaque émission, avec les valeurs que le signal transmet"),
    ("accesseur, mutateur", "<code>value()</code>, <code>setValue()</code>", "une méthode qui lit "
     "une valeur ; une méthode qui la change"),
    ("contrôle", "", "un widget que l'utilisateur manipule"),
    ("sélecteur numérique", "<code>QSlider</code>", "une valeur entière, réglée en faisant glisser "
     "une poignée"),
    ("boîte numérique", "<code>QSpinBox</code>", "une valeur tapée, ou réglée par deux flèches"),
    ("case à cocher", "<code>QCheckBox</code>", "un choix oui ou non"),
    ("liste déroulante", "<code>QComboBox</code>", "un choix parmi plusieurs"),
    ("bouton", "<code>QPushButton</code>", "un clic déclenche une action"),
    ("minuteur", "<code>QTimer</code>", "émet un signal à intervalle régulier"),
    ("curseur de texte", "", "la position de saisie dans un texte"),
)}


def notPartOf(library: str) -> str:
    """« ne font pas partie de Qt », ou « ne font partie ni de PyQtGraph ni de Qt » pour une autre bibliothèque."""
    return "ne font pas partie de Qt" if library == "Qt" else f"ne font partie ni de {library} ni de Qt"


def toolsIntroduction(library: str = "Qt") -> str:
    """La phrase d'en-tête des outils du guide, selon la bibliothèque du sujet (« Qt », « PyQtGraph »)."""
    documentation = ("Vous ne les trouverez pas dans la documentation de Qt." if library == "Qt" else
                     f"Vous ne les trouverez ni dans la documentation de {library}, ni dans celle de Qt.")
    return (
        f"Ces classes {notPartOf(library)} : elles ont été écrites pour ce guide seulement, pour "
        f"montrer ce que produit votre code. {documentation} Hors de ce guide, votre code fonctionne "
        "sans elles : seule la ligne qui affiche le résultat change."
    )


def glossaryHtml(subject: str, subjectSections: Sequence[tuple[str, Sequence[GlossaryRow]]],
                 toolRows: Sequence[GlossaryRow], qtTerms: Sequence[str],
                 extraQtRows: Sequence[GlossaryRow] = (), *, library: str = "Qt") -> str:
    """Le contenu de la page « Glossaire », en HTML simple.

    Args:
        subject: Le sujet de l'application, en minuscules
            (« le dessin avec QPainter ») : il complète le titre
            « Le sujet : … ».
        subjectSections: Les sections du sujet, dans l'ordre : un
            sous-titre (vide s'il n'y a qu'une section) et ses rangées.
        toolRows: Les outils de ce guide. Vide : la famille est omise.
        qtTerms: Les termes de `QtRows` que l'application emploie, dans
            l'ordre voulu.
        extraQtRows: Les termes de Qt propres à l'application, après ceux
            de la base commune.
        library: La bibliothèque du sujet (« Qt », « PyQtGraph ») : elle
            complète la phrase d'en-tête des outils.

    Raises:
        KeyError: Un terme n'est pas dans `QtRows`.
    """
    parts = ["<p>Les mots employés dans ce guide, avec la classe ou l'écriture qui leur "
             "correspond, en trois familles.</p>",
             f"<h3>Le sujet : {subject}</h3>"]
    for subtitle, rows in subjectSections:
        if subtitle:
            parts.append(f"<h4>{subtitle}</h4>")
        parts.append(_table(rows))
    if toolRows:
        parts += ["<h3>Les outils de ce guide</h3>", f"<p>{toolsIntroduction(library)}</p>", _table(toolRows)]
    guideRows = [*GuideRows, *(QtRows[term] for term in qtTerms), *extraQtRows]
    parts += ["<h3>Le guide et Qt</h3>", f"<p>{GuideIntroduction}</p>", _table(guideRows)]
    return "".join(parts)


# ====== Private ======

def _table(rows: Sequence[GlossaryRow]) -> str:
    """Un tableau du glossaire : terme, classe ou écriture, définition, sous un en-tête.

    Même présentation que la grille des prérequis (`annex_style`).
    """
    # Fixed proportions: the columns line up from one table to the next.
    header = ("<tr><th width='22%'>Terme</th><th width='24%'>Classe ou écriture</th>"
              "<th width='54%'>Définition</th></tr>")
    cells = "".join(f"<tr><td><b>{term}</b></td><td>{code}</td><td>{meaning}</td></tr>"
                    for term, code, meaning in rows)
    return f"<table class='{AnnexTableClass}' width='100%' cellspacing='0'>{header}{cells}</table>"
