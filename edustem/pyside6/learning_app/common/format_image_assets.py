"""Produit la version mise en forme des images d'illustration, depuis leur original.

Outil de maintenance, jamais appelé par les applications. Chaque image de
`assets/images/<application>/` existe en deux versions : l'original
(`originals/`), copié tel quel de sa source, et la version que
l'application affiche, réduite à une largeur donnée. Changer cette largeur
revient à relancer l'outil.

Règles :
- une image plus étroite que la largeur, ou un GIF animé, est copiée telle
  quelle (Qt ne réécrit pas un GIF animé) ;
- un SVG est rendu en PNG à la largeur voulue ;
- un JPEG reste un JPEG (qualité 90), un PNG reste un PNG.

Lancement (depuis new/sf3) :
    python -m edustem.pyside6.learning_app.common.format_image_assets [--width 960]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QGuiApplication, QImage, QImageReader, QImageWriter

from .image_assets import ImagesRoot

DefaultWidth = 960


def formatImage(original: Path, folder: Path, key: str, width: int) -> str:
    """Écrit la version mise en forme de `original` dans `folder` ; rend le nom du fichier écrit."""
    reader = QImageReader(str(original))
    size = reader.size()
    suffix = original.suffix.lower()
    animated = reader.supportsAnimation() and reader.imageCount() > 1
    if suffix != ".svg" and (animated or size.width() <= width):
        target = folder / (key + suffix)
        shutil.copyfile(original, target)
        return target.name
    reader.setScaledSize(QSize(width, round(width * size.height() / size.width())))
    image: QImage = reader.read()
    if image.isNull():
        raise ValueError(f"{original}: {reader.errorString()}")
    if suffix == ".svg":
        suffix = ".png"
    elif suffix in (".jpg", ".jpeg"):
        image = image.convertToFormat(QImage.Format.Format_RGB32)
    target = folder / (key + suffix)
    writer = QImageWriter(str(target))
    if suffix in (".jpg", ".jpeg"):
        writer.setQuality(90)
    if not writer.write(image):
        raise ValueError(f"{target}: {writer.errorString()}")
    return target.name


def formatApplication(folder: Path, width: int) -> None:
    """Refait la version mise en forme de chaque image d'une application, et met à jour `images.json`."""
    jsonPath = folder / "images.json"
    entries = json.loads(jsonPath.read_text(encoding="utf-8"))
    for key, entry in entries.items():
        if not entry.get("original"):
            continue  # No original image (e.g. a 3D model): the shown file is the source's own rendering.
        previous = folder / entry["file"]
        name = formatImage(folder / "originals" / entry["original"], folder, key, width)
        if previous.name != name and previous.exists():
            previous.unlink()
        entry["file"] = name
        print(f"{folder.name}/{name} : {(folder / name).stat().st_size // 1024} Ko")
    jsonPath.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(arguments: list[str] | None = None) -> int:
    """Point d'entrée en ligne de commande."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--width", type=int, default=DefaultWidth, help="largeur des versions mises en forme, en pixels")
    options = parser.parse_args(arguments)
    _app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    for jsonPath in sorted(ImagesRoot.glob("*/images.json")):
        formatApplication(jsonPath.parent, options.width)
    return 0


if __name__ == "__main__":
    sys.exit(main())
