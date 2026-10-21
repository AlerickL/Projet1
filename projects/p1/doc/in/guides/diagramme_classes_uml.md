<small>**C**égep du **V**ieux **M**ontréal&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;**S**ciences, **I**nformatique et **M**athématique</small><br><br>

<a id="home"></a>

# Le diagramme de classes UML

Le diagramme de classes est une technique de conception où l'on **dessine** la structure du code **avant** de le programmer. C'est un schéma qui montre les classes du modèle, ce que chacune offre et comment elles sont reliées.

Un diagramme de classes représente **uniquement le modèle**. Les classes de l'interface graphique n'y figurent **jamais**.

L'objectif est de décider du découpage du logiciel, de répartir les responsabilités et de valider ces choix avec l'équipe pendant qu'ils ne coûtent encore rien à corriger. Le diagramme sert aussi à **explorer** le logiciel à construire : il traduit les besoins révélés par la [maquette](maquettage_interface_graphique.md) en classes concrètes.

## 1. En quoi consiste le diagramme de classes

Un diagramme de classes répond à trois questions : 
- quoi : quelles classes composent le modèle
- qui fait quoi : ce que chaque classe sait (attributs) et ce qu'elle fait (opérations)
- avec qui : comment les classes sont reliées entre elles

Il ne répond pas à la question du *comment* : le contenu des méthodes n'y figure pas.

Le diagramme repose sur deux niveaux complémentaires :

| Niveau | Description | Objectif |
| :--- | :--- | :--- |
| **La&nbsp;vue&nbsp;d'ensemble** <br> ou diagramme de structure | Elle montre toutes les classes du modèle et leurs relations. Chaque classe est une simple boîte portant son nom. Les attributs et les opérations sont absents. | Mode exploration, on décide du découpage, des responsabilités et des dépendances. On facilite une vue d'ensemble sans surcharge visuelle. |
| **La&nbsp;vue&nbsp;de&nbsp;détail** <br> ou diagramme de classe détaillé | Elle montre une classe, ou un petit groupe de classes liées, avec ses membres publics : attributs, propriétés et opérations, chacun avec son type. | Mode précision, on fixe l'interface publique d'une classe : ce que le reste du code pourra lui demander. |

### Ce qui mérite une vue de détail

1.  Une classe du modèle : son interface publique est justement la question à résoudre.
2.  Une classe partagée : plusieurs membres de l'équipe l'utilisent et doivent s'entendre sur ce qu'elle offre.
3.  Une classe porteuse de règles : validation, valeurs interdites, attributs en lecture seule.

Une classe fournie ou provenant d'une bibliothèque (`ndarray`, `Enum`) ne mérite pas de vue de détail. Une boîte portant son nom suffit.

### Rappel de la notation

La notation retenue est définie dans la [norme de codage](../informations/norme_de_codage.md). En voici l'essentiel :

| Élément | Notation | Référence |
| :--- | :--- | :--- |
| Visibilité | `+` public, `#` protégé, `-` privé. Les soulignements de Python n'apparaissent jamais dans le diagramme. | [section 2.1](../informations/norme_de_codage.md#21-visibilité-des-membres-à-trois-niveaux) |
| Propriété | Un attribut public marqué `<<property>>`, suivi de `{readOnly}` s'il est en lecture seule. Sa variable interne n'est pas dessinée. | [section 2.2](../informations/norme_de_codage.md#22-propriétés) |
| Membre dérivé | Préfixé par `/` : sa valeur est calculée et non stockée. | [annexe 3](../informations/norme_de_codage.md#annexe-3---complément-sur-la-visibilité-des-membres-de-classe-et-des-propriétés) |

L'[annexe 3](../informations/norme_de_codage.md#annexe-3---complément-sur-la-visibilité-des-membres-de-classe-et-des-propriétés) présente un exemple complet, du diagramme jusqu'au code.

Les relations entre classes se résument à quatre cas :

| Relation | Sens | Exemple |
| :--- | :--- | :--- |
| Héritage | *est un* | Un polynôme est une fonction mathématique. |
| Composition | *possède* : la partie n'existe pas sans le tout | Une fonction possède ses paramètres. |
| Association | *connaît* : un lien durable entre deux objets indépendants | Une méthode d'intégration connaît la fonction qu'elle intègre. |
| Dépendance | *utilise* : un usage ponctuel, sans lien durable | Une fonction reçoit un objet en paramètre ou en retourne un. |

### Un outil d'exploration du logiciel

Dessiner les classes **avant** de programmer, c'est décider de l'organisation du code pendant qu'elle se change encore d'un trait de crayon. On explore le logiciel par sa structure; en se demandant qui est responsable de quoi, on découvre les classes manquantes, les classes trop chargées et les dépendances inutiles.

La maquette et le diagramme de classes se répondent. Chaque besoin révélé par la maquette trouve sa place dans le diagramme :

| Ce que révèle la maquette | Ce qui apparaît au diagramme |
| :--- | :--- |
| Une information affichée | Un attribut ou une propriété. |
| Un contrôle qui déclenche une action | Une opération. |
| Une valeur refusée ou une option grisée | Une propriété validée ou en lecture seule. |
| Deux zones qui partagent une même donnée | Une classe commune et les relations qui y mènent. |

Le diagramme fait partie du processus itératif de création. Il se situe entre la maquette, qui exprime les besoins, et le code, qui les réalise. Il évolue dans les deux sens : une retouche à la maquette ajoute une opération, et une difficulté rencontrée dans le code révèle une classe mal découpée. On corrige alors le diagramme d'abord, puis le code.

## 2. Avantages et inconvénients

| Avantages | Inconvénients |
| :--- | :--- |
| Erreurs peu coûteuses <br> Déplacer une responsabilité d'une classe à une autre prend quelques secondes sur un diagramme. Dans du code déjà écrit, cela prend des heures. | Fausse perception de lenteur <br> Le temps passé à modéliser semble retarder le code (bien que le temps total du projet diminue). |
| Vision commune <br> Toute l'équipe discute de la même structure. Chacun sait ce que les classes des autres lui offriront. | Fausse précision <br> Un diagramme trop détaillé donne l'illusion que tout est décidé et fige des choix qui devraient rester ouverts. |
| Travail en parallèle <br> Une interface publique convenue permet à deux personnes de programmer deux classes en même temps. | Désuétude <br> Un diagramme qui n'est pas mis à jour finit par contredire le code. |
| Modèle indépendant <br> Limité au modèle, le diagramme oblige à le concevoir sans rien emprunter à l'interface graphique. | Limite d'expression <br> Un diagramme de classes montre la structure, pas le déroulement. Il ne dit pas dans quel ordre les objets se parlent. |

## 3. Lignes directrices

Pour réaliser un diagramme utile :

| Ligne directrice | Mise en pratique |
| :--- | :--- |
| Partir&nbsp;des&nbsp;besoins <br> *éviter d'aborder directement le code* | Relire l'énoncé et la maquette. Les noms importants deviennent des classes candidates, les verbes deviennent des opérations candidates. |
| Une&nbsp;responsabilité&nbsp;par&nbsp;classe <br> *éviter la classe qui fait tout* | Décrire le rôle de chaque classe en une phrase. Si la phrase contient plusieurs *et*, la classe doit probablement être divisée. |
| Représenter&nbsp;le&nbsp;modèle&nbsp;seulement <br> *jamais l'interface graphique* | Le diagramme ne contient que les classes du modèle. Elles ne connaissent pas `Qt`. Les classes de l'interface graphique n'y figurent pas. |
| Montrer&nbsp;l'interface&nbsp;publique <br> *le moins de détails possible* | Dessiner ce que la classe offre aux autres. Les membres privés sont des détails d'implémentation et n'apparaissent que s'ils éclairent une décision. |
| Rester&nbsp;indépendant&nbsp;du&nbsp;langage <br> *la notation avant la syntaxe* | Utiliser les symboles `UML` et non la syntaxe de Python : pas de soulignements, pas de `self`, pas de décorateurs. |
| Séparer&nbsp;les&nbsp;niveaux <br> *un point de vue par schéma* | Garder la vue d'ensemble simple. Déplacer les détails dans des diagrammes distincts. |
| Annoter <br> *ce que le diagramme ne dit pas* | Ajouter de courtes notes sur les règles : domaine de validité d'une valeur, raison d'une lecture seule, choix de conception. |
| Itérer <br> *corriger sans regret* | Réviser le diagramme à chaque découverte. Un diagramme est fait pour évoluer avec le projet. |
| Perfection&nbsp;contreproductive <br> *viser un diagramme pertinent sachant qu'il sera imparfait* | Un diagramme de classes est un outil de communication et d'analyse, pas une finalité absolue à atteindre. Il est contreproductif de chercher un travail définitif, le développement du code révèlera des erreurs et des ajustements nécessaires. Il est normal qu'il évolue et s'améliore au fil du projet. Le défi est de trouver le bon compromis entre largeur et profondeur. |
| Tâche&nbsp;exigeante <br> *la modélisation demande de la réflexion* | Si vous avez terminé facilement et rapidement cette étape, vous n'avez pas fait le travail sérieusement avec le niveau de détail attendu. Ce travail demande de la réflexion, de l'analyse et est réputé pour être le plus difficile du projet. |

### Démarche suggérée

1.  Candidates : relever dans l'énoncé et la maquette les classes possibles, sans les juger.
2.  Vue d'ensemble : retenir les classes utiles, nommer leur responsabilité et tracer leurs relations.
3.  Vues de détail : pour chaque classe qui le mérite, définir l'interface publique à partir des besoins de la maquette.
4.  Validation : parcourir un scénario d'utilisation et vérifier que chaque étape trouve son opération dans le diagramme.
5.  Mise au propre : produire le diagramme avec l'outil retenu. La norme utilise `PlantUML` (voir son [annexe 5](../informations/norme_de_codage.md#annexe-5---consultation-des-documents-markdown-avec-visual-studio-code)).
6.  Itération : pendant la programmation, reprendre à une étape antérieure dès que le code et le diagramme divergent.

## 4. Pièges à éviter dans un contexte académique

Pour garantir le succès dans un contexte d'apprentissage :

| Piège à éviter | Stratégie corrective |
| :--- | :--- |
| Diagramme&nbsp;après&nbsp;coup <br> *on dessine le code une fois programmé* | Respecter l'ordre <br> Le diagramme se fait avant le code. Produit après, il ne sert plus à décider et devient une simple copie du code. |
| Notation&nbsp;selon&nbsp;le&nbsp;langage&nbsp;cible <br> *le diagramme reprend la syntaxe de Python* | Appliquer la notation <br> Respecter la norme UML sans considération pour le langage cible. Par exemple, remplacer les soulignements par les symboles de visibilité et les décorateurs par les stéréotypes imposés par la norme. |
| Classe&nbsp;fourre-tout <br> *une seule classe contient presque tout le logiciel* | Répartir les responsabilités <br> Regrouper les membres qui travaillent ensemble et en faire des classes distinctes, chacune avec un rôle clair. |
| Interface&nbsp;dans&nbsp;le&nbsp;diagramme <br> *une fenêtre, un panneau ou un widget apparaît parmi les classes* | Retirer ces classes <br> Le diagramme représente uniquement le modèle. Le modèle offre des données et des opérations, et ne connaît aucun widget. |
| Relations&nbsp;négligées <br> *des boîtes sans liens, ou des liens tous identiques* | Qualifier chaque lien <br> Choisir entre *est un*, *possède*, *connaît* et *utilise*. Un lien qu'on ne sait pas nommer cache une décision à prendre. |
| Diagramme&nbsp;figé <br> *on refuse de le modifier ou on cesse de le consulter* | Le garder vivant <br> Corriger le diagramme dès qu'une décision change, puis ajuster le code. |

## 5. Attentes minimales

Un diagramme de classes acceptable respecte **tous** les points suivants :

- il est réalisé **avant** le début de la programmation des classes qu'il décrit;
- il présente une vue d'ensemble des classes du modèle et de leurs relations - **important** : on n'inclut pas les classes de l'interface graphique;
- chaque relation est qualifiée (héritage, composition, association ou dépendance);
- chaque classe du modèle possède sa vue de détail, avec le type de chaque membre public;
- la notation respecte la [norme de codage](../informations/norme_de_codage.md) (visibilité, propriétés, membres dérivés);
- les classes du modèle ne dépendent d'aucune classe de l'interface graphique;
- chaque besoin révélé par la maquette y est repérable;
- il est déposé en fichier image dans le dossier `doc/out/assets/` (le format PNG est recommandé, les autres formats d'image sont acceptés);
- il est inséré dans le document `doc/out/des/uml_modele.md`, qui assemble tous les diagrammes;
- si un code source ou un fichier de travail a servi à le produire, il est déposé dans `doc/out/work/` pour permettre de le reproduire;
- sa version initiale, celle d'avant la programmation, est conservée dans `doc/out/assets/` à côté de la version finale;
- les écarts entre cette version initiale et le logiciel final sont expliqués dans le rapport.

## Bilan

Le diagramme de classes est bien plus qu'un exercice de notation ; c'est un outil de **conception**, d'**exploration** et de **communication** qui force à réfléchir à l'organisation du code avant de l'écrire.

Bien réalisé, un diagramme sobre coûte peu et évite beaucoup. Il répartit les responsabilités, fixe ce que chaque classe offre aux autres et donne à toute l'équipe une cible commune.

Avec la maquette, il forme un duo : l'une dit ce que l'utilisateur attend, l'autre dit comment le logiciel s'organise pour y répondre.

[↩️](#home)
