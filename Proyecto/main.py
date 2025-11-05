"""
CardSIM - Smart Card Interface
Punto de entrada principal de la aplicación
"""

import sys
import os
import tkinter as tk
from typing import NoReturn

# Añadir el directorio src al path para las importaciones
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gui.interface import CardSimInterface

def main() -> NoReturn:
    """Función principal de la aplicación"""
    try:
        # Crear ventana root
        root = tk.Tk()
        
        # Crear y ejecutar la interfaz
        app = CardSimInterface(root)
        app.run()
        
    except KeyboardInterrupt:
        print("\nAplicación cerrada por el usuario")
        sys.exit(0)
        
    except Exception as e:
        print(f"Error al ejecutar la aplicación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
