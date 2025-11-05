"""
Paquete GUI - Interfaz gráfica de CardSIM
"""

# No importar interface automáticamente para evitar dependencias circulares
# from .interface import CardSimInterface

# Exportar las clases de diálogos para facilitar imports
from .dialogs import (
    ReadMemoryDialog,
    WriteMemoryDialog, 
    ChangePSCDialog,
    WriteProtectDialog,
    UserConfigDialog
)

__all__ = [
    'ReadMemoryDialog',
    'WriteMemoryDialog',
    'ChangePSCDialog', 
    'WriteProtectDialog',
    'UserConfigDialog'
]
