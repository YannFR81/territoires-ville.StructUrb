"""Tests de la ligne de commande (python -m structurb)."""

import os
import subprocess
import sys
from pathlib import Path

from structurb.cli import main

RACINE_PAQUET = Path(__file__).resolve().parents[1]

ETUDE_PAVES = [
    "etude",
    "--structure", "Pavés/GNT",
    "--voie", "desserte",
    "--trafic", "12",
    "--croissance", "2",
    "--duree", "20",
    "--pf", "PF2",
    "--station", "Toulouse",
    "--hiver", "HRNE",
    "--agglo", "moyenne",
    "--pente", "0.5",
]


def test_structures_par_voie(capsys):
    assert main(["structures", "--voie", "desserte"]) == 0
    sortie = capsys.readouterr().out
    assert "Pavés/GNT" in sortie and "ES/GNT" in sortie
    assert "Enrobés /GB3/GB3" not in sortie and "Enrobés/GB3/GB3" not in sortie  # autres types de voie


def test_stations(capsys):
    assert main(["stations"]) == 0
    sortie = capsys.readouterr().out
    assert sortie.count("\n") >= 84
    assert "Ambérieu" in sortie and "Paris le Bourget" in sortie


def test_etude_paves(capsys):
    assert main(ETUDE_PAVES) == 0
    sortie = capsys.readouterr().out
    assert "20 849" in sortie  # NE
    assert "30 000" in sortie  # NE théorique
    assert "Q1" in sortie and "Q2" in sortie
    assert "36" in sortie  # indice de gel de référence


def test_etude_export_html(tmp_path, capsys):
    cible = tmp_path / "note.html"
    assert main(ETUDE_PAVES + ["--html", str(cible), "--titre", "Rue des Lilas"]) == 0
    html = cible.read_text(encoding="utf-8")
    assert "Rue des Lilas" in html and "<svg" in html


def test_structure_variantes_et_inconnue(capsys):
    # Enrobés/GNT existe en deux variantes (positions 1 et 6) ; seule la position 1 sert en desserte
    assert main([
        "etude", "--structure", "Enrobés/GNT", "--voie", "desserte",
        "--trafic", "5", "--croissance", "2", "--duree", "20", "--pf", "PF2",
    ]) == 0
    assert "index 1" in capsys.readouterr().out
    # Structure absente pour ce type de voie
    assert main(["etude", "--structure", "Enrobés/GNT", "--voie", "trafic_lourd",
                 "--trafic", "5", "--croissance", "2", "--duree", "20", "--pf", "PF2"]) == 2
    assert "type de voie" in capsys.readouterr().err
    assert main(["etude", "--structure", "Inexistante", "--voie", "desserte",
                 "--trafic", "10", "--croissance", "2", "--duree", "20", "--pf", "PF2"]) == 2
    assert "inconnue" in capsys.readouterr().err.lower()


def test_index_explicite(capsys):
    assert main([
        "etude", "--index", "49", "--voie", "desserte", "--trafic", "12",
        "--croissance", "2", "--duree", "20", "--pf", "PF2",
    ]) == 0
    assert "Pavés/GNT" in capsys.readouterr().out


def test_module_executable():
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run(
        [sys.executable, "-m", "structurb", "--help"],
        cwd=RACINE_PAQUET, capture_output=True, text=True, encoding="utf-8", env=env,
    )
    assert r.returncode == 0
    assert "etude" in r.stdout
