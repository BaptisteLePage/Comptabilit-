"""Tests des calculs et du stockage.

    python3 -m unittest discover -s tests
"""

import sqlite3
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from comptes import base, exemple, modele, serveur


class TestLectureDesMontants(unittest.TestCase):
    def test_virgule_francaise(self):
        self.assertEqual(modele.nombre("19,99"), 19.99)
        self.assertEqual(modele.nombre("1 234,56"), 1234.56)
        self.assertEqual(modele.nombre("1 234,56"), 1234.56)
        self.assertEqual(modele.nombre("12,50 €"), 12.50)

    def test_valeurs_limites(self):
        for entree in ("", None, "abc", "-", "."):
            self.assertEqual(modele.nombre(entree), 0.0)
        self.assertEqual(modele.nombre(-42), -42.0)
        self.assertEqual(modele.nombre("7"), 7.0)


class TestHeures(unittest.TestCase):
    def test_lecture_des_heures(self):
        self.assertEqual(modele.minutes_depuis_heure("09:30"), 570)
        self.assertEqual(modele.minutes_depuis_heure("9h30"), 570)
        self.assertEqual(modele.minutes_depuis_heure("9"), 540)
        for entree in ("", None, "abc", "25:00", "10:75"):
            self.assertIsNone(modele.minutes_depuis_heure(entree))

    def test_duree_incoherente_vaut_zero(self):
        self.assertEqual(modele.duree_plage("11:00", "09:00"), 0)
        self.assertEqual(modele.duree_plage("09:00", ""), 0)
        self.assertEqual(modele.duree_plage("09:00", "09:00"), 0)

    def test_total_et_salaire(self):
        """Reprend les quatre journées relevées dans le tableau d'origine."""
        creneaux = [
            {"semaine": 1, "matin_debut": "10:04", "matin_fin": "11:30",
             "aprem_debut": "13:36", "aprem_fin": "17:00"},   # 290 min
            {"semaine": 1, "matin_debut": "09:30", "matin_fin": "11:30",
             "aprem_debut": "12:30", "aprem_fin": "15:00"},   # 270 min
            {"semaine": 2, "matin_debut": "10:00", "matin_fin": "11:30",
             "aprem_debut": "12:44", "aprem_fin": "13:28"},   # 134 min
            {"semaine": 3, "matin_debut": "09:30", "matin_fin": "12:16",
             "aprem_debut": "12:48", "aprem_fin": "13:19"},   # 197 min
        ]
        recap = modele.recap_heures(creneaux, 12.02, 21.2)
        self.assertEqual(recap["minutes"], 891)
        self.assertEqual(recap["duree"], "14 h 51")
        self.assertAlmostEqual(recap["brut"], round(891 / 60 * 12.02, 2))
        self.assertAlmostEqual(recap["cotisation"], round(recap["brut"] * 0.212, 2))
        self.assertAlmostEqual(recap["net"], round(recap["brut"] - recap["cotisation"], 2))
        self.assertEqual([s["semaine"] for s in recap["par_semaine"]], [1, 2, 3])

    def test_sans_creneau(self):
        recap = modele.recap_heures([], 12.02, 21.2)
        self.assertEqual(recap["minutes"], 0)
        self.assertEqual(recap["net"], 0.0)


class TestCourses(unittest.TestCase):
    def test_totaux_et_restant(self):
        semaines = [{"numero": 1, "budget": 100}, {"numero": 2, "budget": 100}]
        achats = [
            {"semaine": 1, "poste": "Marché", "montant": 23.40},
            {"semaine": 1, "poste": "Carrefour", "montant": 62.80},
            {"semaine": 2, "poste": "Marché", "montant": 18.90},
        ]
        recap = modele.recap_courses(semaines, achats, 400)
        self.assertEqual(recap["depense"], 105.10)
        self.assertEqual(recap["restant"], 294.90)
        self.assertEqual(recap["semaines"][0]["depense"], 86.20)
        self.assertEqual(recap["semaines"][0]["restant"], 13.80)
        self.assertEqual(recap["semaines"][1]["restant"], 81.10)
        self.assertEqual(recap["par_poste"][0]["poste"], "Carrefour")

    def test_depassement(self):
        recap = modele.recap_courses([{"numero": 1, "budget": 50}],
                                     [{"semaine": 1, "montant": 80}], 50)
        self.assertEqual(recap["restant"], -30.0)
        self.assertEqual(recap["semaines"][0]["restant"], -30.0)


class TestBudget(unittest.TestCase):
    def lignes(self):
        return [
            {"id": 1, "type": "depense", "nature": "fixe", "categorie": "Santé",
             "libelle": "MNH", "estime": 70, "reel": 70, "actif": 1, "lien": ""},
            {"id": 2, "type": "depense", "nature": "variable", "categorie": "Streaming",
             "libelle": "Disney+", "estime": 12, "reel": 0, "actif": 0, "lien": ""},
            {"id": 3, "type": "depense", "nature": "fixe", "categorie": "Garde",
             "libelle": "Assistante maternelle", "estime": 500, "reel": 480,
             "actif": 1, "lien": "garde"},
            {"id": 4, "type": "salaire", "nature": "fixe", "categorie": "Salaire",
             "libelle": "Evry", "estime": 1800, "reel": 1750, "actif": 1, "lien": ""},
            {"id": 5, "type": "aide", "nature": "variable", "categorie": "Aide",
             "libelle": "CAF", "estime": 300, "reel": 310, "actif": 1, "lien": "caf"},
        ]

    def test_une_ligne_en_pause_ne_compte_pas(self):
        recap = modele.recap_budget(self.lignes())
        self.assertEqual(recap["depenses"]["estime"], 570.0)   # 70 + 500, pas les 12
        self.assertEqual(recap["economie_en_pause"], 12.0)
        self.assertEqual(recap["en_pause"][0]["libelle"], "Disney+")

    def test_totaux(self):
        recap = modele.recap_budget(self.lignes())
        self.assertEqual(recap["depenses"]["reel"], 550.0)
        self.assertEqual(recap["revenus"]["reel"], 2060.0)
        self.assertEqual(recap["restant"]["reel"], 1510.0)
        self.assertEqual(recap["surplus"]["reel"], 20.0)       # 570 prévus - 550 réels
        self.assertEqual(recap["garde_nette"]["reel"], 170.0)  # 480 - 310

    def test_repartition_par_categorie(self):
        recap = modele.recap_budget(self.lignes())
        categories = {c["categorie"]: c for c in recap["par_categorie"]}
        self.assertEqual(categories["Garde"]["reel"], 480.0)
        self.assertEqual(categories["Streaming"]["estime"], 0.0)  # en pause
        self.assertNotIn("Salaire", categories)                   # revenus exclus

    def test_ligne_de_type_inconnu_ignoree(self):
        recap = modele.recap_budget([{"type": "autre", "nature": "fixe",
                                      "estime": 99, "reel": 99, "actif": 1}])
        self.assertEqual(recap["depenses"]["reel"], 0.0)


class TestBase(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.TemporaryDirectory()
        self.cnx = base.connexion(Path(self.dossier.name) / "test.db")

    def tearDown(self):
        self.cnx.close()
        self.dossier.cleanup()

    def test_creation_mois(self):
        mois = base.cree_mois(self.cnx, "2026-01")
        self.assertEqual(len(base.liste_semaines(self.cnx, mois["id"])), 4)
        self.assertEqual(len(base.liste_creneaux(self.cnx, mois["id"])), 28)

    def test_mois_en_double_renvoie_l_existant(self):
        premier = base.cree_mois(self.cnx, "2026-01")
        second = base.cree_mois(self.cnx, "2026-01")
        self.assertEqual(premier["id"], second["id"])

    def test_duplication_remet_les_reels_a_zero(self):
        source = exemple.remplit(self.cnx, "2026-01")
        copie = base.cree_mois(self.cnx, "2026-02", copier_de=source["id"])
        lignes_source = base.liste_lignes(self.cnx, source["id"])
        lignes_copie = base.liste_lignes(self.cnx, copie["id"])
        self.assertEqual(len(lignes_source), len(lignes_copie))
        self.assertTrue(all(l["reel"] == 0 for l in lignes_copie))
        self.assertEqual(sum(l["estime"] for l in lignes_copie),
                         sum(l["estime"] for l in lignes_source))
        # Les mises en pause suivent aussi.
        self.assertEqual(sum(1 for l in lignes_copie if not l["actif"]),
                         sum(1 for l in lignes_source if not l["actif"]))

    def test_suppression_mois_en_cascade(self):
        mois = exemple.remplit(self.cnx, "2026-01")
        base.supprime_mois(self.cnx, mois["id"])
        self.assertEqual(self.cnx.execute("SELECT COUNT(*) FROM ligne").fetchone()[0], 0)
        self.assertEqual(self.cnx.execute("SELECT COUNT(*) FROM creneau").fetchone()[0], 0)

    def test_creneau_normalise_la_saisie(self):
        mois = base.cree_mois(self.cnx, "2026-01")
        creneau = base.liste_creneaux(self.cnx, mois["id"])[0]
        maj = base.maj_creneau(self.cnx, creneau["id"],
                               {"matin_debut": "9h5", "matin_fin": "nimporte quoi"})
        self.assertEqual(maj["matin_debut"], "09:05")
        self.assertEqual(maj["matin_fin"], "")

    def test_type_de_ligne_invalide_retombe_sur_depense(self):
        mois = base.cree_mois(self.cnx, "2026-01")
        ligne = base.cree_ligne(self.cnx, mois["id"], {"type": "pirate", "nature": "farfelu"})
        self.assertEqual(ligne["type"], "depense")
        self.assertEqual(ligne["nature"], "variable")

    def test_suppression_semaine_emporte_son_contenu(self):
        mois = base.cree_mois(self.cnx, "2026-01")
        base.cree_achat(self.cnx, mois["id"], {"semaine": 4, "montant": 10})
        base.supprime_semaine(self.cnx, mois["id"], 4)
        self.assertEqual(len(base.liste_semaines(self.cnx, mois["id"])), 3)
        self.assertEqual(len(base.liste_achats(self.cnx, mois["id"])), 0)
        self.assertEqual(len(base.liste_creneaux(self.cnx, mois["id"])), 21)


class TestApi(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.TemporaryDirectory()
        self.cnx = base.connexion(Path(self.dossier.name) / "test.db")
        self.mois = exemple.remplit(self.cnx, "2026-01")
        self.api = serveur.Api(self.cnx)

    def tearDown(self):
        self.cnx.close()
        self.dossier.cleanup()

    def test_report_des_courses(self):
        base.cree_achat(self.cnx, self.mois["id"], {"semaine": 1, "montant": "42,50"})
        detail = self.api.report(self.mois["id"], "courses")
        ligne = next(l for l in detail["lignes"] if l["lien"] == "courses")
        self.assertEqual(ligne["reel"], 42.50)

    def test_report_sans_ligne_reliee(self):
        for ligne in base.liste_lignes(self.cnx, self.mois["id"]):
            if ligne["lien"] == "heures":
                base.maj_ligne(self.cnx, ligne["id"], {"lien": ""})
        with self.assertRaises(serveur.ErreurRequete):
            self.api.report(self.mois["id"], "heures")

    def test_mois_au_mauvais_format_refuse(self):
        with self.assertRaises(serveur.ErreurRequete):
            self.api.nouveau_mois(corps={"libelle": "janvier 2026"})

    def test_export_puis_import(self):
        export = self.api.export_json()
        self.assertEqual(len(export["mois"]), 1)

        autre = base.connexion(Path(self.dossier.name) / "autre.db")
        try:
            resultat = serveur.Api(autre).import_json(corps=export)
            self.assertEqual(resultat["importes"], 1)
            restaure = base.detail_mois(autre, resultat["mois_actif_id"])
            origine = base.detail_mois(self.cnx, self.mois["id"])
            self.assertEqual(len(restaure["lignes"]), len(origine["lignes"]))
            self.assertEqual(restaure["recap"]["budget"]["depenses"],
                             origine["recap"]["budget"]["depenses"])
            self.assertEqual(restaure["recap"]["heures"]["minutes"],
                             origine["recap"]["heures"]["minutes"])
            # Un second import ne duplique rien.
            self.assertEqual(serveur.Api(autre).import_json(corps=export)["importes"], 0)
        finally:
            autre.close()

    def test_export_csv(self):
        nom, contenu = serveur.export_csv(self.cnx, self.mois["id"])
        self.assertEqual(nom, "comptes-2026-01.csv")
        self.assertTrue(contenu.startswith("﻿"))
        self.assertIn("TOTAL DÉPENSES", contenu)
        self.assertIn(";", contenu)

    def test_mois_inconnu(self):
        with self.assertRaises(serveur.ErreurRequete) as cas:
            self.api.detail(99999)
        self.assertEqual(cas.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
