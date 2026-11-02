"""Adresses de la documentation officielle citée par les notions de `learning_app`.

Plomberie partagée : les références d'une étape (`QStepWalkthrough.Step.references`) et ses
liens ciblés se construisent ici, jamais en URL littérales recopiées d'une
notion à l'autre. Les versions documentées sont fixées en un seul endroit :
Qt for Python 6, PyQtGraph 0.14.0, numpy (version stable).
"""

from __future__ import annotations

QtForPythonRoot = "https://doc.qt.io/qtforpython-6"
QtRoot = "https://doc.qt.io/qt-6"
PyqtgraphRoot = "https://pyqtgraph.readthedocs.io/en/pyqtgraph-0.14.0"
NumpyRoot = "https://numpy.org/doc/stable"


def qtDocUrl(module: str, className: str, member: str = "") -> str:
    """La page Qt for Python d'une classe, ou l'ancre d'un de ses membres.

    Args:
        module: Module de PySide6 (« QtGui »).
        className: Nom de la classe (« QPainter »), ou `Qt` pour l'espace de
            noms des constantes.
        member: Méthode, énumération ou propriété (« drawLine »,
            « BrushStyle ») ; vide pour la page entière.

    Returns:
        L'URL de la page, suivie de l'ancre du membre s'il est donné.

    Exemple :
        >>> qtDocUrl("QtGui", "QPainter", "drawLine")
        'https://doc.qt.io/qtforpython-6/PySide6/QtGui/QPainter.html#PySide6.QtGui.QPainter.drawLine'
    """
    url = f"{QtForPythonRoot}/PySide6/{module}/{className}.html"
    return f"{url}#PySide6.{module}.{className}.{member}" if member else url


def qtPageUrl(page: str, anchor: str = "") -> str:
    """Une page générale de la documentation de Qt 6 (C++), comme le système de coordonnées.

    Args:
        page: Nom de la page, sans extension (« coordsys »).
        anchor: Ancre dans la page, sans `#` ; vide pour la page entière.

    Exemple :
        >>> qtPageUrl("coordsys")
        'https://doc.qt.io/qt-6/coordsys.html'
    """
    url = f"{QtRoot}/{page}.html"
    return f"{url}#{anchor}" if anchor else url


def pyqtgraphDocUrl(page: str, symbol: str = "") -> str:
    """Une page de la documentation de PyQtGraph, ou l'ancre d'un symbole.

    Args:
        page: Chemin de la page depuis la racine de la documentation, sans
            extension (« api_reference/graphicsItems/plotitem »).
        symbol: Symbole documenté, sans le préfixe `pyqtgraph.`
            (« PlotItem.addLegend ») ; vide pour la page entière.

    Exemple :
        >>> pyqtgraphDocUrl("api_reference/graphicsItems/plotitem", "PlotItem.addLegend")
        'https://pyqtgraph.readthedocs.io/en/pyqtgraph-0.14.0/api_reference/graphicsItems/plotitem.html#pyqtgraph.PlotItem.addLegend'
    """
    url = f"{PyqtgraphRoot}/{page}.html"
    return f"{url}#pyqtgraph.{symbol}" if symbol else url


def numpyDocUrl(name: str) -> str:
    """La page de référence d'une fonction ou d'une méthode de numpy.

    Args:
        name: Nom après `numpy.` (« linspace », « random.Generator.normal »).

    Exemple :
        >>> numpyDocUrl("linspace")
        'https://numpy.org/doc/stable/reference/generated/numpy.linspace.html'
    """
    return f"{NumpyRoot}/reference/generated/numpy.{name}.html"


def numpyPageUrl(page: str, anchor: str = "") -> str:
    """Une page générale de la documentation de numpy, comme le guide de l'indexation.

    Args:
        page: Chemin de la page depuis la racine, sans extension
            (« user/basics.indexing »).
        anchor: Ancre dans la page, sans `#` ; vide pour la page entière.

    Exemple :
        >>> numpyPageUrl("user/basics.indexing")
        'https://numpy.org/doc/stable/user/basics.indexing.html'
    """
    url = f"{NumpyRoot}/{page}.html"
    return f"{url}#{anchor}" if anchor else url


CommonsUploadRoot = "https://upload.wikimedia.org/wikipedia/commons/"
CommonsFileRoot = "https://commons.wikimedia.org/wiki/File:"


def commonsFilePageUrl(imageUrl: str) -> str:
    """La page Wikimedia Commons du fichier d'une image, ou une chaîne vide si l'image n'en vient pas.

    La page du fichier donne son auteur, sa licence et sa description : la
    légende d'une image externe y renvoie (D-049). L'adresse de l'image
    est celle du fichier (`…/commons/3/3c/Nom.gif`) ou d'une vignette
    (`…/commons/thumb/a/ae/Nom.jpg/960px-Nom.jpg`) : le nom du fichier est
    le segment qui suit les deux dossiers de hachage.

    Exemple :
        >>> commonsFilePageUrl("https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/X.jpg/960px-X.jpg")
        'https://commons.wikimedia.org/wiki/File:X.jpg'
    """
    if not imageUrl.startswith(CommonsUploadRoot):
        return ""
    parts = imageUrl.removeprefix(CommonsUploadRoot).split("/")
    if parts[0] == "thumb":
        parts = parts[1:]
    return CommonsFileRoot + parts[2]
