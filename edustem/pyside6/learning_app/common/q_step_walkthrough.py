"""Panneau de navigation étape par étape, partagé par toutes les applications de `learning_app`.

Le panneau affiche un en-tête reprenant le titre complet de la notion, une
explication, le code réel de l'étape avec coloration syntaxique, une barre
de progression, et trois groupes de boutons de navigation sur une même
rangée : entre les étapes de la notion courante, entre notions, et entre
chapitres. Le code est obtenu par `inspect.getsource`, jamais recopié à la
main : il ne peut donc pas se désynchroniser du code qui s'exécute.

Chaque étape est une méthode liée du widget de la notion, sans paramètre ni
valeur de retour. À chaque navigation, toutes les étapes de la première
jusqu'à celle visée sont rejouées depuis un état vierge. Le panneau ne
connaît rien du sujet enseigné.

Une étape « Vue d'ensemble » est construite automatiquement en tête de
chaque notion, à partir de trois attributs de classe (`Objective`,
`KeyConcepts`, `KeyApis`). `QChapterIntroTab` introduit un chapitre entier.
`createSplitterLayout` assemble le panneau et la zone de contenu d'une
notion. L'assemblage de la fenêtre revient à `QWalkthroughWindow` (voir
`q_walkthrough_app.py`).

Texte d'interface en français, sans `tr()` (exception déclarée dans le skill
`interactive-walkthrough-app`, §10).
"""

from __future__ import annotations

import inspect
import textwrap
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple, override

from PySide6.QtCore import QBuffer, QCoreApplication, QEvent, QIODevice, QSize, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QImage, QImageReader, QMovie, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QFrame, QGroupBox, QHBoxLayout, QLabel, QProgressBar, QPushButton, QScrollArea, QSplitter, QVBoxLayout,
    QWidget,
)

from ...widgets.q_python_code_view import QPythonCodeView
from .annex_style import annexStyleSheet
from .doc_urls import commonsFilePageUrl
from .glossary import notPartOf
from .prerequisites import checkPrerequisiteKeys


class QStepWalkthrough(QWidget):
    """Panneau de navigation étape par étape d'une notion.

    Ne connaît aucun état propre à la notion : chaque étape (`QStepWalkthrough.Step.run`) et
    la réinitialisation (`resetState`) sont des méthodes liées du widget de
    la notion. Ne connaît pas non plus l'arbre de navigation : les boutons
    entre notions et entre chapitres émettent des signaux, connectés par
    `QWalkthroughWindow`.

    Contenu:
        Pour l'étape courante : titre, explication (HTML simple, liens
        ouverts dans le navigateur), références de documentation, code
        affiché (section cachée quand il n'y a aucun code à montrer),
        compteur et barre de progression.

    Disposition:
        Trois bandes. En haut, l'en-tête de la notion, toujours visible. Au
        milieu, le contenu de l'étape (titre, explication, références,
        code), qui défile verticalement quand il dépasse la hauteur du
        panneau ; le code y garde au moins `MinimumCodeLines` lignes. En
        bas, le compteur, la barre de progression et les boutons, toujours
        visibles.

    Navigation:
        `goToStep()` rejoue tout depuis un état vierge, en avançant comme en
        reculant. `goToFirstStep()`, `goToPreviousStep()`,
        `goToNextStep()` et `goToLastStep()` en sont les raccourcis, reliés
        aux quatre boutons d'étape. `currentStepIndex()`, `steps()`,
        `stepTitles()` et `topicHeading()` décrivent l'état courant.

    Signaux:
        stepChanged(int): Émis après chaque changement d'étape, avec l'index
            de la nouvelle étape (0 = « Vue d'ensemble », si elle existe).
        previousTopicRequested(), nextTopicRequested(): Bouton de notion
            précédente ou suivante cliqué.
        previousChapterRequested(), nextChapterRequested(): Bouton de
            chapitre précédent ou suivant cliqué.

    Slots:
        goToStep(int), goToFirstStep(), goToPreviousStep(), goToNextStep(),
        goToLastStep(), setTopicHeading(str),
        setTopicNavigationAvailable(bool, bool),
        setChapterNavigationAvailable(bool, bool).
    """

    @dataclass
    class Step:
        """Une étape d'une notion.

        Attributs:
            title: Titre court de l'étape.
            explanation: Texte pédagogique en HTML simple (`<code>…</code>` pour
                le code en ligne). Peut contenir un lien ciblé (skill, §12.4),
                ouvert dans le navigateur.
            run: Méthode exécutée pour appliquer l'étape : une méthode liée du
                widget de la notion, sans paramètre ni valeur de retour.
            codeSource: Fonctions ou méthodes dont le code est affiché, dans
                l'ordre. `None` (défaut) : seulement `run`. Un tuple vide : aucun
                code à montrer, la section de code est cachée.
            references: Couples `(texte affiché, URL)` vers la documentation
                officielle, chacun vérifié au préalable.
        """

        title: str
        explanation: str
        run: Callable[[], None]
        codeSource: tuple[Callable[..., object], ...] | None = None
        references: list[tuple[str, str]] = field(default_factory=list)

    # Height kept by the code view, in lines, when the step content has to scroll.
    MinimumCodeLines = 12

    stepChanged = Signal(int)
    previousTopicRequested = Signal()
    nextTopicRequested = Signal()
    previousChapterRequested = Signal()
    nextChapterRequested = Signal()

    def __init__(self, steps: list[QStepWalkthrough.Step], resetState: Callable[[], None], *,
                 objective: str = "", keyConcepts: Sequence[str] = (), keyApis: Sequence[str] = (),
                 parent: QWidget | None = None) -> None:
        """Initialise le panneau et affiche la première étape.

        Args:
            steps: Les étapes réelles de la notion, dans l'ordre.
            resetState: Méthode qui ramène le widget de la notion à un état
                vierge, appelée avant chaque rejeu.
            objective, keyConcepts, keyApis: Si l'un des trois est fourni,
                une étape « Vue d'ensemble » est construite à partir d'eux
                et placée en tête.
            parent: Widget parent, ou None.
        """
        super().__init__(parent)
        if objective or keyConcepts or keyApis:
            steps = [_buildOverviewStep(objective, keyConcepts, keyApis, steps), *steps]
        self._steps: list[QStepWalkthrough.Step] = steps
        self._resetState: Callable[[], None] = resetState
        self._currentIndex: int = 0

        # Full topic title, "<chapter>.<rank>" prefix included. Empty until QWalkthroughWindow
        # knows the number and calls setTopicHeading().
        self._topicHeadingLabel: QLabel = QLabel()
        self._topicHeadingLabel.setStyleSheet("font-weight: bold; font-size: 15pt;")
        self._topicHeadingLabel.setWordWrap(True)

        self._titleLabel: QLabel = QLabel()
        self._titleLabel.setStyleSheet("font-weight: bold; font-size: 12pt;")
        self._explanationLabel: QLabel = QLabel()
        self._explanationLabel.setTextFormat(Qt.TextFormat.RichText)
        self._explanationLabel.setWordWrap(True)
        self._explanationLabel.setOpenExternalLinks(True)
        # Explicit top-left alignment: otherwise the text is vertically centered whenever its box
        # receives extra height, which happens on the overview step (its code section is hidden).
        self._explanationLabel.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self._referencesLabel: QLabel = QLabel()
        self._referencesLabel.setTextFormat(Qt.TextFormat.RichText)
        self._referencesLabel.setWordWrap(True)
        self._referencesLabel.setOpenExternalLinks(True)

        codeSeparatorLine = QFrame()
        codeSeparatorLine.setFrameShape(QFrame.Shape.HLine)
        codeSeparatorLine.setFrameShadow(QFrame.Shadow.Sunken)
        codeCaptionRow = QHBoxLayout()
        codeCaptionRow.addWidget(codeSeparatorLine, 1)
        codeCaptionRow.addWidget(QLabel("Code de cette étape"))

        self._codeView: QPythonCodeView = QPythonCodeView()
        codeFrame = 2 * self._codeView.frameWidth() + 2 * round(self._codeView.document().documentMargin())
        self._codeView.setMinimumHeight(
            self._codeView.fontMetrics().lineSpacing() * self.MinimumCodeLines + codeFrame)

        # Caption and code view share one container, so that the whole section can be hidden
        # when a step has no code to show.
        self._codeSection: QWidget = QWidget()
        codeSectionLayout = QVBoxLayout(self._codeSection)
        codeSectionLayout.setContentsMargins(0, 0, 0, 0)
        codeSectionLayout.addLayout(codeCaptionRow)
        codeSectionLayout.addWidget(self._codeView, 1)

        self._stepCounterLabel: QLabel = QLabel()
        self._stepCounterLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._progressBar: QProgressBar = QProgressBar()
        self._progressBar.setTextVisible(False)
        self._progressBar.setMinimum(1)

        self._firstButton: QPushButton = _navigationButton("<<", "Première étape")
        self._firstButton.clicked.connect(self.goToFirstStep)
        self._previousButton: QPushButton = _navigationButton("<", "Étape précédente")
        self._previousButton.clicked.connect(self.goToPreviousStep)
        self._nextButton: QPushButton = _navigationButton(">", "Étape suivante")
        self._nextButton.clicked.connect(self.goToNextStep)
        self._lastButton: QPushButton = _navigationButton(">>", "Étape finale")
        self._lastButton.clicked.connect(self.goToLastStep)

        stepNavigationGroup = QGroupBox("Étapes")
        stepNavigationGroup.setToolTip("Navigation entre les étapes de la notion")
        stepNavigationRow = QHBoxLayout(stepNavigationGroup)
        for button in (self._firstButton, self._previousButton, self._nextButton, self._lastButton):
            stepNavigationRow.addWidget(button)

        # Same topic and chapter navigation as on the chapter introduction pages; its signals
        # are relayed unchanged.
        self._broaderNavigation: QTopicChapterNavigation = QTopicChapterNavigation()
        self._broaderNavigation.previousTopicRequested.connect(self.previousTopicRequested)
        self._broaderNavigation.nextTopicRequested.connect(self.nextTopicRequested)
        self._broaderNavigation.previousChapterRequested.connect(self.previousChapterRequested)
        self._broaderNavigation.nextChapterRequested.connect(self.nextChapterRequested)

        navigationRow = QHBoxLayout()
        navigationRow.addWidget(stepNavigationGroup, 1)
        navigationRow.addWidget(self._broaderNavigation)

        stepContent = QWidget()
        stepContentLayout = QVBoxLayout(stepContent)
        stepContentLayout.setContentsMargins(0, 0, 0, 0)
        stepContentLayout.addWidget(self._titleLabel)
        stepContentLayout.addWidget(self._explanationLabel)
        stepContentLayout.addWidget(self._referencesLabel)
        stepContentLayout.addWidget(self._codeSection, 1)
        # A hidden widget gives up its stretch factor too. Without this zero-factor stretch, a
        # step without code would spread its title and explanation over the free height. A zero
        # factor takes over only when the code section is hidden (verified).
        stepContentLayout.addStretch()

        # Only the step content scrolls: the heading and the navigation stay in sight. The scroll
        # area takes all the free height, so the step counter never moves from one step to the next.
        self._stepContentArea: QScrollArea = QScrollArea()
        self._stepContentArea.setWidgetResizable(True)
        self._stepContentArea.setFrameShape(QFrame.Shape.NoFrame)
        self._stepContentArea.setWidget(stepContent)

        layout = QVBoxLayout(self)
        layout.addWidget(self._topicHeadingLabel)
        layout.addWidget(self._stepContentArea, 1)
        layout.addWidget(self._stepCounterLabel)
        layout.addWidget(self._progressBar)
        layout.addLayout(navigationRow)

        self.goToStep(0)

    # ====== API : état ======

    def steps(self) -> list[QStepWalkthrough.Step]:
        """Toutes les étapes, « Vue d'ensemble » comprise, dans l'ordre (une copie de la liste)."""
        return list(self._steps)

    def topicHeading(self) -> str:
        """L'en-tête : le titre complet de la notion, numéro compris."""
        return self._topicHeadingLabel.text()

    def stepTitles(self) -> list[str]:
        """Les titres de toutes les étapes, « Vue d'ensemble » comprise, dans l'ordre."""
        return [step.title for step in self._steps]

    def currentStepIndex(self) -> int:
        """L'index de l'étape affichée (0 = première étape)."""
        return self._currentIndex

    @Slot(str)
    def setTopicHeading(self, text: str) -> None:
        """Fixe l'en-tête : le titre complet de la notion, numéro compris (ex. « 1.1 Position et taille »).

        Le numéro n'est connu que de `QWalkthroughWindow`, qui appelle cette
        méthode une fois la notion enregistrée.
        """
        self._topicHeadingLabel.setText(text)

    # ====== API : navigation ======

    @Slot(int)
    def goToStep(self, index: int) -> None:
        """Se déplace vers une étape précise, en rejouant tout depuis un état vierge.

        À chaque appel, en avançant comme en reculant, `resetState` ramène la
        notion à un état vierge, puis les étapes de la première jusqu'à celle
        visée sont rejouées dans l'ordre. Reculer ne laisse donc jamais
        visible l'effet d'une étape plus avancée. Après chaque étape, les
        évènements qu'elle a postés sont livrés (un widget ajouté à un layout
        s'affiche, le layout le place) : chaque étape trouve l'état que
        l'étudiant voit en avançant d'une étape à la fois.

        Args:
            index: Index de l'étape visée, borné aux étapes existantes.
        """
        index = max(0, min(index, len(self._steps) - 1))
        self._currentIndex = index

        self._resetState()
        for step in self._steps[: index + 1]:
            step.run()
            # Deliver the events each step posted (queued show of a widget added to a layout,
            # layout requests), as when the learner moves one step at a time: the next step
            # then meets widgets already placed. Neither timers nor input are processed here.
            QCoreApplication.sendPostedEvents()

        step = self._steps[index]
        self._titleLabel.setText(step.title)
        self._explanationLabel.setText(step.explanation)
        self._referencesLabel.setVisible(bool(step.references))
        self._referencesLabel.setText(self._formatReferences(step.references))
        sourceFunctions = step.codeSource if step.codeSource is not None else (step.run,)
        self._codeSection.setVisible(bool(sourceFunctions))
        self._codeView.setPlainText(shownCode(step))
        self._stepContentArea.verticalScrollBar().setValue(0)

        self._stepCounterLabel.setText(f"Étape {index + 1} / {len(self._steps)}")
        # Minimum 1: the first step of a topic shows an empty bar. With a single step, minimum and
        # maximum would be equal, which QProgressBar draws as a busy indicator: start from 0 instead.
        self._progressBar.setMinimum(0 if len(self._steps) == 1 else 1)
        self._progressBar.setMaximum(len(self._steps))
        self._progressBar.setValue(index + 1)

        atFirst, atLast = index == 0, index == len(self._steps) - 1
        self._firstButton.setEnabled(not atFirst)
        self._previousButton.setEnabled(not atFirst)
        self._nextButton.setEnabled(not atLast)
        self._lastButton.setEnabled(not atLast)

        self.stepChanged.emit(index)

    @Slot()
    def goToFirstStep(self) -> None:
        """Va à la toute première étape."""
        self.goToStep(0)

    @Slot()
    def goToPreviousStep(self) -> None:
        """Revient à l'étape précédente, si elle existe."""
        self.goToStep(self._currentIndex - 1)

    @Slot()
    def goToNextStep(self) -> None:
        """Avance à l'étape suivante, si elle existe."""
        self.goToStep(self._currentIndex + 1)

    @Slot()
    def goToLastStep(self) -> None:
        """Va à la toute dernière étape."""
        self.goToStep(len(self._steps) - 1)

    @Slot(bool, bool)
    def setTopicNavigationAvailable(self, hasPrevious: bool, hasNext: bool) -> None:
        """Active ou désactive les boutons de notion précédente et suivante."""
        self._broaderNavigation.setTopicNavigationAvailable(hasPrevious, hasNext)

    @Slot(bool, bool)
    def setChapterNavigationAvailable(self, hasPrevious: bool, hasNext: bool) -> None:
        """Active ou désactive les boutons de chapitre précédent et suivant."""
        self._broaderNavigation.setChapterNavigationAvailable(hasPrevious, hasNext)

    # ====== Privé ======

    @staticmethod
    def _formatReferences(references: list[tuple[str, str]]) -> str:
        """La ligne « Documentation : lien1 · lien2 · … », ou une chaîne vide sans référence."""
        if not references:
            return ""
        links = " · ".join(f'<a href="{url}">{text}</a>' for text, url in references)
        return f"Documentation : {links}"


def shownCode(step: QStepWalkthrough.Step) -> str:
    """Le code affiché pour une étape : la source de chaque fonction montrée, séparée par une ligne vide."""
    sourceFunctions = step.codeSource if step.codeSource is not None else (step.run,)
    return "\n\n".join(textwrap.dedent(inspect.getsource(function)) for function in sourceFunctions)


class QImageCaption(NamedTuple):
    """La légende d'une image d'illustration : quatre sections, chacune sur sa ligne (D-043).

    En HTML simple : `title`, ce que montre l'image ; `author`, son
    auteur ; `source`, d'où elle vient et sous quelle licence ; `note`,
    facultative, son lien avec la page. Les trois premières sont
    obligatoires. `link`, facultatif, est l'adresse de la page de l'image
    en ligne (pour Commons, la page du fichier) : la source devient alors
    un lien hypertexte (D-049). Le moteur met le tout en forme, de la même
    façon sur toutes les pages (`html()`).
    """

    title: str
    author: str
    source: str
    note: str = ""
    link: str = ""

    def html(self) -> str:
        """La légende mise en forme : le titre en gras, l'auteur, la source en italique (en lien s'il y en a un), puis la note."""
        source = f'<a href="{self.link}">{self.source}</a>' if self.link else self.source
        html = (f"<p style='margin: 0;'><b>{self.title}</b></p>"
                f"<p style='margin: 0;'>{self.author}</p>"
                f"<p style='margin: 0; font-style: italic; font-size: small;'>{source}</p>")
        if self.note:
            html += f"<p style='margin-top: 6px; margin-bottom: 0;'>{self.note}</p>"
        return html


class QChapterIntroTab(QWidget):
    """Page d'introduction d'un chapitre, affichée quand son nœud est sélectionné dans l'arbre.

    Uniquement les objectifs du chapitre, sans détail technique, puis la
    table des matières de ses notions. Une image d'illustration optionnelle
    s'affiche à droite du texte : produite par le sujet lui-même quand il
    produit des images (`image`), sinon chargée depuis une source externe
    (`imageUrl`). En bas de page, la même navigation entre notions et entre
    chapitres que dans le panneau d'étapes (`navigation`).

    Le chapitre déclare aussi ses prérequis : les entrées de
    `learning_app/assets/prerequis.md` qu'il emploie pour la première fois dans
    son application. La page ne les affiche pas : la page « Prérequis » de
    l'application les réunit tous (`QPrerequisitesPage`).

    Contenu:
        `chapterTitle()`, `introduction()`, `topicTitles()`,
        `imageCaption()` et `prerequisites()` rendent ce que la page
        affiche ou déclare.

    Attributs:
        navigation: La navigation entre notions et entre chapitres
            (`QTopicChapterNavigation`), câblée par `QWalkthroughWindow`.
    """

    def __init__(self, chapterTitle: str, introduction: str, topicTitles: Sequence[str],
                 imageUrl: str = "", parent: QWidget | None = None, *,
                 prerequisites: Sequence[str] = (), image: QImage | None = None,
                 imageCaption: QImageCaption | None = None) -> None:
        """Initialise la page d'introduction.

        Args:
            chapterTitle: Titre du chapitre.
            introduction: Objectifs du chapitre en HTML simple, sans détail
                technique.
            topicTitles: Titres des notions du chapitre, dans l'ordre.
            imageUrl: Chemin d'un fichier local (`assets/images/`, voir
                `image_assets.py`), ou URL externe téléchargée en
                arrière-plan ; image fixe ou GIF animé. Vide : aucune image.
            parent: Widget parent, ou None.
            prerequisites: Clés des prérequis que le chapitre emploie pour
                la première fois.
            image: Image d'illustration produite localement, prioritaire
                sur `imageUrl`. None : aucune.
            imageCaption: Légende affichée sous l'image, obligatoire avec
                une image.

        Raises:
            KeyError: Un prérequis n'est pas dans `assets/prerequis.md`.
            ValueError: Un prérequis est répété.
        """
        super().__init__(parent)
        checkPrerequisiteKeys(prerequisites)
        self._chapterTitle: str = chapterTitle
        self._introduction: str = introduction
        self._topicTitles: list[str] = list(topicTitles)
        self._prerequisites: list[str] = list(prerequisites)
        self._imageCaption: QImageCaption | None = _linkedCaption(imageCaption, imageUrl)

        titleLabel = QLabel(chapterTitle)
        titleLabel.setStyleSheet("font-weight: bold; font-size: 16pt;")

        introductionLabel = QLabel(introduction)
        introductionLabel.setTextFormat(Qt.TextFormat.RichText)
        introductionLabel.setWordWrap(True)

        tocItems = "".join(f"<li>{title}</li>" for title in topicTitles)
        tocLabel = QLabel(f"<p><b>Dans ce chapitre</b></p><ul>{tocItems}</ul>")
        tocLabel.setTextFormat(Qt.TextFormat.RichText)
        tocLabel.setWordWrap(True)

        textColumn = QVBoxLayout()
        textColumn.addWidget(titleLabel)
        textColumn.addWidget(introductionLabel)
        textColumn.addWidget(tocLabel)
        textColumn.addStretch(1)

        contentRow = QHBoxLayout()
        contentRow.addLayout(textColumn, 1)
        if image is not None or imageUrl:
            contentRow.addWidget(_QIllustration(image, imageUrl, self._imageCaption, self._ImageWidth))

        self.navigation: QTopicChapterNavigation = QTopicChapterNavigation()
        navigationRow = QHBoxLayout()
        navigationRow.addStretch(1)
        navigationRow.addWidget(self.navigation)

        layout = QVBoxLayout(self)
        layout.addLayout(contentRow, 1)
        layout.addLayout(navigationRow)

    # ====== API : contenu ======

    def chapterTitle(self) -> str:
        """Le titre du chapitre."""
        return self._chapterTitle

    def introduction(self) -> str:
        """Les objectifs du chapitre, en HTML simple."""
        return self._introduction

    def topicTitles(self) -> list[str]:
        """Les titres numérotés des notions du chapitre, dans l'ordre."""
        return list(self._topicTitles)

    def imageCaption(self) -> QImageCaption | None:
        """La légende de l'image d'illustration, ou None sans image."""
        return self._imageCaption

    def prerequisites(self) -> list[str]:
        """Les clés des prérequis que le chapitre emploie pour la première fois, dans l'ordre."""
        return list(self._prerequisites)

    # ====== Privé ======

    # Target width of the illustration, in pixels; its height keeps the image proportions.
    _ImageWidth = 280


class QChapterSynthesisPage(QWidget):
    """Page de synthèse d'un chapitre : le dernier nœud du chapitre dans l'arbre, après ses notions.

    Comme l'introduction du chapitre, elle n'a ni code ni exemple : du
    texte et une image à droite, avec sa légende. Le texte résume chaque
    notion du chapitre, prend un point de vue d'ensemble, élargit la
    perspective et, au besoin, ouvre vers un sujet connexe (skill
    `interactive-walkthrough-app`, §6). En bas de page, la même navigation
    que les autres pages (`navigation`) : la page fait partie de la suite
    de lecture, entre la dernière notion du chapitre et la première du
    suivant.

    Contenu:
        `chapterTitle()`, `synthesis()` et `imageCaption()` rendent ce que
        la page affiche.

    Attributs:
        navigation: La navigation entre notions et entre chapitres
            (`QTopicChapterNavigation`), câblée par `QWalkthroughWindow`.
    """

    Title = "Synthèse du chapitre"

    def __init__(self, chapterTitle: str, synthesis: str, *, image: QImage | None = None,
                 imageUrl: str = "", imageCaption: QImageCaption | None = None,
                 parent: QWidget | None = None) -> None:
        """Initialise la page de synthèse.

        Args:
            chapterTitle: Titre du chapitre, affiché sous le titre de la page.
            synthesis: Le texte de la synthèse, en HTML simple.
            image: Image produite par le sujet lui-même, prioritaire sur
                `imageUrl`, ou None.
            imageUrl: Chemin local ou URL externe de l'image, ou vide.
            imageCaption: Légende de l'image, obligatoire.
            parent: Widget parent, ou None.

        Raises:
            ValueError: Le texte est vide, la page n'a pas d'image, ou
                l'image n'a pas de légende.
        """
        super().__init__(parent)
        if not synthesis:
            raise ValueError("a chapter synthesis needs a text")
        if image is None and not imageUrl:
            raise ValueError("a chapter synthesis needs an image")
        self._chapterTitle: str = chapterTitle
        self._synthesis: str = synthesis
        self._imageCaption: QImageCaption | None = _linkedCaption(imageCaption, imageUrl)

        titleLabel = QLabel(self.Title)
        titleLabel.setStyleSheet("font-weight: bold; font-size: 16pt;")
        chapterLabel = QLabel(chapterTitle)
        chapterLabel.setStyleSheet("font-style: italic; font-size: 12pt;")

        synthesisLabel = QLabel(synthesis)
        synthesisLabel.setTextFormat(Qt.TextFormat.RichText)
        synthesisLabel.setWordWrap(True)
        synthesisLabel.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setFrameShape(QFrame.Shape.NoFrame)
        scrollArea.setWidget(synthesisLabel)

        contentRow = QHBoxLayout()
        contentRow.addWidget(scrollArea, 1)
        contentRow.addWidget(_QIllustration(image, imageUrl, self._imageCaption, self._ImageWidth))

        self.navigation: QTopicChapterNavigation = QTopicChapterNavigation()
        navigationRow = QHBoxLayout()
        navigationRow.addStretch(1)
        navigationRow.addWidget(self.navigation)

        layout = QVBoxLayout(self)
        layout.addWidget(titleLabel)
        layout.addWidget(chapterLabel)
        layout.addLayout(contentRow, 1)
        layout.addLayout(navigationRow)

    # ====== API : contenu ======

    def chapterTitle(self) -> str:
        """Le titre du chapitre."""
        return self._chapterTitle

    def synthesis(self) -> str:
        """Le texte de la synthèse, en HTML simple."""
        return self._synthesis

    def imageCaption(self) -> QImageCaption | None:
        """La légende de l'image."""
        return self._imageCaption

    # ====== Privé ======

    # Same width as on the chapter introduction.
    _ImageWidth = 280


class QIntroductionPage(QWidget):
    """Page « Introduction » d'une application, en tête de l'arbre, avant le premier chapitre.

    Structure fixe, la même pour toutes les applications : chaque
    application ne fournit que des champs nommés, la page les met en forme.

    1. L'accroche, une phrase, avec l'image vitrine à droite.
    2. « Pourquoi ce sujet » : la motivation.
    3. « Pour qui, pour quoi » : le public, les quatre usages du guide, le
       même texte pour toutes les applications (`UsesHtml`), et le renvoi à
       la page « Prérequis ».
    4. « Ce que couvre le guide » : chaque chapitre, son titre et son
       résumé d'une ligne, lus sur les chapitres eux-mêmes
       (`setChapterSummaries()`), jamais maintenus à part.
    5. « Ce que vous saurez faire » : les capacités visées, puis « Pour
       aller plus loin ».
    6. « Comment se servir du guide » : le même texte pour toutes les
       applications (`usageHtml()`), qui nomme seulement la bibliothèque
       du sujet.

    Contenu:
        `html()` rend le texte affiché, sans l'image ; `imageCaption()` la
        légende de l'image.

    Attributs:
        navigation: La navigation entre notions et entre chapitres
            (`QTopicChapterNavigation`), câblée par `QWalkthroughWindow` :
            « suivant » mène au premier chapitre.
    """

    Title = "Introduction"

    # Section 3, shared by every application: the four ways to use the guide.
    UsesHtml = (
        "<p>Un même guide, quatre usages :</p>"
        "<ul>"
        "<li><b>Découvrir.</b> Vous abordez le sujet pour la première fois : le guide le construit "
        "avec vous, une idée à la fois, sans rien supposer au-delà des prérequis.</li>"
        "<li><b>Se rafraîchir la mémoire.</b> Un geste oublié se retrouve en quelques minutes, par "
        "l'arbre de navigation (la colonne de gauche de la fenêtre) ou par le glossaire, avec son "
        "code qui s'exécute sous vos yeux.</li>"
        "<li><b>Faire la synthèse.</b> La « Vue d'ensemble » de chaque notion réunit ses concepts "
        "clés, puis ses classes et méthodes clés : de quoi faire le point avant un projet.</li>"
        "<li><b>Explorer.</b> Les étapes « À vous » invitent à pousser chaque réglage jusqu'à ses "
        "limites, pour voir ce que le sujet permet vraiment.</li>"
        "</ul>"
    )

    # Section 6, shared by every application: how the guide works, never what it teaches. The last
    # item names the library of the subject: see usageHtml().
    UsageHtml = (
        "<ul>"
        "<li><b>L'arbre de navigation</b>, la colonne de gauche de la fenêtre, mène partout : les "
        "chapitres, leurs notions (1.1, 1.2…), la synthèse qui ferme chaque chapitre, et les deux "
        "pages annexes en bas, « Prérequis » et « Glossaire ». Le bouton « Afficher les étapes » y "
        "ajoute les étapes de chaque notion.</li>"
        "<li><b>Une notion se suit étape par étape.</b> La page de la notion occupe le reste de la "
        "fenêtre, en deux zones. À gauche, la zone de contenu montre ce que le code produit. À "
        "droite, le panneau des étapes donne l'explication, puis le code de l'étape. La première "
        "étape, « Vue d'ensemble », dit l'objectif de la notion, ses concepts clés, puis ses "
        "classes et méthodes clés. La deuxième, « Récapitulatif », reprend les gestes déjà vus "
        "dont la notion a besoin.</li>"
        "<li><b>Le code affiché est le code réel</b> : c'est exactement celui qui s'exécute à "
        "l'étape, jamais une copie simplifiée.</li>"
        "<li><b>Chaque étape rejoue les précédentes.</b> Pour afficher une étape, le guide repart "
        "d'un état vierge, puis exécute toutes les étapes depuis la première jusqu'à celle-là. "
        "L'effet d'une étape s'ajoute donc à celui des précédentes, et revenir en arrière ne "
        "laisse jamais l'effet d'une étape plus avancée.</li>"
        "<li><b>Les étapes « À vous : … »</b> vous donnent des contrôles à manipuler, ou un geste "
        "à faire à la souris : vous changez une valeur, et vous voyez son effet. Les contrôles "
        "sont des widgets de Qt ordinaires, créés avec la page de la notion et cachés jusque-là : "
        "leur création n'est pas montrée. Le code affiché contient une fonction qui relie chaque "
        "contrôle à son slot, puis le slot lui-même. À l'arrivée sur l'étape, le guide appelle "
        "cette fonction, puis montre les contrôles. L'explication donne le libellé de chaque "
        "contrôle, ses bornes et sa valeur de départ.</li>"
        "<li><b>Deux courts paragraphes reviennent souvent.</b> <i>Pour l'exemple</i> ouvre ce "
        "qui sert seulement à construire l'exemple : ce n'est pas le sujet. <i>Essai</i> propose "
        "un geste facultatif, dans une étape qui n'est pas « À vous ».</li>"
        "<li><b>Les liens « Documentation »</b> ouvrent la documentation officielle dans le "
        "navigateur, à l'endroit qui concerne l'étape.</li>"
        "<li><b>Les boutons du bas</b> passent d'une étape, d'une notion ou d'un chapitre à "
        "l'autre.</li>"
        "<li><b>Dans un guide qui affiche des vues 3D, la fenêtre garde une taille fixe</b> : la "
        "redimensionner en tirant son bord serait lent. Le bouton « Taille de la fenêtre… », sous "
        "l'arbre, en propose d'autres, l'ajuste à l'écran ou passe en plein écran (F11). Le bouton "
        "Agrandir de la fenêtre fonctionne aussi.</li>"
        "<li><b>Quelques classes ont été écrites pour ce guide seulement</b>, pour montrer ce "
        "que produit votre code. Elles {notPartOf} : le glossaire les réunit sous « Les outils "
        "de ce guide ».</li>"
        "</ul>"
    )

    @classmethod
    def usageHtml(cls, library: str = "Qt") -> str:
        """« Comment se servir du guide », pour la bibliothèque du sujet (« Qt », « PyQtGraph »)."""
        return cls.UsageHtml.replace("{notPartOf}", notPartOf(library))

    def __init__(self, *, hook: str, motivation: str, audience: str, outcomes: Sequence[str],
                 furtherReading: Sequence[str] = (), image: QImage | None = None, imageUrl: str = "",
                 imageCaption: QImageCaption | None = None, library: str = "Qt",
                 parent: QWidget | None = None) -> None:
        """Initialise la page, sans chapitres encore.

        Args:
            hook: L'accroche, une phrase en HTML simple.
            motivation: Pourquoi ce sujet, en trois ou quatre phrases : ce
                qu'on fait avec, où on le rencontre.
            audience: Le public et son niveau, en HTML simple.
            outcomes: Trois à cinq capacités concrètes, une par puce.
            furtherReading: Une ou deux pistes pour aller plus loin, une
                par puce ; vide : la liste est omise.
            image: Image vitrine produite par le sujet lui-même, prioritaire
                sur `imageUrl`, ou None.
            imageUrl: Chemin local ou URL externe de l'image vitrine, ou vide.
            imageCaption: Légende de l'image, obligatoire avec une image.
            library: La bibliothèque du sujet (« Qt », « PyQtGraph »),
                nommée par « Comment se servir du guide ».
            parent: Widget parent, ou None.

        Raises:
            ValueError: `outcomes` est vide, ou l'image n'a pas de légende.
        """
        super().__init__(parent)
        if not outcomes:
            raise ValueError("an introduction states at least one outcome")
        self._hook: str = hook
        self._motivation: str = motivation
        self._audience: str = audience
        self._outcomes: list[str] = list(outcomes)
        self._furtherReading: list[str] = list(furtherReading)
        self._imageCaption: QImageCaption | None = _linkedCaption(imageCaption, imageUrl)
        self._library: str = library
        self._chapterSummaries: list[tuple[str, str]] = []

        titleLabel = QLabel(self.Title)
        titleLabel.setStyleSheet("font-weight: bold; font-size: 16pt;")

        hookLabel = QLabel(hook)
        hookLabel.setTextFormat(Qt.TextFormat.RichText)
        hookLabel.setWordWrap(True)
        hookLabel.setStyleSheet("font-size: 12pt;")

        self._contentLabel: QLabel = QLabel()
        self._contentLabel.setTextFormat(Qt.TextFormat.RichText)
        self._contentLabel.setWordWrap(True)
        self._contentLabel.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._contentLabel.setOpenExternalLinks(True)

        textColumn = QWidget()
        textLayout = QVBoxLayout(textColumn)
        textLayout.setContentsMargins(0, 0, 0, 0)
        textLayout.addWidget(hookLabel)
        textLayout.addWidget(self._contentLabel, 1)
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setFrameShape(QFrame.Shape.NoFrame)
        scrollArea.setWidget(textColumn)

        contentRow = QHBoxLayout()
        contentRow.addWidget(scrollArea, 1)
        if image is not None or imageUrl:
            contentRow.addWidget(_QIllustration(image, imageUrl, self._imageCaption, self._ImageWidth))

        self.navigation: QTopicChapterNavigation = QTopicChapterNavigation()
        navigationRow = QHBoxLayout()
        navigationRow.addStretch(1)
        navigationRow.addWidget(self.navigation)

        layout = QVBoxLayout(self)
        layout.addWidget(titleLabel)
        layout.addLayout(contentRow, 1)
        layout.addLayout(navigationRow)
        self._refresh()

    # ====== API : contenu ======

    def hook(self) -> str:
        """L'accroche, en HTML simple."""
        return self._hook

    def html(self) -> str:
        """Le texte affiché sous l'accroche, sections 2 à 6, en HTML simple."""
        return self._contentLabel.text()

    def imageCaption(self) -> QImageCaption | None:
        """La légende de l'image vitrine, ou None sans image."""
        return self._imageCaption

    def setChapterSummaries(self, summaries: Sequence[tuple[str, str]]) -> None:
        """Remplace la liste « Ce que couvre le guide » : le titre et le résumé de chaque chapitre."""
        self._chapterSummaries = list(summaries)
        self._refresh()

    # ====== Privé ======

    # Wider than on a chapter page: the showcase image is the first thing the learner sees.
    _ImageWidth = 360

    def _refresh(self) -> None:
        """Recompose les sections 2 à 6."""
        chapters = "".join(f"<li><b>{title}</b>{' : ' + summary if summary else ''}</li>"
                           for title, summary in self._chapterSummaries)
        outcomes = "".join(f"<li>{outcome}</li>" for outcome in self._outcomes)
        parts = [
            "<h3>Pourquoi ce sujet</h3>", f"<p>{self._motivation}</p>",
            "<h3>Pour qui, pour quoi</h3>", f"<p>{self._audience}</p>", self.UsesHtml,
            "<p>Ce que le guide suppose déjà connu est réuni dans la page « Prérequis », en bas de "
            "l'arbre de navigation : les notions de Python qu'il emploie, et les classes de Qt "
            "qu'il ne présente pas.</p>",
            "<h3>Ce que couvre le guide</h3>", f"<ul>{chapters}</ul>",
            "<h3>Ce que vous saurez faire</h3>", f"<ul>{outcomes}</ul>",
        ]
        if self._furtherReading:
            further = "".join(f"<li>{item}</li>" for item in self._furtherReading)
            parts += ["<p><b>Pour aller plus loin</b></p>", f"<ul>{further}</ul>"]
        parts += ["<h3>Comment se servir du guide</h3>", self.usageHtml(self._library)]
        self._contentLabel.setText("".join(parts))


class QGlossaryPage(QWidget):
    """Page « Glossaire » d'une application : les termes qu'elle emploie, sans navigation.

    Le contenu défile quand il dépasse la hauteur de la page.

    Contenu:
        `glossary()` rend le HTML affiché.
    """

    Title = "Glossaire"

    def __init__(self, html: str, parent: QWidget | None = None) -> None:
        """Initialise la page.

        Args:
            html: Les termes de l'application en HTML simple, typiquement
                en tableau.
            parent: Widget parent, ou None.
        """
        super().__init__(parent)
        self._glossary: str = html
        _buildAnnexPage(self, self.Title, html)

    # ====== API : contenu ======

    def glossary(self) -> str:
        """Le contenu affiché, en HTML simple."""
        return self._glossary


class QPrerequisitesPage(QWidget):
    """Page « Prérequis » d'une application : ce qu'elle suppose connu, sans navigation.

    Une grille réunit les prérequis de tous les chapitres, avec le chapitre
    qui emploie chacun en premier. Le contenu défile quand il dépasse la
    hauteur de la page.

    Contenu:
        `prerequisitesHtml()` rend la grille affichée ; `setPrerequisitesHtml()`
        la remplace.
    """

    Title = "Prérequis"

    # Shown above the grid.
    Introduction = ("<p>Ce guide suppose connu ce qui suit : il ne l'enseigne pas. La dernière "
                    "colonne dit à partir de quel chapitre chaque élément sert.</p>")

    def __init__(self, html: str = "", parent: QWidget | None = None) -> None:
        """Initialise la page.

        Args:
            html: La grille des prérequis en HTML simple
                (`prerequisites.prerequisitesTableHtml`).
            parent: Widget parent, ou None.
        """
        super().__init__(parent)
        self._prerequisitesHtml: str = ""
        self._contentLabel: _QAnnexLabel = _buildAnnexPage(self, self.Title, "")
        self.setPrerequisitesHtml(html)

    # ====== API : contenu ======

    def prerequisitesHtml(self) -> str:
        """La grille affichée, en HTML simple, sans la phrase d'introduction."""
        return self._prerequisitesHtml

    def setPrerequisitesHtml(self, html: str) -> None:
        """Remplace la grille affichée."""
        self._prerequisitesHtml = html
        self._contentLabel.setBodyHtml(self.Introduction + html)


class QTopicChapterNavigation(QWidget):
    """Deux groupes de boutons côte à côte : navigation entre notions, puis entre chapitres.

    Partagé par le panneau d'étapes et par les pages d'introduction : même
    présentation et même comportement partout. Ne connaît pas l'arbre de
    navigation : les boutons émettent des signaux, et `QWalkthroughWindow`
    décide quels boutons sont disponibles.

    Signaux:
        previousTopicRequested(), nextTopicRequested(): Bouton de notion
            précédente ou suivante cliqué.
        previousChapterRequested(), nextChapterRequested(): Bouton de
            chapitre précédent ou suivant cliqué.

    Slots:
        setTopicNavigationAvailable(bool, bool),
        setChapterNavigationAvailable(bool, bool).
    """

    previousTopicRequested = Signal()
    nextTopicRequested = Signal()
    previousChapterRequested = Signal()
    nextChapterRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._previousTopicButton: QPushButton = _navigationButton("<", "Notion précédente")
        self._previousTopicButton.clicked.connect(self.previousTopicRequested)
        self._nextTopicButton: QPushButton = _navigationButton(">", "Notion suivante")
        self._nextTopicButton.clicked.connect(self.nextTopicRequested)
        topicGroup = QGroupBox("Notions")
        topicGroup.setToolTip("Navigation entre notions")
        topicRow = QHBoxLayout(topicGroup)
        topicRow.addWidget(self._previousTopicButton)
        topicRow.addWidget(self._nextTopicButton)

        self._previousChapterButton: QPushButton = _navigationButton("<", "Chapitre précédent")
        self._previousChapterButton.clicked.connect(self.previousChapterRequested)
        self._nextChapterButton: QPushButton = _navigationButton(">", "Chapitre suivant")
        self._nextChapterButton.clicked.connect(self.nextChapterRequested)
        chapterGroup = QGroupBox("Chapitres")
        chapterGroup.setToolTip("Navigation entre chapitres")
        chapterRow = QHBoxLayout(chapterGroup)
        chapterRow.addWidget(self._previousChapterButton)
        chapterRow.addWidget(self._nextChapterButton)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(topicGroup)
        layout.addWidget(chapterGroup)

    # ====== API : disponibilité ======

    @Slot(bool, bool)
    def setTopicNavigationAvailable(self, hasPrevious: bool, hasNext: bool) -> None:
        """Active ou désactive les boutons de notion précédente et suivante."""
        self._previousTopicButton.setEnabled(hasPrevious)
        self._nextTopicButton.setEnabled(hasNext)

    @Slot(bool, bool)
    def setChapterNavigationAvailable(self, hasPrevious: bool, hasNext: bool) -> None:
        """Active ou désactive les boutons de chapitre précédent et suivant."""
        self._previousChapterButton.setEnabled(hasPrevious)
        self._nextChapterButton.setEnabled(hasNext)


def createSplitterLayout(tab: QWidget, contentWidget: QWidget, walkthrough: QStepWalkthrough,
                         recommendedPanelWidth: int) -> QSplitter:
    """Assemble la zone de contenu et le panneau d'étapes dans un séparateur ajustable.

    La zone de contenu absorbe tout l'espace supplémentaire ; le panneau
    d'étapes garde sa largeur, celle de départ ou celle que l'utilisateur lui
    a donnée en glissant la poignée.

    Args:
        tab: Le widget de la notion, sans layout encore.
        contentWidget: La zone de contenu (ou son conteneur), à gauche.
        walkthrough: Le panneau d'étapes, à droite.
        recommendedPanelWidth: Largeur initiale du panneau d'étapes, en
            pixels (attribut de classe `RecommendedPanelWidth` de la notion).

    Returns:
        Le séparateur, déjà inséré dans le layout de `tab`.
    """
    splitter = QSplitter(Qt.Orientation.Horizontal)
    splitter.addWidget(contentWidget)
    splitter.addWidget(walkthrough)
    splitter.setStretchFactor(0, 1)
    splitter.setStretchFactor(1, 0)
    splitter.setSizes([10_000, recommendedPanelWidth])

    layout = QHBoxLayout(tab)
    layout.addWidget(splitter)
    return splitter


# ====== Privé ======

def _buildOverviewStep(objective: str, keyConcepts: Sequence[str], keyApis: Sequence[str],
                       steps: list[QStepWalkthrough.Step]) -> QStepWalkthrough.Step:
    """Construit l'étape « Vue d'ensemble », placée en tête d'une notion.

    Elle ne modifie rien et ne montre aucun code. Ses références sont
    l'union, dans l'ordre de première apparition, de celles de toutes les
    étapes réelles : jamais maintenues séparément.
    """
    conceptItems = "".join(f"<li>{concept}</li>" for concept in keyConcepts)
    apiItems = "".join(f"<li><code>{api}</code></li>" for api in keyApis)
    explanation = (
        f"<p>{objective}</p>"
        f"<p><b>Concepts clés</b></p><ul>{conceptItems}</ul>"
        f"<p><b>Classes et méthodes clés</b></p><ul>{apiItems}</ul>"
    )
    references: list[tuple[str, str]] = []
    for step in steps:
        for reference in step.references:
            if reference not in references:
                references.append(reference)
    return QStepWalkthrough.Step(title="Vue d'ensemble", explanation=explanation, run=lambda: None,
                codeSource=(), references=references)


class _QAnnexLabel(QLabel):
    """Le contenu HTML d'une page annexe, précédé de la feuille de style des tableaux annexes.

    La feuille est tirée de la palette du libellé (`annex_style`), et
    recalculée quand la palette change : la page suit le thème du système.
    """

    def __init__(self, html: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._bodyHtml: str = ""
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setBodyHtml(html)

    def setBodyHtml(self, html: str) -> None:
        """Remplace le contenu affiché, sans la feuille de style, ajoutée ici."""
        self._bodyHtml = html
        self._render()

    @override
    def changeEvent(self, event: QEvent) -> None:
        """Recompose le contenu quand la palette change (changement de thème)."""
        super().changeEvent(event)
        if event.type() == QEvent.Type.PaletteChange:
            self._render()

    def _render(self) -> None:
        """Affiche la feuille de style de la palette courante, puis le contenu."""
        self.setText(annexStyleSheet(self.palette()) + self._bodyHtml)


def _linkedCaption(caption: QImageCaption | None, imageUrl: str) -> QImageCaption | None:
    """La légende, avec le lien vers la page Commons de l'image externe si elle n'en a pas déjà un (D-049)."""
    if caption is None or caption.link:
        return caption
    return caption._replace(link=commonsFilePageUrl(imageUrl))


def _buildAnnexPage(page: QWidget, title: str, html: str) -> _QAnnexLabel:
    """Assemble une page annexe : un titre, puis un contenu HTML qui défile ; rend le libellé du contenu."""
    titleLabel = QLabel(title)
    titleLabel.setStyleSheet("font-weight: bold; font-size: 16pt;")

    contentLabel = _QAnnexLabel(html)
    contentLabel.setWordWrap(True)
    contentLabel.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
    contentLabel.setOpenExternalLinks(True)
    scrollArea = QScrollArea()
    scrollArea.setWidgetResizable(True)
    scrollArea.setFrameShape(QFrame.Shape.NoFrame)
    scrollArea.setWidget(contentLabel)

    layout = QVBoxLayout(page)
    layout.addWidget(titleLabel)
    layout.addWidget(scrollArea, 1)
    return contentLabel


class _QIllustration(QWidget):
    """Une image d'illustration et sa légende, en colonne, à une largeur fixée.

    L'image est produite par le code (`QImage`), lue dans un fichier local
    (`assets/images/`), ou téléchargée en arrière-plan depuis une URL
    externe. Partagée par les pages
    d'introduction de l'application et des chapitres, et par les pages de
    synthèse. Toute image a une légende, qui porte son crédit (D-043) :
    une image sans légende est refusée.
    """

    def __init__(self, image: QImage | None, imageUrl: str, caption: QImageCaption | None, width: int,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        if caption is None or not (caption.title and caption.author and caption.source):
            raise ValueError("every image needs a caption: title, author and source")
        self._width: int = width
        self._imageLabel: QLabel = QLabel()
        self._imageNetworkManager: QNetworkAccessManager | None = None
        self._imageBuffer: QBuffer | None = None
        self._movie: QMovie | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._imageLabel)
        captionLabel = QLabel(caption.html())
        captionLabel.setTextFormat(Qt.TextFormat.RichText)
        captionLabel.setWordWrap(True)
        captionLabel.setOpenExternalLinks(True)
        captionLabel.setMaximumWidth(width)
        layout.addWidget(captionLabel)
        layout.addStretch(1)

        if image is not None:
            self._imageLabel.setPixmap(QPixmap.fromImage(image.scaledToWidth(
                width, Qt.TransformationMode.SmoothTransformation)))
        elif imageUrl.startswith(("http://", "https://")):
            self._imageLabel.setToolTip(imageUrl)
            self._startImageDownload(imageUrl)
        elif imageUrl:
            self._showImageData(Path(imageUrl).read_bytes())

    def _startImageDownload(self, url: str) -> None:
        """Lance le téléchargement asynchrone de l'image."""
        # Kept on self: a local manager would be garbage-collected before the download ends.
        self._imageNetworkManager = QNetworkAccessManager(self)
        reply = self._imageNetworkManager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(lambda: self._showDownloadedImage(reply))

    def _showDownloadedImage(self, reply: QNetworkReply) -> None:
        """Affiche l'image reçue ; ne fait rien en cas d'échec réseau.

        Un échec reste silencieux : la page se lit sans l'image, et sa
        légende reste affichée.
        """
        # The manager is dropped with the reply: kept alive, its idle HTTP/2 connection is closed by
        # the server two minutes later, and Qt then warns "QSslSocket: device not open" (verified).
        reply.deleteLater()
        self._imageNetworkManager.deleteLater()
        self._imageNetworkManager = None
        if reply.error() != QNetworkReply.NetworkError.NoError:
            return
        self._showImageData(reply.readAll().data())

    def _showImageData(self, data: bytes) -> None:
        """Affiche une image fixe ou un GIF animé, à la largeur cible.

        `QMovie` affiche aussi bien une image fixe qu'un GIF animé (vérifié).
        """
        self._imageBuffer = QBuffer(self)
        self._imageBuffer.setData(data)
        self._imageBuffer.open(QIODevice.OpenModeFlag.ReadOnly)
        # The size is read before any frame is decoded: setScaledSize() only applies to frames
        # decoded afterwards, so a still image decoded first would keep its full size (verified).
        originalSize = QImageReader(self._imageBuffer).size()
        self._imageBuffer.seek(0)

        self._movie = QMovie(self)
        self._movie.setDevice(self._imageBuffer)
        if originalSize.width() > 0:
            scaledHeight = round(self._width * originalSize.height() / originalSize.width())
            self._movie.setScaledSize(QSize(self._width, scaledHeight))

        self._imageLabel.setMovie(self._movie)
        self._movie.start()


def _navigationButton(symbol: str, toolTip: str) -> QPushButton:
    """Un bouton de navigation : un symbole ASCII seul, son rôle dans l'infobulle.

    Des symboles ASCII plutôt que des émojis ou des icônes `QStyle` : un
    bouton désactivé grise son texte par la palette normale, et le rendu ne
    dépend pas du thème. La marge interne est réduite à la taille du
    symbole (vérifié).
    """
    button = QPushButton(symbol)
    button.setStyleSheet("padding: 2px 6px;")
    button.setToolTip(toolTip)
    return button
