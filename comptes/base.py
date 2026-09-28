"""Stockage SQLite : schéma, accès et opérations de base.

Un seul fichier ``comptes.db`` contient tout. Il est créé au premier
démarrage ; rien d'autre n'est à installer.
"""

from __future__ import annotations

import datetime
import sqlite3
from pathlib import Path

from . import modele

SCHEMA = """
CREATE TABLE IF NOT EXISTS mois (
    id              INTEGER PRIMARY KEY,
    libelle         TEXT    NOT NULL UNIQUE,
    note            TEXT    NOT NULL DEFAULT '',
    taux_horaire    REAL    NOT NULL DEFAULT 12.02,
    taux_cotisation REAL    NOT NULL DEFAULT 21.2,
    budget_courses  REAL    NOT NULL DEFAULT 400,
    cree_le         TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS ligne (
    id        INTEGER PRIMARY KEY,
    mois_id   INTEGER NOT NULL REFERENCES mois(id) ON DELETE CASCADE,
    type      TEXT    NOT NULL CHECK (type IN ('depense', 'salaire', 'aide')),
    nature    TEXT    NOT NULL CHECK (nature IN ('fixe', 'variable')),
    categorie TEXT    NOT NULL DEFAULT '',
    libelle   TEXT    NOT NULL DEFAULT '',
    estime    REAL    NOT NULL DEFAULT 0,
    reel      REAL    NOT NULL DEFAULT 0,
    actif     INTEGER NOT NULL DEFAULT 1,
    note      TEXT    NOT NULL DEFAULT '',
    lien      TEXT    NOT NULL DEFAULT '',
    rang      INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_ligne_mois ON ligne(mois_id);

CREATE TABLE IF NOT EXISTS semaine (
    id      INTEGER PRIMARY KEY,
    mois_id INTEGER NOT NULL REFERENCES mois(id) ON DELETE CASCADE,
    numero  INTEGER NOT NULL,
    budget  REAL    NOT NULL DEFAULT 100,
    UNIQUE (mois_id, numero)
);

CREATE TABLE IF NOT EXISTS achat (
    id      INTEGER PRIMARY KEY,
    mois_id INTEGER NOT NULL REFERENCES mois(id) ON DELETE CASCADE,
    semaine INTEGER NOT NULL DEFAULT 1,
    poste   TEXT    NOT NULL DEFAULT '',
    libelle TEXT    NOT NULL DEFAULT '',
    montant REAL    NOT NULL DEFAULT 0,
    rang    INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_achat_mois ON achat(mois_id);

CREATE TABLE IF NOT EXISTS creneau (
    id          INTEGER PRIMARY KEY,
    mois_id     INTEGER NOT NULL REFERENCES mois(id) ON DELETE CASCADE,
    semaine     INTEGER NOT NULL,
    jour        INTEGER NOT NULL,
    matin_debut TEXT    NOT NULL DEFAULT '',
    matin_fin   TEXT    NOT NULL DEFAULT '',
    aprem_debut TEXT    NOT NULL DEFAULT '',
    aprem_fin   TEXT    NOT NULL DEFAULT '',
    UNIQUE (mois_id, semaine, jour)
);
CREATE INDEX IF NOT EXISTS idx_creneau_mois ON creneau(mois_id);
"""

SEMAINES_PAR_DEFAUT = 4
CHAMPS_LIGNE = ("type", "nature", "categorie", "libelle", "estime", "reel",
                "actif", "note", "lien", "rang")
CHAMPS_ACHAT = ("semaine", "poste", "libelle", "montant", "rang")
CHAMPS_CRENEAU = ("matin_debut", "matin_fin", "aprem_debut", "aprem_fin")


def connexion(chemin: Path | str) -> sqlite3.Connection:
    """Ouvre la base, crée le schéma si besoin."""
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    cnx = sqlite3.connect(str(chemin), check_same_thread=False)
    cnx.row_factory = sqlite3.Row
    cnx.execute("PRAGMA foreign_keys = ON")
    cnx.executescript(SCHEMA)
    cnx.commit()
    return cnx


def _dict(ligne: sqlite3.Row | None):
    return dict(ligne) if ligne is not None else None


def mois_courant() -> str:
    return datetime.date.today().strftime("%Y-%m")


# --------------------------------------------------------------------------- #
# Mois
# --------------------------------------------------------------------------- #

def liste_mois(cnx) -> list[dict]:
    return [dict(r) for r in cnx.execute("SELECT * FROM mois ORDER BY libelle DESC")]


def lire_mois(cnx, mois_id: int):
    return _dict(cnx.execute("SELECT * FROM mois WHERE id = ?", (mois_id,)).fetchone())


def mois_par_libelle(cnx, libelle: str):
    return _dict(cnx.execute("SELECT * FROM mois WHERE libelle = ?", (libelle,)).fetchone())


def cree_mois(cnx, libelle: str, copier_de: int | None = None,
              nb_semaines: int = SEMAINES_PAR_DEFAUT) -> dict:
    """Crée un mois, éventuellement en recopiant un mois existant.

    La copie reprend les lignes récurrentes (libellés, montants estimés, mises
    en pause) mais remet tous les montants réels à zéro : le nouveau mois
    démarre donc « pré-rempli mais vierge ».
    """
    libelle = (libelle or "").strip() or mois_courant()
    existant = mois_par_libelle(cnx, libelle)
    if existant:
        return existant

    source = lire_mois(cnx, copier_de) if copier_de else None
    cur = cnx.execute(
        "INSERT INTO mois (libelle, taux_horaire, taux_cotisation, budget_courses, cree_le)"
        " VALUES (?, ?, ?, ?, ?)",
        (
            libelle,
            source["taux_horaire"] if source else modele.TAUX_HORAIRE_DEFAUT,
            source["taux_cotisation"] if source else modele.TAUX_COTISATION_DEFAUT,
            source["budget_courses"] if source else 400.0,
            datetime.datetime.now().isoformat(timespec="seconds"),
        ),
    )
    mois_id = int(cur.lastrowid)

    if source:
        cnx.executemany(
            "INSERT INTO ligne (mois_id, type, nature, categorie, libelle, estime, reel,"
            " actif, note, lien, rang) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)",
            [
                (mois_id, r["type"], r["nature"], r["categorie"], r["libelle"],
                 r["estime"], r["actif"], r["note"], r["lien"], r["rang"])
                for r in cnx.execute(
                    "SELECT * FROM ligne WHERE mois_id = ? ORDER BY rang, id", (source["id"],))
            ],
        )
        semaines = [(mois_id, r["numero"], r["budget"]) for r in cnx.execute(
            "SELECT numero, budget FROM semaine WHERE mois_id = ? ORDER BY numero",
            (source["id"],))]
        if semaines:
            cnx.executemany(
                "INSERT INTO semaine (mois_id, numero, budget) VALUES (?, ?, ?)", semaines)
            nb_semaines = 0

    if nb_semaines:
        cnx.executemany(
            "INSERT INTO semaine (mois_id, numero, budget) VALUES (?, ?, ?)",
            [(mois_id, n, 100.0) for n in range(1, nb_semaines + 1)],
        )

    for numero in [r["numero"] for r in cnx.execute(
            "SELECT numero FROM semaine WHERE mois_id = ? ORDER BY numero", (mois_id,))]:
        assure_semaine_creneaux(cnx, mois_id, numero)

    cnx.commit()
    return lire_mois(cnx, mois_id)


def supprime_mois(cnx, mois_id: int) -> None:
    cnx.execute("DELETE FROM mois WHERE id = ?", (mois_id,))
    cnx.commit()


def maj_mois(cnx, mois_id: int, champs: dict) -> dict:
    autorises = {"note": str, "taux_horaire": modele.nombre,
                 "taux_cotisation": modele.nombre, "budget_courses": modele.nombre,
                 "libelle": str}
    sets, valeurs = [], []
    for nom, convertit in autorises.items():
        if nom in champs:
            sets.append(f"{nom} = ?")
            valeurs.append(convertit(champs[nom]))
    if sets:
        valeurs.append(mois_id)
        cnx.execute(f"UPDATE mois SET {', '.join(sets)} WHERE id = ?", valeurs)
        cnx.commit()
    return lire_mois(cnx, mois_id)


# --------------------------------------------------------------------------- #
# Lignes (dépenses, salaires, aides)
# --------------------------------------------------------------------------- #

def liste_lignes(cnx, mois_id: int) -> list[dict]:
    return [dict(r) for r in cnx.execute(
        "SELECT * FROM ligne WHERE mois_id = ? ORDER BY rang, id", (mois_id,))]


def _prochain_rang(cnx, table: str, mois_id: int) -> int:
    valeur = cnx.execute(
        f"SELECT COALESCE(MAX(rang), 0) + 10 FROM {table} WHERE mois_id = ?",
        (mois_id,)).fetchone()[0]
    return int(valeur)


def cree_ligne(cnx, mois_id: int, champs: dict) -> dict:
    donnees = {
        "type": champs.get("type") if champs.get("type") in modele.TYPES else "depense",
        "nature": champs.get("nature") if champs.get("nature") in modele.NATURES else "variable",
        "categorie": str(champs.get("categorie") or "").strip(),
        "libelle": str(champs.get("libelle") or "").strip(),
        "estime": modele.nombre(champs.get("estime")),
        "reel": modele.nombre(champs.get("reel")),
        "actif": 1 if champs.get("actif", True) else 0,
        "note": str(champs.get("note") or ""),
        "lien": str(champs.get("lien") or "").strip(),
        "rang": int(champs.get("rang") or _prochain_rang(cnx, "ligne", mois_id)),
    }
    cur = cnx.execute(
        "INSERT INTO ligne (mois_id, type, nature, categorie, libelle, estime, reel,"
        " actif, note, lien, rang) VALUES (:mois_id, :type, :nature, :categorie, :libelle,"
        " :estime, :reel, :actif, :note, :lien, :rang)",
        {"mois_id": mois_id, **donnees},
    )
    cnx.commit()
    return _dict(cnx.execute("SELECT * FROM ligne WHERE id = ?", (cur.lastrowid,)).fetchone())


def maj_ligne(cnx, ligne_id: int, champs: dict):
    conversions = {
        "type": lambda v: v if v in modele.TYPES else "depense",
        "nature": lambda v: v if v in modele.NATURES else "variable",
        "categorie": lambda v: str(v or "").strip(),
        "libelle": lambda v: str(v or "").strip(),
        "estime": modele.nombre,
        "reel": modele.nombre,
        "actif": lambda v: 1 if v in (True, 1, "1", "true", "on") else 0,
        "note": lambda v: str(v or ""),
        "lien": lambda v: str(v or "").strip(),
        "rang": lambda v: int(v or 0),
    }
    sets, valeurs = [], []
    for nom, convertit in conversions.items():
        if nom in champs:
            sets.append(f"{nom} = ?")
            valeurs.append(convertit(champs[nom]))
    if sets:
        valeurs.append(ligne_id)
        cnx.execute(f"UPDATE ligne SET {', '.join(sets)} WHERE id = ?", valeurs)
        cnx.commit()
    return _dict(cnx.execute("SELECT * FROM ligne WHERE id = ?", (ligne_id,)).fetchone())


def supprime_ligne(cnx, ligne_id: int) -> None:
    cnx.execute("DELETE FROM ligne WHERE id = ?", (ligne_id,))
    cnx.commit()


# --------------------------------------------------------------------------- #
# Courses
# --------------------------------------------------------------------------- #

def liste_semaines(cnx, mois_id: int) -> list[dict]:
    return [dict(r) for r in cnx.execute(
        "SELECT * FROM semaine WHERE mois_id = ? ORDER BY numero", (mois_id,))]


def liste_achats(cnx, mois_id: int) -> list[dict]:
    return [dict(r) for r in cnx.execute(
        "SELECT * FROM achat WHERE mois_id = ? ORDER BY semaine, rang, id", (mois_id,))]


def cree_achat(cnx, mois_id: int, champs: dict) -> dict:
    cur = cnx.execute(
        "INSERT INTO achat (mois_id, semaine, poste, libelle, montant, rang)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (mois_id, int(champs.get("semaine") or 1), str(champs.get("poste") or "").strip(),
         str(champs.get("libelle") or "").strip(), modele.nombre(champs.get("montant")),
         int(champs.get("rang") or _prochain_rang(cnx, "achat", mois_id))),
    )
    cnx.commit()
    return _dict(cnx.execute("SELECT * FROM achat WHERE id = ?", (cur.lastrowid,)).fetchone())


def maj_achat(cnx, achat_id: int, champs: dict):
    conversions = {
        "semaine": lambda v: max(1, int(v or 1)),
        "poste": lambda v: str(v or "").strip(),
        "libelle": lambda v: str(v or "").strip(),
        "montant": modele.nombre,
        "rang": lambda v: int(v or 0),
    }
    sets, valeurs = [], []
    for nom, convertit in conversions.items():
        if nom in champs:
            sets.append(f"{nom} = ?")
            valeurs.append(convertit(champs[nom]))
    if sets:
        valeurs.append(achat_id)
        cnx.execute(f"UPDATE achat SET {', '.join(sets)} WHERE id = ?", valeurs)
        cnx.commit()
    return _dict(cnx.execute("SELECT * FROM achat WHERE id = ?", (achat_id,)).fetchone())


def supprime_achat(cnx, achat_id: int) -> None:
    cnx.execute("DELETE FROM achat WHERE id = ?", (achat_id,))
    cnx.commit()


def maj_semaine(cnx, mois_id: int, numero: int, budget) -> dict:
    cnx.execute(
        "INSERT INTO semaine (mois_id, numero, budget) VALUES (?, ?, ?)"
        " ON CONFLICT (mois_id, numero) DO UPDATE SET budget = excluded.budget",
        (mois_id, int(numero), modele.nombre(budget)),
    )
    cnx.commit()
    return _dict(cnx.execute(
        "SELECT * FROM semaine WHERE mois_id = ? AND numero = ?", (mois_id, numero)).fetchone())


def ajoute_semaine(cnx, mois_id: int) -> dict:
    numero = int(cnx.execute(
        "SELECT COALESCE(MAX(numero), 0) + 1 FROM semaine WHERE mois_id = ?",
        (mois_id,)).fetchone()[0])
    cnx.execute("INSERT INTO semaine (mois_id, numero, budget) VALUES (?, ?, 100)",
                (mois_id, numero))
    assure_semaine_creneaux(cnx, mois_id, numero)
    cnx.commit()
    return {"numero": numero}


def supprime_semaine(cnx, mois_id: int, numero: int) -> None:
    """Supprime la dernière semaine ainsi que ses achats et créneaux."""
    cnx.execute("DELETE FROM semaine WHERE mois_id = ? AND numero = ?", (mois_id, numero))
    cnx.execute("DELETE FROM achat WHERE mois_id = ? AND semaine = ?", (mois_id, numero))
    cnx.execute("DELETE FROM creneau WHERE mois_id = ? AND semaine = ?", (mois_id, numero))
    cnx.commit()


# --------------------------------------------------------------------------- #
# Créneaux de garde
# --------------------------------------------------------------------------- #

def assure_semaine_creneaux(cnx, mois_id: int, numero: int) -> None:
    """Crée les 7 jours d'une semaine s'ils n'existent pas déjà."""
    cnx.executemany(
        "INSERT OR IGNORE INTO creneau (mois_id, semaine, jour) VALUES (?, ?, ?)",
        [(mois_id, numero, jour) for jour in range(7)],
    )


def liste_creneaux(cnx, mois_id: int) -> list[dict]:
    return [dict(r) for r in cnx.execute(
        "SELECT * FROM creneau WHERE mois_id = ? ORDER BY semaine, jour", (mois_id,))]


def maj_creneau(cnx, creneau_id: int, champs: dict):
    sets, valeurs = [], []
    for nom in CHAMPS_CRENEAU:
        if nom in champs:
            minutes = modele.minutes_depuis_heure(champs[nom])
            sets.append(f"{nom} = ?")
            valeurs.append(modele.heure_depuis_minutes(minutes) if minutes is not None else "")
    if sets:
        valeurs.append(creneau_id)
        cnx.execute(f"UPDATE creneau SET {', '.join(sets)} WHERE id = ?", valeurs)
        cnx.commit()
    return _dict(cnx.execute("SELECT * FROM creneau WHERE id = ?", (creneau_id,)).fetchone())


# --------------------------------------------------------------------------- #
# Vue complète d'un mois
# --------------------------------------------------------------------------- #

def detail_mois(cnx, mois_id: int):
    mois = lire_mois(cnx, mois_id)
    if not mois:
        return None
    lignes = liste_lignes(cnx, mois_id)
    semaines = liste_semaines(cnx, mois_id)
    achats = liste_achats(cnx, mois_id)
    creneaux = liste_creneaux(cnx, mois_id)
    for creneau in creneaux:
        creneau["minutes"] = modele.duree_creneau(creneau)
        creneau["duree"] = modele.format_duree(creneau["minutes"]) if creneau["minutes"] else ""
    return {
        "mois": mois,
        "lignes": lignes,
        "semaines": semaines,
        "achats": achats,
        "creneaux": creneaux,
        "recap": modele.recap(mois, lignes, semaines, achats, creneaux),
    }
