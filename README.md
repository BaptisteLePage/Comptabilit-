# Comptes

Application de suivi budgétaire mensuel : interface HTML, moteur Python, aucune
dépendance à installer. Elle reprend la logique du tableau Excel d'origine
(dépenses fixes et variables, salaires, aides, budget courses, compte d'heures
de garde) en la rendant utilisable au quotidien.

## Lancer l'application

```bash
python3 app.py
```

Le navigateur s'ouvre sur `http://127.0.0.1:8000`. C'est tout : pas de `pip
install`, pas de compte, pas de connexion internet. Le serveur n'écoute que sur
votre machine et les données restent dans `donnees/comptes.db`.

Options utiles :

```bash
python3 app.py --port 8080          # changer de port
python3 app.py --sans-navigateur    # ne pas ouvrir le navigateur
python3 app.py --sans-exemple       # démarrer sur un mois vide
python3 app.py --base ~/comptes.db  # ranger les données ailleurs
```

Au tout premier démarrage, un mois est créé et pré-rempli avec les données du
tableau Excel, pour ne pas partir d'une page blanche.

## Ce que l'on peut faire

**Ajouter ou retirer une ligne** — un bouton « + Ligne » dans chaque catégorie,
une croix en bout de ligne pour supprimer, et un « Annuler » qui reste
disponible quelques secondes après une suppression. Tout s'enregistre tout seul
dès qu'on quitte un champ : il n'y a pas de bouton « Sauvegarder ».

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
Excel : séparateur `;`, virgule décimale) ou une sauvegarde JSON complète,
restaurable depuis le même menu.

Le thème suit celui du système et peut être forcé en clair ou sombre. Les
montants s'écrivent avec la virgule française (`19,99`). La touche `Entrée`
valide une saisie, `Échap` l'annule.

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

## Organisation du code

```
app.py                 point d'entrée : options, base de données, serveur
comptes/modele.py      tous les calculs, sans base ni réseau (donc testables)
comptes/base.py        schéma SQLite et accès aux données
comptes/serveur.py     routes de l'API JSON, export CSV, service des fichiers
comptes/exemple.py     données de départ reprises du tableau
web/                   interface : index.html, style.css, app.js
tests/                 tests unitaires
```

Le principe : toute modification part au serveur, qui renvoie le mois entier
recalculé. Les totaux affichés ne peuvent donc jamais s'écarter de ceux
enregistrés.

## Tests

```bash
python3 -m unittest discover -s tests
```

## Sauvegarde

Tout tient dans `donnees/comptes.db`. Copier ce fichier suffit à tout sauvegarder.
Le menu `⋯` permet aussi d'exporter un JSON lisible et de le réimporter.
