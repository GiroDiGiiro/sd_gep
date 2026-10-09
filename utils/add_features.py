from typing import List
from qgis.core import QgsVectorLayer, QgsFeature


def add_features(features: List[QgsFeature],
                 layer: QgsVectorLayer | str,
                 allow_missing_fields: bool = False) -> bool:
    """
    Ajoute des features dans une couche QGIS en copiant uniquement
    les attributs existants dans la couche de destination.

    :param features: Liste des features sources
    :param layer: Couche QGIS ou chemin
    :param allow_missing_fields: 
           - False : erreur si un champ n'existe pas dans la destination
           - True  : ignore silencieusement les champs manquants
    :return: True si succès
    """

    # Charger la couche si string
    if isinstance(layer, str):
        layer = QgsVectorLayer(layer, "Layer", "ogr")
        if not layer.isValid():
            print("Couche invalide.")
            return False

    dest_fields = layer.fields()
    dest_names = dest_fields.names()

    layer.startEditing()

    try:
        for src_feat in features:

            new_feat = QgsFeature(dest_fields)
            new_feat.setGeometry(src_feat.geometry())

            for field_name in src_feat.fields().names():

                if field_name not in dest_names:
                    if not allow_missing_fields:
                        raise AttributeError(f"Champ manquant dans la destination : {field_name}")
                    continue

                new_feat[field_name] = src_feat[field_name]

            if not layer.addFeature(new_feat):
                raise RuntimeError("Échec de l'ajout d'une entité")

        if not layer.commitChanges():
            raise RuntimeError("Échec de l'enregistrement des modifications")

        return True

    except Exception as e:
        layer.rollBack()
        print(f"Erreur : {e}")
        return False