"""
Sistema de configuración persistente de usuario para CardSIM
"""

import json
import os
import sys
from pathlib import Path


class UserConfigManager:
    """Maneja la configuración persistente del usuario"""
    
    def __init__(self):
        # Detectar si estamos en un ejecutable portable o en desarrollo
        self.config_dir = self._get_config_directory()
        self.config_file = self.config_dir / "user_config.json"
        self._user_info = ""
        self._load_config()
    
    def _get_config_directory(self):
        """Obtiene el directorio de configuración según el contexto de ejecución"""
        try:
            # Si estamos en un ejecutable empaquetado (PyInstaller)
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                # Directorio donde está el ejecutable
                exe_dir = Path(sys.executable).parent
                config_dir = exe_dir / "config"
            else:
                # Modo desarrollo - directorio del proyecto
                config_dir = Path(__file__).parent.parent.parent / "config"
            
            return config_dir
        except Exception:
            # Fallback - directorio actual
            return Path.cwd() / "config"
    
    def _ensure_config_dir(self):
        """Asegura que el directorio de configuración existe"""
        try:
            self.config_dir.mkdir(exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create config directory: {e}")
    
    def _load_config(self):
        """Carga la configuración desde el archivo"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self._user_info = config.get('user_info', '')
        except Exception as e:
            print(f"Warning: Could not load user config: {e}")
            self._user_info = ""
    
    def save_config(self):
        """Guarda la configuración al archivo"""
        try:
            self._ensure_config_dir()
            config = {
                'user_info': self._user_info
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not save user config: {e}")
    
    @property
    def user_info(self):
        """Obtiene la información del usuario"""
        return self._user_info
    
    @user_info.setter
    def user_info(self, value):
        """Establece la información del usuario y la guarda"""
        self._user_info = value
        self.save_config()


# Instancia global del manager
user_config_manager = UserConfigManager()
