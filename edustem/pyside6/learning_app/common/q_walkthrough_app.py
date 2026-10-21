"""Fenêtre principale partagée par toutes les applications de `learning_app`.

`QWalkthroughWindow` assemble les chapitres et leurs notions. À gauche, un
arbre de navigation à trois niveaux : un nœud par chapitre, ses notions en
enfants, numérotées « <chapitre>.<rang> », et les étapes de chaque notion en
petits-enfants. Deux boutons sous l'arbre affichent ou masquent d'un coup le
niveau des étapes. À droite, la page sélectionnée : l'introduction d'un
chapitre, ou une notion. Une page « Introduction », de structure fixe,
précède le premier chapitre. Deux pages annexes, consultées au besoin,
suivent le dernier chapitre : « Prérequis », construite à partir des
déclarations des chapitres, puis « Glossaire », facultative. Un projet n'a
plus qu'à déclarer son introduction, son glossaire et ses chapitres (voir
`main.py` de chaque projet).

Une fenêtre qui contient un widget OpenGL (les vues 3D) prend une taille
fixe : sous Windows, la redimensionner en tirant son bord la redessine
lentement à chaque pas. Un menu sous l'arbre en choisit la taille.

`runWalkthroughApplication` crée la `QApplication`, affiche la fenêtre et
lance la boucle d'événements, avec `faulthandler` actif : un plantage au
niveau C++ affiche alors une trace au lieu de fermer l'application en
silence.

Texte d'interface en français, sans `tr()` (exception déclarée dans le skill
`interactive-walkthrough-app`, §10).
"""

from __future__ import annotations

import ctypes
import faulthandler
import sys
from collections.abc import Callable, Sequence
from typing import NamedTuple, override

from PySide6.QtCore import QByteArray, QEvent, QSize, Qt, QTimer, Slot
from PySide6.QtGui import QAction, QImage, QKeySequence, QScreen, QShowEvent
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFrame, QHBoxLayout, QMainWindow, QMenu, QMessageBox, QPushButton, QSplitter,
    QStackedWidget, QStyle, QToolButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)
from shiboken6 import isValid

from .prerequisites import prerequisitesTableHtml
from .q_step_walkthrough import (
    QImageCaption, QChapterIntroTab, QChapterSynthesisPage, QGlossaryPage, QIntroductionPage,
    QPrerequisitesPage, QStepWalkthrough,
)


class QWalkthroughWindow(QMainWindow):
    """Fenêtre principale d'une application d'apprentissage par étapes.

    Chapitres:
        Déclarés par `addChapter()`, dans l'ordre. La numérotation
        « <chapitre>.<rang> » des notions en découle : jamais un numéro écrit
        à la main dans `TabTitle`. Chaque classe de notion définit les
        attributs de classe `TabTitle` et `TabToolTip` (str), et un attribut
        d'instance `walkthrough` (`QStepWalkthrough`). Chaque chapitre
        déclare ses prérequis, chacun une seule fois dans l'application, et
        un résumé d'une ligne, repris par l'introduction. `chapterItems()`
        rend les nœuds des chapitres ; `chapterSummary()` le résumé d'un
        chapitre.

    Introduction:
        `addIntroduction()` ajoute la page « Introduction », toujours la
        première de l'arbre, quel que soit l'ordre des appels
        (`introductionItem()`). La fenêtre s'ouvre alors sur elle, et non
        plus sur le premier chapitre. Sa navigation mène au premier
        chapitre.

    Annexes:
        Placées après le dernier chapitre, quel que soit l'ordre des appels.
        Elles ne comptent pas parmi les chapitres : ni numéro, ni navigation
        entre chapitres ; seul l'arbre y mène. La page « Prérequis » existe
        dès qu'un chapitre déclare un prérequis : une grille de tous les
        prérequis, avec le chapitre qui emploie chacun en premier
        (`prerequisitesItem()`). `addGlossary()` ajoute la page
        « Glossaire », toujours la dernière (`glossaryItem()`).

    Arbre de navigation:
        `navigationTree()` le rend ; `pageOf()` donne la page d'un nœud. Les
        étapes, troisième niveau, sont masquées au départ
        (`showSteps()`, `hideSteps()`, `stepsVisible()`). Sélectionner une
        étape affiche sa notion à cette étape ; changer d'étape depuis le
        panneau sélectionne l'étape dans l'arbre, ou la notion quand les
        étapes sont masquées. L'arbre et les pages partagent un séparateur.

    Synthèses:
        Un chapitre peut se fermer par une page de synthèse
        (`addChapter(synthesis=…)`), son dernier nœud, après ses notions.
        `topicItems()` rend les nœuds des notions d'un chapitre, sans la
        synthèse ; `synthesisItem()` le nœud de la synthèse.

    Navigation entre notions et chapitres:
        Elle suit l'ordre de lecture de toute l'application : les notions,
        et la synthèse de chaque chapitre après sa dernière notion. La
        navigation entre chapitres mène à la page d'introduction du
        chapitre visé. La disponibilité des boutons est réévaluée après
        chaque `addChapter()`.

    Taille de la fenêtre:
        Dès qu'une notion ajoutée contient un `QOpenGLWidget`, la fenêtre
        passe en taille fixe (`fixedSizeEnabled()`). Sous Windows, ce widget
        fait composer toute la fenêtre en OpenGL, même sur une page cachée,
        et chaque pas d'un redimensionnement par le bord devient lent. La
        taille voulue (`windowSize()`, `setWindowSize()`) part de
        `PreferredSize` ; elle est bornée par la zone disponible de l'écran,
        et réappliquée à chaque changement d'écran, d'échelle ou de zone
        disponible. Un bouton à menu sous l'arbre (`windowSizeButton()`)
        propose `SizePresets`, `fitToScreen()` et le plein écran
        (`setFullScreen()`, `fullScreenAction()`, raccourci standard F11).
        La case `freeResizingCheckBox()` lève la contrainte
        (`setFreeResizing()`) ; la décocher fixe la taille courante. Le
        petit bouton « ? », au bout de sa rangée (`windowSizeHelpButton()`), ouvre une
        fenêtre d'information sur la taille fixe (`showWindowSizeHelp()`).
        Maximiser la fenêtre la fait remplir l'écran, sa taille fixe revient
        au rétablissement. Glisser sa barre de titre jusqu'en haut de
        l'écran la maximise aussi ; sur un côté, l'ancre sur une moitié
        d'écran, qui devient la taille voulue. Sans widget OpenGL, rien de
        cela n'existe : ni commande, ni contrainte.

    Slots:
        showSteps(), hideSteps(), setWindowSize(), fitToScreen(),
        setFullScreen(), setFreeResizing(), showWindowSizeHelp().
    """

    PreferredSize = QSize(1500, 850)
    """Taille voulue au démarrage, bornée par l'écran."""

    SizePresets = (QSize(1280, 720), QSize(1440, 810), QSize(1600, 900), QSize(1920, 1080))
    """Tailles prédéfinies du menu « Taille de la fenêtre… »."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        """Initialise une fenêtre vide, sans aucun chapitre.

        Args:
            title: Titre de la fenêtre.
            parent: Widget parent, ou None.
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(self.PreferredSize)

        self._navigationTree: QTreeWidget = QTreeWidget()
        self._navigationTree.setHeaderHidden(True)
        self._navigationTree.setUniformRowHeights(True)
        # Reduced per-level indentation (30 px with the windows11 style): the tree stays narrow,
        # even on three levels.
        self._navigationTree.setIndentation(12)
        self._navigationTree.currentItemChanged.connect(self._showItemPage)

        self._showStepsButton: QPushButton = QPushButton("Afficher les étapes")
        self._showStepsButton.clicked.connect(self.showSteps)
        self._hideStepsButton: QPushButton = QPushButton("Masquer les étapes")
        self._hideStepsButton.clicked.connect(self.hideSteps)
        stepsRow = QHBoxLayout()
        stepsRow.addWidget(self._showStepsButton)
        stepsRow.addWidget(self._hideStepsButton)

        navigationPane = QWidget()
        navigationLayout = QVBoxLayout(navigationPane)
        # No margin around the tree, but the style's bottom margin under the buttons: without it,
        # their lower border touches the window edge and is clipped (windows11 style).
        bottomMargin = navigationPane.style().pixelMetric(QStyle.PixelMetric.PM_LayoutBottomMargin)
        navigationLayout.setContentsMargins(0, 0, 0, bottomMargin)
        navigationLayout.addWidget(self._navigationTree, 1)
        navigationLayout.addLayout(stepsRow)

        sizeMenu = QMenu(self)
        sizeMenu.setToolTipsVisible(True)
        self._sizePresetActions: list[QAction] = []
        for size in self.SizePresets:
            action = sizeMenu.addAction(f"{size.width()} × {size.height()}")
            action.triggered.connect(lambda _checked=False, size=size: self.setWindowSize(size))
            self._sizePresetActions.append(action)
        sizeMenu.addSeparator()
        sizeMenu.addAction("Ajuster à l'écran").triggered.connect(self.fitToScreen)
        self._fullScreenAction: QAction = QAction("Plein écran", self)
        self._fullScreenAction.setCheckable(True)
        self._fullScreenAction.setShortcut(QKeySequence.StandardKey.FullScreen)
        self._fullScreenAction.toggled.connect(self.setFullScreen)
        sizeMenu.addAction(self._fullScreenAction)
        sizeMenu.aboutToShow.connect(self._refreshSizePresets)
        self._windowSizeButton: QPushButton = QPushButton("Taille de la fenêtre…")
        self._windowSizeButton.setToolTip("Choisir la taille de la fenêtre, ou passer en plein écran (F11)")
        self._windowSizeButton.setMenu(sizeMenu)
        self._freeResizingCheckBox: QCheckBox = QCheckBox("Redimensionnement libre")
        # Plain text with explicit line breaks: the tooltip takes the width of its longest line, where
        # Qt would wrap rich text into a narrow column.
        self._freeResizingCheckBox.setToolTip(
            "Permet de redimensionner la fenêtre en tirant son bord.\n\n"
            "Les vues 3D (OpenGL) de cette application rendent ce geste lent,\n"
            "même quand aucune n'est affichée. Le bouton « ? » explique pourquoi.")
        self._freeResizingCheckBox.toggled.connect(self.setFreeResizing)
        self._windowSizeHelpButton: QToolButton = QToolButton()
        self._windowSizeHelpButton.setText("?")
        self._windowSizeHelpButton.setToolTip("Pourquoi la taille de la fenêtre est fixe")
        self._windowSizeHelpButton.setAccessibleName("Aide sur la taille de la fenêtre")
        self._windowSizeHelpButton.clicked.connect(self.showWindowSizeHelp)
        self._windowSizeHelp: QMessageBox | None = None
        freeResizingRow = QHBoxLayout()
        freeResizingRow.addWidget(self._freeResizingCheckBox)
        freeResizingRow.addStretch()
        freeResizingRow.addWidget(self._windowSizeHelpButton)
        # Hidden unless a topic holds an OpenGL widget. Stacked rather than side by side: on one row,
        # they would widen the navigation pane by about 60 px.
        self._sizeRow: QWidget = QWidget()
        sizeRowLayout = QVBoxLayout(self._sizeRow)
        sizeRowLayout.setContentsMargins(0, 0, 0, 0)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        sizeRowLayout.addWidget(separator)
        sizeRowLayout.addWidget(self._windowSizeButton)
        sizeRowLayout.addLayout(freeResizingRow)
        self._sizeRow.hide()
        navigationLayout.addWidget(self._sizeRow)

        self._pages: QStackedWidget = QStackedWidget()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(navigationPane)
        splitter.addWidget(self._pages)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 10_000])
        self.setCentralWidget(splitter)

        # Every chapter, then every topic, in the reading order of the application.
        self._chapters: list[QWalkthroughWindow._ChapterLocation] = []
        self._topics: list[QWalkthroughWindow._TopicLocation] = []
        self._introductionItem: QTreeWidgetItem | None = None
        self._introductionPage: QIntroductionPage | None = None
        self._glossaryItem: QTreeWidgetItem | None = None
        self._prerequisitesItem: QTreeWidgetItem | None = None
        self._prerequisitesPage: QPrerequisitesPage | None = None
        self._stepsVisible: bool = False
        self._updateStepsButtons()

        self._fixedSizeEnabled: bool = False
        self._freeResizing: bool = False
        self._windowSize: QSize = QSize(self.PreferredSize)
        self._watchedScreen: QScreen | None = None
        self._sizeBeforeTitleBarDrag: QSize | None = None
        # Screen and state changes arrive in bursts: one delayed pass applies the size after them.
        self._sizeConstraintTimer: QTimer = QTimer(self)
        self._sizeConstraintTimer.setSingleShot(True)
        self._sizeConstraintTimer.setInterval(self._SizeConstraintDelay)
        self._sizeConstraintTimer.timeout.connect(self._applySizeConstraint)

    # ====== API : arbre de navigation ======

    def navigationTree(self) -> QTreeWidget:
        """L'arbre de navigation : chapitres, notions en enfants, étapes en petits-enfants."""
        return self._navigationTree

    def pageOf(self, item: QTreeWidgetItem) -> QWidget:
        """La page affichée quand `item` est sélectionné : l'introduction d'un chapitre, ou une notion.

        Une étape rend la page de sa notion.
        """
        page = self._pages.widget(item.data(0, self._PageIndexRole))
        assert page is not None
        return page

    def stepsVisible(self) -> bool:
        """`True` si le niveau des étapes est affiché dans l'arbre."""
        return self._stepsVisible

    @Slot()
    def showSteps(self) -> None:
        """Affiche les étapes de toutes les notions, et sélectionne l'étape courante."""
        self._setStepsVisible(True)

    @Slot()
    def hideSteps(self) -> None:
        """Masque les étapes de toutes les notions."""
        self._setStepsVisible(False)

    # ====== API : chapitres ======

    def chapterItems(self) -> list[QTreeWidgetItem]:
        """Les nœuds des chapitres, dans l'ordre, sans ceux des annexes."""
        return [chapter.item for chapter in self._chapters]

    def chapterSummary(self, chapterItem: QTreeWidgetItem) -> str:
        """Le résumé d'une ligne d'un chapitre, tel que déclaré à `addChapter()`."""
        return self._chapterOf(chapterItem).summary

    def topicItems(self, chapterItem: QTreeWidgetItem) -> list[QTreeWidgetItem]:
        """Les nœuds des notions d'un chapitre, dans l'ordre, sans celui de sa synthèse."""
        return [location.item for location in self._topicsOf(chapterItem)]

    def synthesisItem(self, chapterItem: QTreeWidgetItem) -> QTreeWidgetItem | None:
        """Le nœud de la synthèse d'un chapitre, ou None s'il n'en a pas."""
        return self._chapterOf(chapterItem).synthesisItem

    def addChapter(self, chapterTitle: str, introduction: str, topicClasses: Sequence[type[QWidget]], *,
                   imageUrl: str = "", prerequisites: Sequence[str] = (), image: QImage | None = None,
                   imageCaption: QImageCaption | None = None, summary: str = "", synthesis: str = "",
                   synthesisImage: QImage | None = None, synthesisImageUrl: str = "",
                   synthesisImageCaption: QImageCaption | None = None) -> QTreeWidgetItem:
        """Ajoute un chapitre : sa page d'introduction, ses notions, puis sa synthèse.

        Args:
            chapterTitle: Titre du chapitre, affiché sur son nœud.
            introduction: Objectifs du chapitre en HTML simple, sans détail
                technique.
            topicClasses: Classes de notions du chapitre, dans l'ordre.
            imageUrl: Chemin local (`image_assets.py`) ou URL externe d'une
                image d'illustration, ou vide.
            prerequisites: Clés de `learning_app/assets/prerequis.md` que le
                chapitre emploie pour la première fois dans l'application,
                réunies dans la page « Prérequis ».
            image: Image d'illustration produite par le sujet lui-même,
                prioritaire sur `imageUrl`, ou None.
            imageCaption: Légende de l'image (`QImageCaption`), obligatoire avec une image.
            summary: Le chapitre en une ligne, sans détail technique, repris
                par « Ce que couvre le guide » de l'introduction ; ou vide.
            synthesis: Le texte de la page de synthèse, en HTML simple ;
                vide : le chapitre n'a pas de synthèse.
            synthesisImage, synthesisImageUrl, synthesisImageCaption: L'image
                de la synthèse et sa légende, comme celles de
                l'introduction du chapitre.

        Returns:
            Le nœud du chapitre dans l'arbre.

        Raises:
            KeyError: Un prérequis n'est pas dans `assets/prerequis.md`.
            ValueError: Un prérequis est répété, ou déjà déclaré par un
                chapitre précédent ; une image n'a pas de légende ; une
                synthèse n'a pas d'image.
        """
        declaredBefore = {key for chapter in self._chapters for key in chapter.introduction.prerequisites()}
        alreadyDeclared = sorted(declaredBefore.intersection(prerequisites))
        if alreadyDeclared:
            raise ValueError(f"prerequisites already declared by an earlier chapter: {alreadyDeclared}")
        chapterNumber = len(self._chapters) + 1
        topicTitles = [
            f"{chapterNumber}.{rank} {_textAttribute(topicClass, 'TabTitle')}"
            for rank, topicClass in enumerate(topicClasses, start=1)
        ]

        chapterItem = QTreeWidgetItem([chapterTitle])
        chapterItem.setToolTip(0, f"Introduction : {chapterTitle}")
        font = chapterItem.font(0)
        font.setBold(True)
        chapterItem.setFont(0, font)
        introductionPage = QChapterIntroTab(chapterTitle, introduction, topicTitles, imageUrl,
                                            prerequisites=prerequisites, image=image,
                                            imageCaption=imageCaption)
        chapterItem.setData(0, self._PageIndexRole, self._pages.addWidget(introductionPage))
        # Chapters come after the introduction and before the annexes, whatever the order of the
        # calls.
        self._navigationTree.insertTopLevelItem(self._firstChapterRow() + len(self._chapters), chapterItem)

        synthesisPage: QChapterSynthesisPage | None = None
        synthesisItem: QTreeWidgetItem | None = None
        if synthesis:
            synthesisPage = QChapterSynthesisPage(chapterTitle, synthesis, image=synthesisImage,
                                                  imageUrl=synthesisImageUrl,
                                                  imageCaption=synthesisImageCaption)
            synthesisItem = self._annexItem(QChapterSynthesisPage.Title, f"Synthèse : {chapterTitle}",
                                            synthesisPage)
        self._chapters.append(QWalkthroughWindow._ChapterLocation(introductionPage, chapterItem, summary, synthesisPage,
                                               synthesisItem))

        navigation = introductionPage.navigation
        navigation.previousTopicRequested.connect(lambda: self._goToLastStopBefore(chapterItem))
        navigation.nextTopicRequested.connect(lambda: self._goToFirstTopicOf(chapterItem))
        navigation.previousChapterRequested.connect(lambda: self._goToAdjacentChapterOf(chapterItem, -1))
        navigation.nextChapterRequested.connect(lambda: self._goToAdjacentChapterOf(chapterItem, 1))

        for topicTitle, topicClass in zip(topicTitles, topicClasses):
            self._addTopic(chapterItem, topicClass, topicTitle)

        if synthesisPage is not None and synthesisItem is not None:
            chapterItem.addChild(synthesisItem)
            synthesisNavigation = synthesisPage.navigation
            synthesisNavigation.previousTopicRequested.connect(lambda: self._goToAdjacentStop(synthesisItem, -1))
            synthesisNavigation.nextTopicRequested.connect(lambda: self._goToAdjacentStop(synthesisItem, 1))
            synthesisNavigation.previousChapterRequested.connect(
                lambda: self._goToAdjacentChapterOf(chapterItem, -1))
            synthesisNavigation.nextChapterRequested.connect(lambda: self._goToAdjacentChapterOf(chapterItem, 1))

        chapterItem.setExpanded(True)
        if len(self._chapters) == 1 and self._introductionItem is None:
            self._navigationTree.setCurrentItem(chapterItem)
        self._refreshNavigationAvailability()
        self._refreshPrerequisites()
        self._refreshIntroduction()
        return chapterItem

    # ====== API : introduction ======

    def introductionItem(self) -> QTreeWidgetItem | None:
        """Le nœud de la page « Introduction », ou None sans introduction."""
        return self._introductionItem

    def addIntroduction(self, *, hook: str, motivation: str, audience: str,
                        outcomes: Sequence[str], furtherReading: Sequence[str] = (),
                        image: QImage | None = None, imageUrl: str = "",
                        imageCaption: QImageCaption | None = None, library: str = "Qt") -> QTreeWidgetItem:
        """Ajoute la page « Introduction », toujours la première de l'arbre, et l'affiche.

        Champs nommés plutôt qu'un HTML libre : la page a la même structure
        dans toutes les applications (`QIntroductionPage`). La liste des
        chapitres, les usages du guide et le texte « Comment se servir du
        guide » ne se déclarent pas : la première vient des chapitres
        (`summary` de `addChapter()`), les deux autres sont communs.

        Args:
            hook, motivation, audience, outcomes, furtherReading,
            image, imageUrl, imageCaption, library: Voir `QIntroductionPage`.

        Returns:
            Le nœud de l'introduction dans l'arbre.

        Raises:
            ValueError: L'application a déjà une introduction, ou
                `outcomes` est vide.
        """
        if self._introductionItem is not None:
            raise ValueError("this window already has an introduction")
        page = QIntroductionPage(hook=hook, motivation=motivation, audience=audience,
                                 outcomes=outcomes, furtherReading=furtherReading, image=image,
                                 imageUrl=imageUrl, imageCaption=imageCaption, library=library)
        item = self._annexItem(QIntroductionPage.Title, "Ce que propose ce guide, et comment s'en servir",
                               page)
        self._navigationTree.insertTopLevelItem(0, item)
        self._introductionItem = item
        self._introductionPage = page
        page.navigation.nextTopicRequested.connect(self._goToFirstTopic)
        page.navigation.nextChapterRequested.connect(self._goToFirstChapter)
        self._refreshNavigationAvailability()
        self._refreshIntroduction()
        self._navigationTree.setCurrentItem(item)
        return item

    # ====== API : annexes ======

    def prerequisitesItem(self) -> QTreeWidgetItem | None:
        """Le nœud de la page « Prérequis », ou None tant qu'aucun chapitre n'en déclare."""
        return self._prerequisitesItem

    def glossaryItem(self) -> QTreeWidgetItem | None:
        """Le nœud de la page « Glossaire », ou None sans glossaire."""
        return self._glossaryItem

    def addGlossary(self, html: str) -> QTreeWidgetItem:
        """Ajoute la page « Glossaire », toujours la dernière de l'arbre.

        La fenêtre ne s'ouvre jamais sur le glossaire : elle s'ouvre sur
        l'introduction de l'application, à défaut sur celle du premier
        chapitre.

        Args:
            html: Contenu de la page en HTML simple : les termes employés
                par l'application, typiquement en tableau.

        Returns:
            Le nœud du glossaire dans l'arbre.

        Raises:
            ValueError: L'application a déjà un glossaire.
        """
        if self._glossaryItem is not None:
            raise ValueError("this window already has a glossary")
        glossaryItem = self._annexItem(QGlossaryPage.Title, "Les termes employés dans cette application",
                                       QGlossaryPage(html))
        self._insertKeepingSelection(self._navigationTree.topLevelItemCount(), glossaryItem)
        self._glossaryItem = glossaryItem
        return glossaryItem

    # ====== API : taille de la fenêtre ======

    def fixedSizeEnabled(self) -> bool:
        """`True` dès qu'une notion contient un `QOpenGLWidget` : la fenêtre a alors une taille fixe."""
        return self._fixedSizeEnabled

    def windowSize(self) -> QSize:
        """La taille voulue, sans le cadre, en pixels logiques.

        La taille réelle peut être plus petite : elle est bornée par la zone
        disponible de l'écran. La taille voulue revient sur un écran assez
        grand.
        """
        return QSize(self._windowSize)

    @Slot(QSize)
    def setWindowSize(self, size: QSize) -> None:
        """Donne à la fenêtre la taille `size`, bornée par l'écran, et la ramène dans l'écran.

        Quitte d'abord le plein écran ou l'état maximisé. En redimensionnement
        libre, la taille n'est pas fixée.
        """
        self._windowSize = QSize(size)
        if self.isMaximized() or self.isFullScreen():
            self.showNormal()
        if self._fixedSizeEnabled and not self._freeResizing:
            self._applySizeConstraint()
        else:
            self.resize(size.boundedTo(self._room()))
            self._keepOnScreen()

    @Slot()
    def fitToScreen(self) -> None:
        """Donne à la fenêtre toute la zone disponible de l'écran, cadre compris, sans la maximiser."""
        if self.isMaximized() or self.isFullScreen():
            self.showNormal()
        self.setWindowSize(self._room())
        self.move(self.screen().availableGeometry().topLeft())

    @Slot(bool)
    def setFullScreen(self, fullScreen: bool) -> None:
        """Passe en plein écran, ou en sort : la taille d'avant revient."""
        if fullScreen == self.isFullScreen():
            return
        if fullScreen:
            self._releaseSize()
            self.showFullScreen()
        else:
            self.showNormal()
            self._sizeConstraintTimer.start()

    def freeResizing(self) -> bool:
        """`True` si la taille n'est pas fixée, même avec un widget OpenGL."""
        return self._freeResizing

    @Slot(bool)
    def setFreeResizing(self, free: bool) -> None:
        """Lève la taille fixe, ou la rétablit à la taille courante de la fenêtre."""
        if free == self._freeResizing:
            return
        self._freeResizing = free
        self._freeResizingCheckBox.setChecked(free)
        if not free and self.windowState() == Qt.WindowState.WindowNoState:
            self._windowSize = self.size()
        self._applySizeConstraint()

    def windowSizeButton(self) -> QPushButton:
        """Le bouton à menu « Taille de la fenêtre… », visible seulement en taille fixe."""
        return self._windowSizeButton

    def freeResizingCheckBox(self) -> QCheckBox:
        """La case « Redimensionnement libre », visible seulement en taille fixe."""
        return self._freeResizingCheckBox

    def fullScreenAction(self) -> QAction:
        """L'action cochable « Plein écran » du menu, et son raccourci standard (F11)."""
        return self._fullScreenAction

    def windowSizeHelpButton(self) -> QToolButton:
        """Le petit bouton « ? » à droite de la case, visible seulement en taille fixe."""
        return self._windowSizeHelpButton

    @Slot()
    def showWindowSizeHelp(self) -> None:
        """Ouvre, sans bloquer, la fenêtre d'information qui explique la taille fixe et ses commandes."""
        if self._windowSizeHelp is None:
            self._windowSizeHelp = QMessageBox(QMessageBox.Icon.Information, "Taille de la fenêtre",
                                               "<b>Pourquoi la taille de cette fenêtre est-elle fixe ?</b>",
                                               QMessageBox.StandardButton.Ok, self)
            self._windowSizeHelp.setInformativeText(self._WindowSizeHelpHtml)
        self._windowSizeHelp.open()

    # ====== Événements ======

    @override
    def showEvent(self, event: QShowEvent) -> None:
        # Fixing the size after the native window exists keeps its maximize button (see nativeEvent).
        super().showEvent(event)
        if self._fixedSizeEnabled and self._watchedScreen is None:
            self._watchScreen()
            self._applySizeConstraint()

    @override
    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() != QEvent.Type.WindowStateChange or not self._fixedSizeEnabled:
            return
        self._fullScreenAction.setChecked(self.isFullScreen())
        if self.isMaximized() and self._sizeLocked():
            # Maximized within its fixed size, the window would stay in a corner: only a maximize whose
            # constraint was lifted beforehand (nativeEvent) is kept.
            QTimer.singleShot(0, self.showNormal)
        self._sizeConstraintTimer.start()

    @override
    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.DevicePixelRatioChange and self._fixedSizeEnabled:
            self._sizeConstraintTimer.start()
        return super().event(event)

    @override
    def nativeEvent(self, eventType: QByteArray | bytes, message: int) -> tuple[bool, int]:
        """Sous Windows, lève la taille fixe juste avant une maximisation ou un glissement de la barre de titre.

        Windows maximise ou ancre une fenêtre dans ses bornes : levées
        d'abord, la fenêtre remplit l'écran ou sa moitié. Le bouton
        Agrandir, le double-clic sur la barre de titre et Windows + Haut
        passent par la commande système `SC_MAXIMIZE`. Un glissement de la
        barre de titre commence par `SC_MOVE` et finit par
        `WM_EXITSIZEMOVE` ; jusqu'en haut de l'écran, il maximise ; sur un
        côté, il ancre la fenêtre sur une moitié d'écran, et cette taille
        devient la taille voulue. `changeEvent` rétablit la taille fixe au
        retour à l'état normal.
        """
        if self._fixedSizeEnabled and bytes(eventType) == b"windows_generic_MSG":
            windowsMessage = QWalkthroughWindow._WindowsMessage.from_address(int(message))
            command = windowsMessage.wParam & 0xFFF0
            if windowsMessage.message == self._WmSysCommand and command in (self._ScMaximize, self._ScMove):
                if command == self._ScMove:
                    self._sizeBeforeTitleBarDrag = self.size()
                self._releaseSize()
            elif windowsMessage.message == self._WmExitSizeMove and self._sizeBeforeTitleBarDrag is not None:
                QTimer.singleShot(self._TitleBarSnapDelay, self._finishTitleBarDrag)
        return super().nativeEvent(eventType, message)

    # ====== Privé ======

    class _ChapterLocation(NamedTuple):
        """Un chapitre, pour la navigation : sa page d'introduction, son nœud, son résumé et sa synthèse."""

        introduction: QChapterIntroTab
        item: QTreeWidgetItem
        summary: str
        synthesis: QChapterSynthesisPage | None
        synthesisItem: QTreeWidgetItem | None

    class _TopicLocation(NamedTuple):
        """Une notion, pour la navigation : son panneau d'étapes et son nœud."""

        walkthrough: QStepWalkthrough
        item: QTreeWidgetItem

    class _WindowsMessage(ctypes.Structure):
        """Le début de la structure `MSG` de Windows, reçue par `nativeEvent`."""

        _fields_ = [("hwnd", ctypes.c_void_p), ("message", ctypes.c_uint), ("wParam", ctypes.c_size_t),
                    ("lParam", ctypes.c_ssize_t)]

    # Data roles carried by each tree item: the index of its page in the stack, and, for a step
    # only, its index within its topic.
    _PageIndexRole = Qt.ItemDataRole.UserRole
    _StepIndexRole = Qt.ItemDataRole.UserRole + 1

    _SizeConstraintDelay = 100  # ms
    _MaximumWidgetSize = (1 << 24) - 1  # QWIDGETSIZE_MAX, not exported by PySide6
    _WmSysCommand = 0x0112
    _WmExitSizeMove = 0x0232
    _ScMaximize = 0xF030
    _ScMove = 0xF010
    # Windows snaps a window dragged to a screen edge about 50 ms after the drag ends.
    _TitleBarSnapDelay = 400  # ms

    _WindowSizeHelpHtml = (
        "<p>Cette application affiche des vues 3D. Elles sont dessinées par OpenGL, l'interface qui "
        "confie le rendu à la carte graphique. Sous Windows, dès qu'une fenêtre contient une vue OpenGL, toute "
        "la fenêtre est composée par OpenGL, même quand la vue 3D est sur une page cachée.</p>"
        "<p>Dans ce mode, c'est la carte graphique qui assemble l'image de la fenêtre : les vues 3D, "
        "et l'image de chaque widget ordinaire, qui lui est transférée. À chaque changement de "
        "taille, ses surfaces de dessin doivent être recréées à la nouvelle taille, puis toute la "
        "fenêtre redessinée et transférée de nouveau. Un changement de taille coûte ainsi environ dix "
        "fois plus cher qu'à l'ordinaire : près d'une demi-seconde sur un portable courant.</p>"
        "<p>Tirer un bord de la fenêtre pour la redimensionner dynamiquement enchaîne des dizaines de "
        "changements de taille par seconde. La fenêtre ne peut pas suivre : elle se fige, puis "
        "rattrape la souris avec plusieurs secondes de retard. Les gestes qui ne changent pas la "
        "taille de la fenêtre restent rapides : déplacer le séparateur entre deux zones "
        "(<code>QSplitter</code>), ou déplacer et zoomer un graphique 2D ordinaire.</p>"
        "<p>Pour changer la taille d'un seul coup :</p>"
        "<ul>"
        "<li>le bouton « Taille de la fenêtre… » : tailles prédéfinies, ajustement à l'écran, plein "
        "écran (F11) ;</li>"
        "<li>le bouton Agrandir de la fenêtre, ou sa barre de titre glissée en haut ou sur un côté de "
        "l'écran.</li>"
        "</ul>"
        "<p>La case « Redimensionnement libre » permet l'ajustement dynamique de la fenêtre en tirant "
        "sur son bord, avec la lenteur décrite plus haut.</p>"
    )

    def _annexItem(self, title: str, toolTip: str, page: QWidget) -> QTreeWidgetItem:
        """Un nœud d'annexe, en italique, relié à sa page."""
        item = QTreeWidgetItem([title])
        item.setToolTip(0, toolTip)
        font = item.font(0)
        font.setItalic(True)
        item.setFont(0, font)
        item.setData(0, self._PageIndexRole, self._pages.addWidget(page))
        return item

    def _insertKeepingSelection(self, index: int, item: QTreeWidgetItem) -> None:
        """Insère un nœud de premier niveau sans changer la sélection courante."""
        current = self._navigationTree.currentItem()
        self._navigationTree.insertTopLevelItem(index, item)
        if current is not None:
            self._navigationTree.setCurrentItem(current)

    def _firstChapterRow(self) -> int:
        """La rangée du premier chapitre parmi les nœuds de premier niveau : 1 après une introduction."""
        return 0 if self._introductionItem is None else 1

    def _refreshIntroduction(self) -> None:
        """Met à jour la liste des chapitres de l'introduction, s'il y en a une."""
        if self._introductionPage is not None:
            self._introductionPage.setChapterSummaries(
                [(chapter.introduction.chapterTitle(), chapter.summary) for chapter in self._chapters])

    def _refreshPrerequisites(self) -> None:
        """Crée ou met à jour la page « Prérequis », juste après le dernier chapitre."""
        html = prerequisitesTableHtml([
            (chapter.introduction.chapterTitle().replace("Chapitre ", "", 1), chapter.introduction.prerequisites())
            for chapter in self._chapters
        ])
        if not html:
            return
        if self._prerequisitesPage is None:
            self._prerequisitesPage = QPrerequisitesPage(html)
            self._prerequisitesItem = self._annexItem(
                QPrerequisitesPage.Title, "Ce que cette application suppose connu", self._prerequisitesPage)
            self._insertKeepingSelection(self._firstChapterRow() + len(self._chapters),
                                         self._prerequisitesItem)
        else:
            self._prerequisitesPage.setPrerequisitesHtml(html)

    def _addTopic(self, chapterItem: QTreeWidgetItem, topicClass: type[QWidget], numberedTitle: str) -> None:
        """Instancie une notion, l'ajoute sous son chapitre avec ses étapes, et câble sa navigation."""
        topic = topicClass()
        pageIndex = self._pages.addWidget(topic)
        topicItem = QTreeWidgetItem([numberedTitle])
        topicItem.setToolTip(0, _textAttribute(topicClass, "TabToolTip"))
        topicItem.setData(0, self._PageIndexRole, pageIndex)
        chapterItem.addChild(topicItem)

        if topic.findChildren(QOpenGLWidget):
            self._enableFixedSize()

        walkthrough = getattr(topic, "walkthrough", None)
        assert isinstance(walkthrough, QStepWalkthrough), (
            f"{topicClass.__name__} must define a walkthrough instance attribute"
        )
        walkthrough.setTopicHeading(numberedTitle)

        stepTitles = walkthrough.stepTitles()
        for stepIndex, stepTitle in enumerate(stepTitles):
            stepItem = QTreeWidgetItem([stepTitle])
            stepItem.setToolTip(0, f"Étape {stepIndex + 1} / {len(stepTitles)} : {stepTitle}")
            stepItem.setData(0, self._PageIndexRole, pageIndex)
            stepItem.setData(0, self._StepIndexRole, stepIndex)
            topicItem.addChild(stepItem)
        topicItem.setExpanded(self._stepsVisible)

        location = QWalkthroughWindow._TopicLocation(walkthrough, topicItem)
        self._topics.append(location)

        walkthrough.stepChanged.connect(lambda _stepIndex: self._selectInTree(location))
        walkthrough.previousTopicRequested.connect(lambda: self._goToAdjacentStop(topicItem, -1))
        walkthrough.nextTopicRequested.connect(lambda: self._goToAdjacentStop(topicItem, 1))
        walkthrough.previousChapterRequested.connect(lambda: self._goToAdjacentChapter(walkthrough, -1))
        walkthrough.nextChapterRequested.connect(lambda: self._goToAdjacentChapter(walkthrough, 1))

    @Slot(QTreeWidgetItem, QTreeWidgetItem)
    def _showItemPage(self, current: QTreeWidgetItem | None, _previous: QTreeWidgetItem | None) -> None:
        if current is None:
            return
        self._pages.setCurrentIndex(current.data(0, self._PageIndexRole))
        stepIndex = current.data(0, self._StepIndexRole)
        if stepIndex is not None:
            walkthrough = self._pages.currentWidget().walkthrough
            # Selecting the step already shown replays nothing. This guard also breaks the loop
            # with _selectInTree, called back through the stepChanged signal.
            if walkthrough.currentStepIndex() != stepIndex:
                walkthrough.goToStep(stepIndex)

    def _selectInTree(self, location: QWalkthroughWindow._TopicLocation) -> None:
        """Sélectionne une notion dans l'arbre : son étape courante si les étapes sont affichées."""
        target = location.item
        if self._stepsVisible:
            target = location.item.child(location.walkthrough.currentStepIndex())
        if self._navigationTree.currentItem() is not target:
            self._navigationTree.setCurrentItem(target)

    def _setStepsVisible(self, visible: bool) -> None:
        self._stepsVisible = visible
        for location in self._topics:
            location.item.setExpanded(visible)

        # The selection follows: onto the current step when steps appear, onto the topic when
        # they disappear (a hidden step cannot stay selected).
        current = self._navigationTree.currentItem()
        for location in self._topics:
            if current is location.item or (current is not None and current.parent() is location.item):
                self._selectInTree(location)
        self._updateStepsButtons()

    def _updateStepsButtons(self) -> None:
        self._showStepsButton.setEnabled(not self._stepsVisible)
        self._hideStepsButton.setEnabled(self._stepsVisible)

    def _positionOf(self, walkthrough: QStepWalkthrough) -> int:
        return next(position for position, location in enumerate(self._topics)
                    if location.walkthrough is walkthrough)

    def _chapterOf(self, chapterItem: QTreeWidgetItem) -> QWalkthroughWindow._ChapterLocation:
        return next(chapter for chapter in self._chapters if chapter.item is chapterItem)

    def _chapterIndexOf(self, location: QWalkthroughWindow._TopicLocation) -> int:
        return self.chapterItems().index(location.item.parent())

    def _readingStops(self) -> list[QTreeWidgetItem]:
        """La suite de lecture de la navigation entre notions : les notions, puis la synthèse, chapitre par chapitre."""
        stops: list[QTreeWidgetItem] = []
        for chapter in self._chapters:
            stops += self.topicItems(chapter.item)
            if chapter.synthesisItem is not None:
                stops.append(chapter.synthesisItem)
        return stops

    def _goToStop(self, item: QTreeWidgetItem) -> None:
        """Affiche un nœud de la suite de lecture : une notion à son étape courante, ou une synthèse."""
        location = next((location for location in self._topics if location.item is item), None)
        if location is not None:
            self._selectInTree(location)
        else:
            self._navigationTree.setCurrentItem(item)

    def _goToAdjacentStop(self, item: QTreeWidgetItem, offset: int) -> None:
        stops = self._readingStops()
        target = stops.index(item) + offset
        if 0 <= target < len(stops):
            self._goToStop(stops[target])

    def _goToAdjacentChapter(self, walkthrough: QStepWalkthrough, offset: int) -> None:
        self._goToAdjacentChapterOf(self._topics[self._positionOf(walkthrough)].item.parent(), offset)

    def _goToAdjacentChapterOf(self, chapterItem: QTreeWidgetItem, offset: int) -> None:
        chapterItems = self.chapterItems()
        target = chapterItems.index(chapterItem) + offset
        if 0 <= target < len(chapterItems):
            self._navigationTree.setCurrentItem(chapterItems[target])

    def _topicsOf(self, chapterItem: QTreeWidgetItem) -> list[QWalkthroughWindow._TopicLocation]:
        return [location for location in self._topics if location.item.parent() is chapterItem]

    def _previousChapterOf(self, chapterItem: QTreeWidgetItem) -> QTreeWidgetItem | None:
        chapterItems = self.chapterItems()
        index = chapterItems.index(chapterItem)
        return chapterItems[index - 1] if index > 0 else None

    @Slot()
    def _goToFirstTopic(self) -> None:
        if self._topics:
            self._selectInTree(self._topics[0])

    @Slot()
    def _goToFirstChapter(self) -> None:
        if self._chapters:
            self._navigationTree.setCurrentItem(self._chapters[0].item)

    def _goToFirstTopicOf(self, chapterItem: QTreeWidgetItem) -> None:
        topics = self._topicsOf(chapterItem)
        if topics:
            self._selectInTree(topics[0])

    def _lastStopOf(self, chapterItem: QTreeWidgetItem | None) -> QTreeWidgetItem | None:
        """Le dernier nœud de lecture d'un chapitre : sa synthèse, à défaut sa dernière notion."""
        if chapterItem is None:
            return None
        synthesisItem = self.synthesisItem(chapterItem)
        if synthesisItem is not None:
            return synthesisItem
        topicItems = self.topicItems(chapterItem)
        return topicItems[-1] if topicItems else None

    def _goToLastStopBefore(self, chapterItem: QTreeWidgetItem) -> None:
        lastStop = self._lastStopOf(self._previousChapterOf(chapterItem))
        if lastStop is not None:
            self._goToStop(lastStop)

    def _refreshNavigationAvailability(self) -> None:
        """Active ou désactive les boutons de navigation entre notions et entre chapitres.

        Les pages d'introduction suivent la même logique : leur « notion
        suivante » est la première notion de leur chapitre, leur « notion
        précédente » la dernière du chapitre précédent.
        """
        chapterCount = len(self._chapters)
        stops = self._readingStops()
        lastStop = len(stops) - 1
        for location in self._topics:
            chapterIndex = self._chapterIndexOf(location)
            position = stops.index(location.item)
            location.walkthrough.setTopicNavigationAvailable(position > 0, position < lastStop)
            location.walkthrough.setChapterNavigationAvailable(chapterIndex > 0, chapterIndex < chapterCount - 1)
        for chapterIndex, chapter in enumerate(self._chapters):
            hasPreviousStop = self._lastStopOf(self._previousChapterOf(chapter.item)) is not None
            chapter.introduction.navigation.setTopicNavigationAvailable(hasPreviousStop,
                                                                         bool(self._topicsOf(chapter.item)))
            chapter.introduction.navigation.setChapterNavigationAvailable(chapterIndex > 0,
                                                                           chapterIndex < chapterCount - 1)
            if chapter.synthesis is not None and chapter.synthesisItem is not None:
                position = stops.index(chapter.synthesisItem)
                chapter.synthesis.navigation.setTopicNavigationAvailable(position > 0, position < lastStop)
                chapter.synthesis.navigation.setChapterNavigationAvailable(chapterIndex > 0,
                                                                            chapterIndex < chapterCount - 1)
        if self._introductionPage is not None:
            self._introductionPage.navigation.setTopicNavigationAvailable(False, bool(self._topics))
            self._introductionPage.navigation.setChapterNavigationAvailable(False, chapterCount > 0)

    def _enableFixedSize(self) -> None:
        """Passe en taille fixe : montre les commandes de taille et active le raccourci du plein écran."""
        if self._fixedSizeEnabled:
            return
        self._fixedSizeEnabled = True
        self._sizeRow.show()
        self.addAction(self._fullScreenAction)
        if self.isVisible():
            self._watchScreen()
            self._applySizeConstraint()

    def _watchScreen(self) -> None:
        """Suit les changements d'écran de la fenêtre, et ceux de la zone disponible de son écran."""
        window = self.windowHandle()
        assert window is not None
        window.screenChanged.connect(self._followScreen)
        self._followScreen(self.screen())

    @Slot(QScreen)
    def _followScreen(self, screen: QScreen) -> None:
        # An unplugged screen is already destroyed, its connections with it.
        if self._watchedScreen is not None and isValid(self._watchedScreen):
            self._watchedScreen.availableGeometryChanged.disconnect(self._scheduleSizeConstraint)
        self._watchedScreen = screen
        screen.availableGeometryChanged.connect(self._scheduleSizeConstraint)
        self._scheduleSizeConstraint()

    @Slot()
    def _finishTitleBarDrag(self) -> None:
        """Termine un glissement de la barre de titre : une taille donnée par un ancrage devient la taille voulue."""
        if self._sizeBeforeTitleBarDrag is None:
            return
        if self.windowState() == Qt.WindowState.WindowNoState and self.size() != self._sizeBeforeTitleBarDrag:
            self._windowSize = self.size()
        self._sizeBeforeTitleBarDrag = None
        self._applySizeConstraint()

    @Slot()
    def _scheduleSizeConstraint(self) -> None:
        self._sizeConstraintTimer.start()

    @Slot()
    def _applySizeConstraint(self) -> None:
        """Fixe la taille voulue, bornée par l'écran, ou lève la contrainte quand elle n'a pas lieu d'être."""
        if not self._fixedSizeEnabled or self.isMinimized():
            return
        titleBarDrag = self._sizeBeforeTitleBarDrag is not None
        if self._freeResizing or titleBarDrag or self.isMaximized() or self.isFullScreen():
            self._releaseSize()
            return
        size = self._windowSize.boundedTo(self._room())
        # After a scale change, Windows keeps the bounds converted at the previous scale. Bounds equal
        # to `size` would not be sent again: lift them first.
        self._releaseSize()
        self.setFixedSize(size)
        self._keepOnScreen()

    def _releaseSize(self) -> None:
        """Lève la taille fixe sans changer la taille : le minimum redevient celui du contenu, au plus la taille courante."""
        self.setMinimumSize(self.minimumSizeHint().boundedTo(self._room()).boundedTo(self.size()))
        self.setMaximumSize(self._MaximumWidgetSize, self._MaximumWidgetSize)

    def _sizeLocked(self) -> bool:
        return self.minimumSize() == self.maximumSize()

    def _room(self) -> QSize:
        """La plus grande taille dont le cadre tient dans la zone disponible de l'écran."""
        frame = self.frameGeometry().size() - self.size()
        return self.screen().availableGeometry().size() - frame

    def _keepOnScreen(self) -> None:
        """Ramène le cadre dans la zone disponible de l'écran, son coin supérieur gauche en priorité."""
        available = self.screen().availableGeometry()
        frame = self.frameGeometry()
        x = max(min(frame.x(), available.right() + 1 - frame.width()), available.left())
        y = max(min(frame.y(), available.bottom() + 1 - frame.height()), available.top())
        if (x, y) != (frame.x(), frame.y()):
            self.move(x, y)

    @Slot()
    def _refreshSizePresets(self) -> None:
        """Grise les tailles prédéfinies qui ne tiennent pas dans l'écran."""
        room = self._room()
        for action, size in zip(self._sizePresetActions, self.SizePresets):
            fits = size.width() <= room.width() and size.height() <= room.height()
            action.setEnabled(fits)
            action.setToolTip("" if fits else "Plus grande que l'écran")


def runWalkthroughApplication(buildWindow: Callable[[], QWalkthroughWindow]) -> int:
    """Crée l'application, affiche la fenêtre construite par `buildWindow`, et lance la boucle.

    `buildWindow` n'est appelée qu'après la création de la `QApplication`,
    condition pour instancier le moindre widget. Les tests appellent
    directement cette même fonction de construction.

    Returns:
        Le code de sortie de la boucle d'événements.
    """
    faulthandler.enable()
    app = QApplication.instance() or QApplication(sys.argv)
    window = buildWindow()
    window.show()
    return app.exec()


# ====== Privé ======



def _textAttribute(topicClass: type[QWidget], name: str) -> str:
    value = getattr(topicClass, name, None)
    assert isinstance(value, str), f"{topicClass.__name__} must define {name} as a str class attribute"
    return value
