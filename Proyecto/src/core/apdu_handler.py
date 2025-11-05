"""
Manejador de APDUs - Simula las respuestas de comandos APDU
"""

from src.utils.constants import *

class APDUHandler:
    """Maneja la simulación de comandos APDU para tarjetas SLE5542/5528"""
    
    def __init__(self, memory_manager, card_type=CARD_TYPE_5542):
        self.memory_manager = memory_manager
        self.card_type = card_type
        # Establecer error counter según tipo de tarjeta
        if card_type == CARD_TYPE_5542:
            # Para SLE5542: usar índice en la secuencia 07-03-01-00 (0 = 07, 1 = 03, 2 = 01, 3 = 00)
            self.error_counter_index = 0  # Índice en ERROR_COUNTER_SEQUENCE_5542 (empezar con 0x07)
            self.error_counter = self.get_error_counter_value()  # Valor actual del error counter
        else:  # CARD_TYPE_5528
            # Para SLE5528: usar índice en la secuencia de bits (0 = FF, 1 = 7F, máximo = 8 = 00)
            self.error_counter_index = 1  # Índice en ERROR_COUNTER_SEQUENCE_5528 (empezar con 7F)
            self.error_counter = self.get_error_counter_value()  # Valor actual del error counter
    
    def get_error_counter_value(self):
        """Obtiene el valor del error counter según el tipo de tarjeta"""
        if hasattr(self, 'card_type') and self.card_type == CARD_TYPE_5528:
            # SLE5528: usar secuencia basada en bits
            if hasattr(self, 'error_counter_index'):
                return ERROR_COUNTER_SEQUENCE_5528[min(self.error_counter_index, len(ERROR_COUNTER_SEQUENCE_5528) - 1)]
            else:
                return ERROR_COUNTER_SEQUENCE_5528[1]  # 7F por defecto (7 attempts)
        else:
            # SLE5542: usar secuencia 07-03-01-00
            if hasattr(self, 'error_counter_index'):
                return ERROR_COUNTER_SEQUENCE_5542[min(self.error_counter_index, len(ERROR_COUNTER_SEQUENCE_5542) - 1)]
            else:
                return ERROR_COUNTER_SEQUENCE_5542[0]  # 07 por defecto (3 attempts)
    
    def is_card_blocked(self):
        """Verifica si la tarjeta está bloqueada"""
        if hasattr(self, 'card_type') and self.card_type == CARD_TYPE_5528:
            # SLE5528: bloqueada cuando índice llega al final (00)
            return hasattr(self, 'error_counter_index') and self.error_counter_index >= len(ERROR_COUNTER_SEQUENCE_5528) - 1
        else:
            # SLE5542: bloqueada cuando índice llega al final (00)
            return hasattr(self, 'error_counter_index') and self.error_counter_index >= len(ERROR_COUNTER_SEQUENCE_5542) - 1
    
    def is_command_allowed_when_blocked(self, command_name):
        """Verifica si un comando está permitido cuando la tarjeta está bloqueada"""
        # Solo SELECT y READ están permitidos cuando la tarjeta está bloqueada
        allowed_commands = ['select_card', 'read_memory', 'read_error_counter']
        return command_name in allowed_commands
    
    def check_blocked_card_response(self, command_name):
        """Retorna respuesta de comando bloqueado si aplica"""
        if self.is_card_blocked() and not self.is_command_allowed_when_blocked(command_name):
            return {
                'apdu': [],
                'response': [],
                'sw1': 0x69,
                'sw2': 0x83,  # SW_BLOCKED
                'description': f'{command_name} blocked - Card permanently blocked',
                'success': False,
                'message': "❌ Card is PERMANENTLY BLOCKED. Only SELECT and READ operations allowed.",
                'blocked': True
            }
        return None
        
    def process_select_card(self):
        """Procesa el comando SELECT CARD"""
        # Generar APDU según tipo de tarjeta
        if self.memory_manager.card_type == CARD_TYPE_5542:
            # SLE5542: FF A4 00 00 01 06
            apdu = [0xFF, 0xA4, 0x00, 0x00, 0x01, 0x06]
        else:
            # SLE5528: FF A4 00 00 01 05
            apdu = [0xFF, 0xA4, 0x00, 0x00, 0x01, 0x05]
        
        response = [0x3B, 0x04, 0x92, 0x23, 0x10, 0x91]  # ATR típico
        sw1, sw2 = SW_SUCCESS
        
        return {
            'apdu': apdu,
            'response': response,
            'sw1': sw1,
            'sw2': sw2,
            'description': 'Selecting card (RESET)',
            'success': True
        }
    
    def process_read_memory(self, address, length):
        """Procesa el comando READ MEMORY"""
        # Generar APDU según el tipo de tarjeta
        if self.memory_manager.card_type == CARD_TYPE_5528:
            # Para SLE5528: FF B0 MSB LSB MEM_L
            msb = (address >> 8) & 0xFF  # Bits superiores de la dirección
            lsb = address & 0xFF         # Bits inferiores de la dirección
            apdu = APDU_READ_MEMORY + [msb, lsb, length]
        else:
            # Para SLE5542: FF B0 00 address MEM_L
            apdu = APDU_READ_MEMORY + [address, length]
        
        # Leer datos de la memoria
        response = self.memory_manager.read_memory(address, length)
        sw1, sw2 = SW_SUCCESS
        
        return {
            'apdu': apdu,
            'response': response,
            'sw1': sw1,
            'sw2': sw2,
            'description': f'Reading memory from {address:02X}',
            'success': True,
            'data_hex': ' '.join([f"{b:02X}" for b in response])
        }
    
    def process_present_psc(self, psc_bytes):
        """Procesa el comando PRESENT PSC"""
        # Obtener PSC actual desde la memoria
        current_psc = self.memory_manager.get_current_psc()
        
        # Determinar APDU según tipo de tarjeta
        if self.memory_manager.card_type == CARD_TYPE_5542:
            from utils.constants import APDU_PRESENT_PSC_5542
            apdu = APDU_PRESENT_PSC_5542 + psc_bytes
        else:  # CARD_TYPE_5528
            from utils.constants import APDU_PRESENT_PSC_5528  
            apdu = APDU_PRESENT_PSC_5528 + psc_bytes
        
        # Verificar si la tarjeta ya está bloqueada
        if self.is_card_blocked():
            sw1, sw2 = SW_PSC_LOCKED
            return {
                'apdu': apdu,
                'response': [],
                'sw1': sw1,
                'sw2': sw2,
                'description': 'Card is permanently blocked',
                'success': False,
                'message': "❌ Card is PERMANENTLY BLOCKED. Only SELECT and READ operations allowed.",
                'blocked': True
            }
        
        # Verificar si el PSC introducido coincide con el actual
        if psc_bytes == current_psc:
            # PSC correcto - según especificación oficial
            if self.memory_manager.card_type == CARD_TYPE_5542:
                self.error_counter_index = 0  # Resetear a índice 0 (0x07)
                self.error_counter = self.get_error_counter_value()
                sw1, sw2 = (0x90, self.error_counter)  # SW2 contiene el valor 0x07
            else:  # CARD_TYPE_5528
                self.error_counter_index = 0  # Resetear a FF
                self.error_counter = self.get_error_counter_value()
                sw1, sw2 = (0x90, 0xFF)  # (0x90, 0xFF) para SLE5528
            
            # Sincronizar con memory_manager cuando PSC es correcto
            if hasattr(self, 'memory_manager') and self.memory_manager:
                self.memory_manager.error_counter = self.error_counter
                self.memory_manager._update_error_counter_in_memory()
            
            success = True
            message = "✅ PSC accepted. Write operations now enabled."
        else:
            # Simular intentos incorrectos según manual
            if self.memory_manager.card_type == CARD_TYPE_5542:
                # Avanzar en la secuencia 07-03-01-00
                self.error_counter_index = min(self.error_counter_index + 1, len(ERROR_COUNTER_SEQUENCE_5542) - 1)
                self.error_counter = self.get_error_counter_value()
            else:  # CARD_TYPE_5528
                # Avanzar en la secuencia de bits
                self.error_counter_index = min(self.error_counter_index + 1, len(ERROR_COUNTER_SEQUENCE_5528) - 1)
                self.error_counter = self.get_error_counter_value()
            
            # Sincronizar con memory_manager
            if hasattr(self, 'memory_manager') and self.memory_manager:
                self.memory_manager.error_counter = self.error_counter
                self.memory_manager._update_error_counter_in_memory()
            
            # Generar mensajes apropiados según tipo de tarjeta
            if self.memory_manager.card_type == CARD_TYPE_5542:
                # SLE5542: mensajes con valores hex (07-03-01-00)
                attempts_left = len(ERROR_COUNTER_SEQUENCE_5542) - 1 - self.error_counter_index
                sw1, sw2 = (0x90, self.error_counter)  # SW2 contiene el valor actual del error counter
                if attempts_left > 1:
                    message = f"⚠️ Incorrect PSC. Error counter: 0x{self.error_counter:02X} ({attempts_left} attempts remaining)."
                elif attempts_left == 1:
                    message = f"⚠️ Incorrect PSC. Error counter: 0x{self.error_counter:02X} (1 attempt remaining)."
                else:
                    message = "❌ Card PERMANENTLY BLOCKED. Only SELECT and READ operations allowed."
            else:  # CARD_TYPE_5528
                # SLE5528: mensajes basados en bits
                attempts_left = len(ERROR_COUNTER_SEQUENCE_5528) - 1 - self.error_counter_index
                if attempts_left > 1:
                    sw1, sw2 = (0x90, self.error_counter)  # SW2 contiene el valor actual del error counter
                    message = f"⚠️ Incorrect PSC. Error counter: 0x{self.error_counter:02X} ({attempts_left} attempts remaining)."
                elif attempts_left == 1:
                    sw1, sw2 = (0x90, self.error_counter)
                    message = f"⚠️ Incorrect PSC. Error counter: 0x{self.error_counter:02X} (1 attempt remaining)."
                else:
                    sw1, sw2 = SW_PSC_LOCKED
                    message = "❌ Card PERMANENTLY BLOCKED. Only SELECT and READ operations allowed."
            
            success = False
            if self.error_counter > 0:
                # Mostrar el PSC actual como ayuda
                psc_hint = " ".join([f"{b:02X}" for b in current_psc])
                message += f"\n💡 Hint: Current PSC is {psc_hint}"
        
        return {
            'apdu': apdu,
            'response': [],
            'sw1': sw1,
            'sw2': sw2,
            'description': 'Presenting PSC',
            'success': success,
            'message': message
        }
    
    def process_write_memory(self, address, data_bytes):
        """Procesa el comando WRITE MEMORY"""
        # Verificar si la tarjeta está bloqueada
        blocked_response = self.check_blocked_card_response('write_memory')
        if blocked_response:
            return blocked_response
            
        length = len(data_bytes)
        
        # Formato de APDU según el tipo de tarjeta
        if self.memory_manager.card_type == CARD_TYPE_5542:
            # SLE5542 (256B): Formato simple
            apdu = APDU_WRITE_MEMORY + [address, length] + data_bytes
        else:
            # SLE5528 (1KB): Formato con MSB/LSB
            msb = (address >> 8) & 0xFF
            lsb = address & 0xFF
            apdu = APDU_WRITE_MEMORY + [msb, lsb, length] + data_bytes
        
        # Escribir en memoria (la validación ya se hizo en el diálogo)
        write_result = self.memory_manager.write_memory(address, data_bytes)
        sw1, sw2 = SW_SUCCESS
        
        # Preparar mensaje de resultado
        result = {
            'apdu': apdu,
            'response': [],
            'sw1': sw1,
            'sw2': sw2,
            'description': f'Writing memory at {address:02X}',
            'success': True,
            'data_hex': ' '.join([f"{b:02X}" for b in data_bytes]),
            'protected_addresses': write_result['protected_addresses'],
            'readonly_addresses': write_result['readonly_addresses'],
            'user_protected_addresses': write_result['user_protected_addresses'],
            'written_addresses': write_result['written_addresses']
        }
        
        return result
    
    def process_change_psc(self, new_psc_bytes):
        """Procesa el comando CHANGE PSC"""
        # Verificar si la tarjeta está bloqueada
        blocked_response = self.check_blocked_card_response('change_psc')
        if blocked_response:
            return blocked_response
        
        # Generar APDU según tipo de tarjeta (muy diferente entre tipos)
        if self.memory_manager.card_type == CARD_TYPE_5542:
            # SLE5542: FF D2 00 01 03 P1 P2 P3
            apdu = [0xFF, 0xD2, 0x00, 0x01, 0x03] + new_psc_bytes
        else:  # CARD_TYPE_5528
            # SLE5528: FF D0 03 FE 02 P1 P2 (usa WRITE MEMORY al área PSC)
            apdu = [0xFF, 0xD0, 0x03, 0xFE, 0x02] + new_psc_bytes
        
        # Actualizar PSC según tipo de tarjeta
        success = self.memory_manager.set_internal_psc(new_psc_bytes)
        
        if success:
            sw1, sw2 = SW_SUCCESS
            description = f'PSC changed successfully'
        else:
            sw1, sw2 = SW_WRITE_PROTECTION_ERROR
            description = f'PSC change failed - wrong length'
        
        return {
            'apdu': apdu,
            'response': [],
            'sw1': sw1,
            'sw2': sw2,
            'description': description,
            'success': success,
            'new_psc': ' '.join([f"{b:02X}" for b in new_psc_bytes])
        }
    
    def reset_error_counter(self):
        """Resetea el contador de errores según tipo de tarjeta"""
        if self.memory_manager.card_type == CARD_TYPE_5542:
            self.error_counter_index = 0  # Resetear a índice 0 (0x07)
            self.error_counter = ERROR_COUNTER_SEQUENCE_5542[0]  # 0x07
        else:  # CARD_TYPE_5528
            self.error_counter_index = 1  # Resetear a índice 1 (7F)
            self.error_counter = ERROR_COUNTER_SEQUENCE_5528[1]  # 0x7F
            
        # Sincronizar con memory_manager
        if hasattr(self, 'memory_manager') and self.memory_manager:
            self.memory_manager.error_counter = self.error_counter
            self.memory_manager._update_error_counter_in_memory()
