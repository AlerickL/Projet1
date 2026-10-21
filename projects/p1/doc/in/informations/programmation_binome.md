<small>**C**égep du **V**ieux **M**ontréal&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;**S**ciences, **I**nformatique et **M**athématique</small><br><br>

<a id="home"></a>

# La programmation en binôme

La programmation en binôme ou le *pair-programming* est une technique de développement agile où **deux** développeurs travaillent **ensemble** sur un même projet. 

L'objectif est d'améliorer la qualité du code, de favoriser le partage des connaissances et de renforcer la collaboration au sein de l'équipe.

## 1. En quoi consiste la programmation en binôme

La programmation en binôme repose sur deux rôles principaux qui doivent **alterner** régulièrement (en classe, toutes les 30-60 minutes) :

| Rôle | Description | Objectif |
| :--- | :--- | :--- |
| **Le&nbsp;conducteur** <br> ou pilote | Il a les mains sur le clavier. Il écrit le code, se concentre sur les détails syntaxiques et la mise en oeuvre immédiate de la tâche. | Mode production, il met en oeuvre les instructions du navigateur. |
| **Le&nbsp;navigateur** <br> ou copilote | Il observe, révise le code en temps réel et guide le conducteur. Il se concentre sur la stratégie globale, les objectifs à long terme et la détection d'erreurs logiques ou de design. Il a tous les documents nécessaires à portée de main et avec une vue d'ensemble il peut anticiper les problèmes et réfléchir à de meilleurs designs. | Mode supervision, il maintient la vision globale et la qualité du code. |

### Configuration idéale en pédagogie

1.  Deux ordinateurs côte à côte :
    - le conducteur a tous les documents de production de code ouverts
    - le navigateur a tous les documents de référence ouverts (énoncé, documentation, conception, modélisation, références techniques, ...)
2.  Alternance stricte : Définir un minuteur (par exemple 30 minutes) pour forcer le changement de rôle et s'assurer que les deux participent activement à la pensée stratégique et à l'écriture. C'est l'un des aspects les plus difficiles dans un contexte académique.
3.  Communication constante : Il est essentiel que le navigateur verbalise ses réflexions et ses suggestions tout au long du processus. Aucune gêne ne devrait entraver cette communication.
4.  Règles de collaboration : Établir des règles claires pour la collaboration, comme le respect mutuel, l'écoute active et la résolution constructive des conflits.

## 2. Avantages et inconvénients

| Avantages | Inconvénients |
| :--- | :--- |
| Qualité du code <br> Réduction immédiate des erreurs et des fautes de frappe (revue en temps réel). | Perception de vitesse <br> Le temps passé sur le code semble doubler (bien que la qualité soit meilleure, la quantité brute d'heures est supérieure). |
| Transfert de connaissances <br> Le *pair-programming* est excellent pour le mentorat et l'apprentissage mutuel (partage d'astuces, de raccourcis, de structure, ...). | Fatigue et frustration <br> Peut être épuisant s'il n'y a pas d'alternance ou si les membres de l'équipe ont un niveau de compétence ou de motivation inégal. |
| Meilleur design <br> Le *pair-programming* garantit que les choix de conception sont débattus avant d'être implémentés. | Conflits de personnalité <br> Nécessite des compétences en communication et en collaboration pour éviter les disputes sur la *bonne* manière de coder ou d'approcher le projet. |
| Engagement accru <br> Difficulté à être distrait ou à perdre le fil, car l'autre personne est là pour vous ramener à la tâche. | Gestion du temps <br> Si une personne domine, l'autre peut devenir passive, ce qui annule l'avantage de l'approche. |

## 3. Pièges à éviter dans un contexte académique

Pour garantir le succès dans un contexte d'apprentissage :

| Piège à éviter | Stratégie corrective |
| :--- | :--- |
| Domination <br> souvent par l'étudiant le plus expérimenté qui se met au poste de conducteur, y reste et fait tous les rôles | Forcer l'alternance <br> Vous devez vous discipliner et exiger des changements de rôle fréquents (minuterie). Il faut comprendre que c'est une excellente opportunité pour apprendre à expliquer, discuter, échanger, socialiser, ... |
| Passivité du navigateur <br> "*Il n'y a rien à faire*" | Rôle actif <br> Exiger que le navigateur entre en production dans certaines périodes de travail où le conducteur est occupé (rédaction de tests, de documentations, de *refactoring*, ...). |
| Silence <br> travail en solitaire car l'autre ne participe pas | Règle de communication <br> Il est essentiel que le navigateur verbalise ses réflexions et ses suggestions tout au long du processus. La participation active demande un effort soutenu qui est parfois plus difficile du côté navigateur que conducteur. |
| Problème persistant <br> lors de conflit, certaines solutions restent difficiles à trouver ou à mettre de l'avant | Adresser le problème <br> Insister sur le fait de régler des problèmes de bonne façon : on ne laisse pas traîner un problème, on ne le règle pas partiellement, on accepte de faire des compromis, on écoute l'autre et on tente de verbaliser nos opinions le mieux possible. En fait, on règle ses problèmes en adultes professionnels! |
| Illusion du rôle lié au conducteur <br> "*le conducteur a le rôle le plus important, en tant que navigateur je ne suis là qu'à titre de soutien*" | Clarifier les rôles <br> En fait, le rôle du navigateur est le plus important et le plus difficile. Évidemment, le conducteur produit le code, mais c'est le navigateur qui guide : avancement cohérent, qualité du code et de la structure, dynamique d'équipe, communication et coordination globales, prises de notes diverses, etc. |

## 4. Adaptation à une équipe de 3 individus

Lorsque le groupe est composé de trois étudiants, il est possible d'adapter la méthode du *pair-programming* de deux façons distinctes :
- ajout d'un troisième rôle
- développement latéral ponctuel

Ces deux approches ne sont pas exclusives, au contraire, elles peuvent être combinées pour tirer parti des avantages de chacune selon les besoins du projet et la dynamique de l'équipe.

### Ajout d'un troisième rôle

| Rôle | Description | Objectif |
| :--- | :--- | :--- |
| **L'éclaireur** <br> ou *scout* | Il observe le travail du conducteur et du navigateur, prend des notes, identifie les problèmes potentiels, analyse l'évolution du projet en fonction des objectifs et propose des améliorations dès que nécessaire. Il peut aussi prendre un peu de recul et s'assurer que la trajectoire en cours est cohérente avec les objectifs globaux en s'assurant que l'architecture du projet est solide. | Assurer la qualité globale du travail et fournir un retour constructif. |

Son rôle est loin d'être passif ; l'éclaireur doit constamment analyser, anticiper et proposer des améliorations pour garantir la qualité et la cohérence du projet. Il peut aussi faire la mise à jour constante des documents de conception et de suivi. Souvent, il prend un peu de recul sur une tâche spécifique pour en avoir une vue d'ensemble et identifier des opportunités d'amélioration.

### Développement latéral ponctuel

Le développement latéral ponctuel consiste à faire intervenir le troisième étudiant de manière temporaire et ciblée sur certaines tâches spécifiques lorsque ces dernières peuvent être réalisées en parallèle sans impact sur le travail principal. Cela peut inclure :
- production d'une petite section de code utilitaire, facile à réaliser et à tester;
- revue de code rapide;
- rédaction documentaire;
- assistance sur des problèmes complexes;
- rédaction et réalisation de tests.

Cette approche permet de bénéficier de l'expertise supplémentaire du troisième étudiant tout en maintenant la dynamique principale du binôme conducteur-navigateur.

### Priorité à l'alternance des rôles

Avec des équipes de trois individus, l'alternance des rôles **doit** être réalisée par **tous** les membres. Cet aspect est crucial afin que chacun puisse expérimenter les différents rôles et contribuer de manière équilibrée au projet.

Exceptionnellement, l'étudiant ayant le rôle d'éclaireur peut être dispensé de l'alternance des rôles pour se concentrer sur la tâche en cours de production. Cette dérogation doit être décidée en accord avec les autres membres de l'équipe et rester une exception non renouvelable lors de la prochaine permutation des rôles.

## 5. Considérations supplémentaires dans le contexte académique

Si chacun des étudiants développe en silo des aspects spécifiques du projet, chacun développe des compétences spécifiques au domaine qu'il couvre. Toutefois, dans les examens, les questions touchent tous les aspects du projet.

Par exemple, un étudiant ayant focalisé ses efforts exclusivement sur `NumPy` sera pénalisé pour les questions de `Qt` et vice versa.

Le travail en binôme permet de compenser cette limitation en favorisant le partage des connaissances et la collaboration entre les étudiants. 

## Bilan

La programmation en binôme est bien plus qu'une technique de codage ; c'est un outil d'**apprentissage collaboratif intensif** qui renforce les compétences de communication, de révision et de conception de logiciels.

Lorsqu'elle est bien réalisée, les gains sont significatifs et non discutables. Cette technique transforme la manière dont les étudiants abordent le développement logiciel et les prépare mieux pour le travail dans le monde professionnel.

[↩️](#home)
