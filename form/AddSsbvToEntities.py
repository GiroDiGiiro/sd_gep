from typing import Dict, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QHeaderView, QTableWidgetItem, QMessageBox
from gep_sd.algs.QgisTask.AddSsbvToEntitiesTask import AddSsbvToEntitiesTask
from gep_sd.form.ui.add_ssbv_form import Ui_add_ssbv_form
from qgis.core import QgsProject, QgsVectorLayer,QgsApplication
from gep_sd.form.ProgressDialog import ProgressDialog

class AddSsbvToEntities(QDialog, Ui_add_ssbv_form):
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
        self._populate_comboboxe()

    def connect_signals(self) -> None:
        """Connecte les signaux à leurs slots."""
        self.pb_ok.pressed.connect(self._on_ok)
        self.pb_cancel.pressed.connect(self._on_cancel)
        self.le_ssbv_field.editingFinished.connect(self._populate_table)

    def _populate_comboboxe(self):
        # polygon
        self.cb_ssbv_layer.clear()
        line_layers = []

        for layer in QgsProject.instance().mapLayers().values():
            if not isinstance(layer, QgsVectorLayer):
                continue
            if layer.geometryType() == 2:
                self.cb_ssbv_layer.addItem(layer.name(), layer.id())
                line_layers.append(layer)

        idx = self.cb_ssbv_layer.findText('sousbassin_versant')
        if idx != -1:
            self.cb_ssbv_layer.setCurrentIndex(idx)

        if not line_layers:
            self.cb_ssbv_layer.addItem("")

    def _populate_table(self) -> None:
        """Ajoute une ligne par couche vectorielle : [case] [nom] [case]."""
        self.tableWidget.setRowCount(0)

        for layer in QgsProject.instance().mapLayers().values():
            if not isinstance(layer, QgsVectorLayer):
                continue
            if self.le_ssbv_field.text() not in layer.fields().names():
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
            layer = QgsProject.instance().mapLayer(layer_id)
            only_selected = self.tableWidget.item(row, 2).checkState() == Qt.Checked
            result[layer] = only_selected
        return result

    def _on_ok(self) -> None:
        layers_dict = self.get_layers_dict()
        ssbv_layer = QgsProject.instance().mapLayer(self.cb_ssbv_layer.currentData())
        task = AddSsbvToEntitiesTask(ssbv_layer=ssbv_layer,field_name_ssbv=self.le_ssbv_field.text(),info=layers_dict)
        self.interface.gep_sd_task = task
        dlg = ProgressDialog(task=task, parent=self.interface.mainWindow(), show_subprogressbar=True)
        self.interface.gep_sd_progress = dlg
        QgsApplication.taskManager().addTask(task)
        dlg.show()
        self.accept()

    def _on_cancel(self) -> None:
        """Ferme la boîte de dialogue sans lancer de traitement."""
        self.reject()