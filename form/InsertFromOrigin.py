# -*- coding: utf-8 -*-
"""Logique du formulaire ``Ui_insert_from_origin_form`` (PyQGIS / PyQt5).

Le formulaire permet d'insérer les entités de couches « sources » dans des
couches « cibles » de même type de géométrie. Il fonctionne en deux pages :

1. Appariement des couches source -> cible (une paire par ligne de tableau).
2. Pour chaque paire, correspondance des champs source -> champs cible
   (créer le champ, l'ignorer, ou le copier vers un champ existant compatible).
"""
from typing import Dict, List, Optional

from gep_sd.algs.secondary.insert_from_origin import insert_from_origin
from gep_sd.utils.field_mapping import FieldMapping, LayerResult
from gep_sd.form.ui.insert_from_origin_form2 import Ui_insert_from_origin_form
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QComboBox, QDialog, QHeaderView, QMessageBox, QTableWidget,
    QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)
from qgis.core import Qgis, QgsApplication, QgsField, QgsFields, QgsProject, QgsVectorLayer
from qgis.gui import QgsMapLayerComboBox

# Libellés affichés dans les combobox de correspondance des champs.
CREATE_FIELD_LABEL: str = "Ajouter à la couche cible"
NO_ACTION_LABEL: str = "Ne pas ajouter à la couche cible"

# Icône associée à chaque type de champ QVariant (thème QGIS courant).
FIELD_ICONS: Dict[int, QIcon] = {
    QVariant.String: QgsApplication.getThemeIcon("/mIconFieldText.svg"),

    QVariant.Int: QgsApplication.getThemeIcon("/mIconFieldInteger.svg"),
    QVariant.UInt: QgsApplication.getThemeIcon("/mIconFieldInteger.svg"),
    QVariant.LongLong: QgsApplication.getThemeIcon("/mIconFieldInteger.svg"),
    QVariant.ULongLong: QgsApplication.getThemeIcon("/mIconFieldInteger.svg"),

    QVariant.Double: QgsApplication.getThemeIcon("/mIconFieldFloat.svg"),

    QVariant.Date: QgsApplication.getThemeIcon("/mIconFieldDate.svg"),
    QVariant.DateTime: QgsApplication.getThemeIcon("/mIconFieldDateTime.svg"),
    QVariant.Time: QgsApplication.getThemeIcon("/mIconFieldTime.svg"),

    QVariant.Bool: QgsApplication.getThemeIcon("/mIconFieldBool.svg"),
}


class InsertFromOrigin(QDialog, Ui_insert_from_origin_form):
    """Boîte de dialogue d'insertion d'entités depuis des couches d'origine.

    Attributes:
        interface: Interface QGIS (``QgisInterface``) fournie à la création.
        layer_pairs: Paires validées ``{couche_source: couche_cible}``.
        result: Résultat final (voir :meth:`get_result`).
    """

    def __init__(self, interface, parent: Optional[QWidget] = None) -> None:
        """Initialise le formulaire et connecte les signaux des deux pages.

        Args:
            interface: Interface QGIS (``QgisInterface``).
            parent: Widget parent de la boîte de dialogue (optionnel).
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.interface = interface

        self.layer_pairs: Dict[QgsVectorLayer, QgsVectorLayer] = {}  # {layer_source: layer_cible}
        self.result: Dict[QgsVectorLayer, LayerResult] = {}  # résultat final (voir get_result)
        self._tables: Dict[QgsVectorLayer, QTableWidget] = {}  # {layer_source: QTableWidget}

        # --- Page 1 ---
        self.tw_paired_layer.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.pd_add.clicked.connect(self.add_pair_row)
        self.pb_next.clicked.connect(self.go_next)
        self.pb_cancel.clicked.connect(self.reject)
        self.pb_remove.clicked.connect(self.remove_selected_rows)
        self.add_pair_row()  # une première ligne vide est proposée d'office

        # --- Page 2 ---
        self.pb_previous.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.pb_ok.clicked.connect(self.accept_form)

        # frame_tablewidget n'a pas de layout dans le .ui : on le crée ici
        if self.frame_tablewidget.layout() is None:
            QVBoxLayout(self.frame_tablewidget)

    # ------------------------------------------------------------------ page 1
    @staticmethod
    def _make_layer_combo() -> QgsMapLayerComboBox:
        """Crée une combobox de sélection de couche (couches avec géométrie).

        Returns:
            Une ``QgsMapLayerComboBox`` avec une entrée vide sélectionnée.
        """
        cb = QgsMapLayerComboBox()
        cb.setFilters(Qgis.LayerFilter.HasGeometry)
        cb.setShowCrs(True)
        cb.setAllowEmptyLayer(True)
        cb.setCurrentIndex(0)  # couche vide par défaut
        return cb

    @staticmethod
    def _update_target_combo(
        src_layer: Optional[QgsVectorLayer], dst_combo: QgsMapLayerComboBox
    ) -> None:
        """Ne propose en cible que les couches de même type de géométrie que la source.

        La couche source elle-même est également exclue. Si aucune source
        n'est choisie, la combobox cible est désactivée.

        Args:
            src_layer: Couche source sélectionnée, ou ``None`` si vide.
            dst_combo: Combobox des couches cibles à mettre à jour.
        """
        if src_layer is None:
            dst_combo.setExceptedLayerList([])
            dst_combo.setCurrentIndex(0)
            dst_combo.setEnabled(False)  # on choisit d'abord la source
            return

        geom_type = src_layer.geometryType()  # Point / Line / Polygon
        # Couches à masquer : géométrie différente, ou la source elle-même
        excluded = [
            layer for layer in QgsProject.instance().mapLayers().values()
            if isinstance(layer, QgsVectorLayer)
               and (layer.geometryType() != geom_type or layer == src_layer)
        ]
        dst_combo.setExceptedLayerList(excluded)
        dst_combo.setCurrentIndex(0)  # remet à vide pour éviter une cible devenue invalide
        dst_combo.setEnabled(True)

    def add_pair_row(self) -> None:
        """Ajoute une ligne (combobox source + combobox cible) au tableau des paires."""
        row = self.tw_paired_layer.rowCount()
        self.tw_paired_layer.insertRow(row)

        src_combo = self._make_layer_combo()
        dst_combo = self._make_layer_combo()
        self.tw_paired_layer.setCellWidget(row, 0, src_combo)
        self.tw_paired_layer.setCellWidget(row, 1, dst_combo)

        # la cible dépend de la source choisie sur la même ligne
        src_combo.layerChanged.connect(self.on_source_layer_changed)
        self._update_target_combo(src_combo.currentLayer(), dst_combo)

    def on_source_layer_changed(self, layer: Optional[QgsVectorLayer]) -> None:
        """Slot appelé quand la couche source d'une ligne change.

        Met à jour la combobox cible de la même ligne.

        Args:
            layer: Nouvelle couche source sélectionnée (``None`` si vide).
        """
        src_combo = self.sender()  # combobox à l'origine du signal
        row = self._row_of_source_combo(src_combo)
        if row < 0:
            return
        dst_combo = self.tw_paired_layer.cellWidget(row, 1)
        self._update_target_combo(layer, dst_combo)

    def _row_of_source_combo(self, src_combo: QgsMapLayerComboBox) -> int:
        """Retrouve la ligne du tableau contenant une combobox source donnée.

        Args:
            src_combo: Combobox de la colonne « source » à localiser.

        Returns:
            L'indice de la ligne, ou ``-1`` si la combobox est introuvable.
        """
        for row in range(self.tw_paired_layer.rowCount()):
            if self.tw_paired_layer.cellWidget(row, 0) is src_combo:
                return row
        return -1

    def remove_selected_rows(self) -> None:
        """Supprime du tableau les lignes actuellement sélectionnées."""
        # Tri décroissant : supprimer de bas en haut évite de décaler les indices
        rows = sorted({i.row() for i in self.tw_paired_layer.selectedIndexes()}, reverse=True)
        for r in rows:
            self.tw_paired_layer.removeRow(r)

    def collect_pairs(self) -> Optional[Dict[QgsVectorLayer, QgsVectorLayer]]:
        """Lit le tableau et valide les paires de couches.

        Les lignes entièrement vides sont ignorées. Un message d'avertissement
        est affiché à la première erreur rencontrée (paire incomplète, source
        identique à la cible, source utilisée plusieurs fois, aucune paire).

        Returns:
            ``{layer_source: layer_cible}`` si tout est valide, ``None`` sinon.
        """
        pairs: Dict[QgsVectorLayer, QgsVectorLayer] = {}
        for row in range(self.tw_paired_layer.rowCount()):
            src = self.tw_paired_layer.cellWidget(row, 0).currentLayer()
            dst = self.tw_paired_layer.cellWidget(row, 1).currentLayer()
            if src is None and dst is None:
                continue  # ligne vide ignorée
            if src is None or dst is None:
                self._warn(f"Ligne {row + 1} : couche source ou cible manquante.")
                return None
            if src == dst:
                self._warn(f"Ligne {row + 1} : la source et la cible sont identiques.")
                return None
            if src in pairs:
                self._warn(f"La couche « {src.name()} » est utilisée plusieurs fois comme source.")
                return None
            pairs[src] = dst
        if not pairs:
            self._warn("Ajoutez au moins une paire de couches.")
            return None
        return pairs

    def go_next(self) -> None:
        """Valide les paires de la page 1 puis passe à la page 2 (champs)."""
        pairs = self.collect_pairs()
        if pairs is None:
            return  # erreur déjà signalée à l'utilisateur
        self.layer_pairs = pairs
        self._build_page2()
        self.stackedWidget.setCurrentIndex(1)

    # ------------------------------------------------------------------ page 2
    @staticmethod
    def get_compatible_field(src_field: QgsField, dst_fields: QgsFields) -> List[QgsField]:
        """Retourne les champs cibles compatibles avec un champ source.

        Un champ est ici considéré compatible s'il a exactement le même type
        que le champ source.

        Args:
            src_field: Champ de la couche source.
            dst_fields: Champs de la couche cible parmi lesquels chercher.

        Returns:
            La liste (éventuellement vide) des champs cibles compatibles.
        """
        compatible_fields: List[QgsField] = []
        for field in dst_fields:
            if field.type() == src_field.type():
                compatible_fields.append(field)
        return compatible_fields

    def _build_page2(self) -> None:
        """(Re)construit la page 2 : un onglet de correspondance par paire de couches."""
        layout = self.frame_tablewidget.layout()
        while layout.count():  # nettoyage si on revient en arrière
            w = layout.takeAt(0).widget()
            if w is not None:
                w.deleteLater()
        self._tables.clear()

        tabs = QTabWidget(self.frame_tablewidget)
        layout.addWidget(tabs)
        for src_layer, dst_layer in self.layer_pairs.items():
            table = self._make_field_table(src_layer, dst_layer)
            self._tables[src_layer] = table
            tabs.addTab(table, f"{src_layer.name()} -> {dst_layer.name()}")

    def _make_field_table(
        self, src_layer: QgsVectorLayer, dst_layer: QgsVectorLayer
    ) -> QTableWidget:
        """Construit le tableau de correspondance des champs pour une paire.

        Chaque ligne correspond à un champ source ; la seconde colonne propose
        « créer le champ », « ne pas ajouter » ou un champ cible compatible.

        Args:
            src_layer: Couche source.
            dst_layer: Couche cible appariée.

        Returns:
            Le ``QTableWidget`` rempli, prêt à être ajouté à un onglet.
        """
        src_fields = src_layer.fields()
        dst_fields = dst_layer.fields()

        table = QTableWidget(src_fields.count(), 2)
        table.setHorizontalHeaderLabels(
            ["Champ source", "Champ de la couche cible"]
        )
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        for row, sf in enumerate(src_fields):
            # col 0 : champ source (lecture seule)
            item = QTableWidgetItem(sf.name())
            icon = FIELD_ICONS.get(sf.type(), QIcon())
            if icon:
                item.setIcon(icon)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 0, item)

            # col 1 : combobox des champs compatibles
            combo = QComboBox()

            # item 0 (création du champ) : userData = FieldMapping.create()
            combo.addItem(
                QgsApplication.getThemeIcon("/mActionAdd.svg"),
                CREATE_FIELD_LABEL,
                FieldMapping.create(),
            )

            # item 1 (aucune action) : userData = FieldMapping.skip()
            combo.addItem(
                QgsApplication.getThemeIcon("/mActionRemove.svg"),
                NO_ACTION_LABEL,
                FieldMapping.skip(),
            )

            # champs compatibles de la couche cible, avec icône selon le type
            for df in self.get_compatible_field(sf, dst_fields):
                combo.addItem(
                    FIELD_ICONS.get(df.type(), QIcon()),
                    df.name(),
                    FieldMapping.map_to(df.name()),
                )

            # présélection : même nom (insensible à la casse) si compatible,
            # sinon « créer le champ » (index 0)
            idx = combo.findText(sf.name(), Qt.MatchFixedString)
            combo.setCurrentIndex(idx if idx > 0 else 0)

            table.setCellWidget(row, 1, combo)
        return table

    # ------------------------------------------------------------------ résultat
    def get_result(self) -> Dict[QgsVectorLayer, LayerResult]:
        """Collecte les choix de l'utilisateur sur la page 2.

        Returns:
            Un dictionnaire de la forme ::

                {
                  layer_source: {
                    "target_layer": layer_cible,
                    "fields": {
                       nom_champ_source: FieldMapping, ...
                    }
                  }, ...
                }
        """
        result: Dict[QgsVectorLayer, LayerResult] = {}
        for src_layer, table in self._tables.items():
            fields: Dict[str, FieldMapping] = {}
            for row in range(table.rowCount()):
                name = table.item(row, 0).text()
                combo = table.cellWidget(row, 1)
                fields[name] = combo.currentData()  # FieldMapping stocké en userData
            result[src_layer] = {"target_layer": self.layer_pairs[src_layer], "fields": fields}
        return result

    def accept_form(self) -> None:
        """Lance l'insertion, affiche le bilan à l'utilisateur puis ferme le dialogue."""
        result = self.get_result()
        succes, msg = insert_from_origin(result=result)
        if succes:
            QMessageBox.information(self, "Succès", msg)
        else:
            QMessageBox.critical(self, "Erreur", msg)
        self.accept()

    def _warn(self, msg: str) -> None:
        """Affiche une boîte d'avertissement liée à la sélection des paires.

        Args:
            msg: Message à afficher.
        """
        QMessageBox.warning(self, "Paires de couches", msg)