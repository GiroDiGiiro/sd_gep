from typing import Optional

from PyQt5.QtWidgets import QDialog
from gep_sd.algs.QgisTask.GetStreetAndTownTask import GetStreetAndTownTask
from gep_sd.form.ProgressDialog import ProgressDialog
from gep_sd.form.ui.get_name_street_and_town import Ui_get_name_street_and_town
from qgis.core import QgsProject, QgsVectorLayer, QgsApplication

WFS_ROUTES_URL = 'https://data.geopf.fr/annexes/ressources/wfs/topographie.xml'
WFS_COMMUNES_URL = 'https://data.geopf.fr/annexes/ressources/wfs/administratif.xml'


class GetStreetAndTown(QDialog, Ui_get_name_street_and_town):

    def __init__(self, interface, parent: Optional[QDialog] = None) -> None:
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.interface = interface
        self.finish_ui()
        self.connect_signals()

    def connect_signals(self) -> None:
        self.pb_ok.clicked.connect(self._on_ok)
        self.pb_cancel.clicked.connect(self._on_cancel)
        for cb in (self.cb_point_layer, self.cb_line_layer, self.cb_polygone_layer):
            cb.currentIndexChanged.connect(self._populate_secondary_cb)

    def finish_ui(self) -> None:
        self.le_route_url.setText(WFS_ROUTES_URL)
        self.le_commune_url.setText(WFS_COMMUNES_URL)

        self._populate_layer_cb(self.cb_point_layer, 0, 'regard')
        self._populate_layer_cb(self.cb_line_layer, 1,'reseau')
        self._populate_layer_cb(self.cb_polygone_layer, 2,'ouvrage_polygonal')
        self._populate_secondary_cb()

    # ---------- couches ----------
    def _populate_layer_cb(self, combo, geom_type: int, default :str) -> None:
        combo.clear()
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer) and layer.geometryType() == geom_type:
                combo.addItem(layer.name(), layer.id())
        idx = combo.findText(default)
        if idx != -1:
            combo.setCurrentIndex(idx)

    def _get_layer(self, combo) -> Optional[QgsVectorLayer]:
        layer_id = combo.currentData()
        return QgsProject.instance().mapLayer(layer_id) if layer_id else None

    # ---------- champs ----------
    def _populate_secondary_cb(self) -> None:
        point = self._get_layer(self.cb_point_layer)
        line = self._get_layer(self.cb_line_layer)
        polygon = self._get_layer(self.cb_polygone_layer)

        layers = [l for l in (point, line, polygon) if l is not None]
        if layers:
            communs = sorted(set.intersection(*[set(l.fields().names()) for l in layers]))
        else:
            communs = []
        noms_line = line.fields().names() if line else []

        self._fill_field_cb(self.cb_field_rue, communs, 'nom_rue')
        self._fill_field_cb(self.cb_field_rue2, noms_line, 'nom_rue2')
        self._fill_field_cb(self.cb_field_commune, communs, 'commune')

    @staticmethod
    def _fill_field_cb(combo, names, default: str) -> None:
        combo.clear()
        combo.addItems(names)
        idx = combo.findText(default)
        if idx != -1:
            combo.setCurrentIndex(idx)

    # ---------- boutons ----------
    def _on_ok(self) -> None:
        # récupérer les layers
        point_layer = self._get_layer(self.cb_point_layer)
        line_layer = self._get_layer(self.cb_line_layer)
        polygon_layer = self._get_layer(self.cb_polygone_layer)

        # récupérer le nom des champs
        field_name_rue = self.cb_field_rue.currentText()
        field_name_rue2 = self.cb_field_rue2.currentText()
        field_name_commune = self.cb_field_commune.currentText()

        # récupérer les urls des couches wfs
        url_rue = self.le_route_url.text()
        url_commune = self.le_commune_url.text()

        task = GetStreetAndTownTask(point_layer, line_layer, polygon_layer,
                                         field_name_rue, field_name_rue2, field_name_commune,
                                         url_rue, url_commune)
        self.interface.gep_sd_task = task  # référence forte persistante
        self.interface.gep_sd_task = task
        dlg = ProgressDialog(task=task, parent=self.interface.mainWindow(), show_subprogressbar=True)
        self.interface.gep_sd_progress = dlg
        QgsApplication.taskManager().addTask(task)
        dlg.show()
        self.accept()

    def _on_cancel(self) -> None:
        """Ferme la boîte de dialogue sans lancer de traitement."""
        self.reject()
