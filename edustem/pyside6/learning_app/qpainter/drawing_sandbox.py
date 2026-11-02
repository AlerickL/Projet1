"""Exécution du programme de l'apprenant, pour l'atelier de dessin (notion 5.2).

`runDrawingProgram(program, painter)` exécute un texte Python avec un
peintre déjà actif, et rend un `ProgramReport` : la ligne et le message
d'une éventuelle erreur, ce que le programme a affiché avec `print()`, et
le nombre de ses appels de dessin.

Un appel de dessin est l'appel d'une méthode du peintre qui dessine : son
nom commence par l'un des `DrawingMethodPrefixes` (`drawLine()`,
`fillRect()`, `eraseRect()`, `strokePath()`…). Les réglages (`setPen()`…)
ne comptent pas. Le compte passe par `sys.setprofile`, qui voit chaque appel
d'une fonction de Qt : le programme reçoit le vrai peintre, sans enveloppe.

Ce n'est pas un bac à sable sécurisé : en Python, aucun `exec()` ne l'est
vraiment, et l'apprenant exécute déjà ce qu'il veut sur son propre poste.
Ce sont des aides pédagogiques, qui gardent le programme dans le sujet du
cours :

- seuls les noms utiles au dessin sont fournis (`ProvidedNames`) ;
- une instruction `import` n'est acceptée que pour `math`, `random`,
  `PySide6.QtGui` et `PySide6.QtCore`, pour qu'un extrait copié d'une
  notion fonctionne tel quel ;
- un programme qui calcule plus d'une seconde est interrompu (une boucle
  sans fin gèlerait sinon toute l'application).

La limite porte sur le temps de calcul du processus (`time.process_time()`),
pas sur le temps écoulé. Sur une machine occupée, l'attente du processeur ne
compte donc pas : un programme qui passe au repos passe aussi sous la
charge. Ce temps comprend celui des fils de calcul de Qt, qui remplit
certaines formes en parallèle : il peut dépasser le temps écoulé.

Après chaque exécution, `RunNotifier` (`q_run_notifier.py`) émet
`programFinished` avec ce temps de calcul : la barre du temps de calcul de
l'atelier s'y relie, sans que le code affiché de la notion 5.2 en dépende.

Limites, assumées : les fonctions intégrées de Python restent toutes
disponibles, donc `__import__("os")` ou `open()` contournent le contrôle des
imports. La limite de temps est vérifiée entre deux lignes de Python : un
seul appel de Qt très long (dessiner une liste immense de points) n'est pas
interrompu.

Plomberie présentée : jamais montrée dans le code des étapes ; la notion 5.2
présente son rôle, ce que `runDrawingProgram` reçoit et ce qu'il rend.
"""

from __future__ import annotations

import ast
import contextlib
import io
import math
import random
import sys
import time
import traceback
from dataclasses import dataclass
from types import FrameType
from typing import Any

from PySide6.QtCore import QLine, QLineF, QPoint, QPointF, QRect, QRectF, QSize, QSizeF, Qt
from PySide6.QtGui import (
    QBrush, QColor, QConicalGradient, QFont, QFontMetrics, QFontMetricsF, QGradient, QImage,
    QLinearGradient, QPainter, QPainterPath, QPen, QPolygon, QPolygonF, QRadialGradient, QTransform,
)

from .q_run_notifier import RunNotifier

# The file name the program is compiled under: it finds, in the traceback of an error, the
# faulty line of the program rather than a line of Qt or of this module.
ProgramFileName = "<votre programme>"

# Longest run allowed, in seconds of processor time (time.process_time()).
TimeLimit = 1.0

# The name prefixes of the painter methods that draw: each call counts in ProgramReport.drawCalls.
DrawingMethodPrefixes = ("draw", "fill", "erase", "stroke")

# The modules an import statement may name. Any other is refused, with a message.
AllowedModules = ("math", "random", "PySide6.QtGui", "PySide6.QtCore")

# Every name available to the program, besides `painter`.
ProvidedNames: dict[str, Any] = {
    "math": math, "random": random, "Qt": Qt,
    "QPoint": QPoint, "QPointF": QPointF, "QLine": QLine, "QLineF": QLineF,
    "QRect": QRect, "QRectF": QRectF, "QSize": QSize, "QSizeF": QSizeF,
    "QPainter": QPainter, "QPen": QPen, "QBrush": QBrush, "QColor": QColor,
    "QGradient": QGradient, "QLinearGradient": QLinearGradient,
    "QRadialGradient": QRadialGradient, "QConicalGradient": QConicalGradient,
    "QFont": QFont, "QFontMetrics": QFontMetrics, "QFontMetricsF": QFontMetricsF,
    "QPainterPath": QPainterPath, "QPolygon": QPolygon, "QPolygonF": QPolygonF,
    "QImage": QImage, "QTransform": QTransform,
}


@dataclass
class ProgramReport:
    """Le bilan d'une exécution.

    Attributs:
        errorLine: La ligne de l'erreur, numérotée à partir de 1, ou `None`
            si l'erreur n'a pas de ligne dans le programme, ou s'il n'y a
            pas d'erreur.
        errorMessage: Le message d'erreur, ou une chaîne vide si le
            programme s'est terminé normalement.
        output: Tout ce que le programme a affiché avec `print()`.
        drawCalls: Le nombre d'appels de dessin du programme, jusqu'à son
            éventuelle erreur ; 0 pour un programme refusé avant d'être
            exécuté.
    """

    errorLine: int | None = None
    errorMessage: str = ""
    output: str = ""
    drawCalls: int = 0

    def succeeded(self) -> bool:
        """`True` si le programme s'est terminé sans erreur."""
        return not self.errorMessage


def runDrawingProgram(program: str, painter: QPainter) -> ProgramReport:
    """Exécute un programme de dessin avec un peintre déjà actif.

    Le peintre n'est ni commencé ni terminé ici : c'est l'appelant qui le
    fournit, dans son bloc `with`. Ce que le programme a dessiné avant une
    erreur reste donc dessiné.

    Args:
        program: Le texte du programme.
        painter: Le peintre, actif sur la surface où dessiner. Le programme
            le reçoit sous le nom `painter`.

    Returns:
        Le bilan de l'exécution. Aucune exception ne s'en échappe.
    """
    output = io.StringIO()
    try:
        tree = ast.parse(program, ProgramFileName)
        _checkImports(tree)
        code = compile(tree, ProgramFileName, "exec")
    except SyntaxError as error:
        RunNotifier.programFinished.emit(0.0)
        return ProgramReport(error.lineno, f"Erreur de syntaxe : {error.msg}")
    except _RefusedImport as error:
        RunNotifier.programFinished.emit(0.0)
        return ProgramReport(error.line, str(error))

    namespace = {**ProvidedNames, "painter": painter}
    counter = _DrawCallCounter(painter)
    previousTrace = sys.gettrace()
    previousProfile = sys.getprofile()
    start = time.process_time()
    try:
        with contextlib.redirect_stdout(output):
            sys.settrace(_timeLimitTracer(start + TimeLimit))
            sys.setprofile(counter)
            try:
                exec(code, namespace)
            finally:
                sys.setprofile(previousProfile)
                sys.settrace(previousTrace)
    except _TimeLimitExceeded as error:
        report = ProgramReport(_programLine(error), f"Programme interrompu : plus de {TimeLimit:g} s "
                               f"de calcul. Une boucle sans fin ?", output.getvalue())
    except Exception as error:
        report = ProgramReport(_programLine(error), f"{type(error).__name__} : {error}", output.getvalue())
    else:
        report = ProgramReport(output=output.getvalue())
    report.drawCalls = counter.count
    RunNotifier.programFinished.emit(time.process_time() - start)
    return report


# -- Private ----------------------------------------------------------------------------------------

class _RefusedImport(Exception):
    def __init__(self, line: int, module: str) -> None:
        super().__init__(
            f"Import refusé : {module}. Ici, on dessine seulement. Tout le nécessaire est déjà "
            f"disponible, sans import ({', '.join(AllowedModules)} restent permis)."
        )
        self.line = line


class _TimeLimitExceeded(BaseException):
    """Dérive de BaseException : un `except Exception` du programme ne l'arrête pas."""


class _DrawCallCounter:
    """Fonction de profilage (`sys.setprofile`) : compte les appels de dessin d'un peintre."""

    def __init__(self, painter: QPainter) -> None:
        self.painter = painter
        self.count = 0

    def __call__(self, frame: FrameType, event: str, arg: object) -> None:
        # A call to a Qt method is a "c_call" event; its argument is the bound method.
        if event == "c_call" and getattr(arg, "__self__", None) is self.painter \
                and getattr(arg, "__name__", "").startswith(DrawingMethodPrefixes):
            self.count += 1


def _checkImports(tree: ast.Module) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            modules = [node.module or ""]
        else:
            continue
        for module in modules:
            if module not in AllowedModules:
                raise _RefusedImport(node.lineno, module)


def _timeLimitTracer(deadline: float):
    def tracer(frame: FrameType, event: str, arg: object):
        if time.process_time() > deadline:
            raise _TimeLimitExceeded()
        return tracer
    return tracer


def _programLine(error: BaseException) -> int | None:
    """La ligne du programme la plus profonde dans la trace de l'erreur."""
    frames = [frame for frame in traceback.extract_tb(error.__traceback__)
              if frame.filename == ProgramFileName]
    return frames[-1].lineno if frames else None
