<small>**C**égep du **V**ieux **M**ontréal&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;**S**ciences, **I**nformatique et **M**athématique</small><br><br>

# Structure de travail imposée

Tout le code du cours vit dans un seul dossier racine, `sf3`. Ce document en présente l'organisation : ce que chaque dossier contient, ce qui vous est fourni et ce que vous devez produire.

La structure repose sur trois idées simples :
- le code **fourni** (`edustem`) est séparé du code que vous **écrivez** (`projects`);
- dans chaque projet, le **modèle** (`model`) est séparé de l'**interface graphique** (`gui`);
- dans chaque projet, les documents **reçus** (`doc/in`) sont séparés des documents **à produire** (`doc/out`).

## 1. Vue d'ensemble

```
sf3/                                  racine : tout s'importe et se lance d'ici
│
├── p0_main.py                        lance le projet 0
├── p1_main.py                        lance le projet 1
├── p2_main.py                        lance le projet 2
├── learning_*.py                     lance le guide interactif sur le sujet *
│
├── edustem/                          bibliothèque fournie par l'enseignant
│   ├── generic/                      outils génériques
│   │   └── *.py                      fichiers Python utilitaires
│   ├── math/                         outils mathématiques
│   │   └── *.py                      fichiers Python utilitaires
│   └── pyside6/                      widgets Qt réutilisables
│       ├── q_*.py                    un widget par fichier
│       ├── demo/                     demo_q_*.py : une démonstration par widget
│       ├── assets/                   ressources utilisées par les widgets
│       └── learning_app/             guides interactifs d'apprentissage
│           ├── common/               outils partagés par les guides
│           ├── demo/                 démonstrations des outils des guides
│           ├── qpainter/             guide sur QPainter
│           └── ...                   les autres guides s'ajoutent en cours de session
│
└── projects/                         vos projets de la session
    ├── common/                       code partagé entre vos projets
    ├── p0/                           projet 0 (voir les détails ci-dessous)
    ├── p1/                           projet 1 (voir les détails ci-dessous)
    └── p2/                           projet 2 (voir les détails ci-dessous)
```

## 2. Structure d'un projet

Chaque projet suit la même organisation. Le projet 1 est utilisé ici comme exemple.

```
projects/p1/
│
├── __init__.py                       déclare le dossier comme paquet Python
├── __main__.py                       permet de lancer le projet comme module
├── main.py                           point d'entrée : la fonction main()
├── readme.md                         <<< documentation du projet
│
├── model/                            le modèle : calculs et données, sans Qt
│   ├── __init__.py                   déclare le dossier comme paquet Python
│   └── *.py                          vos modules, selon la norme PEP 8
│
├── gui/                              l'interface : les classes qui héritent de Qt
│   ├── __init__.py                   déclare le dossier comme paquet Python
│   └── q_*.py                        vos modules, selon la norme Qt
│
├── tests/                            OPTIONNEL : les tests de votre code
│   ├── __init__.py                   déclare le dossier comme paquet Python
│   └── test_*.py                     un fichier de tests par module testé
│
├── assets/                           OPTIONNEL : les ressources de l'application 
│   │                                             icônes, images, ...
│   └── .gitkeep                      garde le dossier dans git tant qu'il est vide
│
└── doc/                              documentation du projet
    │
    ├── in/                           ce que vous RECEVEZ : à lire, SANS MODIFIER
    │   ├── 420-SF3 Projet 1.md       énoncé du projet
    │   ├── assets/                   images utilisées par l'énoncé
    │   ├── guides/                   démarches : maquettage, diagramme de classes
    │   ├── informations/             règles : norme de codage, binôme, IA, structure
    │   └── rappels/                  notions mathématiques du projet
    │
    └── out/                          ce que vous PRODUISEZ
        ├── assets/                   images utilisées par vos documents
        │   └── *.png                 <<< images des maquettes et des diagrammes UML
        ├── mod/                      modélisation : mathématiques et sciences
        ├── des/                      conception : maquettes, diagrammes UML
        │   ├── maquettes.md          <<< assemblage de toutes les maquettes du GUI
        │   └── uml_modele.md         <<< assemblage de tous les diagrammes UML du modèle
        ├── final/                    remise : rapport final, autoévaluation
        │   ├── autoevaluation_equipe.xlsx <<< le fichier d'autoévaluation de l'équipe
        │   └── rapport_final.md      <<< le rapport final
        └── work/                     OPTIONNEL : documents de travail, 
                                                  sources des diagrammes et autres
```

À la racine du projet, `main.py` est le seul fichier de code : il crée l'application et la lance. Ce fichier est très court et contient uniquement le code nécessaire au démarrage. Tout le reste de votre code se répartit entre `model` et `gui`.

Les dossiers `tests` et `assets` sont optionnels. Ils sont fournis vides : utilisez-les si vous écrivez des tests ou si votre application a besoin de ressources, et laissez-les tels quels sinon.

### Les fichiers `_info.md`

Chaque sous-dossier de `doc/out` contient un fichier `_info.md`. **Lisez-le avant d'y déposer quoi que ce soit** : il précise la nature des documents attendus dans ce dossier, et où placer leurs images. Ces fichiers font partie de la structure imposée : on ne les supprime pas et on ne les modifie pas.

Le tableau suivant en donne un aperçu. Les fichiers `_info.md` restent la référence.

| Dossier | Contenu attendu |
| :--- | :--- |
| `doc/out/mod/` | Analyse mathématique et scientifique, formulation des équations, hypothèses, justification des modèles. |
| `doc/out/des/` | Documents `maquettes.md` et `uml_modele.md`, qui assemblent les maquettes de l'interface graphique et les diagrammes de classes UML du modèle, en version initiale et en version finale. Spécifications, scénarios d'utilisation. |
| `doc/out/final/` | Rapport final, autoévaluation d'équipe et autres documents de remise demandés. |
| `doc/out/assets/` | Images et graphiques insérés dans vos documents, dont les images des maquettes et des diagrammes UML (PNG recommandé). |
| `doc/out/work/` | Code source et fichiers de travail qui permettent de reproduire les diagrammes et les maquettes. Brouillons, calculs, notes de réunion. Optionnel : reste vide si vous n'en avez pas. |

## 3. Lancement et importation

Tout se lance **depuis le dossier `sf3`**. C'est ce qui permet aux importations de fonctionner partout de la même façon.

| Besoin | Commande ou instruction |
| :--- | :--- |
| Lancer un projet | `python p1_main.py` ou `python -m projects.p1` |
| Lancer un guide interactif | `python learning_qpainter.py` |
| Lancer la démonstration d'un widget | `python -m edustem.pyside6.demo.demo_q_color_box` |
| Importer un outil fourni | `from edustem.math.utils import clamp` |
| Importer un module de votre modèle | `from projects.p1.model.my_module import MyClass` |
| Importer un module de votre interface | `from projects.p1.gui.q_my_widget import QMyWidget` |

Une importation part toujours de la racine : elle commence par `edustem` ou par `projects`.

## 4. Règles à respecter

- Le dossier `edustem` est fourni : on l'utilise, on ne le modifie **jamais**.
- Le dossier `doc/in` est fourni : on le consulte, on ne le modifie **jamais**.
- Votre code va dans `projects/p1/`, et le code commun à plusieurs projets dans `projects/common/`.
- À la racine d'un projet, `main.py` est le seul fichier de code. Le reste va dans `model` ou dans `gui`.
- Les dossiers `tests` et `assets` sont optionnels. Si vous écrivez des tests ou ajoutez des ressources, c'est là qu'ils vont.
- Le dossier `model` ne contient aucune classe Qt et n'importe jamais `gui`. C'est `gui` qui importe `model`.
- Vos documents vont dans `doc/out/`, chacun dans le sous-dossier qui correspond à sa nature. Le fichier `_info.md` de chaque sous-dossier indique ce qu'on y attend.
- Les noms de fichiers suivent la [norme de codage](norme_de_codage.md).

Cette infrastructure de travail est imposée et doit être respectée.
