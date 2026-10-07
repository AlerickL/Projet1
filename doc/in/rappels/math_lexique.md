<small>**C**égep du **V**ieux **M**ontréal&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;**S**ciences, **I**nformatique et **M**athématique</small><br><br>

# Lexique des rappels mathématiques

Ce lexique réunit les termes et les notations partagés par les documents de rappel. Chaque document y renvoie plutôt que de les redéfinir.

## I. Valeur exacte et valeur approchée

Une méthode numérique ne donne pas la valeur recherchée, mais une valeur qui s'en approche. Les deux se distinguent par un seul signe : sans accent, la valeur est exacte, et avec l'accent circonflexe, elle est approchée.

Les lettres $f$ et $\widehat{f}$ désignent les deux façons de calculer. Les lettres $v$ et $\widehat{v}$ désignent les valeurs qui en résultent.

| Notion | Terme | Notation | Précision |
| :--- | :--- | :---: | :--- |
| Façon d'obtenir la valeur exacte | calcul analytique | $f$ | |
| Façon d'obtenir la valeur approchée | calcul numérique | $\widehat{f}$ | $f \approx \widehat{f}$ |
| Valeur issue du calcul analytique | valeur exacte | $v$ | $v = f(x)$ |
| Valeur issue du calcul numérique | valeur approchée | $\widehat{v}$ | $v \approx \widehat{v} = \widehat{f}(x)$ |
| Écart entre les deux valeurs | erreur absolue | $E_a$ | $E_a = \widehat{v} - v$, dans l'unité de $v$ |
| Écart rapporté à la valeur exacte | erreur relative | $E_r$ | $E_r = \dfrac{E_a}{v}$, sans unité, si $v \neq 0$ |

L'accent circonflexe se lit *chapeau*, ainsi $\widehat{f}$ se lit $f$ chapeau.

## II. Notations communes

Les mêmes symboles gardent le même sens dans tous les documents de rappel.

### Courbe et variables

| Notation | Terme | Précision |
| :---: | :--- | :--- |
| $f(x)$ | **fonction** | Courbe sous forme explicite. |
| $x(t)$, $y(t)$ | **fonctions coordonnées** | Courbe sous forme paramétrique. |
| $P = (x, y)$ | **point** de la courbe | Une majuscule désigne un point, une minuscule désigne un nombre. |
| $x$ | **abscisse** | Variable indépendante de la forme explicite. |
| $t$ | **paramètre** | Variable indépendante de la forme paramétrique. |
| $\mathcal{D}$ | **domaine de définition** | Ensemble des valeurs de $x$ où $f(x)$ existe. |
| $\mathcal{T}$ | **intervalle du paramètre** | Ensemble des valeurs que parcourt $t$. |
| $[a, b]$, $[t_a, t_b]$ | **bornes** d'un intervalle | Sur $x$ en forme explicite, sur $t$ en forme paramétrique. |
| $f'(x)$, $x'(t)$, $y'(t)$ | **dérivée première** | L'apostrophe indique la dérivée par rapport à la variable indépendante. |
| $m$ | **pente** de la courbe en un point | $m = \dfrac{dy}{dx}$ |
| $F(x, y)$ | **fonction de deux variables** | Courbe sous forme implicite, $F(x, y) = 0$. |
| $U$ | **domaine de définition** de $F$ | Ensemble des points $(x, y)$ où $F$ peut être évaluée. |
| $\dfrac{\partial F}{\partial x}$ | **dérivée partielle** | Dérivée de $F$ par rapport à $x$, en tenant $y$ constant. |

### Réglages des méthodes numériques

| Notation | Terme | Précision |
| :---: | :--- | :--- |
| $h$ | **pas** | Écart entre deux valeurs voisines de la variable indépendante. |
| $\alpha$ | **facteur de positionnement** | Nombre de l'intervalle $[0, 1]$. |
| $N$ | **nombre de sous-intervalles** | Entier positif. |
| $x_i$, $t_i$ | **noeud** d'indice $i$ | L'indice $i$ numérote les noeuds, de $0$ à $N$. |
| $x_i^*$, $t_i^*$ | **point d'évaluation** | L'astérisque indique un point choisi à l'intérieur du sous-intervalle $i$. |
| $g$, $g_i$ | **intégrande** et sa valeur au noeud $i$ | |
| $g_i^*$ | valeur de l'intégrande au **point d'évaluation** | |
| $I$ | **intégrale** définie | |
| $P_i$ | **point** de la courbe au noeud $i$ | $P_i = (x_i, y_i)$ |
| $P_-$, $P_+$ | **points voisins** de la sécante | L'indice $-$ désigne le point situé avant le point d'intérêt, l'indice $+$ celui situé après. De même pour $x_-$, $x_+$, $t_-$ et $t_+$. |
| $\mathcal{M}$ | **méthode** numérique retenue | |

### Transformation canonique

| Notation | Terme | Précision |
| :---: | :--- | :--- |
| $(u, v)$ | **coordonnées de référence** | Point de la courbe avant sa transformation. |
| $(x, y)$ | **coordonnées transformées** | Point de la courbe après sa transformation. |
| $\delta_x$, $\delta_y$ | **translations** | L'indice indique l'axe concerné. |
| $s_x$, $s_y$ | **échelles** | L'indice indique l'axe concerné. |
| $f_c$ | **fonction transformée** | L'indice $c$ rappelle la transformation canonique. |
| $\Phi_{\text{in}}$, $\Phi_{\text{out}}$ | **transformations** de l'intrant et de l'extrant | Propres à la forme explicite. |
| $\ell$ | **largeur** ou **hauteur** d'un motif de la courbe | |

### Signes

| Notation | Lecture | Précision |
| :---: | :--- | :--- |
| $=$ | est égal à | Égalité exacte. |
| $\approx$ | est approximativement égal à | Relie une valeur exacte à sa valeur approchée. |
| $\implies$ | implique | |
| $\uparrow$, $\downarrow$ | augmente, diminue | |
| $\to$ | tend vers | Par exemple $h \to 0$. |
| $\in$ | appartient à | |
| $\subseteq$ | est inclus dans | |
| $[a, b]$, $]a, b[$ | intervalle fermé, intervalle ouvert | Les bornes sont incluses dans le premier, exclues du second. |
| $\lvert s \rvert$ | valeur absolue de $s$ | |
| $\circ$ | composition de fonctions | $(p \circ q)(x) = p(q(x))$ |
| $\cdot$ | multiplication | |
| $\mathbf{x}$ | caractère gras | Met en évidence la valeur ou le point d'intérêt, ou l'entrée d'un tableau. |

## III. Termes communs

| Terme | Définition | Document |
| :--- | :--- | :--- |
| Forme explicite | Courbe décrite par $y = f(x)$. | [Représentations d'une courbe plane](math_representations_courbe_plane.md) |
| Forme paramétrique | Courbe décrite par $x(t)$ et $y(t)$. | [Représentations d'une courbe plane](math_representations_courbe_plane.md) |
| Variable indépendante | Variable que l'on fait varier pour parcourir la courbe : $x$ en forme explicite, $t$ en forme paramétrique. | [Représentations d'une courbe plane](math_representations_courbe_plane.md) |
| Sécante | Droite passant par deux points d'une courbe. | [Dérivée numérique](math_derivation_numerique.md) |
| Courbe de référence | Courbe d'origine, avant sa transformation. | [Transformation canonique](math_transformation_canonique_courbe.md) |

---
