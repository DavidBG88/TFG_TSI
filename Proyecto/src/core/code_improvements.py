"""
Mejoras de código aplicadas al proyecto CardSIM
"""

from typing import Optional, Tuple, Union

def safe_hex_to_ascii(hex_value: str) -> str:
    """
    Convierte un valor hex a ASCII de forma segura.
    
    Args:
        hex_value: String hexadecimal (ej: 'FF', '41')
        
    Returns:
        Carácter ASCII si es imprimible, '.' en caso contrario
    """
    try:
        ascii_val = int(hex_value, 16)
        if 32 <= ascii_val <= 126:
            return chr(ascii_val)
        else:
            return "."
    except (ValueError, TypeError):
        return "."

def format_memory_display(byte_value: str, add_space: bool = True) -> str:
    """
    Formatea un byte para display con ASCII.
    
    Args:
        byte_value: Valor hex del byte
        add_space: Si agregar espacio después del carácter ASCII
        
    Returns:
        String formateado para display ASCII
    """
    ascii_char = safe_hex_to_ascii(byte_value)
    if add_space:
        return ascii_char + " "
    return ascii_char

# Type hints para mejorar la legibilidad del código
SessionId = str
CardName = str
HexByte = str
MemoryAddress = int

# Constantes para mejorar la legibilidad
ASCII_PRINTABLE_MIN = 32
ASCII_PRINTABLE_MAX = 126
DEFAULT_HEX_BYTE = "FF"
ASCII_NON_PRINTABLE = "."

# Funciones helper para logging estructurado

# Decorador para manejo de errores consistente
def error_handler(error_message: str = "Operation failed", return_value=None):
    """
    Decorador para manejo consistente de errores.
    
    Args:
        error_message: Mensaje de error base
        return_value: Valor a retornar en caso de error
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"{error_message}: {str(e)}")
                return return_value
        return wrapper
    return decorator

# Constantes para validación
MAX_BYTE_VALUE = 255
HEX_BYTE_LENGTH = 2
BYTES_PER_ROW = 16

def is_valid_hex_string(text: str, allow_spaces: bool = True) -> bool:
    """
    Valida si un texto contiene solo caracteres hexadecimales válidos.
    
    Args:
        text: Texto a validar
        allow_spaces: Si permitir espacios en el texto
        
    Returns:
        True si es hexadecimal válido, False en caso contrario
    """
    if not text:
        return False
    
    valid_chars = '0123456789ABCDEFabcdef'
    if allow_spaces:
        valid_chars += ' '
    
    return all(c in valid_chars for c in text)

def validate_hex_bytes(hex_values: list) -> Tuple[bool, Optional[str]]:
    """
    Valida una lista de valores hexadecimales.
    
    Args:
        hex_values: Lista de strings hexadecimales
        
    Returns:
        Tupla (es_válido, mensaje_error_opcional)
    """
    for hex_val in hex_values:
        if not hex_val.strip():
            continue
        if not is_valid_hex_string(hex_val, allow_spaces=False):
            return False, f"Invalid hexadecimal character in: '{hex_val}'"
        try:
            int_val = int(hex_val, 16)
            if int_val > 255:
                return False, f"Hex value {hex_val} exceeds byte limit (255)"
        except ValueError:
            return False, f"Invalid hex format: '{hex_val}'"
    
    return True, None

# Constantes para mensajes comunes
class CommonMessages:
    """Mensajes comunes del sistema para evitar duplicación."""
    NO_CARD_SESSION = "No card session active"
    PSC_NOT_VERIFIED = "PSC must be verified before this operation"
    INVALID_HEX_FORMAT = "Invalid hexadecimal format"
    CARD_LIMIT_REACHED = "Maximum cards limit reached"
    OPERATION_FAILED = "Operation failed"

# Decorador para validar sesión activa

def load_icon_safe(icon_path: str, size: tuple = (20, 20), create_placeholder: bool = True):
    """
    Carga un icono de forma segura con manejo de errores consistente.
    
    Args:
        icon_path: Ruta al archivo de icono
        size: Tamaño deseado como (width, height)
        create_placeholder: Si crear un placeholder en caso de error
        
    Returns:
        ImageTk.PhotoImage o None
    """
    try:
        import os
        from PIL import Image, ImageTk
        
        if os.path.exists(icon_path):
            # Cargar y redimensionar la imagen
            image = Image.open(icon_path)
            image = image.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(image)
        else:
            print(f"Warning: Icon not found: {icon_path}")
            if create_placeholder:
                # Crear icono placeholder gris
                placeholder = Image.new('RGBA', size, (100, 100, 100, 255))
                return ImageTk.PhotoImage(placeholder)
            return None
    except Exception as e:
        filename = os.path.basename(icon_path) if icon_path else "unknown"
        print(f"Error loading icon {filename}: {e}")
        if create_placeholder:
            try:
                from PIL import Image, ImageTk
                # Crear icono placeholder en caso de error
                placeholder = Image.new('RGBA', size, (100, 100, 100, 255))
                return ImageTk.PhotoImage(placeholder)
            except:
                pass
        return None
