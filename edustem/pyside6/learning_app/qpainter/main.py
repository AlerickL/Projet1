# Ligne de commande (depuis new/sf3) :
#   python -m edustem.pyside6.learning_app.qpainter

"""Application d'apprentissage interactif : dessiner avec QPainter.

On n'y apprend pas à peindre un widget : on apprend à dessiner. L'apprenant
crée sa propre image (`QImage`), y dessine avec un `QPainter`, puis la
confie au canevas du guide (`QDrawingCanvas`, voir `q_drawing_canvas.py`),
qui l'affiche. Cinq chapitres, quinze notions.

L'assemblage de la fenêtre est entièrement délégué à `QWalkthroughWindow`
(voir `common/q_walkthrough_app.py`) : ce fichier ne fait que déclarer son
introduction, son glossaire et ses chapitres, dans l'ordre, avec leurs
prérequis.

Toutes les images de l'application sont produites par QPainter : l'image de
l'introduction, et celles de l'introduction et de la synthèse de chaque
chapitre, sont des œuvres de `artworks.py`, dont le programme est aussi une
œuvre de l'atelier (notion 5.2) ; l'icône de la fenêtre reprend les
quatre formes de la notion 4.3 (`drawIcons`). Les images des œuvres sont
lues en PNG, pré-générées par `render_artwork_images.py` : la fenêtre
n'exécute aucun programme à sa construction.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap

from ..common.glossary import glossaryHtml
from ..common.doc_urls import qtDocUrl, qtPageUrl
from ..common.q_step_walkthrough import QImageCaption
from ..common.q_walkthrough_app import QWalkthroughWindow, runWalkthroughApplication
from .artworks import Artwork, artworkImage, artworkOfChapter, introductionArtwork
from .topic_1_1_surface import QTopicSurfaceTab
from .topic_1_2_shapes import QTopicShapesTab
from .topic_1_3_quality import QTopicStrokeQualityTab
from .topic_1_4_painter_life import QTopicPainterLifeTab
from .topic_2_1_pen import QTopicPenTab
from .topic_2_2_brush import QTopicBrushTab
from .topic_2_3_colors import QTopicColorsTab
from .topic_2_4_gradients import QTopicGradientsTab
from .topic_3_1_text import QTopicTextTab
from .topic_3_2_transforms import QTopicTransformsTab
from .topic_4_1_paths import QTopicPathsTab
from .topic_4_2_clipping import QTopicClippingTab
from .topic_4_3_images import QTopicImagesTab, drawIcons
from .topic_5_1_illustration import QTopicIllustrationTab
from .topic_5_2_workshop import QTopicWorkshopTab


# Les termes employés par l'application.
_Glossary = glossaryHtml(
    "le dessin avec QPainter",
    [("", [
        ("peintre", "<code>QPainter</code>", "celui qui dessine ; il est <i>actif</i>, "
         "<i>commence</i> et <i>termine</i> (notions 1.1 et 1.4)"),
        ("surface", "<code>QImage</code>, <code>QPixmap</code>", "ce sur quoi le peintre dessine : "
         "une grille de pixels ; ce guide n'emploie que <code>QImage</code>"),
        ("stylo", "<code>QPen</code>", "trace les contours : lignes, bords des formes, texte"),
        ("pinceau", "<code>QBrush</code>", "fait le remplissage : l'intérieur des formes fermées"),
        ("contour", "", "ce que trace le stylo"),
        ("remplissage", "", "ce que fait le pinceau"),
        ("repère", "", "le système de coordonnées : origine en haut à gauche, x vers la droite, "
         "y vers le bas"),
        ("anticrénelage", "<code>Antialiasing</code>", "teinte intermédiaire des pixels du bord, "
         "qui rend un trait lisse"),
        ("dégradé", "<code>QGradient</code>", "un remplissage qui passe d'une couleur à une autre"),
        ("point d'arrêt", "<code>setColorAt()</code>", "une couleur placée à une position du "
         "dégradé"),
        ("chemin", "<code>QPainterPath</code>", "un contour libre fait de droites et de courbes"),
        ("découpage", "<code>setClipRect()</code>", "la zone hors de laquelle le peintre ne "
         "dessine pas"),
        ("composition", "<code>CompositionMode</code>", "la façon de combiner ce qu'on dessine "
         "avec ce qui est déjà là"),
        ("source, destination", "", "ce qu'on dessine, et ce qui est déjà dans l'image"),
    ])],
    [
        ("canevas", "<code>self.canvas</code>", "affiche l'image qu'on lui confie par "
         "<code>setImage()</code> ; grille et agrandissement en option (notions 1.1 et 1.3)"),
        ("damier", "", "le motif gris et blanc du canevas, visible là où l'image est "
         "transparente"),
        ("lecture", "<code>self.readout</code>", "la ligne de texte sous le canevas, remplie par "
         "<code>setText()</code> (notion 1.3)"),
        ("les contrôles", "<code>self.controls</code>", "range sous le canevas les "
         "contrôles d'une étape « À vous » ; <code>setCaption()</code> change le libellé d'un "
         "contrôle, <code>setDivisor()</code> la valeur affichée d'un sélecteur (notion 2.3)"),
        ("éditeur des points d'arrêt", "<code>self.stopsEditor</code>", "règle la couleur et la "
         "position de chaque point d'arrêt ; <code>stops()</code> les rend, le signal "
         "<code>stopsChanged</code> est émis à chaque changement (notion 2.4)"),
        ("code du dégradé", "<code>self.gradientCode</code>", "écrit le code Python qui recrée le "
         "dégradé reçu par <code>setGradient()</code>, avec un bouton pour le copier (notion 2.4)"),
        ("case", "", "une zone carrée de l'image qui reçoit un dessin, dans une grille de dessins "
         "(notions 1.2, 3.1, 4.2 et 4.3) ; à ne pas confondre avec une case à cocher"),
        ("atelier", "", "la page de la notion 5.2 : un éditeur où écrire ses propres programmes de "
         "dessin, et le canevas qui affiche leur dessin à mesure qu'on écrit"),
        ("appel de dessin", "", "l'appel d'une méthode du peintre qui dessine, comme "
         "<code>drawEllipse()</code> ou <code>fillRect()</code> ; l'atelier les compte (notion 5.2)"),
        ("fragment, œuvre", "", "dans l'atelier, un fragment s'insère dans le programme ; une "
         "œuvre le remplace en entier (notion 5.2)"),
    ],
    ["widget, fenêtre", "parent, enfant", "signal, slot", "accesseur, mutateur", "contrôle",
     "sélecteur numérique", "case à cocher", "liste déroulante", "bouton", "curseur de texte"],
)

# La page « Introduction » : des champs nommés, mis en forme par QWalkthroughWindow.
_IntroductionHook = (
    "Avec quelques lignes de Python, un <b>peintre</b> trace des formes, des couleurs, du texte "
    "et des images, pixel par pixel. Ce guide vous apprend à dessiner avec QPainter."
)
_IntroductionMotivation = (
    "QPainter est l'outil de dessin de Qt. Les widgets de Qt eux-mêmes se dessinent avec lui. "
    "On s'en sert pour produire une image, générer une illustration ou une page à imprimer, "
    "ou dessiner un widget sur mesure. Savoir dessiner affranchit des widgets existants : ce "
    "qu'on sait décrire, on peut l'afficher. Ce guide dessine dans des images. Le widget sur "
    "mesure reprend les mêmes gestes : le second lien de « Pour aller plus loin » le présente."
)
_IntroductionAudience = (
    "Ce guide s'adresse à qui sait programmer en Python et a déjà construit une petite "
    "interface avec Qt : des widgets, des signaux et des slots. Il ne suppose aucune "
    "connaissance du dessin ni de QPainter."
)
_IntroductionOutcomes = [
    "dessiner des formes simples et libres, placées au pixel près, avec un trait net ;",
    "maîtriser l'apparence d'un dessin : contours, remplissages, couleurs, transparence et "
    "dégradés ;",
    "écrire du texte, et transformer le repère pour répéter ou orienter un motif ;",
    "limiter le dessin à une zone, combiner des couches, et dessiner des images dans d'autres "
    "images ;",
    "décomposer une illustration en gestes simples, puis écrire vos propres programmes de "
    "dessin.",
]
_IntroductionFurtherReading = [
    f'<a href="{qtPageUrl("paintsystem")}">Le système de dessin de Qt</a> (en anglais) : le '
    "peintre, ses surfaces et ses outils, vus d'ensemble.",
    f'<a href="{qtDocUrl("QtWidgets", "QWidget", "paintEvent")}">Dessiner un widget sur '
    "mesure</a> (en anglais) : les mêmes gestes, dans la méthode qu'un widget appelle pour se "
    "dessiner.",
]

# Objectifs de chaque chapitre, sans aucun détail technique.
_Chapter1Introduction = (
    "Ce chapitre pose le geste de base du dessin avec Qt. Quatre mots reviennent dans tout le "
    "guide : un <b>peintre</b> travaille sur une <b>surface</b>, avec un <b>stylo</b> pour les "
    "contours et un <b>pinceau</b> pour le remplissage. Le chapitre présente ensuite toutes les "
    "formes de base, puis ce qui fait la qualité d'un trait à l'échelle du pixel, et enfin "
    "quand un peintre est actif. L'objectif est de savoir placer précisément n'importe quelle "
    "forme simple, et d'obtenir un trait net."
)
_Chapter2Introduction = (
    "Ce chapitre s'intéresse à l'apparence de ce qu'on dessine : le contour, le "
    "remplissage, les couleurs et leur transparence, puis les dégradés. Quelques mots "
    "s'ajoutent. Un <b>espace de couleurs</b> décrit une couleur par trois nombres : rouge, vert "
    "et bleu, ou teinte, saturation et valeur. L'<b>alpha</b> dit à quel point une couleur cache "
    "ce qui est dessous. Un <b>dégradé</b> passe d'une couleur à l'autre, par des <b>points "
    "d'arrêt</b> qui fixent chaque couleur à sa place. L'objectif est de "
    "maîtriser le rendu d'une forme, pas seulement sa position."
)
_Chapter3Introduction = (
    "Ce chapitre ajoute le texte au dessin, puis apprend à déplacer, tourner et étirer le "
    "repère lui-même plutôt que chaque forme. Quelques mots s'ajoutent. La <b>ligne de "
    "base</b> est la ligne sur laquelle reposent les lettres. Une <b>transformation</b> déplace, "
    "tourne ou étire le repère : tout ce qui est dessiné ensuite la suit. L'objectif est de "
    "composer des dessins "
    "répétitifs ou orientés sans calculer chaque coordonnée à la main."
)
_Chapter4Introduction = (
    "Ce chapitre dépasse les formes de base : des contours libres faits de droites et de "
    "courbes, des zones de dessin limitées, des façons de combiner ce qui est déjà dessiné, "
    "et des images dessinées dans d'autres images. Quelques mots s'ajoutent. Un <b>chemin</b> "
    "est un contour libre, fait de droites et de courbes, dessiné d'un seul coup. Le "
    "<b>découpage</b> limite le dessin à une zone : rien ne paraît au-dehors. La "
    "<b>composition</b> décide comment un nouveau dessin se combine avec ce qui est déjà là. "
    "L'objectif est de pouvoir dessiner "
    "n'importe quelle forme, aussi complexe soit-elle."
)
_Chapter5Introduction = (
    "Ce dernier chapitre réunit toutes les techniques du guide. D'abord dans une seule "
    "illustration, construite couche par couche, qui suit l'heure de la journée. Puis dans vos "
    "propres programmes : vous écrivez votre code de dessin, et le canevas l'affiche à mesure "
    "que vous l'écrivez. L'objectif est de savoir décomposer un dessin complet en gestes "
    "simples, puis de passer de la lecture à l'écriture : composer vos propres dessins, en "
    "réutilisant librement tout ce que le guide a présenté."
)

# Synthèse de chaque chapitre (skill, §6) : chaque notion en une phrase, du recul, une ouverture.
_Chapter1Synthesis = (
    "<ul>"
    "<li><b>1.1</b> Un peintre (<code>QPainter</code>) dessine sur une surface "
    "(<code>QImage</code>), avec un stylo (<code>QPen</code>), dans un repère dont l'origine est "
    "en haut à gauche.</li>"
    "<li><b>1.2</b> Chaque forme de base se place d'une de quatre façons : par ses coins, par un "
    "rectangle englobant, par un centre et des rayons, ou par une liste de points.</li>"
    "<li><b>1.3</b> La netteté se joue au pixel. L'anticrénelage adoucit les obliques, et un "
    "trait d'un pixel est net sur une demi-coordonnée.</li>"
    "<li><b>1.4</b> Un peintre ne dessine que s'il est actif, et une image n'en accepte qu'un à "
    "la fois. Le bloc <code>with</code> le termine toujours.</li>"
    "</ul>"
    "Ces quatre notions forment un seul geste : créer une surface, faire commencer un peintre, "
    "lui donner "
    "un stylo, dessiner, terminer. Le reste du guide garde ce geste et n'en change que les "
    "outils. La géométrie de Qt existe en deux versions, entière et réelle. La version réelle "
    "(<code>QPointF</code>, <code>QRectF</code>) garde la précision : c'est elle qu'on préfère "
    "dès que l'anticrénelage est actif."
    "<br><br>Le même peintre dessine aussi sur un widget, sur une page à imprimer ou dans un "
    "fichier PDF : seule la surface change, et les gestes de ce chapitre valent pour toutes. "
    "L'image ci-contre n'emploie que ces gestes : des cercles d'un simple trait, dont les "
    "croisements font naître des franges."
)
_Chapter2Synthesis = (
    "<ul>"
    "<li><b>2.1</b> Le stylo trace les lignes et les contours : couleur, épaisseur, style, "
    "extrémités et jonctions. Un trait épais est centré sur sa ligne.</li>"
    "<li><b>2.2</b> Le pinceau remplit l'intérieur des formes fermées, d'une couleur ou d'un "
    "motif. <code>fillRect()</code> remplit sans toucher au stylo ni au pinceau.</li>"
    "<li><b>2.3</b> Une couleur se décrit en RGB, en HSV ou en HSL, et son canal alpha la rend "
    "translucide.</li>"
    "<li><b>2.4</b> Un dégradé, linéaire, radial ou conique, se pose dans un pinceau. Ses "
    "points d'arrêt placent ses couleurs.</li>"
    "</ul>"
    "Le stylo et le pinceau se règlent séparément : un contour seul, un remplissage seul, ou les "
    "deux. Le peintre les garde jusqu'au prochain changement. Un dessin se lit donc comme une "
    "suite de réglages, puis de tracés. Pour choisir des couleurs qui vont ensemble, HSV est "
    "souvent le plus commode : on garde la teinte, et on fait varier la saturation ou la "
    "valeur. Les écailles de l'image ci-contre tournent ainsi lentement autour de la roue des "
    "teintes, chacune éclairée par un dégradé de sa propre couleur."
    "<br><br>Les couleurs de ce chapitre sont celles d'un écran : trois lumières qui "
    "s'additionnent. L'imprimerie fait l'inverse : ses encres retirent de la lumière, et elle "
    "décrit une couleur par quatre encres, cyan, magenta, jaune et noir. Ni V ni L ne mesurent "
    "la clarté que perçoit l'œil (notion 2.3) : d'autres espaces de couleurs, conçus pour la "
    "perception, en tiennent compte."
)
_Chapter3Synthesis = (
    "<ul>"
    "<li><b>3.1</b> <code>drawText()</code> pose un texte sur sa ligne de base, avec la police "
    "de <code>setFont()</code> et la couleur du stylo. <code>QFontMetrics</code> le mesure, pour "
    "le centrer ou le raccourcir soi-même.</li>"
    "<li><b>3.2</b> Les transformations déplacent, tournent, agrandissent ou cisaillent le "
    "repère. Elles s'accumulent, leur ordre compte, et <code>save()</code> et "
    "<code>restore()</code> les isolent.</li>"
    "</ul>"
    "Les deux notions répondent à la même question : où placer ce qu'on dessine. Pour un texte, "
    "la police donne les mesures. Pour une forme répétée, la transformation évite de recalculer "
    "chaque coordonnée : on dessine la forme autour de (0, 0), puis on déplace le repère. Le "
    "cadran ci-contre réunit les deux : ses graduations sont posées par rotation, et ses "
    "chiffres centrés grâce à leurs mesures."
    "<br><br>Le repère est une matrice (<code>QTransform</code>). La même mathématique sert à la "
    "cartographie, aux jeux vidéo et à la 3D, où les matrices passent à quatre lignes et quatre "
    "colonnes. Le texte, lui, va bien plus loin qu'une ligne : la mise en page de paragraphes, "
    "de titres et de tableaux est un domaine à part entière, et Qt sait aussi la dessiner."
)
_Chapter4Synthesis = (
    "<ul>"
    "<li><b>4.1</b> Un chemin (<code>QPainterPath</code>) décrit un contour libre, fait de "
    "droites et de courbes de Bézier. Il se remplit selon une règle, et se combine à d'autres "
    "chemins par union, intersection ou différence.</li>"
    "<li><b>4.2</b> Le découpage limite le dessin à une zone. Le mode de composition décide "
    "comment chaque nouveau dessin se combine avec ce que l'image contient déjà.</li>"
    "<li><b>4.3</b> Une image se dessine dans une autre : entière ou en partie, agrandie, "
    "répétée ou translucide. Ses pixels se lisent et s'écrivent un à un.</li>"
    "</ul>"
    "Ces notions changent d'échelle : on ne dessine plus une forme, on compose une image. Le "
    "chemin donne n'importe quelle forme. Le découpage et la composition décident où et comment "
    "elle se pose. Une image dessinée une fois se réutilise comme un tampon. Dans l'image "
    "ci-contre, les pétales sont superposés en mode <code>Screen</code> : chaque recouvrement "
    "éclaircit au lieu de cacher."
    "<br><br>Les logiciels de dessin reposent sur ces mêmes idées : les courbes de Bézier des "
    "logiciels de dessin vectoriel, les modes de fusion des calques des logiciels de retouche. "
    "Lire et écrire chaque pixel ouvre enfin le traitement d'images : flou, détection de "
    "contours, filtres. Pour une grande image, numpy, une bibliothèque de calcul sur des "
    "tableaux de nombres, traite tous les pixels d'un coup."
)
_Chapter5Synthesis = (
    "<ul>"
    "<li><b>5.1</b> Une illustration se décompose en couches, dessinées du fond vers l'avant, "
    "chacune avec la technique qui lui convient. Puis tout le dessin dépend d'un seul nombre : "
    "l'heure de la journée.</li>"
    "<li><b>5.2</b> L'atelier exécute votre propre programme de dessin et l'affiche à mesure "
    "que vous l'écrivez. Les fragments reprennent les gestes de chaque notion, et une erreur "
    "s'affiche à sa ligne.</li>"
    "</ul>"
    "Les deux notions réunissent tout le guide, l'une en lisant, l'autre en écrivant. Dessiner "
    "une scène, c'est d'abord la décomposer : chaque couche a sa méthode et se lit seule. Les "
    "valeurs écrites en clair deviennent ensuite des calculs, et la scène se paramètre. "
    "Écrire soi-même, c'est faire ces choix : la surface, l'ordre des couches, la technique de "
    "chaque partie. Une boucle répète un motif, le hasard le varie, une fonction lui donne un "
    "nom. L'arbre ci-contre va plus loin : la fonction qui dessine une branche s'appelle "
    "elle-même pour les deux branches suivantes, chacune dans un repère tourné."
    "<br><br>Un dessin qui dépend d'un nombre est à un pas de l'animation : il suffit de "
    "changer ce nombre à intervalle régulier, et de redessiner. Ce que vous dessinez dans "
    "l'atelier se dessine de la même façon ailleurs : dans une image enregistrée dans un "
    "fichier, ou dans un widget sur mesure, que présente le second lien « Pour aller plus "
    "loin » de l'introduction. L'art génératif fait enfin de tels programmes une pratique "
    "artistique : des règles simples, un peu de hasard, et des formes qu'on n'aurait pas "
    "dessinées à la main."
)
_Syntheses = {1: _Chapter1Synthesis, 2: _Chapter2Synthesis, 3: _Chapter3Synthesis, 4: _Chapter4Synthesis,
              5: _Chapter5Synthesis}


def buildWindow() -> QWalkthroughWindow:
    """Construit la fenêtre complète, ses chapitres déclarés dans l'ordre.

    Utilisée aussi telle quelle par les tests (voir `learning_app/tests`).
    """
    window = QWalkthroughWindow("Dessiner avec QPainter — Guide d'apprentissage")
    window.setWindowIcon(_applicationIcon())
    artwork = introductionArtwork()
    window.addIntroduction(
        hook=_IntroductionHook, motivation=_IntroductionMotivation, audience=_IntroductionAudience,
        outcomes=_IntroductionOutcomes,
        furtherReading=_IntroductionFurtherReading, image=artworkImage(artwork),
        imageCaption=_caption(artwork))
    window.addGlossary(_Glossary)
    window.addChapter("Chapitre 1 — Premiers traits", _Chapter1Introduction,
                      [QTopicSurfaceTab, QTopicShapesTab, QTopicStrokeQualityTab, QTopicPainterLifeTab],
                      prerequisites=["classes et méthodes", "listes et tuples", "boucles", "f-strings",
                                     "annotations de type", "bloc with",
                                     "modules et imports", "application et widget", "signaux et slots", "accesseur et mutateur",
                                     "constantes Qt", "QSlider", "QCheckBox", "QComboBox", "Slot"],
                      **_illustration(1),
                      summary="le peintre, la surface, les formes de base et la netteté du trait")
    window.addChapter("Chapitre 2 — Stylo, pinceau et couleurs", _Chapter2Introduction,
                      [QTopicPenTab, QTopicBrushTab, QTopicColorsTab, QTopicGradientsTab],
                      prerequisites=["héritage", "QRadioButton"],
                      **_illustration(2),
                      summary="le contour, le remplissage, les couleurs et les dégradés")
    window.addChapter("Chapitre 3 — Texte et transformations", _Chapter3Introduction,
                      [QTopicTextTab, QTopicTransformsTab],
                      prerequisites=["drapeaux combinés"],
                      **_illustration(3),
                      summary="le texte, et les transformations du repère")
    window.addChapter("Chapitre 4 — Formes complexes", _Chapter4Introduction,
                      [QTopicPathsTab, QTopicClippingTab, QTopicImagesTab],
                      **_illustration(4),
                      summary="les formes libres, le découpage, la composition et les images")
    window.addChapter("Chapitre 5 — Synthèse", _Chapter5Introduction,
                      [QTopicIllustrationTab, QTopicWorkshopTab],
                      prerequisites=["module math", "module random", "trigonométrie"],
                      **_illustration(5),
                      summary="une illustration interactive, puis l'atelier, où vous écrivez vos "
                              "propres programmes de dessin")
    return window


def main() -> int:
    return runWalkthroughApplication(buildWindow)


# ====== Privé ======

def _illustration(chapter: int) -> dict[str, object]:
    """Les deux images d'un chapitre (introduction et synthèse), leurs légendes, et le texte de sa synthèse."""
    artwork = artworkOfChapter(chapter)
    synthesisArtwork = artworkOfChapter(chapter, synthesis=True)
    return {"image": artworkImage(artwork), "imageCaption": _caption(artwork),
            "synthesis": _Syntheses[chapter], "synthesisImage": artworkImage(synthesisArtwork),
            "synthesisImageCaption": _caption(synthesisArtwork)}


def _caption(artwork: Artwork) -> QImageCaption:
    """La légende d'une œuvre : son titre, son auteur, sa source, et où trouver son programme."""
    return QImageCaption(f"<i>{artwork.title}</i>", "Un programme de ce guide", "Image dessinée par QPainter",
                        "Son programme est dans l'atelier (notion 5.2, « Charger une œuvre »), à lire, "
                        "exécuter et modifier.")


def _applicationIcon() -> QIcon:
    """L'icône de la fenêtre : les quatre formes de la notion 4.3, redessinées à chaque taille.

    Les formes occupent le carré de 4 à 60 de leur repère de 64 × 64 : le
    recadrage sur ce carré les agrandit, pour qu'elles restent lisibles même
    à 16 pixels.
    """
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        image = QImage(size, size, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        with QPainter(image) as painter:
            painter.scale(size / 58, size / 58)
            painter.translate(-3, -3)
            drawIcons(painter)
        icon.addPixmap(QPixmap.fromImage(image))
    return icon
