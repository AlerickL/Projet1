
<style>
  .reponse-etudiant {
    border: 1px solid #804020;
    background-color: #80808020;
    padding: 15px 30px;
    border-radius: 5px;
  }
</style>

<small>**C**égep du **V**ieux **M**ontréal&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;**S**ciences, **I**nformatique et **M**athématique</small><br><br>

# Rapport

### 420-SF3 Projet 1 - Logiciel d'exploration de méthodes numériques

<br>
<br>

## Directives pour remplir le rapport

Voici les directives importantes pour la rédaction de votre rapport :
- Il est **très important** de comprendre que **toutes** vos réponses **doivent** être **techniques**, **précises** et **concises**. Évitez les généralités, les phrases vagues et les discours philosophiques.
- Sauf pour la section `Évaluation individuelle`, vous devez répondre aux questions en équipe.
- Chaque section **doit** être complétée.
- Votre rapport consiste à remplir **ce** document `markdown` en insérant vos réponses exclusivement dans les sections encadrées par une boîte de réponse (comme ci-dessous). 

    <div class="reponse-etudiant">

    Contenu de votre réponse.

    Si votre réponse nécessite des instructions `markdown`, vous devez laisser un espace après la balise `<div>` et avant la balise `</div>`. C'est le cas ici à cause des caractères *apostrophe inversée* `` ` `` (ou *backtick* en anglais).

    Cette section **ne doit pas** être modifiée ou supprimée.

    </div>

- Vous **ne devez pas** : 
    - supprimer ces boîtes de réponse;
    - modifier le reste du document.
- Pour retrouver rapidement ces sections, recherchez `reponse-etudiant`.

<br>
<br>

## Identification des membres de l'équipe

<div class="reponse-etudiant">

- Langlois, Alérick [2546596]
- El ghardegue, Hiba [2582853] 
- Quinn Zachary [2561652]
- Delcourt, Arthur [2541195]

</div>

<br>
<br>

## Respect des exigences

Identifiez quelles sont les exigences du projet qui sont partiellement ou aucunement fonctionnelles. Pour chaque exigence, indiquez :
- un titre
- une courte description de l'exigence
- la raison principale pour laquelle l'exigence n'est pas (ou partiellement) fonctionnelle

Si toutes les exigences sont fonctionnelles, indiquez simplement : `Toutes les exigences sont fonctionnelles`.

<div class="reponse-etudiant">

Toutes les exigences sont fonctionnelles.

</div>

<br>
<br>

## Discussions techniques

### Conception et modélisation

La réalisation du projet repose sur une première étape consistant à faire une conception préliminaire basée sur un diagramme de classes UML et une maquette de l'interface utilisateur avant même le début du développement. Dans ce contexte, répondez aux questions suivantes :
1. De votre point de vue, quelle a été l'utilité du diagramme de classes UML dans le cadre de ce projet ?
1. En quoi la réalisation de la maquette de l'interface utilisateur a été pertinente ?
1. Nommez les principaux écarts entre votre conception initiale (maquette et diagramme de classes) et le logiciel remis, et donnez la raison de chacun.

<div class="reponse-etudiant">

Réponse aux questions sur la conception :
1. Le diagramme nous a permis d'accélérer la programmation, car nous avons pu nous séparer les taches. Ensuite, Il a facilité le développement, car nous avons prédit certains enjeux que nous allions rencontrer, et nous a permis d'avoir une vision plus globale du projet et de comprendre les enjeux de modularité.
1. La réalisation de la maquette de l'interface nous a servis d'aide mémoire pendant la conception du Gui. La maquette nous a permis de mieux se diviser le travail, en travaillant sur des widgets différents et en établissant les liens (signaux/slots) nécéssaires. Elle nous a aussi permis de compartimenter l'interface et de comprendre quels widgets était nécéssaire.
1. Écarts entre la conception initiale et le logiciel remis :
    - Écart 1 : La classe Modèle n'existait pas sur la première version.  
    Raison : Pour avoir un accès unique au modèle, et séparer le GUI du modèle, nous avons créé la classe modèle pour faire la gestion des intéractions GUI-modèle. De cette manière, toute intéraction avec le modèle ce fait à travers la classe modèle.
    - Écart 2 : Les méthodes privées utilisées 
    Raison : Nos méthodes privées nous ont permis de simplifier les calculs, d'éviter la répétion du code, et d'expliciter la logique. 
    - Écart 3 : La façon de transmettre de l'information  
    Raison: Nous avons ajoutés des Enums, car il était nécéssaire de sauvegarder la façon d'afficher ce qui devait l'être.


</div>

### Structures de données

Outre l'utilisation de `NumPy` pour les calculs numériques, identifiez une structure de données que vous avez utilisée dans votre projet. Attention, on désire que votre choix soit pertinent dans le contexte du projet. Répondez aux questions suivantes :
1. Quelle structure de données avez-vous choisie ?
1. Dans quel contexte l'avez-vous utilisée ?
1. Pourquoi cette structure de données est-elle pertinente dans le contexte du projet et pourquoi vous l'avez retenue plutôt qu'une autre ?

<div class="reponse-etudiant">

Réponse aux questions sur les structures de données :
1. La liste
1. Dans QBoutonMultipleRealSlider, nous l'avons utilisé pour les sliders et les boutons. Plusieurs autres classes du GUI héritent de celle-ci.
1. Cette structure de données permet d'implementer le polymorphisme en permettant de changer la quantité de sliders et de boutons dépendament du besoin.

</div>

### Paradigme de programmation orientée objet

Dans le but de consolider vos compétences en programmation orientée objet (POO), ce projet met l'accent sur l'utilisation de ce paradigme. Répondez aux questions suivantes :
1. Dans le code que **vous** avez produit, nommez au moins un endroit où vous avez utilisé :
    - l'encapsulation
    - l'héritage
    - le polymorphisme
1. Nommez 2 avantages et 1 inconvénient de la modélisation proposée pour la classe abstraite `MathFunction`.
1. Pourquoi le polymorphisme est-il particulièrement utile dans ce projet ?

<div class="reponse-etudiant">

Réponse aux questions sur la POO :
1. Utilisation des concepts de la POO dans le code produit :
    - Encapsulation : Dans QGraphique, nous avons encapsulé la méthode privée __actualiserMethodeNumerique et la slot actualiser l'appelle. Celle-ci appelle également plusieurs autres méthodes encapsulées.
    - Héritage : methode_integrale et methode_derive qui héritent de methode_numerique
    - Polymorphisme : la méthode calculer dans fonction_math applique les transformation canoniques à la méthode calculer de ses enfants.
1. Modélisation de la classe abstraite `MathFunction` :
    1. Avantage 1 : Par héritage, la classe FonctionMath réduit la répétition de code dans ses classes enfants.
    1. Avantage 2 : 
    1. Inconvénient : L'inconvénient de FonctionMath, c'est qu'elle ne permet de changer le type de fonction au sein d'elle même. Ce qui veut dire que nous devons instancier chaque fonction indépendamment. FonctionMath ne sert donc pas d'interface de gestion des fonctions, ce qui aurait été utile si nous avions un beaucoup plus gros projet avec, par exemple, 100 fonctions.
1. Utilité du polymorphisme : Nous avons beaucoup de classes différentes, avec des patrons similaires et les mêmes entrées, mais des fonctionnements très différents. Par exemple, toutes les classes qui héritent de QMultipleRealSlider ont les mêmes intrants, mais vont modifier des sections complétement différentes du modèle/gui. D'autres exemples sont les méthodes numériques et les fonctions.

</div>

### Interprétation du mandat

Le mandat du projet présente volontairement quelques zones d'ombre que votre équipe devait interpréter. Autrement dit, certaines informations sont implicites et requièrent soit une discussion avec l'enseignant précisant les détails manquants ou une prise de décisions éclairées au sein de l'équipe. Répondez aux questions suivantes :
1. Nommez au moins une zone d'ombre que vous avez identifiée dans le mandat. Attention, il doit s'agir d'une zone d'ombre **significative** qui a eu un impact sur la modélisation ou la réalisation du projet.
1. Quelle décision a été prise par votre équipe concernant cette zone d'ombre et pourquoi ?

<div class="reponse-etudiant">

Réponse aux questions sur l'interprétation du mandat :
1. Zone d'ombre identifiée : Dans le mandat, On ne sait pas si les transformations canoniques devraient être sauvegardées lorsqu'on change de fonction ou non. Cette zone d'ombre est significative, car cela change la conception du projet. Si nous n'avions pas eu besoin de sauvegarder les transformations canoniques, nous aurions pu simplement créer un objet de transformation pour chaque fonction.
1. Décision prise et raison : On a décidé de sauvegardées les transformations canoniques. Cela facilite la comparaison des fonctions soumises aux mêmes conditions. 

</div>


<br>
<br>

## Évaluation individuelle

Cette section décrit une contribution individuelle au projet par chaque membre de l'équipe selon son point de vue. Les sujets à couvrir sont :
1. nommez **la** tâche à laquelle vous avez contribué de manière la plus significative
1. décrivez brièvement le défi le plus important de cette tâche et comment vous l'avez surmonté
1. selon vous, quelle est la partie la plus difficile de tout le projet en considérant uniquement les aspects techniques
1. selon vous, quelle est la partie la plus difficile de tout le projet en considérant exclusivement l'organisation du travail en équipe

<div class="reponse-etudiant">

Évaluation individuelle par étudiant :
- Prénom et nom de l'étudiant 1
    1. ...
    1. ...
    1. ...
    1. ...
- Prénom et nom de l'étudiant 2
    1. ...
    1. ...
    1. ...
    1. ...
- Alérick
    1. 
    1. ...
    1. ...
    1. ...
- Arthur Delcourt
    1. La tâche à laquelle j'ai contribué de la manière la plus significative est la création et l'organisations des premiers widgets du menu, comme les QParametre, QTransformationCanonique et autres.
    1. Le défis le plus important a été celui de la réutilisation du code. Il me fallait trouver une façon de ne pas me répéter dans mon code. Je l'ai surmonté en créant les classes QMultipleRealSliderSpinBox et QBooutonMultipleRealSilderSpinBox avec lesquels j'ai construit de nombreuses classes enfants.
    1. Pour moi, la partie la plus difficile en gardant en tête uniquement les aspects techniques a été de gérer certains signaux pour les classes du gui. Plusieurs bugs relié à la priorité des signaux sont apparus au cours du projet et ça m'a prit du temps pour comprendre la nécessité de la commande blocksignal pour solutionner le problème.
    1. Ce qui a été selon moi le plus difficile pour ce qui était du travail en équipe était de trouver des périodes de disponibilités communes pour travailler tous ensemble sur le projet. Nous avons trouver de tel moment, mais avons eu a faire des compromis.


</div>

<br>
<br>

## Autoévaluation d'équipe
N'oubliez pas que vous devez **obligatoirement** remplir en équipe le document `doc/out/final/autoevaluation_equipe.xlsx`. 