import os
import shutil
from pathlib import Path
from typing import Tuple, Dict

import psycopg2
from psycopg2 import sql
from gep_sd.utils.export_layers_to_gpkg import export_layers_to_gpkg
from gep_sd.utils.get_db_info import get_db_info
from gep_sd.utils.load_layer_from_postgis import load_layer_from_postgis
from gep_sd.utils.load_layers_from_gpkg import load_layers_from_gpkg
from gep_sd.utils.move_layers_to_group import move_layers_to_group
from qgis.core import QgsProject, QgsCoordinateReferenceSystem, QgsVectorLayer, QgsEditorWidgetSetup, QgsDataSourceUri, \
    QgsSnappingConfig, QgsTolerance, Qgis, QgsRasterLayer, QgsPointXY, QgsCoordinateReferenceSystem, \
    QgsCoordinateTransform
from qgis.utils import iface


LAYERS_NAMES = ['regard', 'reseau', 'ouvrage_polygonal', 'surface_raccordee', 'sousbassin_versant', 'bassin_versant',
                'diametre_par_materiau']
PLUGIN_PATH = Path(__file__).resolve().parent.parent.parent
GPKG_PATH = os.path.join(PLUGIN_PATH, 'ressources', 'gpkg', 'couches_projet.gpkg')
STYLE_DIRECTORY = os.path.join(PLUGIN_PATH, 'ressources', 'style')

REGARD_FIELD_VALUEMAP: Dict[str, str] = {
    'regard_type_id': 'regard_type',
    'regard_subtype_id': 'regard_subtype',
    'equipement_type_id': 'equipement_type',
    'ouvrage_ponctuel_type_id': 'ouvrage_ponctuel_type',
    'tampon_geometrie_id': 'tampon_geometrie',
    'tampon_nature_id': 'tampon_nature',
    'anomalie_type_id': 'anomalie_ponctuel_type',
}
RESEAU_FIELD_VALUEMAP: Dict[str, str] = {
    'reseau_type_id': 'reseau_type',
    'ouvrage_lineaire_type_id': 'ouvrage_lineaire_type',
    'forme_geometrique_id': 'forme_geometrique',
    'materiau_lineaire_id': 'materiau_lineaire',
    'anomalie_lineaire_type_id': 'anomalie_lineaire_type',
}
OUVRAGE_POLYGONAL_FIELD_VALUEMAP: Dict[str, str] = {
    'ouvrage_gestion_type_id': 'ouvrage_gestion_type',
    'equipement_polygonal_type_id': 'equipement_polygonal_type',
    'anomalie_polygonal_type_id': 'anomalie_polygonal_type',
}

SSBV_FIELD_VALUEMAP: Dict[str, str] = {
    'mode_gestion_id': 'mode_gestion',
    'urbanisation_id': 'urbanisation',
}


def _build_field_valuemaps(db_info: dict, field_valuemap: Dict[str, str]) -> Tuple[Dict[str, Dict[str, int]], str]:
    """Se connecte une seule fois et construit {champ: {libellé: id}} pour chaque table référencée."""
    field_valuemap_dict: Dict[str, Dict[str, int]] = {}
    conn = None
    try:
        conn = psycopg2.connect(
            host=db_info['host'],
            port=db_info['port'],
            database=db_info['database'],
            user=db_info['user'],
            password=db_info['password'],
        )
        cursor = conn.cursor()
        for field_name, table_name in field_valuemap.items():
            query = sql.SQL("SELECT id, nom FROM {schema_name}.{table_name};").format(
                schema_name=sql.Identifier(db_info['schema_name']),
                table_name=sql.Identifier(table_name),
            )
            cursor.execute(query)
            field_valuemap_dict[field_name] = {nom_val: id_val for id_val, nom_val in cursor.fetchall()}
    except (Exception, psycopg2.Error) as error:
        return {}, f'{error}'
    finally:
        if conn:
            conn.close()

    return field_valuemap_dict, ""


def _apply_style_generic(
        db_info: dict,
        layer: QgsVectorLayer,
        style_filename: str,
        style_name: str,
        field_valuemap: Dict[str, str],
        error_label: str,
        **kwargs,
) -> Tuple[bool, str]:
    set_this_style = kwargs.get('set_this_style', True)
    style_path = os.path.join(STYLE_DIRECTORY, style_filename)
    if not os.path.exists(style_path):
        return False, f"style des {error_label} introuvable. path : {style_path}"

    style_manager = layer.styleManager()
    previous_style = style_manager.currentStyle()

    # 1. Créer le style (copie de l'état courant) et le rendre courant AVANT de charger le QML
    if style_name not in style_manager.styles():
        if not style_manager.addStyleFromLayer(style_name):
            return False, f"Erreur lors de la création du style : {style_name}"
    if not style_manager.setCurrentStyle(style_name):
        return False, f"Erreur lors de la sélection du style : {style_name}"

    # 2. Charger le QML dans ce style (loadNamedStyle renvoie un tuple (message, ok))
    message, ok = layer.loadNamedStyle(style_path)
    if not ok:
        return False, f"Erreur lors du chargement du style depuis {style_path} : {message}"

    # 3. Value maps (elles font partie du style, donc à appliquer pendant qu'il est courant)
    if field_valuemap:
        field_valuemap_dict, error = _build_field_valuemaps(db_info, field_valuemap)
        if error:
            return False, error

        for field_name, valuemap in field_valuemap_dict.items():
            idx = layer.fields().lookupField(field_name)
            if idx == -1:
                print(f"[Warning] Champ introuvable sur la couche : {field_name}")
                continue
            layer.setEditorWidgetSetup(idx, QgsEditorWidgetSetup('ValueMap', {'map': valuemap}))

    # 4. Revenir au style précédent si on ne veut pas garder celui-ci comme courant
    #    (le changement de style sauvegarde l'état actuel dans le style qu'on quitte)
    if not set_this_style and previous_style != style_name:
        style_manager.setCurrentStyle(previous_style)

    return True, ""


def apply_style_regard(db_info: dict, layer: QgsVectorLayer) -> Tuple[bool, str]:
    success, message = _apply_style_generic(db_info, layer, 'regard_acquisition.qml', 'acquisition', REGARD_FIELD_VALUEMAP,
                                'regard')

    if not success:
        return False, message

    success, message = _apply_style_generic(db_info=db_info,
                                            layer=layer,
                                            style_filename='regard_traitement.qml',
                                            style_name='traitement',
                                            field_valuemap=REGARD_FIELD_VALUEMAP,
                                            error_label='regard',
                                            set_this_style=False)
    if not success:
        return False, message
    return True, ""

def apply_style_reseau(db_info: dict, layer: QgsVectorLayer) -> Tuple[bool, str]:
    success, message = _apply_style_generic(db_info, layer, 'reseau_acquisition.qml', 'acquisition', RESEAU_FIELD_VALUEMAP,
                                'reseau')

    if not success:
        return False, message

    success, message = _apply_style_generic(db_info=db_info,
                                            layer=layer,
                                            style_filename='reseau_traitement.qml',
                                            style_name='traitement',
                                            field_valuemap=RESEAU_FIELD_VALUEMAP,
                                            error_label='reseau',
                                            set_this_style=False)

    if not success:
        return False, message
    return True, ""

def apply_style_ouvrage_polygonal(db_info: dict, layer: QgsVectorLayer) -> Tuple[bool, str]:
    success, message = _apply_style_generic(db_info, layer, 'ouvrage_polygonal_acquisition.qml', 'acquisition',
                                OUVRAGE_POLYGONAL_FIELD_VALUEMAP,
                                'ouvrage polygonal')

    if not success:
        return False, message

    success, message = _apply_style_generic(db_info=db_info,
                                            layer=layer,
                                            style_filename='ouvrage_polygonal_traitement.qml',
                                            style_name='traitement',
                                            field_valuemap=OUVRAGE_POLYGONAL_FIELD_VALUEMAP,
                                            error_label='ouvrage polygonal',
                                            set_this_style=False)

    if not success:
        return False, message
    return True, ""

def apply_style_surface_raccordee(db_info: dict, layer: QgsVectorLayer) -> Tuple[bool, str]:
    return _apply_style_generic(db_info, layer, 'surface_raccordee_traitement.qml', 'traitement', None,
                                'surface_raccordee')


def apply_style_sousbassin_versant(db_info: dict, layer: QgsVectorLayer) -> Tuple[bool, str]:
    return _apply_style_generic(db_info, layer, 'sousbassin_versant_traitement.qml', 'traitement', SSBV_FIELD_VALUEMAP,
                                'sousbassin_versant')


def apply_style_bassin_versant(db_info: dict, layer: QgsVectorLayer) -> Tuple[bool, str]:
    return _apply_style_generic(db_info, layer, 'bassin_versant_traitement.qml', 'traitement', None,
                                'bassin_versant')


def create_sd(project_name: str, project_path: str | Path, db_name: str, schema_name : str) -> Tuple[bool, str]:
    QgsProject.instance().clear()
    QgsProject.instance().setCrs(QgsCoordinateReferenceSystem(2154))

    # Copié le gpkg contenant les couches type du plugin vers le dossier de travail
    source = Path(GPKG_PATH)
    destination = os.path.join(project_path, 'data.gpkg')
    shutil.copy2(source, destination)

    # Importé puis sauvegarder dans le gpkg copié les couches de définition
    def_layer = load_layer_from_postgis(db_name=db_name,
                                        schema_name=schema_name,
                                        table_name='diametre_par_materiau',
                                        geometry=False,
                                        add_to_legend=False)

    if not export_layers_to_gpkg([def_layer], destination):
        return False, "[Error] Erreur lors de l'export des couches de définition en gpkg"

    # La couche PostGIS ne sert plus : on la retire du projet
    QgsProject.instance().removeMapLayer(def_layer.id())

    # import des couches depuis le gpkg copié
    layers = load_layers_from_gpkg(destination, LAYERS_NAMES)

    if not layers:
        return False, "[Error] Erreur lors de l'import des couches créée en gpkg"

    # Tri des couches pour usage futur
    pt_layers = [layer for layer in layers if layer.geometryType() == 0]
    line_layers = [layer for layer in layers if layer.geometryType() == 1]
    polygon_layers = [layer for layer in layers if layer.geometryType() == 2]
    nogeom_layers = [layer for layer in layers if layer.geometryType() == 4]

    # Récupérer les infos de connection à la base de donné
    db_info = get_db_info(db_name)
    if not db_info:
        return False, f'Impossible de récupérer les info de la bd : {db_name}'
    db_info['schema_name'] = schema_name
    # Appliqué le style des regards
    _, error = apply_style_regard(db_info, pt_layers[0])
    if error:
        return False, error

    _, error = apply_style_reseau(db_info, line_layers[0])
    if error:
        return False, error

    _, error = apply_style_ouvrage_polygonal(db_info, polygon_layers[0])
    if error:
        return False, error

    _, error = apply_style_surface_raccordee(db_info, polygon_layers[1])
    if error:
        return False, error

    _, error = apply_style_sousbassin_versant(db_info, polygon_layers[2])
    if error:
        return False, error

    _, error = apply_style_bassin_versant(db_info, polygon_layers[3])
    if error:
        return False, error

    # Importer GoogleSat
    # Créer l'URI pour le service XYZ
    uri = QgsDataSourceUri()
    uri.setParam('type', 'xyz')
    uri.setParam('url', 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}')
    uri.setParam('zmax', '18')
    uri.setParam('zmin', '0')

    # Créer et ajouter la couche
    layer = QgsRasterLayer(uri.encodedUri().data().decode(), 'GoogleSat', 'wms')

    if not layer.isValid():
        return False, f" Erreur lors de l'import de GoogleMaps uri : {uri}"
    QgsProject.instance().addMapLayer(layer)

    # Mettre les couches dnas des groupes pour plus de clarté
    move_layers_to_group(['regard', 'reseau', 'ouvrage_polygonal'], 'Acquisition', True)
    move_layers_to_group(['surface_raccordee', 'sousbassin_versant', 'bassin_versant', ], 'Traitement', True)
    move_layers_to_group(['GoogleSat'], 'BaseMap', True)
    move_layers_to_group(['diametre_par_materiau'], 'Table de Definition', True)

    # Mettre les options d'accrochage pour une bonne topologie
    my_snap_config = QgsSnappingConfig()
    my_snap_config.setEnabled(True)
    my_snap_config.setType(QgsSnappingConfig.VertexAndSegment)
    my_snap_config.setUnits(QgsTolerance.Pixels)
    my_snap_config.setTolerance(10)
    my_snap_config.setIntersectionSnapping(True)
    my_snap_config.setMode(Qgis.SnappingMode.AllLayers)

    # Appliquer la configuration de snapping au projet
    QgsProject.instance().setSnappingConfig(my_snap_config)

    # Centré sur l'unima
    canvas = iface.mapCanvas()

    src_crs = QgsCoordinateReferenceSystem("EPSG:4326")  # WGS84
    dest_crs = canvas.mapSettings().destinationCrs()  # CRS du canvas

    transform = QgsCoordinateTransform(src_crs, dest_crs, QgsProject.instance())
    point = transform.transform(QgsPointXY(-1.0944229154, 46.1644068195))

    canvas.setCenter(point)
    canvas.zoomScale(1000000)

    # Sauvegarde du projet
    project_path = os.path.join(project_path, f"{project_name}.qgz")
    if not QgsProject.instance().write(project_path):
        msg = f"[Error] Impossible de sauvegarder le projet : {project_path}"
        return False, msg

    # Rafraichir le projet
    iface.addProject(project_path)

    return True, f"Création du projet : {project_name} réussi"
