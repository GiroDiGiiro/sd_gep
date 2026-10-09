import unicodedata


def uniform_name(nom: str) -> str:
    # Conversion en str
    nom = str(nom)

    # Suppression des accents
    nom = unicodedata.normalize('NFD', nom)
    nom = nom.encode('ascii', 'ignore').decode('utf-8')

    # Remplacer espace par _ et supprimer tirets
    nom = nom.replace(" - ", "_").replace('-','_').replace("'", "_").replace(" ", "_").lower()

    return nom
