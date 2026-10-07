<small>**C**égep du **V**ieux **M**ontréal&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;**S**ciences, **I**nformatique et **M**athématique</small><br><br>

# Méthodes d'intégration numérique

Dans un projet d'exploration de méthodes numériques, l'intégration numérique est un sujet de choix : plusieurs méthodes répondent au même problème, avec une précision et un coût de calcul qui dépendent de leurs réglages.

Les paramètres présentés ici sont ce qui peut varier dans le problème, et c'est en les faisant varier qu'une analyse devient intéressante, sur papier comme dans un outil logiciel. Leur présentation sert donc de guide à chaque étape d'un tel travail, de la compréhension mathématique jusqu'à la conception et au code.

## I. Rappel des fondamentaux

Le problème de l'intégration numérique est d'approximer la valeur d'une intégrale définie de la forme :
$$I = \int_{a}^{b} g(x)\, dx$$
en utilisant une somme finie. La fonction $g$ est l'intégrande, et $I$ s'interprète comme l'aire algébrique (signée) sous une courbe.

Le principe repose sur le découpage de l'intervalle $[a, b]$ en $N$ sous-intervalles de largeur $h$, puis sur la somme des aires approchées calculées sur chacun d'eux. Cette somme est la valeur approchée $\widehat{I}$.

$$
\widehat{I} = \sum_{i=0}^{N-1} (\text{Aire approchée sur le sous-intervalle } i)
$$

Plus le nombre de sous-intervalles $N$ est grand (ou plus le pas $h$ est petit), plus l'approximation est précise. À la limite, lorsque $N \to \infty$, $h \to 0$ et la somme converge vers la valeur exacte de l'intégrale.

Cette méthode vaut pour les formes explicite et paramétrique d'une courbe, présentées dans [Représentations d'une courbe plane](math_representations_courbe_plane.md). La forme implicite n'est pas abordée ici. Les termes et les notations communs aux rappels, dont *valeur exacte* et *valeur approchée*, sont définis dans le [lexique](math_lexique.md).

## II. Paramètres de configuration

Une intégration numérique est entièrement définie par les paramètres suivants :

### 1. La courbe à intégrer

C'est la courbe dont on calcule l'aire. Sa forme fixe la variable indépendante, sur laquelle portent tous les autres paramètres, ainsi que l'intégrande $g$.

| | Forme explicite | Forme paramétrique |
| :--- | :---: | :---: |
| Variable indépendante | $x$ | $t$ |
| Intégrande $g$ | $f(x)$ | $y(t) \cdot x'(t)$ |
| Aire exacte $I$ | $\displaystyle\int_a^b f(x)\,dx$ | $\displaystyle\int_{t_a}^{t_b} y(t) \cdot x'(t)\,dt$ |
| Aire approchée $\widehat{I}$ | Selon la méthode $\mathcal{M}$, appliquée à $g$ | Selon la méthode $\mathcal{M}$, appliquée à $g$ |

En forme paramétrique, la dérivée $x'(t)$ est soit connue, soit approximée par une [dérivée numérique](math_derivation_numerique.md).

### 2. $a$ et $b$, ou $t_a$ et $t_b$ : les bornes d'intégration

Définissent l'intervalle de la variable indépendante sur lequel l'intégration est effectuée. En forme paramétrique, ce sont deux valeurs du paramètre et non deux abscisses.

### 3. $N$ : le nombre de sous-intervalles

Contrôle la finesse de la discrétisation. Il définit le pas d'intégration $h$, les noeuds, soit les points qui délimitent les sous-intervalles, et les valeurs $g_i$ de l'intégrande en ces noeuds :

| | Forme explicite | Forme paramétrique |
| :--- | :---: | :---: |
| Pas d'intégration | $h = \dfrac{b - a}{N}$ | $h = \dfrac{t_b - t_a}{N}$ |
| Noeuds | $x_i = a + i \cdot h$ | $t_i = t_a + i \cdot h$ |
| Valeurs de l'intégrande | $g_i = g(x_i)$ | $g_i = g(t_i)$ |

Comme le pas $h$ découle de $N$, il s'adapte de lui-même à l'étendue de la variable indépendante, contrairement au pas de la [dérivée numérique](math_derivation_numerique.md).

Augmenter $N$ augmente aussi le temps de calcul. Le choix optimal de $N$ est un compromis entre la précision souhaitée et les ressources de calcul.

### 4. $\mathcal{M}$ : la méthode d'approximation d'aire

Détermine la méthode d'approximation de l'aire sous la courbe. Il existe plusieurs méthodes possibles mais on présente ici celles basées sur l'approximation polynomiale de degrés variés pour approximer l'intégrande $g$ sur chaque sous-intervalle.

#### 4a. Méthode des rectangles ou somme de Riemann

Approximation de l'aire par l'aire d'un rectangle de hauteur $g_i^*$ (polynôme de degré 0).

$$
\widehat{I} = h \sum_{i=0}^{N-1} g_i^*
$$

Où $g_i^*$ est la valeur de l'intégrande au point d'évaluation du sous-intervalle $i$, défini plus bas par le paramètre $\alpha$.

#### 4b. Méthode des trapèzes

Approximation de l'aire par l'aire d'un trapèze (polynôme de degré 1).

$$
\widehat{I} = \frac{h}{2} \left[g_0 + 2 \sum_{i=1}^{N-1} g_i + g_N\right]
$$

#### 4c. Méthode de Simpson 1/3

Approximation de l'aire par l'intégration d'un polynôme quadratique de degré 2. Exige $N$ pair.

$$
\widehat{I} = \frac{h}{3} \left[g_0 + 4 \sum_{i=1, 3, \dots}^{N-1} g_i + 2 \sum_{i=2, 4, \dots}^{N-2} g_i + g_N\right]
$$

#### 4d. Méthode de Simpson 3/8

Approximation de l'aire par l'intégration d'un polynôme cubique de degré 3. Exige $N$ multiple de 3.

$$
\widehat{I} = \frac{3h}{8} \left[g_0 + 3 \sum_{\substack{i=1 \\ i \,\neq\, 3, 6, \dots}}^{N-1} g_i + 2 \sum_{i=3, 6, \dots}^{N-3} g_i + g_N\right]
$$


### 5. $\alpha$ : positionnement dans le sous-intervalle

Détermine la position du point d'évaluation dans chaque sous-intervalle. Cette paramétrisation n'existe que pour la méthode des rectangles, qui repose sur un point d'évaluation unique par sous-intervalle.

On définit la position du point d'évaluation à l'aide d'un facteur $\alpha \in [0, 1]$ :

| | Forme explicite | Forme paramétrique |
| :--- | :---: | :---: |
| Domaine d'application | L'axe des $x$ | Le paramètre $t$ |
| Point d'évaluation | $x_i^* = x_i + \alpha \cdot h$ | $t_i^* = t_i + \alpha \cdot h$ |
| Sens de *gauche* et *droite* | À gauche et à droite sur l'axe des $x$ | Au début et à la fin du sous-intervalle, selon le sens de parcours de la courbe |

| Valeur de $\alpha$ | Nom de la Méthode | Point $x_i^*$ en forme explicite | Point $t_i^*$ en forme paramétrique |
| :---: | :---: | :---: | :---: |
| $\mathbf{\alpha = 0}$ | Rectangle à gauche | $x_i$ | $t_i$ |
| $\mathbf{\alpha = 0.5}$ | Point milieu | $x_i + h/2$ | $t_i + h/2$ |
| $\mathbf{\alpha = 1}$ | Rectangle à droite | $x_{i+1}$ | $t_{i+1}$ |
| $\mathbf{\alpha \in ]0, 1[}$ | Rectangle généralisé | $x_i + \alpha \cdot h$ | $t_i + \alpha \cdot h$ |

## III. Conclusion

Le choix de la méthode d'intégration numérique est un arbitrage entre la **précision** et le **coût de calcul**, entièrement contrôlé par la **méthode**, le **pas $h$** et la **position relative $\alpha$ du point d'évaluation**.

### Synthèse des paramètres

| Paramètre | Description |
| :--- | :--- |
| La courbe | La courbe à intégrer, sous forme explicite ou paramétrique. Elle fixe l'intégrande $g$. |
| $a$ ou $t_a$ | La borne de départ de l'intervalle d'intégration. |
| $b$ ou $t_b$ | La borne d'arrivée de l'intervalle d'intégration. |
| $N$ | Le nombre de sous-intervalles. |
| $\mathcal{M}$ | La méthode d'approximation d'aire utilisée (rectangles, trapèzes, Simpson 1/3, Simpson 3/8). |
| $\alpha$ | Le facteur de positionnement du point d'évaluation dans chaque sous-intervalle (seulement pour la méthode des rectangles). |
