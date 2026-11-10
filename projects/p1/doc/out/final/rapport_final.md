
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

- El Ghardegue, Hiba[2582853] 
- Nom, Prénom [matricule] de l'étudiant 2
- Pignon, François [12345678]
- ...
- mettre le nom de tous les étudiants et retirer cette ligne

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

Liste des exigences partiellement fonctionnelles ou non fonctionnelles :
- Titre 1 :
    - Description :
    - Raison principale :
- Titre 2 :
    - Description :
    - Raison principale :
- ...

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
1. ...
1. ...
1. Écarts entre la conception initiale et le logiciel remis :
    - Écart 1 : ... Raison : ...
    - Écart 2 : ... Raison : ...
    - ...

</div>

### Structures de données

Outre l'utilisation de `NumPy` pour les calculs numériques, identifiez une structure de données que vous avez utilisée dans votre projet. Attention, on désire que votre choix soit pertinent dans le contexte du projet. Répondez aux questions suivantes :
1. Quelle structure de données avez-vous choisie ?
1. Dans quel contexte l'avez-vous utilisée ?
1. Pourquoi cette structure de données est-elle pertinente dans le contexte du projet et pourquoi vous l'avez retenue plutôt qu'une autre ?

<div class="reponse-etudiant">

Réponse aux questions sur les structures de données :
1. ...
1. ...
1. ...

</div>

### Paradigme de programmation orientée objet

Dans le but de consolider vos compétences en programmation orientée objet (POO), ce projet met l'accent sur l'utilisation de ce paradigme. Répondez aux questions suivantes :
1. Dans le code que **vous** avez produit, nommez au moins un endroit où vous avez utilisé :
    - l'encapsulation
    - l'héritage
    - le polymorphisme
1. Nommez 2 avantages et 1 inconvénient de la modélisation proposée pour la classe abstraite `MathFunction`.
1. Pourquoi le polymorphisme est-il particulièrement utile dans ce projet ?

<div class="-etudiant">

Réponse aux questions sur la POO :
1. Utilisation des concepts de la POO dans le code produit :
    - Encapsulation : ...
    - Héritage : ...
    - Polymorphisme : ...
1. Modélisation de la classe abstraite `MathFunction` :
    1. Avantage 1 : ...
    1. Avantage 2 : ...
    1. Inconvénient : ... 
1. Utilité du polymorphisme : ...

</div>

### Interprétation du mandat

Le mandat du projet présente volontairement quelques zones d'ombre que votre équipe devait interpréter. Autrement dit, certaines informations sont implicites et requièrent soit une discussion avec l'enseignant précisant les détails manquants ou une prise de décisions éclairées au sein de l'équipe. Répondez aux questions suivantes :
1. Nommez au moins une zone d'ombre que vous avez identifiée dans le mandat. Attention, il doit s'agir d'une zone d'ombre **significative** qui a eu un impact sur la modélisation ou la réalisation du projet.
1. Quelle décision a été prise par votre équipe concernant cette zone d'ombre et pourquoi ?

<div class="reponse-etudiant">

Réponse aux questions sur l'interprétation du mandat :
1. Zone d'ombre identifiée : ...
1. Décision prise et raison : ...

</div>


<br>
<br>

## Évaluation individuelle

Cette section décrit une contribution individuelle au projet par chaque membre de l'équipe selon son point de vue. Les sujets à couvrir sont :
`1. nommez **la** tâche à laquelle vous avez contribué de manière la plus significative
1. décrivez brièvement le défi le plus important de cette tâche et comment vous l'avez surmonté
1. selon vous, quelle est la partie la plus difficile de tout le projet en considérant uniquement les aspects techniques`
1. selon vous, quelle est la partie la plus difficile de tout le projet en considérant exclusivement l'organisation du travail en équipe

<div class="reponse-etudiant">

Évaluation individuelle par étudiant :
- Hiba El ghardegue 
    1. moi personnelemnt ,j’ai surtout contribué au modèle en programmant deux fonctions mathématiques à paramètres ajustables, ainsi que le calcul de leur dérivée et de leur intégrale.
    1. le defi le plus important c’était d’intégrer au modèle les fonctions que j’ai codées. pour le surmonte on a éfini la primitive de chaque fonction en se basant sur ses paramètres. Ensuite, on a utilisé la méthode de la classe FonctionMath pour calculer l’intégrale entre deux bornes.
    1. Selon moi, le plus difficile, c’était de relier l’interface graphique au modèle. Quand on a commencé à coder l’interface, il manquait la classe Modele.C’était plus simple de transmettre les paramètres au modèle et de récupérer les résultats à afficher.
    1. En effet , le travail en group a globalement  bien passer , peut-etre trouver des dispos communes a etait la seule complication .
- Prénom et nom de l'étudiant 2
    1. ...
    1. ...
    1. ...
    1. ...
- ...
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