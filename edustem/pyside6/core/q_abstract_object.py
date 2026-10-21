"""Classe abstraite Qt : `QAbstractObject`.

Combine `abc.ABC` et la métaclasse de `QObject`, avec application stricte de
l'abstraction : instancier une sous-classe qui n'implémente pas toutes ses
méthodes abstraites lève `TypeError`, comme le ferait une classe Python
ordinaire héritant de `abc.ABC` — ce que `QObject` seul n'offre pas.
"""

from __future__ import annotations

from abc import ABCMeta
from typing import Any

from PySide6.QtCore import QObject


# No explicit base beyond ABCMeta/type(QObject): see the "Rationale technique"
# section of the class docstring below for why a plain `class Foo(QObject,
# ABC)` fails, and why this combined metaclass alone is not enough either.
class QObjectABCMeta(ABCMeta, type(QObject)):
    """Métaclasse combinant `ABCMeta` et celle de `QObject`, avec application
    stricte de l'abstraction à l'instanciation.

    Seul endroit où vit cette logique : une classe n'a qu'à déclarer
    `metaclass=QObjectABCMeta` — ce que `QAbstractObject` fait déjà pour ses
    sous-classes. Hériter de `QAbstractObject` plutôt qu'utiliser cette
    métaclasse directement.

    Rationale technique
    --------------------
    Combiner `abc` et `QObject` pose un problème d'intégration en plusieurs
    étapes, chacune vérifiée séparément :

    1. **Conflit de métaclasse.** Hériter directement de `QObject` et de
       `abc.ABC` lève `TypeError: metaclass conflict` : `QObject` utilise une
       métaclasse générée par Shiboken (l'outil de liaison C++), `ABC`
       utilise `ABCMeta` — deux hiérarchies de métaclasses que Python ne peut
       pas résoudre seul.
    2. **Métaclasse combinée.** `QObjectABCMeta` hérite des deux (`ABCMeta`
       et `type(QObject)`) pour résoudre ce conflit. L'ordre compte :
       `ABCMeta` doit venir en premier pour que sa logique d'inspection de
       classe (qui construit `__abstractmethods__`) s'exécute avant celle de
       `QObject`.
    3. **Le contournement ne suffit pas seul.** Même avec la métaclasse
       combinée, `__abstractmethods__` est bien peuplé mais jamais vérifié :
       en Python pur, `object.__new__` fait cette vérification, mais le
       `tp_new` de Shiboken pour `QObject` ne passe pas par lui — une
       sous-classe abstraite s'instancie alors silencieusement. Vérifié avec
       PySide6 6.11 : sans l'étape 4, l'instanciation réussit.
    4. **Application manuelle.** `__call__` fait cette vérification lui-même,
       avant toute construction : il inspecte `cls.__abstractmethods__` et
       lève `TypeError` en nommant les méthodes manquantes si l'ensemble
       n'est pas vide. `__call__` (pas `__new__`) parce qu'il vit sur la
       métaclasse : la vérification est héritée automatiquement, sans
       dépendre d'une sous-classe qui appellerait `super().__new__`.

    Limite
    ------
    La vérification s'exécute à l'appel de la classe (`MaClasse(...)`).
    Appeler `MaClasse.__new__(MaClasse)` directement la contourne, comme pour
    toute vérification au niveau métaclasse — pas une situation rencontrée en
    usage normal.
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


class QAbstractObject(QObject, metaclass=QObjectABCMeta):
    """Base réutilisable pour un `QObject` abstrait.

    Hériter de cette classe pour créer un objet Qt abstrait : elle gère déjà
    la complexité technique sous-jacente (voir `QObjectABCMeta` pour le
    détail). Instancier une sous-classe qui laisse une méthode abstraite non
    implémentée lève `TypeError` en la nommant. `QAbstractObject` elle-même
    ne déclare aucune méthode abstraite et s'instancie donc normalement ;
    elle est destinée à être sous-classée.

    Exemple :
        >>> from abc import abstractmethod
        >>> class Worker(QAbstractObject):
        ...     @abstractmethod
        ...     def run(self) -> str: ...
        >>> Worker()
        Traceback (most recent call last):
            ...
        TypeError: Cannot instantiate abstract class Worker with abstract methods: run
    """
