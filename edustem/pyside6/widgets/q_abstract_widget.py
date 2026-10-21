"""Classe abstraite Qt : `QAbstractWidget`.

Combine `abc.ABC` et la métaclasse de `QWidget`, avec application stricte de
l'abstraction : instancier une sous-classe qui n'implémente pas toutes ses
méthodes abstraites lève `TypeError`, comme le ferait une classe Python
ordinaire héritant de `abc.ABC` — ce que `QWidget` seul n'offre pas.
"""

from __future__ import annotations

from abc import ABCMeta
from typing import Any

from PySide6.QtWidgets import QWidget


# No explicit base beyond ABCMeta/type(QWidget): see the "Rationale technique"
# section of the class docstring below for why a plain `class Foo(QWidget,
# ABC)` fails, and why this combined metaclass alone is not enough either.
class QWidgetABCMeta(ABCMeta, type(QWidget)):
    """Métaclasse combinant `ABCMeta` et celle de `QWidget`, avec application
    stricte de l'abstraction à l'instanciation.

    Seul endroit où vit cette logique : une classe n'a qu'à déclarer
    `metaclass=QWidgetABCMeta` — ce que `QAbstractWidget` fait déjà pour ses
    sous-classes. Hériter de `QAbstractWidget` plutôt qu'utiliser cette
    métaclasse directement.

    Rationale technique
    --------------------
    Combiner `abc` et `QWidget` (qui hérite de `QObject`) pose un problème
    d'intégration en plusieurs étapes, chacune vérifiée séparément :

    1. **Conflit de métaclasse.** Hériter directement de `QWidget` et de
       `abc.ABC` lève `TypeError: metaclass conflict` : `QWidget` utilise une
       métaclasse générée par Shiboken (l'outil de liaison C++), `ABC`
       utilise `ABCMeta` — deux hiérarchies de métaclasses que Python ne peut
       pas résoudre seul.
    2. **Métaclasse combinée.** `QWidgetABCMeta` hérite des deux (`ABCMeta`
       et `type(QWidget)`) pour résoudre ce conflit. L'ordre compte :
       `ABCMeta` doit venir en premier pour que sa logique d'inspection de
       classe (qui construit `__abstractmethods__`) s'exécute avant celle de
       `QWidget`/Shiboken.
    3. **Le contournement ne suffit pas seul.** Même avec la métaclasse
       combinée, `__abstractmethods__` est bien peuplé mais jamais vérifié :
       en Python pur, `object.__new__` fait cette vérification, mais le
       `tp_new` de Shiboken pour `QWidget` ne passe pas par lui — une
       sous-classe abstraite s'instancie alors silencieusement. Vérifié avec
       PySide6 6.11 : sans l'étape 4, l'instanciation d'un widget abstrait
       réussit.
    4. **Application manuelle.** `__call__` fait cette vérification lui-même,
       avant toute construction : il inspecte `cls.__abstractmethods__` et
       lève `TypeError` en nommant les méthodes manquantes si l'ensemble
       n'est pas vide, empêchant ainsi robustement l'instanciation de tout
       widget abstrait de la hiérarchie. `__call__` (pas `__new__`) parce
       qu'il vit sur la métaclasse : la vérification est héritée
       automatiquement, sans dépendre d'une sous-classe qui appellerait
       `super().__new__`. S'exécutant avant toute construction, aucune
       `QApplication` n'est nécessaire pour obtenir l'erreur (vérifié : voir
       `QAbstractWidget`).

    Limite
    ------
    La vérification s'exécute à l'appel de la classe (`MonWidget(...)`).
    Appeler `MonWidget.__new__(MonWidget)` directement la contourne, comme
    pour toute vérification au niveau métaclasse — pas une situation
    rencontrée en usage normal.
    """

    def __call__(cls, *args: object, **kwargs: object) -> Any:
        """Instancie `cls`, sauf s'il lui reste des méthodes abstraites non implémentées.

        Lève:
            TypeError: Si `cls.__abstractmethods__` n'est pas vide.
        """
        if cls.__abstractmethods__:
            methods = ", ".join(sorted(cls.__abstractmethods__))
            raise TypeError(
                f"Cannot instantiate abstract class {cls.__name__} "
                f"with abstract methods: {methods}"
            )

        return super().__call__(*args, **kwargs)


class QAbstractWidget(QWidget, metaclass=QWidgetABCMeta):
    """Base réutilisable pour un `QWidget` abstrait.

    Hériter de cette classe pour créer un widget Qt abstrait, typiquement une
    base commune à une famille de panneaux ou de vues devant chacun
    implémenter une partie de l'interface (construire l'UI, se rafraîchir,
    ...). Elle gère déjà la complexité technique sous-jacente (voir
    `QWidgetABCMeta` pour le détail). Instancier une sous-classe qui laisse
    une méthode abstraite non implémentée lève `TypeError` en la nommant, et
    ce sans nécessiter de `QApplication` — la vérification a lieu avant toute
    construction Qt. `QAbstractWidget` elle-même ne déclare aucune méthode
    abstraite et s'instancie donc normalement ; elle est destinée à être
    sous-classée.

    Exemple :
        >>> from abc import abstractmethod
        >>> class Panel(QAbstractWidget):
        ...     @abstractmethod
        ...     def refresh(self) -> str: ...
        >>> Panel()
        Traceback (most recent call last):
            ...
        TypeError: Cannot instantiate abstract class Panel with abstract methods: refresh
    """
