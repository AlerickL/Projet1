"""Produit les images des œuvres qui illustrent une page, en PNG, et leur manifeste.

Outil de maintenance, jamais appelé par l'application. Chaque œuvre qui
illustre une page (`artworks.py`) est exécutée par l'atelier, sur une image
blanche de 480 × 360. Son image est écrite dans `assets/images/qpainter/`,
sous le nom de sa page (`introduction.png`, `chapter2.png`,
`chapter2-synthesis.png`). Le manifeste `artworks.json` associe chaque
titre à son fichier et à l'empreinte sha256 de son programme.

Seules les images absentes ou périmées (empreinte différente) sont refaites,
sauf avec `--all` : l'anticrénelage et les polices varient d'une machine à
l'autre, et une image à jour n'a pas à changer. Une image qui n'illustre plus
aucune page est supprimée.

Les polices doivent être réelles : sous la plateforme `offscreen`, lancer
avec `QT_QPA_FONTDIR` (sinon le texte s'affiche en carrés).

Lancement (depuis new/sf3) :
    python -m edustem.pyside6.learning_app.qpainter.render_artwork_images [--all]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from PySide6.QtGui import QGuiApplication, QImage, QImageWriter

from .artworks import Artwork, Artworks, ImagesFolder, ManifestPath, artworkFingerprint, renderArtwork

# The command that brings the images and their manifest up to date, as the tests quote it.
Command = "python -m edustem.pyside6.learning_app.qpainter.render_artwork_images"


def imageFileName(artwork: Artwork) -> str:
    """Le nom du fichier PNG d'une œuvre, d'après la page qu'elle illustre."""
    if artwork.chapter is None:
        return "introduction.png"
    return f"chapter{artwork.chapter}{'-synthesis' if artwork.synthesis else ''}.png"


def renderArtworkImages(*, everything: bool = False) -> None:
    """Refait l'image de chaque œuvre absente ou périmée, puis réécrit le manifeste.

    Args:
        everything: Refaire toutes les images, même à jour.
    """
    previous = json.loads(ManifestPath.read_text(encoding="utf-8")) if ManifestPath.is_file() else {}
    ImagesFolder.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for artwork in Artworks:
        if not artwork.illustrates:
            continue
        entry = {"file": imageFileName(artwork), "sha256": artworkFingerprint(artwork)}
        manifest[artwork.title] = entry
        path = ImagesFolder / entry["file"]
        if not everything and previous.get(artwork.title) == entry and path.is_file():
            continue
        image = renderArtwork(artwork).convertToFormat(QImage.Format.Format_RGB32)
        writer = QImageWriter(str(path))
        if not writer.write(image):
            raise OSError(f"{path}: {writer.errorString()}")
        print(f"qpainter/{path.name} : {artwork.title}, {path.stat().st_size // 1024} Ko")
    files = {entry["file"] for entry in manifest.values()}
    for path in ImagesFolder.glob("*.png"):
        if path.name not in files:
            path.unlink()
            print(f"qpainter/{path.name} : supprimée")
    ManifestPath.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(arguments: list[str] | None = None) -> int:
    """Point d'entrée en ligne de commande."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--all", action="store_true", help="refaire toutes les images, même à jour")
    options = parser.parse_args(arguments)
    _app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    if QGuiApplication.platformName() == "offscreen" and not os.environ.get("QT_QPA_FONTDIR"):
        parser.error("the offscreen platform needs QT_QPA_FONTDIR, or text is drawn as boxes")
    renderArtworkImages(everything=options.all)
    return 0


if __name__ == "__main__":
    sys.exit(main())
