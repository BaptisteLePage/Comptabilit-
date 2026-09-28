# Comptes

Suivi budgétaire mensuel : **un seul fichier, `comptes.html`**.

## Utilisation

Double-cliquez sur `comptes.html`. Il s'ouvre dans votre navigateur. C'est tout :
rien à installer, pas de compte, pas de connexion internet.

À la première ouverture, un mois est créé et pré-rempli avec les données du
tableau Excel d'origine, pour ne pas partir d'une page blanche.

**Conseil** : rangez `comptes.html` quelque part de stable (Documents, par
exemple) et mettez un raccourci sur le bureau. Vous pouvez aussi le garder
ouvert dans un onglet et le mettre en favori.

## Où sont les données

Elles sont enregistrées **dans votre navigateur**, sur votre ordinateur, et ne
partent nulle part. Chaque modification est enregistrée toute seule : il n'y a
pas de bouton « Sauvegarder ».

Trois conséquences à connaître :

- Changer de navigateur (Chrome → Firefox) ou d'ordinateur ne transporte pas
  les données : passez par le menu `⋯` → **Sauvegarder tout (JSON)**, puis
  **Restaurer une sauvegarde** de l'autre côté.
- Effacer les données de navigation en cochant « cookies et données de sites »
  efface aussi vos comptes. Une sauvegarde JSON de temps en temps met à l'abri.
- En navigation privée, rien n'est conservé à la fermeture. L'application vous
  prévient par un bandeau rouge si elle n'arrive pas à enregistrer.

## Ce que l'on peut faire

**Ajouter ou retirer une ligne** — un bouton « + Ligne » dans chaque catégorie,
une croix en bout de ligne pour supprimer, et un « Annuler » qui reste
disponible quelques secondes après une suppression.

**Mettre un abonnement en pause** — l'interrupteur en début de ligne remplace le
couple de colonnes « Actif / Ref » du tableau. Une ligne en pause garde son
montant affiché mais ne compte plus dans les totaux, et le tableau de bord
récapitule ce que ces pauses font économiser chaque mois.

**Suivre plusieurs mois** — les flèches `‹ ›` passent d'un mois à l'autre.
Créer un mois recopie les lignes récurrentes du mois affiché (libellés, montants
prévus, mises en pause) en remettant les montants réels à zéro : le nouveau mois
démarre pré-rempli mais vierge.

**Budget courses** — une carte par semaine, avec son budget, sa jauge et ses
achats. Les suggestions d'ajout rapide reprennent la liste d'articles du
tableau. Le bouton « Reporter le total dans les dépenses » recopie le total du
mois dans la ligne de dépense reliée.

**Heures gardées** — une grille par semaine (matin, après-midi), la durée se
calcule à chaque saisie. Les horaires se tapent comme on veut : `9h30`, `9:30`
ou `9`. En bas, le salaire brut, les cotisations et le net, avec le même calcul
que le tableau (`heures × taux`, puis retrait du pourcentage de cotisations).
Le bouton « Reporter le net dans les revenus » recopie le net dans la ligne de
salaire reliée.

**Exporter** — le menu `⋯` produit un CSV du mois (ouvrable directement dans
Excel : séparateur `;`, virgule décimale) ou une sauvegarde JSON complète.

Le thème suit celui du système et peut être forcé en clair ou sombre. Les
montants s'écrivent avec la virgule française (`19,99`). La touche `Entrée`
valide une saisie, `Échap` l'annule. L'affichage s'adapte au téléphone.

## Comment le tableau Excel a été traduit

| Dans le tableau | Dans l'application |
|---|---|
| Colonnes `Actif` / `Ref` | Un interrupteur par ligne + un seul montant |
| Colonne `Surplus` (`Estimé − Réel`) | Colonne « Écart », recalculée en direct |
| Deux colonnes `Réel` côte à côte | Un mois = un jeu de montants ; on compare en changeant de mois |
| Blocs `FIXES` / `VARIABLES` | Champ « Nature » sur chaque ligne + filtre en haut |
| `DEPENSE = Assistante maternelle − CAF` | Tuile « Coût net de la garde », via les liens `garde` et `caf` |
| `RESTANT = Revenus − Dépenses` | Le chiffre en haut du tableau de bord |
| Grille `COMPTE HEURE CARACOLE` | Onglet « Heures gardées » |
| Bloc `COURSES` (semaines, budget, restant) | Onglet « Courses » |

Deux écarts assumés, à corriger d'un clic si besoin :

- Les lignes du tableau qui n'avaient qu'un montant réel sans montant prévu
  alors qu'elles figuraient en « FIXES » (Creil, RLP) ont reçu un montant prévu
  égal au réel.
- Les lignes laissées vides dans le tableau (Voiture, Taxe foncière, Repas
  différé, De côté…) n'ont pas été reprises.

## Vérifier que les calculs sont justes

Ouvrez `comptes.html#autotest` (ajoutez `#autotest` à la fin de l'adresse dans
la barre du navigateur). Une page liste 40 vérifications : lecture des montants
à la virgule, durées de garde, salaire brut/net, budget courses, totaux,
lignes en pause, duplication d'un mois, sauvegarde et restauration. Un lien
ramène ensuite à l'application.

## Modifier l'application

Tout tient dans `comptes.html` : le style est dans la balise `<style>`, le code
dans la balise `<script>`, découpé en sept sections commentées (réglages,
calculs, stockage, modifications, affichage, interactions, démarrage). Les
calculs sont regroupés dans la section 2 et ne touchent ni à l'écran ni au
stockage, ce qui les rend faciles à relire et à tester.

## Historique

Une version précédente fonctionnait avec un petit serveur Python
(`python3 app.py`). Elle a été retirée au profit de ce fichier unique, plus
simple à ouvrir. Elle reste disponible dans l'historique du dépôt, au commit
`075749f`.
