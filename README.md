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
| **Courses** | Le budget confié aux courses **est** le montant prévu de votre dépense « Courses ». En retour, le total de vos achats devient son montant payé. |
| **Heures gardées** | Le salaire net calculé devient le montant reçu de votre revenu « Caracole ». |

Une ligne pilotée par un module n'affiche pas un champ mais un montant
encadré en pointillés avec un jeton `↗ Courses` ou `↗ Heures` : il se calcule
tout seul, et un clic vous emmène au module. Pour délier une ligne, ouvrez son
`⋯` et choisissez « Calculé par : personne ».

Un module ne prend la main qu'une fois rempli : tant qu'aucun achat n'est
saisi, le montant écrit à la main dans le budget est conservé. Ouvrir
l'application n'efface donc jamais un montant sans que vous l'ayez demandé.

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
la barre du navigateur). Une page liste 63 vérifications : lecture des montants
(virgule, point des milliers, négatifs), durées de garde, salaire brut/net,
budget courses, totaux, lignes et revenus en pause, liaison entre le budget et
les modules, duplication d'un mois, sauvegarde et restauration. Un lien ramène
ensuite à l'application.

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
