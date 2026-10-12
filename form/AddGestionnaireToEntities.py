from typing import Dict, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QHeaderView, QTableWidgetItem, QMessageBox
from gep_sd.algs.secondary.add_gestionnaire_to_entities import add_gestionnaire_to_entities
from qgis.core import QgsProject, QgsVectorLayer

from gep_sd.form.ui.add_gestionnaire_form import Ui_add_gestionnaire_form


class AddGestionnaireToEntities(QDialog, Ui_add_gestionnaire_form):
    def __init__(self, interface, parent: Optional[QDialog] = None) -> None:
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.interface = interface

        self.finish_ui()
        self.connect_signals()

    def finish_ui(self) -> None:
        """Termine la construction de l'UI."""
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._populate_table()

    def connect_signals(self) -> None:
        """Connecte les signaux à leurs slots."""
        self.pb_ok.pressed.connect(self._on_ok)
        self.pb_cancel.pressed.connect(self._on_cancel)
        self.le_gestionnaire_field.editingFinished.connect(self._populate_table)

    def _populate_table(self) -> None:
        """Ajoute une ligne par couche vectorielle : [case] [nom] [case]."""
        self.tableWidget.setRowCount(0)

        for layer in QgsProject.instance().mapLayers().values():
            if not isinstance(layer, QgsVectorLayer):
                continue
            if self.le_gestionnaire_field.text() not in layer.fields().names():
                continue

            row = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row)

            # Colonne 0 : "je veux traiter cette couche"
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Unchecked)
            item.setCheckState(Qt.Checked)
            self.tableWidget.setItem(row, 0, item)

            # Colonne 1 : nom de la couche (non éditable), l'id est stocké dans la cellule
            name_item = QTableWidgetItem(layer.name())
            name_item.setFlags(Qt.ItemIsEnabled)
            name_item.setData(Qt.UserRole, layer.id())
            self.tableWidget.setItem(row, 1, name_item)

            # Colonne 2 : "seulement les entités sélectionnées"
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Unchecked)
            self.tableWidget.setItem(row, 2, item)

            table = self.tableWidget
            height = table.horizontalHeader().sizeHint().height() + 2 * table.frameWidth()
            for row in range(table.rowCount()):
                height += table.rowHeight(row)
            # Si une barre de défilement horizontale est nécessaire, on la compte aussi
            if table.horizontalScrollBar().isVisible():
                height += table.horizontalScrollBar().height()
            table.setMaximumHeight(height)
            # table.setMaximumHeight(min(height, 400))

    def get_layers_dict(self) -> Dict[str, bool]:
        """Retourne {layer_id: seulement_selection} pour les couches cochées."""
        result: Dict[str, bool] = {}
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.item(row, 0).checkState() != Qt.Checked:
                continue
            layer_id = self.tableWidget.item(row, 1).data(Qt.UserRole)
            only_selected = self.tableWidget.item(row, 2).checkState() == Qt.Checked
            result[layer_id] = only_selected
        return result

    def _on_ok(self) -> None:
        layers_dict = self.get_layers_dict()
        succes, msg = add_gestionnaire_to_entities(self.le_gestionnaire.text(),self.le_gestionnaire_field.text(), layers_dict)
        if succes:
            QMessageBox.information(self, "Succès", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Erreur", msg)
            self.reject()

    def _on_cancel(self) -> None:
        """Ferme la boîte de dialogue sans lancer de traitement."""
        self.close()