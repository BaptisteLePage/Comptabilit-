"""Calculs du budget.

Ce module est volontairement pur : aucune base de données, aucun réseau. Il ne
manipule que des dictionnaires, ce qui le rend simple à tester (voir
``tests/test_modele.py``) et à réutiliser.
"""

from __future__ import annotations

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

TYPES = ("depense", "salaire", "aide")
NATURES = ("fixe", "variable")

# Valeurs par défaut reprises du tableau Excel d'origine.
TAUX_HORAIRE_DEFAUT = 12.02
TAUX_COTISATION_DEFAUT = 21.2


def eur(valeur) -> float:
    """Arrondit un montant au centime."""
    try:
        return round(float(valeur or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def nombre(valeur) -> float:
    """Lit un montant saisi à la française : « 1 234,56 » -> 1234.56."""
    if valeur is None or valeur == "":
        return 0.0
    if isinstance(valeur, (int, float)):
        return eur(valeur)
    texte = str(valeur).strip()
    texte = texte.replace(" ", "").replace(" ", "").replace(" ", "")
    texte = texte.replace("€", "").replace(",", ".")
    if texte in ("", "-", ".", "-."):
        return 0.0
    try:
        return eur(texte)
    except ValueError:
        return 0.0


# --------------------------------------------------------------------------- #
# Heures de garde
# --------------------------------------------------------------------------- #

def minutes_depuis_heure(texte):
    """« 09:30 », « 9h30 » ou « 9 » -> minutes depuis minuit. None si illisible."""
    if texte is None:
        return None
    t = str(texte).strip().lower().replace("h", ":").replace(".", ":")
    if not t:
        return None
    morceaux = t.split(":")
    try:
        heures = int(morceaux[0])
        minutes = int(morceaux[1]) if len(morceaux) > 1 and morceaux[1] != "" else 0
    except ValueError:
        return None
    if not (0 <= heures <= 23 and 0 <= minutes <= 59):
        return None
    return heures * 60 + minutes


def heure_depuis_minutes(minutes) -> str:
    """570 -> « 09:30 »."""
    if minutes is None:
        return ""
    minutes = int(minutes) % (24 * 60)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def duree_plage(debut, fin) -> int:
    """Durée en minutes d'une plage horaire. 0 si incomplète ou incohérente."""
    a = minutes_depuis_heure(debut)
    b = minutes_depuis_heure(fin)
    if a is None or b is None or b <= a:
        return 0
    return b - a


def duree_creneau(creneau) -> int:
    """Durée d'une journée = matin + après-midi, en minutes."""
    return duree_plage(creneau.get("matin_debut"), creneau.get("matin_fin")) + duree_plage(
        creneau.get("aprem_debut"), creneau.get("aprem_fin")
    )


def format_duree(minutes) -> str:
    """891 -> « 14 h 51 »."""
    minutes = int(round(minutes or 0))
    return f"{minutes // 60} h {minutes % 60:02d}"


def recap_heures(creneaux, taux_horaire=TAUX_HORAIRE_DEFAUT,
                 taux_cotisation=TAUX_COTISATION_DEFAUT) -> dict:
    """Total d'heures gardées puis salaire brut / cotisations / net.

    Reprend la formule du tableau : brut = heures x taux, cotisation = brut x
    taux %, net = brut - cotisation.
    """
    par_semaine: dict[int, int] = {}
    total = 0
    for creneau in creneaux:
        duree = duree_creneau(creneau)
        total += duree
        semaine = int(creneau.get("semaine") or 1)
        par_semaine[semaine] = par_semaine.get(semaine, 0) + duree

    heures = total / 60
    brut = eur(heures * float(taux_horaire or 0))
    cotisation = eur(brut * float(taux_cotisation or 0) / 100)
    return {
        "minutes": total,
        "heures": round(heures, 4),
        "duree": format_duree(total),
        "taux_horaire": eur(taux_horaire),
        "taux_cotisation": round(float(taux_cotisation or 0), 2),
        "brut": brut,
        "cotisation": cotisation,
        "net": eur(brut - cotisation),
        "par_semaine": [
            {"semaine": s, "minutes": par_semaine[s], "duree": format_duree(par_semaine[s])}
            for s in sorted(par_semaine)
        ],
    }


# --------------------------------------------------------------------------- #
# Budget courses
# --------------------------------------------------------------------------- #

def recap_courses(semaines, achats, budget_total=0) -> dict:
    """Suivi hebdomadaire des courses : dépensé, restant, répartition par poste."""
    depense_par_semaine: dict[int, float] = {}
    par_poste: dict[str, float] = {}
    total = 0.0

    for achat in achats:
        montant = eur(achat.get("montant"))
        semaine = int(achat.get("semaine") or 1)
        depense_par_semaine[semaine] = eur(depense_par_semaine.get(semaine, 0) + montant)
        poste = (achat.get("poste") or "Autre").strip() or "Autre"
        par_poste[poste] = eur(par_poste.get(poste, 0) + montant)
        total = eur(total + montant)

    lignes = []
    for semaine in semaines:
        numero = int(semaine.get("numero"))
        budget = eur(semaine.get("budget"))
        depense = eur(depense_par_semaine.get(numero, 0))
        lignes.append({
            "numero": numero,
            "budget": budget,
            "depense": depense,
            "restant": eur(budget - depense),
        })

    budget_total = eur(budget_total)
    return {
        "semaines": lignes,
        "budget_total": budget_total,
        "budget_semaines": eur(sum(l["budget"] for l in lignes)),
        "depense": total,
        "restant": eur(budget_total - total),
        "par_poste": [
            {"poste": p, "montant": m}
            for p, m in sorted(par_poste.items(), key=lambda kv: -kv[1])
        ],
    }


# --------------------------------------------------------------------------- #
# Dépenses / revenus
# --------------------------------------------------------------------------- #

def _vide() -> dict:
    return {"estime": 0.0, "reel": 0.0}


def _ajoute(cumul: dict, estime: float, reel: float) -> None:
    cumul["estime"] = eur(cumul["estime"] + estime)
    cumul["reel"] = eur(cumul["reel"] + reel)


def _somme(*cumuls) -> dict:
    total = _vide()
    for cumul in cumuls:
        _ajoute(total, cumul["estime"], cumul["reel"])
    return total


def recap_budget(lignes) -> dict:
    """Totaux du mois.

    Une ligne mise en pause (``actif`` faux) garde son montant estimé affiché
    mais ne compte pas dans les totaux : c'est l'équivalent des colonnes
    « Actif / Ref » du tableau d'origine, ramenées à un simple interrupteur.
    """
    groupes = {
        (t, n): _vide() for t in TYPES for n in NATURES
    }
    par_categorie: dict[str, dict] = {}
    en_pause = []
    garde = _vide()
    caf = _vide()

    for ligne in lignes:
        type_ = ligne.get("type")
        nature = ligne.get("nature")
        if (type_, nature) not in groupes:
            continue
        actif = bool(ligne.get("actif", 1))
        estime_saisi = eur(ligne.get("estime"))
        estime = estime_saisi if actif else 0.0
        reel = eur(ligne.get("reel"))

        _ajoute(groupes[(type_, nature)], estime, reel)

        if not actif and estime_saisi:
            en_pause.append({
                "id": ligne.get("id"),
                "libelle": ligne.get("libelle") or "",
                "categorie": ligne.get("categorie") or "",
                "estime": estime_saisi,
            })

        if type_ == "depense":
            categorie = (ligne.get("categorie") or "Sans catégorie").strip() or "Sans catégorie"
            cumul = par_categorie.setdefault(categorie, {"categorie": categorie, **_vide()})
            _ajoute(cumul, estime, reel)

        lien = (ligne.get("lien") or "").strip()
        if lien == "garde":
            _ajoute(garde, estime, reel)
        elif lien == "caf":
            _ajoute(caf, estime, reel)

    depenses = _somme(groupes[("depense", "fixe")], groupes[("depense", "variable")])
    salaires = _somme(groupes[("salaire", "fixe")], groupes[("salaire", "variable")])
    aides = _somme(groupes[("aide", "fixe")], groupes[("aide", "variable")])
    revenus = _somme(salaires, aides)

    return {
        "depenses": depenses,
        "depenses_fixes": groupes[("depense", "fixe")],
        "depenses_variables": groupes[("depense", "variable")],
        "salaires": salaires,
        "salaires_fixes": groupes[("salaire", "fixe")],
        "salaires_variables": groupes[("salaire", "variable")],
        "aides": aides,
        "aides_fixes": groupes[("aide", "fixe")],
        "aides_variables": groupes[("aide", "variable")],
        "revenus": revenus,
        "restant": {
            "estime": eur(revenus["estime"] - depenses["estime"]),
            "reel": eur(revenus["reel"] - depenses["reel"]),
        },
        # Positif = on a dépensé moins que prévu (le « Surplus » du tableau).
        "surplus": {
            "estime": 0.0,
            "reel": eur(depenses["estime"] - depenses["reel"]),
        },
        "garde": garde,
        "caf": caf,
        "garde_nette": {
            "estime": eur(garde["estime"] - caf["estime"]),
            "reel": eur(garde["reel"] - caf["reel"]),
        },
        "en_pause": sorted(en_pause, key=lambda l: -l["estime"]),
        "economie_en_pause": eur(sum(l["estime"] for l in en_pause)),
        "par_categorie": sorted(
            par_categorie.values(), key=lambda c: (-max(c["reel"], c["estime"]), c["categorie"])
        ),
    }


def recap(mois, lignes, semaines, achats, creneaux) -> dict:
    """Assemble tous les récapitulatifs d'un mois."""
    budget = recap_budget(lignes)
    courses = recap_courses(semaines, achats, mois.get("budget_courses"))
    heures = recap_heures(
        creneaux,
        mois.get("taux_horaire", TAUX_HORAIRE_DEFAUT),
        mois.get("taux_cotisation", TAUX_COTISATION_DEFAUT),
    )
    return {"budget": budget, "courses": courses, "heures": heures}
