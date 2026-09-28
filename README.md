# Comptes

Suivi budgétaire mensuel : **un seul fichier, `comptes.html`**.

Double-cliquez dessus, il s'ouvre dans votre navigateur. Rien à installer, pas
de compte, pas de connexion internet.

## L'idée de l'application

Une question, une page : **qu'est-ce qu'il me reste ?**

Tout le budget du mois tient sur la page d'accueil :

1. **Le bilan**, en haut. Le grand chiffre est votre reste à vivre, et le calcul
   est écrit juste à côté : `Reçu − Payé = Reste`. La barre entière vaut vos
   revenus reçus ; ce qui est peint est parti (bleu : charges fixes, orange :
   dépenses variables, avec leur part en %), **ce qui reste vide est ce dont
   vous disposez encore**. Dessous, une phrase compare au reste que vous aviez
   prévu et dit d'où vient l'écart (revenus pas encore reçus, dépenses pas
   encore payées…).
2. **Ce qui rentre** : salaires et aides.
3. **Ce qui sort** : vos dépenses, rangées par catégorie. Chaque catégorie
   annonce son total et la part de vos revenus qu'elle absorbe.
4. **Les modules** Courses et Heures gardées, résumés en bas de page.

Quand vous descendez dans la page, une bande rappelle en permanence le reste
à vivre sous la navigation. Elle reste aussi affichée sur les pages Courses et
Heures, pour voir l'effet d'un achat sur votre reste.

## Ouvrir et fermer les catégories

À l'ouverture, toutes les catégories sont **fermées** : on voit d'un coup d'œil
le total de chacune. Un clic sur une catégorie l'ouvre ou la referme ; « Tout
ouvrir » / « Tout fermer » agit sur tout le bloc. L'application se souvient de
ce que vous avez laissé ouvert.

## Saisir et modifier

- **Ce qui ressemble à un champ se modifie ; le reste est calculé.** Les
  montants s'écrivent avec la virgule (`19,99`), le point des milliers est
  accepté (`1.234,56`).
- **Les chiffres suivent la frappe** : le bilan, les totaux et l'écart se
  recalculent pendant que vous tapez, sans attendre de quitter le champ. Un
  chiffre qui vient de changer s'illumine un instant, pour qu'on voie l'effet
  de sa saisie.
- `Tab` passe au champ suivant, `Entrée` valide, `Échap` annule la saisie en
  cours. Tout s'enregistre seul.
- **Ajouter** : « + Dépense » ou « + Revenu » ouvre un petit formulaire
  (libellé, catégorie, prévu, payé). Au bas de chaque catégorie, « + Ajouter
  une dépense dans … » crée directement une ligne vide à remplir.
- **Le bouton `⋯`** d'une ligne donne accès à la catégorie, la nature, la
  note, le module qui la calcule, et à la suppression (avec « Annuler »
  quelques secondes).
- **La pastille de couleur** devant une dépense dit si c'est une charge fixe
  (bleu) ou variable (orange). Un clic bascule.

### Mettre une ligne en pause

L'interrupteur en début de ligne la **sort complètement des totaux** — son
prévu comme son payé. Désactiver un abonnement déjà payé fait donc remonter
le reste à vivre d'autant, immédiatement. La ligne reste visible, barrée, avec
le badge « En pause », et son écart indique « hors total ». Cela remplace les
colonnes « Actif / Ref » du tableau d'origine.

### Lire l'écart

- Pour une **dépense** : `prévu − payé`. En vert, la marge qu'il reste (ou ce
  qui n'est pas encore payé) ; en rouge, un dépassement.
- Pour un **revenu** : `reçu − prévu`. En vert, reçu en plus ; en rouge, reçu
  en moins.

## Les deux modules, et leur lien avec le budget

Ils sont indépendants, mais branchés sur le budget :

| Module | Ce qu'il pilote dans le budget |
|---|---|
| **Courses** | Le budget confié aux courses **est** votre dépense « Courses » : il est compté en entier dans le budget du mois (prévu = payé), quels que soient vos achats. Le modifier dans le module le modifie dans le budget, et inversement. Les achats ne font que consommer l'enveloppe, dans le module ; l'écart de la ligne indique ce qu'il reste à dépenser en courses. |
| **Heures gardées** | Le salaire net calculé devient le montant reçu de votre revenu « Caracole ». |

Une ligne pilotée par un module n'affiche pas un champ mais un montant
encadré en pointillés avec un jeton `↗ Courses` ou `↗ Heures` : il se calcule
tout seul, et un clic vous emmène au module. Pour délier une ligne, ouvrez son
`⋯` et choisissez « Calculé par : personne ».

Le module Heures ne prend la main qu'une fois rempli : tant qu'aucun horaire
n'est saisi, le montant écrit à la main dans le budget est conservé. Ouvrir
l'application n'efface donc jamais un montant sans que vous l'ayez demandé.

## Plusieurs mois

Les flèches `‹ ›` passent d'un mois à l'autre. Créer un mois recopie les lignes
récurrentes du mois affiché (libellés, montants prévus, mises en pause) en
remettant les montants réels à zéro : le nouveau mois démarre pré-rempli mais
vierge. Dès que vous avez deux mois, la page Graphiques trace l'évolution.

## Sécurité des données

Vos comptes sont protégés à trois niveaux.

1. **Dans le navigateur, automatiquement.** Chaque modification est
   enregistrée puis relue pour vérifier qu'elle a bien été écrite. Si
   l'application est ouverte dans deux onglets, ils se synchronisent au lieu de
   s'écraser ; si les deux écrivent au même instant, aucune saisie n'est
   perdue (l'une est gardée dans les versions précédentes, et vous êtes
   prévenu). Si les données du navigateur sont un jour illisibles, elles ne
   sont jamais écrasées : une copie est mise de côté et la dernière version
   saine est rouverte.
2. **Les versions précédentes.** Une copie par heure d'activité, et une avant
   chaque opération délicate (suppression de catégorie ou de mois,
   restauration…). Les 30 dernières sont listées dans Paramètres, et chacune
   peut être restaurée ou téléchargée. Les opérations délicates proposent
   aussi un « Annuler » immédiat.
3. **Les copies de sauvegarde.** Un clic (pastille `✓ Enregistré`, bandeau
   de rappel, menu `⋯` ou Paramètres) télécharge un fichier **daté**, par
   exemple `comptes-sauvegarde-2026-09-28-18h30.html`, qui contient
   l'application **et toutes vos données**. C'est un fichier nouveau à chaque
   fois : **il n'y a jamais rien à remplacer**. Ouvert sur n'importe quel
   ordinateur ou navigateur, il retrouve vos comptes. S'il est plus récent que
   ce que le navigateur connaît, c'est lui qui l'emporte, et l'ancienne version
   du navigateur est gardée dans l'historique.

**Il n'y a rien à enregistrer à la main.** Vous pouvez fermer l'onglet ou
éteindre l'ordinateur à tout moment : en rouvrant `comptes.html`, tout est là.
`Ctrl+S` le confirme simplement, sans rien télécharger.

La pastille en haut à droite indique **✓ Enregistré**. Elle devient
**✓ Enregistré · copie conseillée** (avec un bandeau de rappel) quand la
dernière copie de sauvegarde date de plus d'une semaine et que vos comptes ont
changé depuis (délai réglable), et **⚠ Non enregistré** si le navigateur
refusait d'enregistrer ; dans ce cas seulement, fermer l'onglet demande
confirmation.

### Avec Firefox

Par sécurité, Firefox ne permet à aucune page web d'écrire dans un fichier de
votre ordinateur. L'application enregistre donc vos comptes **dans Firefox**,
et les copies de sauvegarde sont des téléchargements.

1. Ouvrez toujours le même `comptes.html` (un marque-page est idéal). Vos
   comptes sont liés à ce fichier à cet emplacement : ne le déplacez pas et ne
   le renommez pas. Si cela arrive, ouvrez votre dernière copie de sauvegarde
   (menu `⋯` › « Ouvrir une sauvegarde… », ou double-clic sur la copie).
2. Pour que les copies se rangent seules, sans question : *Paramètres ›
   Général › Fichiers et applications › Téléchargements* › « Enregistrer les
   fichiers dans » un dossier de votre choix (par exemple *Sauvegardes
   comptes*, éventuellement dans votre Drive), et décochez « Toujours vous
   demander où enregistrer les fichiers ».
3. Attention : effacer l'historique de Firefox avec la case « Cookies et
   données de sites », ou activer « Supprimer les cookies et les données des
   sites à la fermeture de Firefox », efface aussi les comptes enregistrés
   dans Firefox. Évitez-le, ou téléchargez une copie juste avant.

Les anciennes copies peuvent être supprimées quand vous voulez ; gardez au
moins les plus récentes.

## Catégories

Dépenses et revenus sont rangés par catégories **que vous gérez vous-même**.
Elles sont communes à tous les mois.

- **Créer** : « + Catégorie » en haut de chaque bloc. Une catégorie peut rester
  vide.
- **Renommer, déplacer, supprimer** : ouvrez la catégorie ; ses commandes sont
  en bas (✎ Renommer, ↑, ↓, Supprimer la catégorie). Tout se fait aussi depuis
  la page Paramètres.
- **Renommer** agit sur tous les mois. Donner le nom d'une catégorie existante
  **fusionne** les deux (une confirmation est demandée).
- **Supprimer** propose de déplacer ses lignes vers une autre catégorie (choix
  par défaut) ou de les supprimer aussi. Dans les deux cas, « Annuler » est
  possible juste après.
- Taper un nom nouveau dans la case Catégorie d'une ligne crée la catégorie.

## Paramètres

La page ⚙ Paramètres regroupe tout ce qui se règle :

- la sauvegarde (copies de sauvegarde, ouvrir une sauvegarde, versions
  précédentes) ;
- les catégories de dépenses (avec la nature proposée pour leurs nouvelles
  lignes) et de revenus ;
- les modules : activer ou désactiver Courses et Heures gardées, et les
  renommer ;
- les valeurs de départ des nouveaux mois (budget et nombre de semaines de
  courses, taux horaire, cotisations) et les suggestions de courses ;
- le thème, le seuil d'alerte des jauges, la fréquence du rappel de copie
  de sauvegarde, et l'avertissement à la fermeture.

Les paramètres sont enregistrés avec les données : ils voyagent dans les copies
de sauvegarde.

## Ce que devient le tableau Excel

| Dans le tableau | Dans l'application |
|---|---|
| Colonnes `Actif` / `Ref` | Un interrupteur par ligne : en pause, la ligne sort des totaux |
| Colonne `Surplus` (`Estimé − Réel`) | Colonne « Écart », recalculée en direct |
| Blocs `FIXES` / `VARIABLES` | La pastille de couleur, et les deux couleurs de la barre du bilan |
| `RESTANT = Revenus − Dépenses` | Le « Reste à vivre », en haut de la page |
| `DEPENSE = Assistante maternelle − CAF` | Liens `garde` et `caf` sur les lignes concernées |
| Grille `COMPTE HEURE CARACOLE` | Module « Heures gardées » |
| Bloc `COURSES` (semaines, budget, restant) | Module « Courses » |
| Deux colonnes `Réel` côte à côte | Un mois = un jeu de montants ; on compare en changeant de mois |

Deux écarts assumés, à corriger d'un clic si besoin :

- Les lignes du tableau qui n'avaient qu'un montant réel sans montant prévu
  alors qu'elles figuraient en « FIXES » (Creil, RLP) ont reçu un montant prévu
  égal au réel.
- Les lignes laissées vides dans le tableau (Voiture, Taxe foncière, Repas
  différé, De côté…) n'ont pas été reprises.

## Vérifier que les calculs sont justes

Ouvrez `comptes.html#autotest` (ajoutez `#autotest` à la fin de l'adresse dans
la barre du navigateur). Une page liste 103 vérifications : lecture des montants
(virgule, point des milliers, négatifs), durées de garde, salaire brut/net,
budget courses, totaux, lignes et revenus en pause, liaison entre le budget et
les modules, duplication d'un mois, opérations sur les catégories, reprise des
anciennes données, fidélité des copies de sauvegarde et rappel de copie. Cette vérification
n'écrit jamais dans vos données. Un lien ramène ensuite à l'application.

## Modifier l'application

Tout tient dans `comptes.html` : le style dans la balise `<style>`, le code
dans la balise `<script>`, découpé en sept sections commentées — réglages,
calculs, stockage, modifications, affichage, interactions, démarrage. Les
calculs (section 2) ne touchent ni à l'écran ni au stockage, ce qui les rend
faciles à relire et à tester.

L'affichage a deux niveaux : la *structure* (lignes, champs), reconstruite
seulement quand la forme de la page change, et les *zones calculées*
(bilan, totaux, écarts), recalculées à chaque frappe sans toucher aux champs.
C'est ce qui permet aux chiffres de suivre la saisie sans que le curseur saute
ni qu'un clic se perde.

## Historique

Une première version fonctionnait avec un serveur Python (`python3 app.py`),
et une deuxième répartissait le budget sur cinq onglets. Toutes deux restent
consultables dans l'historique du dépôt.
