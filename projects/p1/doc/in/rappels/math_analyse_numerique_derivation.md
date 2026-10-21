<small>**C**égep du **V**ieux **M**ontréal&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;**S**ciences, **I**nformatique et **M**athématique</small><br><br>

# Techniques de dérivée numérique

Dans un projet d'exploration de méthodes numériques, la dérivation numérique est un sujet de choix : la méthode est simple, mais la qualité de son résultat dépend fortement de quelques réglages. 

Les paramètres présentés ici sont ce qui peut varier dans le problème, et c'est en les faisant varier qu'une analyse devient intéressante, sur papier comme dans un outil logiciel. Leur présentation sert donc de guide à chaque étape d'un tel travail, de la compréhension mathématique jusqu'à la conception et au code.

## I. Rappel des fondamentaux

Le problème de la dérivée numérique est d'approximer la pente $m$ d'une fonction en un point d'intérêt $\mathbf{P}$, en utilisant des points voisins de sa courbe.

Cette pente est la dérivée première $f'(x)$, donnée par la limite :
$$f'(x) = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}$$

Le principe repose sur l'approximation de cette limite en utilisant une valeur finie et petite pour le pas de comparaison $\mathbf{h}$. La tangente, de pente exacte $m$, est alors remplacée par la sécante passant par deux points voisins $P_-$ et $P_+$ de la courbe, de pente approchée $\widehat{m}$ :

$$
\widehat{m} = \frac{f(x_+) - f(x_-)}{h}
$$

Les points $P_- = (x_-, f(x_-))$ et $P_+ = (x_+, f(x_+))$ sont définis plus bas, par le paramètre $\alpha$.

Les notations communes aux rappels, dont celles de la *valeur exacte* et de la *valeur approchée*, sont définies dans le [lexique](math_lexique.md).

Plus le pas $h$ est petit, plus l'approximation est précise, sous réserve que les erreurs d'arrondi numérique ne deviennent pas dominantes.

---

## II. Paramètres de configuration

Une approximation de dérivée numérique est entièrement définie par les paramètres suivants :

### 1. La fonction à dériver

C'est la fonction dont on cherche la pente en un point. Tous les autres paramètres portent sur sa variable indépendante.

| Élément | Description |
| :--- | :---: |
| Variable indépendante | $x \in \mathcal{D}$ |
| Point de la courbe | $P = (x, f(x))$ |
| Pente exacte $m$ | $f'(x)$ |
| Pente approchée $\widehat{m}$ | $\dfrac{f(x_+) - f(x_-)}{h}$ |

### 2. $x$ : le point d'intérêt

C'est la valeur de $x$ où l'on souhaite calculer la pente. Elle détermine le point d'intérêt $\mathbf{P} = (x, f(x))$.

### 3. $h$ : le pas de comparaison

Définit l'écart, sur l'axe des $x$, entre les deux points voisins. Le pas $h$ s'exprime donc dans l'unité de $x$.

Une même valeur de $h$ n'a pas le même sens selon l'étendue de $x$. Un pas $h = 0.5$ est très fin si $x$ parcourt l'intervalle $[0, 100]$, mais couvre la moitié de l'intervalle $[0, 1]$. Il faut donc adapter $h$ à l'étendue de la variable indépendante.

### 4. $\alpha$ : positionnement autour du point d'intérêt

Détermine les positions relatives des deux points voisins autour du point d'intérêt.

On utilise deux valeurs de $x$, séparées de $h$ et positionnées à l'aide d'un facteur $\alpha \in [0, 1]$ :

| Élément | Description |
| :--- | :---: |
| Domaine d'application | L'axe des $x$, dans $\mathcal{D}$ |
| Première valeur | $x_- = \mathbf{x} - \alpha h$ |
| Seconde valeur | $x_+ = \mathbf{x} + (1 - \alpha) h$ |
| Sens de *avant* et *arrière* | À droite et à gauche de $\mathbf{P}$ |

Ces deux valeurs donnent les points $P_-$ et $P_+$ de la sécante, donc la pente approchée $\widehat{m}$ du paramètre 1. Elles sont toujours séparées de $h$ : $x_+ - x_- = h$.

| Valeur de $\alpha$ | Nom de la méthode | Valeurs $(x_-,\ x_+)$ |
| :---: | :---: | :---: |
| $\mathbf{\alpha = 0}$ | Différence avant | $(\mathbf{x},\ \mathbf{x} + h)$ |
| $\mathbf{\alpha = 0.5}$ | Différence centrée | $(\mathbf{x} - h/2,\ \mathbf{x} + h/2)$ |
| $\mathbf{\alpha = 1}$ | Différence arrière | $(\mathbf{x} - h,\ \mathbf{x})$ |
| $\mathbf{\alpha \in ]0, 1[}$ | Différence généralisée | $(\mathbf{x} - \alpha h,\ \mathbf{x} + (1 - \alpha) h)$ |

## III. Conclusion

La technique de dérivée numérique est une méthode simple et efficace pour estimer la pente d'une fonction en un point donné. Le choix du pas $h$ et de la position relative $\alpha$ des points de comparaison influence directement la précision de l'approximation. 

La méthode de différence centrée ($\alpha = 0.5$) est souvent privilégiée pour sa meilleure précision, mais le choix final dépend des contraintes spécifiques du problème à résoudre.

### Synthèse des paramètres

| Paramètre | Description |
| :--- | :--- |
| La fonction | La fonction à dériver, $f(x)$. |
| $x$ | Le point d'intérêt où l'on souhaite calculer la pente. |
| $h$ | Le pas de comparaison, définissant l'écart entre les deux points voisins sur l'axe des $x$. |
| $\alpha$ | Le facteur de positionnement des points de comparaison autour du point d'intérêt. |
