"""Serveur HTTP : sert l'interface HTML et l'API JSON.

Uniquement de la bibliothèque standard Python — rien à installer. Le serveur
n'écoute que sur la machine locale : les données restent sur l'ordinateur.
"""

from __future__ import annotations

import csv
import io
import json
import re
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from . import base, modele

RACINE_WEB = Path(__file__).resolve().parent.parent / "web"

FICHIERS_STATIQUES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}


class ErreurRequete(Exception):
    """Erreur renvoyée telle quelle au client, avec un code HTTP."""

    def __init__(self, message: str, code: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code


# --------------------------------------------------------------------------- #
# Routage
# --------------------------------------------------------------------------- #

ROUTES: list[tuple[str, re.Pattern, str]] = []


def route(methode: str, motif: str):
    def decorateur(fonction):
        ROUTES.append((methode, re.compile(f"^{motif}$"), fonction.__name__))
        return fonction
    return decorateur


class Api:
    """Les points d'entrée de l'API. Chaque méthode renvoie un objet JSON."""

    def __init__(self, cnx):
        self.cnx = cnx

    # -- lecture ----------------------------------------------------------- #

    @route("GET", r"/api/etat")
    def etat(self, corps=None):
        mois = base.liste_mois(self.cnx)
        return {"mois": mois, "mois_actif_id": mois[0]["id"] if mois else None}

    @route("GET", r"/api/mois/(\d+)")
    def detail(self, mois_id, corps=None):
        detail = base.detail_mois(self.cnx, int(mois_id))
        if detail is None:
            raise ErreurRequete("Ce mois n'existe pas.", 404)
        detail["mois_disponibles"] = base.liste_mois(self.cnx)
        return detail

    # -- mois -------------------------------------------------------------- #

    @route("POST", r"/api/mois")
    def nouveau_mois(self, corps=None):
        corps = corps or {}
        libelle = str(corps.get("libelle") or base.mois_courant()).strip()
        if not re.match(r"^\d{4}-\d{2}$", libelle):
            raise ErreurRequete("Le mois doit être au format AAAA-MM (par exemple 2026-10).")
        copier_de = corps.get("copier_de")
        mois = base.cree_mois(self.cnx, libelle, int(copier_de) if copier_de else None)
        return self.detail(mois["id"])

    @route("PATCH", r"/api/mois/(\d+)")
    def modifie_mois(self, mois_id, corps=None):
        base.maj_mois(self.cnx, int(mois_id), corps or {})
        return self.detail(mois_id)

    @route("DELETE", r"/api/mois/(\d+)")
    def efface_mois(self, mois_id, corps=None):
        base.supprime_mois(self.cnx, int(mois_id))
        return self.etat()

    # -- lignes ------------------------------------------------------------ #

    @route("POST", r"/api/mois/(\d+)/lignes")
    def nouvelle_ligne(self, mois_id, corps=None):
        ligne = base.cree_ligne(self.cnx, int(mois_id), corps or {})
        detail = self.detail(mois_id)
        detail["nouvel_id"] = ligne["id"]
        return detail

    @route("PATCH", r"/api/lignes/(\d+)")
    def modifie_ligne(self, ligne_id, corps=None):
        ligne = base.maj_ligne(self.cnx, int(ligne_id), corps or {})
        if ligne is None:
            raise ErreurRequete("Cette ligne n'existe pas.", 404)
        return self.detail(ligne["mois_id"])

    @route("DELETE", r"/api/lignes/(\d+)")
    def efface_ligne(self, ligne_id, corps=None):
        ligne = base._dict(self.cnx.execute(
            "SELECT mois_id FROM ligne WHERE id = ?", (int(ligne_id),)).fetchone())
        if ligne is None:
            raise ErreurRequete("Cette ligne n'existe pas.", 404)
        base.supprime_ligne(self.cnx, int(ligne_id))
        return self.detail(ligne["mois_id"])

    # -- courses ----------------------------------------------------------- #

    @route("POST", r"/api/mois/(\d+)/achats")
    def nouvel_achat(self, mois_id, corps=None):
        achat = base.cree_achat(self.cnx, int(mois_id), corps or {})
        detail = self.detail(mois_id)
        detail["nouvel_id"] = achat["id"]
        return detail

    @route("PATCH", r"/api/achats/(\d+)")
    def modifie_achat(self, achat_id, corps=None):
        achat = base.maj_achat(self.cnx, int(achat_id), corps or {})
        if achat is None:
            raise ErreurRequete("Cet achat n'existe pas.", 404)
        return self.detail(achat["mois_id"])

    @route("DELETE", r"/api/achats/(\d+)")
    def efface_achat(self, achat_id, corps=None):
        achat = base._dict(self.cnx.execute(
            "SELECT mois_id FROM achat WHERE id = ?", (int(achat_id),)).fetchone())
        if achat is None:
            raise ErreurRequete("Cet achat n'existe pas.", 404)
        base.supprime_achat(self.cnx, int(achat_id))
        return self.detail(achat["mois_id"])

    @route("PATCH", r"/api/mois/(\d+)/semaines/(\d+)")
    def modifie_semaine(self, mois_id, numero, corps=None):
        base.maj_semaine(self.cnx, int(mois_id), int(numero), (corps or {}).get("budget"))
        return self.detail(mois_id)

    @route("POST", r"/api/mois/(\d+)/semaines")
    def nouvelle_semaine(self, mois_id, corps=None):
        base.ajoute_semaine(self.cnx, int(mois_id))
        return self.detail(mois_id)

    @route("DELETE", r"/api/mois/(\d+)/semaines/(\d+)")
    def efface_semaine(self, mois_id, numero, corps=None):
        semaines = base.liste_semaines(self.cnx, int(mois_id))
        if len(semaines) <= 1:
            raise ErreurRequete("Il faut garder au moins une semaine.")
        base.supprime_semaine(self.cnx, int(mois_id), int(numero))
        return self.detail(mois_id)

    # -- créneaux ---------------------------------------------------------- #

    @route("PATCH", r"/api/creneaux/(\d+)")
    def modifie_creneau(self, creneau_id, corps=None):
        creneau = base.maj_creneau(self.cnx, int(creneau_id), corps or {})
        if creneau is None:
            raise ErreurRequete("Ce créneau n'existe pas.", 404)
        return self.detail(creneau["mois_id"])

    # -- reports automatiques --------------------------------------------- #

    @route("POST", r"/api/mois/(\d+)/report/(courses|heures)")
    def report(self, mois_id, cible, corps=None):
        """Recopie un total calculé dans la ligne de budget qui lui correspond.

        « courses » : le total des courses devient le réel de la ligne liée.
        « heures »  : le salaire net calculé devient le réel du salaire lié.
        """
        mois_id = int(mois_id)
        detail = base.detail_mois(self.cnx, mois_id)
        if detail is None:
            raise ErreurRequete("Ce mois n'existe pas.", 404)
        montant = (detail["recap"]["courses"]["depense"] if cible == "courses"
                   else detail["recap"]["heures"]["net"])
        cibles = [l for l in detail["lignes"] if (l["lien"] or "") == cible]
        if not cibles:
            raise ErreurRequete(
                "Aucune ligne n'est reliée à ce total. Choisissez le lien "
                f"« {cible} » sur la ligne concernée (colonne Lien).")
        for ligne in cibles[:1]:
            base.maj_ligne(self.cnx, ligne["id"], {"reel": montant})
        return self.detail(mois_id)

    # -- import / export --------------------------------------------------- #

    @route("GET", r"/api/export.json")
    def export_json(self, corps=None):
        donnees = {"version": 1, "mois": []}
        for mois in base.liste_mois(self.cnx):
            detail = base.detail_mois(self.cnx, mois["id"])
            donnees["mois"].append({
                "mois": {k: v for k, v in detail["mois"].items() if k != "id"},
                "lignes": [{k: v for k, v in l.items() if k not in ("id", "mois_id")}
                           for l in detail["lignes"]],
                "semaines": [{"numero": s["numero"], "budget": s["budget"]}
                             for s in detail["semaines"]],
                "achats": [{k: v for k, v in a.items() if k not in ("id", "mois_id")}
                           for a in detail["achats"]],
                "creneaux": [{k: v for k, v in c.items()
                              if k not in ("id", "mois_id", "minutes", "duree")}
                             for c in detail["creneaux"]],
            })
        return donnees

    @route("POST", r"/api/import")
    def import_json(self, corps=None):
        """Recrée les mois contenus dans un export. Les mois existants sont ignorés."""
        corps = corps or {}
        importes = 0
        for bloc in corps.get("mois", []):
            entete = bloc.get("mois", {})
            libelle = str(entete.get("libelle") or "").strip()
            if not re.match(r"^\d{4}-\d{2}$", libelle) or base.mois_par_libelle(self.cnx, libelle):
                continue
            mois = base.cree_mois(self.cnx, libelle, nb_semaines=0)
            base.maj_mois(self.cnx, mois["id"], entete)
            for ligne in bloc.get("lignes", []):
                base.cree_ligne(self.cnx, mois["id"], ligne)
            semaines = bloc.get("semaines") or [{"numero": n, "budget": 100} for n in range(1, 5)]
            for semaine in semaines:
                base.maj_semaine(self.cnx, mois["id"], semaine["numero"], semaine.get("budget"))
                base.assure_semaine_creneaux(self.cnx, mois["id"], int(semaine["numero"]))
            for achat in bloc.get("achats", []):
                base.cree_achat(self.cnx, mois["id"], achat)
            for creneau in bloc.get("creneaux", []):
                base.assure_semaine_creneaux(self.cnx, mois["id"], int(creneau.get("semaine") or 1))
                existant = self.cnx.execute(
                    "SELECT id FROM creneau WHERE mois_id = ? AND semaine = ? AND jour = ?",
                    (mois["id"], int(creneau.get("semaine") or 1),
                     int(creneau.get("jour") or 0))).fetchone()
                if existant:
                    base.maj_creneau(self.cnx, existant["id"], creneau)
            importes += 1
        self.cnx.commit()
        etat = self.etat()
        etat["importes"] = importes
        return etat


def export_csv(cnx, mois_id: int) -> tuple[str, str]:
    """Renvoie (nom du fichier, contenu CSV) pour un mois."""
    detail = base.detail_mois(cnx, int(mois_id))
    if detail is None:
        raise ErreurRequete("Ce mois n'existe pas.", 404)
    tampon = io.StringIO()
    # point-virgule + BOM : Excel français ouvre le fichier directement.
    ecrivain = csv.writer(tampon, delimiter=";")
    ecrivain.writerow(["Type", "Nature", "Catégorie", "Libellé", "Estimé", "Réel",
                       "Écart", "Actif", "Note"])
    for ligne in detail["lignes"]:
        estime = modele.eur(ligne["estime"]) if ligne["actif"] else 0.0
        ecrivain.writerow([
            ligne["type"], ligne["nature"], ligne["categorie"], ligne["libelle"],
            f"{modele.eur(ligne['estime']):.2f}".replace(".", ","),
            f"{modele.eur(ligne['reel']):.2f}".replace(".", ","),
            f"{estime - modele.eur(ligne['reel']):.2f}".replace(".", ","),
            "oui" if ligne["actif"] else "non", ligne["note"],
        ])
    budget = detail["recap"]["budget"]
    ecrivain.writerow([])
    for intitule, valeurs in (("TOTAL DÉPENSES", budget["depenses"]),
                              ("TOTAL REVENUS", budget["revenus"]),
                              ("RESTANT", budget["restant"])):
        ecrivain.writerow([intitule, "", "", "",
                           f"{valeurs['estime']:.2f}".replace(".", ","),
                           f"{valeurs['reel']:.2f}".replace(".", ",")])
    ecrivain.writerow([])
    ecrivain.writerow(["Courses — semaine", "Poste", "Libellé", "Montant"])
    for achat in detail["achats"]:
        ecrivain.writerow([achat["semaine"], achat["poste"], achat["libelle"],
                           f"{modele.eur(achat['montant']):.2f}".replace(".", ",")])
    heures = detail["recap"]["heures"]
    ecrivain.writerow([])
    ecrivain.writerow(["Heures gardées", heures["duree"]])
    ecrivain.writerow(["Salaire brut", f"{heures['brut']:.2f}".replace(".", ",")])
    ecrivain.writerow(["Cotisations", f"{heures['cotisation']:.2f}".replace(".", ",")])
    ecrivain.writerow(["Salaire net", f"{heures['net']:.2f}".replace(".", ",")])
    return f"comptes-{detail['mois']['libelle']}.csv", "﻿" + tampon.getvalue()


# --------------------------------------------------------------------------- #
# Couche HTTP
# --------------------------------------------------------------------------- #

class Gestionnaire(BaseHTTPRequestHandler):
    server_version = "Comptes/1.0"
    cnx = None  # injecté par demarre()

    # -- utilitaires ------------------------------------------------------- #

    def _envoie(self, code, contenu: bytes, type_mime: str, entetes=None):
        self.send_response(code)
        self.send_header("Content-Type", type_mime)
        self.send_header("Content-Length", str(len(contenu)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for nom, valeur in (entetes or {}).items():
            self.send_header(nom, valeur)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(contenu)

    def _envoie_json(self, donnees, code=200):
        contenu = json.dumps(donnees, ensure_ascii=False).encode("utf-8")
        self._envoie(code, contenu, "application/json; charset=utf-8")

    def _erreur(self, message: str, code: int = 400):
        self._envoie_json({"erreur": message}, code)

    def _corps(self):
        longueur = int(self.headers.get("Content-Length") or 0)
        if longueur <= 0:
            return {}
        if longueur > 16 * 1024 * 1024:
            raise ErreurRequete("Requête trop volumineuse.", 413)
        brut = self.rfile.read(longueur)
        try:
            donnees = json.loads(brut.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ErreurRequete("Corps de requête illisible (JSON attendu).")
        return donnees if isinstance(donnees, dict) else {}

    # -- méthodes HTTP ----------------------------------------------------- #

    def do_GET(self):
        self._traite("GET")

    def do_HEAD(self):
        self._traite("GET")

    def do_POST(self):
        self._traite("POST")

    def do_PATCH(self):
        self._traite("PATCH")

    def do_DELETE(self):
        self._traite("DELETE")

    def _traite(self, methode: str):
        chemin = unquote(urlparse(self.path).path)
        try:
            if methode == "GET" and chemin in FICHIERS_STATIQUES:
                return self._sert_statique(chemin)

            correspondance = re.match(r"^/api/mois/(\d+)/export\.csv$", chemin)
            if methode == "GET" and correspondance:
                nom, contenu = export_csv(self.cnx, correspondance.group(1))
                return self._envoie(
                    200, contenu.encode("utf-8"), "text/csv; charset=utf-8",
                    {"Content-Disposition": f'attachment; filename="{nom}"'})

            for methode_route, motif, nom_fonction in ROUTES:
                trouve = motif.match(chemin)
                if not trouve:
                    continue
                if methode_route != methode:
                    continue
                api = Api(self.cnx)
                corps = self._corps() if methode in ("POST", "PATCH") else None
                resultat = getattr(api, nom_fonction)(*trouve.groups(), corps=corps)
                return self._envoie_json(resultat)

            if chemin.startswith("/api/"):
                return self._erreur("Point d'entrée inconnu.", 404)
            return self._erreur("Page inconnue.", 404)
        except ErreurRequete as erreur:
            return self._erreur(erreur.message, erreur.code)
        except Exception:  # pragma: no cover - filet de sécurité
            traceback.print_exc()
            return self._erreur("Erreur interne du serveur.", 500)

    def _sert_statique(self, chemin: str):
        nom, type_mime = FICHIERS_STATIQUES[chemin]
        fichier = RACINE_WEB / nom
        if not fichier.is_file():
            return self._erreur(f"Fichier manquant : web/{nom}", 500)
        self._envoie(200, fichier.read_bytes(), type_mime)

    def log_message(self, format, *args):  # pragma: no cover
        if self.server.mode_bavard:
            super().log_message(format, *args)


class Serveur(ThreadingHTTPServer):
    daemon_threads = True
    mode_bavard = False


def demarre(cnx, hote="127.0.0.1", port=8000, mode_bavard=False) -> Serveur:
    Gestionnaire.cnx = cnx
    serveur = Serveur((hote, port), Gestionnaire)
    serveur.mode_bavard = mode_bavard
    return serveur
