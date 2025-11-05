"""
Constantes y configuraciones para CardSIM
Este archivo contiene todas las constantes de configuración,
colores, fuentes y otros valores utilizados en la aplicación.
"""

from typing import Final

# Configuración de la aplicación
APP_TITLE: Final[str] = "CardSIM"
APP_VERSION: Final[str] = "1.0"
WINDOW_TITLE: Final[str] = "CardSIM - Smart Card Interface"
WINDOW_SIZE: Final[str] = "1200x800"

# Textos de interfaz
HEADER_TITLE = "CardSIM Smart Card Interface"
HEADER_SUBTITLE = "SLE5542/5528 Memory Card Simulator"

# Estados de la interfaz
STATUS_NO_CARD_INSERTED = "No card inserted"
STATUS_CARD_SELECTED = "Card selected"
STATUS_PSC_VERIFIED = "PSC verified - Write access enabled"

# Tipos de tarjetas
CARD_TYPE_5542 = 5542
CARD_TYPE_5528 = 5528

# Tamaños de memoria
MEMORY_SIZE_5542 = 256  # bytes
MEMORY_SIZE_5528 = 1024  # bytes (1KB)
PAGES_5528 = 4  # 4 páginas de 256 bytes cada una

# Estados de la aplicación
STATE_NO_CARD = "no_card"
STATE_CARD_CREATED = "card_created"
STATE_CARD_SELECTED = "card_selected"
STATE_PSC_VERIFIED = "psc_verified"

# Colores de la interfaz - Paleta moderna profesional
# Fondos
COLOR_BG_MAIN = '#F4F7FA'               # Fondo principal ventana
COLOR_BG_PANEL = '#E9EEF3'              # Fondo de paneles
COLOR_BG_TABLE = '#1E1E1E'              # Fondo tabla memoria

# Azules principales
COLOR_PRIMARY_BLUE = '#2D6A9F'          # Azul primario
COLOR_PRIMARY_BLUE_HOVER = '#398AC4'    # Azul hover
COLOR_DISABLED_GRAY = '#B0BEC5'         # Gris deshabilitado
COLOR_BORDER = '#B0BEC5'                # Color de borde

# Textos
COLOR_TEXT_PRIMARY = '#212121'          # Texto general
COLOR_TEXT_BUTTON_ENABLED = '#FFFFFF'  # Texto botón habilitado
COLOR_TEXT_BUTTON_DISABLED = '#ECEFF1' # Texto botón deshabilitado
COLOR_TEXT_DISABLED = '#9E9E9E'        # Texto deshabilitado general
COLOR_TEXT_TABLE = '#FFFFFF'            # Texto tabla memoria
COLOR_TEXT_TABLE_MODIFIED = '#FFEB3B'   # Bytes modificados en tabla

# Colores de estado y acento
COLOR_WARNING = '#E65100'               # Advertencia (acciones críticas)
COLOR_SUCCESS = '#2E7D32'               # Éxito
COLOR_ERROR = '#C62828'                 # Error
COLOR_PSC_CORRECT = '#2E7D32'           # PSC correcto
COLOR_PSC_INCORRECT = '#FF9800'         # PSC incorrecto
COLOR_CARD_BLOCKED = '#C62828'          # Tarjeta bloqueada
COLOR_APDU_SPECIAL = '#FF8C42'          # APDU con comportamiento especial (naranja suave)

# Colores contador intentos
COLOR_ATTEMPTS_3 = '#2E7D32'            # 3 intentos
COLOR_ATTEMPTS_2 = '#FF9800'            # 2 intentos  
COLOR_ATTEMPTS_1 = '#F44336'            # 1 intento

# Colores específicos por funcionalidad (usando la nueva paleta)
COLOR_BUTTON_PRIMARY = COLOR_PRIMARY_BLUE
COLOR_BUTTON_SECONDARY = COLOR_DISABLED_GRAY
COLOR_BUTTON_SUCCESS = COLOR_SUCCESS
COLOR_BUTTON_WARNING = COLOR_WARNING
COLOR_BUTTON_DANGER = COLOR_ERROR
COLOR_BUTTON_DISABLED = COLOR_DISABLED_GRAY

# Colores para estados de memoria
COLOR_MEMORY_READONLY = '#FF4444'        # Rojo - Datos de fábrica no modificables
COLOR_MEMORY_WRITABLE = '#FFFFFF'        # Blanco - Direcciones modificables
COLOR_MEMORY_MODIFIED = '#2196F3'        # Azul - Datos modificados
COLOR_MEMORY_PROTECTED = '#FF0000'       # Rojo - Protegido contra escritura
COLOR_MEMORY_PSC = '#9C27B0'             # Púrpura - Área PSC

# Fuentes profesionales
FONT_FAMILY_PRIMARY = 'Segoe UI'
FONT_FAMILY_MONO = 'Consolas'
FONT_FAMILY_HEADER = 'Segoe UI'

FONT_NORMAL = (FONT_FAMILY_PRIMARY, 11)
FONT_BOLD = (FONT_FAMILY_PRIMARY, 11, 'bold')
FONT_LARGE = (FONT_FAMILY_PRIMARY, 13)
FONT_LARGE_BOLD = (FONT_FAMILY_PRIMARY, 13, 'bold')
FONT_SMALL = (FONT_FAMILY_PRIMARY, 10)
FONT_TINY = (FONT_FAMILY_PRIMARY, 8)
FONT_HEADER = (FONT_FAMILY_HEADER, 16, 'bold')
FONT_SECTION_TITLE = (FONT_FAMILY_PRIMARY, 12, 'bold')
FONT_MONO = (FONT_FAMILY_MONO, 11)
FONT_MONO_SMALL = (FONT_FAMILY_MONO, 10)
FONT_STATUS = (FONT_FAMILY_PRIMARY, 10)

# APDUs comunes para SLE5542/5528 - Según manual oficial (CORREGIDO)
APDU_SELECT_CARD = [0xFF, 0xA4, 0x00, 0x00, 0x01, 0x06]  # SELECT_CARD_TYPE (SLE5542)
APDU_READ_MEMORY = [0xFF, 0xB0, 0x00]  # + address + length - READ_MEMORY_CARD
APDU_WRITE_MEMORY = [0xFF, 0xD0, 0x00]  # + address + length + data - WRITE_MEMORY_CARD
APDU_READ_ERROR_COUNTER = [0xFF, 0xB1, 0x00, 0x00, 0x04]  # READ_PRESENTATION_ERROR_COUNTER
APDU_READ_PROTECTION_BITS = [0xFF, 0xB2, 0x00, 0x00, 0x04]  # READ_PROTECTION_BITS
APDU_WRITE_PROTECT = [0xFF, 0xD1, 0x00]  # + address + length + data - WRITE_PROTECTION_MEMORY_CARD

# PSC Commands - Corregidos según especificación oficial
# SLE5542: PSC de 3 bytes
APDU_PRESENT_PSC_5542 = [0xFF, 0x20, 0x00, 0x00, 0x03]  # + 3 PSC bytes (SLE5542)
APDU_CHANGE_PSC_5542 = [0xFF, 0xD2, 0x00, 0x01, 0x03]   # + 3 new PSC bytes (SLE5542)

# SLE5528: PSC de 2 bytes  
APDU_PRESENT_PSC_5528 = [0xFF, 0x20, 0x00, 0x00, 0x02]  # + 2 PSC bytes (SLE5528)
APDU_CHANGE_PSC_5528 = [0xFF, 0xD2, 0x00, 0x01, 0x02]   # + 2 new PSC bytes (SLE5528)

# Compatibilidad hacia atrás (usar el de SLE5542 por defecto)
APDU_PRESENT_PSC = APDU_PRESENT_PSC_5542
APDU_CHANGE_PSC = APDU_CHANGE_PSC_5542

# Status Words - Según manual oficial
SW_SUCCESS = (0x90, 0x00)  # Operación exitosa
# Error Counter valores para SLE5542 (Present PSC response) - Actualizado
SW_PSC_CORRECT = (0x90, 0x07)      # 07h = Verificación correcta (3 intentos disponibles)
SW_PSC_FAILED_2_LEFT = (0x90, 0x03) # 03h = Verificación falló, 2 intentos restantes  
SW_PSC_FAILED_1_LEFT = (0x90, 0x01) # 01h = Verificación falló, 1 intento restante
SW_PSC_LOCKED = (0x90, 0x00)       # 00h = Password bloqueado (excedió máximo de intentos)
SW_WRITE_PROTECTION_ERROR = (0x69, 0x82)  # Write protection error - Dirección protegida

# PSC por defecto para simulación - Corregido según especificación
# SLE5542: 3 bytes PSC
DEFAULT_PSC_5542 = [0xFF, 0xFF, 0xFF]
# SLE5528: 2 bytes PSC (ubicado en las 2 últimas direcciones: 0x3FE-0x3FF)
DEFAULT_PSC_5528 = [0xFF, 0xFF]

# Error Counter - SLE5542 (256B): Secuencia de 4 valores
# Secuencia: 07 (3 intentos) -> 03 (2 intentos) -> 01 (1 intento) -> 00 (bloqueado)
ERROR_COUNTER_SEQUENCE_5542 = [0x07, 0x03, 0x01, 0x00]

# Error Counter - SLE5528 (1KB): Nueva lógica basada en bits
# Secuencia: FF, 7F, 7E, 7C, 78, 70, 60, 40, 00 (cada error elimina un bit)
ERROR_COUNTER_SEQUENCE_5528 = [0xFF, 0x7F, 0x7E, 0x7C, 0x78, 0x70, 0x60, 0x40, 0x00]

# Compatibilidad hacia atrás (mantener nombre original para SLE5528)
ERROR_COUNTER_SEQUENCE = ERROR_COUNTER_SEQUENCE_5528

def get_remaining_attempts_from_error_counter(error_counter_value, card_type):
    """Calcula los intentos restantes según el valor del error counter y tipo de tarjeta"""
    if card_type == CARD_TYPE_5528:
        # SLE5528: buscar el índice del valor en la secuencia
        try:
            current_index = ERROR_COUNTER_SEQUENCE_5528.index(error_counter_value)
            return len(ERROR_COUNTER_SEQUENCE_5528) - 1 - current_index
        except ValueError:
            # Si no se encuentra el valor, asumir 0 intentos
            return 0
    else:
        # SLE5542: buscar el índice en la secuencia 07-03-01-00
        try:
            current_index = ERROR_COUNTER_SEQUENCE_5542.index(error_counter_value)
            # Índice 0 = 3 intentos, 1 = 2 intentos, 2 = 1 intento, 3 = 0 intentos
            return len(ERROR_COUNTER_SEQUENCE_5542) - 1 - current_index
        except ValueError:
            # Si no se encuentra el valor, asumir 0 intentos
            return 0

# Compatibilidad hacia atrás
DEFAULT_PSC = DEFAULT_PSC_5542

# Direcciones de PSC y Error Counter según especificación oficial
# IMPORTANTE: SLE5542 usa registro interno para PSC (no visible en dump de memoria)
# SLE5542 (256 bytes)
PSC_ADDRESS_5542 = 0xFD         # REFERENCIA: PSC sería aquí si fuera visible (pero usa registro interno)
ERROR_COUNTER_ADDRESS_5542 = 0xFC  # Error counter en 0xFC (SÍ visible en memoria)

# SLE5528 (1024 bytes) - PSC SÍ visible en memoria
PSC_ADDRESS_5528 = 0x3FE        # PSC en direcciones 0x3FE-0x3FF (2 bytes, visible en memoria)
ERROR_COUNTER_ADDRESS_5528 = 0x3FD  # Error counter en 0x3FD (visible en memoria)

# Protection Bits según especificación oficial
# SLE5542: Solo 32 bits (protege direcciones 0x00-0x1F)
PROTECTION_BITS_SIZE_5542 = 32  # bits
PROTECTION_BITS_BYTES_5542 = 4  # bytes (32 bits / 8)

# SLE5528: 1024 bits (protege todas las direcciones 0x000-0x3FF)
PROTECTION_BITS_SIZE_5528 = 1024  # bits
PROTECTION_BITS_BYTES_5528 = 128  # bytes (1024 bits / 8)

# Datos de fábrica para SLE5542 (256B) según especificaciones reales
CARD_INIT_DATA_5542 = {
    # Fila 00: A2 13 10 91 FF FF 81 15 | FF FF FF FF FF FF FF FF
    0: 0xA2,   # Byte de identificación
    1: 0x13,   # Versión
    2: 0x10,   # Tipo
    3: 0x91,   # Checksum
    4: 0xFF,   # 
    5: 0xFF,   # 
    6: 0x81,   # 
    7: 0x15,   # 
    8: 0xFF,   # 
    9: 0xFF,   # 
    10: 0xFF,  # 
    11: 0xFF,  # 
    12: 0xFF,  # 
    13: 0xFF,  # 
    14: 0xFF,  # 
    15: 0xFF,  # 
    
    # Fila 10: FF FF FF FF FF D2 76 00 | 00 04 00 FF FF FF FF FF
    16: 0xFF,  # 
    17: 0xFF,  # 
    18: 0xFF,  # 
    19: 0xFF,  # 
    20: 0xFF,  # 
    21: 0xD2,  # 
    22: 0x76,  # 
    23: 0x00,  # 
    24: 0x00,  # 
    25: 0x04,  # 
    26: 0x00,  # 
    27: 0xFF,  # 
    28: 0xFF,  # 
    29: 0xFF,  # 
    30: 0xFF,  # 
    31: 0xFF,  # 
}

# Datos de fábrica para SLE5528 (1KB) según especificaciones reales
CARD_INIT_DATA_5528 = {
    # Fila 00: 92 23 10 91 FF FF 81 13 | FF FF FF FF FF FF FF FF
    0: 0x92,   # Byte de identificación
    1: 0x23,   # Versión
    2: 0x10,   # Tipo
    3: 0x91,   # Checksum
    4: 0xFF,   # 
    5: 0xFF,   # 
    6: 0x81,   # 
    7: 0x13,   #
    8: 0xFF,   # 
    9: 0xFF,   # 
    10: 0xFF,  # 
    11: 0xFF,  # 
    12: 0xFF,  # 
    13: 0xFF,  # 
    14: 0xFF,  # 
    15: 0xFF,  # 
    
    # Fila 10: FF FF FF FF FF D2 76 00 | 00 04 00 FF FF FF FF FF
    16: 0xFF,  # 
    17: 0xFF,  # 
    18: 0xFF,  # 
    19: 0xFF,  # 
    20: 0xFF,  # 
    21: 0xD2,  # 
    22: 0x76,  # 
    23: 0x00,  # 
    24: 0x00,  # 
    25: 0x04,  # 
    26: 0x00,  # 
    27: 0xFF,  # 
    28: 0xFF,  # 
    29: 0xFF,  # 
    30: 0xFF,  # 
    31: 0xFF,  # 
    
    # Últimas direcciones: Error counter y PSC (al final de las 1024 direcciones)
    0x3FD: 0x07,  # Error counter (7 intentos por defecto para SLE5528)
    0x3FE: 0xFF,  # PSC byte 1
    0x3FF: 0xFF,  # PSC byte 2
}

# Mantener compatibilidad hacia atrás
CARD_INIT_DATA = CARD_INIT_DATA_5542

# Posiciones especiales en memoria
PROTECTION_BITS_ADDRESS = 0x30  # Dirección de bits de protección

# Direcciones de solo lectura (datos de fábrica no modificables)
READONLY_ADDRESSES_5542 = {
    # Fila 00: A2 13 10 91 FF FF 81 15 (solo los datos de fábrica, no los FF)
    0, 1, 2, 3, 6, 7,
    # Fila 10: FF FF FF FF FF D2 76 00 00 04 00 FF FF FF FF FF (solo los datos de fábrica)
    21, 22, 23, 24, 25, 26
}

READONLY_ADDRESSES_5528 = {
    # Fila 00: 92 23 10 91 FF FF 81 13 (direcciones con datos de fábrica, excluyendo FF)
    0, 1, 2, 3, 6, 7,
    # Fila 10: FF FF FF FF FF D2 76 00 00 04 00 FF FF FF FF FF (solo los datos de fábrica)
    21, 22, 23, 24, 25, 26,
    # Última dirección: Solo Error counter (PSC debe ser escribible para Change PSC)
    0x3FD  # Solo Error Counter, NO incluir PSC (0x3FE, 0x3FF)
}

# Mantener compatibilidad hacia atrás
READONLY_ADDRESSES = READONLY_ADDRESSES_5542

# Direcciones protegidas de fábrica según especificaciones
# Para SLE5542: todas las direcciones que contienen datos de fábrica (no FF)
FACTORY_PROTECTED_5542 = list(READONLY_ADDRESSES_5542)  # Direcciones con datos de fábrica
FACTORY_PROTECTED_5528 = list(READONLY_ADDRESSES_5528)  # Direcciones con datos de fábrica

# Mensajes de la aplicación
MSG_INIT = "Smart Card Interface initialized"
MSG_CREATE_CARD = "Please create a NEW CARD or OPEN an existing card to begin"
MSG_CARD_READY = "Card ready - you can now SELECT CARD to begin operations"
MSG_SELECT_REQUIRED = "Card not selected. Use SELECT CARD first."
MSG_PSC_REQUIRED = "PSC not verified. Present correct PSC first."
MSG_NO_CARD = "No card available. Create or open a card first."

# Configuración de diálogos
DIALOG_READ_MEMORY = {
    "title": "Read Memory",
    "size": "400x220",
    "default_address": "20",
    "default_length": "10"  # Hex: 0x10 = 16 bytes
}

DIALOG_WRITE_MEMORY = {
    "title": "Write Memory", 
    "size": "400x250",
    "default_address": "20",
    "default_data": "01 02 03 04"
}

DIALOG_CHANGE_PSC = {
    "title": "Change PSC",
    "size": "400x200", 
    "default_psc": "AA BB CC"
}

DIALOG_PRESENT_PSC = {
    "title": "Present PSC",
    "size": "400x200",
    "default_psc": "FF FF FF"
}

DIALOG_WRITE_PROTECT = {
    "title": "Write Protection",
    "size": "400x200",
    "default_address": "10"
}

DIALOG_USER_CONFIG = {
    "title": "USER CONFIGURATION",
    "size": "500x350",
    "info_text": "Your User Identifier and Data will be saved into every Card or Log you Save."
}

# Plantilla por defecto para User Info
USER_INFO_TEMPLATE = """Nombre: 
Apellido1: 
Apellido2: 
NumeroMatricula: 
Curso: """
