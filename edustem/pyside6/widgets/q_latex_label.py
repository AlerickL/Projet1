"""Label de formules LaTeX : `QLatexLabel`, et le moteur qui les rend.

`QLatexLabel` affiche une formule LaTeX (sans délimiteurs `$...$`, sans
document) comme un widget Qt natif : la formule est rendue en SVG par un
moteur partagé, puis peinte par QtSvg. Le rendu est asynchrone.

Composants, dans l'ordre du fichier :

- `QLatexLabel` : le widget.
- `QLatexRenderRequest`, `QLatexRenderResult` : ce qu'on demande à un moteur, et ce
  qu'il rend (SVG, dimensions, ligne de base, MathML).
- `QLatexRenderClient` : le jeton d'un demandeur ; il reçoit ses propres
  résultats, sans diffusion à tous les labels.
- `QAbstractLatexRenderer` : le contrat d'un moteur, pour en ajouter un
  autre sans toucher au widget.
- `QMathJaxRenderer` : MathJax 3.2.2 dans une page QtWebEngine partagée,
  hors ligne par défaut (aucune donnée ne quitte le processus).
- `defaultLatexRenderer()` : le moteur partagé par défaut.

Dépendances locales, assumées : `q_abstract_object.py` (base d'un `QObject`
abstrait, pour `QAbstractLatexRenderer`) et la ressource
`assets/mathjax/tex-svg-full.js` (MathJax 3.2.2, licence Apache 2.0 dans
`assets/mathjax/LICENSE`), à côté de ce fichier. Nécessite PySide6 avec
QtWebEngine et QtSvg.
"""

from __future__ import annotations

import enum
import json
import logging
import math
from abc import abstractmethod
from collections import OrderedDict
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Final, NotRequired, TypedDict, cast, override

import shiboken6
from PySide6.QtCore import (
    Property, QByteArray, QEvent, QMimeData, QObject, QRect, QRectF, QSize, Qt, QTimer, QUrl, Signal,
    Slot,
)
from PySide6.QtGui import QAction, QColor, QPainter, QPaintEvent, QPalette, QPixmap, QShowEvent
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import (
    QWebEngineCertificateError, QWebEnginePage, QWebEngineProfile, QWebEngineSettings, QWebEngineUrlRequestInfo,
    QWebEngineUrlRequestInterceptor,
)
from PySide6.QtWidgets import QApplication, QFileDialog, QSizePolicy, QWidget

from ..core.q_abstract_object import QAbstractObject


class QLatexLabel(QWidget):
    """Label de formule LaTeX, rendu de façon asynchrone par un moteur partagé.

    La source s'écrit sans délimiteurs (`\\frac{1}{2}`, pas `$\\frac{1}{2}$`)
    et sans document LaTeX. Le premier rendu arrive après un court délai :
    le label affiche « … » en attendant.

    Source :
        `latex()` / `setLatex(str)`, `clear()`. Chaque changement programme
        un rendu. Des changements rapprochés sont regroupés : au plus un
        rendu par `updateInterval()` millisecondes (16 par défaut). Changer
        la source fait passer l'état à `RenderState.Pending` ; la dernière
        formule valide reste affichée pendant l'attente.

    Moteur :
        `renderer()` / `setRenderer(QAbstractLatexRenderer)`. Par défaut,
        le moteur partagé de `defaultLatexRenderer()`. Changer de moteur
        annule la demande en cours auprès de l'ancien. Quand le moteur
        redevient prêt (`readyChanged(True)`, par exemple après `reload()`),
        un label en erreur retente son rendu de lui-même.

    Présentation :
        `displayMode()` (hors texte ou en ligne), `alignment()` (dont
        `Qt.AlignmentFlag.AlignBaseline`, voir Géométrie), `scaleMode()`
        (voir `ScaleMode`), `zoomFactor()`, `foregroundColor()` (couleur
        invalide : la couleur de texte de la palette ; l'alpha est
        respecté). Un changement de présentation relance le rendu sans
        quitter l'état `Ready` : la formule reste exportable pendant
        l'attente. Seule la *taille* de la police Qt compte : la fonte
        mathématique est celle de MathJax.

    Rendu impossible :
        `errorMode()` décide de ce que devient le label (voir `ErrorMode`).
        `renderFailed(str)` est émis dans tous les modes, et `errorString()`
        garde le message. `fallbackText()` donne le texte affiché à la place
        de la formule. Les modes qui cachent le label le remontrent dès que
        la formule s'affiche ou que la source est effacée. Un label caché
        par l'appelant lui-même n'est jamais remontré automatiquement.

    État et export :
        `renderState()`, `errorString()`, `svgData()`, `mathML()`,
        `saveSvg()`, `copyLatex()`, `copySvg()`, `copyMathML()`,
        `refresh()`. Le SVG et le MathML n'existent qu'à l'état `Ready`. Un
        menu contextuel offre les copies et l'enregistrement (`actions()`).

    Géométrie :
        `sizeHint()` est la taille naturelle de la formule, zoom compris.
        `ScaleMode.Fit` déclare `heightForWidth()` pour garder les
        proportions dans un layout. `ascent()` et `descent()` donnent la
        hauteur de la formule au-dessus et au-dessous de sa ligne de base,
        et `baselineOffset()` la position de cette ligne dans le widget.
        Avec `AlignBaseline`, la ligne de base de la formule se place sur
        celle d'une ligne de texte de la police du label, alignée en haut :
        un `QLabel` voisin de même police et de mêmes marges, aligné en
        haut, partage alors sa ligne de base.

    Signaux :
        latexChanged(str), rendererChanged(QObject), displayModeChanged(bool),
        alignmentChanged(Qt.AlignmentFlag), scaleModeChanged(ScaleMode),
        errorModeChanged(ErrorMode), zoomFactorChanged(float),
        updateIntervalChanged(int), foregroundColorChanged(QColor),
        renderStateChanged(RenderState), errorChanged(str), renderStarted(),
        renderFinished(), renderFailed(str).

    Slots:
        setLatex(str), clear(), setRenderer(QObject), setDisplayMode(bool),
        setAlignment(Qt.AlignmentFlag), setScaleMode(ScaleMode),
        setZoomFactor(float), setForegroundColor(QColor),
        setUpdateInterval(int), setErrorMode(ErrorMode), copyLatex(),
        copySvg(), copyMathML(), refresh().

    Propriétés Qt :
        latexSource, mathDisplayMode, mathAlignment, mathScaleMode,
        mathErrorMode, mathZoomFactor, mathForeground, renderInterval. Leurs
        noms diffèrent des accesseurs Python, pour que `label.latex()` reste
        une méthode.
    """

    class RenderState(enum.IntEnum):
        """État du rendu de la source courante."""

        Empty = 0    # aucune source
        Pending = 1  # rendu demandé, pas encore prêt
        Ready = 2    # formule affichée
        Error = 3    # rendu impossible

    class ScaleMode(enum.IntEnum):
        """Traitement d'un rectangle trop petit, ou trop grand, pour la formule."""

        Natural = 0      # taille naturelle ; l'excédent est coupé
        ShrinkToFit = 1  # réduction seulement, proportions conservées
        Fit = 2          # agrandissement ou réduction, proportions conservées

    class ErrorMode(enum.IntEnum):
        """Ce que le label devient quand le rendu est impossible."""

        Message = 0        # le message d'erreur, en couleur d'avertissement
        Raw = 1            # la source LaTeX telle quelle, comme un QLabel
        HideAndReport = 2  # caché, et le message est journalisé (module logging)
        Hide = 3           # caché, en silence

    latexChanged = Signal(str)
    rendererChanged = Signal(QObject)
    displayModeChanged = Signal(bool)
    alignmentChanged = Signal(Qt.AlignmentFlag)
    scaleModeChanged = Signal(ScaleMode)
    errorModeChanged = Signal(ErrorMode)
    zoomFactorChanged = Signal(float)
    updateIntervalChanged = Signal(int)
    foregroundColorChanged = Signal(QColor)
    renderStateChanged = Signal(RenderState)
    errorChanged = Signal(str)
    renderStarted = Signal()
    renderFinished = Signal()
    renderFailed = Signal(str)

    # Qt may call setVisible() and changeEvent() during QWidget.__init__, before any instance
    # attribute exists: these class-level defaults keep both overrides safe until then.
    __autoHidden: bool = False
    __initialized: bool = False

    def __init__(
        self,
        latex: str = "",
        parent: QWidget | None = None,
        *,
        renderer: QAbstractLatexRenderer | None = None,
        errorMode: ErrorMode = ErrorMode.Message,
    ) -> None:
        super().__init__(parent)
        self.__latex: str = ""
        self.__display: bool = True
        self.__alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignCenter
        self.__scaleMode: QLatexLabel.ScaleMode = QLatexLabel.ScaleMode.ShrinkToFit
        self.__errorMode: QLatexLabel.ErrorMode = QLatexLabel.ErrorMode(errorMode)
        self.__zoom: float = 1.0
        self.__foreground: QColor = QColor()
        self.__state: QLatexLabel.RenderState = QLatexLabel.RenderState.Empty
        self.__error: str = ""
        self.__revision: int = 0
        self.__renderer: QAbstractLatexRenderer | None = None
        self.__result: QLatexRenderResult | None = None
        self.__svg: QSvgRenderer = QSvgRenderer(self)
        self.__pixmap: QPixmap | None = None
        self.__pixmapKey: tuple[int, int, float] | None = None

        self.__client: QLatexRenderClient = QLatexRenderClient(self)
        self.__client.succeeded.connect(self.__accept)
        self.__client.failed.connect(self.__reject)

        self.__updateTimer: QTimer = QTimer(self)
        self.__updateTimer.setSingleShot(True)
        self.__updateTimer.setInterval(16)
        self.__updateTimer.timeout.connect(self.__submit)

        self.__copyLatexAction: QAction = QAction(self.tr("Copy LaTeX source"), self)
        self.__copySvgAction: QAction = QAction(self.tr("Copy as SVG"), self)
        self.__copyMathMLAction: QAction = QAction(self.tr("Copy as MathML"), self)
        self.__saveSvgAction: QAction = QAction(self.tr("Save as SVG..."), self)
        self.__copyLatexAction.triggered.connect(self.copyLatex)
        self.__copySvgAction.triggered.connect(self.copySvg)
        self.__copyMathMLAction.triggered.connect(self.copyMathML)
        self.__saveSvgAction.triggered.connect(self.__saveSvgInteractively)
        self.addActions([self.__copyLatexAction, self.__copySvgAction, self.__copyMathMLAction,
                         self.__saveSvgAction])
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

        self.setContentsMargins(6, 6, 6, 6)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.__initialized = True
        self.setRenderer(renderer if renderer is not None else defaultLatexRenderer())
        self.setLatex(latex)
        self.__updateActions()

    # ====== API source ======

    def latex(self) -> str:
        """La source LaTeX courante."""
        return self.__latex

    @Slot(str)
    def setLatex(self, latex: str) -> None:
        """Remplace la source et programme son rendu.

        Lève:
            TypeError: Si `latex` n'est pas une chaîne.
        """
        if not isinstance(latex, str):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("latex must be a str")
        if latex == self.__latex:
            return
        self.__latex = latex
        self.setAccessibleName(latex)
        self.__schedule(sourceChanged=True)
        self.latexChanged.emit(latex)

    @Slot()
    def clear(self) -> None:
        """Efface la source : état `Empty`, plus rien d'affiché."""
        self.setLatex("")

    # ====== API moteur ======

    def renderer(self) -> QAbstractLatexRenderer | None:
        """Le moteur qui rend les formules de ce label."""
        return self.__renderer

    @Slot(QObject)
    def setRenderer(self, renderer: QAbstractLatexRenderer) -> None:
        """Change de moteur : annule la demande en cours auprès de l'ancien, et relance le rendu.

        Le label n'est jamais propriétaire de son moteur : il ne le détruit
        pas, et un moteur doit vivre au moins aussi longtemps que ses labels.

        Lève:
            TypeError: Si `renderer` ne dérive pas de `QAbstractLatexRenderer`.
        """
        if not isinstance(renderer, QAbstractLatexRenderer):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("renderer must derive from QAbstractLatexRenderer")
        if renderer is self.__renderer:
            return
        previous = self.__renderer
        if previous is not None and shiboken6.isValid(previous):
            previous.cancel(self.__client)
            previous.readyChanged.disconnect(self.__retryIfReady)
        self.__renderer = renderer
        renderer.readyChanged.connect(self.__retryIfReady)
        self.__schedule(sourceChanged=False)
        self.rendererChanged.emit(renderer)

    # ====== API présentation ======

    def displayMode(self) -> bool:
        """`True` : formule hors texte (display) ; `False` : formule en ligne, plus compacte."""
        return self.__display

    @Slot(bool)
    def setDisplayMode(self, display: bool) -> None:
        display = bool(display)
        if display != self.__display:
            self.__display = display
            self.__schedule(sourceChanged=False)
            self.displayModeChanged.emit(display)

    def alignment(self) -> Qt.AlignmentFlag:
        """Position de la formule dans le rectangle utile (`AlignBaseline` : voir la docstring de classe)."""
        return self.__alignment

    @Slot(Qt.AlignmentFlag)
    def setAlignment(self, alignment: Qt.AlignmentFlag) -> None:
        alignment = Qt.AlignmentFlag(alignment)
        if alignment != self.__alignment:
            self.__alignment = alignment
            self.updateGeometry()
            self.update()
            self.alignmentChanged.emit(alignment)

    def scaleMode(self) -> QLatexLabel.ScaleMode:
        return self.__scaleMode

    @Slot(ScaleMode)
    def setScaleMode(self, mode: QLatexLabel.ScaleMode) -> None:
        """Lève:
            ValueError: Si `mode` n'est pas une valeur de `ScaleMode`.
        """
        mode = QLatexLabel.ScaleMode(mode)
        if mode != self.__scaleMode:
            self.__scaleMode = mode
            self.updateGeometry()
            self.update()
            self.scaleModeChanged.emit(mode)

    def zoomFactor(self) -> float:
        return self.__zoom

    @Slot(float)
    def setZoomFactor(self, zoom: float) -> None:
        """Agrandit la formule (vectoriellement), sans nouveau rendu.

        Lève:
            ValueError: Si `zoom` n'est pas un nombre fini strictement positif.
        """
        zoom = float(zoom)
        if not math.isfinite(zoom) or zoom <= 0:
            raise ValueError("zoom must be finite and strictly positive")
        if zoom != self.__zoom:
            self.__zoom = zoom
            self.updateGeometry()
            self.update()
            self.zoomFactorChanged.emit(zoom)

    def foregroundColor(self) -> QColor:
        """Couleur de la formule ; invalide (défaut) : la couleur de texte de la palette."""
        return QColor(self.__foreground)

    @Slot(QColor)
    def setForegroundColor(self, color: QColor) -> None:
        color = QColor(color)
        if color != self.__foreground:
            self.__foreground = color
            self.__schedule(sourceChanged=False)
            self.foregroundColorChanged.emit(QColor(color))

    def updateInterval(self) -> int:
        """Délai de regroupement des changements, en millisecondes."""
        return self.__updateTimer.interval()

    @Slot(int)
    def setUpdateInterval(self, milliseconds: int) -> None:
        """Lève:
            ValueError: Si `milliseconds` est négatif.
        """
        if milliseconds < 0:
            raise ValueError("update interval cannot be negative")
        if milliseconds != self.__updateTimer.interval():
            active = self.__updateTimer.isActive()
            self.__updateTimer.setInterval(milliseconds)
            if active:
                self.__updateTimer.start()
            self.updateIntervalChanged.emit(milliseconds)

    # ====== API rendu impossible ======

    def errorMode(self) -> QLatexLabel.ErrorMode:
        return self.__errorMode

    @Slot(ErrorMode)
    def setErrorMode(self, mode: QLatexLabel.ErrorMode) -> None:
        """Choisit ce que devient le label quand le rendu est impossible.

        Si le label est déjà en erreur, le nouveau mode s'applique tout de
        suite ; `HideAndReport` journalise alors le message.

        Lève:
            ValueError: Si `mode` n'est pas une valeur de `ErrorMode`.
        """
        mode = QLatexLabel.ErrorMode(mode)
        if mode != self.__errorMode:
            self.__errorMode = mode
            if self.__state == QLatexLabel.RenderState.Error:
                self.__presentError(report=True)
            self.errorModeChanged.emit(mode)

    def fallbackText(self) -> str:
        """Le texte affiché à la place de la formule, ou une chaîne vide s'il n'y en a pas.

        Le message d'erreur (précédé de « ⚠ ») en mode `Message`, la source
        en mode `Raw`, rien dans les modes qui cachent le label.
        """
        if self.__state != QLatexLabel.RenderState.Error:
            return ""
        match self.__errorMode:
            case QLatexLabel.ErrorMode.Message:
                return self.tr("⚠ {0}").format(self.__error)
            case QLatexLabel.ErrorMode.Raw:
                return self.__latex
            case QLatexLabel.ErrorMode.HideAndReport | QLatexLabel.ErrorMode.Hide:
                return ""

    # ====== API état et export ======

    def renderState(self) -> QLatexLabel.RenderState:
        return self.__state

    def errorString(self) -> str:
        """Le dernier message d'erreur, vide si le rendu a réussi."""
        return self.__error

    def svgData(self) -> bytes:
        """Le SVG autonome de la formule affichée, à l'état `Ready` ; vide sinon."""
        if self.__state == QLatexLabel.RenderState.Ready and self.__result is not None:
            return self.__result.svg
        return b""

    def mathML(self) -> str:
        """Le MathML de la formule affichée, à l'état `Ready` ; vide sinon."""
        if self.__state == QLatexLabel.RenderState.Ready and self.__result is not None:
            return self.__result.mathml
        return ""

    @Slot(str)
    def saveSvg(self, filename: str | Path) -> bool:
        """Enregistre le SVG de la formule affichée.

        Retourne:
            `False` si aucune formule n'est prête (rien n'est écrit), `True`
            sinon.

        Lève:
            OSError: Si l'écriture du fichier échoue.
        """
        data = self.svgData()
        if not data:
            return False
        Path(filename).write_bytes(data)
        return True

    @Slot()
    def copyLatex(self) -> None:
        """Copie la source LaTeX dans le presse-papiers."""
        QApplication.clipboard().setText(self.__latex)

    @Slot()
    def copySvg(self) -> None:
        """Copie le SVG dans le presse-papiers (`image/svg+xml`, et en texte). Sans effet hors `Ready`."""
        data = self.svgData()
        if not data:
            return
        mime = QMimeData()
        mime.setData("image/svg+xml", QByteArray(data))
        mime.setText(data.decode("utf-8"))
        QApplication.clipboard().setMimeData(mime)

    @Slot()
    def copyMathML(self) -> None:
        """Copie le MathML dans le presse-papiers. Sans effet hors `Ready`."""
        if mathml := self.mathML():
            QApplication.clipboard().setText(mathml)

    @Slot()
    def refresh(self) -> None:
        """Redemande le rendu de la source courante (le cache du moteur peut y répondre)."""
        self.__schedule(sourceChanged=False)

    # ====== API géométrie ======

    def ascent(self) -> float:
        """Hauteur de la formule au-dessus de sa ligne de base, zoom compris ; 0 sans formule."""
        return self.__result.ascent * self.__zoom if self.__result is not None else 0.0

    def descent(self) -> float:
        """Hauteur de la formule au-dessous de sa ligne de base, zoom compris ; 0 sans formule."""
        if self.__result is None:
            return 0.0
        return (self.__result.height - self.__result.ascent) * self.__zoom

    def baselineOffset(self) -> int:
        """Position verticale, dans le widget, de la ligne de base de la formule telle que peinte.

        Retourne:
            Un y en pixels, ou -1 sans formule.
        """
        placement = self.__placement()
        if placement is None:
            return -1
        rect, scale = placement
        return round(rect.top() + self.__result.ascent * self.__zoom * scale)

    @override
    def sizeHint(self) -> QSize:
        margins = self.contentsMargins()
        extra = QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        if self.__result is not None:
            width = math.ceil(self.__result.width * self.__zoom)
            if self.__alignment & Qt.AlignmentFlag.AlignBaseline:
                metrics = self.fontMetrics()
                height = math.ceil(max(self.ascent(), metrics.ascent()) + max(self.descent(), metrics.descent()))
            else:
                height = math.ceil(self.__result.height * self.__zoom)
            size = QSize(width, height)
        elif text := self.__fallbackOrPending():
            size = self.fontMetrics().boundingRect(
                QRect(0, 0, self._MessageWidthHint, 2000), self.__textFlags(), text).size()
        else:
            size = QSize(self._EmptyWidthHint, self.fontMetrics().height())
        return size + extra

    @override
    def minimumSizeHint(self) -> QSize:
        if self.__scaleMode == QLatexLabel.ScaleMode.Natural:
            return self.sizeHint()
        margins = self.contentsMargins()
        return QSize(margins.left() + margins.right() + self._MinimumContent,
                     margins.top() + margins.bottom() + self._MinimumContent)

    @override
    def hasHeightForWidth(self) -> bool:
        return self.__scaleMode == QLatexLabel.ScaleMode.Fit and self.__result is not None

    @override
    def heightForWidth(self, width: int) -> int:
        if not self.hasHeightForWidth():
            return super().heightForWidth(width)
        margins = self.contentsMargins()
        available = max(0, width - margins.left() - margins.right())
        return margins.top() + margins.bottom() + math.ceil(available * self.__result.height / self.__result.width)

    # ====== Événements Qt ======

    @override
    def setVisible(self, visible: bool) -> None:
        # An explicit choice by the caller always wins over automatic hiding.
        self.__autoHidden = False
        super().setVisible(visible)

    @override
    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        # A label in error shown for the first time must hide again. The context object cancels
        # the call if the label is destroyed first.
        if self.__state == QLatexLabel.RenderState.Error and self.__errorMode in self._HidingModes:
            QTimer.singleShot(0, self, lambda: self.__presentError(report=False))

    @override
    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if not self.__initialized:
            return
        eventType = event.type()
        if eventType in (QEvent.Type.FontChange, QEvent.Type.ApplicationFontChange):
            self.__schedule(sourceChanged=False)
            self.updateGeometry()
        elif eventType in (QEvent.Type.PaletteChange, QEvent.Type.ApplicationPaletteChange):
            if not self.__foreground.isValid():
                self.__schedule(sourceChanged=False)
            self.update()

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        area = QRectF(self.contentsRect())
        painter.setClipRect(area)
        placement = self.__placement()
        if placement is None:
            self.__paintFallback(painter, area)
            return
        rect, _scale = placement
        painter.setOpacity(self.__effectiveColor().alphaF())
        painter.drawPixmap(rect.topLeft(), self.__formulaPixmap(rect.width(), rect.height()))

    # ====== Propriétés Qt ======

    latexSource = Property(str, latex, setLatex, notify=latexChanged)
    mathDisplayMode = Property(bool, displayMode, setDisplayMode, notify=displayModeChanged)
    mathAlignment = Property(Qt.AlignmentFlag, alignment, setAlignment, notify=alignmentChanged)
    mathScaleMode = Property(int, scaleMode, setScaleMode, notify=scaleModeChanged)
    mathErrorMode = Property(int, errorMode, setErrorMode, notify=errorModeChanged)
    mathZoomFactor = Property(float, zoomFactor, setZoomFactor, notify=zoomFactorChanged)
    mathForeground = Property(QColor, foregroundColor, setForegroundColor, notify=foregroundColorChanged)
    renderInterval = Property(int, updateInterval, setUpdateInterval, notify=updateIntervalChanged)

    # ====== Privé ======

    _HidingModes: Final[frozenset[QLatexLabel.ErrorMode]] = frozenset({ErrorMode.HideAndReport, ErrorMode.Hide})
    _MessageWidthHint: Final[int] = 400  # reference width of the fallback text, for sizeHint()
    _EmptyWidthHint: Final[int] = 80
    _MinimumContent: Final[int] = 12

    def __setState(self, state: QLatexLabel.RenderState) -> None:
        if state != self.__state:
            self.__state = state
            self.__updateActions()
            self.renderStateChanged.emit(state)

    def __setError(self, message: str) -> None:
        if message != self.__error:
            self.__error = message
            self.errorChanged.emit(message)

    def __updateActions(self) -> None:
        ready = self.__state == QLatexLabel.RenderState.Ready
        self.__copyLatexAction.setEnabled(bool(self.__latex))
        for action in (self.__copySvgAction, self.__copyMathMLAction, self.__saveSvgAction):
            action.setEnabled(ready)

    def __schedule(self, *, sourceChanged: bool) -> None:
        """Programme un rendu. Seul un changement de source fait quitter l'état `Ready`."""
        self.__revision += 1
        if self.__renderer is not None:
            self.__renderer.cancel(self.__client)
        if not self.__latex.strip():
            self.__updateTimer.stop()
            self.__result = None
            self.__pixmap = None
            self.__setError("")
            self.__setAutoHidden(False)
            self.__setState(QLatexLabel.RenderState.Empty)
            self.updateGeometry()
        else:
            if sourceChanged or self.__state != QLatexLabel.RenderState.Ready:
                self.__setError("")
                self.__setState(QLatexLabel.RenderState.Pending)
            # Throttle, not debounce: under a continuous stream of changes, never postpone forever.
            if not self.__updateTimer.isActive():
                self.__updateTimer.start()
        self.__updateActions()
        self.update()

    @Slot()
    def __submit(self) -> None:
        if not self.__latex.strip() or self.__renderer is None:
            return
        pixels = float(self.font().pixelSize())
        if pixels <= 0:
            pixels = self.font().pointSizeF() * self.logicalDpiY() / 72.0
        # The engine receives an opaque #rrggbb color: the alpha is applied when painting.
        request = QLatexRenderRequest(self.__latex, self.__display, max(1.0, pixels), self.__effectiveColor().name())
        self.__renderer.submit(self.__client, self.__revision, request)
        self.renderStarted.emit()

    def __effectiveColor(self) -> QColor:
        if self.__foreground.isValid():
            return QColor(self.__foreground)
        return self.palette().color(QPalette.ColorRole.WindowText)

    @Slot(int, object)
    def __accept(self, revision: int, result: QLatexRenderResult) -> None:
        if revision != self.__revision:
            return
        if not self.__svg.load(QByteArray(result.svg)):
            self.__reject(revision, self.tr("The SVG produced is not accepted by Qt"))
            return
        self.__result = result
        self.__pixmap = None
        self.__setError("")
        self.__setAutoHidden(False)
        self.__setState(QLatexLabel.RenderState.Ready)
        self.updateGeometry()
        self.update()
        self.renderFinished.emit()

    @Slot(int, str)
    def __reject(self, revision: int, message: str) -> None:
        if revision != self.__revision:
            return
        self.__result = None
        self.__pixmap = None
        self.__setError(message)
        self.__setState(QLatexLabel.RenderState.Error)
        self.__presentError(report=True)
        self.renderFailed.emit(message)

    @Slot(bool)
    def __retryIfReady(self, ready: bool) -> None:
        if ready and self.__state == QLatexLabel.RenderState.Error:
            self.__schedule(sourceChanged=False)

    def __presentError(self, *, report: bool) -> None:
        """Applique `errorMode()` à l'état d'erreur courant."""
        self.__setAutoHidden(self.__errorMode in self._HidingModes)
        if report and self.__errorMode == QLatexLabel.ErrorMode.HideAndReport:
            _Log.warning("QLatexLabel: %s (source: %s)", self.__error, self.__latex)
        self.updateGeometry()
        self.update()

    def __setAutoHidden(self, hidden: bool) -> None:
        """Cache le label à cause d'une erreur, ou lui rend la visibilité que ce mécanisme lui a retirée."""
        if hidden:
            if not self.__autoHidden and not self.isHidden():
                self.__autoHidden = True
                super().setVisible(False)
        elif self.__autoHidden:
            self.__autoHidden = False
            super().setVisible(True)

    @Slot()
    def __saveSvgInteractively(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(self, self.tr("Save formula"), "formula.svg",
                                                  self.tr("SVG images (*.svg)"))
        if filename:
            self.saveSvg(filename)

    def __textFlags(self) -> int:
        horizontal = self.__alignment & Qt.AlignmentFlag.AlignHorizontal_Mask
        vertical = self.__alignment & (Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignBottom
                                       | Qt.AlignmentFlag.AlignVCenter)
        return int(horizontal.value | (vertical.value or Qt.AlignmentFlag.AlignTop.value)
                   | Qt.TextFlag.TextWordWrap.value)

    def __fallbackOrPending(self) -> str:
        if self.__state == QLatexLabel.RenderState.Pending and self.__result is None:
            return self.tr("…")
        return self.fallbackText()

    def __placement(self) -> tuple[QRectF, float] | None:
        """Le rectangle où peindre la formule, et l'échelle appliquée ; `None` sans formule."""
        if self.__result is None:
            return None
        area = QRectF(self.contentsRect())
        width = self.__result.width * self.__zoom
        height = self.__result.height * self.__zoom
        if width <= 0 or height <= 0 or area.isEmpty():
            return None
        scale = 1.0
        if self.__scaleMode != QLatexLabel.ScaleMode.Natural:
            scale = min(area.width() / width, area.height() / height)
            if self.__scaleMode == QLatexLabel.ScaleMode.ShrinkToFit:
                scale = min(1.0, scale)
        width, height = width * scale, height * scale
        x, y = area.x(), area.y()
        if self.__alignment & Qt.AlignmentFlag.AlignRight:
            x += area.width() - width
        elif self.__alignment & Qt.AlignmentFlag.AlignHCenter:
            x += (area.width() - width) / 2
        if self.__alignment & Qt.AlignmentFlag.AlignBaseline:
            baseline = max(float(self.fontMetrics().ascent()), self.__result.ascent * self.__zoom * scale)
            y += baseline - self.__result.ascent * self.__zoom * scale
        elif self.__alignment & Qt.AlignmentFlag.AlignBottom:
            y += area.height() - height
        elif self.__alignment & Qt.AlignmentFlag.AlignVCenter:
            y += (area.height() - height) / 2
        return QRectF(x, y, width, height), scale

    def __formulaPixmap(self, width: float, height: float) -> QPixmap:
        """La formule rendue à cette taille, mise en cache au rapport de pixels de l'écran."""
        ratio = self.devicePixelRatioF()
        key = (round(width * ratio), round(height * ratio), ratio)
        if self.__pixmap is None or self.__pixmapKey != key:
            pixmap = QPixmap(max(1, key[0]), max(1, key[1]))
            pixmap.setDevicePixelRatio(ratio)
            pixmap.fill(Qt.GlobalColor.transparent)
            with QPainter(pixmap) as painter:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                self.__svg.render(painter, QRectF(0, 0, key[0] / ratio, key[1] / ratio))
            self.__pixmap, self.__pixmapKey = pixmap, key
        return self.__pixmap

    def __warningColor(self) -> QColor:
        light = self.palette().color(QPalette.ColorRole.Window).lightness() > 128
        return QColor("#c62828") if light else QColor("#ef9a9a")

    def __paintFallback(self, painter: QPainter, area: QRectF) -> None:
        """Ce qui remplace la formule : l'attente, le message d'erreur ou la source."""
        if self.__state == QLatexLabel.RenderState.Pending:
            painter.setPen(self.palette().color(QPalette.ColorRole.WindowText))
            painter.drawText(area, Qt.AlignmentFlag.AlignCenter, self.tr("…"))
            return
        text = self.fallbackText()
        if not text:
            return
        painter.setPen(self.__warningColor() if self.__errorMode == QLatexLabel.ErrorMode.Message
                       else self.palette().color(QPalette.ColorRole.WindowText))
        painter.drawText(area, self.__textFlags(), text)


@dataclass(frozen=True, slots=True)
class QLatexRenderRequest:
    """Ce qu'on demande à un moteur : la source LaTeX et ses paramètres de rendu.

    Attributs:
        latex: La source, sans délimiteurs.
        display: `True` pour une formule hors texte, `False` en ligne.
        fontPixels: Taille de la police, en pixels (1 em).
        color: Couleur de la formule, `#rrggbb`.
    """

    latex: str
    display: bool = True
    fontPixels: float = 20.0
    color: str = "#000000"


@dataclass(frozen=True, slots=True)
class QLatexRenderResult:
    """Ce que rend un moteur : un SVG autonome, compatible QtSvg, et ses mesures en pixels.

    Attributs:
        svg: Le document SVG, encodé en UTF-8.
        width, height: Dimensions logiques de la formule.
        ascent: Distance du haut de la formule à sa ligne de base.
        mathml: La même formule en MathML, vide si le moteur ne le fournit pas.
    """

    svg: bytes
    width: float
    height: float
    ascent: float = 0.0
    mathml: str = ""


class QLatexRenderClient(QObject):
    """Jeton d'un demandeur auprès d'un moteur : il reçoit ses propres résultats.

    Chaque `QLatexLabel` possède le sien. Un moteur émet les signaux du
    jeton concerné seulement, jamais une diffusion à tous les labels. Quand
    un jeton est détruit, le moteur oublie ses demandes (voir
    `QAbstractLatexRenderer`).

    Signaux:
        succeeded(int, QLatexRenderResult): Révision demandée, et son résultat.
        failed(int, str): Révision demandée, et le message d'erreur.
    """

    succeeded = Signal(int, object)
    failed = Signal(int, str)


class QAbstractLatexRenderer(QAbstractObject):
    """Contrat d'un moteur de rendu LaTeX, pour en ajouter un sans toucher à `QLatexLabel`.

    Méthodes à implémenter :
        `submit(client, revision, request)` demande un rendu. Il doit se
        terminer de façon **asynchrone** : jamais de résultat émis depuis
        `submit()` lui-même. `cancel(client)` invalide toute demande en
        attente de ce client.

    Aides protégées :
        `_deliverSuccess()` et `_deliverFailure()` émettent le signal du
        jeton, en ignorant un jeton déjà détruit.

    Point d'extension :
        `isReady()` : `True` par défaut, pour un moteur sans temps de
        chargement. Un moteur qui en a un le surcharge et émet
        `readyChanged(bool)` ; un label en erreur retente son rendu dès
        que son moteur redevient prêt.

    Le moteur appartient à l'application : les labels ne le détruisent pas.

    Signaux:
        readyChanged(bool): Le moteur devient prêt, ou cesse de l'être.
    """

    readyChanged = Signal(bool)

    @abstractmethod
    def submit(self, client: QLatexRenderClient, revision: int, request: QLatexRenderRequest) -> None:
        """Demande le rendu de `request` pour `client`, à la révision `revision`."""

    @abstractmethod
    def cancel(self, client: QLatexRenderClient) -> None:
        """Oublie toute demande en attente de `client`."""

    def isReady(self) -> bool:
        """Le moteur peut-il rendre dès maintenant ? `True` par défaut."""
        return True

    def _deliverSuccess(self, client: QLatexRenderClient, revision: int, result: QLatexRenderResult) -> None:
        if shiboken6.isValid(client):
            client.succeeded.emit(revision, result)

    def _deliverFailure(self, client: QLatexRenderClient, revision: int, message: str) -> None:
        if shiboken6.isValid(client):
            client.failed.emit(revision, message)


class QMathJaxRenderer(QAbstractLatexRenderer):
    """MathJax 3.2.2 vers SVG autonome, dans une page QtWebEngine partagée, sans serveur ni Node.js.

    Source :
        `Source.Local` (défaut) : le script livré avec ce module, aucun
        accès réseau (tout ce qui n'est pas local est bloqué). `Source.Cdn` :
        jsDelivr, et seulement jsDelivr. `localPath` désigne une autre copie
        du composant `tex-svg-full.js`.

    File d'attente :
        Une seule conversion active à la fois ; au plus une demande en
        attente par client (la plus récente remplace la précédente). Les
        résultats d'une révision dépassée ne sont jamais livrés.

    Cache :
        LRU borné à la fois en nombre d'entrées (`cacheEntries`, 0 : pas de
        cache) et en volume de SVG (`cacheBytes`). `cacheEntryCount()`,
        `cacheByteCount()`, `clearCache()`. `conversionCount()` compte les
        conversions réellement faites par MathJax (hors cache).

    Pannes :
        Un délai dépassé (`timeout()`, au chargement ou par conversion), un
        script introuvable ou une réponse invalide met le moteur en erreur
        (`errorString()`, `engineFailed(str)`) : toutes les demandes en
        cours échouent, et les suivantes aussi, jusqu'à `reload()`. Si le
        processus WebEngine s'interrompt, le moteur se recharge une fois de
        lui-même.

    Fermeture :
        `close()` avant la destruction de l'application (par exemple
        connecté à `QApplication.aboutToQuit`). Après, `submit()` lève
        `RuntimeError`.

    Signaux:
        readyChanged(bool) (hérité), engineFailed(str).

    Slots:
        clearCache(), reload(), close().
    """

    class Source(enum.Enum):
        """Provenance du script MathJax."""

        Local = "local"
        Cdn = "cdn"

    engineFailed = Signal(str)

    def __init__(
        self,
        parent: QObject | None = None,
        *,
        source: QMathJaxRenderer.Source = Source.Local,
        localPath: str | Path | None = None,
        timeoutMs: int = 15000,
        cacheEntries: int = 128,
        cacheBytes: int = 8 * 1024 * 1024,
    ) -> None:
        """Lève:
            ValueError: Si `source` n'est pas une `Source`, ou si un délai ou
                une limite de cache est invalide.
        """
        super().__init__(parent)
        self.__source: QMathJaxRenderer.Source = QMathJaxRenderer.Source(source)
        if timeoutMs <= 0 or cacheEntries < 0 or cacheBytes < 0:
            raise ValueError("invalid timeout or cache limits")
        self.__path: Path = Path(localPath or DefaultMathJaxScript).resolve()
        self.__ready: bool = False
        self.__error: str = ""
        self.__closed: bool = False
        self.__generation: int = 0
        self.__ticket: int = 0
        self.__conversions: int = 0
        self.__reloadedAfterCrash: bool = False
        self.__active: QMathJaxRenderer._ActiveJob | None = None
        self.__pending: OrderedDict[QLatexRenderClient, tuple[int, QLatexRenderRequest]] = OrderedDict()
        self.__latest: dict[QLatexRenderClient, int] = {}
        self.__cache: OrderedDict[QLatexRenderRequest, QLatexRenderResult] = OrderedDict()
        self.__cacheBytes: int = 0
        self.__maxEntries: int = cacheEntries
        self.__maxBytes: int = cacheBytes
        self.__page: QWebEnginePage | None = None
        self.__profile: QWebEngineProfile = QWebEngineProfile(self)  # off the record
        self.__policy: QMathJaxRenderer._NetworkPolicy = QMathJaxRenderer._NetworkPolicy(
            self.__source == QMathJaxRenderer.Source.Local, self.__profile)
        self.__profile.setUrlRequestInterceptor(self.__policy)
        self.__timeout: QTimer = QTimer(self)
        self.__timeout.setSingleShot(True)
        self.__timeout.setInterval(timeoutMs)
        self.__timeout.timeout.connect(self.__reportTimeout)
        QTimer.singleShot(0, self, self.reload)

    # ====== API état ======

    def source(self) -> QMathJaxRenderer.Source:
        return self.__source

    def scriptPath(self) -> Path:
        """Le script MathJax local utilisé en `Source.Local`."""
        return self.__path

    @override
    def isReady(self) -> bool:
        return self.__ready

    def isClosed(self) -> bool:
        return self.__closed

    def errorString(self) -> str:
        """La panne du moteur, vide s'il fonctionne."""
        return self.__error

    def timeout(self) -> int:
        """Délai maximal de chargement du moteur, et de chaque conversion, en millisecondes."""
        return self.__timeout.interval()

    @Slot(int)
    def setTimeout(self, milliseconds: int) -> None:
        """Change le délai maximal ; s'applique au prochain chargement ou à la prochaine conversion.

        Lève:
            ValueError: Si `milliseconds` n'est pas strictement positif.
        """
        if milliseconds <= 0:
            raise ValueError("timeout must be strictly positive")
        self.__timeout.setInterval(milliseconds)

    def pendingCount(self) -> int:
        """Nombre de demandes en attente (au plus une par client), hors conversion active."""
        return len(self.__pending)

    def conversionCount(self) -> int:
        """Nombre de conversions réellement faites par MathJax depuis la création (hors cache)."""
        return self.__conversions

    def cacheEntryCount(self) -> int:
        return len(self.__cache)

    def cacheByteCount(self) -> int:
        """Volume total de SVG en cache, en octets."""
        return self.__cacheBytes

    # ====== API contrat du moteur ======

    @override
    def submit(self, client: QLatexRenderClient, revision: int, request: QLatexRenderRequest) -> None:
        """Lève:
            RuntimeError: Si le moteur est fermé.
        """
        if self.__closed:
            raise RuntimeError("renderer is closed")
        if client not in self.__latest:
            client.destroyed.connect(lambda _=None, forgotten=client: self.cancel(forgotten))
        self.__latest[client] = revision
        self.__pending[client] = (revision, request)
        # Never deliver from submit() itself: always from the event loop.
        QTimer.singleShot(0, self, self.__pump)

    @override
    def cancel(self, client: QLatexRenderClient) -> None:
        self.__latest.pop(client, None)
        self.__pending.pop(client, None)

    # ====== API gestion du moteur ======

    @Slot()
    def clearCache(self) -> None:
        self.__cache.clear()
        self.__cacheBytes = 0

    @Slot()
    def reload(self) -> None:
        """Recrée le contexte JavaScript ; les dernières demandes non terminées sont conservées."""
        if self.__closed:
            return
        if self.__active is not None:
            active = self.__active
            if self.__latest.get(active.client) == active.revision:
                self.__pending.setdefault(active.client, (active.revision, active.request))
        self.__active = None
        self.__generation += 1
        generation = self.__generation
        self.__timeout.stop()
        self.__setReady(False)
        self.__error = ""
        if self.__page is not None:
            self.__page.deleteLater()
            self.__page = None
        if self.__source == QMathJaxRenderer.Source.Local and not self.__path.is_file():
            self.__fatal(f"local MathJax script not found: {self.__path}")
            return

        page = QWebEnginePage(self.__profile, self)
        settings = page.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
                              self.__source == QMathJaxRenderer.Source.Cdn)
        channel = QWebChannel(page)
        bridge = QMathJaxRenderer._Bridge(channel)
        channel.registerObject("bridge", bridge)
        page.setWebChannel(channel)

        # Each callback knows the generation that created it: a page replaced by reload()
        # can no longer change anything.
        def reportCertificateError(error: QWebEngineCertificateError) -> None:
            self.__reportError(generation, f"TLS certificate rejected: {error.description()}")

        def reportTermination(status: QWebEnginePage.RenderProcessTerminationStatus, code: int) -> None:
            self.__recoverFromCrash(generation, code)

        page.certificateError.connect(reportCertificateError)
        page.renderProcessTerminated.connect(reportTermination)
        bridge.ready.connect(lambda: self.__finishLoading(generation))
        bridge.error.connect(lambda message: self.__reportError(generation, message))
        bridge.result.connect(lambda payload: self.__deliverResult(generation, payload))
        self.__page = page

        scriptUrl = (QUrl.fromLocalFile(str(self.__path)).toString()
                     if self.__source == QMathJaxRenderer.Source.Local else MathJaxCdnUrl)
        html = _EngineHtml.replace("__MATHJAX_URL__", escape(scriptUrl, quote=True))
        self.__timeout.start()
        page.setHtml(html, QUrl.fromLocalFile(str(self.__path.parent) + "/"))

    @Slot()
    def close(self) -> None:
        """Ferme le moteur. À appeler avant la destruction de l'application (profil WebEngine)."""
        if self.__closed:
            return
        self.__closed = True
        self.__generation += 1
        self.__timeout.stop()
        self.__pending.clear()
        self.__latest.clear()
        self.__active = None
        self.__setReady(False)
        # The page must be destroyed before the WebEngine profile, immediately.
        if self.__page is not None:
            shiboken6.delete(self.__page)
            self.__page = None

    # ====== Privé ======

    class _NetworkPolicy(QWebEngineUrlRequestInterceptor):
        """Bloque tout ce qui n'est pas local ; en mode CDN, autorise en plus jsDelivr seulement."""

        def __init__(self, localOnly: bool, parent: QObject) -> None:
            super().__init__(parent)
            self.__localOnly: bool = localOnly

        @override
        def interceptRequest(self, info: QWebEngineUrlRequestInfo) -> None:  # noqa: D102 (Qt override)
            url = info.requestUrl()
            allowed = url.scheme() in ("file", "qrc", "data", "about")
            if not self.__localOnly:
                allowed = allowed or (url.scheme() == "https" and url.host() == "cdn.jsdelivr.net")
            info.block(not allowed)

    class _Bridge(QObject):
        """Pont QWebChannel : ses slots sont appelés par la page du moteur."""

        ready = Signal()
        error = Signal(str)
        result = Signal(str)

        @Slot()
        def engineReady(self) -> None:
            self.ready.emit()

        @Slot(str)
        def engineError(self, message: str) -> None:
            self.error.emit(message)

        @Slot(str)
        def completed(self, payload: str) -> None:
            self.result.emit(payload)

    class _ResultPayload(TypedDict):
        """Réponse JSON de la page : `svg`, dimensions et MathML en cas de succès, `error` sinon."""

        ticket: int
        svg: NotRequired[str]
        width: NotRequired[float]
        height: NotRequired[float]
        ascent: NotRequired[float]
        mathml: NotRequired[str]
        error: NotRequired[str]

    @dataclass(frozen=True, slots=True)
    class _ActiveJob:
        client: QLatexRenderClient
        revision: int
        request: QLatexRenderRequest
        ticket: int

    def __setReady(self, value: bool) -> None:
        if self.__ready != value:
            self.__ready = value
            self.readyChanged.emit(value)

    def __finishLoading(self, generation: int) -> None:
        if generation != self.__generation or self.__closed or self.__error:
            return
        self.__timeout.stop()
        self.__reloadedAfterCrash = False
        self.__setReady(True)
        self.__pump()

    def __reportError(self, generation: int, message: str) -> None:
        if generation == self.__generation and not self.__closed:
            self.__fatal(message)

    def __recoverFromCrash(self, generation: int, code: int) -> None:
        if generation != self.__generation or self.__closed:
            return
        self.__fatal(f"WebEngine process terminated ({code})")
        if not self.__reloadedAfterCrash:
            self.__reloadedAfterCrash = True
            QTimer.singleShot(0, self, self.reload)

    @Slot()
    def __reportTimeout(self) -> None:
        self.__fatal("render timed out" if self.__active is not None else "MathJax load timed out")

    def __fatal(self, message: str) -> None:
        """Panne du moteur : toutes les demandes en cours échouent avec ce message."""
        self.__timeout.stop()
        self.__generation += 1  # also ignores late answers from the page
        self.__error = message
        self.__setReady(False)
        jobs = list(self.__pending.items())
        self.__pending.clear()
        if self.__active is not None:
            active = self.__active
            jobs.insert(0, (active.client, (active.revision, active.request)))
            self.__active = None
        self.engineFailed.emit(message)
        for client, (revision, _request) in jobs:
            if self.__latest.get(client) == revision:
                self._deliverFailure(client, revision, message)

    def __pump(self) -> None:
        if self.__closed or self.__active is not None:
            return
        if self.__error:
            jobs = list(self.__pending.items())
            self.__pending.clear()
            for client, (revision, _request) in jobs:
                if self.__latest.get(client) == revision:
                    self._deliverFailure(client, revision, self.__error)
            return
        if not self.__ready or not self.__pending or self.__page is None:
            return
        client, (revision, request) = self.__pending.popitem(last=False)
        cached = self.__cache.get(request)
        if cached is not None:
            self.__cache.move_to_end(request)
            if self.__latest.get(client) == revision:
                self._deliverSuccess(client, revision, cached)
            QTimer.singleShot(0, self, self.__pump)
            return
        self.__ticket += 1
        self.__active = QMathJaxRenderer._ActiveJob(client, revision, request, self.__ticket)
        # The keys are those read by the page. JSON, never LaTeX interpolated into JavaScript.
        payload = {"ticket": self.__ticket, "latex": request.latex, "display": request.display,
                   "pixels": request.fontPixels, "color": request.color}
        self.__timeout.start()
        self.__page.runJavaScript("window.renderEquation(" + json.dumps(payload) + ");")

    def __deliverResult(self, generation: int, data: str) -> None:
        active = self.__active
        if generation != self.__generation or active is None or self.__closed:
            return
        try:
            payload = cast(QMathJaxRenderer._ResultPayload, json.loads(data))
            if payload["ticket"] != active.ticket:
                return
            error = payload.get("error", "")
            result: QLatexRenderResult | None = None
            if not error:
                svg, width, height = payload.get("svg"), payload.get("width"), payload.get("height")
                if svg is None or width is None or height is None:
                    raise KeyError("svg, width or height")
                result = QLatexRenderResult(svg.encode("utf-8"), float(width), float(height),
                                      float(payload.get("ascent", height)), payload.get("mathml", ""))
        except (ValueError, KeyError, TypeError) as exception:
            self.__fatal(f"invalid MathJax answer: {exception}")
            return

        self.__timeout.stop()
        self.__active = None
        self.__conversions += 1
        if result is not None:
            self.__store(active.request, result)
            if self.__latest.get(active.client) == active.revision:
                self._deliverSuccess(active.client, active.revision, result)
        elif self.__latest.get(active.client) == active.revision:
            self._deliverFailure(active.client, active.revision, error)
        QTimer.singleShot(0, self, self.__pump)

    def __store(self, request: QLatexRenderRequest, result: QLatexRenderResult) -> None:
        """Ajoute un résultat au cache, en respectant ses deux bornes (entrées, octets)."""
        if not self.__maxEntries or len(result.svg) > self.__maxBytes:
            return
        previous = self.__cache.pop(request, None)
        if previous is not None:
            self.__cacheBytes -= len(previous.svg)
        self.__cache[request] = result
        self.__cacheBytes += len(result.svg)
        while len(self.__cache) > self.__maxEntries or self.__cacheBytes > self.__maxBytes:
            _request, old = self.__cache.popitem(last=False)
            self.__cacheBytes -= len(old.svg)


def defaultLatexRenderer() -> QMathJaxRenderer:
    """Le moteur local partagé par les labels qui n'en désignent pas un.

    Créé au premier appel, enfant de l'application et fermé à
    `QApplication.aboutToQuit`. Recréé s'il a été fermé ou détruit.

    Lève:
        RuntimeError: Si aucune `QApplication` n'existe encore.
    """
    global _defaultRenderer
    application = QApplication.instance()
    if application is None:
        raise RuntimeError("create a QApplication before any QLatexLabel")
    renderer = _defaultRenderer
    if renderer is None or not shiboken6.isValid(renderer) or renderer.isClosed():
        renderer = QMathJaxRenderer(application)
        application.aboutToQuit.connect(renderer.close)
        _defaultRenderer = renderer
    return renderer


MathJaxVersion: Final[str] = "3.2.2"
MathJaxCdnUrl: Final[str] = f"https://cdn.jsdelivr.net/npm/mathjax@{MathJaxVersion}/es5/tex-svg-full.js"
DefaultMathJaxScript: Final[Path] = Path(__file__).parent / "assets" / "mathjax" / "tex-svg-full.js"

_Log: Final[logging.Logger] = logging.getLogger(__name__)
_defaultRenderer: QMathJaxRenderer | None = None

# The engine page. MathJax uses an explicit set of TeX packages, identical locally and on the
# CDN, without any network autoload; user macros are disabled. The ascent comes from the SVG
# viewBox (its minimum y is minus the ascent, in thousandths of an em).
_EngineHtml: Final[str] = """<!doctype html>
<html><head><meta charset="utf-8">
<style>html,body{margin:0;padding:0} #stage{display:inline-block}</style>
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
<script>
"use strict";
window.MathJax = {
  loader: {load: []},
  tex: {
    packages: ['base', 'ams', 'boldsymbol', 'mhchem'],
    maxBuffer: 32768, maxMacros: 1000,
    formatError: (_jax, error) => {throw error;}
  },
  svg: {fontCache: 'none'},
  options: {enableMenu: false},
  startup: {typeset: false}
};
window.engineScriptFailed = false;
</script>
<script src="__MATHJAX_URL__" onerror="window.engineScriptFailed=true"></script>
</head><body><div id="stage"></div>
<script>
new QWebChannel(qt.webChannelTransport, async function(channel) {
  const bridge = channel.objects.bridge;
  const stage = document.getElementById('stage');
  try {
    if (window.engineScriptFailed || !MathJax.startup)
      throw new Error('cannot load the MathJax component');
    await MathJax.startup.promise;
    window.renderEquation = async function(request) {
      try {
        stage.replaceChildren();
        stage.style.fontSize = request.pixels + 'px';
        MathJax.texReset();
        const node = await MathJax.tex2svgPromise(request.latex, {
          display: request.display, em: request.pixels,
          ex: request.pixels * 0.442, containerWidth: 100000
        });
        const invalid = node.querySelector('[data-mml-node="merror"]');
        if (invalid) throw new Error(invalid.textContent || 'invalid LaTeX expression');
        stage.appendChild(node);
        const svg = node.querySelector('svg');
        if (!svg) throw new Error('no SVG produced');
        const box = svg.viewBox.baseVal;
        const scale = request.pixels / 1000;
        const width = Math.max(1, box.width * scale);
        const height = Math.max(1, box.height * scale);
        const ascent = Math.min(height, Math.max(0, -box.y * scale));
        svg.setAttribute('width', width + 'px');
        svg.setAttribute('height', height + 'px');
        svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
        svg.removeAttribute('style');
        // Invisible characters (such as U+2061, emitted after \\sin or \\log) come as empty
        // paths, which Qt SVG reports as "Invalid path data". They draw nothing: drop them.
        svg.querySelectorAll('path:not([d]), path[d=""]').forEach(path => path.remove());
        // Qt SVG does not inherit currentColor from the HTML page.
        const serialized = new XMLSerializer().serializeToString(svg)
          .replace(/currentColor/g, request.color);
        MathJax.texReset();
        const mathml = await MathJax.tex2mmlPromise(request.latex, {display: request.display});
        bridge.completed(JSON.stringify({ticket: request.ticket, svg: serialized, width, height,
                                         ascent, mathml}));
      } catch (error) {
        bridge.completed(JSON.stringify({ticket: request.ticket, error: String(error.message || error)}));
      } finally {
        stage.replaceChildren();
      }
    };
    bridge.engineReady();
  } catch (error) {
    bridge.engineError(String(error.message || error));
  }
});
</script></body></html>
"""
