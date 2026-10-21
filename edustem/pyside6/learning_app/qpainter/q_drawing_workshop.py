"""L'atelier de dessin : un éditeur de programme, et son dessin sur le canevas (notion 5.2).

Outil de l'application qpainter. Il assemble les outils du projet : le
canevas (`q_drawing_canvas.py`), l'éditeur (`q_drawing_code_editor.py`), la
lecture (`common/q_readout_label.py`), la barre du temps de calcul
(`q_run_time_bar.py`), l'exécution d'un programme (`drawing_sandbox.py`),
les fragments (`sandbox_snippets.py`), les œuvres (`artworks.py`), et le
carré de couleur de la bibliothèque (`widgets/q_color_box.py`). Cette
dépendance locale est sa raison d'être.

Son code n'est jamais montré : la notion 5.2 décrit son emploi en mots. Le
programme exécuté est celui que l'étudiant lit et écrit dans l'éditeur.
"""

from __future__ import annotations

from PySide6.QtCore import QTimer, Qt, Slot
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtWidgets import (
    QCheckBox, QHBoxLayout, QMenu, QPushButton, QSizePolicy, QToolButton, QVBoxLayout, QWidget,
)

from ...widgets.q_color_box import QColorBox
from ..common.q_readout_label import QReadoutLabel
from .artworks import Artworks
from .drawing_sandbox import ProgramReport, TimeLimit, runDrawingProgram
from .q_drawing_canvas import QDrawingCanvas
from .q_drawing_code_editor import QDrawingCodeEditor
from .q_run_notifier import RunNotifier
from .q_run_time_bar import QRunTimeBar
from .sandbox_snippets import SnippetGroups


class QDrawingWorkshop(QWidget):
    """L'atelier : le programme de l'éditeur, exécuté avec un peintre, et son dessin sur le canevas.

    Disposition, de haut en bas:
        Le canevas (480 × 360) ; le temps de calcul de la dernière exécution
        (`QRunTimeBar`) ; la lecture, qui donne le bilan ; la case « Grille »,
        qui affiche la grille du canevas, et à côté le carré de couleur
        (`QColorBox`) qui choisit sa couleur ; la barre de l'éditeur (« Insérer
        un fragment », « Charger une œuvre », « Vider », « Copier »), de la
        largeur de l'éditeur ; l'éditeur, qui prend la hauteur restante.

    Exécution:
        `runProgram()` exécute le programme de l'éditeur avec un peintre
        actif sur une image blanche neuve de 480 × 360
        (`runDrawingProgram`), puis affiche l'image et le bilan. Le
        programme est relancé `RunDelay` millisecondes après la dernière
        modification de l'éditeur. L'atelier démarre sur `StartingProgram`,
        déjà exécuté.

    Bilan:
        La lecture écrit ce que le programme a affiché avec `print()`, puis
        un verdict : l'erreur et sa ligne, surlignée dans l'éditeur ; une
        invite si l'éditeur est vide ; un avertissement si le programme n'a
        fait aucun appel de dessin ; sinon le nombre d'appels de dessin. La
        barre du temps de calcul suit chaque exécution par `RunNotifier`.

    Slots:
        setProgram(str), runProgram(), copyProgram().
    """

    RunDelay = 500
    StartingProgram = (
        "# Votre dessin. Le peintre « painter » est déjà actif sur une image de 480 × 360.\n"
        "# Modifiez le cercle ci-dessous, ou écrivez vos propres lignes : le dessin suit.\n"
        "painter.setRenderHint(QPainter.RenderHint.Antialiasing)\n"
        "painter.drawEllipse(QPointF(240, 180), 80, 80)\n"
        "\n"
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise l'atelier sur `StartingProgram`, déjà exécuté.

        Args:
            parent: Widget parent, ou None.
        """
        super().__init__(parent)
        self.__image: QImage = QImage()
        self.__report: ProgramReport | None = None

        self.__canvas: QDrawingCanvas = QDrawingCanvas()
        self.__runTimeBar: QRunTimeBar = QRunTimeBar(TimeLimit)
        self.__runTimeBar.setMaximumWidth(self.__canvas.width())
        RunNotifier.programFinished.connect(self.__runTimeBar.setRunTime)
        self.__readout: QReadoutLabel = QReadoutLabel()
        self.__gridCheck: QCheckBox = QCheckBox("Grille")
        self.__gridCheck.toggled.connect(self.__canvas.setGridVisible)
        self.__gridColorBox: QColorBox = QColorBox(self.__canvas.gridColor(), useAlpha=False)
        self.__gridColorBox.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.__gridColorBox.setToolTip("Couleur de la grille")
        self.__gridColorBox.colorChanged.connect(self.__canvas.setGridColor)
        self.__editor: QDrawingCodeEditor = QDrawingCodeEditor()
        self.__editor.setMinimumSize(self.__canvas.width(), 200)

        self.__runTimer: QTimer = QTimer(self)
        self.__runTimer.setSingleShot(True)
        self.__runTimer.setInterval(self.RunDelay)
        self.__editor.textChanged.connect(self.__runTimer.start)
        self.__runTimer.timeout.connect(self.runProgram)

        layout = QVBoxLayout(self)
        layout.addWidget(self.__canvas)
        layout.addWidget(self.__runTimeBar)
        layout.addWidget(self.__readout)
        gridRow = QHBoxLayout()
        gridRow.addWidget(self.__gridCheck)
        gridRow.addWidget(self.__gridColorBox)
        gridRow.addStretch(1)
        layout.addLayout(gridRow)
        layout.addWidget(self.__createToolBar())
        layout.addWidget(self.__editor, 1)
        self.setProgram(self.StartingProgram)

    # ====== API: program ======

    def program(self) -> str:
        """Le programme de l'éditeur."""
        return self.__editor.toPlainText()

    @Slot(str)
    def setProgram(self, program: str) -> None:
        """Remplace le programme de l'éditeur, et l'exécute aussitôt."""
        self.__editor.setPlainText(program)
        self.runProgram()

    @Slot()
    def runProgram(self) -> None:
        """Exécute le programme de l'éditeur sur une image blanche neuve, puis affiche l'image et le bilan."""
        self.__runTimer.stop()
        program = self.program()
        image = QImage(self.__canvas.width(), self.__canvas.height(), QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.white)
        with QPainter(image) as painter:
            report = runDrawingProgram(program, painter)
        self.__image = image
        self.__report = report
        self.__canvas.setImage(image)
        self.__readout.setText(report.output + _verdict(report, program))
        self.__editor.setErrorLine(report.errorLine)

    @Slot()
    def copyProgram(self) -> None:
        """Copie le programme de l'éditeur dans le presse-papiers."""
        QGuiApplication.clipboard().setText(self.program())

    # ====== API: last run ======

    def image(self) -> QImage:
        """L'image de la dernière exécution."""
        return QImage(self.__image)

    def report(self) -> ProgramReport | None:
        """Le bilan de la dernière exécution, ou None avant la première."""
        return self.__report

    # ====== API: parts ======

    def editor(self) -> QDrawingCodeEditor:
        """L'éditeur du programme."""
        return self.__editor

    def canvas(self) -> QDrawingCanvas:
        """Le canevas qui affiche l'image."""
        return self.__canvas

    def readout(self) -> QReadoutLabel:
        """La lecture du bilan, sous le canevas."""
        return self.__readout

    def runTimeBar(self) -> QRunTimeBar:
        """La barre du temps de calcul."""
        return self.__runTimeBar

    def gridCheck(self) -> QCheckBox:
        """La case qui affiche la grille du canevas."""
        return self.__gridCheck

    def gridColorBox(self) -> QColorBox:
        """Le carré de couleur, à côté de la case, qui choisit la couleur de la grille."""
        return self.__gridColorBox

    # ====== Private ======

    def __createToolBar(self) -> QWidget:
        """La barre de l'éditeur : fragments et œuvres à gauche, vider et copier à droite."""
        snippetMenu = QMenu(self)
        for groupTitle, snippets in SnippetGroups:
            groupMenu = snippetMenu.addMenu(groupTitle)
            for snippet in snippets:
                action = groupMenu.addAction(snippet.title)
                action.setToolTip(snippet.code)
                action.triggered.connect(lambda _=False, code=snippet.code: self.__editor.insertSnippet(code))
            groupMenu.setToolTipsVisible(True)
        snippetButton = QToolButton()
        snippetButton.setText("Insérer un fragment")
        snippetButton.setMenu(snippetMenu)
        snippetButton.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        artworkMenu = QMenu(self)
        for artwork in Artworks:
            action = artworkMenu.addAction(f"{artwork.pageTitle()} : {artwork.title}")
            action.triggered.connect(lambda _=False, code=artwork.code: self.__editor.setPlainText(code))
        artworkButton = QToolButton()
        artworkButton.setText("Charger une œuvre")
        artworkButton.setToolTip("Remplacer le programme par l'œuvre d'une page du guide")
        artworkButton.setMenu(artworkMenu)
        artworkButton.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        clearButton = QPushButton("Vider")
        clearButton.setToolTip("Effacer tout le programme")
        clearButton.clicked.connect(self.__editor.clear)
        copyButton = QPushButton("Copier")
        copyButton.setToolTip("Copier tout le programme dans le presse-papiers")
        copyButton.clicked.connect(self.copyProgram)

        toolBar = QWidget()
        row = QHBoxLayout(toolBar)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(snippetButton)
        row.addWidget(artworkButton)
        row.addStretch(1)
        row.addWidget(clearButton)
        row.addWidget(copyButton)
        return toolBar


def _verdict(report: ProgramReport, program: str) -> str:
    """Le verdict d'une exécution, écrit dans la lecture après la sortie de `print()`."""
    if report.errorMessage:
        return f"Ligne {report.errorLine} : {report.errorMessage}"
    if program == "":
        return ("L'éditeur est vide. Écrivez une ligne, comme painter.drawLine(0, 0, 480, 360), "
                "insérez un fragment ou chargez une œuvre.")
    if report.drawCalls == 0:
        return "Programme terminé, sans aucun appel de dessin : rien n'est dessiné."
    return f"Dessin terminé. Appels de dessin : {report.drawCalls}."
