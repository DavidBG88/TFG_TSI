"""
Gestor de recursos para la aplicación CardSIM.
Maneja las rutas de assets tanto en desarrollo como en el ejecutable empaquetado.
"""
import os
import sys
from pathlib import Path

def get_resource_path(relative_path):
    """
    Obtiene la ruta absoluta a un recurso, funciona tanto en desarrollo 
    como en el ejecutable empaquetado por PyInstaller.
    
    Args:
        relative_path (str): Ruta relativa al recurso (ej: "assets/icons/etsisi.ico")
    
    Returns:
        str: Ruta absoluta al recurso
    """
    try:
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # En desarrollo, usar el directorio raíz del proyecto
        base_path = Path(__file__).parent.parent.parent
    
    return os.path.join(base_path, relative_path)

def get_icon_path(icon_name):
    """
    Obtiene la ruta al icono especificado.
    
    Args:
        icon_name (str): Nombre del icono (con o sin extensión)
    
    Returns:
        str: Ruta absoluta al icono
    """
    if not icon_name.endswith(('.ico', '.png', '.jpg', '.jpeg')):
        # Por defecto buscar .ico, si no existe buscar .png
        ico_path = get_resource_path(f"assets/icons/{icon_name}.ico")
        if os.path.exists(ico_path):
            return ico_path
        else:
            return get_resource_path(f"assets/icons/{icon_name}.png")
    else:
        return get_resource_path(f"assets/icons/{icon_name}")