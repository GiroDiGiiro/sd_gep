"""Insertion d'entités de couches sources dans des couches cibles."""
from typing import Dict, List, Optional, Tuple

from gep_sd.utils.field_mapping import FieldAction, LayerResult
from gep_sd.utils.add_fields import add_fields
from gep_sd.utils.add_features import  add_features
from gep_sd.utils.unique_name import unique_name
from gep_sd.utils.uniform_name import uniform_name
from qgis.core import (
    QgsCoordinateTransform, QgsFeature, QgsField, QgsProject, QgsVectorLayer,
)


def insert_from_origin(result: Dict[QgsVectorLayer, LayerResult]) -> Tuple[bool, str]:
    """Copie les entités de chaque couche source vers sa couche cible.

    Pour chaque paire, les champs marqués ``CREATE`` sont d'abord ajoutés à
    la couche cible (avec un nom unique), puis les entités sont reprojetées
    si besoin, remappées sur le schéma de la cible et insérées.

    Args:
        result: Résultat du formulaire, de la forme ::

            {
              layer_source: {
                "target_layer": layer_cible,
                "fields": {nom_champ_source: FieldMapping, ...},
              }, ...
            }

    Returns:
        Un tuple ``(succes, message)``. ``succes`` vaut ``False`` dès qu'une
        insertion échoue (les paires suivantes ne sont alors pas traitées) ;
        le message indique alors la paire en erreur. En cas de succès, le
        message récapitule toutes les paires traitées.
    """
    summaries: List[str] = []  # une ligne de bilan par paire traitée

    for layer_source, info in result.items():
        layer_cible: QgsVectorLayer = info["target_layer"]
        src_fields = layer_source.fields()

        # 1. Table de correspondance nom source -> nom cible
        #    + liste des champs à créer dans la couche cible
        name_map: Dict[str, str] = {}
        to_create: List[QgsField] = []
        existing: List[str] = list(layer_cible.fields().names())  # noms déjà pris dans la cible

        for src_name, mapping in info["fields"].items():
            match mapping.action:
                case FieldAction.SKIP:
                    continue  # champ ignoré

                case FieldAction.MAP:
                    # copie vers un champ existant de la cible
                    name_map[src_name] = mapping.target

                case FieldAction.CREATE:
                    # nom normalisé puis rendu unique vis-à-vis des champs existants
                    normalized_name = uniform_name(src_name)
                    new_name = unique_name(normalized_name, existing)
                    existing.append(new_name)

                    new_field = QgsField(src_fields.field(src_name))  # copie
                    new_field.setName(new_name)
                    to_create.append(new_field)

                    name_map[src_name] = new_name

        # 2. Création des champs manquants dans la couche cible
        if to_create:
            add_fields(layer_cible, to_create)  # appelle updateFields()

        # 3. Construction des features au schéma de la couche cible
        dst_fields = layer_cible.fields()  # à relire APRÈS add_fields

        # Reprojection nécessaire uniquement si les SCR diffèrent
        transform: Optional[QgsCoordinateTransform] = None
        if layer_source.crs() != layer_cible.crs():
            transform = QgsCoordinateTransform(
                layer_source.crs(), layer_cible.crs(), QgsProject.instance()
            )

        new_features: List[QgsFeature] = []
        for src_feat in layer_source.getFeatures():
            new_feat = QgsFeature(dst_fields)

            geom = src_feat.geometry()
            if transform and not geom.isNull():
                geom.transform(transform)
            new_feat.setGeometry(geom)

            # copie des attributs selon la table de correspondance
            for src_name, dst_name in name_map.items():
                new_feat[dst_name] = src_feat[src_name]

            new_features.append(new_feat)

        # 4. Insertion
        if not add_features(new_features, layer_cible):
            return False, (
                f"Erreur lors de l'ajout des nouvelles entités de "
                f"{layer_source.name()} vers {layer_cible.name()}."
            )

        summaries.append(
            f"Entités de {layer_source.name()} ajoutées avec succès à {layer_cible.name()}"
        )

    return True, "\n".join(summaries)