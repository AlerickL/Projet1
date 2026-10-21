"""Liaison entre `QDomainExplorerBox` et un curseur-boîte numérique : `QSliderSpinBoxDomainBinding`.

Contrairement aux autres widgets de ce projet, ce fichier n'est pas autonome : il relie deux
modules du projet l'un à l'autre (`q_domain_explorer_box` et `q_slider_spin_box`) et dépend
donc, en plus de PySide6, de ces deux modules locaux. C'est là toute sa raison d'être.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import override

from PySide6.QtCore import Slot

from .q_domain_explorer_box import QDomainBinding
from .q_slider_spin_box import QRealSliderSpinBox, QSliderSpinBox


class QSliderSpinBoxDomainBinding(QDomainBinding[QSliderSpinBox | QRealSliderSpinBox, float]):
    """Implémentation de `QDomainBinding` pour `QSliderSpinBox` et `QRealSliderSpinBox`.

    Les widgets internes d'un curseur-boîte numérique ne sont pas exposés : cette liaison passe
    uniquement par son interface publique (`value`, `setValue`, `minimum`, `maximum` et, en
    réel, `resolution`).

    Le domaine compte une position par valeur représentable, comme pour `QSliderDomainBinding`
    et `QRealSliderDomainBinding` :

    - **En entier**, l'unité vaut 1 : l'index est `value() - minimum()`, et le domaine compte
      `maximum() - minimum() + 1` positions.
    - **En réel**, l'unité vaut `resolution()` (10**-decimals) : avec 2 décimales sur
      [0.0, 1.0], le domaine compte 101 positions. Aucun pas n'est à fournir : le widget
      discrétise déjà sa propre plage. L'index compte les unités entre le minimum et la
      valeur, chacun arrondi à ces décimales comme le fait le widget : une valeur à mi-chemin
      entre deux positions s'éloigne de zéro. L'aller-retour `setIndex(i)` puis `index()`
      redonne exactement `i`.

    Comme toute modification passe par `setValue`, le widget lié émet un seul `valueChanged`
    par déplacement, et aucun `editingFinished` (ce n'est pas une interaction de l'utilisateur
    avec le widget).

    La valeur d'une position est celle du widget : un entier pour `QSliderSpinBox`, un réel
    pour `QRealSliderSpinBox`. La valeur par défaut se donne donc dans l'unité du widget, et
    suit un changement de plage ou de décimales. Elle peut tomber entre deux positions :
    `defaultIndex()` désigne alors exactement la valeur que le widget retiendrait.

    ```python
    box = QRealSliderSpinBox()
    box.setRange(-5.0, 5.0)
    explorer = QDomainExplorerBox()
    explorer.setBinding(QSliderSpinBoxDomainBinding(box, defaultValue=1.0))
    ```
    """

    @override
    def index(self) -> int:
        return self.indexFromValue(self.element().value())

    @override
    @Slot(int)
    def setIndex(self, index: int) -> None:
        element = self.element()
        if isinstance(element, QRealSliderSpinBox):
            element.setValue(element.minimum() + index * element.resolution())
        else:
            element.setValue(element.minimum() + index)

    @override
    def size(self) -> int:
        return self.indexFromValue(self.element().maximum()) + 1

    @override
    def valueFromIndex(self, index: int) -> float:
        element = self.element()
        if isinstance(element, QRealSliderSpinBox):
            return round(element.minimum() + index * element.resolution(), element.decimals())
        return element.minimum() + index

    @override
    def indexFromValue(self, value: float) -> int:
        element = self.element()
        decimals = element.decimals() if isinstance(element, QRealSliderSpinBox) else 0
        return _unitsOf(value, decimals) - _unitsOf(element.minimum(), decimals)


# -----------------------------------------------------------------------------
#                                  Private
# -----------------------------------------------------------------------------

def _unitsOf(value: float, decimals: int) -> int:
    """La valeur en unités de 10**-decimals, arrondie comme le font les widgets réels."""
    return int(Decimal(value).scaleb(decimals).to_integral_value(rounding=ROUND_HALF_UP))
