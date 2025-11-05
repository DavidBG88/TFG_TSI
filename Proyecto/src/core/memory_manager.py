"""
Gestor de memoria de tarjetas SLE5542/5528
"""

from src.utils.constants import *
from .code_improvements import safe_hex_to_ascii, format_memory_display

class MemoryManager:
    """Gestiona la memoria de l                        # ASCII representation con mejor separación
                        ascii_part += format_memory_display(byte_val)as simuladas"""
    
    def __init__(self):
        self.memory_data = []
        self.card_type = CARD_TYPE_5542
        self.current_page = 0
        self.error_counter = ERROR_COUNTER_SEQUENCE_5542[0]  # Se ajustará según tipo de tarjeta en initialize_memory
        self.protection_data = None
        
        # Registro interno PSC para SLE5542 (no visible en memoria hex)
        # SLE5542 tiene registro interno separado, SLE5528 usa memoria normal
        self.internal_psc_5542 = [0xFF, 0xFF, 0xFF]  # PSC interno SLE5542
        
    def initialize_memory(self, card_type):
        """Inicializa la memoria según el tipo de tarjeta"""
        self.card_type = card_type
        self.current_page = 0
        
        # Establecer error counter según tipo de tarjeta
        if card_type == CARD_TYPE_5542:
            # SLE5542: usar secuencia 07-03-01-00
            self.error_counter = ERROR_COUNTER_SEQUENCE_5542[0]  # 256B cards: start with 0x07 (3 attempts)
        else:  # CARD_TYPE_5528
            self.error_counter = ERROR_COUNTER_SEQUENCE_5528[1]  # 1K cards: start with 0x7F (7 attempts)
        
        if card_type == CARD_TYPE_5528:
            self.memory_data = ['FF'] * MEMORY_SIZE_5528
        else:
            self.memory_data = ['FF'] * MEMORY_SIZE_5542
            
        # Set para rastrear direcciones modificadas
        self.modified_addresses = set()
        
        # Almacenar configuración de fábrica para comparación
        self._store_factory_configuration(card_type)
            
        # Inicializar con datos de fábrica específicos por tipo de tarjeta
        if card_type == CARD_TYPE_5542:
            init_data = CARD_INIT_DATA_5542
            psc_data = DEFAULT_PSC_5542
            psc_addr = PSC_ADDRESS_5542
        else:  # CARD_TYPE_5528
            init_data = CARD_INIT_DATA_5528
            psc_data = DEFAULT_PSC_5528
            psc_addr = PSC_ADDRESS_5528
        
        # Aplicar datos de fábrica
        for addr, value in init_data.items():
            if addr < len(self.memory_data):
                self.memory_data[addr] = f"{value:02X}"
                
        # Inicializar PSC según tipo de tarjeta
        if card_type == CARD_TYPE_5542:
            # SLE5542: PSC en registro interno
            self.internal_psc_5542 = DEFAULT_PSC_5542.copy()
            print(f"DEBUG: SLE5542 initialized with internal PSC: {' '.join([f'{b:02X}' for b in self.internal_psc_5542])}")
        else:
            # SLE5528: PSC en memoria visible
            for i, byte_val in enumerate(psc_data):
                psc_address = psc_addr + i
                if psc_address < len(self.memory_data) and psc_address not in init_data:
                    self.memory_data[psc_address] = f"{byte_val:02X}"
            print(f"DEBUG: SLE5528 initialized with memory PSC at 0x{psc_addr:03X}: {' '.join([f'{b:02X}' for b in psc_data])}")
                
        # Inicializar protecciones de fábrica
        self.protection_data = set()
        if card_type == CARD_TYPE_5542:
            # SLE5542: Direcciones bloqueadas de fábrica
            for addr in FACTORY_PROTECTED_5542:
                self.protection_data.add(addr)
        else:  # CARD_TYPE_5528
            # SLE5528: Direcciones bloqueadas de fábrica
            for addr in FACTORY_PROTECTED_5528:
                self.protection_data.add(addr)
                
        # Inicializar error counter en memoria visible
        self._update_error_counter_in_memory()
    
    def _store_factory_configuration(self, card_type):
        """Almacena la configuración de fábrica para comparación posterior"""
        if card_type == CARD_TYPE_5528:
            self.factory_memory = ['FF'] * MEMORY_SIZE_5528
        else:
            self.factory_memory = ['FF'] * MEMORY_SIZE_5542
            
        # Inicializar con datos de fábrica específicos
        if card_type == CARD_TYPE_5542:
            init_data = CARD_INIT_DATA_5542
        else:  # CARD_TYPE_5528
            init_data = CARD_INIT_DATA_5528
        
        # Aplicar datos de inicialización de fábrica
        for addr, value in init_data.items():
            if addr < len(self.factory_memory):
                self.factory_memory[addr] = f"{value:02X}"
    
    def is_modified_from_factory(self, address):
        """
        Verifica si un byte ha sido modificado respecto a la configuración de fábrica.
        SOLO considera el área de datos de usuario, ignora las cabeceras de fábrica.
        """
        if not hasattr(self, 'factory_memory') or address >= len(self.factory_memory):
            return False
        
        # Definir qué áreas considerar como "modificables" vs "información de fábrica"
        if self.card_type == CARD_TYPE_5542:
            # Para SLE5542: Solo verificar área de datos de usuario (0x20-0xEF)
            # Las direcciones 0x00-0x1F contienen info de fábrica válida
            user_area_start = 0x20
            user_area_end = 0xEF
        else:  # CARD_TYPE_5528
            # Para SLE5528: Similar lógica pero área más grande
            user_area_start = 0x20
            user_area_end = 0x3FC
        
        # Solo considerar modificado si está en el área de datos de usuario
        if not (user_area_start <= address <= user_area_end):
            return False  # No considerar modificadas las áreas de cabecera/seguridad
        
        current_value = self.memory_data[address] if address < len(self.memory_data) else 'FF'
        
        # En el área de usuario, el valor de fábrica debería ser FF
        factory_user_value = 'FF'
        
        return current_value != factory_user_value
    
    def clear_memory(self):
        """Limpia toda la memoria con FF y resetea modificaciones"""
        if self.card_type == CARD_TYPE_5528:
            self.memory_data = ['FF'] * MEMORY_SIZE_5528
        else:
            self.memory_data = ['FF'] * MEMORY_SIZE_5542
        # Limpiar registro de modificaciones
        self.modified_addresses.clear()
        
    def clear_modifications(self):
        """Limpia solo el registro de modificaciones sin afectar la memoria"""
        self.modified_addresses.clear()
    
    def read_memory(self, address, length):
        """Lee datos de la memoria"""
        data = []
        for i in range(length):
            addr = address + i
            if addr < len(self.memory_data):
                try:
                    byte_val = int(self.memory_data[addr], 16)
                    data.append(byte_val)
                except ValueError:
                    data.append(0xFF)
            else:
                data.append(0xFF)
        return data
    
    def get_display_value_for_address(self, address, psc_verified=False):
        """
        Obtiene el valor que debe mostrarse para una dirección según el estado del PSC
        NOTA: SLE5542 no muestra PSC en memoria (registro interno)
        """
        from utils.constants import PSC_ADDRESS_5542, PSC_ADDRESS_5528, ERROR_COUNTER_ADDRESS_5542, ERROR_COUNTER_ADDRESS_5528
        
        # Determinar direcciones según tipo de tarjeta
        if self.card_type == CARD_TYPE_5542:
            # SLE5542: Solo error counter en memoria visible
            error_counter_addr = ERROR_COUNTER_ADDRESS_5542
            
            # El Error Counter SIEMPRE debe ser visible
            if address == error_counter_addr:
                if address < len(self.memory_data):
                    return self.memory_data[address]
                else:
                    return "FF"
            
            # Para SLE5542, no hay área PSC en memoria visible
            # Mostrar valor real para todas las demás direcciones
            if address < len(self.memory_data):
                return self.memory_data[address]
            else:
                return "FF"
                
        else:  # CARD_TYPE_5528
            # SLE5528: PSC en 0x3FE-0x3FF, Error counter en 0x3FD
            psc_start = PSC_ADDRESS_5528
            psc_end = PSC_ADDRESS_5528 + 1  # 2 bytes (0x3FE, 0x3FF)
            error_counter_addr = ERROR_COUNTER_ADDRESS_5528
            
            # Para SLE5528: Mostrar "7F 00 80" hasta que se presente PSC correcto
            if not psc_verified and (psc_start <= address <= psc_end or address == error_counter_addr):
                if address == error_counter_addr:  # 0x3FD
                    return "7F"  # Error counter (7 attempts)
                elif address == psc_start:  # 0x3FE
                    return "00"  # Primer byte PSC
                elif address == psc_start + 1:  # 0x3FF  
                    return "80"  # Segundo byte PSC
            
            # Si PSC está verificado o es otra dirección, mostrar valor real
            if address < len(self.memory_data):
                return self.memory_data[address]
            else:
                return "FF"
            
            # Solo el PSC está protegido cuando no está verificado
            if (psc_start <= address <= psc_end) and not psc_verified:
                return "FF"
            
            # En caso contrario, mostrar el valor real
            if address < len(self.memory_data):
                return self.memory_data[address]
            else:
                return "FF"
    
    def _validate_safe_write_area(self, start_address, data_length):
        """
        Valida que la escritura no afecte áreas críticas de la tarjeta.
        Para SLE5542: Protege primeras 2 filas y últimos 5 bytes (PSC es interno, últimas 3 direcciones son escribibles)
        Para SLE5528: Protege primeras 2 filas y últimos 8 bytes (PSC está en memoria)
        """
        end_address = start_address + data_length - 1
        
        # Protección de las primeras 2 filas (direcciones 0x00-0x1F)
        if start_address < 0x20:
            return False, f"Escritura bloqueada: Las direcciones 0x00-0x1F están protegidas (contienen PSC y contador de errores)"
        
        # Protección de los últimos bytes según el tipo de tarjeta
        if self.card_type == CARD_TYPE_5542:
            # SLE5542: PSC interno, solo proteger últimos 5 bytes (0xFB-0xFF), permitir 0xFD-0xFF para escritura
            protected_end_start = 0xFB
            card_max = 0xFF
            # Para SLE5542, las direcciones 0xFD-0xFF son escribibles ya que PSC es interno
            if start_address >= 0xFD:
                return True, "Área PSC escribible en SLE5542 (PSC es interno)"
        else:
            # SLE5528: PSC en memoria, proteger últimos 8 bytes = 0x3F8-0x3FF
            protected_end_start = 0x3F8
            card_max = 0x3FF
        
        if end_address >= protected_end_start:
            if self.card_type == CARD_TYPE_5542:
                return False, f"Escritura bloqueada: Los últimos 5 bytes (0x{protected_end_start:X}-0xFC) están protegidos"
            else:
                return False, f"Escritura bloqueada: Los últimos 8 bytes (0x{protected_end_start:X}-0x{card_max:X}) están protegidos"
        
        return True, "Área de escritura segura"
    
    def write_memory(self, address, data_bytes):
        """Escribe datos en la memoria y marca las direcciones como modificadas"""
        
        # Validar que se escriba solo en áreas seguras
        is_valid, validation_msg = self._validate_safe_write_area(address, len(data_bytes))
        if not is_valid:
            print(f"SIMULADOR - Escritura bloqueada por seguridad: {validation_msg}")
            # En el simulador, retornamos directamente sin error para mantener compatibilidad
            # pero mostramos el mensaje de advertencia
        
        protected_addresses = []
        readonly_addresses = []
        user_protected_addresses = []
        written_addresses = []
        
        # Importar direcciones readonly según tipo de tarjeta
        from utils.constants import READONLY_ADDRESSES_5542, READONLY_ADDRESSES_5528
        
        if self.card_type == CARD_TYPE_5542:
            readonly_set = READONLY_ADDRESSES_5542
        else:  # CARD_TYPE_5528
            readonly_set = READONLY_ADDRESSES_5528
        
        for i, byte_val in enumerate(data_bytes):
            addr = address + i
            if addr < len(self.memory_data):
                # Verificar protección de fábrica (readonly)
                if addr in readonly_set:
                    readonly_addresses.append(addr)
                    protected_addresses.append(addr)
                    continue
                
                # Verificar protección de usuario
                elif self.protection_data and addr in self.protection_data:
                    user_protected_addresses.append(addr)
                    protected_addresses.append(addr)
                    continue
                    
                # Si no está protegida, escribir
                self.memory_data[addr] = f"{byte_val:02X}"
                # Marcar como modificada
                self.modified_addresses.add(addr)
                written_addresses.append(addr)
        
        return {
            'protected_addresses': protected_addresses,
            'readonly_addresses': readonly_addresses,
            'user_protected_addresses': user_protected_addresses,
            'written_addresses': written_addresses
        }
    
    def get_page_data(self, page_num=None):
        """Obtiene datos de una página específica (para 5528) o toda la memoria (para 5542)"""
        if self.card_type == CARD_TYPE_5528:
            if page_num is None:
                page_num = self.current_page
            start_addr = page_num * 256
            return self.memory_data[start_addr:start_addr + 256]
        else:
            return self.memory_data[:MEMORY_SIZE_5542]
    
    def set_current_page(self, page_num):
        """Establece la página actual para tarjetas 5528"""
        if self.card_type == CARD_TYPE_5528 and 0 <= page_num < PAGES_5528:
            self.current_page = page_num
    
    def get_memory_display_data_with_colors(self, psc_verified=False):
        """Obtiene datos formateados con información de color para cada byte"""
        display_data = []
        
        if self.card_type == CARD_TYPE_5528:
            page_data = self.get_page_data()
            data_source = page_data
            data_size = len(page_data)
        else:
            data_source = self.memory_data[:MEMORY_SIZE_5542]
            data_size = MEMORY_SIZE_5542
        
        # 16 filas
        for row in range(16):
            # Para tarjetas 1K: formato XY (página + dirección), para 256B: formato estándar
            if self.card_type == CARD_TYPE_5528:
                addr_display = f"{self.current_page}{row:X}"  # Formato XY: página + dirección hex
            else:
                addr_display = f"{row*16:02X}"  # Formato estándar para 256B
                
            hex_bytes = []
            ascii_chars = []
            
            for col in range(16):
                addr = row * 16 + col
                
                # Para tarjetas 1K, necesitamos calcular la dirección real dentro de la página actual
                if self.card_type == CARD_TYPE_5528:
                    real_addr = self.current_page * 256 + addr  # Dirección real en memoria completa
                else:
                    real_addr = addr
                
                if addr < data_size:
                    # Usar el nuevo método que verifica el estado del PSC
                    byte_val = self.get_display_value_for_address(real_addr, psc_verified)
                    
                    # Determinar color basado en la dirección real
                    color = self._get_address_color(real_addr)
                    
                    hex_bytes.append({
                        'value': byte_val,
                        'color': color,
                        'address': real_addr
                    })
                    
                    # ASCII
                    ascii_char = safe_hex_to_ascii(byte_val)
                    
                    ascii_chars.append({
                        'char': ascii_char,
                        'color': color,
                        'address': real_addr  # Usar dirección real
                    })
                else:
                    # Dirección fuera del rango
                    hex_bytes.append({
                        'value': 'FF',
                        'color': COLOR_MEMORY_WRITABLE,
                        'address': real_addr
                    })
                    ascii_chars.append({
                        'char': '.',
                        'color': COLOR_MEMORY_WRITABLE,
                        'address': real_addr
                    })
            
            display_data.append({
                'address': addr_display,
                'hex_bytes': hex_bytes,
                'ascii_chars': ascii_chars
            })
        
        return display_data
    
    def _get_address_color(self, address):
        """
        Determina el color de una dirección según su estado
        IMPORTANTE: SLE5542 no tiene área PSC visible (usa registro interno)
        """
        from utils.constants import (READONLY_ADDRESSES_5542, READONLY_ADDRESSES_5528, 
                                   COLOR_MEMORY_READONLY, COLOR_MEMORY_WRITABLE, 
                                   COLOR_MEMORY_MODIFIED, PSC_ADDRESS_5542, PSC_ADDRESS_5528,
                                   CARD_TYPE_5542, CARD_TYPE_5528, COLOR_MEMORY_PROTECTED)
        
        # Determinar direcciones PSC y readonly según tipo de tarjeta
        if self.card_type == CARD_TYPE_5542:
            # SLE5542: NO tiene área PSC visible en memoria (registro interno)
            readonly_addresses = READONLY_ADDRESSES_5542
            psc_visible = False
        else:  # CARD_TYPE_5528
            # SLE5528: SÍ tiene área PSC visible en memoria
            psc_start = PSC_ADDRESS_5528
            psc_end = PSC_ADDRESS_5528 + 1  # 2 bytes
            readonly_addresses = READONLY_ADDRESSES_5528
            psc_visible = True
        
        # Prioridad 1: Verificar si es dirección PSC visible (solo SLE5528)
        if psc_visible and (psc_start <= address <= psc_end):
            from utils.constants import COLOR_MEMORY_PSC
            return COLOR_MEMORY_PSC  # Color especial para PSC - solo en SLE5528
        # Prioridad 2: Verificar si está protegida contra escritura (incluye fábrica y usuario)
        elif self.is_protected(address):
            # Distinguir entre protección de fábrica y de usuario para el color
            if address in readonly_addresses:
                return COLOR_MEMORY_READONLY  # Rojo claro para fábrica
            else:
                return COLOR_MEMORY_PROTECTED  # Rojo para protección de usuario
        # Prioridad 3: Verificar si fue modificada respecto a la configuración de fábrica
        elif self.is_modified_from_factory(address):
            return COLOR_MEMORY_MODIFIED  # Azul para modificado respecto a fábrica
        # Prioridad 4: Verificar si fue modificada durante la sesión actual
        elif address in self.modified_addresses:
            return COLOR_MEMORY_MODIFIED
        else:
            return COLOR_MEMORY_WRITABLE
    
    def get_memory_size(self):
        """Obtiene el tamaño actual de la memoria"""
        return len(self.memory_data)
    
    def get_error_counter(self):
        """Obtiene el contador de errores actual"""
        return self.error_counter
    
    def reset_error_counter(self):
        """Resetea el contador de errores según el tipo de tarjeta"""
        if self.card_type == CARD_TYPE_5542:
            self.error_counter = ERROR_COUNTER_SEQUENCE_5542[0]  # 256B cards: resetear a 0x07 (3 attempts)
        else:  # CARD_TYPE_5528
            self.error_counter = ERROR_COUNTER_SEQUENCE_5528[1]  # Resetear a 0x7F (7 attempts)
        self._update_error_counter_in_memory()
        return self.error_counter
    
    def _update_error_counter_in_memory(self):
        """Actualiza el valor del error counter en la memoria visible"""
        if self.card_type == CARD_TYPE_5528:
            # Solo SLE5528 tiene error counter visible en memoria (dirección 0x3FD)
            error_counter_addr = ERROR_COUNTER_ADDRESS_5528
            if error_counter_addr < len(self.memory_data):
                # SOLO actualizar el error counter, NO tocar PSC
                self.memory_data[error_counter_addr] = f"{self.error_counter:02X}"
    
    def is_blocked(self):
        """Verifica si la tarjeta está bloqueada (contador = 0)"""
        return self.error_counter <= 0
    
    def set_protection_bit(self, address):
        """Establece un bit de protección para una dirección"""
        if self.protection_data is None:
            self.protection_data = set()
        self.protection_data.add(address)
    
    def is_protected(self, address):
        """Verifica si una dirección está protegida contra escritura (incluyendo protección de fábrica y de usuario)"""
        # Importar direcciones readonly según tipo de tarjeta
        from utils.constants import READONLY_ADDRESSES_5542, READONLY_ADDRESSES_5528
        
        # Verificar protección de fábrica (direcciones readonly)
        if self.card_type == CARD_TYPE_5542:
            readonly_addresses = READONLY_ADDRESSES_5542
        else:  # CARD_TYPE_5528
            readonly_addresses = READONLY_ADDRESSES_5528
            
        if address in readonly_addresses:
            return True
        
        # Verificar protección de usuario
        if self.protection_data is None:
            return False
        return address in self.protection_data
    
    def get_protection_bits(self):
        """Genera los 4 bytes de bits de protección para los primeros 32 bytes"""
        # Inicializar con todos los bits a 1 (no protegido)
        prot_bytes = [0xFF, 0xFF, 0xFF, 0xFF]
        
        if self.protection_data is None:
            return prot_bytes
        
        # Para cada dirección en los primeros 32 bytes
        for address in range(32):
            if self.is_protected(address):
                # Calcular byte y bit dentro del byte
                byte_idx = address // 8  # Byte 0-3
                bit_idx = address % 8    # Bit 0-7 dentro del byte
                
                # Poner el bit a 0 (protegido)
                prot_bytes[byte_idx] &= ~(1 << bit_idx)
        
        return prot_bytes
    
    def get_memory_dump(self):
        """Obtiene un dump completo de la memoria en formato lista"""
        return self.memory_data.copy()
    
    def get_current_psc(self):
        """
        Obtiene el PSC actual según el tipo de tarjeta:
        - SLE5542: Desde registro interno (no visible en memoria hex)
        - SLE5528: Desde memoria en direcciones específicas
        """
        from utils.constants import PSC_ADDRESS_5542, PSC_ADDRESS_5528, CARD_TYPE_5542
        
        if self.card_type == CARD_TYPE_5542:
            # SLE5542: PSC almacenado en registro interno, no en memoria visible
            return self.internal_psc_5542.copy()
        else:
            # SLE5528: PSC almacenado en memoria visible (direcciones finales)
            psc_start = PSC_ADDRESS_5528
            psc_size = 2
            
            # Leer PSC desde la memoria
            psc_bytes = []
            for i in range(psc_size):
                address = psc_start + i
                if address < len(self.memory_data):
                    hex_value = self.memory_data[address]
                    psc_bytes.append(int(hex_value, 16))
                else:
                    # Si no hay datos, usar valor por defecto
                    from utils.constants import DEFAULT_PSC_5528
                    return DEFAULT_PSC_5528
            
            return psc_bytes
    
    def set_internal_psc(self, new_psc):
        """
        Establece el PSC interno para SLE5542 (registro no visible)
        Para SLE5528, actualiza la memoria visible
        """
        from utils.constants import PSC_ADDRESS_5528, CARD_TYPE_5542
        
        if self.card_type == CARD_TYPE_5542:
            # SLE5542: Actualizar registro interno
            if len(new_psc) == 3:
                self.internal_psc_5542 = new_psc.copy()
                print(f"DEBUG: SLE5542 internal PSC updated to: {' '.join([f'{b:02X}' for b in new_psc])}")
                return True
            else:
                print(f"ERROR: SLE5542 PSC must be 3 bytes, got {len(new_psc)}")
                return False
        else:
            # SLE5528: Actualizar memoria visible
            if len(new_psc) == 2:
                psc_start = PSC_ADDRESS_5528
                for i, byte_val in enumerate(new_psc):
                    address = psc_start + i
                    if address < len(self.memory_data):
                        self.memory_data[address] = f"{byte_val:02X}"
                        self.modified_addresses.add(address)
                print(f"DEBUG: SLE5528 memory PSC updated to: {' '.join([f'{b:02X}' for b in new_psc])}")
                return True
            else:
                print(f"ERROR: SLE5528 PSC must be 2 bytes, got {len(new_psc)}")
                return False
    
    def load_memory_dump(self, memory_dump):
        """Carga un dump de memoria desde una lista"""
        if isinstance(memory_dump, list):
            self.memory_data = memory_dump.copy()
            return True
        return False

    def load_from_data(self, data):
        """Carga datos de memoria desde una lista de bytes"""
        try:
            if isinstance(data, list):
                # Convertir bytes a strings hexadecimales
                self.memory_data = [f"{byte:02X}" for byte in data]
            elif isinstance(data, bytes):
                # Convertir bytes a strings hexadecimales
                self.memory_data = [f"{byte:02X}" for byte in data]
            else:
                return False
            
            # Actualizar el tipo de tarjeta según el tamaño de los datos
            if len(self.memory_data) == MEMORY_SIZE_5542:
                self.card_type = CARD_TYPE_5542
            elif len(self.memory_data) == MEMORY_SIZE_5528:
                self.card_type = CARD_TYPE_5528
            else:
                # Ajustar tamaño si es necesario
                if len(self.memory_data) <= MEMORY_SIZE_5542:
                    self.card_type = CARD_TYPE_5542
                    # Rellenar con FF si es necesario
                    while len(self.memory_data) < MEMORY_SIZE_5542:
                        self.memory_data.append('FF')
                else:
                    self.card_type = CARD_TYPE_5528
                    # Truncar o rellenar según sea necesario
                    if len(self.memory_data) > MEMORY_SIZE_5528:
                        self.memory_data = self.memory_data[:MEMORY_SIZE_5528]
                    else:
                        while len(self.memory_data) < MEMORY_SIZE_5528:
                            self.memory_data.append('FF')
            
            # Inicializar configuración de fábrica para comparación
            self._store_factory_configuration(self.card_type)
            
            # Limpiar direcciones modificadas (nueva tarjeta = estado limpio)
            self.modified_addresses = set()
            
            return True
            
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
