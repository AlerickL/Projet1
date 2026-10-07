<small>**C**égep du **V**ieux **M**ontréal&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;**S**ciences, **I**nformatique et **M**athématique</small><br><br>

# Représentations d'une courbe plane

## I. Rappel des fondamentaux

Une courbe plane est un ensemble de points $(x, y)$ du plan. Le problème de sa représentation est de décrire cet ensemble par une ou plusieurs équations.

Une courbe peut s'écrire sous trois formes, dites **explicite**, **implicite** et **paramétrique** :

$$
y = f(x)
\qquad\qquad
F(x, y) = 0
\qquad\qquad
\begin{cases} x = x(t) \\ y = y(t) \end{cases}
$$

Le principe repose sur la façon dont les coordonnées $x$ et $y$ sont liées : l'une est calculée à partir de l'autre, les deux sont liées par une condition, ou les deux sont calculées à partir d'une troisième variable.

Chaque forme a ses caractéristiques propres et se prête plus ou moins bien à certains calculs. Certaines courbes ne s'expriment que sous une ou deux de ces formes. Les termes et les notations communs aux rappels sont définis dans le [lexique](math_lexique.md).

---

## II. Les trois formes

### 1. Forme explicite

La coordonnée $y$ est isolée et s'exprime directement en fonction de $x$.

$$y = f(x), \qquad x \in \mathcal{D}$$

| Caractéristique | Description |
|:----|:----|
| Rôle | C'est la forme d'une fonction réelle. La courbe est le graphe de $f$ sur son domaine $\mathcal{D}$. |
| Domaine de définition | $\mathcal{D} \subseteq \mathbb{R}$ est l'ensemble des valeurs de $x$ pour lesquelles $f(x)$ existe. |
| Délimitation de la courbe | La courbe est produite en parcourant $\mathcal{D}$. Restreindre $x$ à un intervalle $[a, b] \subseteq \mathcal{D}$ ne garde qu'une portion de la courbe. |
| Contrainte | À chaque valeur de $x$ correspond une seule valeur de $y$. Une courbe fermée ou une tangente verticale ne peuvent pas être représentées. |
| Exemple | $y = \sqrt{1 - x^2}$, avec $\mathcal{D} = [-1, 1]$, ne décrit que la moitié supérieure du cercle unité. |

### 2. Forme implicite

Les coordonnées $x$ et $y$ sont liées par une équation, sans que l'une soit isolée.

$$F(x, y) = 0, \qquad (x, y) \in U$$

| Caractéristique | Description |
|:----|:----|
| Rôle | La courbe est l'ensemble des points qui satisfont l'équation. Il suffit d'évaluer $F$ pour savoir si un point appartient à la courbe. |
| Domaine de définition | $U \subseteq \mathbb{R}^2$ est l'ensemble des points $(x, y)$ où $F$ peut être évaluée. C'est souvent le plan entier. |
| Délimitation de la courbe | Le domaine ne produit pas la courbe : c'est l'équation qui sélectionne les points. Pour ne garder qu'une portion de la courbe, on ajoute une inégalité, par exemple $y \geq 0$. |
| Convention | Le zéro du membre de droite est une convention d'écriture. Toute équation $G(x, y) = H(x, y)$ s'y ramène en posant $F = G - H$. |
| Contrainte | L'équation ne fournit pas directement les points de la courbe. Il faut la résoudre pour les obtenir. |
| Exemple | $x^2 + y^2 - 1 = 0$, avec $U = \mathbb{R}^2$, décrit le cercle unité en entier. |

### 3. Forme paramétrique

Les coordonnées $x$ et $y$ s'expriment chacune en fonction d'une troisième variable $t$, appelée le paramètre.

$$x = x(t), \quad y = y(t), \qquad t \in \mathcal{T}$$

| Caractéristique | Description |
|:----|:----|
| Rôle | La courbe est l'ensemble des points obtenus en faisant varier le paramètre $t$ sur l'intervalle $\mathcal{T}$. Elle est parcourue dans un sens, celui des valeurs croissantes de $t$. |
| Domaine de définition | $\mathcal{T} \subseteq \mathbb{R}$ est l'intervalle du paramètre, sur lequel $x(t)$ et $y(t)$ existent. |
| Délimitation de la courbe | La courbe est produite en parcourant $\mathcal{T}$. Restreindre $t$ à un intervalle $[t_a, t_b] \subseteq \mathcal{T}$ ne garde qu'une portion de la courbe. |
| Contrainte | La représentation n'est pas unique. Plusieurs paramétrisations différentes décrivent la même courbe. |
| Exemple | $x = \cos t$, $y = \sin t$, avec $\mathcal{T} = [0, 2\pi]$, décrit le cercle unité en entier, parcouru dans le sens antihoraire. |

### Passage d'une forme à l'autre

La grille se lit de la ligne vers la colonne : la **ligne** est la forme de départ, la **colonne** est la forme d'arrivée.

| De &nbsp; $\downarrow$ &nbsp; Vers &nbsp; $\to$ | Explicite | Implicite | Paramétrique |
| :--- | :---: | :---: | :---: |
| **Explicite** | - | Toujours | Toujours |
| **Implicite** | Pas toujours | - | Pas toujours |
| **Paramétrique** | Pas toujours | Pas toujours | - |

*Toujours* signifie que le passage existe pour toute courbe écrite sous la forme de départ. *Pas toujours* signifie qu'il dépend de la courbe : il peut être impossible, ou exiger de découper la courbe en plusieurs morceaux.

La forme explicite est donc un cas particulier des deux autres : toute courbe explicite s'écrit aussi sous forme implicite et sous forme paramétrique, alors que l'inverse est faux. C'est la forme la plus restrictive. Le cercle unité l'illustre : il possède une forme implicite et une forme paramétrique, mais aucune forme explicite unique. Il en faut deux, une pour chaque moitié.

## III. Dérivée et intégrale

La forme d'une courbe détermine la façon de calculer deux grandeurs usuelles :

* **La pente** $m = \dfrac{dy}{dx}$ : la dérivée, soit l'inclinaison de la tangente en un point de la courbe.
* **L'aire sous la courbe** : la surface comprise entre la courbe et l'axe des $x$, entre deux points.

Les bornes sont $a$ et $b$ sur l'axe des $x$ pour la forme explicite, et $t_a$ et $t_b$ sur l'intervalle $\mathcal{T}$ pour la forme paramétrique.

| Forme | Pente $m$ | Aire sous la courbe |
| :--- | :---: | :---: |
| **Explicite** <br> $y = f(x)$ | $f'(x)$ | $\displaystyle\int_a^b f(x)\,dx$ |
| **Implicite** <br> $F(x, y) = 0$ | $-\dfrac{\partial F / \partial x}{\partial F / \partial y}$ | Pas de formule directe |
| **Paramétrique** <br> $x(t),\ y(t)$ | $\dfrac{y'(t)}{x'(t)}$ | $\displaystyle\int_{t_a}^{t_b} y(t) \cdot x'(t)\,dt$ |

Notes :
- la pente n'est définie que si le dénominateur est non nul;
- pour la forme implicite, l'aire exige d'abord de passer à une autre forme;
- pour la forme paramétrique, le signe de l'aire dépend du sens de parcours.

La forme explicite donne les formules les plus simples. La forme paramétrique les généralise : en posant $x = t$ et $y = f(t)$, on retrouve exactement les formules de la forme explicite.

## IV. Conclusion

Les trois formes décrivent le même objet, une courbe du plan, mais n'offrent pas les mêmes facilités. La forme **explicite** est la plus simple et la plus limitée, la forme **implicite** teste l'appartenance d'un point, et la forme **paramétrique** est la plus générale pour tracer et pour calculer.
