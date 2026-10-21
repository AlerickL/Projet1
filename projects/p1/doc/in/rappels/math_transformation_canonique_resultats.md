<small>**C**égep du **V**ieux **M**ontréal&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;**S**ciences, **I**nformatique et **M**athématique</small><br><br>

# Résultats d'une analyse après transformation canonique

## I. Le problème

La [transformation canonique](math_transformation_canonique.md) déplace et redimensionne une fonction de référence $f$ pour produire la fonction transformée :

$$
f_c(x) = s_y f\left(\frac{x - \delta_x}{s_x}\right) + \delta_y
$$

Analyser $f_c$, c'est par exemple calculer sa dérivée en un point ou son aire entre deux bornes. Une fois $f$ analysée, faut-il tout recommencer à chaque nouvelle transformation ? Non : le résultat pour $f_c$ se déduit de celui pour $f$.

### 1. Deux chemins vers le même résultat

$$
\begin{array}{ccc}
f & \xrightarrow{\quad \text{transformation canonique} \quad} & f_c \\[4pt]
\Big\downarrow \text{analyse en } u & & \Big\downarrow \text{analyse en } x \\[4pt]
z & \xrightarrow{\qquad\qquad T \qquad\qquad} & z_c
\end{array}
$$

Le résultat de l'analyse est noté $z$ pour $f$ et $z_c$ pour $f_c$. La transformation $T$ fait passer de l'un à l'autre.

Le chemin de droite analyse $f_c$ directement. Le chemin de gauche analyse $f$, puis transforme son résultat. C'est ce second chemin que nous privilégions : il réutilise les résultats connus de $f$, comme ceux du [catalogue](math_fonctions_suggerees.md), et il montre l'effet de chaque paramètre de la transformation. Les sections suivantes présentent $T$ pour chaque sorte d'analyse. Les démonstrations sont en annexe.

### 2. Le chemin par la fonction de référence

| Étape | Opération |
| :--- | :--- |
| 1. Passer à la référence | Chaque point $x$ devient $u = \dfrac{x - \delta_x}{s_x}$, et chaque pas $h$ devient $\dfrac{h}{s_x}$. |
| 2. Analyser $f$ | On obtient $z$. |
| 3. Transformer le résultat | $z_c = T(z)$ |

Ce chemin vaut pour toute analyse, qu'elle soit analytique ou numérique.

---

## II. La dérivée

| Élément | Description |
| :--- | :--- |
| Analyse | Dérivée en un point |
| Résultats | $z = f'(u)$, la dérivée de $f$ en $u$ <br> $z_c = f_c'(x)$, la dérivée de $f_c$ en $x$ |
| Passage à la référence | $x \to u$ et $h \to \dfrac{h}{s_x}$, avec le même $\alpha$ |
| Transformation du résultat | $T(z) = \dfrac{s_y}{s_x} z$ |

D'où :

$$
\begin{aligned}
f_c'(x) &= \frac{s_y}{s_x} f'\left(\frac{x - \delta_x}{s_x}\right) \\[6pt]
z_c &= \frac{s_y}{s_x} z
\end{aligned}
$$

Cette relation vaut pour la dérivée analytique ([démonstration](#annexe-a1)). Elle vaut aussi pour la dérivée numérique, celle de $f$ étant calculée avec le pas $\dfrac{h}{s_x}$ ([démonstration](#annexe-a2)).

### 1. L'effet de chaque paramètre

| Paramètre | Effet sur la dérivée |
| :--- | :--- |
| $\delta_x$ | Aucun sur la valeur. Il déplace seulement le point $u$ où $f'$ est évaluée. |
| $\delta_y$ | Aucun. La dérivée d'une constante est nulle. |
| $s_x$ | Divise la dérivée. Un signe négatif change son signe. |
| $s_y$ | Multiplie la dérivée. Un signe négatif change son signe. |
| $s_x = s_y$ | Dérivée inchangée : la courbe est agrandie sans être déformée. |

### 2. L'effet sur l'erreur

Le résultat analytique et le résultat numérique subissent la même transformation $T$. L'erreur absolue est donc multipliée par $\dfrac{s_y}{s_x}$, et l'erreur relative ne change pas. La précision relative de la méthode dépend seulement du pas vu par la fonction de référence, soit $\dfrac{h}{s_x}$.

---

## III. L'intégrale

| Élément | Description |
| :--- | :--- |
| Analyse | Intégrale entre deux bornes |
| Résultats | $z = \displaystyle\int_{u_a}^{u_b} f(u)\,du$, l'intégrale de $f$ entre $u_a$ et $u_b$ <br> $z_c = \displaystyle\int_a^b f_c(x)\,dx$, l'intégrale de $f_c$ entre $a$ et $b$ |
| Passage à la référence | $a \to u_a$ et $b \to u_b$, avec le même $N$ et le même $\alpha$. Le pas $h$ devient $\dfrac{h}{s_x}$ de lui-même. |
| Transformation du résultat | $T(z) = s_x s_y z + \delta_y (b - a)$ |

D'où :

$$
\begin{aligned}
\int_a^b f_c(x)\,dx &= s_x s_y \int_{\frac{a - \delta_x}{s_x}}^{\frac{b - \delta_x}{s_x}} f(u)\,du + \delta_y (b - a) \\[6pt]
z_c &= s_x s_y z + \delta_y (b - a)
\end{aligned}
$$

Cette relation vaut pour l'intégrale analytique ([démonstration](#annexe-b1)). Elle vaut aussi pour l'intégrale numérique, celle de $f$ étant calculée avec le même $N$ ([démonstration](#annexe-b2)).

Contrairement à la dérivée, $T$ dépend aussi des bornes : la translation $\delta_y$ ajoute l'aire d'un rectangle de hauteur $\delta_y$ et de largeur $b - a$.

Si $s_x < 0$, on obtient $u_a > u_b$. La relation s'applique telle quelle : il ne faut pas remettre les bornes de référence en ordre.

### 1. L'effet de chaque paramètre

| Paramètre | Effet sur l'intégrale |
| :--- | :--- |
| $\delta_x$ | Aucun sur la valeur. Il déplace seulement les bornes $u_a$ et $u_b$. |
| $\delta_y$ | Ajoute $\delta_y (b - a)$, l'aire du rectangle sous la translation. |
| $s_x$ | Multiplie l'intégrale par $\lvert s_x \rvert$. Un signe négatif inverse les bornes de référence, sans changer le signe du résultat. |
| $s_y$ | Multiplie l'intégrale. Un signe négatif change son signe. |
| $s_x s_y = 1$ | Intégrale inchangée, hors $\delta_y$ : la courbe est étirée dans un sens et écrasée dans l'autre. |

### 2. L'effet sur l'erreur

Le résultat analytique et le résultat numérique subissent la même transformation $T$. Le terme $\delta_y (b - a)$ est identique pour les deux et s'annule dans l'erreur absolue, qui est donc multipliée par $s_x s_y$. L'erreur relative ne change pas si $\delta_y = 0$. Sinon, elle change, car la valeur analytique change de taille alors que l'erreur absolue n'en dépend pas.

---

## Annexe A. Démonstration pour la dérivée

<a id="annexe-a1"></a>
### 1. La dérivée analytique

Soit l'expression :

$$
y = s_y f\left(\frac{x - \delta_x}{s_x}\right) + \delta_y
$$

En posant la variable intermédiaire :

$$
u(x) = \frac{x - \delta_x}{s_x} = \frac{1}{s_x}\,x - \frac{\delta_x}{s_x}
$$

La dérivée de $u$ par rapport à $x$ vaut :

$$
\frac{du}{dx} = \frac{1}{s_x}
$$

En appliquant la règle de dérivation en chaîne, la dérivée $\dfrac{dy}{dx}$ s'écrit :

$$
\frac{dy}{dx} = s_y f'(u) \frac{du}{dx} + 0
$$

D'où :

$$
\frac{dy}{dx} = \frac{s_y}{s_x} f'\left(\frac{x - \delta_x}{s_x}\right)
$$

<a id="annexe-a2"></a>
### 2. La dérivée numérique

Soit la dérivée numérique de $f_c$ en $x$, avec le pas $h$ :

$$
\frac{f_c(x_+) - f_c(x_-)}{h}
$$

Les points voisins $x_-$ et $x_+$ ont pour points de référence :

$$
u_- = \frac{x_- - \delta_x}{s_x}
\qquad\qquad
u_+ = \frac{x_+ - \delta_x}{s_x}
$$

Ces deux points sont séparés de :

$$
u_+ - u_- = \frac{x_+ - x_-}{s_x} = \frac{h}{s_x}
$$

Au numérateur, la translation $\delta_y$ s'annule :

$$
f_c(x_+) - f_c(x_-) = \big(s_y f(u_+) + \delta_y\big) - \big(s_y f(u_-) + \delta_y\big) = s_y \big(f(u_+) - f(u_-)\big)
$$

D'où :

$$
\frac{f_c(x_+) - f_c(x_-)}{h} = \frac{s_y}{s_x} \frac{f(u_+) - f(u_-)}{h / s_x}
$$

Le dernier quotient est la dérivée numérique de $f$ en $u$, avec le pas $\dfrac{h}{s_x}$.

---

## Annexe B. Démonstration pour l'intégrale

<a id="annexe-b1"></a>
### 1. L'intégrale analytique

Soit l'intégrale :

$$
z_c = \int_a^b \left( s_y f\left(\frac{x - \delta_x}{s_x}\right) + \delta_y \right) dx
$$

En séparant les deux termes :

$$
z_c = s_y \int_a^b f\left(\frac{x - \delta_x}{s_x}\right) dx + \int_a^b \delta_y \, dx
$$

Le second terme vaut :

$$
\int_a^b \delta_y \, dx = \delta_y (b - a)
$$

Pour le premier terme, on pose la variable intermédiaire :

$$
u(x) = \frac{x - \delta_x}{s_x}
$$

Sa dérivée donne $du = \dfrac{dx}{s_x}$, soit $dx = s_x\,du$. Les bornes $a$ et $b$ deviennent :

$$
u_a = \frac{a - \delta_x}{s_x}
\qquad\qquad
u_b = \frac{b - \delta_x}{s_x}
$$

Par changement de variable, le premier terme s'écrit :

$$
s_y \int_a^b f\left(\frac{x - \delta_x}{s_x}\right) dx = s_y \int_{u_a}^{u_b} f(u)\, s_x\, du = s_x s_y \int_{u_a}^{u_b} f(u)\,du
$$

D'où :

$$
z_c = s_x s_y \int_{u_a}^{u_b} f(u)\,du + \delta_y (b - a)
$$

<a id="annexe-b2"></a>
### 2. L'intégrale numérique

Les méthodes d'intégration numérique s'écrivent toutes comme une somme pondérée de valeurs de la fonction. Soit l'intégrale numérique de $f_c$ entre $a$ et $b$, avec $N$ sous-intervalles de pas $h = \dfrac{b - a}{N}$ :

$$
h \sum_k w_k f_c(x_k)
$$

Les points $x_k$ et les poids $w_k$ dépendent de la méthode. Par exemple, pour la méthode des rectangles, tous les poids valent $1$. Dans tous les cas, la somme des poids vaut $N$.

Les points $x_k$ ont pour points de référence :

$$
u_k = \frac{x_k - \delta_x}{s_x}
$$

Ils occupent les mêmes positions relatives dans les $N$ sous-intervalles de $[u_a, u_b]$, de pas $\dfrac{h}{s_x}$.

En remplaçant $f_c(x_k) = s_y f(u_k) + \delta_y$ :

$$
h \sum_k w_k f_c(x_k) = s_y h \sum_k w_k f(u_k) + \delta_y h \sum_k w_k
$$

Le second terme vaut $\delta_y h N = \delta_y (b - a)$. Le premier se réécrit avec le pas $\dfrac{h}{s_x}$ :

$$
s_y h \sum_k w_k f(u_k) = s_x s_y \frac{h}{s_x} \sum_k w_k f(u_k)
$$

D'où :

$$
h \sum_k w_k f_c(x_k) = s_x s_y \frac{h}{s_x} \sum_k w_k f(u_k) + \delta_y (b - a)
$$

La dernière somme est l'intégrale numérique de $f$ entre $u_a$ et $u_b$, avec la même méthode et les mêmes $N$ et $\alpha$.
