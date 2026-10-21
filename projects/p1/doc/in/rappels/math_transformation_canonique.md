<small>**C**égep du **V**ieux **M**ontréal&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;**S**ciences, **I**nformatique et **M**athématique</small><br><br>

# Transformation canonique d'une fonction

Dans un projet d'exploration de méthodes numériques, la transformation canonique sert à faire varier la fonction étudiée : une même fonction de référence, déplacée et redimensionnée, montre comment une méthode réagit à des situations différentes. 

Les paramètres présentés ici sont ce qui peut varier dans le problème, et c'est en les faisant varier qu'une analyse devient intéressante, sur papier comme dans un outil logiciel. Leur présentation sert donc de guide à chaque étape d'un tel travail, de la compréhension mathématique jusqu'à la conception et au code.

## I. Rappel des fondamentaux

Le problème de la transformation canonique est d'obtenir, à partir d'une fonction de référence $v = f(u)$, une nouvelle fonction de même forme, dont la courbe est déplacée et redimensionnée dans le plan. Les notations communes aux rappels sont définies dans le [lexique](math_lexique.md).

Le principe repose sur deux transformations affines indépendantes, une par axe. Chacune combine une **translation** $\delta$ et une **échelle** $s$. Un point $(u, v)$ de la courbe de référence devient le point $(x, y)$ de la courbe transformée :

$$
x = s_x u + \delta_x
\qquad\qquad
y = s_y v + \delta_y
$$

Pour exprimer $y$ en fonction de $x$, il faut inverser la première relation. On obtient deux transformations :
- la première, $\Phi_{\text{in}}$, conditionne l'**intrant** $x$ avant qu'il n'entre dans $f$
- la seconde, $\Phi_{\text{out}}$, conditionne l'**extrant** $v$ à la sortie de $f$

$$
x \;\xrightarrow{\quad \Phi_{\text{in}} \quad}\; u \;\xrightarrow{\quad f \quad}\; v \;\xrightarrow{\quad \Phi_{\text{out}} \quad}\; y
$$

$$
u = \Phi_{\text{in}}(x) = \frac{x - \delta_x}{s_x}
\qquad\qquad
y = \Phi_{\text{out}}(v) = s_y v + \delta_y
$$

On remarque que les deux calculs sont l'inverse l'un de l'autre : $\Phi_{\text{in}}$ soustrait puis divise, tandis que $\Phi_{\text{out}}$ multiplie puis additionne. La fonction transformée $f_c(x)$ s'obtient par la composition :

$$
f_c(x) = (\Phi_{\text{out}} \circ f \circ \Phi_{\text{in}})(x) = s_y f\left(\frac{x - \delta_x}{s_x}\right) + \delta_y
$$

Où l'opérateur $\circ$ désigne la composition de fonctions : $(p \circ q)(x) = p(q(x))$.

Avec $\delta_x = 0$, $\delta_y = 0$, $s_x = 1$ et $s_y = 1$, la fonction reste inchangée : $f_c(x) = f(x)$. On dira que la transformation est neutre ou identité.

---

## II. Paramètres de configuration

Une transformation canonique est entièrement définie par les paramètres suivants :

### 1. $f$ : la fonction de référence

C'est la fonction dont on déplace et redimensionne la courbe. Elle détermine la forme de la fonction transformée.

| Élément | Description |
| :--- | :---: |
| Variable indépendante | $u \in \mathcal{D}$ |
| Point de la courbe de référence | $(u, f(u))$ |
| Fonction transformée | $y = f_c(x)$ |
| Domaine d'application de $\delta_x$ et $s_x$ | La variable indépendante $u$, par $\Phi_{\text{in}}$ |
| Domaine d'application de $\delta_y$ et $s_y$ | La valeur $v = f(u)$, par $\Phi_{\text{out}}$ |
| Effet sur le domaine | $\mathcal{D}$ devient $\delta_x + s_x \mathcal{D}$ |

### 2. $\delta_x$ : la translation horizontale

Déplace la courbe le long de l'axe des $x$. Le point de la courbe de référence situé en $u = 0$ se retrouve en $x = \delta_x$. La valeur neutre est $\delta_x = 0$.

| Valeur de $\delta_x$ | Nom de l'effet | Description |
| :---: | :---: | :--- |
| $\mathbf{\delta_x = 0}$ | Neutre | Aucun déplacement horizontal. |
| $\mathbf{\delta_x > 0}$ | Translation à droite | La courbe se déplace de $\delta_x$ vers la **droite**. |
| $\mathbf{\delta_x < 0}$ | Translation à gauche | La courbe se déplace de $\lvert \delta_x \rvert$ vers la **gauche**. |

### 3. $s_x$ : l'échelle horizontale

Étire ou resserre la courbe le long de l'axe des $x$, autour de la droite verticale $x = \delta_x$. La valeur neutre est $s_x = 1$.

Une largeur $\ell$ sur la courbe de référence devient une largeur $\lvert s_x \rvert \ell$ sur la courbe transformée.

| Valeur de $s_x$ | Nom de l'effet | Description |
| :---: | :---: | :--- |
| $\mathbf{s_x = 1}$ | Neutre | Aucune déformation horizontale. |
| $\mathbf{\lvert s_x \rvert > 1}$ | Dilatation | La courbe s'étire horizontalement. |
| $\mathbf{0 < \lvert s_x \rvert < 1}$ | Contraction | La courbe se resserre horizontalement. |
| $\mathbf{s_x < 0}$ | Réflexion | Miroir par rapport à la droite verticale $x = \delta_x$. S'ajoute à la dilatation ou à la contraction. |
| $\mathbf{s_x = 0}$ | Interdit | La courbe s'effondre sur la droite verticale $x = \delta_x$, et $\Phi_{\text{in}}$ divise par zéro. |

### 4. $\delta_y$ : la translation verticale

Déplace la courbe le long de l'axe des $y$. Le niveau $v = 0$ de la courbe de référence se retrouve au niveau $y = \delta_y$. La valeur neutre est $\delta_y = 0$.

| Valeur de $\delta_y$ | Nom de l'effet | Description |
| :---: | :---: | :--- |
| $\mathbf{\delta_y = 0}$ | Neutre | Aucun déplacement vertical. |
| $\mathbf{\delta_y > 0}$ | Translation vers le haut | La courbe se déplace de $\delta_y$ vers le **haut**. |
| $\mathbf{\delta_y < 0}$ | Translation vers le bas | La courbe se déplace de $\lvert \delta_y \rvert$ vers le **bas**. |

### 5. $s_y$ : l'échelle verticale

Amplifie ou atténue la courbe le long de l'axe des $y$, autour de la droite horizontale $y = \delta_y$. La valeur neutre est $s_y = 1$.

Une hauteur $\ell$ sur la courbe de référence devient une hauteur $\lvert s_y \rvert \ell$ sur la courbe transformée.

| Valeur de $s_y$ | Nom de l'effet | Description |
| :---: | :---: | :--- |
| $\mathbf{s_y = 1}$ | Neutre | Aucune déformation verticale. |
| $\mathbf{\lvert s_y \rvert > 1}$ | Amplification | La courbe s'étire verticalement. |
| $\mathbf{0 < \lvert s_y \rvert < 1}$ | Atténuation | La courbe s'écrase verticalement. |
| $\mathbf{s_y < 0}$ | Inversion | Miroir par rapport à la droite horizontale $y = \delta_y$. S'ajoute à l'amplification ou à l'atténuation. |
| $\mathbf{s_y = 0}$ | Interdit | La courbe s'effondre sur la droite horizontale $y = \delta_y$ et perd sa forme. |

## III. Conclusion

La transformation canonique sépare la **forme** d'une fonction, portée par la fonction de référence, de la **position** et de la **dimension** de sa courbe dans le plan, entièrement contrôlées par les **translations** $\delta_x$ et $\delta_y$ et par les **échelles** $s_x$ et $s_y$.

Les translations s'expriment dans l'unité de leur axe et ne sont pas affectées par les échelles.

L'effet de la transformation sur la dérivée et sur l'intégrale d'une fonction est présenté dans [Résultats d'une analyse après transformation canonique](math_transformation_canonique_resultats.md).

### Synthèse des paramètres

| Paramètre | Description |
| :--- | :--- |
| La fonction | La fonction de référence $v = f(u)$, qui détermine la forme. |
| $\delta_x$ | La translation horizontale, vers la droite si positive (neutre : $0$). |
| $s_x$ | L'échelle horizontale, non nulle, avec réflexion si négative (neutre : $1$). |
| $\delta_y$ | La translation verticale, vers le haut si positive (neutre : $0$). |
| $s_y$ | L'échelle verticale, non nulle, avec inversion si négative (neutre : $1$). |
