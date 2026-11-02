# Ligne de commande (depuis new/sf3) :
#   python -m edustem.pyside6.learning_app.pyqtgraph

"""Application d'apprentissage interactif : visualiser des données avec PyQtGraph.

Quatre chapitres, dix-neuf notions : les graphiques 2D, la géométrie et
les champs dans le plan, la visualisation 3D, puis une synthèse, un tableau
de bord.

L'assemblage de la fenêtre est entièrement délégué à `QWalkthroughWindow`
(voir `common/q_walkthrough_app.py`) : ce fichier ne fait que déclarer son
introduction, son glossaire et ses chapitres, dans l'ordre, avec leurs
prérequis.
"""

from ..common.doc_urls import pyqtgraphDocUrl, qtPageUrl
from ..common.glossary import glossaryHtml
from ..common.image_assets import imageAssets
from ..common.q_walkthrough_app import QWalkthroughWindow, runWalkthroughApplication
from .topic_1_1_lines import QTopicLinesTab
from .topic_1_2_scatter import QTopicScatterTab
from .topic_1_3_interaction import QTopicInteractionTab
from .topic_1_4_realtime import QTopicRealTimeTab
from .topic_1_5_layout import QTopicLayoutTab
from .topic_1_6_statistics import QTopicStatisticsTab
from .topic_1_7_view import QTopicViewTab
from .topic_1_8_signals import QTopicSignalsTab
from .topic_2_1_polygons import QTopicPolygonsTab
from .topic_2_2_transformations import QTopicTransformationsTab
from .topic_2_3_polygon_series import QTopicPolygonSeriesTab
from .topic_2_4_heatmap import QTopicHeatMapTab
from .topic_2_5_vector_field import QTopicVectorFieldTab
from .topic_3_1_scene import QTopicSceneTab
from .topic_3_2_projectile import QTopicProjectileTab
from .topic_3_3_surface import QTopicSurfaceTab
from .topic_3_4_vector_field import QTopicVectorField3DTab
from .topic_3_5_volume import QTopicVolumeTab
from .topic_4_1_dashboard import QTopicDashboardTab


# Les images d'illustration et leurs légendes : assets/images/pyqtgraph/images.json.
_Images = imageAssets("pyqtgraph")


# Les termes employés par l'application.
_Glossary = glossaryHtml(
    "les graphiques avec PyQtGraph",
    [("Les graphiques 2D", [
        ("graphique", "<code>PlotItem</code>", "les axes, la grille, le titre et tout ce qui est "
         "tracé ; le widget qui le contient est un <code>PlotWidget</code> (notion 1.1)"),
        ("zone visible", "<code>ViewBox</code>", "la région des données montrée par le graphique "
         "(notion 1.2)"),
        ("élément graphique", "", "tout ce qu'on ajoute à un graphique : une courbe, un nuage, une "
         "flèche, un texte…"),
        ("courbe", "<code>PlotDataItem</code>", "des points reliés par un trait"),
        ("nuage de points", "<code>ScatterPlotItem</code>", "des points sans trait"),
        ("légende", "<code>LegendItem</code>", "la liste des éléments nommés, avec leur échantillon"),
        ("axe, grille", "<code>AxisItem</code>", "la règle graduée d'un côté du graphique ; les "
         "lignes de repère"),
        ("barre d'erreur", "<code>ErrorBarItem</code>", "un trait qui montre l'incertitude d'une "
         "mesure"),
        ("stylo", "<code>pg.mkPen()</code>", "décrit les traits et les contours : couleur, "
         "épaisseur, style"),
        ("pinceau", "<code>pg.mkBrush()</code>", "décrit le remplissage"),
        ("opacité", "", "à quel point une couleur cache ce qui est derrière, de 0 (transparent) à "
         "son maximum (opaque). Le maximum dépend de l'écriture : 255 pour le quatrième nombre "
         "d'une couleur 2D ou du tableau de couleurs d'une image ou d'un volume, 1 pour "
         "<code>alpha</code> et pour une couleur 3D en tuple ou en tableau (surface, lignes, "
         "points), 100 % pour un sélecteur numérique"),
        ("ligne de lecture", "<code>InfiniteLine</code>", "une ligne qu'on déplace à la souris pour "
         "lire une valeur (notion 1.3)"),
        ("cible", "<code>TargetItem</code>", "un marqueur placé sur un point (notion 1.3)"),
        ("étiquette d'information", "<code>TextItem</code>", "un texte placé dans le graphique, avec "
         "un contour et un fond, qui donne un résultat (notion 1.3)"),
        ("tampon", "", "un tableau de taille fixe qui garde les dernières mesures (notion 1.4)"),
        ("fenêtre glissante", "", "les dernières secondes d'un flux, qui avancent avec le temps"),
        ("échelle logarithmique", "<code>setLogMode()</code>", "un axe où chaque graduation vaut "
         "dix fois la précédente ; une <i>décade</i> est l'écart entre deux puissances de 10"),
        ("histogramme, tranche", "<code>np.histogram</code>", "le nombre de mesures dans chaque "
         "tranche de valeurs"),
        ("écart type", "<code>np.std</code>", "la dispersion typique des mesures autour de leur "
         "moyenne, noté σ"),
        ("incertitude sur la moyenne", "", "σ/√n : la précision de la moyenne de n mesures"),
        ("échelle égale, exagération", "<code>setAspectLocked()</code>", "un mètre vaut autant de "
         "pixels sur les deux axes ; ou un rapport choisi, qui grandit le relief d'un profil "
         "(notion 1.7)"),
        ("ajustement automatique", "<code>enableAutoRange()</code>", "un axe cadré de lui-même sur "
         "les données, à chaque changement ; <code>autoRange()</code> cadre une seule fois "
         "(notion 1.7)"),
        ("barre d'échelle", "<code>ScaleBar</code>", "une longueur de référence, dessinée sur une "
         "carte sans axes (notion 1.7)"),
        ("gain, fréquence de coupure", "", "le rapport des amplitudes de sortie et d'entrée d'un "
         "filtre ; la fréquence où il vaut 1/√2 (notion 1.8)"),
        ("bande", "<code>LinearRegionItem</code>", "un intervalle déplaçable, entre deux bornes "
         "(notion 1.8)"),
        ("écho", "", "un changement renvoyé à sa source par deux commandes reliées dans les deux "
         "sens (notion 1.8)"),
    ]),
     ("Géométrie et champs", [
        ("polygone", "<code>QGraphicsPolygonItem</code>", "une forme fermée, donnée par ses sommets"),
        ("parent, enfant", "<code>setParentItem()</code>", "un enfant s'affiche avec son parent et "
         "suit sa position, sa transformation et sa visibilité (notion 2.3)"),
        ("série de polygones", "<code>QGraphicsItemGroup</code>", "des polygones rangés sous un même "
         "parent, qui les gère ensemble (notion 2.3)"),
        ("élément témoin", "", "un élément jamais tracé, qui donne à la légende l'échantillon d'une "
         "série (notion 2.3)"),
        ("déterminant", "<code>np.linalg.det</code>", "pour une matrice 2 × 2, le facteur par lequel "
         "elle multiplie les aires"),
        ("flèche, hampe, pointe", "<code>ArrowItem</code>", "une flèche ; sa hampe est le trait, sa "
         "pointe le triangle du bout"),
        ("résultante", "", "la somme de plusieurs forces"),
        ("transformation, matrice", "<code>QTransform</code>", "tourner, agrandir ou déplacer un "
         "élément graphique ; la matrice qui fait ce calcul"),
        ("ancre", "", "le point d'un texte placé à la position donnée"),
        ("carte de chaleur", "<code>ImageItem</code>", "une grandeur du plan montrée par des "
         "couleurs"),
        ("palette, barre de couleurs", "<code>ColorMap</code>, <code>ColorBarItem</code>", "la "
         "suite des couleurs d'une carte, et la règle qui la montre"),
        ("équipotentielle", "<code>IsocurveItem</code>", "la ligne des points de même potentiel"),
        ("champ de flèches", "", "une flèche en chaque point d'une grille"),
        ("scène Qt", "<code>QGraphicsScene</code>", "l'espace en pixels où vivent les éléments d'un "
         "graphique 2D (notion 2.4)"),
    ]),
     ("La 3D", [
        ("vue 3D", "<code>GLViewWidget</code>", "le widget qui montre une scène en trois "
         "dimensions"),
        ("scène 3D", "", "l'ensemble des éléments placés dans la vue"),
        ("caméra", "", "le point d'où l'on regarde la scène"),
        ("azimut, élévation", "", "l'angle de la caméra autour de l'axe vertical, et sa hauteur "
         "au-dessus du sol, en degrés"),
        ("maillage", "<code>MeshData</code>", "une forme faite de triangles"),
        ("surface", "<code>GLSurfacePlotItem</code>", "une hauteur en chaque point d'une grille"),
        ("volume", "<code>GLVolumeItem</code>", "une grandeur en chaque point d'un cube, montrée "
         "translucide"),
        ("coupe", "<code>GLImageItem</code>", "les valeurs d'une grandeur dans un plan, extraites "
         "d'une surface (notion 3.3) ou d'un volume (notion 3.5)"),
        ("test de profondeur", "<code>GL.GL_DEPTH_TEST</code>", "pour chaque pixel, OpenGL ne "
         "dessine pas ce qui est plus loin que ce qu'il y a déjà dessiné (notion 3.5)"),
        ("ordre de dessin", "<code>setDepthValue()</code>", "les éléments 3D sont dessinés de la "
         "plus petite valeur à la plus grande ; malgré son nom, cette valeur n'est pas une "
         "profondeur (notion 3.5)"),
    ])],
    [
        ("lecture", "<code>self.readout</code>", "la ligne de texte sous le graphique, remplie par "
         "<code>setText()</code> (notion 1.5)"),
    ],
    ["widget, fenêtre", "parent, enfant", "signal, slot", "accesseur, mutateur", "contrôle",
     "sélecteur numérique", "case à cocher", "liste déroulante", "bouton", "minuteur"],
    library="PyQtGraph",
)

# Objectifs de chaque chapitre, sans aucun détail technique.
_Chapter1Introduction = (
    "Ce chapitre couvre les graphiques de données en deux dimensions. Quelques mots reviennent "
    "dans tout le guide. Un <b>graphique</b> montre une <b>zone visible</b> des données, avec "
    "ses <b>axes</b> et sa <b>légende</b>. On y ajoute des <b>éléments graphiques</b>, comme "
    "une <b>courbe</b> ou un <b>nuage de points</b>, tracés avec un <b>stylo</b> et remplis "
    "avec un <b>pinceau</b>. Le chapitre trace des courbes et des mesures avec leurs "
    "incertitudes, fait réagir un graphique à la souris, l'anime en temps réel, compose une "
    "figure de plusieurs graphiques et résume des mesures répétées. Il finit par la vue elle-même, "
    "qu'on pilote, et par les signaux qu'un graphique émet. L'objectif est de savoir "
    "construire un graphique clair, interactif et fidèle aux données."
)
_Chapter2Introduction = (
    "Ce chapitre passe des courbes aux figures et aux champs. Quelques mots s'ajoutent. Un "
    "<b>polygone</b> est une forme fermée, donnée par ses sommets. Une <b>série de "
    "polygones</b> est un groupe de polygones qu'on transforme ensemble, d'un coup. Une "
    "<b>grandeur</b> du plan prend une valeur en chaque point, comme la température d'une "
    "plaque. Un <b>champ de vecteurs</b> place une flèche en chaque point, comme le vent sur "
    "une carte. Le chapitre dessine des polygones et des flèches, les tourne, les agrandit et "
    "les déplace, transforme toute une série d'un coup, puis montre une grandeur et un champ de "
    "vecteurs. L'objectif est de savoir représenter une géométrie ou un phénomène qui occupe "
    "tout le plan, et non une seule courbe."
)
_Chapter3Introduction = (
    "Ce chapitre introduit la visualisation en trois dimensions : se repérer dans une scène "
    "et déplacer la caméra, représenter une trajectoire, une surface, un champ de vecteurs "
    "dans l'espace, puis un volume. L'objectif est de comprendre quand la troisième dimension "
    "apporte une information qu'un graphique plan ne montre pas."
)

# Images d'illustration des pages d'introduction : toujours une source externe (Wikimedia
# Commons), jamais produite localement (voir le docstring de QChapterIntroTab).
# La page « Introduction » : des champs nommés, mis en forme par QWalkthroughWindow.
_IntroductionHook = (
    "Une courbe qui défile en temps réel, des flèches qui couvrent tout un plan, une surface en "
    "3D qu'on fait tourner à la souris. Ce guide vous apprend à visualiser des données avec "
    "PyQtGraph."
)
_IntroductionMotivation = (
    "PyQtGraph est une bibliothèque de graphiques scientifiques pour Python, bâtie sur Qt. Elle "
    "est conçue pour la vitesse : un graphique se met à jour assez vite pour suivre une mesure "
    "en direct. On la rencontre en laboratoire, en instrumentation et en simulation, partout "
    "où il faut voir des données pendant qu'elles arrivent. Ses graphiques sont des widgets "
    "Qt : ils prennent place dans une interface comme un bouton."
)
_IntroductionAudience = (
    "Ce guide s'adresse à qui sait programmer en Python, connaît les bases de numpy et a déjà "
    "construit une petite interface avec Qt. Il ne suppose aucune connaissance de PyQtGraph."
)
_IntroductionOutcomes = [
    "tracer des courbes et des nuages de points, avec leurs axes, leur légende et leurs "
    "incertitudes ;",
    "rendre un graphique interactif, piloter sa vue, réagir à ses signaux, et l'animer en temps "
    "réel ;",
    "composer une figure de plusieurs graphiques, et résumer des mesures répétées ;",
    "représenter une figure, une grandeur ou un champ de vecteurs dans tout le plan ;",
    "construire une scène en 3D : trajectoire, surface, champ de vecteurs et volume.",
]
_IntroductionFurtherReading = [
    f'<a href="{pyqtgraphDocUrl("index")}">La documentation de PyQtGraph</a> (en anglais).',
    "La galerie d'exemples de PyQtGraph, qui s'ouvre par la commande "
    "<code>python -m pyqtgraph.examples</code> : chaque exemple s'exécute à côté de son code.",
]

# Une image par chapitre (skill, §6) : vérifiées par requête HTTP, avec leur auteur et leur licence.

# Synthèse de chaque chapitre (skill, §6) : chaque notion en une phrase, du recul, une ouverture.
_Chapter1Synthesis = (
    "<ul>"
    "<li><b>1.1</b> Un graphique (<code>PlotItem</code>, dans son widget "
    "<code>PlotWidget</code>) se titre, nomme ses axes et prépare "
    "sa légende ; ses courbes viennent de tableaux numpy.</li>"
    "<li><b>1.2</b> Un nuage de points garde chaque mesure isolée, et ses barres d'erreur "
    "montrent l'incertitude.</li>"
    "<li><b>1.3</b> Une courbe gardée dans un attribut se met à jour par <code>setData()</code>, "
    "et les éléments interactifs émettent des signaux.</li>"
    "<li><b>1.4</b> Un tampon de taille fixe et un minuteur font défiler des mesures en temps "
    "réel.</li>"
    "<li><b>1.5</b> Une grille de graphiques compose une figure ; ses axes se lient, et une "
    "échelle logarithmique change une exponentielle en droite.</li>"
    "<li><b>1.6</b> La moyenne, l'écart type et l'histogramme résument des mesures "
    "répétées.</li>"
    "<li><b>1.7</b> La zone visible se pilote : même échelle pour une carte, relief exagéré pour "
    "un profil, ajustement automatique axe par axe, souris limitée et bornes.</li>"
    "<li><b>1.8</b> Chaque axe passe en échelle logarithmique, où la zone visible compte en "
    "exposants ; chaque signal a un émetteur, un moment et des arguments.</li>"
    "</ul>"
    "Un graphique est un assemblage d'éléments graphiques. Celui qu'on veut changer ensuite est "
    "gardé dans un attribut, et se modifie sans que le reste soit redessiné : c'est la clé du "
    "temps réel et de "
    "l'interaction. La forme se choisit selon la donnée : une courbe pour une grandeur "
    "continue, un nuage pour des mesures isolées, des barres d'erreur pour une incertitude, un "
    "histogramme pour une distribution. Le graphique de Playfair, en 1786, montrait déjà deux "
    "courbes et l'écart entre elles, comme le remplissage entre deux courbes de la notion 1.3."
    "<br><br>Les deux dernières notions montrent l'autre face de l'interaction. La vue se règle "
    "par le code autant qu'à la souris, et chaque changement s'annonce par un signal. Le choix du "
    "signal compte : de la souris seule ou aussi du code, en direct ou à la fin du geste. Il évite "
    "les boucles, les échos et les calculs inutiles."
    "<br><br>PyQtGraph mise sur la vitesse et l'interaction. Pour une figure à publier, figée "
    "et soignée, matplotlib est la bibliothèque la plus répandue en Python. Les deux se "
    "complètent : l'une pour explorer et surveiller, l'autre pour imprimer."
    "<br><br>Tous ces objets viennent du cadre <i>Graphics View</i> de Qt. Le widget du "
    "graphique est un <code>QGraphicsView</code>, une fenêtre sur une scène. Le graphique et sa "
    "zone visible sont des <code>QGraphicsWidget</code>, et chaque élément graphique est un "
    "<code>QGraphicsObject</code>. Chaque élément hérite donc des méthodes et des signaux de Qt, "
    "comme <code>setParentItem()</code> (notion 1.7) ou <code>visibleChanged</code>. Pour aller "
    "plus loin : la vue d'ensemble du "
    f'<a href="{qtPageUrl("graphicsview")}">Graphics View Framework</a> de Qt, la section '
    f'<a href="{pyqtgraphDocUrl("getting_started/qtcrashcourse")}#graphicsview-and-graphicsitems">'
    "« GraphicsView and GraphicsItems »</a> du cours éclair de PyQtGraph, et son "
    f'<a href="{pyqtgraphDocUrl("api_reference/uml_overview")}">diagramme des classes</a>, qui '
    "montre cet héritage. Le chapitre 2 y entre par la scène, à la notion 2.4."
)
_Chapter2Synthesis = (
    "<ul>"
    "<li><b>2.1</b> Des flèches et un polygone rempli représentent des forces, et leur "
    "équilibre.</li>"
    "<li><b>2.2</b> Un élément graphique tourne, s'agrandit et se déplace ; derrière ces "
    "outils, une matrice de transformation.</li>"
    "<li><b>2.3</b> Une série de polygones, rangée sous un parent, se transforme, se cache et "
    "se nomme d'un coup.</li>"
    "<li><b>2.4</b> Une carte de chaleur montre une grandeur du plan par la couleur de chaque "
    "pixel.</li>"
    "<li><b>2.5</b> Un champ de vecteurs place une flèche en chaque point d'une grille, toutes "
    "dans un seul élément graphique.</li>"
    "</ul>"
    "Le chapitre passe d'un élément graphique à des milliers de valeurs : un polygone, une série "
    "de seize carrés, une image de milliers de pixels, un champ de flèches en un seul élément. "
    "Deux idées reviennent. La transformation agit sur l'affichage "
    "sans toucher aux données. Et le calcul se fait d'un coup sur une grille, avec numpy, "
    "jamais point par point. La couleur montre une valeur, la flèche une direction : les deux "
    "se superposent, comme le potentiel en fond du champ de la notion 2.5. La carte de Halley, "
    "en 1686, montrait déjà le vent par des traits orientés, un par lieu."
    "<br><br>Les cartes météo, l'écoulement de l'air autour d'une aile ou le champ électrique "
    "d'un circuit se représentent ainsi. La cartographie ajoute les projections, qui changent "
    "la sphère terrestre en plan : encore une transformation."
)
_Chapter3Synthesis = (
    "<ul>"
    "<li><b>3.1</b> Une scène 3D a besoin de repères, des axes et une grille, et d'une caméra "
    "décrite par sa distance, son élévation et son azimut.</li>"
    "<li><b>3.2</b> Une trajectoire sort du plan quand deux effets la dévient ; une flèche 3D "
    "s'assemble de formes simples.</li>"
    "<li><b>3.3</b> Une surface montre une grandeur du plan en relief : l'éclairage donne la "
    "forme, la couleur la hauteur.</li>"
    "<li><b>3.4</b> Un champ de vecteurs 3D trace toutes ses flèches dans un seul élément, "
    "colorées selon l'intensité.</li>"
    "<li><b>3.5</b> Un volume translucide montre une grandeur de l'espace, et une coupe en "
    "révèle l'intérieur.</li>"
    "</ul>"
    "La 3D montre ce qu'un plan ne peut pas montrer : une trajectoire qui sort du plan, un champ "
    "qui s'enroule, un volume. Mais elle cache aussi : une partie de la scène est toujours "
    "derrière une autre, et la profondeur se lit mal sur un écran plat. D'où la caméra qu'on "
    "tourne, et la coupe qui ramène au plan. Une bonne visualisation 3D offre toujours un "
    "retour au 2D. La surface de l'image ne se comprend bien qu'en la tournant."
    "<br><br>La même démarche sert l'imagerie médicale, où un scanner produit un volume qu'on "
    "explore par coupes, et la simulation numérique. Pour des scènes plus lourdes, des "
    "bibliothèques dédiées à la visualisation scientifique en 3D, comme VTK et son interface "
    "Python PyVista, vont plus loin."
)
_Chapter4Introduction = (
    "Ce dernier chapitre réunit les gestes du guide dans une seule page : un tableau de bord, "
    "qui surveille une plaque chauffée. Il n'apporte aucun geste nouveau. L'objectif est de "
    "savoir composer plusieurs graphiques qui répondent ensemble à une question, et de les "
    "tenir à jour."
)
_Chapter4Synthesis = (
    "<ul>"
    "<li><b>4.1</b> Un tableau de bord réunit une carte, un capteur en temps réel, un seuil "
    "d'alerte et des statistiques, mis à jour par un seul minuteur.</li>"
    "</ul>"
    "Un tableau de bord est une composition : chaque graphique répond à une question, et tous "
    "montrent le même instant. Le plus difficile n'est pas le code, mais le choix : quoi "
    "montrer, sous quelle forme, à quelle échelle. La carte de Minard, en 1869, en est "
    "l'exemple célèbre : la taille d'une armée, son chemin, sa direction et la température, "
    "réunis sur une seule image."
    "<br><br>Les tableaux de bord sont partout : salles de contrôle, laboratoires, suivi d'une "
    "usine ou d'un serveur. Les gestes du guide suffisent pour en construire un. Pour un vrai "
    "capteur, seule la façon d'obtenir chaque mesure change ; le tampon, le minuteur et les "
    "graphiques restent les mêmes."
)


def buildWindow() -> QWalkthroughWindow:
    """Construit la fenêtre complète, ses chapitres déclarés dans l'ordre.

    Utilisée aussi telle quelle par les tests (voir `learning_app/tests`).
    """
    window = QWalkthroughWindow("Visualiser des données avec PyQtGraph — Guide d'apprentissage")
    window.addIntroduction(
        hook=_IntroductionHook, motivation=_IntroductionMotivation, audience=_IntroductionAudience,
        outcomes=_IntroductionOutcomes,
        furtherReading=_IntroductionFurtherReading, imageUrl=_Images["introduction"].path,
        imageCaption=_Images["introduction"].caption, library="PyQtGraph")
    window.addGlossary(_Glossary)
    window.addChapter("Chapitre 1 — Graphiques 2D", _Chapter1Introduction,
                      [QTopicLinesTab, QTopicScatterTab, QTopicInteractionTab, QTopicRealTimeTab,
                       QTopicLayoutTab, QTopicStatisticsTab, QTopicViewTab, QTopicSignalsTab],
                      imageUrl=_Images["chapter1"].path, imageCaption=_Images["chapter1"].caption,
                      synthesis=_Chapter1Synthesis, synthesisImageUrl=_Images["chapter1-synthesis"].path,
                      synthesisImageCaption=_Images["chapter1-synthesis"].caption,
                      prerequisites=["classes et méthodes", "listes et tuples", "boucles", "f-strings",
                                     "annotations de type",
                                     "modules et imports", "module math", "numpy de base",
                                     "application et widget", "layouts courants", "signaux et slots",
                                     "accesseur et mutateur", "constantes Qt", "QLabel", "QPushButton",
                                     "QCheckBox", "QSlider", "QTimer", "QFileDialog", "QPointF",
                                     "QComboBox", "QSplitter", "Slot", "dictionnaires"],
                      summary="courbes, nuages de points, interaction, temps réel, statistiques, vue et "
                              "signaux")
    window.addChapter("Chapitre 2 — Géométrie et champs", _Chapter2Introduction,
                      [QTopicPolygonsTab, QTopicTransformationsTab, QTopicPolygonSeriesTab, QTopicHeatMapTab,
                       QTopicVectorFieldTab],
                      imageUrl=_Images["chapter2"].path, imageCaption=_Images["chapter2"].caption,
                      synthesis=_Chapter2Synthesis, synthesisImageUrl=_Images["chapter2-synthesis"].path,
                      synthesisImageCaption=_Images["chapter2-synthesis"].caption,
                      prerequisites=["compréhensions de liste", "trigonométrie", "matrices de transformation",
                                     "QRectF"],
                      summary="figures, transformations, séries de polygones, grandeurs et champs dans le plan")
    window.addChapter("Chapitre 3 — Visualisation 3D", _Chapter3Introduction,
                      [QTopicSceneTab, QTopicProjectileTab, QTopicSurfaceTab, QTopicVectorField3DTab,
                       QTopicVolumeTab],
                      imageUrl=_Images["chapter3"].path, imageCaption=_Images["chapter3"].caption,
                      synthesis=_Chapter3Synthesis, synthesisImageUrl=_Images["chapter3-synthesis"].path,
                      synthesisImageCaption=_Images["chapter3-synthesis"].caption,
                      prerequisites=["coordonnées dans l'espace", "QWidget", "QVector3D"],
                      summary="scènes, trajectoires, surfaces, champs et volumes")
    window.addChapter("Chapitre 4 — Synthèse", _Chapter4Introduction, [QTopicDashboardTab],
                      imageUrl=_Images["chapter4"].path, imageCaption=_Images["chapter4"].caption,
                      synthesis=_Chapter4Synthesis, synthesisImageUrl=_Images["chapter4-synthesis"].path,
                      synthesisImageCaption=_Images["chapter4-synthesis"].caption,
                      summary="un tableau de bord qui réunit les gestes du guide")
    return window


def main() -> int:
    return runWalkthroughApplication(buildWindow)
