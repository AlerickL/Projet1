<small>**C**égep du **V**ieux **M**ontréal&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;**S**ciences, **I**nformatique et **M**athématique</small><br><br>

# Transformation canonique d'une courbe

Dans un projet d'exploration de méthodes numériques, la transformation canonique sert à faire varier la courbe étudiée : une même courbe de référence, déplacée et redimensionnée, montre comment une méthode réagit à des situations différentes. 

Les paramètres présentés ici sont ce qui peut varier dans le problème, et c'est en les faisant varier qu'une analyse devient intéressante, sur papier comme dans un outil logiciel. Leur présentation sert donc de guide à chaque étape d'un tel travail, de la compréhension mathématique jusqu'à la conception et au code.

## I. Rappel des fondamentaux

Le problème de la transformation canonique est d'obtenir, à partir d'une courbe de référence, une nouvelle courbe de même forme, mais déplacée et redimensionnée dans le plan.

Le principe repose sur deux transformations affines indépendantes, une par axe. Chacune combine une **translation** $\delta$ et une **échelle** $s$. Un point $(u, v)$ de la courbe de référence devient le point $(x, y)$ de la courbe transformée :

$$
x = s_x \cdot u + \delta_x
\qquad\qquad
y = s_y \cdot v + \delta_y
$$

Ces relations s'appliquent aux formes explicite et paramétrique d'une courbe, présentées dans [Représentations d'une courbe plane](math_representations_courbe_plane.md). La forme implicite n'est pas abordée ici. Les termes et les notations communs aux rappels sont définis dans le [lexique](math_lexique.md).

**En forme paramétrique**, la courbe de référence est $(u(t), v(t))$ et les deux relations s'appliquent directement :

$$
x(t) = s_x \cdot u(t) + \delta_x
\qquad\qquad
y(t) = s_y \cdot v(t) + \delta_y
$$

**En forme explicite**, la courbe de référence est $v = f(u)$. Pour exprimer $y$ en fonction de $x$, il faut inverser la première relation. On obtient deux transformations :
- la première, $\Phi_{\text{in}}$, conditionne l'**intrant** $x$ avant qu'il n'entre dans $f$
- la seconde, $\Phi_{\text{out}}$, conditionne l'**extrant** $v$ à la sortie de $f$

$$
x \;\xrightarrow{\quad \Phi_{\text{in}} \quad}\; u \;\xrightarrow{\quad f \quad}\; v \;\xrightarrow{\quad \Phi_{\text{out}} \quad}\; y
$$

$$
u = \Phi_{\text{in}}(x) = \frac{x - \delta_x}{s_x}
\qquad\qquad
y = \Phi_{\text{out}}(v) = s_y \cdot v + \delta_y
$$

On remarque que les deux calculs sont l'inverse l'un de l'autre : $\Phi_{\text{in}}$ soustrait puis divise, tandis que $\Phi_{\text{out}}$ multiplie puis additionne. La fonction transformée $f_c(x)$ s'obtient par la composition :

$$
f_c(x) = (\Phi_{\text{out}} \circ f \circ \Phi_{\text{in}})(x) = s_y \cdot f\left(\frac{x - \delta_x}{s_x}\right) + \delta_y
$$

Où l'opérateur $\circ$ désigne la composition de fonctions : $(p \circ q)(x) = p(q(x))$.

Avec $\delta_x = 0$, $\delta_y = 0$, $s_x = 1$ et $s_y = 1$, la courbe reste inchangée $f_c(x) = f(x)$. On dira que la transformation est neutre ou identité.

---

## II. Paramètres de configuration

Une transformation canonique est entièrement définie par les paramètres suivants :

### 1. La courbe de référence

C'est la courbe que l'on déplace et redimensionne. Elle détermine la forme de la courbe transformée. Sa forme fixe ce sur quoi agissent les quatre paramètres suivants.

| | Forme explicite | Forme paramétrique |
| :--- | :---: | :---: |
| Variable indépendante | $u \in \mathcal{D}$ | $t \in \mathcal{T}$ |
| Point de la courbe de référence | $(u, f(u))$ | $(u(t), v(t))$ |
| Courbe transformée | $y = f_c(x)$ | $(x(t), y(t))$ |
| Domaine d'application de $\delta_x$ et $s_x$ | La variable indépendante $u$ | La coordonnée $u(t)$, et non le paramètre $t$ |
| Domaine d'application de $\delta_y$ et $s_y$ | La valeur $v = f(u)$ | La coordonnée $v(t)$ |
| Effet sur le domaine | $\mathcal{D}$ devient $\delta_x + s_x \cdot \mathcal{D}$ | $\mathcal{T}$ reste inchangé |

### 2. $\delta_x$ : la translation horizontale

Déplace la courbe le long de l'axe des $x$. Le point de la courbe de référence situé en $u = 0$ se retrouve en $x = \delta_x$. La valeur neutre est $\delta_x = 0$.

$\delta_x > 0$ $\implies$ déplacement vers la **droite**, et $\delta_x < 0$ $\implies$ déplacement vers la **gauche**.

### 3. $s_x$ : l'échelle horizontale

Étire ou resserre la courbe le long de l'axe des $x$, autour de la droite verticale $x = \delta_x$. La valeur neutre est $s_x = 1$.

Une largeur $\ell$ sur la courbe de référence devient une largeur $\lvert s_x \rvert \cdot \ell$ sur la courbe transformée.

| Valeur de $s_x$ | Nom de l'effet | Description |
| :---: | :---: | :--- |
| $\mathbf{s_x = 1}$ | Neutre | Aucune déformation horizontale. |
| $\mathbf{\lvert s_x \rvert > 1}$ | Dilatation | La courbe s'étire horizontalement. |
| $\mathbf{0 < \lvert s_x \rvert < 1}$ | Contraction | La courbe se resserre horizontalement. |
| $\mathbf{s_x < 0}$ | Réflexion | Miroir par rapport à la droite verticale $x = \delta_x$. S'ajoute à la dilatation ou à la contraction. |
| $\mathbf{s_x = 0}$ | Interdit | La courbe s'effondre sur la droite verticale $x = \delta_x$. En forme explicite, la formule divise par zéro. |

### 4. $\delta_y$ : la translation verticale

Déplace la courbe le long de l'axe des $y$. Le niveau $v = 0$ de la courbe de référence se retrouve au niveau $y = \delta_y$. La valeur neutre est $\delta_y = 0$.

$\delta_y > 0$ $\implies$ déplacement vers le **haut**, et $\delta_y < 0$ $\implies$ déplacement vers le **bas**.

### 5. $s_y$ : l'échelle verticale

Amplifie ou atténue la courbe le long de l'axe des $y$, autour de la droite horizontale $y = \delta_y$. La valeur neutre est $s_y = 1$.

Une hauteur $\ell$ sur la courbe de référence devient une hauteur $\lvert s_y \rvert \cdot \ell$ sur la courbe transformée.

| Valeur de $s_y$ | Nom de l'effet | Description |
| :---: | :---: | :--- |
| $\mathbf{s_y = 1}$ | Neutre | Aucune déformation verticale. |
| $\mathbf{\lvert s_y \rvert > 1}$ | Amplification | La courbe s'étire verticalement. |
| $\mathbf{0 < \lvert s_y \rvert < 1}$ | Atténuation | La courbe s'écrase verticalement. |
| $\mathbf{s_y < 0}$ | Inversion | Miroir par rapport à la droite horizontale $y = \delta_y$. S'ajoute à l'amplification ou à l'atténuation. |
| $\mathbf{s_y = 0}$ | Interdit | La courbe s'effondre sur la droite horizontale $y = \delta_y$ et perd sa forme. |

## III. Conclusion

La transformation canonique sépare la **forme** d'une courbe, portée par la courbe de référence, de sa **position** et de sa **dimension** dans le plan, entièrement contrôlées par les **translations** $\delta_x$ et $\delta_y$ et par les **échelles** $s_x$ et $s_y$.

Les translations s'expriment dans l'unité de leur axe et ne sont pas affectées par les échelles. En forme paramétrique, une seule échelle négative inverse le sens de rotation du parcours (horaire ou antihoraire), alors que deux échelles négatives le conservent.

### Synthèse des paramètres

| Paramètre | Description |
| :--- | :--- |
| La courbe | La courbe de référence, sous forme explicite ou paramétrique, qui détermine la forme. |
| $\delta_x$ | La translation horizontale, vers la droite si positive (neutre : $0$). |
| $s_x$ | L'échelle horizontale, non nulle, avec réflexion si négative (neutre : $1$). |
| $\delta_y$ | La translation verticale, vers le haut si positive (neutre : $0$). |
| $s_y$ | L'échelle verticale, non nulle, avec inversion si négative (neutre : $1$). |
