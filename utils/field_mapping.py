"""Types partagés entre le formulaire d'insertion et l'algorithme d'insertion.

Ce module est volontairement indépendant de l'interface (pas d'import du
formulaire) afin d'éviter tout import circulaire entre
``InsertFromOrigin`` (formulaire) et ``insert_from_origin`` (algorithme).
"""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional, TypedDict

from qgis.core import QgsVectorLayer


class FieldAction(Enum):
    """Action à effectuer pour un champ de la couche source."""

    CREATE = auto()  # créer le champ dans la couche cible
    SKIP = auto()  # ne rien faire
    MAP = auto()  # copier vers un champ existant


@dataclass(frozen=True)
class FieldMapping:
    """Décision de correspondance pour un champ source.

    Attributes:
        action: Action choisie par l'utilisateur.
        target: Nom du champ cible. Renseigné uniquement pour
            ``FieldAction.MAP``, ``None`` sinon.
    """

    action: FieldAction
    target: Optional[str] = None  # nom du champ cible (uniquement pour MAP)

    @classmethod
    def create(cls) -> "FieldMapping":
        """Construit un mapping de type ``CREATE`` (créer le champ)."""
        return cls(FieldAction.CREATE)

    @classmethod
    def skip(cls) -> "FieldMapping":
        """Construit un mapping de type ``SKIP`` (ignorer le champ)."""
        return cls(FieldAction.SKIP)

    @classmethod
    def map_to(cls, name: str) -> "FieldMapping":
        """Construit un mapping de type ``MAP`` vers un champ existant.

        Args:
            name: Nom du champ de la couche cible qui recevra les valeurs.
        """
        return cls(FieldAction.MAP, name)


class LayerResult(TypedDict):
    """Résultat du formulaire pour une couche source."""

    target_layer: QgsVectorLayer  # couche cible appariée
    fields: Dict[str, FieldMapping]  # {nom_champ_source: FieldMapping}