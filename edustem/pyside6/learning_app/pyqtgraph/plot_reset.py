"""Remise à zéro des graphiques et des vues de pyqtgraph, partagée par les notions.

Le rejeu des étapes ramène chaque graphique à un état vierge avant de
rejouer les étapes (voir le skill « interactive-walkthrough-app »).
`PlotItem.clear()` ne retire que les éléments graphiques : titre, axes,
grille, légende, échelle logarithmique, axes liés, proportions et zone
visible se remettent à zéro séparément (`resetPlotItem`). Une grille de
graphiques se vide par `removeLayoutItems`, une vue 3D par `resetGLView`.

Plomberie de démonstration : jamais montrée dans le code des étapes.
"""

from __future__ import annotations

from collections.abc import Iterable

import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import QGraphicsItem


def resetPlotItem(plotItem: pg.PlotItem) -> None:
    """Ramène un graphique à son état d'origine, tel qu'à sa création.

    Retire les éléments, la légende, le titre et les titres des axes ;
    remet l'espacement automatique des graduations, montre les axes, cache
    la grille, revient à l'échelle linéaire, délie les axes, libère les
    proportions, retire les limites, rend la souris aux deux axes en mode
    glisser, et réactive l'ajustement automatique de la zone visible, sur
    toutes les données.
    """
    plotItem.clear()
    plotItem.setTitle("")
    for axisName in ("bottom", "left"):
        plotItem.setLabel(axisName, "")
        plotItem.getAxis(axisName).setTickSpacing()
        plotItem.showAxis(axisName)
    plotItem.showGrid(x=False, y=False)
    plotItem.setLogMode(x=False, y=False)
    plotItem.setXLink(None)
    plotItem.setYLink(None)
    plotItem.setAspectLocked(False)
    viewBox = plotItem.getViewBox()
    # The ViewBox defaults: ±1e307 means no bound (None would break its comparisons), None no width limit.
    viewBox.setLimits(xMin=-1e307, xMax=1e307, yMin=-1e307, yMax=1e307, minXRange=None, maxXRange=None,
                      minYRange=None, maxYRange=None)
    viewBox.setMouseEnabled(x=True, y=True)
    viewBox.setMouseMode(pg.ViewBox.PanMode)
    viewBox.setAutoVisible(x=False, y=False)
    plotItem.enableAutoRange()
    removeLegend(plotItem)


def removeLegend(plotItem: pg.PlotItem) -> None:
    """Retire la légende d'un graphique : le prochain addLegend() en créera une neuve.

    Sans légende, ne fait rien.
    """
    if plotItem.legend is not None:
        if plotItem.legend.scene() is not None:
            plotItem.legend.scene().removeItem(plotItem.legend)
        plotItem.legend = None


def removeLayoutItems(layoutWidget: pg.GraphicsLayoutWidget, keep: Iterable[QGraphicsItem] = ()) -> None:
    """Retire de la grille d'un `GraphicsLayoutWidget` tous ses éléments, sauf ceux de `keep`.

    Un élément retiré quitte la grille et la scène : sa cellule redevient
    libre, et un `addPlot()` ou un `addItem()` peut la reprendre. Les
    éléments gardés restent dans leur cellule, sans être remis à zéro
    (voir `resetPlotItem`). Une grille vide ne change pas.

    Args:
        layoutWidget: La grille de graphiques.
        keep: Les éléments à laisser en place, par exemple les graphiques
            créés une seule fois dans `__init__`.
    """
    kept = set(map(id, keep))
    layout = layoutWidget.ci
    for item in list(layout.items):
        if id(item) not in kept:
            layout.removeItem(item)


def resetGLView(view: gl.GLViewWidget, distance: float = 10, elevation: float = 30, azimuth: float = 45) -> None:
    """Vide une vue 3D et remet sa caméra en place, centrée sur l'origine.

    Args:
        view: La vue 3D.
        distance: Distance de la caméra au centre.
        elevation: Hauteur de la caméra, en degrés au-dessus du plan XY.
        azimuth: Angle de la caméra autour de l'axe Z, en degrés.
    """
    view.clear()
    view.setCameraPosition(pos=QVector3D(0, 0, 0), distance=distance, elevation=elevation, azimuth=azimuth)
