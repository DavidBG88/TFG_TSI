"""
Gestor de múltiples sesiones de tarjetas simultáneas
"""

from .card_session import CardSession
from src.utils.constants import *
from .code_improvements import is_valid_hex_string, validate_hex_bytes
import os

class SessionManager:
    """Gestiona múltiples sesiones de tarjetas simultáneas"""
    
    def __init__(self):
        self.sessions = {}  # {session_id: CardSession}
        self.active_session_id = None
        self.session_order = []  # Para mantener orden de creación
    
    def create_new_card_session(self, card_name, card_type=CARD_TYPE_5542):
        """Crea una nueva sesión de tarjeta"""
        # Verificar que el nombre no esté en uso
        for session in self.sessions.values():
            if session.card_name == card_name:
                return None, f"Card name '{card_name}' already exists"
        
        # Crear nueva sesión
        session = CardSession(card_name, card_type)
        
        # Aplicar configuración global de usuario si existe
        try:
            from utils.user_config import user_config_manager
            if user_config_manager.user_info:
                session.user_info = user_config_manager.user_info
        except Exception:
            pass  # Si no hay configuración global, continúa normalmente
        
        self.sessions[session.session_id] = session
        self.session_order.append(session.session_id)
        
        # Hacer esta sesión la activa
        self.active_session_id = session.session_id
        
        return session, "Card session created successfully"
    
    def open_card_from_file(self, filepath, card_name=None):
        """Crea una sesión desde un archivo de tarjeta guardado"""
        try:
            # Si no se proporciona nombre, usar el nombre del archivo
            if not card_name:
                card_name = os.path.splitext(os.path.basename(filepath))[0]
            
            # Detectar tipo de tarjeta del archivo
            card_type = self._detect_card_type_from_file(filepath)
            print(f"[DEBUG] Opening card from file: {filepath}")
            print(f"[DEBUG] Detected card type: {card_type}")
            
            # Crear sesión
            session, message = self.create_new_card_session(card_name, card_type)
            if not session:
                return None, message
            
            print(f"[DEBUG] Created session with card type: {session.card_type}")
            
            # Cargar datos del archivo
            success = self._load_card_data_from_file(session, filepath)
            if not success:
                # Si falla la carga, eliminar la sesión creada
                self.close_session(session.session_id)
                return None, "Failed to load card data from file"
            
            print(f"[DEBUG] Final session card type: {session.card_type}")
            print(f"[DEBUG] PSC should be: {session.get_current_psc()}")
            
            return session, "Card loaded successfully from file"
            
        except Exception as e:
            print(f"[ERROR] Error opening card from file: {e}")
            return None, f"Error opening card file: {str(e)}"
    
    def _detect_card_type_from_file(self, filepath):
        """Detecta el tipo de tarjeta basado en el contenido del archivo"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # Buscar indicadores específicos del tipo de tarjeta
            lines = content.split('\n')
            
            # Buscar en el header del archivo
            for line in lines[:10]:  # Revisar las primeras 10 líneas
                line_upper = line.upper()
                if "SLE5528" in line_upper or "1KB" in line_upper:
                    print(f"[DEBUG] Detected SLE5528 from header: {line}")
                    return CARD_TYPE_5528
                elif "SLE5542" in line_upper or "256B" in line_upper:
                    print(f"[DEBUG] Detected SLE5542 from header: {line}")
                    return CARD_TYPE_5542
                elif "PAGE" in line_upper and any(x in line_upper for x in ["0", "1", "2", "3"]):
                    print(f"[DEBUG] Detected SLE5528 from PAGE indicator: {line}")
                    return CARD_TYPE_5528
            
            # Contar líneas de datos reales (no comentarios ni headers)
            data_lines = 0
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('-') or 'ASCII' in line.upper():
                    continue
                if ':' in line and any(c in '0123456789ABCDEFabcdef' for c in line):
                    data_lines += 1
            
            # Heurística: SLE5542 tiene ~16 líneas de datos, SLE5528 tiene ~64 líneas
            print(f"[DEBUG] Data lines counted: {data_lines}")
            if data_lines > 30:  # Para 1KB (64 líneas de 16 bytes cada una)
                print(f"[DEBUG] Detected SLE5528 based on data lines count")
                return CARD_TYPE_5528
            else:  # Para 256B (16 líneas de 16 bytes cada una)
                print(f"[DEBUG] Detected SLE5542 based on data lines count")
                return CARD_TYPE_5542
                
        except Exception as e:
            print(f"[DEBUG] Exception in card type detection: {e}")
            # Por defecto, asumir 5542
            return CARD_TYPE_5542
    
    def _load_card_data_from_file(self, session, filepath):
        """Carga los datos de la tarjeta desde un archivo"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            lines = content.split('\n')
            memory_data = []
            internal_psc_5542 = None  # Para almacenar PSC interno si se encuentra
            
            print(f"[DEBUG] Cargando archivo: {filepath}")
            print(f"[DEBUG] Total lines: {len(lines)}")
            
            # Primero, buscar PSC interno en el header (solo para SLE5542)
            if session.card_type == CARD_TYPE_5542:
                for line in lines:
                    line = line.strip()
                    if line.startswith('# Internal PSC (SLE5542):'):
                        try:
                            psc_part = line.split(':', 1)[1].strip()
                            psc_bytes = []
                            for hex_str in psc_part.split():
                                if len(hex_str) == 2 and all(c in '0123456789ABCDEFabcdef' for c in hex_str):
                                    psc_bytes.append(int(hex_str, 16))
                            if len(psc_bytes) == 3:
                                internal_psc_5542 = psc_bytes
                                print(f"[DEBUG] Found internal PSC in file: {' '.join([f'{b:02X}' for b in internal_psc_5542])}")
                                break
                        except Exception as e:
                            print(f"[DEBUG] Error parsing internal PSC: {e}")
            
            # Parsear el archivo para extraer datos hex
            for line_num, line in enumerate(lines):
                original_line = line
                line = line.strip()
                
                # Saltar líneas vacías y comentarios
                if not line or line.startswith('#'):
                    continue
                
                # Verificar si la línea tiene el formato de datos: "DIRECCIÓN: HEX_DATA | ASCII"
                # Las líneas de datos SIEMPRE tienen ':' y la parte antes del ':' es una dirección hex
                if ':' not in line:
                    continue
                
                # Dividir por ':' para separar dirección de datos
                parts = line.split(':', 1)
                if len(parts) < 2:
                    continue
                
                addr_part = parts[0].strip()
                data_part = parts[1].strip()

                # Verificar que la parte de dirección sea válida (formato hex o Page.Row)
                if not addr_part or len(addr_part) > 4:
                    continue
                
                # Verificar que todos los caracteres sean hex válidos o '.'
                if not all(c in '0123456789ABCDEFabcdef.' for c in addr_part):
                    continue
                
                # Filtrar específicamente "Ad" y "Addr" (encabezados)
                if addr_part.upper() in ['AD', 'ADDR']:
                    continue
                
                # Separar datos hex del ASCII si existe el separador '|'
                hex_part = data_part
                if '|' in hex_part:
                    hex_part = hex_part.split('|')[0].strip()
                
                # Extraer bytes hex individuales
                hex_bytes = hex_part.split()
                line_data_count = 0
                for hex_byte in hex_bytes:
                    # Verificar que sea exactamente 2 caracteres hex
                    if len(hex_byte) == 2 and all(c in '0123456789ABCDEFabcdef' for c in hex_byte):
                        memory_data.append(hex_byte.upper())
                        line_data_count += 1
                
                if line_data_count > 0:
                    print(f"[DEBUG] Line {line_num+1}: {line_data_count} bytes extracted from: {original_line[:50]}...")
            
            print(f"[DEBUG] Total bytes extracted: {len(memory_data)}")
            
            # Si no se encontraron suficientes datos, llenar con FF
            target_size = MEMORY_SIZE_5528 if session.card_type == CARD_TYPE_5528 else MEMORY_SIZE_5542
            while len(memory_data) < target_size:
                memory_data.append('FF')
            
            # Truncar si hay demasiados datos
            memory_data = memory_data[:target_size]
            
            print(f"[DEBUG] Final memory size: {len(memory_data)} bytes")
            print(f"[DEBUG] First 10 bytes: {memory_data[:10]}")
            
            # Cargar los datos en la memoria de la sesión
            session.memory_manager.load_memory_dump(memory_data)
            
            # Cargar PSC interno para SLE5542 si se encontró en el archivo
            if session.card_type == CARD_TYPE_5542 and internal_psc_5542 is not None:
                success = session.memory_manager.set_internal_psc(internal_psc_5542)
                if success:
                    print(f"[DEBUG] Internal PSC loaded: {' '.join([f'{b:02X}' for b in internal_psc_5542])}")
                else:
                    print(f"[DEBUG] Failed to set internal PSC")
            
            # Sincronizar estado entre APDU handler y memory manager
            self._synchronize_card_state(session)
            
            # Marcar como modificadas las direcciones que difieren de fábrica
            self._mark_modified_from_factory(session)
            
            session.add_to_log("INFO", f"Card data loaded from: {filepath} ({len(memory_data)} bytes)")
            return True
            
        except Exception as e:
            print(f"[ERROR] Exception in _load_card_data_from_file: {e}")
            session.add_to_log("ERROR", f"Failed to load card data: {str(e)}")
            return False
    
    def get_active_session(self):
        """Obtiene la sesión actualmente activa"""
        if self.active_session_id and self.active_session_id in self.sessions:
            return self.sessions[self.active_session_id]
        return None
    
    def set_active_session(self, session_id):
        """Establece una sesión como activa"""
        if session_id in self.sessions:
            self.active_session_id = session_id
            return True
        return False
    
    def get_session(self, session_id):
        """Obtiene una sesión específica por ID"""
        return self.sessions.get(session_id)
    
    def get_session_by_name(self, card_name):
        """Obtiene una sesión por nombre de tarjeta"""
        for session in self.sessions.values():
            if session.card_name == card_name:
                return session
        return None
    
    def get_all_sessions(self):
        """Obtiene todas las sesiones en orden de creación"""
        return [self.sessions[sid] for sid in self.session_order if sid in self.sessions]
    
    def close_session(self, session_id):
        """Cierra una sesión específica"""
        if session_id not in self.sessions:
            return False
        
        # Limpiar la sesión
        session = self.sessions[session_id]
        session.cleanup()
        
        # Remover de las listas
        del self.sessions[session_id]
        if session_id in self.session_order:
            self.session_order.remove(session_id)
        
        # Si era la sesión activa, no seleccionar automáticamente otra
        if self.active_session_id == session_id:
            self.active_session_id = None
        
        return True
    
    def close_all_sessions(self):
        """Cierra todas las sesiones"""
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            self.close_session(session_id)
    
    def save_session_to_file(self, session_id, filepath):
        """Guarda una sesión específica a un archivo con formato visual (filas y columnas)"""
        session = self.get_session(session_id)
        if not session:
            return False, "Session not found"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # User Info al principio si existe y no es la plantilla por defecto
                from utils.constants import USER_INFO_TEMPLATE
                if (session.user_info and 
                    session.user_info.strip() and 
                    session.user_info.strip() != USER_INFO_TEMPLATE.strip()):
                    f.write(f"# User Info: {session.user_info}\n")
                    f.write("#" + "="*70 + "\n")
                    f.write("\n")
                
                # Encabezado del archivo
                f.write(f"# CardSIM Session: {session.card_name}\n")
                f.write(f"# Card Type: {session._get_card_type_display()}\n")
                f.write(f"# Created: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# PSC Status: {'Verified' if session.psc_verified else 'Not verified'}\n")
                f.write(f"# Card Selected: {'Yes' if session.card_selected else 'No'}\n")
                
                # Guardar PSC interno para SLE5542
                if session.card_type == CARD_TYPE_5542:
                    current_psc = session.memory_manager.get_current_psc()
                    psc_hex = ' '.join([f"{b:02X}" for b in current_psc])
                    f.write(f"# Internal PSC (SLE5542): {psc_hex}\n")
                
                f.write("\n")
                
                # Formato visual similar a la interfaz
                if session.card_type == CARD_TYPE_5528:
                    # Para tarjetas 1KB - mostrar por páginas
                    f.write("# SLE5528 1KB Memory Content (by pages)\n")
                    f.write("# Format: Page.Row: HH HH HH ... | ASCII\n")
                    f.write("#" + "="*69 + "\n\n")
                    
                    memory_data = session.memory_manager.get_memory_dump()
                    
                    # 4 páginas de 256 bytes cada una
                    for page in range(4):
                        f.write(f"# PAGE {page}\n")
                        f.write("Ad: " + " ".join([f"{i:02X}" for i in range(16)]) + "        ASCII\n")
                        f.write("-"*70 + "\n")
                        
                        for row in range(16):
                            addr = page * 256 + row * 16
                            addr_str = f"{page}.{row:X}: "
                            hex_part = ""
                            ascii_part = ""
                            
                            for col in range(16):
                                byte_addr = addr + col
                                if byte_addr < len(memory_data):
                                    byte_val = memory_data[byte_addr]
                                    hex_part += f"{byte_val} "
                                    
                                    # ASCII
                                    try:
                                        ascii_val = int(byte_val, 16)
                                        if 32 <= ascii_val <= 126:
                                            ascii_part += chr(ascii_val)
                                        else:
                                            ascii_part += "."
                                    except:
                                        ascii_part += "."
                                else:
                                    hex_part += "FF "
                                    ascii_part += "."
                            
                            f.write(f"{addr_str}{hex_part.rstrip()} | {ascii_part}\n")
                        f.write("\n")
                        
                else:
                    # Para tarjetas 256B - formato compacto
                    f.write("# SLE5542 256B Memory Content\n") 
                    f.write("# Format: Row: HH HH HH ... | ASCII\n")
                    f.write("#" + "="*69 + "\n\n")
                    f.write("Ad: " + " ".join([f"{i:02X}" for i in range(16)]) + "        ASCII\n")
                    f.write("-"*70 + "\n")
                    
                    memory_data = session.memory_manager.get_memory_dump()
                    
                    for row in range(16):  # 16 filas de 16 bytes = 256 bytes
                        addr = row * 16
                        addr_str = f"{addr:02X}: "
                        hex_part = ""
                        ascii_part = ""
                        
                        for col in range(16):
                            byte_addr = addr + col
                            if byte_addr < len(memory_data):
                                byte_val = memory_data[byte_addr]
                                hex_part += f"{byte_val} "
                                
                                # ASCII
                                try:
                                    ascii_val = int(byte_val, 16)
                                    if 32 <= ascii_val <= 126:
                                        ascii_part += chr(ascii_val)
                                    else:
                                        ascii_part += "."
                                except:
                                    ascii_part += "."
                            else:
                                hex_part += "FF "
                                ascii_part += "."
                        
                        f.write(f"{addr_str}{hex_part.rstrip()} | {ascii_part}\n")
                
                f.write(f"\n# End of {session.card_name} memory dump\n")
            
            session.add_to_log("INFO", f"Card saved to: {filepath}")
            return True, "Card saved successfully"
            
        except Exception as e:
            return False, f"Error saving card: {str(e)}"
    
    def has_active_session(self):
        """Verifica si hay una sesión activa"""
        return self.active_session_id is not None and self.active_session_id in self.sessions
    
    def _synchronize_card_state(self, session):
        """Sincroniza el estado entre APDU handler y memory manager después de cargar."""
        try:
            # Para SLE5528, sincronizar el error counter que es visible en memoria
            if session.card_type == "SLE5528":
                # Obtener el error counter de la memoria y sincronizar con APDU handler
                error_counter_address = 0x3FD
                memory_data = session.memory_manager.memory
                if error_counter_address < len(memory_data):
                    error_counter_value = memory_data[error_counter_address]
                    session.apdu_handler.error_counter = error_counter_value
                    print(f"[SYNC] Error counter sincronizado: {error_counter_value}")
                    
                # Verificar PSC desde memoria
                psc_addresses = [0x3FE, 0x3FF]
                psc_values = []
                for addr in psc_addresses:
                    if addr < len(memory_data):
                        psc_values.append(memory_data[addr])
                print(f"[SYNC] PSC values: {[hex(val) for val in psc_values]}")
                
            elif session.card_type == "SLE5542":
                # Para SLE5542, el error counter no es visible en memoria
                # Verificar el PSC
                psc_addresses = [0xFD, 0xFE, 0xFF]
                memory_data = session.memory_manager.memory
                psc_values = []
                for addr in psc_addresses:
                    if addr < len(memory_data):
                        psc_values.append(memory_data[addr])
                print(f"[SYNC] PSC values: {[hex(val) for val in psc_values]}")
                
        except Exception as e:
            print(f"[ERROR] Error en sincronización de estado: {e}")

    def _mark_modified_from_factory(self, session):
        """Marca como modificadas las direcciones que difieren de la configuración de fábrica"""
        # Crear una sesión temporal con configuración de fábrica
        factory_memory = session.memory_manager.__class__()
        factory_memory.initialize_memory(session.card_type)
        factory_data = factory_memory.get_memory_dump()
        
        # Comparar con los datos actuales y marcar diferencias
        current_data = session.memory_manager.get_memory_dump()
        
        session.memory_manager.clear_modifications()  # Limpiar primero
        
        for address, (current_byte, factory_byte) in enumerate(zip(current_data, factory_data)):
            if current_byte.upper() != factory_byte.upper():
                # Solo marcar como modificado si no es una dirección especial
                from utils.constants import (PSC_ADDRESS_5542, PSC_ADDRESS_5528, 
                                           READONLY_ADDRESSES_5542, READONLY_ADDRESSES_5528,
                                           CARD_TYPE_5542, CARD_TYPE_5528)
                
                # Configurar direcciones según tipo de tarjeta
                card_type = session.memory_manager.card_type
                if card_type == CARD_TYPE_5542:
                    readonly_addresses = READONLY_ADDRESSES_5542
                    psc_start = PSC_ADDRESS_5542
                    psc_size = 3
                else:  # CARD_TYPE_5528
                    readonly_addresses = READONLY_ADDRESSES_5528
                    psc_start = PSC_ADDRESS_5528
                    psc_size = 2
                
                if address not in readonly_addresses and not (psc_start <= address <= psc_start + psc_size - 1):
                    session.memory_manager.modified_addresses.add(address)
    
    def __del__(self):
        """Destructor - limpia todas las sesiones"""
        self.close_all_sessions()
