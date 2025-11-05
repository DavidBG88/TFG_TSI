"""
Physical Card Handler - Manejo de tarjetas físicas con lectores reales
Basado en el código de Gestión Náutica para comunicación PC/SC
"""

try:
    from smartcard.System import readers
    from smartcard.util import toHexString, toBytes
    SMARTCARD_AVAILABLE = True
except ImportError:
    SMARTCARD_AVAILABLE = False
    print("Warning: pyscard library not found. Install with: pip install pyscard")

from src.utils.constants import CARD_TYPE_5542, CARD_TYPE_5528

class PhysicalCardHandler:
    """Maneja la comunicación con lectores de tarjetas físicas"""
    
    def __init__(self):
        self.connection = None
        self.reader = None
        
    def get_safe_write_areas(self, card_type):
        """
        Retorna información sobre las áreas seguras de escritura.
        
        Returns:
            dict: Información sobre áreas protegidas y escribibles
        """
        if card_type == CARD_TYPE_5542:
            return {
                'card_name': 'SLE5542',
                'total_size': 256,
                'protected_areas': [
                    {'start': 0x00, 'end': 0x1F, 'description': 'Primeras 2 filas (datos de fábrica)'},
                    {'start': 0xF8, 'end': 0xFF, 'description': 'Últimos 8 bytes (padding de seguridad)'}
                ],
                'writable_area': {'start': 0x20, 'end': 0xF7, 'size': 216},
                'address_format': '0x{:02X}'
            }
        else:  # CARD_TYPE_5528
            return {
                'card_name': 'SLE5528',
                'total_size': 1024,
                'protected_areas': [
                    {'start': 0x000, 'end': 0x01F, 'description': 'Primeras 2 filas (datos de fábrica)'},
                    {'start': 0x3FD, 'end': 0x3FF, 'description': 'Últimos 3 bytes (Error Counter + PSC)'}
                ],
                'writable_area': {'start': 0x20, 'end': 0x3FC, 'size': 989},
                'address_format': '0x{:03X}'
            }
    
    def check_smartcard_library(self):
        """Verifica si la librería pyscard está disponible"""
        return SMARTCARD_AVAILABLE
    
    def get_available_readers(self):
        """Obtiene la lista de lectores disponibles"""
        if not SMARTCARD_AVAILABLE:
            return []
        
        try:
            reader_list = readers()
            return [str(reader) for reader in reader_list]
        except Exception as e:
            print(f"Error obteniendo lectores: {e}")
            return []
    
    def connect_to_reader(self, reader_identifier=0):
        """Conecta al lector especificado (índice o nombre)"""
        if not SMARTCARD_AVAILABLE:
            return False
        
        try:
            reader_list = readers()
            if not reader_list:
                return False
            
            # Si es string, buscar por nombre
            if isinstance(reader_identifier, str):
                reader_names = [str(reader) for reader in reader_list]
                if reader_identifier not in reader_names:
                    return False
                reader_index = reader_names.index(reader_identifier)
            else:
                # Es un índice
                reader_index = reader_identifier
                if reader_index >= len(reader_list):
                    return False
            
            self.reader = reader_list[reader_index]
            self.connection = self.reader.createConnection()
            self.connection.connect()
            
            return True
            
        except Exception as e:
            print(f"Error conectando al lector: {e}")
            return False
    
    def disconnect(self):
        """Desconecta del lector"""
        try:
            if self.connection:
                self.connection.disconnect()
                self.connection = None
                self.reader = None
            return True, "Desconectado correctamente"
        except Exception as e:
            return False, f"Error desconectando: {e}"
    
    def send_apdu(self, apdu):
        """Envía una APDU y devuelve la respuesta"""
        if not self.connection:
            return None, 0x6F, 0x00, "No hay conexión activa"
        
        try:
            response, sw1, sw2 = self.connection.transmit(apdu)
            apdu_hex = " ".join([f"{b:02X}" for b in apdu])
            resp_hex = " ".join([f"{b:02X}" for b in response]) if response else ""
            
            print(f"APDU: {apdu_hex}")
            if response:
                print(f"Response: {resp_hex}")
            print(f"SW: {sw1:02X} {sw2:02X}")
            
            return response, sw1, sw2, "OK"
            
        except Exception as e:
            return None, 0x6F, 0x00, f"Error enviando APDU: {e}"
    
    def select_card(self, card_type=CARD_TYPE_5542):
        """Selecciona la tarjeta según su tipo"""
        if card_type == CARD_TYPE_5542:
            # SLE5542: FF A4 00 00 01 06
            select_apdu = [0xFF, 0xA4, 0x00, 0x00, 0x01, 0x06]
        else:
            # SLE5528: FF A4 00 00 01 05
            select_apdu = [0xFF, 0xA4, 0x00, 0x00, 0x01, 0x05]
        
        response, sw1, sw2, status = self.send_apdu(select_apdu)
        
        if sw1 == 0x90 and sw2 == 0x00:
            return True, f"Tarjeta {card_type} seleccionada correctamente"
        else:
            return False, f"Error seleccionando tarjeta: SW={sw1:02X}{sw2:02X}"
    
    def present_psc(self, card_type=CARD_TYPE_5542, psc=None):
        """Presenta el PSC (Password Security Code) según el tipo de tarjeta
        Devuelve: (success: bool, message: str, error_counter: int|None)
        """
        if psc is None:
            # PSC por defecto (FF FF FF para 5542, FF FF para 5528)
            if card_type == CARD_TYPE_5542:
                psc = [0xFF, 0xFF, 0xFF]
            else:
                psc = [0xFF, 0xFF]
        
        if card_type == CARD_TYPE_5542:
            # SLE5542: FF 20 00 00 03 P1 P2 P3 (3 bytes PSC)
            psc_apdu = [0xFF, 0x20, 0x00, 0x00, 0x03] + psc[:3]
            # Respuesta esperada: 90 07
            expected_sw1, expected_sw2 = 0x90, 0x07
        else:
            # SLE5528: FF 20 00 00 02 P1 P2 (2 bytes PSC)
            psc_apdu = [0xFF, 0x20, 0x00, 0x00, 0x02] + psc[:2]
            # Respuesta esperada: 90 FF
            expected_sw1, expected_sw2 = 0x90, 0xFF
        
        response, sw1, sw2, status = self.send_apdu(psc_apdu)
        
        if sw1 == expected_sw1 and sw2 == expected_sw2:
            return True, f"PSC presentado correctamente para {card_type}", sw2
        else:
            # Si falló, sw2 contiene el Error Counter
            return False, f"Error presentando PSC: SW={sw1:02X}{sw2:02X} (esperado: {expected_sw1:02X}{expected_sw2:02X})", sw2
    
    def change_psc(self, card_type=CARD_TYPE_5542, new_psc=None):
        """Cambia el PSC (Password Security Code) en la tarjeta física"""
        if new_psc is None:
            return False, "Nuevo PSC no puede ser None"
        
        if card_type == CARD_TYPE_5542:
            # SLE5542: FF D2 00 01 03 P1 P2 P3 (3 bytes PSC) - Comando nativo
            if len(new_psc) != 3:
                return False, "PSC para SLE5542 debe tener exactamente 3 bytes"
            change_psc_apdu = [0xFF, 0xD2, 0x00, 0x01, 0x03] + new_psc[:3]
        else:
            # SLE5528: No tiene comando Change PSC nativo, escribir directamente en 0x3FE-0x3FF
            if len(new_psc) != 2:
                return False, "PSC para SLE5528 debe tener exactamente 2 bytes"
            # FF D0 03 FE 02 P1 P2 (escribir 2 bytes en dirección 0x3FE)
            change_psc_apdu = [0xFF, 0xD0, 0x03, 0xFE, 0x02] + new_psc[:2]

        response, sw1, sw2, status = self.send_apdu(change_psc_apdu)
        
        if sw1 == 0x90 and sw2 == 0x00:
            return True, f"PSC cambiado correctamente para {card_type}"
        else:
            return False, f"Error cambiando PSC: SW={sw1:02X}{sw2:02X}"
    
    def read_error_counter(self, card_type=CARD_TYPE_5542):
        """Lee el Error Counter de la tarjeta física"""
        if card_type == CARD_TYPE_5542:
            # SLE5542: FF B1 00 00 04
            error_counter_apdu = [0xFF, 0xB1, 0x00, 0x00, 0x04]
        else:
            # SLE5528: FF B1 00 00 03
            error_counter_apdu = [0xFF, 0xB1, 0x00, 0x00, 0x03]
        
        response, sw1, sw2, status = self.send_apdu(error_counter_apdu)
        
        if sw1 == 0x90 and sw2 == 0x00:
            return response, f"Error Counter leído correctamente"
        else:
            return None, f"Error leyendo Error Counter: SW={sw1:02X}{sw2:02X}"
    
    def read_memory(self, start_address, length, card_type=CARD_TYPE_5542):
        """Lee memoria de la tarjeta física"""
        # Primero seleccionar la tarjeta
        success, msg = self.select_card(card_type)
        if not success:
            return None, msg
        
        try:
            if card_type == CARD_TYPE_5542:
                # SLE5542: FF B0 00 <address> <length>
                if start_address > 0xFF or length > 0xFF:
                    return None, "Dirección o longitud fuera de rango para SLE5542"
                read_apdu = [0xFF, 0xB0, 0x00, start_address, length]
            else:
                # SLE5528: FF B0 <MSB> <LSB> <length>
                if start_address > 0x3FF or length > 0xFF:
                    return None, "Dirección o longitud fuera de rango para SLE5528"
                msb = (start_address >> 8) & 0xFF
                lsb = start_address & 0xFF
                read_apdu = [0xFF, 0xB0, msb, lsb, length]
            
            response, sw1, sw2, status = self.send_apdu(read_apdu)
            
            if sw1 == 0x90 and sw2 == 0x00:
                return response, f"Lectura exitosa: {len(response)} bytes"
            else:
                return None, f"Error leyendo memoria: SW={sw1:02X}{sw2:02X}"
                
        except Exception as e:
            return None, f"Error en lectura: {e}"
    
    def _validate_safe_write_area(self, start_address, data_length, card_type):
        """
        Valida que la escritura sea en un área segura de la tarjeta.
        
        Protecciones implementadas:
        - SLE5542: No permite escritura en las 2 primeras filas (0x00-0x1F) ni en los últimos 8 bytes (0xF8-0xFF)
        - SLE5528: No permite escritura en las 2 primeras filas (0x000-0x01F) ni en los últimos 3 bytes (0x3FD-0x3FF)
        """
        # Definir áreas protegidas según tipo de tarjeta
        if card_type == CARD_TYPE_5542:
            # SLE5542 (256 bytes): 0x00 a 0xFF
            min_safe_address = 0x20  # No escribir en las primeras 2 filas (32 bytes: 0x00-0x1F)
            max_safe_address = 0xF7  # No escribir en los últimos 8 bytes (0xF8-0xFF)
            card_name = "SLE5542"
            protected_end_description = "últimos 8 bytes"
        else:  # CARD_TYPE_5528
            # SLE5528 (1024 bytes): 0x000 a 0x3FF
            min_safe_address = 0x20   # No escribir en las primeras 2 filas (32 bytes: 0x000-0x01F)
            max_safe_address = 0x3FC  # No escribir en los últimos 3 bytes (0x3FD-0x3FF: Error Counter + PSC)
            card_name = "SLE5528"
            protected_end_description = "últimos 3 bytes (Error Counter + PSC)"
        
        end_address = start_address + data_length - 1
        
        # Validar dirección inicial
        if start_address < min_safe_address:
            return False, f"Área protegida: No se puede escribir en las primeras 2 filas (0x00-0x1F) de {card_name}"
        
        # Validar dirección final
        if end_address > max_safe_address:
            return False, f"Área protegida: No se puede escribir en los {protected_end_description} de {card_name}. Dirección final: 0x{end_address:03X}"
        
        return True, "Área de escritura segura"
    
    def write_memory(self, start_address, data, card_type=CARD_TYPE_5542, psc=[0xFF, 0xFF, 0xFF]):
        """Escribe datos en la tarjeta física (requiere PSC) con protecciones de seguridad"""
        # Convertir datos a enteros si son strings hex
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], str):
            data_bytes = [int(hex_str, 16) for hex_str in data]
        else:
            data_bytes = list(data)
        
        # VALIDACIÓN DE SEGURIDAD: Verificar área segura de escritura
        is_safe, safety_msg = self._validate_safe_write_area(start_address, len(data_bytes), card_type)
        if not is_safe:
            return False, f"❌ ESCRITURA BLOQUEADA: {safety_msg}"
        
        # Primero seleccionar la tarjeta
        success, msg = self.select_card(card_type)
        if not success:
            return False, msg
        
        try:
            # Presentar PSC antes de escribir
            if card_type == CARD_TYPE_5542:
                psc_apdu = [0xFF, 0x20, 0x00, 0x00, 0x03] + psc
            else:
                # SLE5528 usa PSC de 2 bytes
                psc_apdu = [0xFF, 0x20, 0x00, 0x00, 0x02] + psc[:2]
            
            response, sw1, sw2, status = self.send_apdu(psc_apdu)
            
            # Verificar respuesta PSC
            if not (sw1 == 0x90 or (sw1 == 0x63 and sw2 == 0x07)):
                return False, f"PSC incorrecto: SW={sw1:02X}{sw2:02X}"
            
            # Proceder con la escritura
            if card_type == CARD_TYPE_5542:
                # SLE5542: FF D0 00 <address> <length> <data>
                if start_address > 0xFF or len(data_bytes) > 0xFF:
                    return False, "Dirección o datos fuera de rango para SLE5542"
                write_apdu = [0xFF, 0xD0, 0x00, start_address, len(data_bytes)] + data_bytes
            else:
                # SLE5528: FF D0 <MSB> <LSB> <length> <data>
                if start_address > 0x3FF or len(data_bytes) > 0xFF:
                    return False, "Dirección o datos fuera de rango para SLE5528"
                msb = (start_address >> 8) & 0xFF
                lsb = start_address & 0xFF
                write_apdu = [0xFF, 0xD0, msb, lsb, len(data_bytes)] + data_bytes
            
            response, sw1, sw2, status = self.send_apdu(write_apdu)
            
            print("Write APDU:", ' '.join([hex(b) for b in write_apdu]))
            print(f"Write Response SW: {sw1:02X} {sw2:02X}")
            
            if sw1 == 0x90 and sw2 == 0x00:
                return True, f"Escritura exitosa: {len(data)} bytes"
            else:
                return False, f"Error escribiendo memoria: SW={sw1:02X}{sw2:02X}"
                
        except Exception as e:
            return False, f"Error en escritura: {e}"
    
    def read_full_card(self, card_type=CARD_TYPE_5542, psc=None):
        """Lee toda la memoria de la tarjeta"""
        try:
            print(f"Starting optimized read for card type {card_type}")
            
            # Seleccionar la tarjeta primero
            if card_type == CARD_TYPE_5542:
                # SLE5542 (256 bytes) - SELECT 06
                select_apdu = [0xFF, 0xA4, 0x00, 0x00, 0x01, 0x06]
                total_size = 256
                print("Configuration: SLE5542 - 256 bytes, 4 total commands (SELECT 06 + PRESENT PSC + 2 reads)")
            else:
                # SLE5528 (1024 bytes) - SELECT 05
                select_apdu = [0xFF, 0xA4, 0x00, 0x00, 0x01, 0x05]
                total_size = 1024
                print("Configuration: SLE5528 - 1024 bytes, 10 total commands (SELECT 05 + PRESENT PSC + 8 reads)")
            
            # Enviar comando SELECT
            print("Step 1: Sending SELECT CARD command...")
            response, sw1, sw2, status = self.send_apdu(select_apdu)
            if sw1 != 0x90 or sw2 != 0x00:
                print(f"SELECT command failed: {sw1:02X} {sw2:02X}")
                return None
            print("SELECT command successful")
            
            # Presentar PSC después del SELECT
            print("Step 2: Sending PRESENT PSC command...")
            success, message, error_counter = self.present_psc(card_type, psc)
            if not success:
                print(f"PRESENT PSC command failed: {message}")
                # Devolver None para datos, pero incluir el error_counter
                return None, error_counter
            print("PRESENT PSC command successful")
            
            full_data = []
            
            if card_type == CARD_TYPE_5542:
                print("SLE5542: Reading in 2 optimized commands (no pages)...")
                
                # Leer direcciones 0x00 a 0xFE (255 bytes)
                print("Step 3/4: Reading 255 main bytes (FF B0 00 00 FF)...")
                read_apdu = [0xFF, 0xB0, 0x00, 0x00, 0xFF]
                response, sw1, sw2, status = self.send_apdu(read_apdu)
                
                if sw1 == 0x90 and sw2 == 0x00:
                    full_data.extend(response)
                    print(f"Read {len(response)} bytes successfully")
                else:
                    print(f"Read error: {sw1:02X} {sw2:02X}")
                    return None
                
                # Leer la última dirección (0xFF)
                print("Step 4/4: Reading last byte (FF B0 00 FF 01)...")
                read_last_apdu = [0xFF, 0xB0, 0x00, 0xFF, 0x01]
                response, sw1, sw2, status = self.send_apdu(read_last_apdu)
                
                if sw1 == 0x90 and sw2 == 0x00:
                    full_data.extend(response)
                    print(f"Last byte: {response[0]:02X}")
                else:
                    print(f"Last byte error: {sw1:02X} {sw2:02X}")
                    return None
                    
            else:
                print("SLE5528: Reading by pages (2 commands per page)...")
                
                # SLE5528: Leer por páginas (4 páginas de 256 bytes cada una)
                for page in range(4):
                    cmd_num = 3 + (page * 2)
                    print(f"Page {page} ({page*256}-{(page+1)*256-1})...")
                    
                    # Leer 255 bytes de la página
                    print(f"Step {cmd_num}/10: Reading 255 bytes from page {page} (FF B0 {page:02X} 00 FF)...")
                    read_apdu = [0xFF, 0xB0, page, 0x00, 0xFF]
                    response, sw1, sw2, status = self.send_apdu(read_apdu)
                    
                    if sw1 == 0x90 and sw2 == 0x00:
                        full_data.extend(response)
                        print(f"Page {page}: {len(response)} bytes read")
                    else:
                        print(f"Page {page} error: {sw1:02X} {sw2:02X}")
                        return None
                    
                    # Leer la última dirección de la página
                    print(f"Step {cmd_num+1}/10: Last byte from page {page} (FF B0 {page:02X} FF 01)...")
                    read_last_apdu = [0xFF, 0xB0, page, 0xFF, 0x01]
                    response, sw1, sw2, status = self.send_apdu(read_last_apdu)
                    
                    if sw1 == 0x90 and sw2 == 0x00:
                        full_data.extend(response)
                        print(f"Page {page}: Last byte {response[0]:02X}")
                    else:
                        print(f"Page {page} last byte error: {sw1:02X} {sw2:02X}")
                        return None
            
            print("Optimized read completed successfully!")
            print(f"Total: {len(full_data)} bytes")
            print(f"First 8 bytes: {' '.join([f'{b:02X}' for b in full_data[:8]])}")
            
            # Para SLE5528, reemplazar el dato en 0x3FD con el Error Counter real
            if card_type == CARD_TYPE_5528:
                print("Reading Error Counter for SLE5528 simulation...")
                error_counter_data, error_msg = self.read_error_counter(card_type)
                if error_counter_data and len(error_counter_data) > 0:
                    # Reemplazar el byte en la dirección 0x3FD (1021) con el Error Counter
                    error_counter_address = 0x3FD
                    if error_counter_address < len(full_data):
                        original_value = full_data[error_counter_address]
                        full_data[error_counter_address] = error_counter_data[0]
                        print(f"Error Counter address 0x3FD: {original_value:02X} → {error_counter_data[0]:02X}")
                    else:
                        print(f"Warning: Error Counter address 0x3FD out of range")
                else:
                    print(f"Warning: Could not read Error Counter: {error_msg}")
            
            # Devolver datos y None para error_counter (éxito)
            return full_data, None
            
        except Exception as e:
            print(f"Error during optimized read: {e}")
            return None, None
    
    def write_full_card(self, data, card_type=CARD_TYPE_5542, psc=[0xFF, 0xFF, 0xFF]):
        """
        Escribe datos a la tarjeta física con protocolo optimizado por tipo de tarjeta.
        
        Para SLE5542 (256b): Select -> PSC -> 1 APDU desde 0x20 hasta final
        Para SLE5528 (1k): Select -> PSC -> Escritura por páginas optimizada
        """
        try:
            print(f"DEBUG write_full_card: Recibido data tipo={type(data)}, len={len(data)}")
            print(f"DEBUG write_full_card: card_type={card_type} (type: {type(card_type)})")
            print(f"DEBUG write_full_card: psc={psc} (type: {type(psc)})")
            print(f"DEBUG write_full_card: Primeros 5 elementos de data: {data[:5]}")
            
            expected_size = 256 if card_type == CARD_TYPE_5542 else 1024
            
            if len(data) != expected_size:
                return False, f"Tamaño de datos incorrecto. Esperado: {expected_size}, Recibido: {len(data)}", None
            
            # PASO 1: Seleccionar la tarjeta
            success, msg = self.select_card(card_type)
            if not success:
                return False, f"Error seleccionando tarjeta: {msg}", None
            
            # PASO 2: Presentar PSC según tipo de tarjeta
            if card_type == CARD_TYPE_5542:
                # SLE5542: PSC de 3 bytes, respuesta esperada: 90 07
                psc_apdu = [0xFF, 0x20, 0x00, 0x00, 0x03] + psc
                expected_sw1, expected_sw2 = 0x90, 0x07
                card_name = "SLE5542"
            else:
                # SLE5528: PSC de 2 bytes, respuesta esperada: 90 FF  
                psc_apdu = [0xFF, 0x20, 0x00, 0x00, 0x02] + psc[:2]
                expected_sw1, expected_sw2 = 0x90, 0xFF
                card_name = "SLE5528"
            
            response, sw1, sw2, status = self.send_apdu(psc_apdu)
            print(f"PSC APDU: {' '.join([hex(b) for b in psc_apdu])}")
            print(f"PSC Response SW: {sw1:02X} {sw2:02X}")
            
            # Verificar respuesta PSC específica según tipo de tarjeta
            if not (sw1 == expected_sw1 and sw2 == expected_sw2):
                error_msg = (f"PSC verification failed for {card_name}. "
                           f"Expected: {expected_sw1:02X} {expected_sw2:02X}, "
                           f"Got: {sw1:02X} {sw2:02X}")
                print(f"ERROR: {error_msg}")
                
                # Retornar SW2 que contiene el Error Counter
                return False, error_msg, sw2
            
            print(f"SUCCESS: PSC verified correctly for {card_name}")
            
            # PASO 3: Escribir datos según tipo de tarjeta
            if card_type == CARD_TYPE_5542:
                return self._write_sle5542_optimized(data, card_type)
            else:
                return self._write_sle5528_optimized(data, card_type)
                
        except Exception as e:
            error_msg = f"Error in write_full_card: {e}"
            print(f"EXCEPTION: {error_msg}")
            return False, error_msg, None
    
    def _write_sle5542_optimized(self, data, card_type):
        """Escritura optimizada para SLE5542: 1 APDU desde 0x20 hasta final"""
        try:
            # SLE5542: Escribir desde 0x20 hasta 0xFF (224 bytes)
            start_addr = 0x20
            end_addr = 0xFF
            write_size = end_addr - start_addr + 1  # 224 bytes (0xE0)
            
            # Convertir datos a enteros si son strings hex
            if isinstance(data[0], str):
                data = [int(x, 16) for x in data]
            
            # Extraer datos desde la posición 0x20 hasta el final de la tarjeta
            write_data = data[start_addr:end_addr + 1]
            
            print(f"SLE5542: Writing {len(write_data)} bytes from 0x{start_addr:02X} to 0x{end_addr:02X}")
            
            # Construir APDU: FF D0 00 20 E0 <224_bytes>
            write_apdu = [0xFF, 0xD0, 0x00, start_addr, len(write_data)] + write_data
            
            print(f"Write APDU header: FF D0 00 {start_addr:02X} {len(write_data):02X}")
            print(f"First 8 data bytes: {' '.join([f'{b:02X}' for b in write_data[:8]])}")
            print(f"APDU length: {len(write_apdu)} bytes total")
            
            response, sw1, sw2, status = self.send_apdu(write_apdu)
            
            # Leer Error Counter después de la escritura
            error_counter_data, _ = self.read_error_counter(card_type)
            error_counter = error_counter_data[0] if error_counter_data else None
            
            if sw1 == 0x90 and sw2 == 0x00:
                print(f"SUCCESS: SLE5542 written successfully")
                print(f"Error Counter after write: 0x{error_counter:02X}" if error_counter else "Error Counter: N/A")
                return True, f"SLE5542 written successfully: {len(write_data)} bytes in 1 APDU", error_counter
            else:
                error_msg = f"Write failed: SW={sw1:02X}{sw2:02X}"
                print(f"ERROR: {error_msg}")
                return False, error_msg, error_counter
                
        except Exception as e:
            error_msg = f"Error in SLE5542 write: {e}"
            print(f"EXCEPTION: {error_msg}")
            return False, error_msg, None
    
    def _write_sle5528_optimized(self, data, card_type):
        """Escritura optimizada para SLE5528: Por páginas según especificación"""
        try:
            # Convertir datos a enteros si son strings hex
            if isinstance(data[0], str):
                data = [int(x, 16) for x in data]
                
            total_apdus = 0
            bytes_written = 0
            
            print("SLE5528: Starting page-by-page optimized write")
            
            # PÁGINA 0 (0x000-0x0FF): Escribir desde 0x20 hasta 0xFF
            print("Writing Page 0: 0x020-0xFF (224 bytes)")
            page_0_start = 0x20
            page_0_end = 0xFF
            page_0_data = data[page_0_start:page_0_end + 1]  # 224 bytes
            
            apdu_0 = [0xFF, 0xD0, 0x00, page_0_start, len(page_0_data)] + page_0_data
            response, sw1, sw2, status = self.send_apdu(apdu_0)
            total_apdus += 1
            
            if not (sw1 == 0x90 and sw2 == 0x00):
                return False, f"Page 0 write failed: SW={sw1:02X}{sw2:02X}"
            
            bytes_written += len(page_0_data)
            print(f"Page 0 written successfully: {len(page_0_data)} bytes")
            
            # PÁGINA 1 (0x100-0x1FF): 2 APDUs de 128 bytes cada una
            print("Writing Page 1: 0x100-0x1FF (256 bytes in 2 APDUs)")
            
            # Primera mitad: 0x100-0x17F (128 bytes)
            page_1_half1_data = data[0x100:0x180]  # 128 bytes
            apdu_1a = [0xFF, 0xD0, 0x01, 0x00, 0x80] + page_1_half1_data
            response, sw1, sw2, status = self.send_apdu(apdu_1a)
            total_apdus += 1
            
            if not (sw1 == 0x90 and sw2 == 0x00):
                return False, f"Page 1 first half write failed: SW={sw1:02X}{sw2:02X}"
            
            bytes_written += len(page_1_half1_data)
            print(f"Page 1 first half written: {len(page_1_half1_data)} bytes")
            
            # Segunda mitad: 0x180-0x1FF (128 bytes)
            page_1_half2_data = data[0x180:0x200]  # 128 bytes
            apdu_1b = [0xFF, 0xD0, 0x01, 0x80, 0x80] + page_1_half2_data
            response, sw1, sw2, status = self.send_apdu(apdu_1b)
            total_apdus += 1
            
            if not (sw1 == 0x90 and sw2 == 0x00):
                return False, f"Page 1 second half write failed: SW={sw1:02X}{sw2:02X}"
            
            bytes_written += len(page_1_half2_data)
            print(f"Page 1 second half written: {len(page_1_half2_data)} bytes")
            
            # PÁGINA 2 (0x200-0x2FF): 2 APDUs de 128 bytes cada una
            print("Writing Page 2: 0x200-0x2FF (256 bytes in 2 APDUs)")
            
            # Primera mitad: 0x200-0x27F (128 bytes)
            page_2_half1_data = data[0x200:0x280]  # 128 bytes
            apdu_2a = [0xFF, 0xD0, 0x02, 0x00, 0x80] + page_2_half1_data
            response, sw1, sw2, status = self.send_apdu(apdu_2a)
            total_apdus += 1
            
            if not (sw1 == 0x90 and sw2 == 0x00):
                return False, f"Page 2 first half write failed: SW={sw1:02X}{sw2:02X}"
            
            bytes_written += len(page_2_half1_data)
            print(f"Page 2 first half written: {len(page_2_half1_data)} bytes")
            
            # Segunda mitad: 0x280-0x2FF (128 bytes)
            page_2_half2_data = data[0x280:0x300]  # 128 bytes
            apdu_2b = [0xFF, 0xD0, 0x02, 0x80, 0x80] + page_2_half2_data
            response, sw1, sw2, status = self.send_apdu(apdu_2b)
            total_apdus += 1
            
            if not (sw1 == 0x90 and sw2 == 0x00):
                return False, f"Page 2 second half write failed: SW={sw1:02X}{sw2:02X}"
            
            bytes_written += len(page_2_half2_data)
            print(f"Page 2 second half written: {len(page_2_half2_data)} bytes")
            
            # PÁGINA 3 (0x300-0x3FC): 1 APDU con 253 bytes (0xFD)
            print("Writing Page 3: 0x300-0x3FC (253 bytes)")
            page_3_end = 0x3FC  # Hasta 0x3FC para respetar últimos 3 bytes (Error Counter + PSC)
            page_3_data = data[0x300:page_3_end + 1]  # 253 bytes
            
            apdu_3 = [0xFF, 0xD0, 0x03, 0x00, len(page_3_data)] + page_3_data
            response, sw1, sw2, status = self.send_apdu(apdu_3)
            total_apdus += 1
            
            if not (sw1 == 0x90 and sw2 == 0x00):
                return False, f"Page 3 write failed: SW={sw1:02X}{sw2:02X}"
            
            bytes_written += len(page_3_data)
            print(f"Page 3 written successfully: {len(page_3_data)} bytes")
            
            # Leer Error Counter después de la escritura
            error_counter_data, _ = self.read_error_counter(card_type)
            error_counter = error_counter_data[0] if error_counter_data else None
            
            print(f"SLE5528 write completed: {bytes_written} bytes using {total_apdus} APDUs")
            print(f"Error Counter after write: 0x{error_counter:02X}" if error_counter else "Error Counter: N/A")
            return True, f"SLE5528 written successfully: {bytes_written} bytes in {total_apdus} APDUs", error_counter
            
        except Exception as e:
            error_msg = f"Error in SLE5528 write: {e}"
            print(f"EXCEPTION: {error_msg}")
            return False, error_msg, None