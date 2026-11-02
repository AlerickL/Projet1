"""Notion 5.2 : l'atelier de dessin.

Contexte : l'apprenant écrit lui-même ses programmes de dessin. À gauche,
l'atelier (`QDrawingWorkshop`, `q_drawing_workshop.py`) : un éditeur, et le
canevas qui affiche le dessin à mesure qu'on écrit. À droite, un mode
d'emploi.

Page d'atelier (skill `interactive-walkthrough-app`, §5) : une seule étape,
sans code affiché. Le code qui s'exécute est celui que l'apprenant lit et
écrit dans l'éditeur ; le code de l'atelier lui-même est de l'outillage,
jamais montré. Le programme de l'apprenant reste dans l'éditeur d'une
visite à l'autre, tant que l'application reste ouverte.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from ..common.doc_urls import qtDocUrl
from ..common.q_step_walkthrough import QStepWalkthrough, createSplitterLayout
from .q_drawing_workshop import QDrawingWorkshop


class QTopicWorkshopTab(QWidget):
    """Onglet de la notion 5.2 : l'atelier à gauche, son mode d'emploi à droite.

    Attributs de classe:
        TabTitle: Titre compact affiché dans l'arbre de navigation.
        TabToolTip: Texte descriptif affiché au survol.
        RecommendedPanelWidth: Largeur initiale, en pixels, du panneau
            d'étapes (voir `createSplitterLayout`).
        Objective, KeyConcepts, KeyApis: Vides : une page d'atelier n'a pas
            de vue d'ensemble, son unique étape la remplace.

    Attributs d'instance:
        workshop: L'atelier (plomberie décrite en mots).
    """

    TabTitle = "L'atelier de dessin"
    TabToolTip = "Écrire son propre programme de dessin, et le voir apparaître sur le canevas"
    RecommendedPanelWidth = 600
    Objective = ""
    KeyConcepts: list[str] = []
    KeyApis: list[str] = []

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.workshop = QDrawingWorkshop()
        self.walkthrough = QStepWalkthrough(self._buildSteps(), self._resetState)
        createSplitterLayout(self, self.workshop, self.walkthrough, self.RecommendedPanelWidth)

    def _resetState(self) -> None:
        """Ne remet rien à zéro : l'éditeur garde le programme de l'apprenant d'une visite à l'autre."""

    def _openWorkshop(self) -> None:
        """L'unique étape : l'atelier exécute lui-même le programme de l'éditeur, rien d'autre à faire."""

    def _buildSteps(self) -> list[QStepWalkthrough.Step]:
        """Construit l'unique étape de la page : le mode d'emploi de l'atelier, sans code."""
        return [
            QStepWalkthrough.Step(
                title="Mode d'emploi de l'atelier",
                explanation=(
                    "Ici, vous écrivez vos propres programmes de dessin. Votre code est dans "
                    "l'éditeur, à gauche. Le canevas affiche son dessin à mesure que vous écrivez. "
                    "Cette page n'a donc pas de code à lire. L'atelier est un outil de ce guide : "
                    "il ne fait pas partie de Qt. Ce que vous y écrivez fonctionne aussi dans vos "
                    "propres programmes."

                    "<br><br><b>Le principe.</b> À chaque exécution, l'atelier crée une image "
                    "blanche de 480 × 360 pixels, avec un peintre déjà actif sur elle (notion 1.1). "
                    "Votre programme reçoit ce peintre sous le nom <code>painter</code>. Il ne crée "
                    "ni l'image ni le peintre : il dessine. Le repère est celui du guide : l'origine "
                    "en haut à gauche, y vers le bas, le centre en (240, 180). Une demi-seconde "
                    "après votre dernière frappe, l'atelier relance le programme sur une image "
                    "blanche neuve."
                    "<br><br><i>Essai</i> : dans l'éditeur, remplacez les deux 80 par 120. Le "
                    "cercle grandit une demi-seconde plus tard."
                    "<br><br>Un réglage du peintre agit sur les dessins qui le suivent, jamais sur "
                    "ceux d'avant. Au départ, le stylo est noir, d'un pixel, et il n'y a aucun "
                    "pinceau : les formes ne sont pas remplies. Pour remplir le cercle, placez "
                    "<code>painter.setBrush(QColor(\"gold\"))</code> au-dessus de la ligne "
                    "<code>drawEllipse()</code> (notion 2.2)."
                    "<br><br>Sans import, votre programme dispose de <code>math</code>, de "
                    "<code>random</code>, de <code>Qt</code>, et de ces classes de Qt : "
                    "<code>QPainter</code>, <code>QPen</code>, <code>QBrush</code>, "
                    "<code>QColor</code>, <code>QFont</code>, <code>QFontMetrics</code>, "
                    "<code>QFontMetricsF</code>, <code>QPoint</code>, <code>QPointF</code>, "
                    "<code>QLine</code>, <code>QLineF</code>, <code>QRect</code>, "
                    "<code>QRectF</code>, <code>QSize</code>, <code>QSizeF</code>, "
                    "<code>QPolygon</code>, <code>QPolygonF</code>, <code>QPainterPath</code>, "
                    "<code>QGradient</code>, <code>QLinearGradient</code>, "
                    "<code>QRadialGradient</code>, <code>QConicalGradient</code>, "
                    "<code>QImage</code> et <code>QTransform</code>. Pour une autre classe, "
                    "importez-la de <code>PySide6.QtGui</code> ou de <code>PySide6.QtCore</code>. "
                    "L'atelier n'accepte aucun autre import : il arrête le programme avant de "
                    "l'exécuter, et surligne la ligne de l'import."
                    "<br><br>Sous la lecture, la case <b>Grille</b> affiche la grille du canevas "
                    "(notion 1.1). Elle aide à choisir des coordonnées. Le petit carré à côté "
                    "choisit sa couleur : une grille claire se lit mieux sur un fond sombre."

                    "<br><br><b>Le bilan.</b> Sous le canevas, deux lignes rendent compte de "
                    "chaque exécution."
                    "<ul>"
                    "<li>Le temps de calcul, comparé à la seconde permise. Sa barre passe du vert "
                    "à l'orange, puis au rouge près de la limite. Au-delà d'une seconde, "
                    "l'atelier interrompt le programme. Une boucle sans fin ne gèle donc pas "
                    "l'application. La lecture le signale, et la ligne en cours est surlignée. "
                    "Ce qui était déjà dessiné reste visible.</li>"
                    "<li>La lecture : ce que le programme affiche avec <code>print()</code>, puis "
                    "le verdict. Sans erreur, le verdict compte les appels de dessin : les appels "
                    "aux méthodes du peintre qui dessinent, comme <code>drawEllipse()</code> ou "
                    "<code>fillRect()</code>. Les réglages, comme <code>setPen()</code>, ne "
                    "comptent pas.</li>"
                    "</ul>"
                    "Le compte confirme qu'une boucle dessine autant de fois que prévu. S'il est "
                    "positif et que rien n'apparaît, le dessin est peut-être hors de l'image, ou "
                    "de la couleur du fond."
                    "<br><br><i>Essai</i> : remplacez la ligne <code>drawEllipse()</code> par "
                    "trois lignes : <code>radius = 80</code>, puis "
                    "<code>print(\"diamètre :\", 2 * radius)</code>, puis "
                    "<code>painter.drawEllipse(QPointF(240, 180), radius, radius)</code>. La "
                    "lecture écrit « diamètre : 160 » avant le verdict. <code>print()</code> "
                    "montre la valeur d'un calcul."

                    "<br><br><b>Les erreurs.</b> Le programme s'arrête à la première erreur. Sa "
                    "ligne est surlignée en rouge. La lecture donne le message de Python, en "
                    "anglais. Ce qui était déjà dessiné reste visible. Pendant la frappe, une "
                    "ligne encore incomplète provoque une erreur. L'erreur disparaît quand la "
                    "ligne est complète."
                    "<br><br><i>Essai</i> : sous la ligne <code>drawEllipse()</code>, ajoutez "
                    "<code>painter.drawCircle(240, 180, 50)</code>. La lecture signale une "
                    "<code>AttributeError</code> : le peintre n'a pas de méthode de ce nom. Le "
                    "premier cercle, dessiné avant l'erreur, reste visible. Remplacez ensuite la "
                    "ligne par <code>painter.drawEllipse(QPointF(240, 180), 50, 50)</code> : un "
                    "cercle est une ellipse aux deux rayons égaux (notion 1.2)."

                    "<br><br><b>Les boutons au-dessus de l'éditeur.</b>"
                    "<ul>"
                    "<li><b>Insérer un fragment</b> ouvre un menu, un sous-menu par notion. Un "
                    "fragment est un court extrait de code, tiré d'une notion, à adapter. Survolez "
                    "une entrée pour voir son code. Le fragment s'insère sous la ligne du curseur "
                    "de texte, à la même indentation. Si le curseur est dans une boucle, le "
                    "fragment y entre aussi.</li>"
                    "<li><b>Charger une œuvre</b> remplace tout le programme par une œuvre du "
                    "guide. Une œuvre est un programme complet, à lire et à modifier. La plupart "
                    "dessinent les images des pages d'introduction et de synthèse des "
                    "chapitres.</li>"
                    "<li><b>Vider</b> efface tout le programme.</li>"
                    "<li><b>Copier</b> place tout le programme dans le presse-papiers.</li>"
                    "</ul>"
                    "Votre programme reste dans l'éditeur quand vous quittez cette page, tant que "
                    "l'application reste ouverte. Charger une œuvre et Vider le remplacent sans "
                    "demander de confirmation. Ctrl+Z ne le rétablit pas. Copiez-le d'abord pour "
                    "le garder."

                    "<br><br><b>Quelques idées.</b> Décomposez le dessin en couches, du fond vers "
                    "l'avant, comme à la notion 5.1."
                    "<ul>"
                    "<li>Un visage ou un drapeau : les formes de base (notion 1.2), le stylo et le "
                    "pinceau (notions 2.1 et 2.2).</li>"
                    "<li>Une horloge à l'heure de votre choix : <code>translate()</code> et "
                    "<code>rotate()</code> (notion 3.2).</li>"
                    "<li>Une rosace de couleurs : une boucle, <code>rotate()</code>, et des "
                    "teintes HSV (notion 2.3).</li>"
                    "<li>Un ciel étoilé : des positions tirées au hasard. Avec un générateur à "
                    "graine fixe, <code>generator = random.Random(7)</code>, puis "
                    "<code>generator.uniform(0, 480)</code> pour chaque x et "
                    "<code>generator.uniform(0, 360)</code> pour chaque y, les étoiles "
                    "restent les mêmes à chaque exécution (notion 5.1). Avec "
                    "<code>random.uniform()</code> seul, elles changent à chaque frappe.</li>"
                    "</ul>"

                    "<b>Reprendre le code d'une notion.</b> Le plus simple : insérez le fragment "
                    "de la notion. Pour reprendre une méthode entière :"
                    "<ul>"
                    "<li>sélectionnez son code dans la zone de code de la notion, copiez-le "
                    "(Ctrl+C), puis collez-le dans l'éditeur (Ctrl+V) ;</li>"
                    "<li>retirez la ligne <code>def</code>, la docstring, et toutes les lignes qui "
                    "emploient <code>self</code>, la ligne <code>with</code> comprise : l'atelier "
                    "fournit déjà l'image et le peintre ;</li>"
                    "<li>sélectionnez tout (Ctrl+A), puis appuyez deux fois sur Maj+Tab. Chaque "
                    "appui retire quatre espaces au début de chaque ligne sélectionnée ;</li>"
                    "<li>sélectionnez les lignes de l'ancien bloc <code>with</code>, puis appuyez "
                    "une fois sur Maj+Tab ;</li>"
                    "<li>copiez au-dessus une fonction que la méthode appelle, comme "
                    "<code>drawArrow()</code> (notion 3.2) ;</li>"
                    "<li>un paramètre de la méthode devient une variable : donnez-lui une "
                    "valeur.</li>"
                    "</ul>"
                    "Par exemple, de <code>drawSun()</code> (notion 2.4), il reste les quatre "
                    "lignes du dégradé, puis les quatre lignes de l'ancien bloc <code>with</code>."
                ),
                run=self._openWorkshop,
                codeSource=(),
                references=[("QPainter", qtDocUrl("QtGui", "QPainter"))],
            ),
        ]
