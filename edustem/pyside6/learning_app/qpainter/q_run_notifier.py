"""Annonce de la fin de chaque exécution d'un programme de l'atelier (notion 5.2).

Plomberie : `runDrawingProgram` (`drawing_sandbox.py`) émet
`RunNotifier.programFinished` après chaque exécution, avec son temps de
calcul. La barre du temps de calcul de l'atelier (`QRunTimeBar`) s'y relie,
sans que le code affiché de la notion en dépende.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class QRunNotifier(QObject):
    """Émet le temps de calcul de chaque exécution terminée.

    Signaux:
        programFinished(float): Le temps de calcul de l'exécution, en
            secondes (`time.process_time()`). Il vaut 0 pour un programme
            refusé avant d'être exécuté, et dépasse la limite de temps pour
            un programme interrompu.
    """

    programFinished = Signal(float)


# The single notifier, which every run of runDrawingProgram goes through.
RunNotifier = QRunNotifier()
