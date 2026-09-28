#!/usr/bin/env python3
"""Comptes — suivi budgétaire mensuel.

Lancement :

    python3 app.py

Le navigateur s'ouvre sur http://127.0.0.1:8000. Aucune dépendance à
installer : tout vient de la bibliothèque standard de Python.
"""

from __future__ import annotations

import argparse
import sys
import threading
import webbrowser
from pathlib import Path

from comptes import base, exemple, serveur

BASE_PAR_DEFAUT = Path(__file__).resolve().parent / "donnees" / "comptes.db"


def analyse_arguments(argv=None):
    analyseur = argparse.ArgumentParser(
        description="Lance l'application de comptes dans le navigateur.")
    analyseur.add_argument("--port", type=int, default=8000,
                           help="port d'écoute (8000 par défaut)")
    analyseur.add_argument("--base", type=Path, default=BASE_PAR_DEFAUT,
                           help="chemin du fichier de données SQLite")
    analyseur.add_argument("--sans-navigateur", action="store_true",
                           help="ne pas ouvrir le navigateur automatiquement")
    analyseur.add_argument("--sans-exemple", action="store_true",
                           help="démarrer avec un mois vide plutôt que pré-rempli")
    analyseur.add_argument("--bavard", action="store_true",
                           help="afficher chaque requête HTTP")
    return analyseur.parse_args(argv)


def main(argv=None) -> int:
    options = analyse_arguments(argv)
    cnx = base.connexion(options.base)

    if not base.liste_mois(cnx):
        if options.sans_exemple:
            base.cree_mois(cnx, base.mois_courant())
            print("→ Mois vide créé.")
        else:
            exemple.remplit(cnx)
            print("→ Premier démarrage : mois pré-rempli avec les données du tableau.")

    for essai in range(20):
        try:
            httpd = serveur.demarre(cnx, port=options.port + essai,
                                    mode_bavard=options.bavard)
            break
        except OSError:
            if essai == 19:
                print(f"Impossible d'ouvrir un port à partir de {options.port}.",
                      file=sys.stderr)
                return 1
    else:  # pragma: no cover
        return 1

    adresse = f"http://127.0.0.1:{httpd.server_address[1]}"
    print(f"\n  Comptes est prêt : {adresse}")
    print(f"  Données : {options.base}")
    print("  Arrêter : Ctrl+C\n")

    if not options.sans_navigateur:
        threading.Timer(0.6, lambda: webbrowser.open(adresse)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nÀ bientôt.")
    finally:
        httpd.server_close()
        cnx.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
