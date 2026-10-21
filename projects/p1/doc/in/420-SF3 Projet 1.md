<small>**C**égep du **V**ieux **M**ontréal&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;**S**ciences, **I**nformatique et **M**athématique</small><br><br>

# 420-SF3 Projet 1

<a id="home"></a>
## Logiciel d'exploration de méthodes numériques

#### Table des matières
- [I. Introduction](#i-introduction)
- [II. Objectifs spécifiques du projet](#ii-objectifs-spécifiques-du-projet)
- [III. Spécifications fonctionnelles](#iii-spécifications-fonctionnelles)
- [IV. Contraintes](#iv-contraintes)
- [V. Rapport final et autoévaluation](#v-rapport-final-et-autoévaluation)
- [VI. Grille d'évaluation](#vi-grille-dévaluation)
- [Annexe 1 - Références](#annexe-1-references)
- [Annexe 2 - Notes techniques](#annexe-2-notes-techniques)

## I. Introduction
Ce projet consiste à développer une application informatique visant l'exploration de méthodes numériques. Le logiciel offrira à l'usager un outil interactif pour explorer ces méthodes et mieux comprendre leur fonctionnement.

Ce projet est le premier du cours 420-SF3-RM et vaut pour 20 % de la note finale du cours. Il constitue aussi la base de connaissances du premier examen. 

L'objectif principal de ce projet est de mettre en pratique les notions vues en classe depuis le début de votre DEC. Il ne suffit pas de produire un logiciel fonctionnel, il faut aussi démontrer une bonne maîtrise des concepts de programmation enseignés.

[↩️](#home)

## II. Objectifs spécifiques du projet

On divise les objectifs du projet en deux catégories : les objectifs fonctionnels et les objectifs de qualité. Dans les deux cas, on s'attend à ce que l'étudiant profite du projet pour mettre en pratique ces notions.

### A. Objectifs fonctionnels

Les objectifs fonctionnels du projet sont les suivants :
1. Le logiciel doit offrir une interface utilisateur intuitive et interactive autant que possible.
2. Le logiciel se divise en quatre parties principales : 
   - sélection et configuration de la fonction mathématique,
   - paramétrisation de la transformation canonique,
   - sélection et exploration de la technique d'analyse numérique,
   - un graphique affichant toutes les informations pertinentes de l'exploration en cours.
3. Deux méthodes d'analyse numérique doivent être implémentées :
    - dérivation numérique
    - intégration numérique d'aire
4. Quoique l'interactivité du graphique soit un atout important, il est recommandé de débuter le projet en provoquant la mise à jour du graphique manuellement via un bouton. Progressivement, un élément à la fois, vous ajusterez le logiciel pour offrir les interactions en temps réel.

### B. Objectifs de qualité

La note finale n'est pas exclusivement liée au respect des fonctionnalités demandées. Au contraire, une partie importante est attribuée en considération de la qualité du code et de la rigueur mathématique, en tenant compte des aspects suivants :
- structure de code d'un bon niveau et **modulaire** (*DRY*),
- qualité de la programmation **orientée objet** (abstraction, encapsulation, héritage, polymorphisme),
- utilisation pertinente des **structures de données** (choix adapté et analyse de la complexité pour justifier vos choix),
- utilisation juste de la bibliothèque de calcul numérique `NumPy` (utilisation intelligente du `ndarray` et vectorisation lorsque possible),
- utilisation juste de la bibliothèque graphique Qt `PySide6` (modularité, héritage, widgets personnalisés par composition, signaux et slots, ...),
- utilisation juste de la bibliothèque de graphiques `PyQtGraph` (graphique encapsulé dans un widget, éléments mis à jour plutôt que recréés lorsque possible),
- **qualité** générale du code : lisibilité, autodocumentation, commentaires, documentation, citation de ses sources, ...


[↩️](#home)

## III. Spécifications fonctionnelles

Les spécifications fonctionnelles du projet sont les suivantes :

- On désire un logiciel de bureau (*desktop application*).
- Pour chaque technique d'analyse numérique, quatre sections sont requises :
    1. un panneau de sélection de la fonction mathématique à analyser et de ses paramètres,
    2. un panneau permettant de configurer la transformation canonique,
    3. un panneau exploratoire de la méthode numérique,
    4. un graphique interactif affichant la courbe de la fonction et les résultats de la méthode.
- Il est possible de partager les panneaux de même nature (1, 2, 4 et autres) entre les différentes techniques d'analyse numérique. Toutefois, sachez que cette approche est un peu plus difficile et demande plus de travail. 

### Fonctions mathématiques à analyser

Vous devez implémenter quatre fonctions mathématiques à analyser numériquement, dont deux imposées et deux au choix. Le [catalogue de fonctions analytiques](./rappels/math_fonctions_suggerees.md) les présente toutes, avec leur dérivée et leur intégrale exactes. 

| Statut | Fonctions |
| :--- | :--- |
| Imposée | Une fonction trigonométrique : le sinus ou le cosinus (section 1 du catalogue). |
| Imposée | Un polynôme de degré $2$ ou plus, au choix (section 2 du catalogue), avec les coefficients par défaut donnés ci-dessous. |
| Au choix | Deux fonctions parmi les sections 3 à 7 du catalogue : la sinusoïde amortie, le battement, la double bosse, la saturation et la cloche hyperbolique asymétrique. |

Les coefficients par défaut du polynôme donnent une courbe intéressante sur l'intervalle $[-3, 3]$ : ses racines et ses extremums s'y trouvent.

| Degré | Polynôme par défaut | Coefficients par défaut |
| :---: | :--- | :--- |
| $2$ | $\frac{1}{2} x^2 - \frac{1}{2} x - 2$ | $c_0 = -2$, $c_1 = -\frac{1}{2}$, $c_2 = 0.5$ |
| $3$ | $\frac{1}{4} x^3 - \frac{3}{2} x$ | $c_0 = 0$, $c_1 = -\frac{3}{2}$, $c_2 = 0$, $c_3 = \frac{1}{4}$ |
| $4$ | $\frac{1}{10} x^4 - x^2 + \frac{1}{2}$ | $c_0 = \frac{1}{2}$, $c_1 = 0$, $c_2 = -1$, $c_3 = 0$, $c_4 = \frac{1}{10}$ |

> **Notes** 
> 
> - Une équipe peut implémenter un polynôme générique, dont le degré est lui-même un *meta-paramètre* déterminant le nombre de coefficients. Cette implémentation compte alors pour deux fonctions.
> - Pour la dernière, il est permis de proposer une fonction de votre choix à condition de fournir également sa dérivée et son intégrale exactes.

### Méthodes d'analyse numérique

Les méthodes d'analyse numérique à implémenter sont :
- [dérivation numérique](./rappels/math_analyse_numerique_derivation.md)
- [intégration numérique d'aire](./rappels/math_analyse_numerique_integration.md)

Pour les équipes intéressées, vous pouvez expérimenter d'autres méthodes d'analyse numérique. Ces ajouts ne sont ni exigés ni évalués. Par exemple :
- Le calcul numérique de la longueur d'arc. On remplace la courbe par une ligne brisée de $N$ segments, puis on additionne leurs longueurs.
- Le polynôme de Taylor. On approxime la fonction par un polynôme de Taylor d'ordre $n$ autour d'un point donné.
- La méthode de Newton-Raphson. On utilise une approche itérative pour trouver les racines de la fonction.

### Paramètre de configuration

Dans plusieurs contextes du projet, on doit définir la valeur d'un paramètre numérique (un nombre entier ou réel) servant à la configuration d'un aspect du projet. La récurrence de ce besoin impose de le gérer de manière claire et structurée.  

Un paramètre numérique doit inclure :
- un nom,
- une valeur minimale, maximale et par défaut,
- sa valeur actuelle modifiable par l'utilisateur,
- une description sommaire affichée en info-bulle,
- des instructions de formatage permettant la conversion du nombre en chaîne de caractères, incluant la précision du nombre, un préfixe ou un suffixe.

Dans le reste du document, on fera référence à ces composants par *paramètres numériques*.

### Panneau de sélection de la fonction mathématique

Le panneau de sélection de la fonction mathématique doit permettre à l'utilisateur de choisir la fonction à analyser ainsi que d'ajuster ses paramètres internes. Il doit inclure :

- Un menu déroulant pour sélectionner la fonction mathématique.
- Un champ de saisie pour chacun des *paramètres numériques* internes de la fonction.
- Un bouton permettant de réinitialiser les paramètres à leur valeur par défaut.
- Un bouton permettant d'afficher, dans une boîte de dialogue, une description détaillée de la fonction sélectionnée et de ses paramètres.

### Panneau de configuration de la transformation canonique

Le panneau de configuration de la [transformation canonique](./rappels/math_transformation_canonique.md) doit permettre à l'utilisateur de configurer la transformation canonique appliquée à la fonction mathématique. Il doit inclure :

- Quatre champs de saisie pour chacun des *paramètres numériques* de la transformation canonique.
- Des boutons réinitialisant les 4 paramètres pour des transformations connues : l'identité, la réflexion ($s_x = -1$) et l'inversion ($s_y = -1$).

### Panneau de visualisation de la fonction mathématique

Ce panneau doit afficher graphiquement la courbe de la fonction sélectionnée en tenant compte des paramètres internes et de la transformation canonique appliquée. Il doit inclure :
- Un titre principal.
- Une zone de tracé affichant la courbe.
- Des axes avec des titres, des graduations et des étiquettes.
- Une légende indiquant tous les constituants du graphique.
- Selon l'analyse numérique en cours, les informations supplémentaires indiquées dans les sections correspondantes doivent être affichées.

Comme mentionné, le graphique doit être dynamique et refléter en temps réel les modifications apportées aux divers paramètres de l'application (fonction, transformation et analyse numérique).

### Valeurs exactes et transformation canonique

Toutes les fonctions du catalogue ont une dérivée et une intégrale analytiques. Le catalogue les donne pour la fonction de référence $f$. Pour la fonction transformée $f_c$, la valeur exacte s'obtient en transformant ce résultat selon le rappel [Résultats d'une analyse après transformation canonique](./rappels/math_transformation_canonique_resultats.md), sans refaire l'analyse.

Une fonction sans dérivée ou sans intégrale analytique pourrait être ajoutée. Il faudrait alors adapter le modèle et l'affichage des erreurs. Toutefois, on recommande un développement progressif étape par étape de cette partie.

### Panneau exploratoire de la dérivation numérique

On utilise la méthode des différences finies pour la dérivation numérique (voir le document [`math_analyse_numerique_derivation.md`](./rappels/math_analyse_numerique_derivation.md)). Le panneau exploratoire doit inclure ces éléments :
- les intrants :
    - $x$, l'abscisse du point d'intérêt $P = (x, f(x))$ où la pente est évaluée
    - $h$, le pas de comparaison, exprimé dans l'unité de $x$
    - $\alpha$, le facteur de positionnement des deux points voisins autour de $P$
    - trois boutons permettant de déterminer rapidement la valeur de $\alpha$ :
        - `Avant` : $\alpha = 0.0$ (différence avant)
        - `Centrée` : $\alpha = 0.5$ (différence centrée)
        - `Arrière` : $\alpha = 1.0$ (différence arrière)
    - $r$, l'étendue de la partie visible de la courbe autour de $P$. Le graphique affiche la courbe entre $x - r$ et $x + r$. Ce paramètre ne sert pas au calcul de la dérivée, mais uniquement à l'affichage.
- les extrants :
    - résultats numériques :
        - $\widehat{m}$, la pente approchée de la courbe en $P$, issue de la dérivation numérique
        - $m$, la pente exacte de la courbe en $P$, issue du calcul analytique
        - $E_a$, l'erreur absolue : $E_a = \widehat{m} - m$
        - $E_r$, l'erreur relative : $E_r = \displaystyle \frac{E_a}{m}$, si $m \neq 0$
    - s'ajoutent au graphique :
        - le point $P$
        - la tangente à la courbe en $P$
        - les deux points voisins $P_-$ et $P_+$ définissant l'intervalle d'évaluation autour de $P$
        - la droite passant par ces deux points voisins.
- les actions :
    - un bouton permet de réinitialiser les paramètres à leur valeur par défaut.
    - un bouton permet d'afficher une description de la méthode par une boîte de dialogue.
    - tout changement des intrants doit mettre à jour automatiquement le graphique et les extrants.

### Panneau exploratoire de l'intégration d'aire numérique

On utilise les méthodes des rectangles et des trapèzes pour l'intégration numérique d'aire (voir le document [`math_analyse_numerique_integration.md`](./rappels/math_analyse_numerique_integration.md)). Le panneau exploratoire doit inclure ces éléments :
- les intrants :
    - $a$ et $b$, les bornes d'intégration sur l'axe des $x$ (attention, on veut garantir que $a < b$)
    - $N$, le nombre de sous-intervalles entre les bornes
    - deux méthodes d'intégration sélectionnables par l'utilisateur :
        - la méthode des rectangles
        - la méthode des trapèzes
    - seulement pour la méthode des rectangles :
        - $\alpha$, le facteur de positionnement du point d'évaluation dans chaque sous-intervalle
        - trois boutons permettant de déterminer rapidement la valeur de $\alpha$ :
            - `Gauche` : $\alpha = 0.0$
            - `Milieu` : $\alpha = 0.5$
            - `Droite` : $\alpha = 1.0$
- les extrants :
    - résultats numériques :
        - $\widehat{I}$, la valeur approchée de l'intégrale entre les bornes, issue de l'intégration numérique
        - $I$, la valeur exacte de l'intégrale entre les bornes, issue du calcul analytique
        - $E_a$, l'erreur absolue : $E_a = \widehat{I} - I$
        - $E_r$, l'erreur relative : $E_r = \displaystyle \frac{E_a}{I}$, si $I \neq 0$
    - s'ajoutent au graphique :
        - une forme géométrique par sous-intervalle : un rectangle ou un trapèze, selon la méthode.
- les actions :
    - un bouton permet de réinitialiser les paramètres à leur valeur par défaut.
    - un bouton permet d'afficher une description de la méthode par une boîte de dialogue.
    - tout changement des intrants doit mettre à jour automatiquement le graphique et les extrants.

### Résumé des exigences

Les tableaux suivants résument les exigences détaillées dans les sections précédentes.

#### Exigences générales

| Exigence | Contrainte |
| :--- | :--- |
| Type de logiciel | Application de bureau (*desktop application*) |
| Fonctions mathématiques | Quatre fonctions : <br> 1. Sinus ou cosinus (imposée) <br> 2. Polynôme de degré $2$ ou plus, avec les coefficients par défaut (imposée) <br> 3. et 4. Deux fonctions au choix parmi les sections 3 à 7 du catalogue |
| Méthodes numériques | Deux méthodes imposées : <br> 1. Dérivation numérique <br> 2. Intégration numérique d'aire |
| Sections de l'interface | 1. Sélection de la fonction <br> 2. Transformation canonique <br> 3. Exploration de la méthode numérique <br> 4. Graphique |
| Langage de programmation | `Python` |
| Bibliothèques à utiliser | `NumPy` <br> `PySide6` <br> `PyQtGraph` |
| Bibliothèques interdites | Toute autre bibliothèque, par exemple `SymPy`, `SciPy` et `Matplotlib` |
| Mise à jour de l'affichage | Automatique à tout changement d'un intrant (développement progressif recommandé) |

#### Paramètre numérique

Chaque *paramètre numérique* du logiciel réunit les composants suivants.

| Composant | Description |
| :--- | :--- |
| Nom | Identifie le paramètre dans l'interface |
| Valeur minimale | Borne inférieure permise |
| Valeur maximale | Borne supérieure permise |
| Valeur par défaut | Valeur initiale, rétablie lors d'une réinitialisation |
| Valeur actuelle | Valeur modifiable par l'utilisateur |
| Description | Texte sommaire affiché en info-bulle |
| Formatage | Conversion du nombre en texte : précision, préfixe et suffixe |

#### Panneaux communs

| Panneau | Élément | Description |
| :--- | :--- | :--- |
| Sélection de la fonction | Choix de la fonction | Menu déroulant |
| | Paramètres internes | Un champ de saisie par *paramètre numérique* de la fonction sélectionnée |
| | Actions | 1. Bouton réinitialisant les paramètres à leur valeur par défaut <br> 2. Bouton affichant, dans une boîte de dialogue, la description de la fonction et de ses paramètres |
| Transformation canonique | Paramètres | Un champ de saisie pour chacun des 4 *paramètres numériques* : <br> 1. Translation horizontale $\delta_x$ <br> 2. Translation verticale $\delta_y$ <br> 3. Échelle horizontale $s_x$ <br> 4. Échelle verticale $s_y$ |
| | Réinitialisation | Boutons fixant les 4 paramètres pour la transformation identité |
| Visualisation | Contenu | 1. Titre principal <br> 2. Zone de tracé affichant la courbe de la fonction <br> 3. Axes avec titres, graduations et étiquettes <br> 4. Légende de tous les constituants du graphique <br> 5. Ajouts propres à la méthode numérique en cours |
| | Comportement | Le tracé tient compte des paramètres internes de la fonction et de la transformation canonique |

#### Méthodes numériques

| | Dérivation | Intégration d'aire |
| :--- | :--- | :--- |
| Document de référence | [`math_analyse_numerique_derivation.md`](./rappels/math_analyse_numerique_derivation.md) | [`math_analyse_numerique_integration.md`](./rappels/math_analyse_numerique_integration.md) |
| Intrants | 1. Point d'intérêt $P$, défini par son abscisse $x$ <br> 2. Pas $h$ <br> 3. Facteur de positionnement $\alpha$ <br> 4. Étendue visible $r$ (affichage seulement) | 1. Bornes $a$ et $b$, avec $a < b$ <br> 2. Nombre de sous-intervalles $N$ <br> 3. Méthode : rectangles ou trapèzes <br> 4. Facteur de positionnement $\alpha$ (rectangles seulement) |
| Raccourcis pour $\alpha$ | `Avant` : $\alpha = 0.0$ <br> `Centrée` : $\alpha = 0.5$ <br> `Arrière` : $\alpha = 1.0$ | `Gauche` : $\alpha = 0.0$ <br> `Milieu` : $\alpha = 0.5$ <br> `Droite` : $\alpha = 1.0$ <br> (rectangles seulement) |
| Valeur approchée | $\widehat{m}$, la pente de la courbe en $P$ | $\widehat{I}$, l'intégrale entre les bornes |
| Valeur exacte | $m$, la pente exacte en $P$ | $I$, l'intégrale exacte entre les bornes |
| Ajouts au graphique | 1. Le point $P$ <br> 2. La tangente à la courbe en $P$ <br> 3. Les deux points voisins $P_-$ et $P_+$ autour de $P$ <br> 4. La droite passant par ces deux points | Une forme géométrique par sous-intervalle : rectangle ou trapèze |

#### Éléments communs à toutes les méthodes

Dans ce tableau, $\widehat{v}$ désigne la valeur approchée et $v$ la valeur exacte, comme dans le [lexique](./rappels/math_lexique.md).

| Élément | Description |
| :--- | :--- |
| Résultats affichés | 1. Valeur approchée $\widehat{v}$ <br> 2. Valeur exacte $v$, transformée selon la transformation canonique <br> 3. Erreur absolue $E_a = \widehat{v} - v$ <br> 4. Erreur relative $E_r = \dfrac{E_a}{v}$, si $v \neq 0$ |
| Actions | 1. Bouton réinitialisant les paramètres à leur valeur par défaut <br> 2. Bouton affichant, dans une boîte de dialogue, la description de la méthode |
| Mise à jour | Tout changement d'un intrant met à jour le graphique et les résultats |

### Éléments de conception logicielle

Avant d'entamer le développement, vous devez produire un document de conception UML détaillant les classes et les interactions entre elles. Rappelez-vous que seules les classes associées au modèle sont requises. Les classes de l'interface utilisateur ne sont pas à modéliser.

On s'attend à ce que le document de conception UML inclue toutes les classes du modèle ainsi que leurs relations, telles que l'héritage, la composition, l'agrégation et la dépendance. Les diagrammes doivent suivre les conventions établies dans la norme de codage du cours. 

On met à votre disposition une conception préliminaire de la gestion des fonctions mathématiques. Ce diagramme est incomplet et n'est pas imposé strictement. Vous pouvez l'adapter à votre guise. D'ailleurs, il est impossible de réaliser le projet tel quel sans y apporter des modifications. Vous pouvez l'ignorer et repartir de zéro si vous le souhaitez. Toutefois, sachez que vous devez valoriser les notions de la programmation orientée objet et que la note finale en tiendra fortement compte. 

Le diagramme suivant introduit les classes du modèle :
- `Information`
- `Parameter`
- `MathFunction`
- `SinFunction`
- `CanonicalTransformation`

<p align="center">
  <img src="assets/uml_model_math_function_prototype.png" width="1000" alt="Diagramme de classes UML pour le modèle des fonctions mathématiques">
</p>

Aucun diagramme de classes UML n'est fourni pour amorcer la conception des modèles associés aux méthodes numériques. Toutefois, on peut s'attendre à ce que des classes spécifiques soient définies pour encapsuler la logique de ces méthodes. C'est à vous de valoriser au maximum vos compétences à cet effet. Votre conception devra refléter cette approche orientée objet.

Dans tous les cas, on peut s'attendre à voir minimalement les classes suivantes :
- `NumericalDifferentiation`
- `NumericalIntegrationArea`

Dans toutes les classes du modèle, l'utilisation de `NumPy` est attendue là où des calculs numériques sont nécessaires.

Finalement, on vous suggère de faire plusieurs diagrammes de classes UML pour faciliter la production et la lecture de votre conception.

#### Considérations pour les classes de l'interface graphique utilisateur

Même si vous n'avez pas à produire de conception UML pour cette partie, vous devez tout de même produire un code réutilisable et bien organisé.

On peut imaginer avoir minimalement une classe par panneau :
- `QMathFunctionPanel`
- `QCanonicalTransformationPanel`
- `QNumericalDifferentiationPanel`
- `QNumericalIntegrationAreaPanel`

Toutes ces classes héritent de `QWidget` et exploitent habilement les constituants du modèle.

Elles possèdent toutes :
- des accesseurs et des mutateurs leur permettant de manipuler les paramètres,
- des signaux et connecteurs (*slots*) permettant de réagir aux changements de paramètres.

Pour construire ces panneaux, la bibliothèque `edustem` met à votre disposition des widgets et des classes utilitaires. Le [catalogue des widgets](../../../../edustem/pyside6/widgets/doc/catalogue_widgets.md) présente brièvement chacun d'eux.

L'[annexe 2 - Notes techniques](#annexe-2-notes-techniques) présente quelques notions utilitaires pour le projet. Par exemple, on y retrouve une fonction vidant un *layout* et ses constituents.


[↩️](#home)

## IV. Contraintes 

On divise les contraintes en deux catégories : les contraintes techniques et les contraintes de gestion de projet.

### A. Contraintes techniques

- Les technologies à utiliser sont :
    - `Python`
    - `PySide6`
    - `PyQtGraph`
    - `NumPy`
    - `Visual Studio Code`
    - Dans tous les cas, on utilisera les versions correspondantes aux environnements de l'école.
- Les documents de conception suivants sont attendus :
    - vous devez faire une maquette relativement détaillée de votre interface utilisateur
    - vous devez produire un diagramme de classes UML présentant toutes les classes nécessaires au modèle, principalement : 
        - les fonctions mathématiques
        - les méthodes d'analyse numérique
        - **important** :
            - il est attendu que vous produisiez ces documents avant de commencer le développement
            - ces documents ne doivent pas être parfaits et peuvent évoluer au cours du développement
            - ces documents doivent être produits en équipe et validés par tous les membres avant de commencer
            - il ne faut pas modéliser les classes de l'interface utilisateur
- Le code doit suivre la [`norme_de_codage`](./informations/norme_de_codage.md) du cours.
- Pour `NumPy` :
    - vous devez utiliser `ndarray` pour les calculs numériques
    - vous devez éviter les boucles `for` lorsque possible en utilisant la vectorisation
- L'interface utilisateur avec `PySide6` :
    - l'interface utilisateur doit être conçue en code (pas de `*.ui` généré par Qt Designer)
    - l'interface utilisateur doit être modulaire et réutilisable (création de widgets personnalisés composés de widgets)
    - l'interface utilisateur doit utiliser les signaux et slots pour la communication entre les composants
    - l'interface utilisateur doit être *responsive* (utilisation pertinente des *layouts* en ne fixant pas de tailles absolues sauf pour quelques cas particuliers).
- Le graphique avec `PyQtGraph` :
    - le graphique doit être produit avec `PyQtGraph`
    - le graphique doit être encapsulé dans un widget personnalisé basé sur `PlotWidget`, qui s'intègre aux *layouts* comme tout autre widget
    - les données tracées doivent être transmises directement sous forme de `ndarray`, sans conversion en liste
    - chaque constituant du graphique (courbe, point d'intérêt, points voisins, tangente, rectangles, ...) doit être un élément distinct, identifié dans la légende lorsque possible
    - lorsque possible, les éléments du graphique sont créés une seule fois, puis mis à jour à chaque changement (par exemple avec `setData`), plutôt que détruits et recréés. Les éléments dont le nombre varie, comme les rectangles ou les trapèzes, peuvent être recréés (voir l'[annexe 2 - Notes techniques](#annexe-2-notes-techniques))
    - le zoom et le déplacement à la souris offerts par `PyQtGraph` peuvent rester fonctionnels
    - à terme, le graphique doit suivre en temps réel toutes les modifications des intrants ; il est toutefois recommandé de débuter le projet en provoquant la mise à jour du graphique via un bouton.
- Le logiciel ne doit pas *planter* dans des conditions normales d'utilisation. Vous devez gérer les erreurs et les exceptions de manière appropriée. On mettra l'accent sur ces aspects :
    - validation des intrants utilisateur
    - gestion des erreurs de calcul (division par zéro, racine carrée de nombre négatif, logarithme de nombre négatif, ...)
    - messages d'erreur clairs et informatifs pour l'utilisateur
- Produit final
    - L'enseignant vous présentera l'exemple d'un logiciel fonctionnel pour le projet. 
    - Toutefois, gardez en tête que ce n'est qu'un exemple. 
    - Autrement dit, vous avez pleine liberté pour produire la forme du logiciel qui vous inspire, pourvu que vous répondiez aux exigences fonctionnelles et techniques du projet.

### B. Contraintes de gestion de projet

- Projet d'équipe :
    - Le projet doit être réalisé en équipe de quatre étudiants. Si le nombre d'étudiants inscrits dans la classe ne permet pas de former des équipes de quatre, des ajustements seront faits par l'enseignant.
    - Chaque étudiant doit contribuer de manière significative au projet. 
    - Un fichier d'autoévaluation est à remplir par l'équipe à la fin du projet (cette évaluation sera prise en compte dans la note finale en pondérant l'implication de chacun).
    - La programmation en binôme (*pair programming*) doit être au premier plan (voir le document [`programmation_binome`](./informations/programmation_binome.md)).
    - Chaque équipe possède deux sous-équipes de deux personnes.
    - La permutation des membres des sous-équipes doit être fréquente (maximum 1 heure entre chaque permutation).
- Étapes de développement recommandées :
    - **Planification** : 
        - Assurez-vous de bien comprendre le projet, ses objectifs et les fonctionnalités attendues. Le projet est costaud et beaucoup de documents sont mis à votre disposition.
        - Il est important de bien lire ce document et d'en clarifier le contenu avec vos collègues de travail d'abord et avec l'enseignant ensuite.
        - Rédigez un plan de projet avec des jalons et des échéances.
        - Divisez les tâches entre les membres de l'équipe en fonction de leurs compétences et intérêts.
    - **Conception** : 
        - Produisez une maquette détaillée de l'interface utilisateur.
        - Faites la conception UML (diagramme de classes) des classes du modèle : les fonctions mathématiques et les méthodes d'analyse numérique.
        - Il est important que tous les membres de l'équipe comprennent et approuvent la conception avant de commencer le développement.
    - **Développement** : 
        - Formez des sous-équipes de deux personnes et répartissez les tâches selon les divisions faites lors de la planification.
        - Codez les fonctionnalités en vous assurant de tester régulièrement votre code.
        - La programmation en binôme (*pair programming*) doit être au premier plan.
- Structure de dossiers et remise du projet :
    - La remise du projet doit inclure tous les fichiers et dossiers nécessaires au bon fonctionnement du code, les documents produits et tous les documents initialement fournis.
    - Le projet doit être remis avant la date limite indiquée.
    - Toute forme de plagiat ou de tricherie entraînera des sanctions sévères conformément aux politiques académiques de l'institution. Si vous avez des questions sur ce qui est permis ou non, n'hésitez pas à les poser.
    - La remise du projet se fait via Moodle à raison d'une remise par équipe.
    - Vous devez maintenir votre projet fonctionnel dans la structure de travail stricte qui vous est imposée. Référez-vous au document [`structure_projet`](./informations/structure_projet.md).
    - Le fichier `readme.md` présente votre projet à quiconque ouvre le dépôt. Un gabarit vous est fourni à la racine du projet. Complétez chacune de ses sections, puis retirez les consignes en italique. Il doit contenir :
        - une présentation sommaire du logiciel : ce qu'il fait et à qui il s'adresse,
        - les technologies utilisées, avec leur version,
        - la commande de lancement, déjà fournie, à garder exacte,
        - le nom de chaque membre de l'équipe.

### C. Fichiers à modifier et à produire pour la remise

L'arborescence suivante liste tous les fichiers attendus à la remise. Un fichier **à modifier** vous est fourni et vous le complétez. Un fichier **à créer** n'existe pas encore.

```
projects/p1/
│
├── main.py                              À MODIFIER : point d'entrée de votre application
├── readme.md                            À MODIFIER : présentation, technologies, lancement, auteurs
│
├── model/
│   └── *.py                             À CRÉER : code, classes du modèle, sans Qt
│
├── gui/
│   └── q_*.py                           À CRÉER : code, classes de l'interface graphique
│
└── doc/out/
    ├── assets/
    │   └── *.png                        À CRÉER : images insérées dans les documents de des/,
    │                                               soit les maquettes et les diagrammes UML,
    │                                               en version initiale et en version finale
    ├── des/
    │   ├── maquettes.md                 À MODIFIER : assemblage des maquettes
    │   └── uml_modele.md                À MODIFIER : assemblage des diagrammes UML
    └── final/
        ├── rapport_final.md             À MODIFIER : rapport final
        ├── autoevaluation_equipe.xlsx   À MODIFIER : autoévaluation de l'équipe
        └── commentaires_et_coquilles.md OPTIONNEL : commentaires sur le projet
```

Sont aussi optionnels : les tests (`tests/test_*.py`), les ressources de l'application (`assets/`) et vos fichiers de travail (`doc/out/work/`).

Aucun autre fichier fourni ne doit être modifié, notamment les fichiers `__init__.py`, `__main__.py` et `_info.md`, ainsi que tout le contenu de `doc/in/` et de `edustem/`. Le document [`structure_projet`](./informations/structure_projet.md) présente la structure complète.

[↩️](#home)

## V. Rapport final et autoévaluation

À la fin du projet, vous avez un rapport final à produire. 

Le rapport consiste à répondre à des questions spécifiques reliées au projet. Le document existe déjà ([`doc/out/final/rapport_final.md`](../out/final/rapport_final.md)) et est prêt à accueillir vos réponses.

Vous y retrouverez tous les détails nécessaires pour compléter ce rapport. Voici tout de même les grandes lignes :
- Identification des membres de l'équipe
- Respect des exigences
- Discussions techniques
    - Conception et modélisation
    - Structures de données
    - Paradigme de programmation orientée objet
    - Interprétation du mandat
- Évaluation individuelle

N'oubliez pas que vous devez **obligatoirement** remplir en équipe le document [`doc/out/final/autoevaluation_equipe.xlsx`](../out/final/autoevaluation_equipe.xlsx). 

[↩️](#home)

## VI. Grille d'évaluation 

La grille d'évaluation suivante illustre les critères qui seront utilisés pour évaluer votre projet ainsi que la pondération de chaque élément.

| Catégorie | Critère | Pondération |
| :--- | :--- | ---: |
| <br> **Documents de conception** |  | <br> **10 %** |
| - Diagramme de classes UML *7 %* | - Niveau de détail <br> - Exploitation des concepts orientés objet <br> - Qualité de la présentation | 2 % <br> 4 % <br> 1 % |
| - Maquette de l'interface utilisateur *3 %* | - Niveau de détail <br> - Qualité de la présentation | 2 % <br> 1 % |
| <br> **Respect et qualité des spécifications** |  | <br> **64 %** |
| - Interface utilisateur *3 %* | - Intuitive <br> - Interactive <br> - Robustesse de l'application dans l'ensemble des scénarios d'usage | 1 % <br> 1 % <br> 1 % |
| - Fonctions mathématiques *15 %* | - Modèle : <br> &nbsp; - Classe abstraite (ex : `MathFunction`) et dépendances <br> &nbsp; - 4 classes concrètes : 2 fonctions imposées et 2 au choix (un polynôme générique compte pour deux) <br> &nbsp; - Gestion des *paramètres numériques* <br> &nbsp; - Utilisation adéquate de `NumPy` (*vectorisation*) <br> - IUG : <br> &nbsp; - Sélection de la fonction <br> &nbsp; - Configuration de tous les paramètres de la fonction <br> &nbsp; - Bouton de réinitialisation <br> &nbsp; - Bouton d'information sur la fonction <br> &nbsp; - Réalisation technique par un *widget* autonome | <br> 3 % <br> 3 % <br> 1 % <br> 1 % <br><br> 1 % <br> 2 % <br> 1 % <br> 1 % <br> 2 % |
| - Transformation canonique *6 %* | - Modèle : <br> &nbsp; - Classe de transformation applicable à toutes les fonctions <br> - IUG : <br> &nbsp; - Configuration des 4 paramètres <br> &nbsp; - Boutons de préréglage (identité, réflexion et inversion) <br> &nbsp; - Réalisation technique par un *widget* autonome | <br> 2 % <br><br> 1 % <br> 1 % <br> 2 % |
| - Graphique *9 %* | - Titre, axes (titres, graduations et étiquettes) et légende <br> - Tracé de la courbe selon ses paramètres et la transformation canonique <br> - Mise à jour en temps réel <br> - Réalisation technique avec `PyQtGraph` par un *widget* autonome | 2 % <br> 3 % <br> 3 % <br> 1 % |
| - Dérivation numérique *15 %* | - Modèle : <br> &nbsp; - Classe de gestion de la méthode numérique <br> &nbsp; - Utilisation adéquate de `NumPy` (*vectorisation*) <br> - IUG : <br> &nbsp; - Paramétrisation de la méthode (4 paramètres et raccourcis pour $\alpha$) <br> &nbsp; - Exactitude et affichage des résultats : valeur approchée, valeur exacte transformée, erreurs <br> &nbsp; - Ajouts au graphique (4 éléments) <br> &nbsp; - Boutons de réinitialisation et d'information <br> &nbsp; - Réalisation technique par un *widget* autonome | <br> 4 % <br> 1 % <br><br> 3 % <br> 2 % <br> 3 % <br> 1 % <br> 1 % |
| - Intégration numérique d'aire *16 %* | - Modèle : <br> &nbsp; - Classe de gestion de la méthode numérique (rectangles et trapèzes) <br> &nbsp; - Utilisation adéquate de `NumPy` (*vectorisation*) <br> - IUG : <br> &nbsp; - Paramétrisation de la méthode (bornes, sous-intervalles, méthode, $\alpha$ et ses raccourcis) <br> &nbsp; - Exactitude et affichage des résultats : valeur approchée, valeur exacte transformée, erreurs <br> &nbsp; - Ajouts au graphique (rectangles ou trapèzes) <br> &nbsp; - Boutons de réinitialisation et d'information <br> &nbsp; - Réalisation technique par un *widget* autonome | <br> 5 % <br> 1 % <br><br> 3 % <br> 2 % <br> 3 % <br> 1 % <br> 1 % |
| <br> **Respect des objectifs** |  | <br> **16 %** |
| - Qualité générale *11 %* | - Structure de code adaptée et modulaire <br> - Qualité de la programmation orientée objet <br> - Utilisation pertinente des structures de données <br> - Utilisation juste de la bibliothèque `NumPy` <br> - Utilisation juste de la bibliothèque `PySide6` <br> - Utilisation juste de la bibliothèque `PyQtGraph` <br> - Qualité générale du code <br> - Remise adéquate et respect de la structure de travail imposée <br> - Fichier `readme.md` complet | 2 % <br> 2 % <br> 1 % <br> 1 % <br> 1 % <br> 1 % <br> 1 % <br> 1 % <br> 1 % |
| - Contraintes techniques *5 %* | - Respect de la norme de codage du cours <br> - Qualité de la `docstring` <br> - Interface conçue en code, avec des *layouts* adaptatifs <br> - Communication entre les composants par signaux et slots | 2 % <br> 1 % <br> 1 % <br> 1 % |
| <br> **Rapport** |  | <br> **10 %** |
| - Respect des exigences *1 %* | - Déclaration complète et exacte des exigences partiellement ou non fonctionnelles | 1 % |
| - Conception et modélisation *3 %* | - Utilité du diagramme de classes UML et de la maquette <br> - Écarts entre la conception initiale et le logiciel remis | 1 % <br> 2 % |
| - Qualité de la conception *3 %* | - Choix et justification d'une structure de données <br> - Concepts de la POO illustrés par le code de l'équipe | 1 % <br> 2 %|
| - Interprétation du mandat *1 %* | - Zone d'ombre identifiée et décision justifiée | 1 % |
| - Évaluation individuelle *2 %* | - Contribution, défi surmonté et réflexion sur le projet | 2 % |
| | | *100 %* |


[↩️](#home)


## Annexes

<a id="annexe-1-references"></a>
### Annexe 1 - Références

Consultez les documents suivants :
- comme guide de production technique :
    - [Le maquettage d'une interface graphique](./guides/maquettage_interface_graphique.md)
    - [Le diagramme de classes UML](./guides/diagramme_classes_uml.md)
- pour les outils fournis par la bibliothèque `edustem` :
    - [Catalogue des widgets fournis](../../../../edustem/pyside6/widgets/doc/catalogue_widgets.md)
    - les guides interactifs sur `QPainter` et sur `PyQtGraph`, lancés depuis le dossier `sf3` par `python learning_qpainter.py` et `python learning_pyqtgraph.py` (voir le [`readme.md`](../../readme.md) du projet)
- pour un rappel des notions mathématiques nécessaires à ce projet :
    - [Lexique des rappels mathématiques](./rappels/math_lexique.md)
    - [Transformation canonique d'une fonction](./rappels/math_transformation_canonique.md)
    - [Résultats d'une analyse après transformation canonique](./rappels/math_transformation_canonique_resultats.md)
    - [Catalogue de fonctions analytiques](./rappels/math_fonctions_suggerees.md)
    - [Techniques de dérivée numérique](./rappels/math_analyse_numerique_derivation.md)
    - [Méthodes d'intégration numérique](./rappels/math_analyse_numerique_integration.md)
- à titre de rappel des informations générales sur le projet :
    - [Structure de travail imposée](./informations/structure_projet.md)
    - [Norme de codage](./informations/norme_de_codage.md)
    - [La programmation en binôme](./informations/programmation_binome.md)
    - [Mises en garde concernant l'utilisation de l'intelligence artificielle](./informations/mises_en_garde_ia.md)

Plus largement, vous pouvez aussi consulter ces ressources en ligne pour vous aider dans le développement :
- Mathématiques : articles Wikipédia :
    - [Dérivée](https://fr.wikipedia.org/wiki/D%C3%A9riv%C3%A9e)
    - [Différences finies](https://fr.wikipedia.org/wiki/Diff%C3%A9rences_finies)
    - [Intégrale définie](https://fr.wikipedia.org/wiki/Int%C3%A9grale_d%C3%A9finie)
    - [Calcul numérique d'une intégrale](https://fr.wikipedia.org/wiki/Calcul_num%C3%A9rique_d%27une_int%C3%A9grale)

- Informatique : documentation officielle :
    - [Python](https://docs.python.org/3/)
    - [PySide6](https://doc.qt.io/qtforpython/)
    - [PyQtGraph](https://pyqtgraph.readthedocs.io/en/latest/)
    - [NumPy](https://numpy.org/doc/)

[↩️](#home)

<a id="annexe-2-notes-techniques"></a>
### Annexe 2 - Notes techniques

#### 1. Vider un layout

Pour vider un layout de tous ses éléments, quel que soit son type (`QVBoxLayout`, `QHBoxLayout`, `QGridLayout`, `QFormLayout`, `QStackedLayout`, ...), vous pouvez utiliser la fonction utilitaire `clearLayout` suivante. Elle vide aussi les sous-layouts et retire les espacements (`addStretch`, `addSpacing`, ...).

```python
from PySide6.QtWidgets import QFormLayout, QLayout, QLayoutItem


def clearLayout(layout: QLayout) -> None:
    """Retire tous les éléments d'un layout, quel que soit son type.

    Les widgets retirés n'ont plus de parent : sans autre référence, ils sont
    détruits. Les sous-layouts sont vidés de la même façon. Les espacements
    sont simplement retirés.

    Args:
        layout (QLayout): Le layout à vider.
    """
    if isinstance(layout, QFormLayout):
        # takeRow() retire aussi la ligne, alors que takeAt() laisserait des lignes vides.
        while layout.rowCount() > 0:
            row = layout.takeRow(0)
            releaseLayoutItem(row.labelItem)
            releaseLayoutItem(row.fieldItem)
    else:
        while layout.count() > 0:
            releaseLayoutItem(layout.takeAt(0))


def releaseLayoutItem(item: QLayoutItem | None) -> None:
    """Libère un élément retiré d'un layout.

    Un widget est détaché de son parent. Un sous-layout est vidé, puis détaché.
    Un espacement ne demande rien de plus.

    Args:
        item (QLayoutItem | None): L'élément retiré, ou None pour une case vide.
    """
    if item is None:
        return
    widget = item.widget()
    subLayout = item.layout()
    if widget is not None:
        widget.setParent(None)
    elif subLayout is not None:
        clearLayout(subLayout)
        subLayout.setParent(None)
```

Un widget retiré est détruit, sauf si vous en gardez une référence. Dans ce cas, il reste intact et vous pouvez l'ajouter de nouveau à un layout.

#### 2. Ajouter et retirer des polygones dans un graphique `PyQtGraph`

Un graphique `PyQtGraph` est une scène Qt. On peut donc y ajouter tout élément graphique Qt, par exemple un `QGraphicsPolygonItem`. Ses sommets s'expriment dans les coordonnées des données : le polygone suit le zoom et le déplacement. `pg.mkPen` crée un crayon cosmétique, dont l'épaisseur reste la même quel que soit le zoom.

Pour modifier ou retirer un polygone, il faut en garder la référence. On conserve donc les polygones affichés dans une liste, par exemple un attribut du widget du graphique. Trois fonctions suffisent : ajouter des polygones, déplacer un sommet d'un polygone, et tout retirer.

```python
import pyqtgraph as pg
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPolygonF
from PySide6.QtWidgets import QGraphicsPolygonItem

def addPolygons(plotWidget: pg.PlotWidget, items: list[QGraphicsPolygonItem],
                polygons: list[QPolygonF]) -> None:
    for polygon in polygons:
        item = QGraphicsPolygonItem(polygon)
        item.setPen(pg.mkPen("#1e88e5"))
        item.setBrush(pg.mkBrush("#1e88e550"))  # couleur et transparence
        plotWidget.addItem(item)
        items.append(item)                      # référence gardée pour le retrait

def moveVertex(items: list[QGraphicsPolygonItem], polygonIndex: int,
               vertexIndex: int, point: QPointF) -> None:
    polygon = items[polygonIndex].polygon()     # copie des sommets
    polygon[vertexIndex] = point
    items[polygonIndex].setPolygon(polygon)     # le graphique se redessine

def clearPolygons(plotWidget: pg.PlotWidget, items: list[QGraphicsPolygonItem]) -> None:
    for item in items:
        plotWidget.removeItem(item)
    items.clear()                               # plus aucune référence à garder

polygonItems: list[QGraphicsPolygonItem] = []
rectangle = QPolygonF([QPointF(0.0, 0.0), QPointF(1.0, 0.0), QPointF(1.0, 2.0), QPointF(0.0, 2.0)])
addPolygons(plotWidget, polygonItems, [rectangle, rectangle.translated(1.0, 0.0)])
moveVertex(polygonItems, 0, 2, QPointF(1.0, 3.0))   # 3e sommet du 1er polygone
clearPolygons(plotWidget, polygonItems)
```

`polygon()` rend une copie des sommets : la modifier ne change rien à l'affichage tant qu'on ne la redonne pas par `setPolygon()`.

[↩️](#home)
