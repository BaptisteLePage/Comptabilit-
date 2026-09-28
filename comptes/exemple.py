"""Données de départ, reprises du tableau Excel d'origine.

Utilisé au premier démarrage pour que l'application ne s'ouvre pas sur une page
blanche. Les colonnes « Actif / Ref » du tableau deviennent ici un simple
interrupteur : un abonnement en pause garde son prix mais ne compte plus dans
les totaux.
"""

from __future__ import annotations

from . import base

# (nature, catégorie, libellé, estimé, réel, actif, note, lien)
DEPENSES = [
    ("fixe", "Santé", "MNH", 70, 70, 1, "", ""),
    ("fixe", "Transports", "Navigo", 34, 34, 1, "", ""),
    ("fixe", "Transports", "Essence", 80, 0, 1, "", ""),
    ("fixe", "Quotidien", "Courses", 400, 400, 1,
     "Suivi détaillé dans l'onglet Courses", "courses"),
    ("fixe", "Abonnements", "Google One Plus", 10, 10, 1, "", ""),
    ("fixe", "Abonnements", "Orange Mobile", 40, 40, 1, "", ""),
    ("fixe", "Abonnements", "Spotify", 22, 22, 1, "", ""),
    ("fixe", "Abonnements", "Piano", 60, 60, 1, "Différable", ""),
    ("fixe", "Banque", "Cotisation eurocompte", 10, 10, 1, "", ""),
    ("fixe", "Garde", "Assistante maternelle", 0, 0, 1,
     "Coût net = ce montant moins la CAF", "garde"),

    ("variable", "Streaming", "Twitch", 10, 10, 1, "", ""),
    ("variable", "Streaming", "Hors-Série", 3, 3, 1, "", ""),
    ("variable", "Streaming", "Paramount+ (Prime Video)", 0, 0, 0, "", ""),
    ("variable", "Streaming", "HB+ MAX (Prime Video)", 0, 0, 0, "", ""),
    ("variable", "Streaming", "Disney+", 0, 0, 0, "", ""),
    ("variable", "Streaming", "Medici", 0, 0, 0, "", ""),
    ("variable", "Streaming", "Paris Opera Play", 10, 0, 0, "", ""),
    ("variable", "Streaming", "Met on Demand", 15, 0, 1, "", ""),
    ("variable", "Presse", "Télérama", 3, 0, 0, "", ""),
    ("variable", "Presse", "La Lettre du Musicien", 0, 0, 0, "", ""),
    ("variable", "Abonnements", "FlightRadar24", 0, 0, 0, "", ""),
    ("variable", "Abonnements", "Transkribus", 19.99, 0, 1, "", ""),
    ("variable", "Abonnements", "Claude Pro", 21.60, 0, 0, "", ""),
    ("variable", "Abonnements", "Claude Max", 90, 90, 1, "", ""),
    ("variable", "Abonnements", "PlayStation Plus", 16, 15, 1, "", ""),
    ("variable", "Abonnements", "GitHub", 4, 4, 1, "", ""),
    ("variable", "Abonnements", "DeepL Pro", 30, 0, 1, "", ""),
    ("variable", "Abonnements", "ChatGPT", 21.99, 0, 0, "", ""),
    ("variable", "Abonnements", "Amazon Prime", 7, 0, 0, "", ""),
    ("variable", "Paiement en 4 fois", "Aspirateur", 0, 0, 1, "", ""),
    ("variable", "Paiement en 4 fois", "Chemises", 24.75, 24.75, 1, "", ""),
    ("variable", "Paiement en 4 fois", "AirSense 11", 249, 249, 1, "", ""),
    ("variable", "Paiement en 4 fois", "PlayStation", 150, 150, 1, "", ""),
    ("variable", "Paiement en 4 fois", "TV", 225, 225, 1, "", ""),
    ("variable", "Autres", "Cotisations", 91, 91, 1, "", ""),
    ("variable", "Autres", "Piano différé", 60, 60, 1, "", ""),
    ("variable", "Autres", "Julie", 30, 30, 1, "", ""),
    ("variable", "Autres", "Restaurant Paris", 35, 35, 1, "", ""),
    ("variable", "Autres", "Jeux", 70, 70, 1, "", ""),
]

# (type, nature, catégorie, libellé, estimé, réel, lien)
REVENUS = [
    ("salaire", "fixe", "Salaire", "Evry", 1781.34, 1174.88, ""),
    ("salaire", "fixe", "Salaire", "Creil", 394.40, 394.40, ""),
    ("salaire", "variable", "Salaire", "Caracole", 0, 0, "heures"),
    ("salaire", "variable", "Salaire", "Commande", 0, 0, ""),
    ("salaire", "variable", "Salaire", "Virement 1", 0, 0, ""),
    ("salaire", "variable", "Salaire", "Virement 2", 0, 0, ""),
    ("aide", "fixe", "Aide", "RLP", 360, 360, ""),
    ("aide", "variable", "Aide", "CAF", 0, 0, "caf"),
]

# Créneaux relevés dans le tableau : (semaine, jour, matin, après-midi)
CRENEAUX = [
    (1, 0, "10:04", "11:30", "13:36", "17:00"),
    (1, 3, "09:30", "11:30", "12:30", "15:00"),
    (2, 0, "10:00", "11:30", "12:44", "13:28"),
    (3, 3, "09:30", "12:16", "12:48", "13:19"),
]


def remplit(cnx, libelle: str | None = None) -> dict:
    """Crée un mois pré-rempli avec les données du tableau d'origine."""
    mois = base.cree_mois(cnx, libelle or base.mois_courant())
    mois_id = mois["id"]
    if base.liste_lignes(cnx, mois_id):
        return mois

    rang = 0
    for nature, categorie, libelle_ligne, estime, reel, actif, note, lien in DEPENSES:
        rang += 10
        base.cree_ligne(cnx, mois_id, {
            "type": "depense", "nature": nature, "categorie": categorie,
            "libelle": libelle_ligne, "estime": estime, "reel": reel,
            "actif": bool(actif), "note": note, "lien": lien, "rang": rang,
        })
    for type_, nature, categorie, libelle_ligne, estime, reel, lien in REVENUS:
        rang += 10
        base.cree_ligne(cnx, mois_id, {
            "type": type_, "nature": nature, "categorie": categorie,
            "libelle": libelle_ligne, "estime": estime, "reel": reel,
            "lien": lien, "rang": rang,
        })

    for semaine, jour, matin_debut, matin_fin, aprem_debut, aprem_fin in CRENEAUX:
        base.assure_semaine_creneaux(cnx, mois_id, semaine)
        creneau = cnx.execute(
            "SELECT id FROM creneau WHERE mois_id = ? AND semaine = ? AND jour = ?",
            (mois_id, semaine, jour)).fetchone()
        if creneau:
            base.maj_creneau(cnx, creneau["id"], {
                "matin_debut": matin_debut, "matin_fin": matin_fin,
                "aprem_debut": aprem_debut, "aprem_fin": aprem_fin,
            })
    cnx.commit()
    return mois
