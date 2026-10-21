<small>**C**égep du **V**ieux **M**ontréal&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;**S**ciences, **I**nformatique et **M**athématique</small><br><br>

# Lexique des rappels mathématiques

Ce lexique réunit les notations communes à plusieurs rappels. Les notations propres à un seul document sont présentées sur place.

## I. Valeur exacte et valeur approchée

Une méthode numérique donne une valeur approchée de la valeur recherchée. L'accent circonflexe, lu *chapeau*, les distingue : $\widehat{v}$ se lit $v$ chapeau. Selon le contexte, on parle aussi de résultat *analytique* pour la valeur exacte, et de résultat *numérique* pour la valeur approchée.

| Notation | Terme | Précision |
| :---: | :--- | :--- |
| $v$ | valeur exacte | Issue du calcul analytique. |
| $\widehat{v}$ | valeur approchée | Issue du calcul numérique. |
| $E_a$ | erreur absolue | $E_a = \widehat{v} - v$, dans l'unité de $v$. |
| $E_r$ | erreur relative | $E_r = \dfrac{E_a}{v}$, sans unité, si $v \neq 0$. |

## II. Notations communes

### Fonction et méthodes numériques

| Notation | Terme | Précision |
| :---: | :--- | :--- |
| $f(x)$ | **fonction** | Objet étudié. Sa courbe est l'ensemble des points $(x, f(x))$ du plan. |
| $x$ | **variable indépendante** | |
| $\mathcal{D}$ | **domaine de définition** | Valeurs de $x$ où $f(x)$ existe. |
| $f'(x)$ | **dérivée** | |
| $m$ | **pente** de la courbe en un point | $m = f'(x)$ |
| $[a, b]$ | **bornes** | Intervalle sur l'axe des $x$. |
| $I$ | **intégrale** définie | Aire algébrique sous la courbe, entre $a$ et $b$. |
| $h$ | **pas** | Écart entre deux valeurs voisines de $x$. |
| $\alpha$ | **facteur de positionnement** | Nombre de l'intervalle $[0, 1]$. |
| $N$ | **nombre de sous-intervalles** | |

### Transformation canonique

| Notation | Terme | Précision |
| :---: | :--- | :--- |
| $f$ | **fonction de référence** | Fonction avant sa transformation, $v = f(u)$. |
| $f_c$ | **fonction transformée** | L'indice $c$ rappelle la transformation canonique. |
| $(u, v)$, $(x, y)$ | **coordonnées** de référence et transformées | Point de la courbe avant et après la transformation. |
| $\delta_x$, $\delta_y$ | **translations** | L'indice indique l'axe concerné. |
| $s_x$, $s_y$ | **échelles** | L'indice indique l'axe concerné. |

## III. Conventions d'écriture

| Notation | Lecture | Précision |
| :---: | :--- | :--- |
| $]a, b[$ | intervalle ouvert | Les bornes sont exclues. Elles sont incluses dans $[a, b]$. |
| $s_x s_y$ | multiplication | Le produit s'écrit par juxtaposition. Le point, comme $2 \cdot 3$, ne sert qu'entre deux nombres ou pour lever une ambiguïté. |
| $\mathbf{x}$ | caractère gras | Met en évidence le point d'intérêt, ou l'entrée d'un tableau. |
