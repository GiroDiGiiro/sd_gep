from typing import Optional

from PyQt5.QtWidgets import QDialog, QMessageBox
from gep_sd.algs.secondary.generate_code import generate_code
from gep_sd.form.ui.generate_code import Ui_generate_code
from qgis.core import QgsProject, QgsVectorLayer

DB_NAME = 'projets'
SCHEMA_NAME = 'gep_ref'

class GenerateCode(QDialog, Ui_generate_code):


    def __init__(self, interface, parent: Optional[QDialog] = None) -> None:
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.interface = interface

        self.finish_ui()
        self.connect_signals()

    def finish_ui(self) -> None:
        """Termine la construction de l'UI."""
        self._populate_combo()
        self.le_bd_name.setText(DB_NAME)
        self.le_schema_name.setText(SCHEMA_NAME)
        # self.textBrowser.setHtml(HELP_TEXT_POST_CANOE_TO_GEP)

    def connect_signals(self) -> None:
        """Connecte les signaux leurs slots."""
        self.pb_ok.pressed.connect(self._on_ok)
        self.pb_cancel.pressed.connect(self._on_cancel)

    def _populate_combo(self):
        """Peuple les combobox avec les couches du projet."""
        # ponctuel
        self.cb_point_layer.clear()
        point_layer = []

        for layer in QgsProject.instance().mapLayers().values():
            if not isinstance(layer, QgsVectorLayer):
                continue
            if layer.geometryType() == 0:
                self.cb_point_layer.addItem(layer.name(), layer.id())
                point_layer.append(layer)

        idx = self.cb_point_layer.findText('regard')
        if idx != -1:
            self.cb_point_layer.setCurrentIndex(idx)

        if not point_layer:
            self.cb_point_layer.addItem("")

        # line
        self.cb_line_layer.clear()
        line_layers = []

        for layer in QgsProject.instance().mapLayers().values():
            if not isinstance(layer, QgsVectorLayer):
                continue
            if layer.geometryType() == 1:
                self.cb_line_layer.addItem(layer.name(), layer.id())
                line_layers.append(layer)

        idx = self.cb_line_layer.findText('reseau')
        if idx != -1:
            self.cb_line_layer.setCurrentIndex(idx)

        if not line_layers:
            self.cb_line_layer.addItem("")

        # polygon
        self.cb_polygon_layer.clear()
        polygon_layers = []

        for layer in QgsProject.instance().mapLayers().values():
            if not isinstance(layer, QgsVectorLayer):
                continue
            if layer.geometryType() == 2:
                self.cb_polygon_layer.addItem(layer.name(), layer.id())
                polygon_layers.append(layer)

        idx = self.cb_polygon_layer.findText('ouvrage_polygonal')
        if idx != -1:
            self.cb_polygon_layer.setCurrentIndex(idx)

        if not polygon_layers:
            self.cb_polygon_layer.addItem("")

    def _on_ok(self) -> None:

        point_layer: QgsVectorLayer = QgsProject.instance().mapLayer(self.cb_point_layer.currentData())
        line_layer: QgsVectorLayer = QgsProject.instance().mapLayer(self.cb_line_layer.currentData())
        polygon_layer: QgsVectorLayer = QgsProject.instance().mapLayer(self.cb_polygon_layer.currentData())
        db_name = self.le_bd_name.text()
        schema_name = self.le_schema_name.text()

        succes, msg = generate_code(point_layer=point_layer,
                                    line_layer=line_layer,
                                    polygon_layer=polygon_layer,
                                    db_name=db_name,
                                    schema_name=schema_name)

        if succes:
            QMessageBox.information(self, "Succès", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Erreur", msg)
            self.reject()

    def _on_cancel(self) -> None:
        """Ferme la boîte de dialogue sans lancer de traitement."""
        self.close()
