"""
Gestión de sesiones individuales de tarjetas para trabajo simultáneo
"""

import uuid
import datetime
import tempfile
import os
import json
from src.utils.constants import *
from src.utils.app_states import AppStates, ButtonStates, CardStates
from .memory_manager import MemoryManager
from .apdu_handler import APDUHandler
from .code_improvements import CommonMessages

class CardSession:
    """Representa una sesión individual de trabajo con una tarjeta"""
    
    def __init__(self, card_name, card_type=CARD_TYPE_5542):
        # Identificación única
        self.session_id = str(uuid.uuid4())
        self.card_name = card_name
        self.card_type = card_type
        self.created_at = datetime.datetime.now()
        
        # Gestores específicos de esta sesión
        self.memory_manager = MemoryManager()
        self.apdu_handler = APDUHandler(self.memory_manager, card_type)
        
        # Estados de la tarjeta
        self.card_created = True  # Se crea al instanciar
        self.card_selected = False
        self.psc_verified = False
        self.psc_has_been_changed = False  # Rastrear si el PSC fue modificado alguna vez
        self.is_blocked = False
        
        # Log de comandos específico de esta sesión
        self.command_log = []
        
        # Información del usuario para esta tarjeta
        self.user_info = ""
        
        # Archivo temporal para persistencia
        self.temp_file = None
        self._create_temp_file()
        
        # Inicializar memoria según tipo de tarjeta
        self.memory_manager.initialize_memory(card_type)
        
        # Log inicial
        self.add_to_log("INFO", f"Card session created: {card_name} ({self._get_card_type_display()})")
    
    def _get_card_type_display(self):
        """Obtiene el nombre mostrable del tipo de tarjeta"""
        return "5542 (256B)" if self.card_type == CARD_TYPE_5542 else "5528 (1KB)"
    
    def _create_temp_file(self):
        """Crea un archivo temporal para esta sesión"""
        try:
            # Crear directorio temporal si no existe
            temp_dir = os.path.join(tempfile.gettempdir(), "CardSIM_sessions")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Crear archivo temporal específico para esta sesión
            temp_filename = f"card_session_{self.session_id}.json"
            self.temp_file = os.path.join(temp_dir, temp_filename)
            
            # Guardar estado inicial
            self.save_session_state()
            
        except Exception as e:
            print(f"Warning: Could not create temp file for session: {e}")
            self.temp_file = None
    
    def save_session_state(self):
        """Guarda el estado actual de la sesión en archivo temporal"""
        if not self.temp_file:
            return
            
        try:
            session_data = {
                'session_id': self.session_id,
                'card_name': self.card_name,
                'card_type': self.card_type,
                'created_at': self.created_at.isoformat(),
                'card_selected': self.card_selected,
                'psc_verified': self.psc_verified,
                'psc_has_been_changed': self.psc_has_been_changed,  # Preservar estado del PSC
                'is_blocked': self.is_blocked,
                'user_info': self.user_info,
                'command_log': self.command_log,
                'memory_data': self.memory_manager.get_memory_dump(),
                'error_counter': self.apdu_handler.error_counter
            }
            
            with open(self.temp_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Warning: Could not save session state: {e}")
    
    def add_to_log(self, log_type, message, apdu_data=None):
        """Añade una entrada al log de comandos de esta sesión"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        log_entry = {
            'timestamp': timestamp,
            'type': log_type,  # INFO, APDU_SEND, APDU_RESPONSE, ERROR
            'message': message
        }
        
        if apdu_data:
            log_entry.update(apdu_data)
        
        self.command_log.append(log_entry)
        
        # Guardar estado después de cada log
        self.save_session_state()
    
    def execute_select_card(self):
        """Ejecuta el comando Select Card específico para esta sesión"""
        result = self.apdu_handler.process_select_card()
        
        if result['success']:
            self.card_selected = True
            
            # Log del comando
            self.add_to_log("APDU_SEND", "SELECT CARD", {
                'apdu': ' '.join([f"{b:02X}" for b in result['apdu']]),
                'description': result['description']
            })
            
            self.add_to_log("APDU_RESPONSE", "Success", {
                'sw': f"{result['sw1']:02X} {result['sw2']:02X}"
            })
            
        return result
    
    def execute_present_psc(self, psc_bytes):
        """Ejecuta Present PSC específico para esta sesión"""
        result = self.apdu_handler.process_present_psc(psc_bytes)
        
        # Log del comando siempre
        self.add_to_log("APDU_SEND", "PRESENT PSC", {
            'apdu': ' '.join([f"{b:02X}" for b in result['apdu']])
        })
        
        # Log de la respuesta siempre
        if result['success']:
            self.psc_verified = True
            self.add_to_log("APDU_RESPONSE", "PSC Verified", {
                'sw': f"{result['sw1']:02X} {result['sw2']:02X}"
            })
        else:
            self.add_to_log("APDU_RESPONSE", "PSC Verification Failed", {
                'sw': f"{result['sw1']:02X} {result['sw2']:02X}"
            })
            
        return result
    
    def execute_read_memory(self, address, length):
        """Ejecuta Read Memory específico para esta sesión"""
        result = self.apdu_handler.process_read_memory(address, length)
        return result
    
    def execute_write_memory(self, address, data_bytes):
        """Ejecuta Write Memory específico para esta sesión"""
        if not self.psc_verified:
            return {
                'success': False,
                'message': CommonMessages.PSC_NOT_VERIFIED
            }
            
        result = self.apdu_handler.process_write_memory(address, data_bytes)
        
        if result['success']:
            # Log del comando
            self.add_to_log("APDU_SEND", "WRITE MEMORY", {
                'apdu': ' '.join([f"{b:02X}" for b in result['apdu']]),
                'description': result['description']
            })
            
            # Formatear datos para el log
            data_hex = ' '.join([f"{b:02X}" for b in data_bytes])
            data_ascii = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in data_bytes])
            
            self.add_to_log("APDU_RESPONSE", "Data written", {
                'sw': f"{result['sw1']:02X} {result['sw2']:02X}",
                'data': f"{data_hex}   {data_ascii}",
                'address': address
            })
            
        return result
    
    def execute_change_psc(self, new_psc_bytes):
        """Ejecuta Change PSC específico para esta sesión"""
        if not self.psc_verified:
            return {
                'success': False,
                'message': CommonMessages.PSC_NOT_VERIFIED
            }
        
        # Ejecutar el comando Change PSC apropiado según tipo de tarjeta
        result = self.apdu_handler.process_change_psc(new_psc_bytes)
        
        if result['success']:
            # Marcar que el PSC ha sido cambiado
            self.psc_has_been_changed = True
            
            # Log del comando específico para Change PSC
            self.add_to_log("APDU_SEND", "CHANGE PSC", {
                'apdu': ' '.join([f"{b:02X}" for b in result['apdu']]),
                'description': result['description']
            })
            
            # Formatear datos para el log (PSC se muestra ofuscado por seguridad)
            data_hex = ' '.join([f"{b:02X}" for b in new_psc_bytes])
            psc_size = len(new_psc_bytes)
            masked_psc = "** " * psc_size  # Ajustar máscara según tamaño
            
            self.add_to_log("APDU_RESPONSE", "PSC changed", {
                'sw': f"{result['sw1']:02X} {result['sw2']:02X}",
                'data': f"{data_hex}   (Hidden for security)",
                'internal': f"Stored in {'internal register' if self.memory_manager.card_type == 5542 else 'memory'}"
            })
            
        return result
    
    def get_memory_display_data_with_colors(self):
        """Obtiene los datos de memoria formateados con colores para la interfaz"""
        # Para SLE5542: PSC es visible solo si está verificado o ha sido cambiado (registro interno)
        # Para SLE5528: PSC es visible solo si está verificado, aunque esté en memoria física
        from utils.constants import CARD_TYPE_5528
        if self.memory_manager.card_type == CARD_TYPE_5528:
            # SLE5528: El PSC debe estar protegido hasta que se verifique correctamente
            psc_should_be_visible = self.psc_verified
        else:
            # SLE5542: Lógica original para registro interno
            psc_should_be_visible = (self.psc_verified or self.psc_has_been_changed)
        
        return self.memory_manager.get_memory_display_data_with_colors(psc_should_be_visible)
    
    def get_current_app_state(self):
        """Obtiene el estado actual de la aplicación para esta sesión"""
        if not self.card_created:
            return AppStates.INITIAL
        elif not self.card_selected:
            return AppStates.CARD_LOADED
        elif self.apdu_handler.is_card_blocked():
            return AppStates.CARD_BLOCKED
        elif not self.psc_verified:
            return AppStates.CARD_SELECTED
        else:
            return AppStates.PSC_PRESENTED
    
    def get_current_psc(self):
        """Obtiene el PSC actual usando el método apropiado según tipo de tarjeta"""
        if not self.card_created:
            return "-- -- --"
        
        try:
            # Usar el método del memory_manager que maneja ambos tipos
            psc_bytes = self.memory_manager.get_current_psc()
            # Formatear como hex con espacios
            return " ".join([f"{b:02X}" for b in psc_bytes])
        except Exception:
            # Valor por defecto si hay error, según tipo de tarjeta
            from utils.constants import CARD_TYPE_5542
            if self.memory_manager.card_type == CARD_TYPE_5542:
                return "FF FF FF"
            else:
                return "FF FF"
    
    def present_psc(self, psc_hex_string, use_physical=False):
        """Presenta PSC para verificación - versión con soporte físico"""
        try:
            # Convertir string hex a bytes
            psc_bytes = bytes.fromhex(psc_hex_string.replace(' ', ''))
            
            if use_physical:
                # Usar tarjeta física
                from .physical_card_handler import PhysicalCardHandler
                handler = PhysicalCardHandler()
                success, message = handler.present_psc(self.memory_manager.card_type, list(psc_bytes))
                
                if success:
                    # También actualizar estado local
                    self.execute_present_psc(psc_bytes)
                    return {'success': True, 'message': message}
                else:
                    return {'success': False, 'message': message}
            else:
                # Operación en memoria local
                return self.execute_present_psc(psc_bytes)
                
        except Exception as e:
            return {'success': False, 'message': f'PSC presentation failed: {str(e)}'}
    
    def cleanup(self):
        """Limpia los recursos de la sesión"""
        try:
            if self.temp_file and os.path.exists(self.temp_file):
                os.remove(self.temp_file)
        except Exception as e:
            print(f"Warning: Could not clean up session file: {e}")
    
    def __del__(self):
        """Destructor - limpia automáticamente"""
        self.cleanup()
