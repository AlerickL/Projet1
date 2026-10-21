"""Lecture des images d'illustration locales (`learning_app/assets/images/`).

Plomberie : chaque application range ses images d'introduction et de
synthèse dans `assets/images/<application>/`, avec un fichier
`images.json` qui donne, pour chaque clé, ses fichiers et sa légende. Le
document reste la seule source : aucune légende n'est recopiée dans le
code. Les images s'affichent ainsi sans réseau ; seul le lien de la
légende mène en ligne.

Chaque image existe en deux versions : l'original, dans `originals/`,
copié tel quel de sa source, et la version mise en forme, que
l'application affiche (`format_image_assets.py` la produit).
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import NamedTuple

from .q_step_walkthrough import QImageCaption

ImagesRoot = Path(__file__).resolve().parents[1] / "assets" / "images"


class ImageAsset(NamedTuple):
    """Une image locale et sa légende.

    `path` est le chemin de la version mise en forme, à passer comme
    `imageUrl` au moteur. `original` est le chemin de l'original, ou une
    chaîne vide quand la source n'est pas une image (un modèle 3D, dont on
    garde le rendu). `origin` est l'adresse d'où l'original a été copié.
    """

    path: str
    caption: QImageCaption
    origin: str
    original: str


@cache
def imageAssets(application: str) -> dict[str, ImageAsset]:
    """Les images d'une application, par clé (`introduction`, `chapter2`, `chapter2-synthesis`…).

    Raises:
        FileNotFoundError: L'application n'a pas de `images.json`, ou la version
            mise en forme d'une image manque. L'original peut manquer (export
            étudiant).
    """
    folder = ImagesRoot / application
    entries = json.loads((folder / "images.json").read_text(encoding="utf-8"))
    assets = {}
    for key, entry in entries.items():
        path = folder / entry["file"]
        if not path.is_file():
            raise FileNotFoundError(path)
        caption = QImageCaption(entry["title"], entry["author"], entry["source"], entry.get("note", ""),
                               entry.get("link", ""))
        # The original is not required at run time: the student export leaves the originals out.
        original = str(folder / "originals" / entry["original"]) if entry.get("original") else ""
        assets[key] = ImageAsset(str(path), caption, entry.get("origin", ""), original)
    return assets
