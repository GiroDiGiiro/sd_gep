#!/usr/bin/env python3
"""
build.py – Compile automatiquement tous les .ui et .qrc pour le plugin QGIS
Equivalent du Makefile que nous avions conçu.
"""
import os
import subprocess
from pathlib import Path

# ----------------------------
# Configuration
# ----------------------------

# Dossier des sources
SRC_DIR = Path("ressources/raw_ui")

# Dossier de destination
DST_DIR = Path("form/ui")

# Chemin Python pour les imports
PLUGIN_PACKAGE = Path(__file__).resolve().parent.name
IMPORT_FROM = f"{PLUGIN_PACKAGE}.form.ui"

# Binaries
PYUIC = "pyuic5"
PYRCC = "pyrcc5"

# ----------------------------
# Fonctions utilitaires
# ----------------------------

def compile_ui(ui_file: Path, dst_dir: Path):
    dst_dir.mkdir(parents=True, exist_ok=True)
    py_file = dst_dir / f"{ui_file.stem}.py"
    print(f"[UI] {ui_file} -> {py_file}")
    subprocess.run([PYUIC, str(ui_file), "-o", str(py_file), "--import-from", IMPORT_FROM], check=True)


def compile_qrc(qrc_file: Path, dst_dir: Path):
    dst_dir.mkdir(parents=True, exist_ok=True)
    py_file = dst_dir / f"{qrc_file.stem}_rc.py"
    print(f"[QRC] {qrc_file} -> {py_file}")
    subprocess.run([PYRCC, str(qrc_file), "-o", str(py_file)], check=True)


def clean(dst_dir: Path):
    print(f"[CLEAN] Suppression des fichiers générés dans {dst_dir}")
    for f in dst_dir.glob("*.py"):
        f.unlink()
    print("Terminé.")


# ----------------------------
# Main
# ----------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Compile .ui and .qrc files for QGIS plugin.")
    parser.add_argument("action", nargs="?", default="all", choices=["all", "ui", "resources", "clean"],
                        help="Action à exécuter (default: all)")
    args = parser.parse_args()

    if args.action == "clean":
        clean(DST_DIR)
        return

    if args.action in ["all", "ui"]:
        ui_files = list(SRC_DIR.rglob("*.ui"))
        for ui in ui_files:
            compile_ui(ui, DST_DIR)

    if args.action in ["all", "resources"]:
        qrc_files = list(SRC_DIR.glob("*.qrc"))
        for qrc in qrc_files:
            compile_qrc(qrc, DST_DIR)


if __name__ == "__main__":
    main()