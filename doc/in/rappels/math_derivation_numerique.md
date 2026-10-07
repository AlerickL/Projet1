<small>**C**égep du **V**ieux **M**ontréal&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;**S**ciences, **I**nformatique et **M**athématique</small><br><br>

# Techniques de dérivée numérique

Dans un projet d'exploration de méthodes numériques, la dérivation numérique est un sujet de choix : la méthode est simple, mais la qualité de son résultat dépend fortement de quelques réglages. 

Les paramètres présentés ici sont ce qui peut varier dans le problème, et c'est en les faisant varier qu'une analyse devient intéressante, sur papier comme dans un outil logiciel. Leur présentation sert donc de guide à chaque étape d'un tel travail, de la compréhension mathématique jusqu'à la conception et au code.

## I. Rappel des fondamentaux

Le problème de la dérivée numérique est d'approximer la pente $m$ d'une courbe en un point d'intérêt $\mathbf{P}$, en utilisant des points voisins de la courbe.

Pour une fonction $f(x)$, cette pente est la dérivée première $f'(x)$, donnée par la limite :
$$f'(x) = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}$$

Le principe repose sur l'approximation de cette limite en utilisant une valeur finie et petite pour le pas de comparaison $\mathbf{h}$. La tangente, de pente exacte $m$, est alors remplacée par la sécante passant par deux points voisins $P_-$ et $P_+$ de la courbe, de pente approchée $\widehat{m}$ :

$$
\widehat{m} = \frac{y_+ - y_-}{x_+ - x_-}
$$

Les points $P_- = (x_-, y_-)$ et $P_+ = (x_+, y_+)$ sont définis plus bas, par le paramètre $\alpha$.

Cette formule vaut pour les formes explicite et paramétrique d'une courbe, présentées dans [Représentations d'une courbe plane](math_representations_courbe_plane.md). La forme implicite n'est pas abordée ici. Les termes et les notations communs aux rappels, dont *valeur exacte* et *valeur approchée*, sont définis dans le [lexique](math_lexique.md).

Plus le pas $h$ est petit, plus l'approximation est précise, sous réserve que les erreurs d'arrondi numérique ne deviennent pas dominantes.

---

## II. Paramètres de configuration

Une approximation de dérivée numérique est entièrement définie par les paramètres suivants :

### 1. La courbe à dériver

C'est la courbe dont on cherche la pente en un point. Sa forme fixe la variable indépendante, sur laquelle portent tous les autres paramètres.

| | Forme explicite | Forme paramétrique |
| :--- | :---: | :---: |
| Variable indépendante | $x \in \mathcal{D}$ | $t \in \mathcal{T}$ |
| Point de la courbe | $P = (x, f(x))$ | $P = (x(t), y(t))$ |
| Pente exacte $m$ | $f'(x)$ | $\dfrac{y'(t)}{x'(t)}$ |
| Pente approchée $\widehat{m}$ | $\dfrac{f(x_+) - f(x_-)}{h}$ | $\dfrac{y(t_+) - y(t_-)}{x(t_+) - x(t_-)}$ |

### 2. $x$ ou $t$ : le point d'intérêt

C'est la valeur de la variable indépendante où l'on souhaite calculer la pente. Elle détermine la position du point d'intérêt $\mathbf{P}$.

### 3. $h$ : le pas de comparaison

Définit l'écart, sur la variable indépendante, entre les deux points voisins. Le pas $h$ s'exprime donc dans l'unité de cette variable : celle de $x$ en forme explicite, celle de $t$ en forme paramétrique.

Une même valeur de $h$ n'a donc pas le même sens d'une forme à l'autre. Si $x$ parcourt l'intervalle $[0, 100]$ et que $t$ parcourt $[0, 1]$, un pas $h = 0.5$ est très fin pour la première et couvre la moitié de la courbe pour la seconde. En passant d'une forme à l'autre, il faut adapter $h$ à l'étendue de la variable indépendante.


### 4. $\alpha$ : positionnement autour du point d'intérêt

Détermine les positions relatives des deux points voisins autour du point d'intérêt.

On utilise deux valeurs de la variable indépendante, séparées de $h$ et positionnées à l'aide d'un facteur $\alpha \in [0, 1]$ :

| | Forme explicite | Forme paramétrique |
| :--- | :---: | :---: |
| Domaine d'application | L'axe des $x$, dans $\mathcal{D}$ | Le paramètre $t$, dans $\mathcal{T}$ |
| Première valeur | $x_- = \mathbf{x} - \alpha \cdot h$ | $t_- = \mathbf{t} - \alpha \cdot h$ |
| Seconde valeur | $x_+ = \mathbf{x} + (1 - \alpha) \cdot h$ | $t_+ = \mathbf{t} + (1 - \alpha) \cdot h$ |
| Sens de *avant* et *arrière* | À droite et à gauche de $\mathbf{P}$ | Selon le sens de parcours de la courbe |

Ces deux valeurs donnent les points $P_-$ et $P_+$ de la sécante, donc la pente approchée $\widehat{m}$ du paramètre 1. En forme explicite, $x_+ - x_- = h$. En forme paramétrique, le pas $h$ se simplifie dans le quotient $y'(t) / x'(t)$, et il faut $x_+ \neq x_-$ : la formule ne s'applique pas à une tangente verticale.

| Valeur de $\alpha$ | Nom de la Méthode | Valeurs $(x_-,\ x_+)$ en forme explicite | Valeurs $(t_-,\ t_+)$ en forme paramétrique |
| :---: | :---: | :---: | :---: |
| $\mathbf{\alpha = 0}$ | Différence avant | $(\mathbf{x},\ \mathbf{x} + h)$ | $(\mathbf{t},\ \mathbf{t} + h)$ |
| $\mathbf{\alpha = 0.5}$ | Différence centrée | $(\mathbf{x} - h/2,\ \mathbf{x} + h/2)$ | $(\mathbf{t} - h/2,\ \mathbf{t} + h/2)$ |
| $\mathbf{\alpha = 1}$ | Différence arrière | $(\mathbf{x} - h,\ \mathbf{x})$ | $(\mathbf{t} - h,\ \mathbf{t})$ |
| $\mathbf{\alpha \in ]0, 1[}$ | Différence généralisée | $(\mathbf{x} - \alpha \cdot h,\ \mathbf{x} + (1 - \alpha) \cdot h)$ | $(\mathbf{t} - \alpha \cdot h,\ \mathbf{t} + (1 - \alpha) \cdot h)$ |


## III. Conclusion

La technique de dérivée numérique est une méthode simple et efficace pour estimer la pente d'une courbe en un point donné. Le choix du pas $h$ et de la position relative $\alpha$ des points de comparaison influence directement la précision de l'approximation. 

La méthode de différence centrée ($\alpha = 0.5$) est souvent privilégiée pour sa meilleure précision, mais le choix final dépend des contraintes spécifiques du problème à résoudre.

### Synthèse des paramètres

| Paramètre | Description |
| :--- | :--- |
| La courbe | La courbe à dériver, sous forme explicite ou paramétrique. |
| $x$ ou $t$ | Le point d'intérêt où l'on souhaite calculer la pente. |
| $h$ | Le pas de comparaison, définissant l'écart entre les deux points voisins sur la variable indépendante. |
| $\alpha$ | Le facteur de positionnement des points de comparaison autour du point d'intérêt. |
