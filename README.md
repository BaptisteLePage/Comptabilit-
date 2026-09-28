# Comptes

Suivi budgétaire mensuel : **un seul fichier, `comptes.html`**.

Double-cliquez dessus, il s'ouvre dans votre navigateur. Rien à installer, pas
de compte, pas de connexion internet.

## L'idée de l'application

Une question, une page : **qu'est-ce qu'il me reste ?**

Tout le budget du mois tient sur la page d'accueil, dans cet ordre :

1. **Le bilan**, en haut, toujours visible même en faisant défiler. La barre
   entière vaut vos revenus du mois. Ce qui est peint est parti — bleu pour les
   charges fixes, orange pour les dépenses variables — et **ce qui reste vide
   est ce dont vous disposez encore**. C'est là que se lit, d'un coup d'œil,
   l'incidence de vos dépenses sur vos revenus.
2. **Ce qui rentre** : salaires et aides.
3. **Ce qui sort** : vos dépenses, regroupées par catégorie. Chaque catégorie
   se déplie d'un clic et indique le pourcentage de vos revenus qu'elle absorbe.
4. **Les modules**, résumés en bas de page.

Les **graphiques** ont leur propre page, ainsi que les deux modules
complémentaires, **Courses** et **Heures gardées**, volontairement mis à part
du budget.

## Les deux modules, et leur lien avec le budget

Ils sont indépendants, mais branchés sur le budget :

| Module | Ce qu'il pilote dans le budget |
|---|---|
| **Courses** | Le budget confié aux courses **est** le montant prévu de votre ligne de dépense « Courses ». En retour, le total de vos achats devient le montant réel de cette ligne. |
| **Heures gardées** | Le salaire net calculé devient le montant réel de votre revenu « Caracole ». |

Sur la page Budget, ces deux lignes portent un jeton `↗ Courses` ou
`↗ Heures` : leur montant réel n'est pas saisissable, il vient du module, et
le jeton vous y emmène. Pour délier une ligne, ouvrez son `⋯` et remettez
« Relié à » sur `—`.

Un module ne prend la main qu'une fois rempli : tant qu'aucun achat n'est
saisi, le montant que vous aviez écrit à la main est conservé. Ouvrir
l'application n'efface donc jamais un montant que vous n'avez pas demandé
d'effacer.

## Manipuler ses lignes

- **Ajouter** : « + Dépense » en haut du bloc, ou « + Ajouter dans … » au bas
  d'une catégorie (la catégorie est alors déjà remplie).
- **Modifier** : tapez directement dans les cases Prévu et Réel. Tout
  s'enregistre tout seul ; il n'y a pas de bouton « Sauvegarder ».
- **Le reste** (catégorie, note, nature, module relié, suppression) est derrière
  le bouton `⋯` de chaque ligne. Après une suppression, un « Annuler » reste
  disponible quelques secondes.
- **La pastille de couleur** à gauche du libellé dit si la dépense est une
  charge fixe (bleu) ou variable (orange) — les mêmes couleurs que la barre du
  bilan. Un clic bascule de l'une à l'autre.
- **L'interrupteur** met une ligne en pause : elle garde son montant affiché
  mais sort des totaux. C'est l'équivalent des colonnes « Actif / Ref » du
  tableau d'origine.

Les montants s'écrivent avec la virgule française (`19,99`). `Entrée` valide
une saisie, `Échap` l'annule. Les horaires se tapent comme on veut : `9h30`,
`9:30` ou `9`. L'affichage s'adapte au téléphone.

## Plusieurs mois

Les flèches `‹ ›` passent d'un mois à l'autre. Créer un mois recopie les lignes
récurrentes du mois affiché (libellés, montants prévus, mises en pause) en
remettant les montants réels à zéro : le nouveau mois démarre pré-rempli mais
vierge. Dès que vous avez deux mois, la page Graphiques trace l'évolution.

## Où sont les données

Elles sont enregistrées **dans votre navigateur**, sur votre ordinateur, et ne
partent nulle part.

- Changer de navigateur ou d'ordinateur ne les transporte pas : menu `⋯` →
  **Sauvegarder tout (JSON)**, puis **Restaurer une sauvegarde** de l'autre côté.
- Effacer les données de navigation en cochant « cookies et données de sites »
  les efface aussi. Une sauvegarde JSON de temps en temps met à l'abri.
- En navigation privée, rien n'est conservé. L'application le signale par un
  bandeau rouge si elle n'arrive pas à enregistrer.

Le menu `⋯` exporte aussi le mois en CSV, directement lisible par Excel
(séparateur `;`, virgule décimale).

## Ce que devient le tableau Excel

| Dans le tableau | Dans l'application |
|---|---|
| Colonnes `Actif` / `Ref` | Un interrupteur par ligne + un seul montant |
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
la barre du navigateur). Une page liste 50 vérifications : lecture des montants
à la virgule, durées de garde, salaire brut/net, budget courses, totaux, lignes
en pause, liaison entre le budget et les modules, duplication d'un mois,
sauvegarde et restauration. Un lien ramène ensuite à l'application.

## Modifier l'application

Tout tient dans `comptes.html` : le style dans la balise `<style>`, le code
dans la balise `<script>`, découpé en sept sections commentées — réglages,
calculs, stockage, modifications, affichage, interactions, démarrage. Les
calculs (section 2) ne touchent ni à l'écran ni au stockage, ce qui les rend
faciles à relire et à tester.

## Historique

Une première version fonctionnait avec un serveur Python (`python3 app.py`),
et une deuxième répartissait le budget sur cinq onglets. Toutes deux restent
consultables dans l'historique du dépôt.
