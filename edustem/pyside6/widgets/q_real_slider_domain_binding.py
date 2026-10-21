"""Liaison entre `QDomainExplorerBox` et un `QRealControl` : `QRealSliderDomainBinding`.

Contrairement aux autres widgets de ce projet, ce fichier n'est pas autonome :
il relie deux modules du projet l'un à l'autre (`q_domain_explorer_box` et
`q_real_slider`). Il dépend donc, en plus de PySide6, de ces deux modules
locaux. C'est là toute sa raison d'être.
"""

from __future__ import annotations

from typing import override

from PySide6.QtCore import Slot

from .q_domain_explorer_box import QDomainBinding
from .q_real_slider import QRealControl


class QRealSliderDomainBinding(QDomainBinding[QRealControl, float]):
    """Implémentation de `QDomainBinding` pour un `QRealControl` (`QRealSlider`,
    `QRealScrollBar`, `QRealDial`).

    Même forme que `QSliderDomainBinding`, mais transposée à un contrôle réel :
    la position dans le domaine correspond à la valeur exprimée en unités de
    résolution (`resolution()`) plutôt qu'à la valeur elle-même. Contrairement
    à `QDoubleSpinBoxDomainBinding`, aucun pas ne doit être fourni ni deviné :
    un `QRealControl` discrétise déjà sa propre plage
    (`decimals()`/`resolution()`). L'index est l'entier interne de Qt, obtenu
    par les conversions `baseFromValue()`/`valueFromBase()` du contrôle
    lui-même : la correspondance est exacte.

    La valeur d'une position est le réel du contrôle. La valeur par défaut se
    donne donc comme un réel, et suit un changement de plage ou de décimales :

    ```python
    slider = QRealSlider()
    slider.setRange(-5.0, 5.0)
    explorer = QDomainExplorerBox()
    explorer.setBinding(QRealSliderDomainBinding(slider, defaultValue=1.0))
    ```

    Le contrôle arrondit toute valeur à ses décimales, comme le fait
    `indexFromValue()` : la position la plus proche d'une valeur par défaut
    est exactement la valeur que le contrôle retiendrait.
    """

    @override
    def index(self) -> int:
        return self.indexFromValue(self.element().value())

    @override
    @Slot(int)
    def setIndex(self, index: int) -> None:
        self.element().setValue(self.valueFromIndex(index))

    @override
    def size(self) -> int:
        return self.element().stepCount() + 1

    @override
    def valueFromIndex(self, index: int) -> float:
        element = self.element()
        return element.valueFromBase(element.baseFromValue(element.minimum()) + index)

    @override
    def indexFromValue(self, value: float) -> int:
        element = self.element()
        return element.baseFromValue(value) - element.baseFromValue(element.minimum())
