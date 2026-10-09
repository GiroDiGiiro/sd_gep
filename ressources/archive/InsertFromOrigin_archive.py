from PyQt5.QtWidgets import QDialog, QHeaderView, QTableWidgetItem, QMessageBox
from gep_sd.form.ui.insert_from_origin_form import Ui_insert_from_origin_form
from qgis.core import QgsProject, QgsVectorLayer

class InsertFromOrigin(QDialog, Ui_insert_from_origin_form):
    def __init__(self, interface, parent: Optional[QDialog] = None) -> None:
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.interface = interface

        self.tables = [self.tw_regard_origin, self.tw_reseau_origin, self.tw_ouvrage_polygonal_origin,
                       self.tw_ssbv_origin, self.tw_bv_origin, self.tw_surface_raccordee_origin]
        self.finish_ui()
        self.connect_signals()

    def finish_ui(self) -> None:
        """Termine la construction de l'UI."""
        for tablewidget in self.tables:
            self._styling_table(tablewidget)

    def _styling_table(self, tablewidget) -> None:
        header = tablewidget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

    def connect_signals(self) -> None:
        # Signaux des checkBox
        self.chk_regard.toggled.connect(on_chk_regard_toggled)
        self.chk_reseau.toggled.connect(on_chk_reseau_toggled)
        self.chk_ouvrage_polygonal.toggled.connect(on_chk_ouvrage_polygonal_toggled)
        self.chk_ssbv.toggled.connect(on_chk_ssbv_toggled)
        self.chk_bv.toggled.connect(on_chk_bv_toggled)
        self.chk_surface_raccordee.toggled.connect(on_chk_surface_raccordee_toggled)

        # Signaux des combobox
        self.cb_regard_origin.currentIndexChanged.connect(on_cb_regard_index_changed)
        self.cb_reseau_origin.currentIndexChanged.connect(on_cb_reseau_index_changed)
        self.cb_ouvrage_polygonal_origin.currentIndexChanged.connect(on_cb_ouvrage_polygonal_index_changed)
        self.cb_ssbv_origin.currentIndexChanged.connect(on_cb_ssbv_index_changed)
        self.cb_bv_origin.currentIndexChanged.connect(on_cb_bv_index_changed)
        self.cb_surface_raccordee_origin.currentIndexChanged.connect(on_cb_surface_raccordee_index_changed)

    def populate_cb_regard_origin(self):
        for layer in QgsProject.instance().mapLayers().values():
            if not isinstance(layer, QgsVectorLayer):
                continue
            if layer.geometryType() == 0:
                self.cb_regard_origin.addItem(layer.name(), layer)

    def populate_cb_reseau_origin(self):
        for layer in QgsProject.instance().mapLayers().values():
            if not isinstance(layer, QgsVectorLayer):
                continue
            if layer.geometryType() == 1:
                self.cb_reseau_origin.addItem(layer.name(), layer)

    def populate_cb_ouvrage_polygonal_origin(self):
        for layer in QgsProject.instance().mapLayers().values():
            if not isinstance(layer, QgsVectorLayer):
                continue
            if layer.geometryType() == 2:
                self.cb_ouvrage_polygonal_origin.addItem(layer.name(), layer)

    def populate_cb_ssbv_origin(self):
        for layer in QgsProject.instance().mapLayers().values():
            if not isinstance(layer, QgsVectorLayer):
                continue
            if layer.geometryType() == 2:
                self.cb_ssbv_origin.addItem(layer.name(), layer)

    def populate_cb_bv_origin(self):
        for layer in QgsProject.instance().mapLayers().values():
            if not isinstance(layer, QgsVectorLayer):
                continue
            if layer.geometryType() == 2:
                self.cb_bv_origin.addItem(layer.name(), layer)

    def populate_cb_surface_raccordee_origin(self):
        for layer in QgsProject.instance().mapLayers().values():
            if not isinstance(layer, QgsVectorLayer):
                continue
            if layer.geometryType() == 2:
                self.cb_surface_raccordee_origin.addItem(layer.name(), layer)


