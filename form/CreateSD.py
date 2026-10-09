import os
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import QDialog, QMessageBox, QFileDialog
from gep_sd.form.ui.create_sd import Ui_create_sd_form
from gep_sd.utils.is_local_path import is_local_path
from gep_sd.algs.secondary.create_sd import create_sd

DB_NAME = 'projets'
SCHEMA_NAME = 'gep_ref'

class CreateSD(QDialog, Ui_create_sd_form):
    """Boite de dialogue de configuration et de lancement de la création d'un schéma directeur GEP"""

    def __init__(self, interface, parent: Optional[QDialog] = None) -> None:
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.interface = interface

        self.finish_ui()
        self.connect_signals()

    def finish_ui(self) -> None:
        """Termine la construction de l'UI."""
        self.le_db_name.setText(DB_NAME)
        self.le_schema_name.setText(SCHEMA_NAME)
        pass
        # self.textBrowser.setHtml(HELP_TEXT_POST_CANOE_TO_GEP)

    def connect_signals(self) -> None:
        """Connecte les signaux leurs slots."""
        self.pb_project_path.pressed.connect(self._on_project_path)
        self.pb_ok.pressed.connect(self._on_ok)
        self.pb_cancel.pressed.connect(self._on_cancel)

    def _on_project_path(self) -> None:
        """ Ouvre un QFileDialog pour séléctionner un Répertoire"""
        folder = QFileDialog.getExistingDirectory(self)
        folder = folder + "/"
        self.le_project_path.setText(folder)

    def _verif(self, project_name: str, project_path: Path) -> bool:

        if project_name == '':
            message = "Merci de choisir un nom pour votre projet"
            QMessageBox.warning(self, "Warning", message)
            return False
        if project_path == '':
            message = "Merci de choisir un dossier de sauvegarde pour votre projet."
            QMessageBox.warning(self, "Warning", message)
            return False

        if len(os.listdir(project_path)) > 0:
            message = "Merci de choisir un nouveau dossier de sauvegarde vide pour votre projet. <br> Des fichiers ont été identifiés dans le dossier choisi"
            QMessageBox.warning(self, "Warning", message)
            return False

        # if not is_local_path(project_path):
        #     message = " Merci de choisir un dossier de travail sur votre disque dur"
        #     QMessageBox.warning(self, "Warning", message)
        #     return False

        return True

    def _on_ok(self) -> None:

        project_name = self.le_project_name.text()
        project_path = self.le_project_path.text()
        db_name = self.le_db_name.text()
        schema_name =self.le_schema_name.text()
        if not self._verif(project_name, project_path):
            return

        success = create_sd(project_name, project_path,db_name,schema_name)

        self.close()


    def _on_cancel(self) -> None:
        """Ferme la boîte de dialogue sans lancer de traitement."""
        self.close()
