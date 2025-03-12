import unicodedata
import os
from PyQt5.QtCore import QUrl

def format_filename(filepath):
    """Remove acentos e espaços do nome do arquivo"""
    directory, filename = os.path.split(filepath)
    name, ext = os.path.splitext(filename)

    # Remove acentos e caracteres especiais
    name = unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("utf-8")

    # Substitui espaços por underscores
    name = name.replace(" ", "_")

    
    return QUrl.fromLocalFile(os.path.join(directory, name + ext))