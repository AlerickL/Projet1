<small>**C**égep du **V**ieux **M**ontréal&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;**S**ciences, **I**nformatique et **M**athématique</small><br><br>

<a id="home"></a>

# Le maquettage d'une interface graphique

Le maquettage ou *wireframing* est une technique de conception où l'on **dessine** l'interface **avant** de la programmer. Une maquette est un schéma volontairement simple qui montre ce que l'interface contient et comment elle s'organise.

L'objectif est de décider de la structure de l'interface, de valider les choix avec l'équipe et de détecter les oublis pendant qu'ils ne coûtent encore rien à corriger. La maquette sert aussi à **explorer** le logiciel à construire : elle révèle ce que le code devra offrir, bien au-delà de l'interface.

## 1. En quoi consiste le maquettage

Une maquette répond à trois questions : 
- quoi : quels contrôles et quelles informations
- où : comment ils sont regroupés
- dans quel ordre : ce que l'utilisateur rencontre en premier

Elle ne répond pas à la question de l'apparence finale.

Le maquettage repose sur deux niveaux complémentaires :

| Niveau | Description | Objectif |
| :--- | :--- | :--- |
| **La&nbsp;vue&nbsp;d'ensemble** <br> ou maquette de structure | Elle montre une fenêtre entière. Chaque zone est une simple boîte nommée par son intention : réglage de l'échelle, tracé de la courbe, résumé des paramètres. Les détails de chaque composant sont absents. | Mode exploration, on décide du contenu, des regroupements et de la hiérarchie. On facilite une vue d'ensemble sans surcharge visuelle. |
| **La&nbsp;vue&nbsp;de&nbsp;détail** <br> ou maquette de composant | Elle isole un composant (une sous-partie) et le montre en détail hors de son contexte. On y présente ses états (actif, inactif, erreur), ses cas limites et parfois deux ou trois variantes à comparer. | Mode précision, on règle la forme d'un composant nouveau ou difficile. Ces dessins sont séparés de la vue d'ensemble et permettent de se concentrer sur les détails. |

### Ce qui mérite une vue de détail

1.  Un composant nouveau : sa forme est justement la question à résoudre.
2.  Un composant à plusieurs états : un seul dessin ne suffit pas à le décrire.
3.  Une contrainte de place : on doute que les éléments tiennent dans l'espace prévu.

Un composant standard ou déjà existant (bouton, liste déroulante, curseur) ne mérite pas de vue de détail. Une boîte étiquetée suffit.

### Un outil d'exploration du logiciel

Dessiner l'interface **avant** de programmer, c'est partir du résultat attendu pour découvrir ce qu'il faut construire. On explore le logiciel par l'usage; en se demandant ce que l'utilisateur doit voir et faire, on trouve ce que le code doit offrir. Les besoins apparaissent clairement, un à un, plutôt qu'en cours de programmation.

Chaque élément dessiné devient ainsi une exigence :

| Ce que montre la maquette | Ce qu'elle exige du logiciel |
| :--- | :--- |
| Une information affichée | Le modèle doit fournir cette donnée. |
| Un contrôle qui déclenche une action | Le modèle doit offrir cette opération. |
| Une valeur refusée ou une option grisée | Le modèle doit porter cette règle. |

La maquette fait partie du processus itératif de création. Elle guide la conception de l'interface, précise le fonctionnement attendu de chaque fonctionnalité et oriente le développement technique. Son influence dépasse le code de l'interface et atteint celui du **modèle** : on voit plus facilement quelles classes développer et quelle interface publique leur donner. On réduit ainsi les allers-retours entre conception et implémentation, et le logiciel gagne en cohérence.

## 2. Avantages et inconvénients

| Avantages | Inconvénients |
| :--- | :--- |
| Erreurs peu coûteuses <br> Déplacer une boîte prend quelques secondes. Réorganiser une interface déjà programmée prend des heures. | Fausse perception de lenteur <br> Le temps passé à dessiner semble retarder le code (bien que le temps total du projet diminue). |
| Vision commune <br> Toute l'équipe discute du même dessin. Les malentendus apparaissent avant la programmation. Mieux encore, la maquette favorise l'alignement général du projet en précisant concrètement ce qui est à produire. | Fausse précision <br> Une maquette trop soignée donne l'illusion que tout est décidé et attire des remarques sur le dessin plutôt que sur la conception. |
| Besoins révélés <br> Chaque contrôle dessiné exige une donnée ou une opération. La maquette révèle ainsi ce que les classes du modèle doivent offrir. | Désuétude <br> Une maquette qui n'est pas mise à jour finit par contredire le logiciel. |
| Liberté d'explorer <br> On compare deux dispositions en les dessinant, sans écrire une ligne de code. | Limite d'expression <br> Une maquette montre mal le mouvement et l'interaction (animation, glisser-déposer). |

## 3. Lignes directrices

Pour réaliser une maquette utile :

| Ligne directrice | Mise en pratique |
| :--- | :--- |
| Partir des besoins <br> éviter d'aborder directement les widgets | Lister d'abord ce que l'utilisateur doit voir et ce qu'il doit pouvoir faire. Chaque élément de la maquette doit répondre à un besoin de cette liste. |
| Nommer par l'intention <br> éviter d'aborder le projet par les considérations d'implémentation technique | Définir une zone *Choix de la fonction* plutôt que `QComboBox`. Le choix du widget vient après et reste un détail d'implémentation. |
| Rester sobre <br> le moins de détails possible | Utiliser des boîtes, des étiquettes et du gris. Pas de couleurs, pas d'icônes soignées, pas d'alignement au pixel. |
| Regrouper et hiérarchiser <br> structurer et organiser | Placer ensemble ce qui est lié. Mettre en évidence ce qui est le plus utilisé. Vérifier l'ordre de lecture, de haut en bas et de gauche à droite. |
| Séparer les niveaux <br> une question par dessin | Garder la vue d'ensemble simple. Déplacer tout détail nécessaire dans une vue de détail distincte. |
| Annoter <br> ce que le dessin ne dit pas | Ajouter de courtes notes sur le comportement : ce qui se passe au clic, ce qui est lié, ce qui est interdit. |
| Itérer <br> jeter sans regret | Produire plusieurs versions rapides et les comparer. Une maquette est faite pour être remplacée. |

### Démarche suggérée

1.  Croquis : dessiner à la main deux ou trois dispositions différentes, en quelques minutes chacune.
2.  Choix : discuter en équipe et retenir une disposition.
3.  Mise au propre : reproduire la disposition retenue dans un outil de maquettage.
4.  Détails : ajouter une vue de détail pour chaque composant qui le mérite.
5.  Validation : relire la maquette en la comparant à l'énoncé, puis en déduire les besoins du modèle (diagramme de classes).
6.  Itération : au besoin, reprendre à une étape antérieure.

## 4. Pièges à éviter dans un contexte académique

Pour garantir le succès dans un contexte d'apprentissage :

| Piège à éviter | Stratégie corrective |
| :--- | :--- |
| Excès de détails <br> on dessine chaque bouton et chaque graduation | Revenir à l'intention <br> Remplacer le composant par une boîte étiquetée. Se demander quelle décision ce détail aide à prendre. S'il n'en aide aucune, il est de trop. |
| Maquette après coup <br> on dessine le logiciel une fois programmé | Respecter l'ordre <br> La maquette se fait avant le code. Dessinée après, elle ne sert plus à décider et devient une simple capture d'écran. |
| Maquette solitaire <br> un seul membre la produit et les autres la découvrent | Concevoir en équipe <br> Les croquis et le choix de la disposition se font ensemble. La mise au propre peut ensuite être confiée à une personne. |
| Attachement <br> on refuse de modifier une maquette qui a demandé beaucoup de travail | Rester rapide <br> Une maquette sobre se refait en quelques minutes. C'est sa sobriété qui la rend facile à remettre en question. |
| Oubli de l'énoncé <br> la maquette est élégante mais incomplète | Vérifier la couverture <br> Passer l'énoncé point par point et repérer chaque exigence sur la maquette. |
| Graphisme <br> se concentrer sur l'esthétique plutôt que sur la fonctionnalité | Ne pas oublier l'intention <br> Une maquette doit avant tout clarifier les besoins et l'organisation de l'interface. Le graphisme est secondaire et ne doit pas masquer les choix fonctionnels. Plus important encore, certains étudiants confondent les objectifs du cours. Ce n'est pas un cours de graphisme mais de développement logiciel! Faites attention au temps considérable que demande le raffinement graphique. |

## 5. Attentes minimales

Une maquette acceptable respecte **tous** les points suivants :

- elle est réalisée **avant** le début de la programmation de l'interface;
- elle présente une vue d'ensemble de chaque fenêtre de l'application;
- chaque zone est nommée par son intention et son rôle se comprend sans explication orale;
- chaque exigence de l'énoncé qui touche l'interface y est repérable;
- chaque composant nouveau ou à plusieurs états possède sa vue de détail;
- de courtes annotations décrivent les comportements que le dessin ne montre pas;
- elle est déposée en fichier image dans le dossier `doc/out/assets/` (le format PNG est recommandé, les autres formats d'image sont acceptés);
- elle est insérée dans le document `doc/out/des/maquettes.md`, qui assemble toutes les maquettes;
- si un fichier de travail a servi à la produire, il est déposé dans `doc/out/work/` pour permettre de la reproduire;
- sa version initiale, celle d'avant la programmation, est conservée dans `doc/out/assets/` à côté de la version finale;
- les écarts entre cette version initiale et le logiciel final sont expliqués dans le rapport.

## Bilan

Le maquettage est bien plus qu'un exercice de dessin ; c'est un outil de **conception**, d'**exploration** et de **communication** qui force à réfléchir à l'utilisateur avant de réfléchir au code.

Bien réalisée, une maquette sobre coûte peu et évite beaucoup. Elle clarifie les objectifs de l'interface, révèle les besoins du modèle et donne à toute l'équipe une cible commune.

Elle est certainement l'un des outils les plus puissants et sous-estimés du développement logiciel en début de projet.

[↩️](#home)
