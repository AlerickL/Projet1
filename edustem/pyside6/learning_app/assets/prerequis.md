# Prérequis des applications d'apprentissage

Liste commune à tous les projets d'apprentissage d'edustem. Une
application n'enseigne jamais ce qui figure ici : elle le suppose connu,
et le déclare.

**Usage.** Chaque chapitre déclare, dans `addChapter(prerequisites=…)`,
les entrées qu'il emploie pour la première fois dans son application. Le
moteur les réunit dans la page « Prérequis » de l'application, une grille
groupée par catégorie de ce document (les titres `##`), avec le chapitre
de première utilisation. Une entrée déclarée dans un chapitre ne l'est plus dans les
suivants. Le sujet d'une application n'y figure jamais : une
application sur les layouts ne déclare pas les layouts en prérequis.

**Format.** Une entrée par puce : `- **clé** : description courte.` La
clé est le nom passé à `addChapter()`. Pour une classe, c'est le nom de
la classe entre accents graves, et chaque classe
du code affiché doit être déclarée ici ou présentée par une notion. Une
description tient sur une ligne ou se poursuit sur des lignes indentées.
Ajouter une entrée au besoin, sans détail : ce n'est pas un cours.

## Python

- **classes et méthodes** : définir une classe, `self` et ses attributs
  (`self.x`), appeler une méthode.
- **héritage** : hériter d'une classe, redéfinir une méthode, `super()`.
- **listes et tuples** : créer, indicer, parcourir, `append`.
- **compréhensions de liste** : `[f(x) for x in valeurs]`, un seul `for`.
- **dictionnaires** : créer, lire et écrire par clé, parcourir par `items()`.
- **boucles** : `for`, `range`, `enumerate`, `zip`, `while`.
- **f-strings** : `f"x = {x}"`.
- **annotations de type** : `x: int`, `-> None`, `QWidget | None` ; elles
  documentent le code, Python ne les vérifie pas.
- **décorateurs** : `@nom` sur la ligne au-dessus d'une fonction ou d'une
  méthode, qui la marque ou la transforme.
- **bloc `with`** : `with objet as nom:` ; l'objet est préparé à l'entrée
  du bloc et libéré à sa sortie.
- **modules et imports** : `import …`, `from … import …`.
- **module `math`** : ses constantes et fonctions, comme `math.pi`,
  `math.cos`, `math.sqrt`, `math.exp`.
- **module `random`** : un générateur à graine fixe, `uniform`.
- **énumérations** : les membres d'une énumération et leur `.value`.

## numpy

- **numpy de base** : `np.array`, `np.zeros`, `np.linspace`, indices,
  opérations sur tout un tableau.

## Mathématiques

- **trigonométrie** : cosinus, sinus, angles en degrés et en radians.
- **matrices de transformation** : rotation, échelle, translation (cours
  d'algèbre linéaire).
- **coordonnées dans l'espace** : x, y, z.

## Qt : concepts

- **application et widget** : `QApplication`, un widget, une fenêtre.
- **parent et enfant** : le parent d'un widget, ses enfants.
- **signaux et slots** : `signal.connect(slot)`.
- **accesseur et mutateur** : `value()` et `setValue()`.
- **constantes `Qt`** : l'espace de noms des constantes, comme
  `Qt.GlobalColor.white`.
- **layouts courants** : `QVBoxLayout`, `QHBoxLayout`, `addWidget()`.
- **drapeaux combinés** : l'opérateur `|` sur des drapeaux Qt.
- **police d'un widget** : `font()`, `setFont()`,
  `QFont.setPointSizeF()`.

## Qt : classes

- **`QWidget`** : le widget de base.
- **`QVBoxLayout`** : layout vertical.
- **`QHBoxLayout`** : layout horizontal.
- **`QLabel`** : étiquette de texte.
- **`QPushButton`** : bouton.
- **`QLineEdit`** : champ de texte d'une ligne.
- **`QTextEdit`** : zone de texte de plusieurs lignes.
- **`QSlider`** : sélecteur numérique ; son signal `valueChanged` est émis
  quand la valeur change.
- **`QSpinBox`** : boîte numérique entière.
- **`QDoubleSpinBox`** : boîte numérique décimale.
- **`QComboBox`** : liste déroulante ; `currentData()` rend la valeur du
  choix courant, et le signal `currentIndexChanged` est émis quand ce choix
  change.
- **`QCheckBox`** : case à cocher ; son signal `toggled` est émis quand
  elle est cochée ou décochée.
- **`QRadioButton`** : bouton radio, un choix parmi plusieurs.
- **`QListWidget`** : liste d'éléments.
- **`QMainWindow`** : fenêtre principale.
- **`QSplitter`** : séparateur ; range des widgets côte à côte ou l'un sous
  l'autre, et leur partage se règle à la souris par la poignée.
- **`Slot`** : le décorateur `@Slot(types)` de `PySide6.QtCore`, qui
  déclare une méthode comme slot ; les types sont ceux des arguments reçus.
- **`QAction`** : action d'un menu ou d'une barre d'outils.
- **`QFrame`** : cadre.
- **`QTimer`** : minuteur.
- **`QFileDialog`** : boîte de dialogue de fichier.
- **`QFont`** : police de caractères.
- **`QFontMetrics`** : mesures d'un texte dans une police.
- **`QPoint`** : point entier.
- **`QPointF`** : point réel.
- **`QRect`** : rectangle entier.
- **`QRectF`** : rectangle réel.
- **`QSize`** : taille entière.
- **`QVector3D`** : vecteur à trois composantes.
