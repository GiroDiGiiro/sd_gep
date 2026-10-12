from typing import Optional, List

from PyQt5.QtWidgets import QDialog, QListWidgetItem, QMessageBox
from gep_sd.algs.secondary.get_and_verif_canalisation import get_and_verif_canalisation
from gep_sd.form.ui.get_and_verif_canalisation_form import Ui_get_and_verif_canalisation_form
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsProject, QgsVectorLayer


class GetAndVerifCanalisation(QDialog, Ui_get_and_verif_canalisation_form):

    def __init__(self, interface, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.interface = interface

        self.layer: Optional[QgsVectorLayer] = None
        self.pt_layers: Optional[List[QgsVectorLayer]] = []

        self.finish_ui()
        self.connect_signals()

        self.pb_ok.pressed.connect(self._on_ok)
        self.pb_cancel.pressed.connect(self._on_cancel)

    def finish_ui(self):
        self._populate_combo()

    def connect_signals(self):
        self.cb_point_layer.currentIndexChanged.connect(self._on_point_changed)
        self.cb_line_layer.currentIndexChanged.connect(self._on_line_changed)

    def _populate_combo(self):
        """Peuple les combobox avec les couches ponctuelles et linéaires du projet."""
        # ponctuel
        self.cb_point_layer.clear()
        line_layers = []

        for layer in QgsProject.instance().mapLayers().values():
            if not isinstance(layer, QgsVectorLayer):
                continue
            if layer.geometryType() == 0:
                self.cb_point_layer.addItem(layer.name(), layer.id())
                line_layers.append(layer)

        if not line_layers:
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

        if not line_layers:
            self.cb_line_layer.addItem("")

        self._on_line_changed()
        self._on_point_changed()

    def _on_point_changed(self):
        self.cb_regard_id.clear()
        pt_l_fields = QgsProject.instance().mapLayer(self.cb_point_layer.currentData()).fields()
        for field in pt_l_fields:
            self.cb_regard_id.addItem(field.name(), pt_l_fields.lookupField(f'{field.name()}'))

        idx_fid = pt_l_fields.lookupField('fid')
        if idx_fid != -1:
            self.cb_regard_id.setCurrentIndex(idx_fid)

    def _on_line_changed(self):
        self.cb_reseau_am.clear()
        self.cb_reseau_av.clear()
        line_layer_fields = QgsProject.instance().mapLayer(self.cb_line_layer.currentData()).fields()
        for field in line_layer_fields:
            self.cb_reseau_am.addItem(field.name(), line_layer_fields.lookupField(f'{field.name()}'))
            self.cb_reseau_av.addItem(field.name(), line_layer_fields.lookupField(f'{field.name()}'))

        idx_fid = line_layer_fields.lookupField('regard_amont_id')
        if idx_fid != -1:
            self.cb_reseau_am.setCurrentIndex(idx_fid)

        idx_fid = line_layer_fields.lookupField('regard_aval_id')
        if idx_fid != -1:
            self.cb_reseau_av.setCurrentIndex(idx_fid)

    def _on_ok(self):
        layer_id = self.cb_point_layer.currentData()
        point_layer: QgsVectorLayer = QgsProject.instance().mapLayer(layer_id)

        layer_id = self.cb_line_layer.currentData()
        line_layer: QgsVectorLayer = QgsProject.instance().mapLayer(layer_id)

        errors = get_and_verif_canalisation(layer=line_layer, pt_layers=[point_layer],
                                            idx_fid=self.cb_regard_id.currentData(),
                                            idx_am=self.cb_reseau_am.currentData(),
                                            idx_av=self.cb_reseau_av.currentData(),
                                            show_error=self.chk_add_errors.isChecked())

        msg = f'{len(errors)} erreurs trouvées sur la couche {line_layer.name()}' if errors else 'Aucune erreur trouvée. Bravo !'
        QMessageBox.information(self, "Info", msg)
        self.accept()

    def _on_cancel(self):
        self.close()
