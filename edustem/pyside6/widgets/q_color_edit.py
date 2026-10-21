"""Éditeur de couleur compact, haut comme un `QLineEdit` : `QColorEdit`.

Sur une seule rangée, le widget montre la couleur, puis une bande par canal de l'espace de
couleur choisi (RGB, HSV, HSL ou CMYK). Chaque bande montre les couleurs qu'on obtiendrait en
y glissant la poignée. Un plan à deux canaux peut s'y ajouter, qui s'ouvre en grand dans une
fenêtre flottante.

    edit = QColorEdit(QColor("tomato"))
    edit.setColorSpace(QColorEdit.ColorSpace.Hsv)
    edit.colorChanged.connect(print)

Voir `QColorEdit` pour la documentation complète.

Dépendance locale : la pipette, `QScreenColorPicker` (`q_screen_color_picker.py`), un outil
partagé avec `QColorBox`.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Iterable, Sequence
from enum import Enum
from itertools import combinations
from typing import Final, cast, override

from PySide6.QtCore import QEvent, QObject, QPoint, QPointF, QRect, QRectF, QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import (QBrush, QColor, QEnterEvent, QFocusEvent, QFont, QFontMetrics, QHelpEvent, QHideEvent, QImage, QKeyEvent, QKeySequence,
                           QLinearGradient, QMouseEvent, QPainter, QPainterPath, QPaintEvent, QPalette, QPen, QPolygonF, QResizeEvent,
                           QValidator, QWheelEvent, qGray)
from PySide6.QtWidgets import (QApplication, QColorDialog, QFrame, QLineEdit, QSizePolicy, QStyle, QStyleOptionButton,
                               QStyleOptionFocusRect, QStyleOptionFrame, QToolTip, QWidget)

from .q_screen_color_picker import EyedropperButton, QScreenColorPicker


class QColorEdit(QWidget):
    """Éditeur de couleur sur une rangée, de la hauteur d'un `QLineEdit`.

    Les parties
    -----------
    De gauche à droite, à l'horizontale :

    - **La pastille** montre la couleur, avec son alpha, sur un damier. Un clic ouvre un
      `QColorDialog` (`isDialogEnabled`). Sa longueur se règle (`setSwatchLength`).
    - **La pipette** : un coin replié au bout de la pastille, ou une section juste après elle
      (`eyedropperButton`). Voir « La pipette ».
    - **La poignée de la pastille**, étroite, à trois points : la glisser règle la longueur de
      la pastille ; un double-clic la rend automatique.
    - **La bascule de déploiement** montre ou cache tout ce qui suit (`isExpanded`). Replié,
      la pastille occupe toute la longueur.
    - **La bascule de l'alpha** ajoute ou retire la bande de l'alpha (`isAlphaVisible`).
    - **L'étiquette de l'espace** nomme l'espace de couleur. Un clic passe au suivant parmi
      les espaces offerts (`availableColorSpaces`). S'il n'en reste qu'un, elle ne fait que
      le nommer.
    - **La bascule de notation** choisit comment une valeur s'écrit (`valueNotation`) : en
      entiers, en réels ou en hexadécimal, chaque clic passant à la suivante.
    - **La zone de texte**, fermée par défaut (`textWidth`), puis **sa poignée**, juste à
      gauche des bandes. Voir « Saisie des valeurs ».
    - **Les bandes**, une par canal. Chaque bande est un dégradé opaque : la couleur qu'on
      obtiendrait à chaque position, les autres canaux restant où ils sont. La bande de
      l'alpha, la dernière, va de la couleur transparente à la couleur opaque, sur un damier.
    - **Le plan** (`isPlaneVisible`, vrai par défaut), un carré qui montre deux canaux à la fois, avec une
      croix sur la couleur. Un clic l'ouvre en grand dans une fenêtre flottante.
    - **La bascule du plan** montre ou cache ce carré.

    Chaque bascule, l'étiquette et les deux poignées se masquent par programme
    (`setExpandToggleVisible`, `setAlphaToggleVisible`, `setColorSpaceLabelVisible`,
    `setNotationToggleVisible`, `setPlaneToggleVisible`, `setSwatchHandleVisible`,
    `setTextHandleVisible`). L'état qu'elles règlent reste accessible par son mutateur.

    Le plan
    -------
    Un plan prend deux canaux de l'espace courant, jamais l'alpha : RG, RB ou GB en RGB,
    six plans en CMYK (`planes`, `plane`, `setPlane`). Le premier canal court de gauche à
    droite, le second de bas en haut. Chaque point montre la couleur qu'on y obtiendrait.

    La fenêtre flottante (`showPlanePopup`) reprend le plan en grand. On y glisse la croix,
    ce qui règle les deux canaux et déplace leurs poignées. Juste à droite, une bande
    verticale règle chaque canal restant (deux en CMYK). Leurs lettres s'écrivent à la
    suite, en haut à droite. Sous le plan, une bande horizontale règle l'alpha, si la barre
    affiche la sienne. Toutes ces bandes ont la taille de celles du widget et sont collées
    au plan et l'une à l'autre. Au-dessus du plan, un bouton le nomme : un clic passe au
    suivant, un clic droit au précédent.

    Dans cette fenêtre, les flèches déplacent la croix d'un pas dans le sens où elles
    pointent, et la molette règle la bande sous le pointeur. Avec Maj, comme dans les
    logiciels de dessin, ou avec Ctrl, le pas est décuplé. Le côté du plan se règle entre deux bornes
    (`setPlanePopupSize`). La fenêtre se ferme par un clic au-dehors ou par Échap.

    En bas, un bouton écrit la couleur dans l'espace et la notation courants, comme
    `RGB = (230, 120, 40)`, sur deux lignes si une seule ne suffit pas. Un clic la copie
    dans le presse-papiers. Un double-clic le
    change en champ de saisie, au patron de cette écriture : Entrée retient les valeurs
    tapées, ramenées dans leur étendue, Échap abandonne. Ctrl+C copie aussi, et Ctrl+V
    applique une couleur du presse-papiers : cette même écriture, des nombres seuls, ou un
    code `#RRGGBB`. Un nom d'espace en tête est respecté, sans changer l'espace affiché.

    Dans la barre, le carré du plan ne porte qu'une croix d'un pixel : il montre le plan,
    c'est la fenêtre flottante qui le règle.

    La pipette
    ----------
    La commande de la pipette prend l'une des formes de `EyedropperButton`
    (`eyedropperButton`, `Corner` par défaut), choisie à la construction ou par
    `setEyedropperButton` :

    - `Corner` : un coin replié, en bas de la pastille, à son bout, porte l'icône d'une
      pipette. Il ne prend aucune place en plus. Sa taille est fixe, tirée de la hauteur d'un
      `QLineEdit` : la bande de l'alpha ne la change pas.
    - `Section` : une section à part, juste après la pastille, comme les autres bascules ;
      elle reste là quand les bandes sont repliées.
    - `Hidden` : aucune commande.

    Un clic sur la commande lance la pipette : l'écran se fige, un réticule suit le
    pointeur, et un panneau grossit les pixels visés. Ce panneau montre aussi la couleur
    avant et après, un aperçu de l'éditeur dans son espace et sa notation, la couleur écrite
    comme dans la fenêtre du plan, le contraste avec la couleur courante et l'historique des
    prises. Un clic prend la couleur. On peut aussi appuyer sur la commande, glisser jusqu'à
    la couleur et relâcher. `pickScreenColor` lance la pipette par programme, quelle que soit
    la commande. Les gestes de la prise sont décrits par `QScreenColorPicker`, que
    `screenColorPicker` rend pour en régler le zoom, la moyenne ou la taille de la loupe.

    Pendant la prise, les poignées et la croix du plan disparaissent : les couleurs qu'elles
    cachent se prennent aussi. La couleur prise garde l'alpha de la couleur courante, et
    l'espace affiché ne change pas.

    Orientation et sens
    -------------------
    À la verticale (`setOrientation`), tout pivote : la pastille est en haut, les bandes
    sont côte à côte.

    Une valeur augmente vers la droite et vers le haut, comme dans `QSlider`.
    `setInvertedAppearance` inverse ce sens. À l'horizontale, une mise en page de droite à
    gauche (`setLayoutDirection`) retourne l'ordre des parties et le sens des bandes. Les
    axes du plan ne changent jamais.

    Les textes suivent `textDirection` : le long du widget (`Aligned`, par défaut, la seule
    lecture confortable dans les deux orientations), en travers (`Perpendicular`), ou toujours
    à l'horizontale (`Horizontal`).

    Taille
    ------
    Aucune dimension n'est fixée d'avance. L'épaisseur est celle d'un `QLineEdit` du style
    courant, pour la police du widget. Les bandes se partagent l'épaisseur à parts égales.

    - **Les textes** prennent la police du widget, en gras, un peu réduite. En travers, elle
      est réduite encore, jusqu'à ce que le plus long texte tienne dans l'épaisseur.
    - **L'étiquette de l'espace** porte deux lignes quand la bande de l'alpha est affichée :
      le nom de l'espace, à la même taille, un peu remonté, et « alpha » en petit dessous.
    - **La notation** se lit sur un pictogramme dessiné, de la hauteur d'une capitale : trois
      paliers pour les entiers, une pente continue pour les réels, de même largeur.
    - **Une bascule garde toujours sa taille**, réglée sur le plus long texte qu'elle puisse
      porter (« CMYK » et sa ligne « alpha »), quels que soient les espaces offerts.
    - **Une poignée garde toujours sa longueur** : deux fois l'épaisseur d'une bande dans le
      cas de référence (trois bandes, sans alpha, à l'épaisseur recommandée). Sa hauteur est
      celle de sa bande.
    - **La longueur minimum** compte la pastille à sa longueur automatique, les deux poignées
      étroites, les bascules offertes, le plan, et trois longueurs de poignée pour les bandes.
      Ce que les poignées donnent à la pastille ou à la zone de texte se prend sur les bandes :
      le widget garde sa taille.

    Avec la bande de l'alpha, l'épaisseur grandit d'un tiers, quel que soit l'espace de
    couleur : changer d'espace ne déplace donc jamais les widgets voisins.

    Comme un `QLineEdit`, le widget ne grandit pas en épaisseur de lui-même (politique
    `Fixed`). Si on lui donne plus de place, les bandes, la pastille et le plan la prennent.

    Toute la géométrie est calée sur les pixels de l'écran : à une échelle d'affichage de
    150 %, les bandes gardent la même épaisseur, à un pixel d'écran près.

    Le style courant dessine autour du widget un cadre discret, celui d'un panneau
    (`hasFrame`). Le focus se lit de deux façons. Le rectangle de focus du style
    (`PE_FrameFocusRect`), juste à l'intérieur du cadre, dit que le widget a le focus, comme
    pour `QColorBox` et tout autre widget : son dessin suit le style et le système (sous
    Windows, un anneau neutre, qui peut n'apparaître qu'après une navigation au clavier). La
    poignée de la bande courante, remplie de la couleur d'accent du système
    (`QPalette.Highlight`), comme celle d'un curseur de Windows 11, dit quel canal les flèches
    règlent.

    Désactivé, le widget s'estompe, sauf la pastille, comme `QColorBox` : la couleur est
    l'information affichée, elle reste telle quelle. Seul le survol du widget désactivé la
    désature et l'assombrit, pour rappeler qu'elle ne peut pas être changée depuis là.

    Couleur et canaux
    -----------------
    Le widget retient la valeur de chaque canal de l'espace courant (`channelValues`). La
    teinte survit donc à une saturation nulle, et la saturation à une couleur noire.
    `setColor` accepte une couleur de n'importe quel espace et ne change pas l'espace
    affiché. `color` rend la couleur reçue, ou celle que les canaux composent après un
    réglage.

    L'alpha ne se règle que par le dialogue et par la bande de l'alpha. Quand `useAlpha`
    est faux, la couleur est montrée opaque et ni le dialogue ni les bandes n'offrent
    l'alpha ; l'alpha de la couleur retenue n'est pas modifié pour autant.

    Souris, clavier, molette
    ------------------------
    - On glisse une poignée d'où on l'a prise. Comme dans `QSlider`, un clic ailleurs dans la
      bande avance la poignée d'une page (dix pas) vers le pointeur, puis encore tant que le
      bouton reste enfoncé, jusqu'au pointeur. Maj+clic, ou un clic du milieu, y amène la
      poignée d'un coup, qui se glisse ensuite.
    - Le widget n'a qu'un arrêt de tabulation. Un canal est « courant » (`currentChannel`).
      Les flèches en travers des bandes choisissent le canal ; les flèches le long des bandes
      le règlent d'un pas, Page précédente et Page suivante de dix, Début et Fin vont aux
      bouts. Espace ou Entrée ouvre le dialogue.
    - La molette règle la bande sous le pointeur.
    - Raccourcis, quand le widget a le focus : F2 ouvre la zone de texte, I lance la
      pipette, P ouvre la fenêtre du plan. Ctrl+C copie la couleur écrite
      (`RGB = (230, 120, 40)`), Ctrl+V applique une couleur du presse-papiers, comme dans la
      fenêtre du plan.

    Un pas vaut une unité de la notation entière (1/255, ou un degré de teinte), aussi en
    hexadécimal, ou un centième en notation réelle.

    Saisie des valeurs
    ------------------
    Juste à gauche des bandes, une poignée étroite ouvre la zone de texte, qui se déploie à sa
    gauche : la poignée suit le pointeur, comme celle d'un séparateur. Les bandes restent là,
    plus courtes, et suivent la frappe ; le widget garde sa taille. Un clic sur la poignée
    ouvre ou ferme la zone (`isTextVisible`, `setTextVisible`), qui garde sa largeur
    (`textWidth`, sa largeur naturelle par défaut, `naturalTextWidth`). La glisser en règle
    la largeur, jamais au-delà de sa largeur naturelle (plus loin, il ne resterait que du
    vide) ni de la longueur minimum des bandes ; une zone glissée sous la moitié de sa
    largeur naturelle se ferme, et sa prochaine ouverture reprend la largeur naturelle. F2 ou
    `editAsText` l'ouvre au besoin et y donne le focus, la première valeur sélectionnée. La
    zone ne prend jamais la place minimum des bandes.

    À la verticale, un champ ne tient pas en travers du widget : un clic sur la poignée, F2
    ou `editAsText` ouvre les mêmes champs dans un volet flottant, à côté du widget, à la
    hauteur de la poignée. Entrée y retient la couleur et le ferme, Échap la rétablit et le
    ferme, un clic au-dehors la retient et le ferme. Repliées, les bandes n'ont plus de
    place : la saisie se fait alors dans la fenêtre du plan.

    Le champ des valeurs écrit `(230, 120, 40)`, dans l'espace et la notation courants. Comme
    dans `QRangeSpinBox`, les parenthèses et les virgules sont protégées, les nombres ont une
    largeur libre, et la frappe y insère normalement. Taper `,` sélectionne la valeur
    suivante ; les flèches haut et bas règlent la valeur sous le curseur d'un pas, de dix
    avec Maj. Remplacer tout le texte ouvre la saisie libre, lue à Entrée comme un collage
    (`#E67828`, `RGB = (230, 120, 40)`, des nombres seuls) ; un texte qui n'écrit aucune
    couleur est défait.

    À droite, s'il apporte quelque chose et s'il tient, le champ du code : `#RRGGBB`, ou
    `#AARRGGBB` avec la bande de l'alpha. C'est l'ordre de Qt (`QColor.name`), et non celui
    du CSS, `#RRGGBBAA`. Il est omis en RGB hexadécimal, où il redirait les canaux. Tab passe des
    valeurs au code, Maj+Tab revient.

    Chaque frappe qui complète un champ montre la couleur dans la pastille et les bandes,
    sans la retenir ; l'autre champ suit. Entrée ou la perte du focus la retiennent ; Échap
    rend la couleur qu'il y avait quand le champ a pris le focus. Ctrl+C et Ctrl+V s'y font
    comme ailleurs. Tout changement venu d'ailleurs (bandes, plan, programme) réécrit les
    champs, sauf celui où l'on tape.

    Chaque partie a son infobulle : son état en valeurs, l'effet d'un clic, les raccourcis.
    Celle d'une bande paraît tout de suite et suit le glissement.

    Suivi
    -----
    Avec suivi (`hasTracking`, vrai par défaut), la couleur change pendant le glissement.
    Sans suivi, les bandes et la pastille montrent le réglage en cours, mais `color` et
    `colorChanged` ne changent qu'au relâchement.

    Propriétés:
        color (QColor): La couleur. Accesseur `color()`, mutateur `setColor()`, signal
            `colorChanged`.
        colorSpace (ColorSpace): L'espace affiché. Accesseur `colorSpace()`, mutateur
            `setColorSpace()`, signal `colorSpaceChanged`.
        expanded (bool): Les bandes sont déployées. Accesseur `isExpanded()`, mutateur
            `setExpanded()`, signal `expandedChanged`.
        alphaVisible (bool): La bande de l'alpha est affichée. Accesseur
            `isAlphaVisible()`, mutateur `setAlphaVisible()`, signal `alphaVisibleChanged`.
        planeVisible (bool): Le plan est affiché. Accesseur `isPlaneVisible()`, mutateur
            `setPlaneVisible()`, signal `planeVisibleChanged`.
        plane (tuple[int, int]): Les deux canaux du plan. Accesseur `plane()`, mutateur
            `setPlane()`, signal `planeChanged`.
        valueNotation (ValueNotation): L'écriture des valeurs. Accesseur
            `valueNotation()`, mutateur `setValueNotation()`, signal
            `valueNotationChanged`.
        orientation (Qt.Orientation): Accesseur `orientation()`, mutateur
            `setOrientation()`.
        textDirection (TextDirection): Accesseur `textDirection()`, mutateur
            `setTextDirection()`.
        invertedAppearance (bool): Accesseur `invertedAppearance()`, mutateur
            `setInvertedAppearance()`.
        swatchLength (int): Accesseur `swatchLength()`, mutateur `setSwatchLength()`.
        textVisible (bool): La zone de texte est ouverte. Accesseur `isTextVisible()`,
            mutateur `setTextVisible()`, signal `textVisibleChanged`.
        textWidth (int): La largeur de la zone de texte ouverte ; sa largeur naturelle si on y
            met 0. Accesseur `textWidth()`, mutateur `setTextWidth()`, signal
            `textWidthChanged`.
        swatchHandleVisible (bool): Accesseur `isSwatchHandleVisible()`, mutateur
            `setSwatchHandleVisible()`.
        textHandleVisible (bool): Accesseur `isTextHandleVisible()`, mutateur
            `setTextHandleVisible()`.
        planePopupSize (int): Accesseur `planePopupSize()`, mutateur
            `setPlanePopupSize()`.
        frame (bool): Accesseur `hasFrame()`, mutateur `setFrame()`.
        useAlpha (bool): Accesseur `useAlpha()`, mutateur `setUseAlpha()`.
        tracking (bool): Accesseur `hasTracking()`, mutateur `setTracking()`.
        dialogEnabled (bool): Accesseur `isDialogEnabled()`, mutateur
            `setDialogEnabled()`.
        eyedropperButton (EyedropperButton): Accesseur `eyedropperButton()`, mutateur
            `setEyedropperButton()`.
        currentChannel (int): Accesseur `currentChannel()`, mutateur
            `setCurrentChannel()`.

    Signaux:
        colorChanged: Signal(QColor). Émis quand la couleur change.
        colorSpaceChanged: Signal(ColorSpace). Émis quand l'espace affiché change.
        expandedChanged: Signal(bool). Émis quand les bandes sont déployées ou repliées.
        alphaVisibleChanged: Signal(bool). Émis quand la bande de l'alpha paraît ou
            disparaît.
        planeVisibleChanged: Signal(bool). Émis quand le plan paraît ou disparaît.
        planeChanged: Signal(int, int). Émis quand le plan change de canaux.
        valueNotationChanged: Signal(ValueNotation). Émis quand la notation change.
        textVisibleChanged: Signal(bool). Émis quand la zone de texte s'ouvre ou se ferme.
        textWidthChanged: Signal(int). Émis quand la largeur de la zone de texte change.

    Slots:
        setColor(QColor): Fixe la couleur.
        setChannelValue(int, float): Fixe un canal de l'espace courant.
        setColorSpace(ColorSpace): Choisit l'espace affiché.
        setAvailableColorSpaces(object): Choisit les espaces offerts.
        setExpanded(bool): Déploie ou replie les bandes.
        setAlphaVisible(bool): Montre ou cache la bande de l'alpha.
        setPlaneVisible(bool): Montre ou cache le plan.
        setPlane(int, int): Choisit les deux canaux du plan.
        showPlanePopup(): Ouvre le plan dans sa fenêtre flottante.
        setPlanePopupSize(int): Fixe le côté du plan de la fenêtre flottante.
        setValueNotation(ValueNotation): Choisit l'écriture des valeurs.
        setOrientation(Qt.Orientation): Fixe l'orientation.
        setTextDirection(TextDirection): Choisit le sens des textes.
        setInvertedAppearance(bool): Inverse le sens des bandes.
        setSwatchLength(int): Fixe la longueur de la pastille.
        setFrame(bool): Montre ou cache le cadre.
        setUseAlpha(bool): Active ou désactive l'alpha.
        setTracking(bool): Active ou désactive le suivi.
        setDialogEnabled(bool): Permet ou interdit le dialogue.
        setCurrentChannel(int): Choisit le canal que le clavier règle.
        setExpandToggleVisible(bool): Montre ou cache la bascule de déploiement.
        setAlphaToggleVisible(bool): Montre ou cache la bascule de l'alpha.
        setColorSpaceLabelVisible(bool): Montre ou cache l'étiquette de l'espace.
        setNotationToggleVisible(bool): Montre ou cache la bascule de notation.
        setPlaneToggleVisible(bool): Montre ou cache la bascule du plan.
        setEyedropperButton(EyedropperButton): Choisit la commande de la pipette.
        pickScreenColor(): Lance la pipette.
        setTextVisible(bool): Ouvre ou ferme la zone de texte.
        setTextWidth(int): Fixe la largeur de la zone de texte ouverte.
        setSwatchHandleVisible(bool): Montre ou cache la poignée de la pastille.
        setTextHandleVisible(bool): Montre ou cache la poignée du texte.
        editAsText(): Donne le focus aux valeurs écrites, en ouvrant la zone au besoin.
    """

    class ColorSpace(Enum):
        """Un espace de couleur que le widget sait afficher.

        Attributs:
            Rgb: Rouge, vert, bleu.
            Hsv: Teinte, saturation, valeur.
            Hsl: Teinte, saturation, luminosité.
            Cmyk: Cyan, magenta, jaune, noir.
        """

        Rgb = 0
        Hsv = 1
        Hsl = 2
        Cmyk = 3

    class ValueNotation(Enum):
        """La façon d'écrire la valeur d'un canal, d'après les deux familles d'accesseurs de `QColor`.

        Attributs:
            Integer: De 0 à 255, sauf la teinte, de 0 à 359 (comme `QColor.red()`).
            Real: De 0.0 à 1.0 (comme `QColor.redF()`).
            Hexadecimal: Les entiers de `Integer`, écrits en base 16 : de 00 à FF, sauf la
                teinte, de 000 à 167.
        """

        Integer = 0
        Real = 1
        Hexadecimal = 2

    class TextDirection(Enum):
        """Le sens des textes des bascules.

        Attributs:
            Perpendicular: En travers du widget ; la police est réduite pour y tenir.
            Aligned: Le long du widget, à la taille de la police du widget.
            Horizontal: Toujours à l'horizontale : le long d'un widget horizontal, en travers d'un widget vertical.
        """

        Perpendicular = 0
        Aligned = 1
        Horizontal = 2

    EyedropperButton = EyedropperButton

    colorChanged = Signal(QColor)
    colorSpaceChanged = Signal(ColorSpace)
    expandedChanged = Signal(bool)
    alphaVisibleChanged = Signal(bool)
    planeVisibleChanged = Signal(bool)
    planeChanged = Signal(int, int)
    valueNotationChanged = Signal(ValueNotation)
    textVisibleChanged = Signal(bool)
    textWidthChanged = Signal(int)

    def __init__(self, color: QColor | None = None, orientation: Qt.Orientation = Qt.Orientation.Horizontal,
                 parent: QWidget | None = None, *,
                 eyedropperButton: EyedropperButton = EyedropperButton.Corner) -> None:
        """Construit l'éditeur, déployé, en RGB.

        Args:
            color: La couleur initiale, ou None pour le noir opaque.
            orientation: L'orientation du widget.
            parent: Widget parent, ou None.
            eyedropperButton: La commande de la pipette.
        """
        super().__init__(parent)
        Part = QColorEdit._Part
        self.__color: QColor = QColor(0, 0, 0)
        self.__colorSpace: QColorEdit.ColorSpace = QColorEdit.ColorSpace.Rgb
        self.__components: list[float] = [0.0, 0.0, 0.0]     # the channels of the current space, each in [0, 1]
        self.__alpha: float = 1.0
        self.__available: frozenset[QColorEdit.ColorSpace] = frozenset(QColorEdit.ColorSpace)
        self.__orientation: Qt.Orientation = orientation
        self.__textDirection: QColorEdit.TextDirection = QColorEdit.TextDirection.Aligned
        self.__invertedAppearance: bool = False
        self.__expanded: bool = True
        self.__alphaVisible: bool = False
        self.__planeVisible: bool = True
        self.__planeRank: int = 0                    # which pair of channels, among those of the current space
        self.__planePopupSize: int = 0               # 0: the default
        self.__swatchLength: int = 0                 # 0: automatic
        self.__valueNotation: QColorEdit.ValueNotation = QColorEdit.ValueNotation.Integer
        self.__useAlpha: bool = True
        self.__tracking: bool = True
        self.__dialogEnabled: bool = True
        self.__frame: bool = True
        self.__expandToggleVisible: bool = True
        self.__alphaToggleVisible: bool = True
        self.__colorSpaceLabelVisible: bool = True
        self.__notationToggleVisible: bool = False
        self.__planeToggleVisible: bool = True
        self.__currentChannel: int = 0
        self.__pressedPart: QColorEdit._Part = Part.NoPart
        self.__hoverPart: QColorEdit._Part = Part.NoPart
        self.__hoverChannel: int = -1
        self.__draggedChannel: int = -1
        self.__wheelRemainder: int = 0
        self.__planeCache: tuple[tuple[object, ...], QImage] | None = None
        self.__popup: QColorEdit._PlanePopup | None = None
        self.__eyedropperButton: EyedropperButton = eyedropperButton
        self.__picker: QColorEdit._ScreenPicker | None = None
        self.__picking: bool = False
        self.__eyedropperDragged: bool = False
        self.__pressPosition: QPoint = QPoint()
        self.__textVisible: bool = False
        self.__textWidth: int = 0                            # 0: the natural width
        self.__swatchHandleVisible: bool = True
        self.__textHandleVisible: bool = True
        self.__channelsField: QLineEdit | None = None        # the fields of the text zone, while it is open
        self.__codeField: QLineEdit | None = None
        self.__freeEntry: bool = False                       # the channels' field takes any text until Enter
        self.__typedFrom: _QColorState | None = None         # the colour when a field took the focus
        self.__handleDrag: tuple[QColorEdit._Part, int, int] | None = None   # the handle, where it was taken, its value
        self.__flyout: QColorEdit._TextFlyout | None = None   # upright, the fields of the text, beside the widget
        self.__dragOffset: float = 0.0                       # from the grip's centre to where it was taken
        self.__pagedChannel: int = -1                        # the band a click away from its grip pages through
        self.__pageTarget: float = 0.0
        self.__pageTimer: QTimer = QTimer(self)
        self.__pageTimer.timeout.connect(self.__stepPage)

        policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed, QSizePolicy.ControlType.LineEdit)
        if orientation == Qt.Orientation.Vertical:
            policy.transpose()
        self.setSizePolicy(policy)
        self.setAttribute(Qt.WidgetAttribute.WA_WState_OwnSizePolicy, False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        if color is not None:
            self.setColor(color)

    # =================================================================== color

    def color(self) -> QColor:
        """Une copie de la couleur retenue, alpha compris."""
        return QColor(self.__color)

    @Slot(QColor)
    def setColor(self, color: QColor) -> None:
        """Fixe la couleur, sans changer l'espace affiché.

        Une couleur invalide est ignorée, de même qu'une couleur qui s'écrit comme la couleur
        retenue sur 8 bits par canal. Une couleur grise garde la teinte déjà affichée.

        Args:
            color: La nouvelle couleur, de n'importe quel espace. Copiée.
        """
        if not color.isValid() or _sameColor(color, self.__color):
            return
        self.__color = QColor(color)
        self.__alpha = color.alphaF()
        self.__components = _componentsOf(color, self.__colorSpace, self.__components, self.__hue())
        self.__repaint()
        self.colorChanged.emit(self.color())

    def channelCount(self) -> int:
        """Le nombre de bandes : les canaux de l'espace courant, plus l'alpha si sa bande est affichée."""
        return len(self.__components) + (1 if self.__alphaShown() else 0)

    def channelValues(self) -> tuple[float, ...]:
        """Les valeurs des canaux de l'espace courant, puis l'alpha si sa bande est affichée.

        Chaque valeur va de 0.0 à 1.0 ; la teinte y est une fraction de tour. Pendant un
        glissement sans suivi, ce sont les valeurs en cours de réglage.
        """
        return (*self.__components, self.__alpha) if self.__alphaShown() else tuple(self.__components)

    @Slot(int, float)
    def setChannelValue(self, channel: int, value: float) -> None:
        """Fixe un canal de l'espace courant, comme le fait un glissement dans sa bande.

        Args:
            channel: Le rang de la bande, à partir de 0.
            value: La valeur, ramenée dans [0.0, 1.0].

        Lève:
            IndexError: Si `channel` n'est le rang d'aucune bande.
        """
        self.__checkChannel(channel)
        self._setChannels({channel: value}, commit=True)

    def currentChannel(self) -> int:
        """Le rang de la bande que le clavier règle."""
        return self.__currentChannel

    @Slot(int)
    def setCurrentChannel(self, channel: int) -> None:
        """Choisit la bande que le clavier règle.

        Lève:
            IndexError: Si `channel` n'est le rang d'aucune bande.
        """
        self.__checkChannel(channel)
        self.__currentChannel = channel
        self.update()

    def useAlpha(self) -> bool:
        """Indique si l'alpha est pris en compte (vrai par défaut)."""
        return self.__useAlpha

    @Slot(bool)
    def setUseAlpha(self, use: bool) -> None:
        """Active ou désactive l'alpha : pastille, dialogue, bande et bascule de l'alpha."""
        if use != self.__useAlpha:
            self.__useAlpha = use
            self.__relayout()

    def hasTracking(self) -> bool:
        """Indique si la couleur suit le glissement d'une poignée (vrai par défaut)."""
        return self.__tracking

    @Slot(bool)
    def setTracking(self, enable: bool) -> None:
        """Active ou désactive le suivi de la couleur pendant un glissement."""
        self.__tracking = enable

    def isDialogEnabled(self) -> bool:
        """Indique si la pastille ouvre le dialogue de couleur (vrai par défaut)."""
        return self.__dialogEnabled

    @Slot(bool)
    def setDialogEnabled(self, enable: bool) -> None:
        """Permet ou interdit l'ouverture du dialogue de couleur."""
        self.__dialogEnabled = enable

    # ============================================================= color space

    def colorSpace(self) -> ColorSpace:
        """L'espace de couleur affiché (`Rgb` par défaut)."""
        return self.__colorSpace

    @Slot(ColorSpace)
    def setColorSpace(self, space: ColorSpace) -> None:
        """Choisit l'espace de couleur affiché ; la couleur ne change pas.

        Le plan garde son rang parmi les plans du nouvel espace, ou revient au premier.

        Lève:
            ValueError: Si `space` n'est pas parmi les espaces offerts.
        """
        if space not in self.__available:
            raise ValueError(f"The colour space {space.name} is not available.")
        if space == self.__colorSpace:
            return
        self.__components = _componentsOf(self._shownColor(), space, None, self.__hue())
        self.__colorSpace = space
        self.__currentChannel = min(self.__currentChannel, self.channelCount() - 1)
        if self.__planeRank >= len(self.planes()):
            self.__planeRank = 0
        self.__relayout()
        self.colorSpaceChanged.emit(space)
        self.planeChanged.emit(*self.plane())

    def availableColorSpaces(self) -> list[ColorSpace]:
        """Les espaces offerts, dans l'ordre où l'étiquette les parcourt."""
        return [space for space in QColorEdit.ColorSpace if space in self.__available]

    @Slot(object)
    def setAvailableColorSpaces(self, spaces: Iterable[ColorSpace]) -> None:
        """Choisit les espaces offerts.

        Si l'espace affiché n'en fait plus partie, le suivant dans l'ordre le remplace.

        Args:
            spaces: Les espaces offerts, un au moins. Leur ordre ne compte pas.

        Lève:
            ValueError: Si `spaces` est vide.
        """
        available = frozenset(spaces)
        if not available:
            raise ValueError("At least one colour space must stay available.")
        self.__available = available
        if self.__colorSpace not in available:
            self.setColorSpace(self.__nextColorSpace())
        self.update()

    # =================================================================== plane

    def isPlaneVisible(self) -> bool:
        """Indique si le plan est demandé (vrai par défaut) ; il n'est dessiné que si les bandes sont déployées."""
        return self.__planeVisible

    @Slot(bool)
    def setPlaneVisible(self, visible: bool) -> None:
        """Montre ou cache le plan, au bout du widget opposé à la pastille."""
        if visible != self.__planeVisible:
            self.__planeVisible = visible
            self.__relayout()
            self.planeVisibleChanged.emit(visible)

    def planes(self) -> list[tuple[int, int]]:
        """Les plans de l'espace courant : toutes les paires de ses canaux, sans l'alpha."""
        return list(combinations(range(len(self.__components)), 2))

    def plane(self) -> tuple[int, int]:
        """Les rangs des deux canaux du plan : celui de l'axe horizontal, puis celui de l'axe vertical."""
        return self.planes()[self.__planeRank]

    @Slot(int, int)
    def setPlane(self, first: int, second: int) -> None:
        """Choisit les deux canaux du plan ; leur ordre ne compte pas.

        Lève:
            ValueError: Si ces deux rangs ne forment pas un plan de l'espace courant.
        """
        pair = (min(first, second), max(first, second))
        if pair not in self.planes():
            raise ValueError(f"The channels {first} and {second} make no plane of {self.__colorSpace.name}.")
        rank = self.planes().index(pair)
        if rank != self.__planeRank:
            self.__planeRank = rank
            self.__relayout()
            self.planeChanged.emit(*pair)

    def planePopupSize(self) -> int:
        """Le côté du plan dans la fenêtre flottante, en pixels."""
        low, high = self.minimumPlanePopupSize(), self.maximumPlanePopupSize()
        asked = self.__planePopupSize or self._DefaultPopupSize * self.__baseThickness()
        return max(low, min(high, asked))

    @Slot(int)
    def setPlanePopupSize(self, size: int) -> None:
        """Fixe le côté du plan de la fenêtre flottante, ramené entre ses deux bornes ; 0 redonne la taille par défaut."""
        self.__planePopupSize = max(0, size)
        if self.__popup is not None:
            self.__popup.relayout()

    def minimumPlanePopupSize(self) -> int:
        """Le plus petit côté permis : quatre fois l'épaisseur d'un `QLineEdit`."""
        return self._PopupSizeRange[0] * self.__baseThickness()

    def maximumPlanePopupSize(self) -> int:
        """Le plus grand côté permis : seize fois l'épaisseur d'un `QLineEdit`."""
        return self._PopupSizeRange[1] * self.__baseThickness()

    @Slot()
    def showPlanePopup(self) -> None:
        """Ouvre le plan dans sa fenêtre flottante, sous le widget ou au-dessus s'il manque de place."""
        if self.__popup is None:
            self.__popup = QColorEdit._PlanePopup(self)
        popup = self.__popup
        popup.relayout()
        anchor = self._geometry()[0].get(QColorEdit._Part.Plane, QRectF(self.rect())).toAlignedRect()
        below = self.mapToGlobal(anchor.bottomLeft() + QPoint(0, self._Line))
        screen = self.screen().availableGeometry()
        x = max(screen.left(), min(below.x(), screen.right() - popup.width()))
        y = below.y()
        if y + popup.height() > screen.bottom():
            y = self.mapToGlobal(anchor.topLeft()).y() - popup.height() - self._Line
        popup.move(x, max(screen.top(), y))
        popup.show()

    def isPlanePopupVisible(self) -> bool:
        """Indique si la fenêtre flottante du plan est ouverte."""
        return self.__popup is not None and self.__popup.isVisible()

    # ============================================================== eyedropper

    def eyedropperButton(self) -> EyedropperButton:
        """La commande de la pipette (`Corner` par défaut)."""
        return self.__eyedropperButton

    @Slot(EyedropperButton)
    def setEyedropperButton(self, button: EyedropperButton) -> None:
        """Choisit la commande de la pipette ; `Section` allonge le widget de sa cellule."""
        self.__eyedropperButton = button
        self.__relayout()

    def screenColorPicker(self) -> QScreenColorPicker:
        """La pipette du widget, créée au besoin : pour en régler le zoom, la moyenne ou la loupe.

        Le widget en reste propriétaire.
        """
        if self.__picker is None:
            self.__picker = QColorEdit._ScreenPicker(self)
            self.__picker.colorSelected.connect(self.__takeColor)
            self.__picker.activeChanged.connect(self.__showPicking)
        return self.__picker

    @Slot()
    def pickScreenColor(self) -> None:
        """Lance la pipette, quelle que soit sa commande ; sans effet si le widget est désactivé ou si une prise est en cours.

        La fenêtre du plan se ferme.
        """
        self.screenColorPicker()
        picker = self.__picker
        if picker is None or not self.isEnabled() or picker.isActive():
            return
        if self.__popup is not None:
            self.__popup.hide()
        self.__hoverPart, self.__hoverChannel = QColorEdit._Part.NoPart, -1
        QToolTip.hideText()
        picker.prepare()
        picker.start()

    # ============================================================== text entry

    def isTextVisible(self) -> bool:
        """Indique si la zone de texte est ouverte, à gauche des bandes (faux par défaut)."""
        return self.__textVisible

    @Slot(bool)
    def setTextVisible(self, visible: bool) -> None:
        """Ouvre ou ferme la zone de texte, à sa largeur (`textWidth`) ; fermée, ce qui y était tapé est retenu.

        Repliée ou à la verticale, la zone n'est pas montrée, mais reste ouverte : elle
        reparaît avec les bandes à l'horizontale.
        """
        if visible == self.__textVisible:
            return
        self.__textVisible = visible
        self.__relayout()
        self.textVisibleChanged.emit(visible)

    def textWidth(self) -> int:
        """La largeur de la zone de texte ouverte, en pixels : sa largeur naturelle par défaut."""
        return self.__textWidth if self.__textWidth > 0 else self.naturalTextWidth()

    @Slot(int)
    def setTextWidth(self, width: int) -> None:
        """Fixe la largeur de la zone de texte ; 0 redonne sa largeur naturelle. Ne l'ouvre ni ne la ferme.

        La zone n'est jamais montrée plus large que sa largeur naturelle, ni au point de
        prendre la place minimum des bandes : elle est rognée à l'affichage.
        """
        width = max(0, width)
        if width == self.__textWidth:
            return
        self.__textWidth = width
        self.__relayout()
        self.textWidthChanged.emit(self.textWidth())

    def naturalTextWidth(self) -> int:
        """La largeur où tiennent les valeurs à leur plus large, et le code s'il en est un : celle d'un clic sur la poignée."""
        metrics = QFontMetrics(self.font())
        room = 3 * metrics.averageCharWidth()           # the margins of a frameless line edit, and some air
        width = metrics.horizontalAdvance(self._fieldTemplate()) + room
        if self._hasCode():
            width += metrics.horizontalAdvance("#" + "D" * (8 if self.__alphaShown() else 6)) + room
        return width

    @Slot()
    def editAsText(self) -> None:
        """Donne le focus aux valeurs écrites, la première sélectionnée ; sans effet si le widget est désactivé.

        À l'horizontale, bandes déployées, la zone de texte s'ouvre au besoin, à sa largeur
        naturelle. À la verticale, les champs s'ouvrent dans un volet flottant, à côté du
        widget. Repliées, les bandes n'ont plus de place : la fenêtre du plan s'ouvre, son
        champ de saisie ouvert.
        """
        if not self.isEnabled():
            return
        if not self.__expanded:
            self.showPlanePopup()
            if self.__popup is not None:
                self.__popup.startEdit()
            return
        if self.__orientation == Qt.Orientation.Vertical:
            self.__openFlyout()
            return
        self.setTextVisible(True)
        field = self.__channelsField
        if field is not None:
            field.setFocus(Qt.FocusReason.ShortcutFocusReason)
            self.__selectSection(field, 0)

    # ================================================================== layout

    def orientation(self) -> Qt.Orientation:
        """L'orientation du widget (horizontale par défaut)."""
        return self.__orientation

    @Slot(Qt.Orientation)
    def setOrientation(self, orientation: Qt.Orientation) -> None:
        """Fixe l'orientation ; comme `QSlider.setOrientation`, la politique de taille est transposée."""
        if orientation == self.__orientation:
            return
        self.__orientation = orientation
        if not self.testAttribute(Qt.WidgetAttribute.WA_WState_OwnSizePolicy):
            self.setSizePolicy(self.sizePolicy().transposed())
            self.setAttribute(Qt.WidgetAttribute.WA_WState_OwnSizePolicy, False)
        self.__relayout()

    def textDirection(self) -> TextDirection:
        """Le sens des textes des bascules (`Aligned` par défaut)."""
        return self.__textDirection

    @Slot(TextDirection)
    def setTextDirection(self, direction: TextDirection) -> None:
        """Choisit le sens des textes ; la police et la taille des bascules s'y ajustent."""
        self.__textDirection = direction
        self.__relayout()

    def invertedAppearance(self) -> bool:
        """Indique si le sens des bandes est inversé (le minimum à droite, ou en haut)."""
        return self.__invertedAppearance

    @Slot(bool)
    def setInvertedAppearance(self, inverted: bool) -> None:
        """Inverse le sens des bandes, comme `QSlider.setInvertedAppearance` ; les axes du plan ne changent pas."""
        self.__invertedAppearance = inverted
        self.update()

    def swatchLength(self) -> int:
        """La longueur de la pastille le long du widget, en pixels, quand les bandes sont déployées."""
        if self.__swatchLength > 0:
            return self.__swatchLength
        return self.__automaticSwatchLength()

    @Slot(int)
    def setSwatchLength(self, length: int) -> None:
        """Fixe la longueur de la pastille ; 0 redonne la longueur automatique, à peu près carrée.

        La longueur se prend sur les bandes : la taille recommandée du widget ne change pas,
        et la pastille cède si les bandes manquent de place.
        """
        self.__swatchLength = max(0, length)
        self.__relayout()

    def hasFrame(self) -> bool:
        """Indique si le cadre du style courant est dessiné autour du widget (vrai par défaut)."""
        return self.__frame

    @Slot(bool)
    def setFrame(self, frame: bool) -> None:
        """Montre ou cache le cadre, comme `QLineEdit.setFrame` ; l'épaisseur recommandée ne change pas."""
        self.__frame = frame
        self.__relayout()

    def isExpanded(self) -> bool:
        """Indique si les bandes sont déployées (vrai par défaut)."""
        return self.__expanded

    @Slot(bool)
    def setExpanded(self, expanded: bool) -> None:
        """Déploie ou replie les bandes ; replié, la pastille occupe toute la longueur."""
        if expanded != self.__expanded:
            self.__expanded = expanded
            self.update()
            self.__placeTextFields()
            self.expandedChanged.emit(expanded)

    def isAlphaVisible(self) -> bool:
        """Indique si la bande de l'alpha est demandée (faux par défaut).

        Elle n'est dessinée que si `useAlpha()` est vrai et les bandes déployées.
        """
        return self.__alphaVisible

    @Slot(bool)
    def setAlphaVisible(self, visible: bool) -> None:
        """Montre ou cache la bande de l'alpha ; l'épaisseur du widget grandit d'un tiers avec elle."""
        if visible != self.__alphaVisible:
            self.__alphaVisible = visible
            self.__relayout()
            self.alphaVisibleChanged.emit(visible)

    def valueNotation(self) -> ValueNotation:
        """L'écriture des valeurs dans les infobulles (`Integer` par défaut)."""
        return self.__valueNotation

    @Slot(ValueNotation)
    def setValueNotation(self, notation: ValueNotation) -> None:
        """Choisit l'écriture des valeurs, et avec elle la taille d'un pas du clavier et de la molette."""
        if notation != self.__valueNotation:
            self.__valueNotation = notation
            self.__relayout()
            self.valueNotationChanged.emit(notation)

    def isExpandToggleVisible(self) -> bool:
        """Indique si la bascule de déploiement est offerte (vrai par défaut)."""
        return self.__expandToggleVisible

    @Slot(bool)
    def setExpandToggleVisible(self, visible: bool) -> None:
        """Montre ou cache la bascule de déploiement."""
        self.__expandToggleVisible = visible
        self.__relayout()

    def isAlphaToggleVisible(self) -> bool:
        """Indique si la bascule de l'alpha est offerte (vrai par défaut)."""
        return self.__alphaToggleVisible

    @Slot(bool)
    def setAlphaToggleVisible(self, visible: bool) -> None:
        """Montre ou cache la bascule de l'alpha."""
        self.__alphaToggleVisible = visible
        self.__relayout()

    def isColorSpaceLabelVisible(self) -> bool:
        """Indique si l'étiquette de l'espace est affichée (vrai par défaut)."""
        return self.__colorSpaceLabelVisible

    @Slot(bool)
    def setColorSpaceLabelVisible(self, visible: bool) -> None:
        """Montre ou cache l'étiquette de l'espace."""
        self.__colorSpaceLabelVisible = visible
        self.__relayout()

    def isNotationToggleVisible(self) -> bool:
        """Indique si la bascule de notation est offerte (faux par défaut)."""
        return self.__notationToggleVisible

    @Slot(bool)
    def setNotationToggleVisible(self, visible: bool) -> None:
        """Montre ou cache la bascule de notation."""
        self.__notationToggleVisible = visible
        self.__relayout()

    def isSwatchHandleVisible(self) -> bool:
        """Indique si la poignée de la pastille est offerte (vrai par défaut)."""
        return self.__swatchHandleVisible

    @Slot(bool)
    def setSwatchHandleVisible(self, visible: bool) -> None:
        """Montre ou cache la poignée de la pastille ; `swatchLength` reste réglable par programme."""
        self.__swatchHandleVisible = visible
        self.__relayout()

    def isTextHandleVisible(self) -> bool:
        """Indique si la poignée du texte est offerte (vrai par défaut)."""
        return self.__textHandleVisible

    @Slot(bool)
    def setTextHandleVisible(self, visible: bool) -> None:
        """Montre ou cache la poignée du texte ; la zone reste ouvrable par `setTextVisible`, F2 ou `editAsText`."""
        self.__textHandleVisible = visible
        self.__relayout()

    def isPlaneToggleVisible(self) -> bool:
        """Indique si la bascule du plan est offerte (vrai par défaut)."""
        return self.__planeToggleVisible

    @Slot(bool)
    def setPlaneToggleVisible(self, visible: bool) -> None:
        """Montre ou cache la bascule du plan."""
        self.__planeToggleVisible = visible
        self.__relayout()

    # ==================================================================== size

    @override
    def sizeHint(self) -> QSize:
        """La taille recommandée : l'épaisseur d'un `QLineEdit`, et des bandes longues de six fois cette épaisseur."""
        return self.__hint(max(self._HintBandLength * self.__baseThickness(),
                               math.ceil(self._MinimumBandGrips * self._gripLength())))

    @override
    def minimumSizeHint(self) -> QSize:
        """La taille minimum recommandée : la pastille, les poignées, les bascules offertes, le plan, et trois longueurs de poignée ; la zone de texte cède."""
        return self.__hint(math.ceil(self._MinimumBandGrips * self._gripLength()))

    # ================================================================== events

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        Part = QColorEdit._Part
        painter = QPainter(self)
        palette = self.palette()
        parts, bands = self._geometry()
        if self.__frame:        # first: some styles fill the inside of a frame
            self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Frame, self.__frameOption(), painter, self)
        if parts[Part.Swatch].isValid():
            painter.fillRect(self.__contentRect(), palette.color(QPalette.ColorRole.Mid))     # the separators
        if not self.isEnabled():
            for rect in parts.values():
                painter.fillRect(rect, palette.color(QPalette.ColorRole.Window))

        # As QColorBox: the colour is the information on display, shown as is even when disabled,
        # except while hovered when disabled, to tell that it cannot be changed from here.
        swatch = parts[Part.Swatch]
        shown = self._shownColor()
        dimmed = not self.isEnabled() and self.underMouse()
        if dimmed:
            shown = _desaturated(shown, self._DisabledHoverDesaturation)
            painter.setOpacity(self._DisabledHoverOpacity)
        if self.__useAlpha and shown.alpha() < 255:
            self._paintCheckerboard(painter, swatch)
        else:
            shown.setAlpha(255)
        painter.fillRect(swatch, shown)
        painter.setOpacity(1.0)
        if not self.isEnabled():
            painter.setOpacity(self._DisabledOpacity)
        if self.__eyedropperButton == EyedropperButton.Corner and Part.Eyedropper in parts:
            self.__paintCorner(painter, parts[Part.Eyedropper])

        # Arrows: `along` points away from the swatch, `across` to where the alpha band is added.
        horizontal = self.__orientation == Qt.Orientation.Horizontal
        Arrow = Qt.ArrowType
        if horizontal:
            along, back = (Arrow.LeftArrow, Arrow.RightArrow) if self.__mirrored() else (Arrow.RightArrow, Arrow.LeftArrow)
            across, acrossBack = Arrow.DownArrow, Arrow.UpArrow
        else:
            along, back, across, acrossBack = Arrow.DownArrow, Arrow.UpArrow, Arrow.RightArrow, Arrow.LeftArrow
        arrows = {Part.ExpandToggle: along if self.__expanded else back,
                  Part.AlphaToggle: across if self.__alphaVisible else acrossBack,
                  Part.PlaneToggle: along if self.__planeVisible else back}
        texts = {Part.SpaceLabel: self._SpaceNames[self.__colorSpace]}
        under = {Part.SpaceLabel: self.tr("alpha") if self.__alphaShown() else ""}
        for part, rect in parts.items():
            if part in arrows or part in texts or part == Part.NotationToggle:
                inert = part == Part.SpaceLabel and len(self.__available) < 2
                self._paintCell(painter, rect, hovered=part == self.__hoverPart, pressed=part == self.__pressedPart,
                                inert=inert)
            if part in arrows:
                self._paintArrow(painter, rect, arrows[part])
            elif part in texts:
                self._paintText(painter, rect, texts[part], turned=self.__textTurned(), under=under.get(part, ""))
            elif part == Part.NotationToggle:
                self._paintNotation(painter, rect, self.__valueNotation)
            elif part == Part.Eyedropper and self.__eyedropperButton == EyedropperButton.Section:
                self._paintCell(painter, rect, hovered=part == self.__hoverPart,
                                pressed=part == self.__pressedPart or self.__picking)
                side = min(rect.width(), rect.height()) * self._SectionIconRatio
                QScreenColorPicker.paintIcon(painter, QRectF(rect.center().x() - side / 2, rect.center().y() - side / 2,
                                                             side, side), palette.color(QPalette.ColorRole.ButtonText))
            elif part in (Part.SwatchHandle, Part.TextHandle):
                self.__paintHandle(painter, rect, part)
            elif part == Part.Text:
                painter.fillRect(rect, palette.color(QPalette.ColorRole.Base))

        reverse = self.__reversed()
        for channel, band in enumerate(bands):
            self._paintBand(painter, channel, band, horizontal, reverse)
        if not self.__picking:          # the eyedropper may take the colours a grip or the cross hides
            for channel, band in enumerate(bands):
                lit = channel in (self.__hoverChannel, self.__draggedChannel)
                focused = self.hasFocus() and channel == self.__currentChannel
                self._paintGrip(painter, channel, band, horizontal, reverse, self._gripLength(), lit, focused)
        if Part.Plane in parts:
            self._paintPlane(painter, parts[Part.Plane], edged=False, crossed=not self.__picking)
        if self.hasFocus():             # as every widget of the style: QColorBox, a check box, a slider
            focus = QStyleOptionFocusRect()
            focus.initFrom(self)
            focus.rect = self.__contentRect().toAlignedRect()
            focus.backgroundColor = palette.color(QPalette.ColorRole.Window)
            painter.setOpacity(1.0)
            self.style().drawPrimitive(QStyle.PrimitiveElement.PE_FrameFocusRect, focus, painter, self)

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        Part = QColorEdit._Part
        point = event.position().toPoint()
        part = self.__partAt(point)
        middle = event.button() == Qt.MouseButton.MiddleButton and part == Part.Bands
        if event.button() != Qt.MouseButton.LeftButton and not middle:
            event.ignore()
            return
        event.accept()
        self.__pressedPart = part
        if part == Part.Eyedropper:                     # press, drag to a colour, release; or a mere click
            self.__eyedropperDragged = True
            self.__pressPosition = event.globalPosition().toPoint()
            self.pickScreenColor()
        elif part in (Part.SwatchHandle, Part.TextHandle):     # from the length on display, which may have given way
            self.__handleDrag = (part, self.__alongOf(point), self.__shownLength(part))
            self.__pressPosition = event.globalPosition().toPoint()
        elif part == Part.Bands:
            channel = self.__currentChannel = self.__channelAt(point)
            jump = middle or bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
            offset = self.__gripOffset(channel, point)
            if jump or offset is not None:              # drag the grip, from where it was taken, or from here
                self.__draggedChannel = channel
                self.__dragOffset = 0.0 if jump or offset is None else offset
                self.__dragTo(point, event.globalPosition().toPoint())
            else:                                       # as QSlider: a page toward the pointer, again while held
                self.__pagedChannel = channel
                self.__pageTarget = self.__valueAt(channel, point)
                self.__stepPage()
                self.__pageTimer.start(self._RepeatDelay)
        self.update()

    @override
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        Part = QColorEdit._Part
        point = event.position().toPoint()
        if self.__eyedropperDragged:
            self.screenColorPicker().moveTo(event.globalPosition().toPoint())
            return
        if self.__draggedChannel >= 0:
            self.__dragTo(point, event.globalPosition().toPoint())
            return
        if self.__pagedChannel >= 0:                    # the pages go on toward the pointer where it now is
            self.__pageTarget = self.__valueAt(self.__pagedChannel, point)
            return
        if self.__handleDrag is not None:
            handle, start, value = self.__handleDrag
            along = self.__alongOf(point)
            length = value + along - start
            if handle == Part.TextHandle and self.__orientation == Qt.Orientation.Vertical:
                return                                  # upright, the text's handle is only clicked
            if handle == Part.SwatchHandle:
                self.setSwatchLength(max(self.__handleLength(), length))
                shown = self.__shownLength(handle)
                self.__swatchLength = shown
            else:
                self.setTextVisible(True)
                self.setTextWidth(max(1, length))
                shown = self.__shownLength(handle)
                if shown < self.textWidth():
                    self.__textWidth = shown
                    self.textWidthChanged.emit(shown)
            if shown < length:          # stopped where the bands stop it: coming back acts at once
                self.__handleDrag = (handle, along, shown)
            return
        handles = (Part.SwatchHandle, Part.TextHandle)
        if self.__partAt(point) in handles:
            self.setCursor(Qt.CursorShape.SplitHCursor if self.__orientation == Qt.Orientation.Horizontal
                           else Qt.CursorShape.SplitVCursor)
        elif self.__hoverPart in handles:
            self.unsetCursor()
        part = self.__partAt(point)
        channel = self.__channelAt(point) if part == Part.Bands else -1
        if (part, channel) != (self.__hoverPart, self.__hoverChannel):
            self.__hoverPart, self.__hoverChannel = part, channel
            self.update()
            QToolTip.hideText()        # that of the part just left
        if channel >= 0:               # a band tells its value at once, without the usual delay
            QToolTip.showText(event.globalPosition().toPoint(), self._toolTipAt(point), self)

    @override
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        Part = QColorEdit._Part
        if event.button() not in (Qt.MouseButton.LeftButton, Qt.MouseButton.MiddleButton):
            event.ignore()
            return
        event.accept()
        pressed, self.__pressedPart = self.__pressedPart, Part.NoPart
        self.update()
        if self.__handleDrag is not None:
            handle = self.__handleDrag[0]
            self.__handleDrag = None
            moved = (event.globalPosition().toPoint() - self.__pressPosition).manhattanLength()
            natural = self.naturalTextWidth()
            if handle == Part.TextHandle and self.__orientation == Qt.Orientation.Vertical:
                if moved < QApplication.startDragDistance():
                    self.__openFlyout()
            elif handle == Part.TextHandle and moved < QApplication.startDragDistance():
                self.setTextVisible(not self.__textVisible)                    # a click opens or closes it
            elif handle == Part.TextHandle and self.textWidth() < natural * self._ClosingFraction:
                self.setTextVisible(False)                                     # dragged nearly shut: shut,
                self.setTextWidth(0)                                           # to open at the natural width
        elif self.__pagedChannel >= 0:
            self.__pageTimer.stop()
            self.__pagedChannel = -1
            self._commit()
        elif event.button() != Qt.MouseButton.LeftButton:
            if self.__draggedChannel >= 0:              # the drag of a middle click
                self.__draggedChannel = -1
                self._commit()
                QToolTip.hideText()
        elif self.__eyedropperDragged:
            self.__eyedropperDragged = False
            if (event.globalPosition().toPoint() - self.__pressPosition).manhattanLength() >= QApplication.startDragDistance():
                picker = self.screenColorPicker()
                picker.moveTo(event.globalPosition().toPoint())
                picker.select()
        elif self.__draggedChannel >= 0:
            self.__draggedChannel = -1
            self._commit()
            QToolTip.hideText()
        elif pressed != Part.NoPart and pressed == self.__partAt(event.position().toPoint()):
            self.__click(pressed)

    @override
    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """Sur la poignée de la pastille, rend sa longueur automatique ; ailleurs, un clic de plus."""
        if (event.button() == Qt.MouseButton.LeftButton
                and self.__partAt(event.position().toPoint()) == QColorEdit._Part.SwatchHandle):
            event.accept()
            self.setSwatchLength(0)
            return
        self.mousePressEvent(event)

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        self.update()       # disabled, the swatch tells it when hovered
        super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        self.__hoverPart, self.__hoverChannel = QColorEdit._Part.NoPart, -1
        if self.__handleDrag is None:
            self.unsetCursor()
        self.update()

    @override
    def focusInEvent(self, event: QFocusEvent) -> None:
        self.update()       # the current grip shows the focus
        super().focusInEvent(event)

    @override
    def focusOutEvent(self, event: QFocusEvent) -> None:
        self.update()
        super().focusOutEvent(event)

    @override
    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        plain = not event.modifiers() & ~Qt.KeyboardModifier.KeypadModifier
        if event.matches(QKeySequence.StandardKey.Copy):
            QApplication.clipboard().setText(self._colorText())
            return
        if event.matches(QKeySequence.StandardKey.Paste):
            self._applyText(QApplication.clipboard().text())
            return
        if plain and key == Qt.Key.Key_F2:
            self.editAsText()
            return
        if plain and key == Qt.Key.Key_I:
            self.pickScreenColor()
            return
        if plain and key == Qt.Key.Key_P:
            self.showPlanePopup()
            return
        if key in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.__click(QColorEdit._Part.Swatch)
            return
        horizontal = self.__orientation == Qt.Orientation.Horizontal
        lower, higher = (Qt.Key.Key_Left, Qt.Key.Key_Right) if horizontal else (Qt.Key.Key_Down, Qt.Key.Key_Up)
        if self.__reversed():           # an arrow moves the grip the way it points
            lower, higher = higher, lower
        previous, following = (Qt.Key.Key_Up, Qt.Key.Key_Down) if horizontal else (Qt.Key.Key_Left, Qt.Key.Key_Right)
        steps: dict[int, int] = {lower: -1, higher: 1, Qt.Key.Key_PageDown: -self._PageSteps,
                                 Qt.Key.Key_PageUp: self._PageSteps}
        channel = self.__currentChannel
        if not self.__expanded:
            event.ignore()
        elif key in steps:
            self._setChannels({channel: self.channelValues()[channel] + steps[key] * self._step(channel)}, commit=True)
        elif key in (Qt.Key.Key_Home, Qt.Key.Key_End):
            self._setChannels({channel: 0.0 if key == Qt.Key.Key_Home else 1.0}, commit=True)
        elif key in (previous, following):
            self.setCurrentChannel(max(0, min(self.channelCount() - 1, channel + (1 if key == following else -1))))
        else:
            event.ignore()

    @override
    def wheelEvent(self, event: QWheelEvent) -> None:
        point = event.position().toPoint()
        delta = event.angleDelta().y() or event.angleDelta().x()
        if delta == 0 or self.__partAt(point) != QColorEdit._Part.Bands:
            event.ignore()
            return
        event.accept()
        self.__wheelRemainder += -delta if event.inverted() else delta
        notches = int(self.__wheelRemainder / self._WheelNotch)
        if notches == 0:
            return
        self.__wheelRemainder -= notches * self._WheelNotch
        if event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            notches *= self._PageSteps
        channel = self.__channelAt(point)
        self._setChannels({channel: self.channelValues()[channel] + notches * self._step(channel)}, commit=True)

    @override
    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.ToolTip and isinstance(event, QHelpEvent):
            text = self._toolTipAt(event.pos())
            if text:
                QToolTip.showText(event.globalPos(), text, self)
            else:
                QToolTip.hideText()
                event.ignore()
            return True
        return super().event(event)

    @override
    def changeEvent(self, event: QEvent) -> None:
        if event.type() in (QEvent.Type.FontChange, QEvent.Type.StyleChange, QEvent.Type.LayoutDirectionChange):
            self.updateGeometry()       # every dimension derives from the font and the style
            self.update()
            self.__placeTextFields()
        super().changeEvent(event)

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.__placeTextFields()
        super().resizeEvent(event)

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Les touches et le focus des champs de la zone de texte."""
        fields = [field for field in (self.__channelsField, self.__codeField) if field is not None]
        if watched not in fields:
            return super().eventFilter(watched, event)
        field = cast(QLineEdit, watched)
        if event.type() == QEvent.Type.KeyPress and isinstance(event, QKeyEvent):
            return self.__typeKey(field, event)
        if event.type() == QEvent.Type.FocusIn and self.__typedFrom is None:
            self.__typedFrom = self._colorState()       # what Escape gives back
        elif event.type() == QEvent.Type.FocusOut:
            QTimer.singleShot(0, self, self.__leaveText)
        return False

    # ================================================================ protected

    class _Part(Enum):
        """Une partie du widget, pour le dessin et pour la souris."""

        NoPart = 0
        Swatch = 1
        ExpandToggle = 2
        AlphaToggle = 3
        SpaceLabel = 4
        NotationToggle = 5
        Bands = 6
        Plane = 7
        PlaneToggle = 8
        Eyedropper = 9
        SwatchHandle = 10
        TextHandle = 11
        Text = 12

    _SpaceNames: Final[dict[ColorSpace, str]] = {
        ColorSpace.Rgb: "RGB", ColorSpace.Hsv: "HSV", ColorSpace.Hsl: "HSL", ColorSpace.Cmyk: "CMYK"}
    _AlphaLetter: Final[str] = "A"
    _NotationSteps: Final[int] = 3           # steps of the pictogram of the integer notation
    _HueChannels: Final[frozenset[ColorSpace]] = frozenset({ColorSpace.Hsv, ColorSpace.Hsl})

    _Line: Final[int] = 1                    # hairline, in logical pixels: separators, gaps between bands
    _LineEditVerticalMargin: Final[int] = 1  # both as QLineEdit::sizeHint, to get its exact height
    _LineEditMinimumTextHeight: Final[int] = 14
    _HintBandLength: Final[int] = 6          # length of the bands in sizeHint, in line-edit heights
    _MinimumBandGrips: Final[int] = 3        # length of the bands in minimumSizeHint, in grips
    _NominalBands: Final[int] = 3            # the reference case a grip is sized from: three bands, no alpha
    _GripRatio: Final[int] = 2               # a grip is that many nominal band thicknesses long
    _AlphaGrowth: Final[int] = 3             # the alpha band adds one such fraction of the thickness
    _GradientStops: Final[int] = 12          # intervals of a band's gradient: exact for every channel, hue included
    _PlaneGrid: Final[int] = 64              # a plane is computed on at most that many points a side, then scaled
    _DefaultPopupSize: Final[int] = 8        # side of the plane in its popup, in line-edit heights
    _PopupSizeRange: Final[tuple[int, int]] = (4, 16)
    _PageSteps: Final[int] = 10              # steps of a page key, or of a wheel notch with a modifier
    _WheelNotch: Final[int] = 120            # eighths of a degree for one notch of a wheel
    _RepeatDelay: Final[int] = 500           # ms before a held click pages again, then between pages: as QAbstractSlider
    _RepeatInterval: Final[int] = 50
    _HueTurn: Final[int] = 360
    _ByteMax: Final[int] = 255
    _RealStep: Final[float] = 0.01
    _AlongFontScale: Final[float] = 0.85     # texts along the widget: the widget's font, a little smaller
    _SmallFontScale: Final[float] = 0.65     # the second line of the space label, and the values of the popup
    _SmallestPointSize: Final[float] = 1.0   # guard of the font fitting loop, never reached in practice
    _DisabledOpacity: Final[float] = 0.4
    _DisabledHoverDesaturation: Final[float] = 0.5   # the swatch, disabled and hovered: as QColorBox
    _DisabledHoverOpacity: Final[float] = 0.8
    _CornerRatio: Final[float] = 1.0         # side of the eyedropper's corner, from the inner thickness without alpha
    _IconRatio: Final[float] = 0.58          # side of the eyedropper's icon, from the corner's
    _IconCentre: Final[float] = 0.64         # centre of the icon, from the corner's square, away from its right angle
    _SectionRatio: Final[float] = 0.85       # length of the eyedropper's section, from the height of a line edit
    _HandleFraction: Final[int] = 4          # a handle is that fraction of a line edit's height long
    _HandleLeast: Final[int] = 5
    _HandleDot: Final[float] = 1.5           # side of a dot of a handle
    _HandleDotOpacity: Final[float] = 0.55
    _ClosingFraction: Final[float] = 0.5     # a text zone dragged narrower than that of its natural width closes
    _SectionIconRatio: Final[float] = 0.62   # side of the icon, from the section's least side
    # Fixed whatever the theme: a grip, a cross and a checkerboard must read on any colour.
    _GripCoreColor: Final[QColor] = QColor(250, 250, 250)
    _GripEdgeColor: Final[QColor] = QColor(24, 24, 24)
    _CheckerColors: Final[tuple[QColor, QColor]] = (QColor(255, 255, 255), QColor(200, 200, 200))

    def _chooseColor(self) -> None:
        """Ouvre le dialogue de couleur et retient la couleur choisie ; une annulation ne change rien."""
        options = (QColorDialog.ColorDialogOption.ShowAlphaChannel if self.__useAlpha
                   else QColorDialog.ColorDialogOption(0))
        chosen = QColorDialog.getColor(self.color(), self, self.tr("Select Color"), options)
        if chosen.isValid():
            if not self.__useAlpha:
                chosen.setAlphaF(self.__alpha)
            self.setColor(chosen)

    def _shownColor(self) -> QColor:
        """La couleur que les canaux composent : celle retenue, ou celle d'un glissement sans suivi."""
        return _colorFrom(self.__colorSpace, self.__components, self.__alpha)

    def _setChannels(self, values: dict[int, float], *, commit: bool) -> None:
        """Fixe un ou plusieurs canaux d'un coup, chacun ramené dans [0.0, 1.0].

        Args:
            values: La valeur de chaque canal à changer, par son rang de bande.
            commit: Vrai pour retenir aussitôt la couleur ; faux pendant un glissement sans suivi.
        """
        for channel, value in values.items():
            value = max(0.0, min(1.0, float(value)))
            if channel < len(self.__components):
                self.__components[channel] = value
            else:
                self.__alpha = value
        self.__repaint()
        if commit:
            self._commit()

    def _commit(self) -> None:
        """Retient la couleur que les canaux composent, et l'annonce si elle a changé."""
        composed = self._shownColor()
        if not _sameColor(composed, self.__color):
            self.__color = composed
            self.colorChanged.emit(self.color())

    def _toolTipAt(self, point: QPoint) -> str:
        """Le texte de l'infobulle de la partie située sous un point : son état, l'effet d'un clic, les raccourcis.

        Retourne:
            Une chaîne vide hors de toute partie.
        """
        Part = QColorEdit._Part
        part = self.__partAt(point)
        if part == Part.Bands:
            return self._bandToolTip(self.__channelAt(point), self.__orientation == Qt.Orientation.Horizontal)
        if part == Part.Plane:
            return self._planeToolTip(self.tr("Click · P: open the plane"))
        tips = {Part.Swatch: self.__swatchToolTip, Part.Eyedropper: self.__eyedropperToolTip,
                Part.ExpandToggle: self.__expandToolTip,
                Part.AlphaToggle: self.__alphaToolTip, Part.SpaceLabel: self.__spaceToolTip,
                Part.NotationToggle: self.__notationToolTip, Part.PlaneToggle: self.__planeToggleToolTip,
                Part.SwatchHandle: self.__swatchHandleToolTip, Part.TextHandle: self.__textHandleToolTip}
        return tips[part]() if part in tips else ""

    def _bandToolTip(self, channel: int, horizontal: bool, keys: bool = True) -> str:
        """L'infobulle d'une bande : la lettre du canal, sa valeur, son étendue, puis les gestes.

        Args:
            channel: Le rang du canal ; au-delà des canaux de l'espace, l'alpha.
            horizontal: Vrai si la bande court à l'horizontale.
            keys: Faux pour une bande que le clavier ne règle pas : celles de la fenêtre flottante.
        """
        if self.__valueNotation == QColorEdit.ValueNotation.Real:
            scope = "0.0–1.0"
        elif self.__valueNotation == QColorEdit.ValueNotation.Hexadecimal:
            scope = f"000–{self._HueTurn - 1:03X}" if self.__isHue(channel) else f"00–{self._ByteMax:02X}"
        else:
            scope = f"0–{self._HueTurn - 1}" if self.__isHue(channel) else f"0–{self._ByteMax}"
        if keys:
            gestures = (self.tr("Drag the grip · Click: ±{0} toward · Shift+click: here").format(self._PageSteps) + "\n"
                + self.tr("Wheel · {0} ±1 · PgUp PgDn ±{1} · Home End").format(
                    "← →" if horizontal else "↑ ↓", self._PageSteps) + "\n"
                + self.tr("F2: type the values · Ctrl+C Ctrl+V"))
        else:
            gestures = self.tr("Drag · Wheel ±1 · Shift+Wheel ±{0}").format(self._PageSteps)
        return f"{self._channelLetter(channel)} {self._valueText(channel)}  [{scope}]\n\n{gestures}"

    def _planeToolTip(self, action: str) -> str:
        """L'infobulle du plan : ses deux canaux et leurs valeurs, puis le geste donné."""
        first, second = self.plane()
        return (self.tr("Plane {0}").format(self._planeName(self.plane())) + "\n"
                + f"{self._channelLetter(first)} {self._valueText(first)}  "
                  f"{self._channelLetter(second)} {self._valueText(second)}\n\n{action}")

    def _channelLetter(self, channel: int) -> str:
        """La lettre d'un canal de l'espace courant ; au-delà, celle de l'alpha."""
        letters = self._SpaceNames[self.__colorSpace]
        return letters[channel] if channel < len(letters) else self._AlphaLetter

    def _planeName(self, plane: tuple[int, int]) -> str:
        """Le nom d'un plan : les lettres de ses deux canaux."""
        return self._channelLetter(plane[0]) + self._channelLetter(plane[1])

    def _valueText(self, channel: int) -> str:
        """La valeur d'un canal de l'espace courant, ou de l'alpha au-delà, dans la notation courante."""
        value = self.__components[channel] if channel < len(self.__components) else self.__alpha
        if self.__valueNotation == QColorEdit.ValueNotation.Real:
            return f"{value:.3f}"
        whole = self.__wholeValue(channel, value)
        if self.__valueNotation == QColorEdit.ValueNotation.Hexadecimal:
            return f"{whole:03X}" if self.__isHue(channel) else f"{whole:02X}"
        return str(whole)

    def _textFont(self, along: bool, small: bool = False) -> QFont:
        """La police des textes : celle du widget, en gras, réduite jusqu'à tenir dans l'épaisseur.

        Elle est réglée une fois pour toutes sur le cas le plus contraignant, deux lignes dans
        l'étiquette de l'espace, que la bande de l'alpha soit affichée ou non.

        Args:
            along: Vrai si le texte court le long du widget : ses deux lignes doivent alors
                tenir en hauteur. Faux s'il court en travers : c'est le plus long texte qui
                doit tenir en largeur.
            small: Vrai pour la petite police : la seconde ligne de l'étiquette de l'espace.
        """
        font = QFont(self.font())
        font.setBold(True)
        room = self.__baseThickness() - 4 * self._Line      # the frame, and as much around the text
        texts = self.__cellTexts(QColorEdit._Part.SpaceLabel)
        size = font.pointSizeF() if font.pointSizeF() > 0 else float(QApplication.font().pointSizeF())
        size *= self._AlongFontScale if along else 1.0
        while size > self._SmallestPointSize:
            font.setPointSizeF(size)
            metrics = QFontMetrics(font)
            if along:
                lower = QFont(font)
                lower.setPointSizeF(size * self._SmallFontScale)
                needed = metrics.height() + QFontMetrics(lower).height()
            else:
                needed = max(metrics.horizontalAdvance(text) for text in texts)
            if needed <= room:
                break
            size -= 0.5
        if small:
            font.setPointSizeF(size * self._SmallFontScale)
        return font

    def _gripLength(self) -> float:
        """La longueur d'une poignée le long de sa bande, la même pour toutes.

        Deux fois l'épaisseur d'une bande dans le cas de référence : trois bandes, sans alpha,
        à l'épaisseur recommandée du widget.
        """
        scale = self.devicePixelRatioF()
        line = max(1, round(self._Line * scale))
        content = self.__baseThickness() - 2 * self.__frameWidth() - (self._NominalBands - 1) * self._Line
        return max(3 * line, round(self._GripRatio * content / self._NominalBands * scale)) / scale

    def _geometry(self) -> tuple[dict[_Part, QRectF], list[QRectF]]:
        """La place de chaque partie, puis celle de chaque bande, pour la taille actuelle du widget.

        Tout est calculé en pixels de l'écran, puis rendu en coordonnées du widget : un bord
        tombe toujours entre deux pixels, quelle que soit l'échelle d'affichage.
        """
        Part = QColorEdit._Part
        scale = self.devicePixelRatioF()
        horizontal = self.__orientation == Qt.Orientation.Horizontal
        mirrored = self.__mirrored()
        line = max(1, round(self._Line * scale))
        edge = round(self.__frameWidth() * scale)
        total = round((self.width() if horizontal else self.height()) * scale)
        alongEnd = total - edge
        thickness = round((self.height() if horizontal else self.width()) * scale) - 2 * edge

        def rect(along: int, length: int, across: int, size: int) -> QRectF:
            length, size = max(0, length), max(0, size)
            if mirrored:
                along = total - along - length
            if horizontal:
                return QRectF(along / scale, across / scale, length / scale, size / scale)
            return QRectF(across / scale, along / scale, size / scale, length / scale)

        folded = (Part.Eyedropper, Part.ExpandToggle)           # what stays next to the swatch when folded
        cells = self.__cells() if self.__expanded else [part for part in self.__cells() if part in folded]
        lengths = {part: round(self.__cellLength(part) * scale) for part in cells}
        parts: dict[QColorEdit._Part, QRectF] = {}
        along = edge
        handle = round(self.__handleLength() * scale)
        textLength = 0
        if self.__expanded:
            # The swatch, then the text, give way so that the bands keep their least length.
            handles = int(self.__swatchHandleVisible) + int(self.__textHandleVisible)
            fixed = 2 * edge + line + handles * (handle + line) + sum(length + line for length in lengths.values())
            fixed += (round(self.__cellLength(Part.PlaneToggle) * scale) + line) if self.__planeToggleVisible else 0
            fixed += (thickness + line) if self.__planeVisible else 0
            room = max(0, total - fixed - round(self._MinimumBandGrips * self._gripLength() * scale))
            swatchLength = min(round(self.swatchLength() * scale), room)
            if horizontal and self.__textVisible:       # never wider than its natural width: past it, only blank
                textLength = max(0, min(round(min(self.textWidth(), self.naturalTextWidth()) * scale),
                                        room - swatchLength - line))
        else:
            swatchLength = alongEnd - edge - sum(length + line for length in lengths.values())
        parts[Part.Swatch] = rect(along, swatchLength, edge, thickness)
        if self.__eyedropperButton == EyedropperButton.Corner:
            # A square at the far end of the swatch, across at its bottom (or right); fixed, whether alpha shows or not.
            content = round(self.__baseThickness() * scale) - 2 * edge
            corner = min(max(0, swatchLength), thickness, round(self._CornerRatio * content))
            if corner > 0:
                parts[Part.Eyedropper] = rect(along + swatchLength - corner, corner, edge + thickness - corner, corner)
        along += max(0, swatchLength) + line
        swatchHandle = self.__expanded and self.__swatchHandleVisible
        for part in cells:
            if part != Part.Eyedropper and swatchHandle and Part.SwatchHandle not in parts:
                parts[Part.SwatchHandle] = rect(along, handle, edge, thickness)     # after the swatch and its section
                along += handle + line
            parts[part] = rect(along, lengths[part], edge, thickness)
            along += lengths[part] + line
        if swatchHandle and Part.SwatchHandle not in parts:
            parts[Part.SwatchHandle] = rect(along, handle, edge, thickness)
            along += handle + line
        if not self.__expanded:
            return parts, []
        # The text zone, then its handle, as a splitter's, before the bands; upright, the handle alone opens a flyout.
        if textLength > 0:
            parts[Part.Text] = rect(along, textLength, edge, thickness)
            along += textLength + line
        if self.__textHandleVisible:
            parts[Part.TextHandle] = rect(along, handle, edge, thickness)
            along += handle + line

        # From the far end backwards: the plane's toggle, then the plane, a square.
        if self.__planeToggleVisible:
            length = round(self.__cellLength(Part.PlaneToggle) * scale)
            parts[Part.PlaneToggle] = rect(alongEnd - length, length, edge, thickness)
            alongEnd -= length + line
        if self.__planeVisible:
            parts[Part.Plane] = rect(alongEnd - thickness, thickness, edge, thickness)
            alongEnd -= thickness + line
        parts[Part.Bands] = rect(along, alongEnd - along, edge, thickness)

        # Equal bands, in whole pixels: the pixels left over go to the last bands.
        count = self.channelCount()
        room = max(0, thickness - (count - 1) * line)
        bands: list[QRectF] = []
        across = edge
        for rank in range(count):
            size = room // count + (1 if rank >= count - room % count else 0)
            bands.append(rect(along, alongEnd - along, across, size))
            across += size + line
        return parts, bands

    # -- Painting, shared with the plane's popup ---------------------------------

    def _paintCheckerboard(self, painter: QPainter, rect: QRectF) -> None:
        """Peint un damier dans un rectangle, à cases d'une demi-épaisseur."""
        scale = self.devicePixelRatioF()
        line = max(1, round(self._Line * scale))
        cell = max(2 * line, round(min(rect.width(), rect.height()) * scale) // 2) / scale
        painter.save()
        painter.setClipRect(rect)
        painter.fillRect(rect, self._CheckerColors[0])
        for row in range(int(rect.height() / cell) + 1):
            for column in range(row % 2, int(rect.width() / cell) + 1, 2):
                painter.fillRect(QRectF(rect.left() + column * cell, rect.top() + row * cell, cell, cell),
                                 self._CheckerColors[1])
        painter.restore()

    def _paintCell(self, painter: QPainter, rect: QRectF, *, hovered: bool, pressed: bool, inert: bool = False) -> None:
        """Peint le fond d'une bascule ou d'une étiquette, teinté au survol et à l'appui."""
        palette = self.palette()
        painter.fillRect(rect, palette.color(QPalette.ColorRole.Button))
        if inert or not self.isEnabled() or not (hovered or pressed):
            return
        tint = QColor(palette.color(QPalette.ColorRole.Highlight))
        tint.setAlphaF(0.45 if pressed else 0.25)
        painter.fillRect(rect, tint)

    def _paintText(self, painter: QPainter, rect: QRectF, text: str, *, turned: bool, along: bool | None = None,
                   under: str = "", small: bool = False) -> None:
        """Peint un texte centré dans une cellule, avec au besoin une seconde ligne en petit.

        Args:
            painter: Le peintre.
            rect: La cellule.
            text: Le texte.
            turned: Vrai pour le tourner d'un quart de tour (il se lit alors de bas en haut).
            along: La police à prendre (voir `_textFont`) ; None pour celle du sens courant des textes.
            under: Une seconde ligne, en petit, sous la première, qui remonte pour lui faire place.
            small: Vrai pour écrire `text` lui-même en petit, raccourci s'il dépasse la cellule.
        """
        along = self.__textAlong() if along is None else along
        font = self._textFont(along, small)
        metrics = QFontMetrics(font)
        lowerFont = self._textFont(along, True)
        lowerMetrics = QFontMetrics(lowerFont)
        if small:
            text = metrics.elidedText(text, Qt.TextElideMode.ElideRight, int(rect.width()))
        shift = lowerMetrics.height() / 2 if under else 0.0     # the two lines, centred as one block
        painter.save()
        painter.setPen(self.palette().color(QPalette.ColorRole.ButtonText))
        painter.translate(rect.center())
        if turned:
            painter.rotate(-90)
        painter.setFont(font)
        painter.drawText(QPointF(-metrics.horizontalAdvance(text) / 2,
                                 (metrics.ascent() - metrics.descent()) / 2 - shift), text)
        if under:
            painter.setFont(lowerFont)
            painter.drawText(QPointF(-lowerMetrics.horizontalAdvance(under) / 2,
                                     (lowerMetrics.ascent() - lowerMetrics.descent()) / 2 + metrics.height() / 2), under)
        painter.restore()

    def _paintArrow(self, painter: QPainter, rect: QRectF, direction: Qt.ArrowType) -> None:
        """Peint un chevron au centre d'une cellule, à la taille de la police des textes."""
        reach = QFontMetrics(self._textFont(self.__textAlong())).ascent() / 4
        tip: dict[Qt.ArrowType, tuple[float, float]] = {
            Qt.ArrowType.RightArrow: (1, 0), Qt.ArrowType.LeftArrow: (-1, 0),
            Qt.ArrowType.DownArrow: (0, 1), Qt.ArrowType.UpArrow: (0, -1)}
        dx, dy = tip[direction]
        center = rect.center()
        apex = center + QPointF(dx, dy) * (reach / 2)
        back = center - QPointF(dx, dy) * (reach / 2)
        side = QPointF(-dy, dx) * reach
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(self.palette().color(QPalette.ColorRole.ButtonText), max(1.0, reach / 2))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawPolyline([back + side, apex, back - side])
        painter.restore()

    def _notationSide(self) -> float:
        """Le côté du pictogramme de la notation : la hauteur d'une capitale, en paliers d'un nombre entier de pixels."""
        scale = self.devicePixelRatioF()
        capital = QFontMetrics(self._textFont(self.__textAlong())).ascent()
        return self._NotationSteps * max(1, round(capital * scale / self._NotationSteps)) / scale

    def _paintNotation(self, painter: QPainter, rect: QRectF, notation: ValueNotation) -> None:
        """Peint le pictogramme d'une notation au centre d'une cellule : des paliers, ou une pente continue."""
        scale = self.devicePixelRatioF()
        side = self._notationSide()
        left = round((rect.center().x() - side / 2) * scale) / scale
        top = round((rect.center().y() - side / 2) * scale) / scale
        color = self.palette().color(QPalette.ColorRole.ButtonText)
        painter.save()
        if notation == QColorEdit.ValueNotation.Integer:
            step = side / self._NotationSteps
            for rank in range(self._NotationSteps):
                painter.fillRect(QRectF(left + rank * step, top + side - (rank + 1) * step, step, (rank + 1) * step), color)
        elif notation == QColorEdit.ValueNotation.Hexadecimal:      # a hash sign, as in #RRGGBB
            stroke = max(1, round(side * scale / 6)) / scale
            for offset in (side / 3, 2 * side / 3):
                at = round((offset - stroke / 2) * scale) / scale
                painter.fillRect(QRectF(left + at, top, stroke, side), color)
                painter.fillRect(QRectF(left, top + at, side, stroke), color)
        else:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawPolygon(QPolygonF([QPointF(left, top + side), QPointF(left + side, top + side),
                                           QPointF(left + side, top)]))
        painter.restore()

    def _bandAxis(self, band: QRectF, horizontal: bool, reverse: bool, grip: float) -> tuple[QPointF, QPointF]:
        """Le centre d'une poignée aux valeurs 0 et 1 (une seule coordonnée compte).

        Args:
            band: Le rectangle de la bande.
            horizontal: Vrai si la bande court à l'horizontale.
            reverse: Vrai si la valeur augmente vers la gauche, ou vers le bas.
            grip: La longueur de la poignée.
        """
        if horizontal:
            low, high = QPointF(band.left() + grip / 2, 0), QPointF(band.right() - grip / 2, 0)
        else:
            low, high = QPointF(0, band.bottom() - grip / 2), QPointF(0, band.top() + grip / 2)
        return (high, low) if reverse else (low, high)

    def _bandValueAt(self, band: QRectF, horizontal: bool, reverse: bool, grip: float, point: QPoint) -> float:
        """La valeur qu'un point désigne dans une bande, sans la borner."""
        start, stop = self._bandAxis(band, horizontal, reverse, grip)
        travel = (stop.x() - start.x()) if horizontal else (stop.y() - start.y())
        if travel == 0:
            return 0.0
        return ((point.x() - start.x()) if horizontal else (point.y() - start.y())) / travel

    def _paintBand(self, painter: QPainter, channel: int, band: QRectF, horizontal: bool, reverse: bool,
                   grip: float | None = None) -> None:
        """Peint le dégradé d'une bande : la couleur qu'on obtiendrait à chaque position.

        Args:
            painter: Le peintre.
            channel: Le rang du canal ; au-delà des canaux de l'espace, l'alpha.
            band: Le rectangle de la bande.
            horizontal: Vrai si la bande court à l'horizontale.
            reverse: Vrai si la valeur augmente vers la gauche, ou vers le bas.
            grip: La longueur de la poignée ; None pour celle du widget.
        """
        if band.isEmpty():
            return
        start, stop = self._bandAxis(band, horizontal, reverse, self._gripLength() if grip is None else grip)
        # Beyond its two ends, a gradient keeps its end colours: that fills the half grip at each end.
        gradient = QLinearGradient(start, stop)
        if channel >= len(self.__components):
            self._paintCheckerboard(painter, band)
            for position, alpha in ((0.0, 0.0), (1.0, 1.0)):
                gradient.setColorAt(position, _colorFrom(self.__colorSpace, self.__components, alpha))
        else:
            for stopRank in range(self._GradientStops + 1):
                position = stopRank / self._GradientStops
                components = list(self.__components)
                components[channel] = position
                gradient.setColorAt(position, _colorFrom(self.__colorSpace, components, 1.0))
        painter.fillRect(band, QBrush(gradient))

    def _paintGrip(self, painter: QPainter, channel: int, band: QRectF, horizontal: bool, reverse: bool,
                   grip: float, lit: bool, focused: bool = False) -> None:
        """Peint la poignée d'une bande : un rectangle clair bordé de sombre, calé sur les pixels de l'écran.

        Args:
            painter: Le peintre.
            channel: Le rang du canal ; au-delà des canaux de l'espace, l'alpha.
            band: Le rectangle de la bande.
            horizontal: Vrai si la bande court à l'horizontale.
            reverse: Vrai si la valeur augmente vers la gauche, ou vers le bas.
            grip: La longueur de la poignée.
            lit: Vrai pour border la poignée de la couleur d'accent : survol, glissement.
            focused: Vrai pour la remplir de la couleur d'accent, bordée de sombre : la poignée
                que le clavier règle quand le widget a le focus, comme celle d'un curseur de
                Windows 11.
        """
        if band.isEmpty():
            return
        scale = self.devicePixelRatioF()
        line = max(1, round(self._Line * scale)) / scale
        start, stop = self._bandAxis(band, horizontal, reverse, grip)
        value = self.__components[channel] if channel < len(self.__components) else self.__alpha
        center = start + (stop - start) * value
        if horizontal:
            rect = QRectF(round((center.x() - grip / 2) * scale) / scale, band.top(), grip, band.height())
        else:
            rect = QRectF(band.left(), round((center.y() - grip / 2) * scale) / scale, band.width(), grip)
        lit, focused = lit and self.isEnabled(), focused and self.isEnabled()
        accent = self.palette().color(QPalette.ColorRole.Highlight)
        painter.fillRect(rect, accent if lit and not focused else self._GripEdgeColor)
        core = rect.adjusted(line, line, -line, -line)
        if core.width() <= 0 or core.height() <= 0:        # too thin for an edge all around: along the band only
            core = rect.adjusted(line, 0, -line, 0) if horizontal else rect.adjusted(0, line, 0, -line)
        painter.fillRect(core, accent if focused else self._GripCoreColor)

    def _paintPlane(self, painter: QPainter, rect: QRectF, *, edged: bool, crossed: bool = True) -> None:
        """Peint le plan dans un carré : la couleur de chaque point, puis la croix sur la couleur courante.

        Args:
            painter: Le peintre.
            rect: Le carré.
            edged: Vrai pour border la croix de sombre, lisible sur toute couleur ; faux pour
                une croix d'un seul pixel, qui cache le moins possible d'un petit carré.
            crossed: Faux pour le plan seul, sans croix.
        """
        if rect.isEmpty():
            return
        scale = self.devicePixelRatioF()
        line = max(1, round(self._Line * scale)) / scale
        painter.save()
        painter.setClipRect(rect)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawImage(rect, self.__planeImage(min(self._PlaneGrid, max(2, round(rect.width() * scale)))))
        if not crossed:
            painter.restore()
            return
        first, second = self.plane()
        x = round((rect.left() + self.__components[first] * (rect.width() - line)) * scale) / scale
        y = round((rect.bottom() - line - self.__components[second] * (rect.height() - line)) * scale) / scale
        strokes = ((line, self._GripEdgeColor), (0.0, self._GripCoreColor)) if edged else ((0.0, self._GripCoreColor),)
        for extra, color in strokes:
            painter.fillRect(QRectF(x - extra, rect.top(), line + 2 * extra, rect.height()), color)
            painter.fillRect(QRectF(rect.left(), y - extra, rect.width(), line + 2 * extra), color)
        painter.restore()

    def _planeValuesAt(self, rect: QRectF, point: QPoint) -> tuple[float, float]:
        """Les valeurs des deux canaux du plan qu'un point désigne dans son carré, sans les borner."""
        if rect.width() <= 1 or rect.height() <= 1:
            return 0.0, 0.0
        # From the first pixel to the last one: both ends of each channel can be reached inside the square.
        return ((point.x() - rect.left()) / (rect.width() - 1),
                (rect.bottom() - 1 - point.y()) / (rect.height() - 1))

    # ================================================================== private

    def __repaint(self) -> None:
        self.update()
        if self.__popup is not None and self.__popup.isVisible():
            self.__popup.update()
        self.__writeFields()

    def __relayout(self) -> None:
        self.__currentChannel = min(self.__currentChannel, self.channelCount() - 1)
        self.updateGeometry()
        self.__repaint()
        if self.__popup is not None:
            self.__popup.relayout()
        self.__placeTextFields(rewrite=True)

    # -- Text zone ---------------------------------------------------------------

    def __placeTextFields(self, rewrite: bool = False) -> None:
        """Lays the two fields in the text zone, made at need; gone with it, what was typed is retained.

        The values on the left at their widest, the code on the right if it brings anything
        and fits; between them, the background of the zone.
        """
        if self.__flyout is not None:                   # upright, the fields live in the flyout
            if self.__orientation == Qt.Orientation.Horizontal or not self.__expanded:
                self.__flyout.hide()                    # what was typed is retained as it closes
            elif rewrite:
                self.__layFields(self.__flyout.contentsRect())
                self.__writeFields(force=True)
            return
        zone = self._geometry()[0].get(QColorEdit._Part.Text)
        if zone is None:
            self.__dropTextFields()
            return
        if self.__channelsField is None or self.__codeField is None:
            self.__channelsField = self.__makeField(QColorEdit._ChannelsValidator, self.__readChannels, self)
            self.__codeField = self.__makeField(QColorEdit._CodeValidator, self.__readCode, self)
            rewrite = True
        self.__layFields(zone.toAlignedRect())
        if rewrite:
            self.__freeEntry = False
            self.__writeFields(force=True)

    def __fieldWidths(self) -> tuple[int, int]:
        """The widths of the values' field at its widest, and of the code's field."""
        metrics = QFontMetrics(self.font())
        room = 3 * metrics.averageCharWidth()           # the margins of a frameless line edit, and some air
        return (metrics.horizontalAdvance(self._fieldTemplate()) + room,
                metrics.horizontalAdvance("#" + "D" * (8 if self.__alphaShown() else 6)) + room)

    def __layFields(self, area: QRect) -> None:
        """The values on the left at their widest, the code on the right if it brings anything and fits."""
        channelsField, codeField = self.__channelsField, self.__codeField
        if channelsField is None or codeField is None:
            return
        channels, code = self.__fieldWidths()
        channelsField.setGeometry(area.left(), area.top(), min(channels, area.width()), area.height())
        shown = self._hasCode() and channels + code <= area.width()
        codeField.setVisible(shown)
        if shown:
            codeField.setGeometry(area.right() + 1 - code, area.top(), code, area.height())

    def __openFlyout(self) -> None:
        """Upright: the two fields in a flyout beside the text's handle, the first value selected."""
        if self.__flyout is not None:
            return
        self.__dropTextFields()
        flyout = QColorEdit._TextFlyout(self)
        self.__flyout = flyout
        self.__channelsField = self.__makeField(QColorEdit._ChannelsValidator, self.__readChannels, flyout)
        self.__codeField = self.__makeField(QColorEdit._CodeValidator, self.__readCode, flyout)
        channels, code = self.__fieldWidths()
        frame = self._Line
        width = channels + (code if self._hasCode() else 0) + 2 * frame
        height = self.__baseThickness()
        flyout.resize(width, height)
        flyout.setContentsMargins(frame, frame, frame, frame)
        self.__layFields(flyout.contentsRect())
        self.__freeEntry = False
        self.__writeFields(force=True)
        # Beside the widget, level with the handle; on the other side if the screen ends.
        handle = self._geometry()[0][QColorEdit._Part.TextHandle].toAlignedRect()
        screen = self.screen().availableGeometry()
        right = self.mapToGlobal(QPoint(self.width() + self._Line, handle.center().y() - height // 2))
        left = self.mapToGlobal(QPoint(-width - self._Line, handle.center().y() - height // 2))
        position = right if right.x() + width <= screen.right() else left
        flyout.move(max(screen.left(), position.x()), max(screen.top(), min(position.y(), screen.bottom() - height)))
        flyout.show()
        self.__channelsField.setFocus(Qt.FocusReason.PopupFocusReason)
        self.__selectSection(self.__channelsField, 0)

    def _closeTextFlyout(self) -> None:
        """Le volet flottant se ferme : ce qu'il montrait est retenu, ses champs partent avec lui."""
        flyout, self.__flyout = self.__flyout, None
        if flyout is None:
            return
        if self.__channelsField is not None:
            self.__acceptText()
        for field in (self.__channelsField, self.__codeField):
            if field is not None:
                field.removeEventFilter(self)
        self.__channelsField = self.__codeField = None
        self.__typedFrom = None
        flyout.deleteLater()

    def __makeField(self, validator: type[QValidator], read: Callable[[str], None], parent: QWidget) -> QLineEdit:
        field = QLineEdit(parent)
        field.setFrame(False)
        field.setToolTip(self.__fieldToolTip(validator is QColorEdit._ChannelsValidator))
        field.setValidator(validator(field))
        field.installEventFilter(self)
        field.textEdited.connect(read)
        field.show()
        return field

    def __dropTextFields(self) -> None:
        """Closes the fields; one that had the focus gives it back to the editor, what it showed retained."""
        fields = [field for field in (self.__channelsField, self.__codeField) if field is not None]
        if not fields:
            return
        hadFocus = any(field.hasFocus() for field in fields)
        if hadFocus:
            self.__acceptText()
        self.__channelsField = self.__codeField = None
        self.__typedFrom = None
        for field in fields:
            field.removeEventFilter(self)
            field.hide()
            field.setParent(None)           # at once: deleteLater alone would leave it found until the event loop
            field.deleteLater()
        if hadFocus:
            self.setFocus()

    def __writeFields(self, force: bool = False) -> None:
        """Writes the colour in the fields; a field being typed in keeps its text, unless forced."""
        for field, text in ((self.__channelsField, self._fieldText()), (self.__codeField, self._codeText())):
            if field is None or (not force and field.hasFocus() and field.isModified()):
                continue
            if field.text() != text:
                cursor = field.cursorPosition()
                field.setText(text)
                field.setCursorPosition(min(cursor, len(text)))

    def __acceptText(self) -> None:
        """Retains what the fields show: the values read in free entry, or the colour shown."""
        field = self.__channelsField
        if field is not None and self.__freeEntry:
            self.__freeEntry = False
            self._applyText(field.text())
        else:
            self._commit()
        self.__writeFields(force=True)

    @Slot()
    def __leaveText(self) -> None:
        """The focus has left a field: if it left the text zone too, what was typed is retained."""
        focus = QApplication.focusWidget()
        if focus is not None and focus in (self.__channelsField, self.__codeField):
            return
        if self.__channelsField is not None:
            self.__acceptText()
        self.__typedFrom = None

    @Slot(str)
    def __readChannels(self, text: str) -> None:
        if self.__freeEntry:
            return
        values = self._fieldValues(text)
        if values is not None:
            self._setChannels(dict(enumerate(values)), commit=False)

    @Slot(str)
    def __readCode(self, text: str) -> None:
        if len(text) - 1 in (6, 8):
            self._previewColor(QColor(text))

    def __typeKey(self, field: QLineEdit, event: QKeyEvent) -> bool:
        """The keys of a field of the text zone; true when handled here, false to let the field type."""
        key = event.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.__acceptText()
            self.__typedFrom = self._colorState()
            if self.__flyout is not None:               # a flyout is done with
                self.__flyout.hide()
        elif key == Qt.Key.Key_Escape:
            if self.__typedFrom is not None:
                self._setColorState(self.__typedFrom)
            self.__freeEntry = False
            self.__writeFields(force=True)
            if self.__flyout is not None:
                self.__flyout.hide()
        elif event.matches(QKeySequence.StandardKey.Copy):
            QApplication.clipboard().setText(self._colorText())
        elif event.matches(QKeySequence.StandardKey.Paste):
            if self._applyText(QApplication.clipboard().text()):
                self.__freeEntry = False
                self.__writeFields(force=True)
        elif key in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab) and self.__codeField is not None \
                and not self.__codeField.isHidden() and self.__channelsField is not None \
                and (field is self.__channelsField) == (key == Qt.Key.Key_Tab and not event.modifiers()
                                                        & Qt.KeyboardModifier.ShiftModifier):
            # From the values to the code with Tab, and back with Shift+Tab; beyond, the usual focus chain.
            if field is self.__channelsField:
                self.__codeField.setFocus(Qt.FocusReason.TabFocusReason)
                self.__codeField.selectAll()
            else:
                self.__channelsField.setFocus(Qt.FocusReason.BacktabFocusReason)
                self.__selectSection(self.__channelsField, 0)
        elif field is not self.__channelsField or self.__freeEntry:
            return False
        elif key == Qt.Key.Key_Comma:                   # to the next number, selected, as QDateTimeEdit
            self.__selectSection(field, self.__sectionAt(field) + 1)
        elif key in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            rank = self.__sectionAt(field)
            steps = (1 if key == Qt.Key.Key_Up else -1) * (self._PageSteps if event.modifiers()
                                                           & Qt.KeyboardModifier.ShiftModifier else 1)
            self._setChannels({rank: self.channelValues()[rank] + steps * self._step(rank)}, commit=False)
            self.__writeFields(force=True)
            self.__selectSection(field, rank)
        else:
            if event.text().isprintable() and event.text() and field.hasSelectedText() \
                    and field.selectedText() == field.text():
                self.__freeEntry = True                 # all the text replaced: free entry, read at Enter
            return False
        return True

    def __sectionAt(self, field: QLineEdit) -> int:
        """The rank of the number under the text cursor of the values' field."""
        spans = self._fieldSpans(field.text()) or []
        cursor = field.cursorPosition()
        return next((rank for rank, (_, end) in enumerate(spans) if cursor <= end), max(0, len(spans) - 1))

    def __selectSection(self, field: QLineEdit, rank: int) -> None:
        spans = self._fieldSpans(field.text())
        if not spans:
            return
        start, end = spans[max(0, min(len(spans) - 1, rank))]
        field.setSelection(start, end - start)

    def __alphaShown(self) -> bool:
        return self.__useAlpha and self.__alphaVisible

    def __hue(self) -> float | None:
        """The hue on display, if the current space has one."""
        return self.__components[0] if self.__colorSpace in self._HueChannels else None

    def __checkChannel(self, channel: int) -> None:
        if isinstance(channel, bool) or not isinstance(channel, int) or not 0 <= channel < self.channelCount(): # pyright: ignore[reportUnnecessaryIsInstance]
            raise IndexError(f"No band has the rank {channel!r} (there are {self.channelCount()}).")

    def _step(self, channel: int) -> float:
        """Le pas d'un canal : une unité de la notation entière, ou un centième en notation réelle."""
        if self.__valueNotation == QColorEdit.ValueNotation.Real:
            return self._RealStep
        return 1 / (self._HueTurn if self.__isHue(channel) else self._ByteMax)

    def __isHue(self, channel: int) -> bool:
        return channel == 0 and self.__colorSpace in self._HueChannels

    def __nextColorSpace(self) -> ColorSpace:
        spaces = list(QColorEdit.ColorSpace)
        start = spaces.index(self.__colorSpace)
        return next(space for space in spaces[start + 1:] + spaces[:start + 1] if space in self.__available)

    def __mirrored(self) -> bool:
        """Whether the parts follow one another from right to left."""
        return self.__orientation == Qt.Orientation.Horizontal and self.isRightToLeft()

    def __reversed(self) -> bool:
        """Whether a value grows leftwards, or downwards, as in QSlider."""
        if self.__orientation == Qt.Orientation.Horizontal:
            return self.__invertedAppearance != self.isRightToLeft()
        return self.__invertedAppearance

    def __textAlong(self) -> bool:
        """Whether the texts run along the widget rather than across it."""
        Direction = QColorEdit.TextDirection
        if self.__textDirection == Direction.Horizontal:
            return self.__orientation == Qt.Orientation.Horizontal
        return self.__textDirection == Direction.Aligned

    def __textTurned(self) -> bool:
        """Whether the texts are drawn turned a quarter, that is, read from bottom to top."""
        return self.__textAlong() != (self.__orientation == Qt.Orientation.Horizontal)

    def __click(self, part: _Part) -> None:
        Part = QColorEdit._Part
        if part == Part.Swatch and self.__dialogEnabled:
            self._chooseColor()
        elif part == Part.ExpandToggle:
            self.setExpanded(not self.__expanded)
        elif part == Part.AlphaToggle:
            self.setAlphaVisible(not self.__alphaVisible)
        elif part == Part.SpaceLabel and len(self.__available) > 1:
            self.setColorSpace(self.__nextColorSpace())
        elif part == Part.NotationToggle:
            self.setValueNotation(self.__nextNotation())
        elif part == Part.PlaneToggle:
            self.setPlaneVisible(not self.__planeVisible)
        elif part == Part.Plane:
            self.showPlanePopup()

    def __dragTo(self, point: QPoint, globalPoint: QPoint) -> None:
        channel = self.__draggedChannel
        horizontal = self.__orientation == Qt.Orientation.Horizontal
        shift = QPoint(round(self.__dragOffset), 0) if horizontal else QPoint(0, round(self.__dragOffset))
        self._setChannels({channel: self.__valueAt(channel, point - shift)}, commit=self.__tracking)
        QToolTip.showText(globalPoint, f"{self._channelLetter(channel)} {self._valueText(channel)}", self)

    def __shownLength(self, handle: _Part) -> int:
        """The length on display of what a handle sets: the swatch, or the text zone (0 when closed)."""
        Part = QColorEdit._Part
        parts = self._geometry()[0]
        rect = parts.get(Part.Swatch if handle == Part.SwatchHandle else Part.Text)
        if rect is None:
            return 0
        return round(rect.width() if self.__orientation == Qt.Orientation.Horizontal else rect.height())

    def __alongOf(self, point: QPoint) -> int:
        """A point's coordinate along the widget, growing away from the swatch (rightward, or leftward when mirrored)."""
        if self.__orientation == Qt.Orientation.Vertical:
            return point.y()
        return -point.x() if self.__mirrored() else point.x()

    def __valueAt(self, channel: int, point: QPoint) -> float:
        """The value a point designates in a channel's band, unbounded."""
        horizontal = self.__orientation == Qt.Orientation.Horizontal
        return self._bandValueAt(self._geometry()[1][channel], horizontal, self.__reversed(), self._gripLength(), point)

    def __gripOffset(self, channel: int, point: QPoint) -> float | None:
        """How far a point lies from the centre of a channel's grip, along the band; None off the grip."""
        horizontal = self.__orientation == Qt.Orientation.Horizontal
        grip = self._gripLength()
        start, stop = self._bandAxis(self._geometry()[1][channel], horizontal, self.__reversed(), grip)
        centre = start + (stop - start) * self.channelValues()[channel]
        offset = point.x() - centre.x() if horizontal else point.y() - centre.y()
        return offset if abs(offset) <= grip / 2 else None

    @Slot()
    def __stepPage(self) -> None:
        """One page of the paged channel toward its target; the repeat stops there, under the pointer."""
        channel = self.__pagedChannel
        if channel < 0:
            self.__pageTimer.stop()
            return
        self.__pageTimer.setInterval(self._RepeatInterval)         # the first repeat waits longer, as QAbstractSlider
        value, target = self.channelValues()[channel], max(0.0, min(1.0, self.__pageTarget))
        page = self._PageSteps * self._step(channel)
        if abs(target - value) < 1e-9:
            return
        value = min(value + page, target) if target > value else max(value - page, target)
        self._setChannels({channel: value}, commit=self.__tracking)

    def __planeImage(self, cells: int) -> QImage:
        """The colours of the plane on a grid of `cells` points a side, kept until a fixed channel moves."""
        first, second = self.plane()
        fixed = tuple(value for rank, value in enumerate(self.__components) if rank not in (first, second))
        key = (self.__colorSpace, first, second, fixed, cells)
        if self.__planeCache is not None and self.__planeCache[0] == key:
            return self.__planeCache[1]
        image = QImage(cells, cells, QImage.Format.Format_RGB32)
        components = list(self.__components)
        for row in range(cells):
            components[second] = 1 - row / (cells - 1)
            for column in range(cells):
                components[first] = column / (cells - 1)
                image.setPixel(column, row, _colorFrom(self.__colorSpace, components, 1.0).rgb())
        self.__planeCache = (key, image)
        return image

    # -- Texts -------------------------------------------------------------------

    def __notationScope(self, notation: ValueNotation) -> str:
        if notation == QColorEdit.ValueNotation.Integer:
            return self.tr("Integers") + f"  0–{self._ByteMax} · H 0–{self._HueTurn - 1}"
        if notation == QColorEdit.ValueNotation.Hexadecimal:
            return self.tr("Hexadecimal") + f"  00–{self._ByteMax:02X} · H 000–{self._HueTurn - 1:03X}"
        return self.tr("Reals") + "  0.0–1.0"

    def __nextNotation(self) -> ValueNotation:
        """The notation the toggle passes to: Integer, Real, Hexadecimal, and round again."""
        notations = list(QColorEdit.ValueNotation)
        return notations[(notations.index(self.__valueNotation) + 1) % len(notations)]

    def __wholeValue(self, channel: int, value: float) -> int:
        """A value of [0, 1] as the integer of QColor: 0 to 255, or 0 to 359 for a hue."""
        if self.__isHue(channel):
            return min(self._HueTurn - 1, round(value * self._HueTurn))
        return round(value * self._ByteMax)

    def __widest(self, channel: int) -> str:
        """The widest text a channel may take in the current notation."""
        Notation = QColorEdit.ValueNotation
        if self.__valueNotation == Notation.Real:
            return "0.000"
        top = self._HueTurn - 1 if self.__isHue(channel) else self._ByteMax
        return f"{top:X}" if self.__valueNotation == Notation.Hexadecimal else str(top)

    def __cellTexts(self, part: _Part) -> list[str]:
        """Every text a cell may ever carry: its size is set on the longest, once and for all."""
        if part == QColorEdit._Part.SpaceLabel:
            return list(self._SpaceNames.values())
        return []

    def _colorText(self) -> str:
        """La couleur écrite dans l'espace et la notation courants : `RGB = (230, 120, 40)`.

        L'alpha y figure quand sa bande est affichée : `RGBA = (230, 120, 40, 200)`.
        """
        return f"{self._channelLetters()} = ({', '.join(self._valueText(rank) for rank in range(self.channelCount()))})"

    def _colorTemplate(self) -> str:
        """`_colorText` à sa plus grande largeur : chaque valeur à son maximum de chiffres."""
        return f"{self._channelLetters()} = ({', '.join(self.__widest(rank) for rank in range(self.channelCount()))})"

    def _channelLetters(self) -> str:
        """Les lettres des bandes affichées, à la suite : le nom de l'espace, puis `A` si la bande de l'alpha l'est."""
        return self._SpaceNames[self.__colorSpace] + (self._AlphaLetter if self.__alphaShown() else "")

    def _colorMask(self) -> str:
        """Le patron de saisie de `_colorText`, pour `QLineEdit.setInputMask`.

        Un entier a un à trois chiffres ; un réel s'écrit `0.000` ; un nombre hexadécimal a un
        ou deux chiffres, trois pour la teinte, mis en capitales. Les lettres du nom sont
        protégées : plusieurs ont un sens dans un patron.
        """
        Notation = QColorEdit.ValueNotation

        def group(channel: int) -> str:
            if self.__valueNotation == Notation.Real:
                return "9.999"
            if self.__valueNotation == Notation.Hexadecimal:
                return "Hhh" if self.__isHue(channel) else "Hh"
            return "900"

        name = "".join("\\" + letter for letter in self._channelLetters())
        upper = ">" if self.__valueNotation == Notation.Hexadecimal else ""
        return f"{upper}{name} = ({', '.join(group(rank) for rank in range(self.channelCount()))});_"

    # -- Text zone -------------------------------------------------------------

    def _fieldText(self) -> str:
        """Les valeurs des bandes affichées, pour le champ des valeurs : `(230, 120, 40)`."""
        return f"({', '.join(self._valueText(rank) for rank in range(self.channelCount()))})"

    def _fieldTemplate(self) -> str:
        """`_fieldText` à sa plus grande largeur : chaque valeur à son maximum de chiffres."""
        return f"({', '.join(self.__widest(rank) for rank in range(self.channelCount()))})"

    def _fieldPattern(self) -> str:
        """L'expression régulière du champ des valeurs : les parenthèses, les virgules, et un nombre par bande, peut-être vide.

        Chaque nombre est capturé ; il a au plus les chiffres de sa notation (trois, deux en
        hexadécimal hors de la teinte, trois décimales pour un réel).
        """
        Notation = QColorEdit.ValueNotation
        numbers: list[str] = []
        for rank in range(self.channelCount()):
            if self.__valueNotation == Notation.Real:
                numbers.append(r"(\d?(?:\.\d{0,3})?)")
            elif self.__valueNotation == Notation.Hexadecimal:
                numbers.append(r"([0-9A-F]{0,%d})" % (3 if self.__isHue(rank) else 2))
            else:
                numbers.append(r"(\d{0,3})")
        return r"\(\s*" + r"\s*,\s*".join(numbers) + r"\s*\)"

    def _fieldSpans(self, text: str) -> list[tuple[int, int]] | None:
        """Où est chaque nombre dans un texte du champ des valeurs : son début et sa fin ; None hors du patron."""
        match = re.fullmatch(self._fieldPattern(), text)
        if match is None:
            return None
        return [match.span(rank + 1) for rank in range(self.channelCount())]

    def _fieldValues(self, text: str) -> list[float] | None:
        """Les valeurs qu'écrit un texte du champ des valeurs, chacune ramenée dans [0, 1].

        Retourne:
            None si le texte sort du patron ou si un nombre manque encore.
        """
        Notation = QColorEdit.ValueNotation
        match = re.fullmatch(self._fieldPattern(), text)
        if match is None:
            return None
        values: list[float] = []
        for rank, piece in enumerate(match.groups()):
            if piece in ("", "."):
                return None
            if self.__valueNotation == Notation.Real:
                value = float(piece)
            else:
                whole = int(piece, 16 if self.__valueNotation == Notation.Hexadecimal else 10)
                value = whole / (self._HueTurn if self.__isHue(rank) else self._ByteMax)
            values.append(max(0.0, min(1.0, value)))
        return values

    def _validateField(self, text: str, position: int) -> tuple[QValidator.State, str, int]:
        """Valide une frappe dans le champ des valeurs, comme `QValidator.validate`.

        Le patron est protégé : une frappe qui toucherait aux parenthèses ou aux virgules est
        refusée. Un nombre qui manque encore laisse le texte intermédiaire. En saisie libre,
        tout est accepté, et lu à Entrée. L'hexadécimal passe en capitales.
        """
        State = QValidator.State
        if self.__freeEntry:
            return State.Intermediate, text, position
        if self.__valueNotation == QColorEdit.ValueNotation.Hexadecimal:
            text = text.upper()
        spans = self._fieldSpans(text)
        if spans is None:
            return State.Invalid, text, position
        return (State.Acceptable if self._fieldValues(text) is not None else State.Intermediate), text, position

    def _codeText(self) -> str:
        """Le code de la couleur montrée : `#RRGGBB`, ou `#AARRGGBB` (l'ordre de Qt) si la bande de l'alpha est affichée."""
        color = self._shownColor()
        return color.name(QColor.NameFormat.HexArgb if self.__alphaShown() else QColor.NameFormat.HexRgb).upper()

    def _validateCode(self, text: str, position: int) -> tuple[QValidator.State, str, int]:
        """Valide une frappe dans le champ du code : `#`, puis six chiffres hexadécimaux, ou huit avec l'alpha, en capitales."""
        State = QValidator.State
        text = text.upper()
        if re.fullmatch(r"#[0-9A-F]{0,8}", text) is None:
            return State.Invalid, text, position
        return (State.Acceptable if len(text) - 1 in (6, 8) else State.Intermediate), text, position

    def _hasCode(self) -> bool:
        """Indique si le champ de saisie offre le code : sauf en RGB hexadécimal, où il redirait les canaux."""
        return not (self.__colorSpace == QColorEdit.ColorSpace.Rgb
                    and self.__valueNotation == QColorEdit.ValueNotation.Hexadecimal)

    def _colorState(self) -> _QColorState:
        """La couleur retenue et les canaux montrés, pour les rétablir plus tard (`_setColorState`)."""
        return QColor(self.__color), list(self.__components), self.__alpha

    def _setColorState(self, state: _QColorState) -> None:
        """Rétablit une couleur et des canaux ; annonce la couleur si elle change."""
        color, components, alpha = state
        changed = not _sameColor(color, self.__color)
        self.__color, self.__components, self.__alpha = QColor(color), list(components), alpha
        self.__repaint()
        if changed:
            self.colorChanged.emit(self.color())

    def _previewColor(self, color: QColor) -> None:
        """Montre une couleur dans les canaux, sans la retenir ; son alpha compte si la bande de l'alpha est affichée."""
        self.__components = _componentsOf(color, self.__colorSpace, self.__components, self.__hue())
        if self.__alphaShown():
            self.__alpha = color.alphaF()
        self.__repaint()

    def _applyText(self, text: str) -> bool:
        """Retient la couleur qu'un texte écrit, s'il en écrit une.

        Lu : `RGB = (230, 120, 40)`, des nombres seuls (`230, 120, 40` ou `230 120 40`), ou
        un code `#RRGGBB`. Un nom d'espace en tête est respecté, sans changer l'espace
        affiché ; sans nom, c'est l'espace courant. Les nombres sont lus dans la notation
        courante, sans rien deviner, et ramenés dans leur étendue. Un nombre de plus que de
        canaux est l'alpha ; sans lui, l'alpha ne change pas.

        Retourne:
            Faux si le texte n'écrit aucune couleur ; rien ne change alors.
        """
        text = text.strip()
        if text.startswith("#"):
            color = QColor(text)
            if color.isValid():
                self.setColor(color)
            return color.isValid()
        space = self.__colorSpace
        named = re.match(r"([A-Za-z]+)\s*=", text)
        if named is not None:
            spaces = {name: candidate for candidate, name in self._SpaceNames.items()}
            name = named.group(1).upper()
            name = name if name in spaces else name.removesuffix(self._AlphaLetter)
            if name not in spaces:
                return False
            space, text = spaces[name], text[named.end():]
        if self.__valueNotation == QColorEdit.ValueNotation.Hexadecimal:
            numbers = [float(int(number, 16)) for number in re.findall(r"[0-9A-Fa-f]+", text)]
        else:
            numbers = [float(number) for number in re.findall(r"\d+\.?\d*|\.\d+", text)]
        count = len(self._SpaceNames[space])
        if len(numbers) not in (count, count + 1):
            return False
        real = self.__valueNotation == QColorEdit.ValueNotation.Real
        hue = space in self._HueChannels
        values = [min(1.0, number if real else number / (self._HueTurn if hue and rank == 0 else self._ByteMax))
                  for rank, number in enumerate(numbers)]
        if space == self.__colorSpace:
            self._setChannels({rank if rank < count else len(self.__components): value for rank, value in enumerate(values)},
                              commit=True)
        else:
            self.setColor(_colorFrom(space, values[:count], values[count] if len(values) > count else self.__alpha))
        return True

    def _valuesLine(self) -> str:
        """Chaque canal avec sa valeur, l'alpha compris s'il est en usage : `R 230  G 120  B 40  A 200`."""
        count = len(self.__components)
        pairs = [f"{self._channelLetter(rank)} {self._valueText(rank)}" for rank in range(count + int(self.__useAlpha))]
        return "  ".join(pairs)

    def __swatchToolTip(self) -> str:
        color = self._shownColor()
        name = color.name(QColor.NameFormat.HexArgb if self.__useAlpha else QColor.NameFormat.HexRgb).upper()
        action = self.tr("Click · Space: colour dialog") if self.__dialogEnabled else self.tr("Colour dialog: off")
        return f"{name}\n{self._valuesLine()}\n\n{action}"

    def __expandToolTip(self) -> str:
        if self.__expanded:
            return self.tr("Channels: shown") + "\n\n" + self.tr("Click: fold")
        return self.tr("Channels: folded") + "\n\n" + self.tr("Click: show")

    def __alphaToolTip(self) -> str:
        value = f"{self._AlphaLetter} {self._valueText(len(self.__components))}"
        if self.__alphaVisible:
            return self.tr("Alpha band: shown") + f"\n{value}\n\n" + self.tr("Click: hide")
        return self.tr("Alpha band: hidden") + f"\n{value}\n\n" + self.tr("Click: show")

    def __spaceToolTip(self) -> str:
        offered = self.availableColorSpaces()
        name = self._SpaceNames[self.__colorSpace]
        if len(offered) < 2:
            return f"{name}\n\n" + self.tr("Only space available")
        return (f"{name}\n\n" + self.tr("Click: {0}").format(self._SpaceNames[self.__nextColorSpace()]) + "\n"
                + self.tr("Available: {0}").format(" · ".join(self._SpaceNames[space] for space in offered)))

    def __notationToolTip(self) -> str:
        return (self.__notationScope(self.__valueNotation) + "\n\n"
                + self.tr("Click: {0}").format(self.__notationScope(self.__nextNotation())))

    def __planeToggleToolTip(self) -> str:
        name = self._planeName(self.plane())
        if self.__planeVisible:
            return self.tr("Plane {0}: shown").format(name) + "\n\n" + self.tr("Click: hide")
        return self.tr("Plane {0}: hidden").format(name) + "\n\n" + self.tr("Click: show")

    # -- Geometry ----------------------------------------------------------------

    def __frameOption(self) -> QStyleOptionFrame:
        """The style option of a framed panel on this widget's rectangle; it also measures a QLineEdit's height."""
        option = QStyleOptionFrame()
        option.initFrom(self)
        option.lineWidth = self.style().pixelMetric(QStyle.PixelMetric.PM_DefaultFrameWidth, option, self)
        option.midLineWidth = 0
        option.frameShape = QFrame.Shape.StyledPanel
        option.state |= QStyle.StateFlag.State_Sunken
        option.state &= ~QStyle.StateFlag.State_HasFocus      # the style's focus rectangle shows it, inside the frame
        return option

    def __frameWidth(self) -> int:
        return self.__frameOption().lineWidth if self.__frame else 0

    def __baseThickness(self) -> int:
        """The height of a QLineEdit of the current style, for this widget's font."""
        self.ensurePolished()
        option = self.__frameOption()
        metrics = self.fontMetrics()
        iconSize = self.style().pixelMetric(QStyle.PixelMetric.PM_SmallIconSize, None, self)
        content = (max(metrics.height(), self._LineEditMinimumTextHeight, iconSize - 2)
                   + 2 * self._LineEditVerticalMargin)
        return self.style().sizeFromContents(QStyle.ContentsType.CT_LineEdit, option, QSize(0, content), self).height()

    def __thickness(self) -> int:
        base = self.__baseThickness()
        return base + (round(base / self._AlphaGrowth) if self.__alphaShown() else 0)

    def __automaticSwatchLength(self) -> int:
        """Roughly square: a line edit's height, and a button's margin."""
        return self.__baseThickness() + self.style().pixelMetric(QStyle.PixelMetric.PM_ButtonMargin, None, self)

    def __handleLength(self) -> int:
        """The length of a handle along the widget: narrow, a quarter of a line edit's height, five pixels at least."""
        return max(self._HandleLeast, round(self.__baseThickness() / self._HandleFraction))

    def __paintHandle(self, painter: QPainter, rect: QRectF, part: _Part) -> None:
        """A handle: the cell of a toggle, with three dots in a row across the widget, as a splitter's grip."""
        dragged = self.__handleDrag is not None and self.__handleDrag[0] == part
        self._paintCell(painter, rect, hovered=part == self.__hoverPart, pressed=dragged)
        scale = self.devicePixelRatioF()
        dot = max(2, round(self._HandleDot * scale)) / scale
        horizontal = self.__orientation == Qt.Orientation.Horizontal
        color = QColor(self.palette().color(QPalette.ColorRole.ButtonText))
        color.setAlphaF(self._HandleDotOpacity)
        centre = rect.center()
        for rank in (-1, 0, 1):
            offset = rank * 2.5 * dot
            x = round((centre.x() - dot / 2 + (0 if horizontal else offset)) * scale) / scale
            y = round((centre.y() - dot / 2 + (offset if horizontal else 0)) * scale) / scale
            painter.fillRect(QRectF(x, y, dot, dot), color)

    def __cellLength(self, part: _Part) -> int:
        """The length of a toggle or of a label along the widget; it never depends on the state."""
        Part = QColorEdit._Part
        along = self.__textAlong()
        metrics = QFontMetrics(self._textFont(along))
        lower = QFontMetrics(self._textFont(along, True))
        texts = self.__cellTexts(part)
        if part == Part.NotationToggle:     # its pictogram, with some air around
            return math.ceil(self._notationSide()) + metrics.averageCharWidth() + 2 * self._Line
        if part == Part.Eyedropper:         # as the section of QColorBox, whatever the texts
            return round(self._SectionRatio * self.__baseThickness())
        if not texts:                       # an arrow: a square of the height of a capital
            return metrics.ascent() + 2 * self._Line
        if not along:                       # across: one line of text, or the two of the space label
            return metrics.height() + (lower.height() if part == Part.SpaceLabel else 0) + 2 * self._Line
        widest = max(metrics.horizontalAdvance(text) for text in texts)
        if part == Part.SpaceLabel:
            widest = max(widest, lower.horizontalAdvance(self.tr("alpha")))
        return widest + metrics.averageCharWidth() + 2 * self._Line

    def __cells(self) -> list[_Part]:
        """The toggles and the label on offer next to the swatch, in order, were the bands deployed."""
        Part = QColorEdit._Part
        offered = ((Part.Eyedropper, self.__eyedropperButton == EyedropperButton.Section),
                   (Part.ExpandToggle, self.__expandToggleVisible),
                   (Part.AlphaToggle, self.__alphaToggleVisible and self.__useAlpha),
                   (Part.SpaceLabel, self.__colorSpaceLabelVisible),
                   (Part.NotationToggle, self.__notationToggleVisible))
        return [part for part, visible in offered if visible]

    def __hint(self, bandLength: int) -> QSize:
        """The size of the widget for bands of a given length, whether it is folded or not.

        The handles count, the swatch at its automatic length; what the handles give the swatch
        or the text zone is taken from the bands, so the widget keeps its size.
        """
        Part = QColorEdit._Part
        line, edge = self._Line, self.__frameWidth()
        along = 2 * edge + self.__automaticSwatchLength() + line + bandLength
        handles = int(self.__swatchHandleVisible) + int(self.__textHandleVisible)
        along += handles * (self.__handleLength() + line)              # the swatch's handle and the text's
        along += sum(self.__cellLength(part) + line for part in self.__cells())
        if self.__planeToggleVisible:
            along += line + self.__cellLength(Part.PlaneToggle)
        if self.__planeVisible:
            along += line + self.__thickness() - 2 * edge
        size = QSize(along, self.__thickness())
        if self.__orientation == Qt.Orientation.Vertical:
            size.transpose()
        return size

    def __contentRect(self) -> QRectF:
        """What the frame leaves, snapped to the pixels of the screen."""
        scale = self.devicePixelRatioF()
        edge = round(self.__frameWidth() * scale)
        return QRectF(edge / scale, edge / scale, (round(self.width() * scale) - 2 * edge) / scale,
                      (round(self.height() * scale) - 2 * edge) / scale)

    def __partAt(self, point: QPoint) -> _Part:
        Part = QColorEdit._Part
        parts = self._geometry()[0]
        corner = self.__eyedropperButton == EyedropperButton.Corner
        if corner and Part.Eyedropper in parts and self.__inCorner(parts[Part.Eyedropper], QPointF(point)):
            return Part.Eyedropper
        for part, rect in parts.items():
            if not (corner and part == Part.Eyedropper) and rect.contains(QPointF(point)):
                return part
        return Part.NoPart

    # -- Eyedropper ----------------------------------------------------------------

    def __cornerAtLeft(self) -> bool:
        """Whether the corner's right angle is at the bottom left: the swatch's far end, from right to left."""
        return self.__mirrored()

    def __inCorner(self, square: QRectF, point: QPointF) -> bool:
        """Whether a point lies in the corner: the half of its square beyond the diagonal, on the right angle's side."""
        if not square.contains(point):
            return False
        across = point.x() - square.left() if not self.__cornerAtLeft() else square.right() - point.x()
        return across + (point.y() - square.top()) >= square.width()

    def __paintCorner(self, painter: QPainter, square: QRectF) -> None:
        palette = self.palette()
        atLeft = self.__cornerAtLeft()
        right = square.bottomLeft() if atLeft else square.bottomRight()
        far = square.topLeft() if atLeft else square.topRight()
        near = square.bottomRight() if atLeft else square.bottomLeft()
        triangle = QPainterPath()
        triangle.moveTo(far)
        triangle.lineTo(right)
        triangle.lineTo(near)
        triangle.closeSubpath()
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillPath(triangle, palette.color(QPalette.ColorRole.Button))
        Part = QColorEdit._Part
        hovered = self.__hoverPart == Part.Eyedropper
        pressed = self.__pressedPart == Part.Eyedropper or self.__picking
        if self.isEnabled() and (hovered or pressed):
            tint = QColor(palette.color(QPalette.ColorRole.Highlight))
            tint.setAlphaF(0.45 if pressed else 0.25)
            painter.fillPath(triangle, tint)
        painter.setPen(QPen(palette.color(QPalette.ColorRole.Mid), max(1, round(self._Line * self.devicePixelRatioF()))
                            / self.devicePixelRatioF()))
        painter.drawLine(far, near)
        side = square.width() * self._IconRatio
        offset = square.width() * self._IconCentre
        centre = QPointF(square.right() - offset if atLeft else square.left() + offset, square.top() + offset)
        if atLeft:          # the pipette lies along the diagonal
            painter.translate(centre)
            painter.scale(-1, 1)
            painter.translate(-centre)
        QScreenColorPicker.paintIcon(painter, QRectF(centre.x() - side / 2, centre.y() - side / 2, side, side),
                                     palette.color(QPalette.ColorRole.ButtonText))
        painter.restore()

    @Slot(QColor)
    def __takeColor(self, picked: QColor) -> None:
        color = QColor(picked)
        color.setAlphaF(self.__alpha)
        self.setColor(color)

    @Slot(bool)
    def __showPicking(self, active: bool) -> None:
        self.__picking = active
        if not active:
            self.__eyedropperDragged = False
        self.update()

    def __eyedropperToolTip(self) -> str:
        return self.tr("Eyedropper: pick a colour on screen") + "\n\n" + self.tr("Click · Press, drag, release · I")

    def __fieldToolTip(self, values: bool) -> str:
        keys = self.tr("Enter: retain · Esc: undo · Ctrl+C Ctrl+V")
        if values:
            return (self.tr("Values") + "\n\n" + self.tr(", : next value · ↑ ↓ ±1 · Shift ±{0}").format(self._PageSteps)
                    + "\n" + self.tr("Select all, then type: free entry") + "\n" + keys)
        return self.tr("Code #RRGGBB, or #AARRGGBB with alpha (Qt's order)") + "\n\n" + keys

    def __swatchHandleToolTip(self) -> str:
        return self.tr("Swatch length") + "\n\n" + self.tr("Drag: resize · Double-click: automatic")

    def __textHandleToolTip(self) -> str:
        if self.__orientation == Qt.Orientation.Vertical:
            return self.tr("Values as text") + "\n\n" + self.tr("Click · F2: type them beside")
        if self.__textVisible:
            return self.tr("Values as text: shown") + "\n\n" + self.tr("Click: hide · Drag: width · F2: type")
        return self.tr("Values as text: hidden") + "\n\n" + self.tr("Click · Drag · F2: show and type")

    def __channelAt(self, point: QPoint) -> int:
        """The band under a point of the bands' area; a gap belongs to the nearest band."""
        horizontal = self.__orientation == Qt.Orientation.Horizontal
        across = point.y() if horizontal else point.x()
        bands = self._geometry()[1]

        def distance(rank: int) -> float:
            first, last = (bands[rank].top(), bands[rank].bottom()) if horizontal else (bands[rank].left(), bands[rank].right())
            return max(first - across, across - last, 0.0)

        return min(range(len(bands)), key=distance)

    # ==================================================================== popup

    class _PlanePopup(QWidget):
        """Fenêtre flottante du plan.

        En haut, un bouton qui nomme le plan, puis les lettres des canaux restés hors du
        plan. Au milieu, le plan en grand ; collée à sa droite, une bande verticale par canal
        restant ; collée dessous, la bande de l'alpha, à l'horizontale, si la barre l'affiche.
        Ces bandes ont la taille de celles de l'éditeur. En bas, un bouton écrit la couleur :
        un clic la copie, un double-clic la rend saisissable. La fenêtre ne garde aucun état
        de couleur : elle lit et règle tout par son éditeur.
        """

        Plane: Final[int] = -1      # what a point may be over, besides the rank of a band's channel
        Label: Final[int] = -2
        Values: Final[int] = -3

        def __init__(self, editor: QColorEdit) -> None:
            """Construit la fenêtre, enfant de son éditeur.

            Args:
                editor: L'éditeur dont elle montre et règle la couleur.
            """
            super().__init__(editor, Qt.WindowType.Popup)
            self.__dragged: int | None = None
            self.__pressed: int | None = None       # the button held down, `Label` or `Values`
            self.__hover: int | None = None
            self.__wheelRemainder: int = 0
            self.setMouseTracking(True)

        def _editor(self) -> QColorEdit:
            """L'éditeur, retrouvé par le lien de parenté de Qt.

            La fenêtre ne le retient pas dans un attribut : l'éditeur la retient déjà, et deux
            objets Qt qui se retiennent l'un l'autre ne sont détruits que par le ramasse-miettes
            cyclique, tard et dans un ordre quelconque.
            """
            return cast(QColorEdit, self.parentWidget())

        def relayout(self) -> None:
            """Reprend la taille que demandent l'éditeur et son espace de couleur ; une saisie en cours est abandonnée."""
            self.cancelEdit()
            _, _, _, _, values = self.layoutRects()
            line = self._editor()._Line
            self.setFixedSize(math.ceil(values.right()) + line, math.ceil(values.bottom()) + line)
            self.update()

        def layoutRects(self) -> tuple[QRectF, QRectF, list[tuple[int, QRectF, bool]], QRectF, QRectF]:
            """La place de chaque partie de la fenêtre.

            Retourne:
                Le bouton du plan ; le plan ; pour chaque bande, le rang de son canal, son
                rectangle, et vrai si elle court à l'horizontale ; la zone des lettres des
                bandes verticales ; le bouton des valeurs.
            """
            editor = self._editor()
            scale = self.devicePixelRatioF()
            line = editor._Line
            side = editor.planePopupSize()
            metrics = QFontMetrics(editor._textFont(True))
            row = metrics.height() + 4 * line
            thickness = editor._gripLength() / editor._GripRatio        # that of a band of the editor
            count = len(editor._SpaceNames[editor.colorSpace()])
            others = [rank for rank in range(count) if rank not in editor.plane()]
            plane = QRectF(line, line + row + line, side, side)
            # Glued to the plane and to one another, on whole pixels of the screen.
            bands = [(rank, QRectF(round((plane.right() + index * thickness) * scale) / scale, plane.top(), thickness, side),
                      False) for index, rank in enumerate(others)]
            right = bands[-1][1].right()
            bottom = plane.bottom()
            if editor.channelCount() > count:       # the alpha band of the bar is shown: here too, under the plane
                bands.append((count, QRectF(plane.left(), plane.bottom(), side, thickness), True))
                bottom += thickness
            letters = "".join(editor._channelLetter(rank) for rank in others)
            lettersWidth = max(right - plane.right(), metrics.horizontalAdvance(letters) + metrics.averageCharWidth())
            button = QRectF(line, line, right - lettersWidth - line, row)
            # Two lines when one does not hold the widest text: its size never depends on the values.
            lines = 1 if metrics.horizontalAdvance(editor._colorTemplate()) <= right - line - self.__iconZone() else 2
            return (button, plane, bands, QRectF(button.right(), line, lettersWidth, row),
                    QRectF(line, bottom + line, right - line, lines * metrics.height() + 4 * line))

        def targetAt(self, point: QPoint) -> int | None:
            """Ce qui se trouve sous un point : le rang d'un canal, `Plane`, `Label`, `Values`, ou None."""
            button, plane, bands, _, values = self.layoutRects()
            spot = QPointF(point)
            if button.contains(spot):
                return self.Label
            if values.contains(spot):
                return self.Values
            if plane.contains(spot):
                return self.Plane
            for rank, band, _ in bands:
                if band.contains(spot):
                    return rank
            return None

        def toolTipAt(self, point: QPoint) -> str:
            """Le texte de l'infobulle de ce qui se trouve sous un point."""
            editor = self._editor()
            target = self.targetAt(point)
            if target == self.Label:
                planes = editor.planes()
                rank = planes.index(editor.plane())
                return (editor.tr("Plane {0}").format(editor._planeName(editor.plane())) + "\n\n"
                        + editor.tr("Click: {0} · Right-click: {1}").format(
                            editor._planeName(planes[(rank + 1) % len(planes)]),
                            editor._planeName(planes[rank - 1])) + "\n"
                        + editor.tr("Planes: {0}").format(" · ".join(editor._planeName(plane) for plane in planes)))
            if target == self.Values:
                return (editor._colorText() + "\n\n" + editor.tr("Click: copy · Double-click: type the values") + "\n"
                        + editor.tr("Ctrl+C: copy · Ctrl+V: paste"))
            if target == self.Plane:
                return editor._planeToolTip(editor.tr("Drag: set both") + "\n"
                                            + editor.tr("← → ↑ ↓ ±1 · Shift ±{0}").format(editor._PageSteps))
            if target is not None:
                horizontal = next(flat for rank, _, flat in self.layoutRects()[2] if rank == target)
                return editor._bandToolTip(target, horizontal, keys=False)
            return ""

        def editField(self) -> QLineEdit | None:
            """Le champ de saisie des valeurs, s'il est ouvert."""
            return self.findChild(QLineEdit)

        def startEdit(self) -> None:
            """Remplace le bouton des valeurs par un champ de saisie, au patron de l'espace et de la notation courants.

            Entrée retient les valeurs tapées ; Échap, ou la perte du focus, abandonne.
            """
            self.cancelEdit()
            editor = self._editor()
            field = QLineEdit(self)
            field.setFrame(False)
            field.setAlignment(Qt.AlignmentFlag.AlignCenter)
            values = self.layoutRects()[4]
            field.setFont(self.__fittedFont(editor._colorTemplate() + "0", values.width() - 4 * editor._Line))
            field.setInputMask(editor._colorMask())
            field.setText(editor._colorText())
            field.setGeometry(values.toAlignedRect())
            field.installEventFilter(self)      # no signal connected: nothing keeps the field and the window alive
            field.show()
            field.setFocus()
            field.setCursorPosition(field.inputMask().index("("))

        def cancelEdit(self) -> None:
            """Ferme le champ de saisie sans rien retenir."""
            field = self.editField()
            if field is not None:
                field.removeEventFilter(self)
                field.setParent(None)           # at once: deleteLater alone would leave it found until the event loop
                field.deleteLater()
                self.update()

        def acceptEdit(self) -> bool:
            """Retient les valeurs du champ de saisie et le ferme.

            Retourne:
                Faux si le champ est incomplet : il reste alors ouvert.
            """
            field = self.editField()
            if field is None or not field.hasAcceptableInput() or not self._editor()._applyText(field.text()):
                return False
            self.cancelEdit()
            return True

        @override
        def eventFilter(self, watched: QObject, event: QEvent) -> bool:
            if event.type() == QEvent.Type.KeyPress and isinstance(event, QKeyEvent):
                if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    self.acceptEdit()
                    return True
                if event.key() == Qt.Key.Key_Escape:        # the field only: the window stays open
                    self.cancelEdit()
                    return True
            elif event.type() == QEvent.Type.FocusOut:
                self.cancelEdit()
            return False

        @override
        def paintEvent(self, event: QPaintEvent) -> None:
            editor = self._editor()
            palette = editor.palette()
            line = editor._Line
            painter = QPainter(self)
            painter.fillRect(self.rect(), palette.color(QPalette.ColorRole.Mid))            # the outline
            painter.fillRect(QRectF(self.rect()).adjusted(line, line, -line, -line), palette.color(QPalette.ColorRole.Button))
            button, plane, bands, letters, values = self.layoutRects()
            metrics = QFontMetrics(editor._textFont(True))

            self.__paintButton(painter, button, self.Label)
            editor._paintText(painter, button, editor._planeName(editor.plane()), turned=False, along=True)
            painter.save()                          # the letters, one after the other, against the right edge
            painter.setFont(editor._textFont(True))
            painter.setPen(palette.color(QPalette.ColorRole.ButtonText))
            painter.drawText(letters.adjusted(0, 0, -2 * line, 0), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                             "".join(editor._channelLetter(rank) for rank, _, horizontal in bands if not horizontal))
            painter.restore()

            editor._paintPlane(painter, plane, edged=True)
            grip = editor._gripLength()
            for rank, band, horizontal in bands:
                editor._paintBand(painter, rank, band, horizontal, False)
            for rank, band, horizontal in bands:
                editor._paintGrip(painter, rank, band, horizontal, False, grip, rank in (self.__hover, self.__dragged))

            self.__paintButton(painter, values, self.Values)
            icon = metrics.ascent()
            iconRect = QRectF(values.right() - self.__iconZone() + metrics.averageCharWidth() / 2,
                              values.center().y() - icon / 2, icon, icon)
            self.__paintValues(painter, values, QRectF(values.left(), values.top(), iconRect.left() - values.left(),
                                                       values.height()))
            self.__paintCopyIcon(painter, iconRect)

        @override
        def mousePressEvent(self, event: QMouseEvent) -> None:
            point = event.position().toPoint()
            target = self.targetAt(point)
            if not self.rect().contains(point):
                super().mousePressEvent(event)      # a press outside closes a popup
            elif target in (self.Label, self.Values):
                self.__pressed = target
                self.update()
            elif target is not None and event.button() == Qt.MouseButton.LeftButton:
                self.__dragged = target
                self.__dragTo(point)

        @override
        def mouseMoveEvent(self, event: QMouseEvent) -> None:
            point = event.position().toPoint()
            if self.__dragged is not None:
                self.__dragTo(point)
                return
            target = self.targetAt(point)
            if target != self.__hover:
                self.__hover = target
                self.update()
                QToolTip.hideText()

        @override
        def mouseReleaseEvent(self, event: QMouseEvent) -> None:
            editor = self._editor()
            pressed, self.__pressed = self.__pressed, None
            if self.__dragged is not None and event.button() == Qt.MouseButton.LeftButton:
                self.__dragged = None
                editor._commit()
            elif pressed is not None and pressed == self.targetAt(event.position().toPoint()):
                if pressed == self.Label:
                    planes = editor.planes()
                    step = -1 if event.button() == Qt.MouseButton.RightButton else 1
                    editor.setPlane(*planes[(planes.index(editor.plane()) + step) % len(planes)])
                else:
                    self.__copy(event.globalPosition().toPoint())
            self.update()

        @override
        def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
            if self.targetAt(event.position().toPoint()) == self.Values:
                self.startEdit()
            else:
                self.mousePressEvent(event)         # a fast second click on the plane's button is one more click

        @override
        def keyPressEvent(self, event: QKeyEvent) -> None:
            if event.matches(QKeySequence.StandardKey.Copy):
                self.__copy(self.mapToGlobal(self.layoutRects()[4].center().toPoint()))
            elif event.matches(QKeySequence.StandardKey.Paste):
                self._editor()._applyText(QApplication.clipboard().text())
            elif not self.__nudge(event):
                super().keyPressEvent(event)        # Escape closes a popup

        @override
        def wheelEvent(self, event: QWheelEvent) -> None:
            editor = self._editor()
            target = self.targetAt(event.position().toPoint())
            delta = event.angleDelta().y() or event.angleDelta().x()        # some platforms turn a shifted wheel sideways
            if target is None or target < 0 or delta == 0:
                event.ignore()
                return
            event.accept()
            self.__wheelRemainder += -delta if event.inverted() else delta
            notches = int(self.__wheelRemainder / editor._WheelNotch)
            if notches == 0:
                return
            self.__wheelRemainder -= notches * editor._WheelNotch
            self.__move(target, notches, event.modifiers())

        @override
        def hideEvent(self, event: QHideEvent) -> None:
            self.cancelEdit()
            super().hideEvent(event)

        @override
        def leaveEvent(self, event: QEvent) -> None:
            self.__hover = None
            self.update()

        @override
        def event(self, event: QEvent) -> bool:
            if event.type() == QEvent.Type.ToolTip and isinstance(event, QHelpEvent):
                text = self.toolTipAt(event.pos())
                if text:
                    QToolTip.showText(event.globalPos(), text, self)
                else:
                    QToolTip.hideText()
                    event.ignore()
                return True
            return super().event(event)

        def __iconZone(self) -> float:
            """The width kept for the copy icon at the right end of the values button."""
            metrics = QFontMetrics(self._editor()._textFont(True))
            return metrics.ascent() + metrics.averageCharWidth() + 2 * self._editor()._Line

        def __fittedFont(self, text: str, width: float) -> QFont:
            """The font of the labels, shrunk just enough for a text to hold in a width."""
            font = self._editor()._textFont(True)
            needed = QFontMetrics(font).horizontalAdvance(text)
            if needed > width > 0:
                font.setPointSizeF(font.pointSizeF() * width / needed)
            return font

        def __paintValues(self, painter: QPainter, button: QRectF, room: QRectF) -> None:
            """The colour as text: on one line, centred in the button; or its name over its values, left of the icon."""
            editor = self._editor()
            text, template = editor._colorText(), editor._colorTemplate()
            metrics = QFontMetrics(editor._textFont(True))
            painter.save()
            painter.setPen(editor.palette().color(QPalette.ColorRole.ButtonText))
            if metrics.horizontalAdvance(template) <= room.width():
                centred = metrics.horizontalAdvance(template) <= button.width() - 2 * self.__iconZone()
                painter.setFont(editor._textFont(True))
                painter.drawText(button if centred else room, Qt.AlignmentFlag.AlignCenter, text)
            else:
                name, _, numbers = text.partition(" = ")
                half = room.height() / 2
                painter.setFont(editor._textFont(True))
                painter.drawText(QRectF(room.left(), room.top(), room.width(), half),
                                 Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom, name)
                painter.setFont(self.__fittedFont(template.partition(" = ")[2], room.width() - 2 * editor._Line))
                painter.drawText(QRectF(room.left(), room.top() + half, room.width(), half),
                                 Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, numbers)
            painter.restore()

        def __nudge(self, event: QKeyEvent) -> bool:
            """Moves the cross one step the way an arrow key points; tells whether the key was an arrow."""
            first, second = self._editor().plane()
            arrows = {Qt.Key.Key_Left: (first, -1), Qt.Key.Key_Right: (first, 1),
                      Qt.Key.Key_Down: (second, -1), Qt.Key.Key_Up: (second, 1)}
            if event.key() not in arrows:
                return False
            channel, direction = arrows[Qt.Key(event.key())]
            self.__move(channel, direction, event.modifiers())
            return True

        def __move(self, channel: int, steps: int, modifiers: Qt.KeyboardModifier) -> None:
            """Moves a channel by steps: ten at a time with Shift, as drawing programs do, or with Control."""
            editor = self._editor()
            if modifiers & (Qt.KeyboardModifier.ShiftModifier | Qt.KeyboardModifier.ControlModifier):
                steps *= editor._PageSteps
            value = editor.channelValues()[channel] if channel < editor.channelCount() else 0.0
            editor._setChannels({channel: value + steps * editor._step(channel)}, commit=True)

        def __copy(self, globalPoint: QPoint) -> None:
            QApplication.clipboard().setText(self._editor()._colorText())
            QToolTip.showText(globalPoint, self._editor().tr("Copied"), self)

        def __paintButton(self, painter: QPainter, rect: QRectF, target: int) -> None:
            """The bevel of a push button of the current style: it reads as something to press."""
            option = QStyleOptionButton()
            option.initFrom(self)
            option.rect = rect.toAlignedRect()
            option.state &= ~(QStyle.StateFlag.State_MouseOver | QStyle.StateFlag.State_HasFocus)
            option.state |= QStyle.StateFlag.State_Sunken if self.__pressed == target else QStyle.StateFlag.State_Raised
            if self.__hover == target:
                option.state |= QStyle.StateFlag.State_MouseOver
            self.style().drawControl(QStyle.ControlElement.CE_PushButtonBevel, option, painter, self)

        def __paintCopyIcon(self, painter: QPainter, rect: QRectF) -> None:
            """Two overlapping sheets: the usual sign for a copy."""
            editor = self._editor()
            sheet = QRectF(0, 0, rect.width() * 0.68, rect.height() * 0.78)
            pen = QPen(editor.palette().color(QPalette.ColorRole.ButtonText), max(1.0, rect.width() / 9))
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(pen)
            back = sheet.translated(rect.right() - sheet.width(), rect.top())
            front = sheet.translated(rect.left(), rect.bottom() - sheet.height())
            painter.drawRect(back)
            painter.fillRect(front, editor.palette().color(QPalette.ColorRole.Button))     # the front sheet hides the back one
            painter.drawRect(front)
            painter.restore()

        def __dragTo(self, point: QPoint) -> None:
            editor = self._editor()
            _, plane, bands, _, _ = self.layoutRects()
            if self.__dragged == self.Plane:
                first, second = editor.plane()
                x, y = editor._planeValuesAt(plane, point)
                editor._setChannels({first: x, second: y}, commit=editor.hasTracking())
            elif self.__dragged is not None:
                band, horizontal = next((rect, flat) for rank, rect, flat in bands if rank == self.__dragged)
                value = editor._bandValueAt(band, horizontal, False, editor._gripLength(), point)
                editor._setChannels({self.__dragged: value}, commit=editor.hasTracking())
            self.update()

    # =============================================================== eyedropper

    class _ScreenPicker(QScreenColorPicker):
        """La pipette de l'éditeur : son panneau montre un éditeur miroir, et écrit la couleur comme la fenêtre du plan.

        Le miroir prend l'espace, la notation et les espaces offerts de l'éditeur, sans alpha
        ni bascules ; il suit la couleur visée.
        """

        def __init__(self, editor: QColorEdit) -> None:
            """Construit la pipette, enfant de son éditeur.

            Args:
                editor: L'éditeur qui la lance.
            """
            super().__init__(editor)
            self.__mirror: QColorEdit = QColorEdit()
            mirror = self.__mirror
            mirror.setUseAlpha(False)
            mirror.setEyedropperButton(EyedropperButton.Hidden)
            mirror.setSwatchHandleVisible(False)
            mirror.setTextHandleVisible(False)
            for setter in (mirror.setExpandToggleVisible, mirror.setAlphaToggleVisible, mirror.setPlaneToggleVisible,
                           mirror.setNotationToggleVisible):
                setter(False)
            self.currentColorChanged.connect(mirror.setColor)
            self.setPreviewWidget(mirror)

        def prepare(self) -> None:
            """Accorde le miroir et la référence à l'éditeur, juste avant une prise."""
            editor = cast(QColorEdit, self.parent())
            mirror = self.__mirror
            mirror.setAvailableColorSpaces(editor.availableColorSpaces())
            mirror.setColorSpace(editor.colorSpace())
            mirror.setValueNotation(editor.valueNotation())
            mirror.setPlaneVisible(editor.isPlaneVisible())
            mirror.setPlane(*editor.plane())
            mirror.setFont(editor.font())
            mirror.setColor(editor.color())
            self.setReferenceColor(editor.color())

        @override
        def _colorText(self, color: QColor) -> str:
            self.__mirror.setColor(color)
            return self.__mirror._colorText()

    # =============================================================== text zone

    class _ChannelsValidator(QValidator):
        """Le validateur du champ des valeurs : il s'en remet à l'éditeur (`_validateField`).

        Sans éditeur (le champ fermé, ou l'éditeur en cours de destruction), tout reste intermédiaire.
        """

        @override
        def validate(self, text: str, position: int) -> object:
            editor = _editorOf(cast(QLineEdit, self.parent()))
            if editor is None:
                return QValidator.State.Intermediate, text, position
            return editor._validateField(text, position)

    class _CodeValidator(QValidator):
        """Le validateur du champ du code : il s'en remet à l'éditeur (`_validateCode`)."""

        @override
        def validate(self, text: str, position: int) -> object:
            editor = _editorOf(cast(QLineEdit, self.parent()))
            if editor is None:
                return QValidator.State.Intermediate, text, position
            return editor._validateCode(text, position)

    class _TextFlyout(QWidget):
        """Le volet flottant des champs de texte, à côté d'un éditeur vertical.

        Une fenêtre surgissante (`Qt.Popup`) : un clic au-dehors la ferme. En se fermant, elle
        laisse l'éditeur retenir ce qu'elle montrait (`_closeTextFlyout`).
        """

        def __init__(self, editor: QColorEdit) -> None:
            """Construit le volet, enfant de son éditeur.

            Args:
                editor: L'éditeur dont il écrit la couleur.
            """
            super().__init__(editor, Qt.WindowType.Popup)

        @override
        def paintEvent(self, event: QPaintEvent) -> None:
            palette = self.palette()
            with QPainter(self) as painter:
                painter.fillRect(self.rect(), palette.color(QPalette.ColorRole.Mid))
                painter.fillRect(self.contentsRect(), palette.color(QPalette.ColorRole.Base))

        @override
        def hideEvent(self, event: QHideEvent) -> None:
            editor = self.parentWidget()
            if isinstance(editor, QColorEdit):
                editor._closeTextFlyout()
            super().hideEvent(event)

def _editorOf(field: QWidget) -> QColorEdit | None:
    """The editor a field of the text belongs to, through the flyout if it is in one; None once gone."""
    widget = field.parentWidget()
    while widget is not None and not isinstance(widget, QColorEdit):
        widget = widget.parentWidget()
    return widget


type _QColorState = tuple[QColor, list[float], float]
"""The colour retained, the channels on display and the alpha: what `_setColorState` gives back."""


def _desaturated(color: QColor, amount: float) -> QColor:
    """A copy of a colour blended toward the grey of the same luminance, alpha kept; as `QColorBox._desaturated`."""
    gray = qGray(color.rgb())
    return QColor(round(color.red() * (1 - amount) + gray * amount), round(color.green() * (1 - amount) + gray * amount),
                  round(color.blue() * (1 - amount) + gray * amount), color.alpha())


def _sameColor(first: QColor, second: QColor) -> bool:
    """Whether two colours read the same at 8 bits per channel, whatever the space each is expressed in.

    A conversion between two spaces does not round-trip exactly at the 16 bits QColor keeps.
    """
    return first.rgba() == second.rgba()


def _colorFrom(space: QColorEdit.ColorSpace, components: Sequence[float], alpha: float) -> QColor:
    """The colour that the channels of a space compose."""
    Space = QColorEdit.ColorSpace
    if space == Space.Rgb:
        return QColor.fromRgbF(components[0], components[1], components[2], alpha)
    if space == Space.Hsv:
        return QColor.fromHsvF(components[0], components[1], components[2], alpha)
    if space == Space.Hsl:
        return QColor.fromHslF(components[0], components[1], components[2], alpha)
    return QColor.fromCmykF(components[0], components[1], components[2], components[3], alpha)


def _componentsOf(color: QColor, space: QColorEdit.ColorSpace, kept: Sequence[float] | None,
                  hue: float | None) -> list[float]:
    """The channels of a colour in a space, each in [0, 1].

    A channel that the colour leaves undefined keeps a former value rather than falling to
    zero: the hue of a grey, the saturation of black (and of white, in HSL), the cyan, magenta
    and yellow of pure black.

    Args:
        color: The colour to express.
        space: The space to express it in.
        kept: The channels on display, if they are those of this same space.
        hue: The hue on display, if any.
    """
    Space = QColorEdit.ColorSpace
    if space == Space.Rgb:
        return [color.redF(), color.greenF(), color.blueF()]
    if space == Space.Cmyk:
        components = [color.cyanF(), color.magentaF(), color.yellowF(), color.blackF()]
        if kept is not None and components[3] >= 1.0:
            components[:3] = kept[:3]
        return components
    if space == Space.Hsv:
        components = [color.hsvHueF(), color.hsvSaturationF(), color.valueF()]
        saturationLost = components[2] <= 0.0
    else:
        components = [color.hslHueF(), color.hslSaturationF(), color.lightnessF()]
        saturationLost = components[2] <= 0.0 or components[2] >= 1.0
    if components[0] < 0.0:                 # achromatic: QColor reports a hue of -1
        components[0] = hue if hue is not None else 0.0
    if kept is not None and saturationLost:
        components[1] = kept[1]
    return components
