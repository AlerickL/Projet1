"""Mise en pause d'un minuteur quand la page de sa notion est cachée.

Plomberie partagée par les notions animées de `learning_app` : une
animation continue ne tourne pas pendant que l'étudiant lit une autre
notion. Décrite en mots dans l'explication de l'étape du minuteur, jamais
montrée.
"""

from __future__ import annotations

from typing import override

from PySide6.QtCore import QEvent, QObject, QTimer
from PySide6.QtWidgets import QWidget


class QTimerPause(QObject):
    """Filtre d'événements qui arrête un minuteur quand une page est cachée, et le relance au retour.

    Comportement:
        À l'événement `Hide` de la page, un minuteur actif est arrêté et
        noté en pause. À l'événement `Show`, seul un minuteur noté en pause
        repart : un minuteur arrêté par la notion elle-même reste arrêté.
        `isPaused()` dit si le minuteur attend le retour de la page.

    Durée de vie:
        Enfant Qt de la page, installé comme filtre sur elle : détruit avec
        elle, sans autre gestion.
    """

    def __init__(self, page: QWidget, timer: QTimer) -> None:
        """Installe le filtre sur `page`.

        Args:
            page: La page de la notion, dont le masquage suspend le minuteur.
            timer: Le minuteur de l'animation.
        """
        super().__init__(page)
        self._timer: QTimer = timer
        self._paused: bool = False
        page.installEventFilter(self)

    # ====== API: state ======

    def isPaused(self) -> bool:
        """`True` si le minuteur a été arrêté par le masquage de la page et attend son retour."""
        return self._paused

    # ====== Events ======

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Hide and self._timer.isActive():
            self._timer.stop()
            self._paused = True
        elif event.type() == QEvent.Type.Show and self._paused:
            self._paused = False
            self._timer.start()
        return False


def pauseWhileHidden(page: QWidget, timer: QTimer) -> QTimerPause:
    """Suspend `timer` tant que `page` est cachée ; appelée une fois, dans `__init__` de la notion.

    Returns:
        Le filtre installé, enfant de `page`.
    """
    return QTimerPause(page, timer)
