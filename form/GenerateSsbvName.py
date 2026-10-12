from typing import Optional

from PyQt5.QtWidgets import QDialog, QMessageBox
from gep_sd.algs.secondary.generate_ssbv_name import generate_ssbv_name
from gep_sd.form.ui.generate_ssbv_name import Ui_generate_ssbv_name
from qgis.core import QgsProject, QgsVectorLayer


class GenerateSsbvName(QDialog, Ui_generate_ssbv_name):

    def __init__(self, interface, parent: Optional[QDialog] = None) -> None:
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.interface = interface

        self.finish_ui()
        self.connect_signals()

    def connect_signals(self) -> None:
        """Connecte les signaux leurs slots."""
        self.pb_ok.pressed.connect(self._on_ok)
        self.pb_cancel.pressed.connect(self._on_cancel)
        self.cb_ssbv_layer.currentIndexChanged.connect(self._populate_combo_field)
        self.cb_regard_layer.currentIndexChanged.connect(self._populate_combo_field)

    def finish_ui(self) -> None:
        """Termine la construction de l'UI."""
        self._populate_combo_layer()
        self._populate_combo_field()

    def _populate_combo_layer(self) -> None:
        # ponctuel
        self.cb_regard_layer.clear()
        point_layer = []

        for layer in QgsProject.instance().mapLayers().values():
            if not isinstance(layer, QgsVectorLayer):
                continue
            if layer.geometryType() == 0:
                self.cb_regard_layer.addItem(layer.name(), layer)
                point_layer.append(layer)

        idx = self.cb_regard_layer.findText('regard')
        if idx != -1:
            self.cb_regard_layer.setCurrentIndex(idx)

        if not point_layer:
            self.cb_regard_layer.addItem("")

        # polygon
        self.cb_ssbv_layer.clear()
        polygon_layers = []

        for layer in QgsProject.instance().mapLayers().values():
            if not isinstance(layer, QgsVectorLayer):
                continue
            if layer.geometryType() == 2:
                self.cb_ssbv_layer.addItem(layer.name(), layer)
                polygon_layers.append(layer)

        idx = self.cb_ssbv_layer.findText('sousbassin_versant')
        if idx != -1:
            self.cb_ssbv_layer.setCurrentIndex(idx)

        if not polygon_layers:
            self.cb_ssbv_layer.addItem("")

    def _populate_combo_field(self) -> None:
        # champ nom de la couche ssbv (le champs qui va être renseigné)
        self.cb_field_ssbv_name.clear()
        ssbv_l_fields = self.cb_ssbv_layer.currentData().fields()
        for field in ssbv_l_fields:
            self.cb_field_ssbv_name.addItem(field.name(), ssbv_l_fields.lookupField(f'{field.name()}'))

        idx_fid = ssbv_l_fields.lookupField('nom')
        if idx_fid != -1:
            self.cb_field_ssbv_name.setCurrentIndex(idx_fid)

        # champ reagrd_id de la couche ssbv (le champs pour faire la jointure)
        self.cb_field_ssbv_regard_id.clear()
        ssbv_l_fields = self.cb_ssbv_layer.currentData().fields()
        for field in ssbv_l_fields:
            self.cb_field_ssbv_regard_id.addItem(field.name(), ssbv_l_fields.lookupField(f'{field.name()}'))

        idx_fid = ssbv_l_fields.lookupField('regard_id')
        if idx_fid != -1:
            self.cb_field_ssbv_regard_id.setCurrentIndex(idx_fid)

        # champ code de la couche regard (le champ qui va être copié)
        self.cb_field_regard_code.clear()
        ssbv_l_fields = self.cb_regard_layer.currentData().fields()
        for field in ssbv_l_fields:
            self.cb_field_regard_code.addItem(field.name(), ssbv_l_fields.lookupField(f'{field.name()}'))

        idx_fid = ssbv_l_fields.lookupField('code')
        if idx_fid != -1:
            self.cb_field_regard_code.setCurrentIndex(idx_fid)

    def _on_ok(self):
        ssbv_layer = self.cb_ssbv_layer.currentData()
        regard_layer = self.cb_regard_layer.currentData()

        regard_id_field = self.cb_field_ssbv_regard_id.currentData()
        nom_field = self.cb_field_ssbv_name.currentData()
        code_field = self.cb_field_regard_code.currentData()

        succes, msg = generate_ssbv_name(ssbv_layer=ssbv_layer,
                                         regard_layer=regard_layer,
                                         regard_id_field=regard_id_field,
                                         nom_field=nom_field,
                                         code_field=code_field)

        if succes:
            QMessageBox.information(self, "Succès", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Erreur", msg)
            self.reject()

    def _on_cancel(self):
        self.close()
