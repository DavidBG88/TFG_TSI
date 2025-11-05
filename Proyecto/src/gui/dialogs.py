"""
Diálogos específicos para la interfaz CardSIM
"""

import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import os
from src.utils.constants import *
from src.utils.resource_manager import get_resource_path, get_icon_path
from src.core.code_improvements import is_valid_hex_string, validate_hex_bytes, CommonMessages, load_icon_safe

def load_icon_image(icon_name, size=(24, 24)):
    """Carga un icono PNG desde assets/icons/ y lo redimensiona"""
    try:
        # Usar el resource manager para obtener la ruta correcta
        icon_path = get_icon_path(icon_name)
        return load_icon_safe(icon_path, size, create_placeholder=False)
    except Exception as e:
        print(f"Error in load_icon_image: {e}")
        return None

def set_dialog_icon(dialog):
    """Configura el icono de ETSISI para un diálogo"""
    try:
        # Ruta al icono de ETSISI
        icon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'icons', 'etsisi.jpg')
        icon_path = os.path.abspath(icon_path)
        
        if os.path.exists(icon_path):
            from PIL import Image, ImageTk
            
            # Cargar y redimensionar la imagen para icono (32x32)
            image = Image.open(icon_path)
            # Redimensionar manteniendo proporción y centrando en 32x32
            image = image.resize((32, 32), Image.Resampling.LANCZOS)
            
            # Convertir a PhotoImage para Tkinter
            photo = ImageTk.PhotoImage(image)
            
            # Configurar como icono de la ventana
            dialog.iconphoto(True, photo)
            
            # Guardar referencia en el diálogo para evitar garbage collection
            dialog._dialog_icon = photo
            
    except Exception as e:
        # Si hay algún error, usar el icono por defecto
        pass

def center_dialog_on_parent(dialog, parent, auto_size=False):
    """Centra un diálogo sobre su ventana padre en el mismo monitor"""
    # Solo establecer transient si no está ya configurado
    if dialog.master != parent:
        dialog.transient(parent)
    
    # Solo establecer grab_set si no está ya activo
    try:
        current_grab = dialog.grab_current()
        if current_grab != dialog:
            dialog.grab_set()
    except:
        dialog.grab_set()
    
    if auto_size:
        # Para auto-sizing: usar posicionamiento relativo
        dialog.update_idletasks()
        dialog.after(10, lambda: _center_dialog_after_pack(dialog, parent))
    else:
        # Forzar actualización antes del posicionamiento
        dialog.update_idletasks()
        parent.update_idletasks()
        
        # Obtener dimensiones del diálogo
        geometry = dialog.geometry()
        size_part = geometry.split('+')[0] if '+' in geometry else geometry
        dialog_width, dialog_height = map(int, size_part.split('x'))
        
        # Obtener información de la ventana padre
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty() 
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        # Calcular posición centrada DIRECTAMENTE sobre la ventana padre
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        # Aplicar posición inmediatamente
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        # Asegurar que está visible en el monitor correcto
        dialog.lift()
        dialog.focus_force()

def _center_dialog_after_pack(dialog, parent):
    """Función auxiliar para centrar después de que el contenido esté empaquetado"""
    # Forzar actualización completa
    dialog.update_idletasks()
    parent.update_idletasks()
    
    # Obtener dimensiones calculadas automáticamente
    dialog_width = dialog.winfo_reqwidth()
    dialog_height = dialog.winfo_reqheight()
    
    # Obtener información de la ventana padre
    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    parent_width = parent.winfo_width()
    parent_height = parent.winfo_height()
    
    # Calcular posición centrada directamente sobre la ventana padre
    x = parent_x + (parent_width - dialog_width) // 2
    y = parent_y + (parent_height - dialog_height) // 2
    
    # Aplicar posición
    dialog.geometry(f"+{x}+{y}")
    
    # Asegurar que está visible en el monitor correcto
    dialog.lift()
    dialog.focus_force()

class ReadMemoryDialog:
    """Diálogo para leer memoria"""
    
    def __init__(self, parent, callback, session_manager=None):
        self.callback = callback
        self.session_manager = session_manager
        self.is_1kb_card = False
        
        # Detectar si es tarjeta de 1KB (SLE5528)
        if session_manager:
            active_session = session_manager.get_active_session()
            if active_session and active_session.card_type == CARD_TYPE_5528:
                self.is_1kb_card = True
        
        self.create_dialog(parent)
    
    def create_dialog(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(DIALOG_READ_MEMORY["title"])
        
        # Configurar icono de ETSISI
        set_dialog_icon(self.dialog)
        
        # Auto-sizing en lugar de tamaño fijo
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=COLOR_BG_MAIN, padx=20, pady=15)
        
        # Crear contenido primero
        self.create_content()
        
        # Centrar con auto-sizing
        center_dialog_on_parent(self.dialog, parent, auto_size=True)
        
    def create_content(self):
        """Crea el contenido del diálogo"""
        # Campos de entrada organizados
        fields_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN)
        fields_frame.pack(pady=(5, 15))
        
        # Campo de página solo para tarjetas de 1KB
        if self.is_1kb_card:
            tk.Label(fields_frame, text="Page (0-3):", bg=COLOR_BG_MAIN, 
                    font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY).pack(pady=(0, 5))
            self.page_entry = tk.Entry(fields_frame, font=FONT_NORMAL, width=15, justify=tk.CENTER)
            self.page_entry.pack(pady=(0, 10))
            self.page_entry.insert(0, "0")  # Página por defecto
        
        tk.Label(fields_frame, text="Start address (hex):", bg=COLOR_BG_MAIN, 
                font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY).pack(pady=(0, 5))
        self.addr_entry = tk.Entry(fields_frame, font=FONT_NORMAL, width=15, justify=tk.CENTER)
        self.addr_entry.pack(pady=(0, 10))
        self.addr_entry.insert(0, DIALOG_READ_MEMORY["default_address"])
        
        tk.Label(fields_frame, text="Number of bytes (hex):", bg=COLOR_BG_MAIN, 
                font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY).pack(pady=(0, 5))
        self.len_entry = tk.Entry(fields_frame, font=FONT_NORMAL, width=15, justify=tk.CENTER)
        self.len_entry.pack()
        self.len_entry.insert(0, DIALOG_READ_MEMORY["default_length"])
        
        # Etiqueta informativa sobre la limitación
        tk.Label(fields_frame, text="(Maximum: FF)", bg=COLOR_BG_MAIN, 
                font=("Segoe UI", 8), fg=COLOR_TEXT_DISABLED).pack(pady=(2, 0))
        
        # Botones
        button_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN)
        button_frame.pack(pady=(10, 5))
        
        tk.Button(button_frame, text="Read", command=self.execute_read,
                 bg=COLOR_BUTTON_PRIMARY, fg=COLOR_TEXT_BUTTON_ENABLED, font=FONT_NORMAL,
                 width=10).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(button_frame, text="Cancel", command=self.dialog.destroy,
                 bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_BUTTON_ENABLED, font=FONT_NORMAL,
                 width=8).pack(side=tk.LEFT)
        
        # Bind Enter and Escape keys
        self.dialog.bind('<Return>', lambda e: self.execute_read())
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        
        # Focus en el primer campo
        if self.is_1kb_card:
            self.page_entry.focus()
        else:
            self.addr_entry.focus()
    
    def execute_read(self):
        try:
            address = int(self.addr_entry.get(), 16)
            length = int(self.len_entry.get(), 16)
            
            # Para tarjetas de 1KB, validar y procesar la página
            if self.is_1kb_card:
                page = int(self.page_entry.get())
                
                # Validar página (0-3 para SLE5528)
                if page < 0 or page > 3:
                    try:
                        messagebox.showerror("Error", 
                                           f"Invalid page number: {page}\n"
                                           f"Valid pages for SLE5528: 0-3")
                    except Exception:
                        pass
                    return
                
                # Validar que la dirección local esté en el rango correcto (0-255)
                if address > 255:
                    try:
                        messagebox.showerror("Error", 
                                           f"Address within page cannot exceed 0xFF (255)\n"
                                           f"Address: 0x{address:02X} ({address})")
                    except Exception:
                        pass
                    return
                
                # Validar que la lectura no exceda los límites de la página
                page_end_address = 255  # Cada página tiene direcciones 0-255
                if address + length - 1 > page_end_address:
                    max_length_in_page = page_end_address - address + 1
                    try:
                        messagebox.showerror("Error", 
                                           f"Read operation exceeds page {page} boundaries\n"
                                           f"Starting at address 0x{address:02X} in page {page}\n"
                                           f"Requested: 0x{length:02X} ({length} bytes), Maximum in this page: 0x{max_length_in_page:02X} ({max_length_in_page} bytes)\n"
                                           f"Page {page} addresses: 0x00-0xFF")
                    except Exception:
                        pass
                    return
                
                # Calcular la dirección completa: página * 256 + dirección local
                full_address = (page * 256) + address
                
                # Usar la dirección completa para la operación
                final_address = full_address
            else:
                final_address = address
            
            # Validar que la longitud no exceda 255 bytes (0xFF)
            if length > 255:
                try:
                    messagebox.showerror("Error", 
                                       f"Length cannot exceed 0xFF (255 bytes)\n"
                                       f"Requested: 0x{length:02X} ({length} bytes), Maximum allowed: 0xFF (255 bytes)")
                except Exception:
                    # Si falla el messagebox (app cerrándose), simplemente pasar
                    pass
                return
            
            self.callback(final_address, length)
            self.dialog.destroy()
        except ValueError:
            try:
                messagebox.showerror("Error", "Invalid input values")
            except Exception:
                # Si falla el messagebox (app cerrándose), simplemente pasar
                pass
        except Exception:
            # Si ocurre cualquier otra excepción durante el cierre, simplemente pasar
            pass

class WriteMemoryDialog:
    """Diálogo para escribir memoria"""
    
    def __init__(self, parent, callback, session_manager=None):
        self.callback = callback
        self.session_manager = session_manager
        self.is_1kb_card = False
        
        # Detectar si es tarjeta de 1KB (SLE5528)
        if session_manager:
            active_session = session_manager.get_active_session()
            if active_session and active_session.card_type == CARD_TYPE_5528:
                self.is_1kb_card = True
        
        self.create_dialog(parent)
    
    def create_dialog(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(DIALOG_WRITE_MEMORY["title"])
        
        # Configurar icono de ETSISI
        set_dialog_icon(self.dialog)
        
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=COLOR_BG_MAIN, padx=20, pady=15)
        
        # Mantener el mismo tamaño base, ajustar solo si es necesario
        dialog_height = 350 if self.is_1kb_card else 320
        self.dialog.geometry(f"450x{dialog_height}")
        self.dialog.resizable(False, False)
        
        # Crear contenido
        self.create_content()
        
        # Centrar manualmente sin auto-sizing
        self.dialog.update_idletasks()  # Asegurar que el diálogo esté completamente renderizado
        
        # Obtener dimensiones de la ventana padre
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        # Calcular posición centrada
        x = parent_x + (parent_width - 450) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"450x{dialog_height}+{x}+{y}")
        
    def create_content(self):
        """Crea el contenido del diálogo"""
        # Campos de entrada organizados
        fields_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN)
        fields_frame.pack(pady=(5, 15))
        
        # Campo de página (solo para tarjetas de 1KB) - Compacto
        if self.is_1kb_card:
            tk.Label(fields_frame, text="Page (0-3):", bg=COLOR_BG_MAIN, 
                    font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY).pack(pady=(0, 5))
            self.page_entry = tk.Entry(fields_frame, font=FONT_NORMAL, width=15, justify=tk.CENTER)
            self.page_entry.pack(pady=(0, 10))
            self.page_entry.insert(0, "0")
        
        tk.Label(fields_frame, text="Start address (hex):", bg=COLOR_BG_MAIN, 
                font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY).pack(pady=(0, 5))
        self.addr_entry = tk.Entry(fields_frame, font=FONT_NORMAL, width=15, justify=tk.CENTER)
        self.addr_entry.pack(pady=(0, 10))
        
        # Configuración específica por tipo de tarjeta
        if self.is_1kb_card:
            self.addr_entry.insert(0, "20")  # Tarjetas 1KB: dirección 20
        else:
            self.addr_entry.insert(0, "20")  # Tarjetas 256B: dirección 20
        
        # Frame para selección de formato
        format_frame = tk.Frame(fields_frame, bg=COLOR_BG_MAIN)
        format_frame.pack(pady=(0, 10))
        
        tk.Label(format_frame, text="Input format:", bg=COLOR_BG_MAIN, 
                font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY).pack(pady=(0, 5))
        
        # Variable para el formato seleccionado
        self.format_var = tk.StringVar(value="HEX")
        
        # Botones de radio para selección de formato
        format_buttons_frame = tk.Frame(format_frame, bg=COLOR_BG_MAIN)
        format_buttons_frame.pack()
        
        self.hex_radio = tk.Radiobutton(format_buttons_frame, text="HEX", variable=self.format_var, 
                                       value="HEX", bg=COLOR_BG_MAIN, fg=COLOR_TEXT_PRIMARY, 
                                       font=FONT_NORMAL, command=self.on_format_change)
        self.hex_radio.pack(side=tk.LEFT, padx=(0, 20))
        
        self.ascii_radio = tk.Radiobutton(format_buttons_frame, text="ASCII", variable=self.format_var, 
                                         value="ASCII", bg=COLOR_BG_MAIN, fg=COLOR_TEXT_PRIMARY, 
                                         font=FONT_NORMAL, command=self.on_format_change)
        self.ascii_radio.pack(side=tk.LEFT)
        
        # Label dinámico para descripción del formato (ancho fijo)
        self.format_label = tk.Label(fields_frame, bg=COLOR_BG_MAIN, 
                                    font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY,
                                    width=55, anchor="w", justify="left")
        self.format_label.pack(pady=(0, 5))
        
        # Campo de entrada de datos
        self.data_entry = tk.Entry(fields_frame, width=40, font=FONT_NORMAL)
        self.data_entry.pack()
        
        # Configurar formato inicial
        self.on_format_change()
        
        # Botones
        button_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN)
        button_frame.pack(pady=(10, 5))
        
        tk.Button(button_frame, text="Write", command=self.execute_write,
                 bg=COLOR_BUTTON_PRIMARY, fg=COLOR_TEXT_BUTTON_ENABLED, font=FONT_NORMAL,
                 width=10).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(button_frame, text="Cancel", command=self.dialog.destroy,
                 bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_BUTTON_ENABLED, font=FONT_NORMAL,
                 width=8).pack(side=tk.LEFT)
        
        # Bind Enter and Escape keys
        self.dialog.bind('<Return>', lambda e: self.execute_write())
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        
        # Focus en el primer campo
        if self.is_1kb_card:
            self.page_entry.focus()
        else:
            self.addr_entry.focus()
    
    def on_format_change(self):
        """Actualiza la interfaz según el formato seleccionado"""
        format_type = self.format_var.get()
        
        if format_type == "HEX":
            self.format_label.config(text="Data (space-separated hex bytes, e.g., FF 00 A5):")
            # Limpiar y poner ejemplo hex si está vacío o tiene contenido ASCII
            current_text = self.data_entry.get()
            if not current_text or not is_valid_hex_string(current_text, allow_spaces=True):
                self.data_entry.delete(0, tk.END)
                self.data_entry.insert(0, DIALOG_WRITE_MEMORY["default_data"])
        else:  # ASCII
            self.format_label.config(text="Data (ASCII text, spaces are allowed, e.g., Hello World):")
            # Limpiar y poner ejemplo ASCII si está vacío o tiene contenido hex
            current_text = self.data_entry.get()
            if not current_text or ' ' in current_text or is_valid_hex_string(current_text.replace(' ', ''), allow_spaces=False):
                self.data_entry.delete(0, tk.END)
                self.data_entry.insert(0, "Hello")
    
    def execute_write(self):
        try:
            # Para tarjetas de 1KB, validar y procesar página
            if self.is_1kb_card:
                try:
                    page = int(self.page_entry.get())
                    if page < 0 or page > 3:
                        messagebox.showerror("Error", "Page must be between 0 and 3 for SLE5528 cards")
                        return
                except ValueError:
                    messagebox.showerror("Error", "Invalid page number. Please enter 0, 1, 2, or 3")
                    return
                
                # Validar dirección dentro de la página (0x00-0xFF)
                try:
                    page_address = int(self.addr_entry.get(), 16)
                    if page_address < 0 or page_address > 0xFF:
                        messagebox.showerror("Error", "Address within page must be between 0x00 and 0xFF")
                        return
                except ValueError:
                    messagebox.showerror("Error", "Invalid address format")
                    return
                
                # Calcular dirección absoluta: página * 256 + dirección dentro de página
                address = page * 256 + page_address
            else:
                # Para tarjetas de 256 bytes, usar dirección directamente
                address = int(self.addr_entry.get(), 16)
            
            data_str = self.data_entry.get().strip()
            
            # Validar que el campo de datos no esté vacío
            if not data_str:
                messagebox.showerror("Error", "Data field cannot be empty")
                return
            
            # Procesar datos según el formato seleccionado
            format_type = self.format_var.get()
            validated_bytes = []
            
            if format_type == "HEX":
                # Procesar formato HEX (con espacios)
                hex_values = data_str.split()
                
                for i, hex_val in enumerate(hex_values):
                    hex_val = hex_val.strip()
                    
                    # Verificar que sea formato hexadecimal válido
                    if not hex_val:
                        continue  # Saltar valores vacíos
                    
                    # Verificar longitud exacta de 2 caracteres para un byte hex
                    if len(hex_val) != 2:
                        messagebox.showerror("Error", 
                                           f"Invalid hex byte length in position {i+1}: '{hex_val}'\n"
                                           f"Each hex byte must be exactly 2 characters (00-FF)\n"
                                           f"Found {len(hex_val)} characters")
                        return
                        
                    # Verificar que solo contenga caracteres hexadecimales
                    if not is_valid_hex_string(hex_val):
                        messagebox.showerror("Error", 
                                           f"Invalid hex character in byte {i+1}: '{hex_val}'\n"
                                           "Only 0-9, A-F characters allowed")
                        return
                    
                    # Convertir y validar rango de byte
                    try:
                        byte_value = int(hex_val, 16)
                        if byte_value > 255:  # Técnicamente imposible con 2 chars, pero por seguridad
                            messagebox.showerror("Error", 
                                               f"Byte value too large in position {i+1}: '{hex_val}'")
                            return
                        validated_bytes.append(hex_val.upper())  # Normalizar a mayúsculas
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid hex value: '{hex_val}'")
                        return
            
            else:  # ASCII format
                # Procesar formato ASCII (sin espacios ni caracteres de control)
                # Filtrar saltos de línea y otros caracteres de control
                cleaned_data_str = data_str.replace('\n', '').replace('\r', '').replace('\t', '')
                
                for i, char in enumerate(cleaned_data_str):
                    # Convertir cada carácter ASCII a su valor hexadecimal
                    ascii_val = ord(char)
                    
                    # Validar que esté en el rango ASCII válido
                    if ascii_val > 255:
                        messagebox.showerror("Error", 
                                           f"Character at position {i+1} ('{char}') is not a valid ASCII character\n"
                                           f"ASCII value {ascii_val} exceeds 255")
                        return
                    
                    # Convertir a hexadecimal de 2 dígitos
                    hex_val = f"{ascii_val:02X}"
                    validated_bytes.append(hex_val)
            
            if not validated_bytes:
                messagebox.showerror("Error", "No valid data found")
                return
            
            # NUEVA VALIDACIÓN: Verificar tamaño y protección
            from utils.constants import (MEMORY_SIZE_5542, MEMORY_SIZE_5528, 
                                       READONLY_ADDRESSES_5542, READONLY_ADDRESSES_5528,
                                       PSC_ADDRESS_5542, PSC_ADDRESS_5528, 
                                       CARD_TYPE_5542, CARD_TYPE_5528)
            
            # Importar para obtener el tipo de tarjeta actual
            # Necesitamos acceso al session manager para estas validaciones
            # Esto se hará a través de una referencia pasada al diálogo
            if hasattr(self, 'session_manager') and self.session_manager:
                active_session = self.session_manager.get_active_session()
                if active_session:
                    card_type = active_session.card_type
                    
                    # Determinar tamaño máximo según tipo de tarjeta
                    max_memory_size = MEMORY_SIZE_5528 if card_type == 5528 else MEMORY_SIZE_5542
                    
                    # Validar que la dirección inicial esté dentro del rango
                    if address >= max_memory_size:
                        messagebox.showerror("Error", 
                                           f"Start address 0x{address:02X} ({address}) exceeds card memory size\n"
                                           f"Maximum address for this card: 0x{max_memory_size-1:02X} ({max_memory_size-1})")
                        return
                    
                    # Validar que los datos no excedan el tamaño de la tarjeta
                    end_address = address + len(validated_bytes) - 1
                    if end_address >= max_memory_size:
                        max_bytes = max_memory_size - address
                        messagebox.showerror("Error", 
                                           f"Data size ({len(validated_bytes)} bytes) exceeds available space\n"
                                           f"Starting at address 0x{address:02X}, maximum {max_bytes} bytes can be written\n"
                                           f"End address would be 0x{end_address:02X}, but card memory ends at 0x{max_memory_size-1:02X}")
                        return
                    
                    # Configurar direcciones según tipo de tarjeta
                    if card_type == CARD_TYPE_5542:
                        readonly_addresses = READONLY_ADDRESSES_5542
                        psc_start = PSC_ADDRESS_5542
                        psc_size = 3
                    else:  # CARD_TYPE_5528
                        readonly_addresses = READONLY_ADDRESSES_5528
                        psc_start = PSC_ADDRESS_5528
                        psc_size = 2
                    
                    # Validar que no se escriba en direcciones protegidas
                    protected_addresses = []
                    for i in range(len(validated_bytes)):
                        addr = address + i
                        # Verificar direcciones de solo lectura (datos de fábrica)
                        if addr in readonly_addresses:
                            protected_addresses.append(f"0x{addr:02X}")
                        # Verificar área PSC (solo bloqueado para SLE5528, SLE5542 permite escritura ya que PSC es interno)
                        elif psc_start <= addr <= psc_start + psc_size - 1 and card_type == CARD_TYPE_5528:
                            protected_addresses.append(f"0x{addr:02X} (PSC area)")
                        # Verificar direcciones protegidas por el usuario
                        elif active_session.memory_manager.is_protected(addr):
                            # Verificar si es protección de usuario (no de fábrica)
                            if addr not in readonly_addresses:
                                protected_addresses.append(f"0x{addr:02X} (user protected)")
                    
                    if protected_addresses:
                        # Separar tipos de protección para el mensaje
                        factory_addrs = [addr for addr in protected_addresses if "(PSC area)" not in addr and "(user protected)" not in addr]
                        psc_addrs = [addr for addr in protected_addresses if "(PSC area)" in addr]
                        user_addrs = [addr for addr in protected_addresses if "(user protected)" in addr]
                        
                        error_msg = f"Cannot write to protected addresses:\n{', '.join(protected_addresses)}\n\n"
                        error_msg += "Protected addresses include:\n"
                        
                        if factory_addrs:
                            error_msg += "• Factory data (readonly addresses in red)\n"
                        if psc_addrs:
                            error_msg += f"• PSC area (0x{psc_start:02X}-0x{psc_start+psc_size-1:02X}) - use Change PSC command (SLE5528 only)\n"
                        if user_addrs:
                            error_msg += "• User protected addresses (set via Write Protect command)\n"
                        
                        messagebox.showerror("Error", error_msg.strip())
                        return
            
            # Reconstruir string validado
            validated_data_str = ' '.join(validated_bytes)
            
            # Llamar al callback con datos validados
            self.callback(address, validated_data_str)
            self.dialog.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid address format: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Validation error: {str(e)}")

class ChangePSCDialog:
    """Diálogo para cambiar PSC - Adaptado según tipo de tarjeta"""
    
    def __init__(self, parent, callback, card_type=CARD_TYPE_5542):
        self.callback = callback
        self.card_type = card_type
        self.create_dialog(parent)
    
    def create_dialog(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(DIALOG_CHANGE_PSC["title"])
        
        # Configurar icono de ETSISI
        set_dialog_icon(self.dialog)
        
        # Auto-sizing
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=COLOR_BG_MAIN, padx=20, pady=15)
        
        # Crear contenido primero
        self.create_content()
        
        # Centrar con auto-sizing
        center_dialog_on_parent(self.dialog, parent, auto_size=True)
        
    def create_content(self):
        """Crea el contenido del diálogo"""
        # Campo de entrada organizado según tipo de tarjeta
        fields_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN)
        fields_frame.pack(pady=(5, 15))
        
        # Configurar según tipo de tarjeta
        if self.card_type == CARD_TYPE_5542:
            label_text = "New PSC (3 2-char hex bytes - e.g., FF FF FF):"
            default_psc = "FF FF FF"
            self.psc_length = 3
        else:  # CARD_TYPE_5528
            label_text = "New PSC (2 2-char hex bytes - e.g., FF FF):"
            default_psc = "FF FF"
            self.psc_length = 2
        
        tk.Label(fields_frame, text=label_text, bg=COLOR_BG_MAIN, 
                font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY).pack(pady=(0, 5))
        self.psc_entry = tk.Entry(fields_frame, width=15, font=FONT_NORMAL, justify=tk.CENTER)
        self.psc_entry.pack()
        self.psc_entry.insert(0, default_psc)
        
        # Botones
        button_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN)
        button_frame.pack(pady=(10, 5))
        
        tk.Button(button_frame, text="Change PSC", command=self.execute_change,
                 bg=COLOR_BUTTON_PRIMARY, fg=COLOR_TEXT_BUTTON_ENABLED, font=FONT_NORMAL,
                 width=12).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(button_frame, text="Cancel", command=self.dialog.destroy,
                 bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_BUTTON_ENABLED, font=FONT_NORMAL,
                 width=8).pack(side=tk.LEFT)
        
        # Bind Enter and Escape keys
        self.dialog.bind('<Return>', lambda e: self.execute_change())
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        
        # Focus en el campo de entrada
        self.psc_entry.focus()
    
    def execute_change(self):
        try:
            new_psc = self.psc_entry.get().strip()
            
            if not new_psc:
                messagebox.showerror("Error", "PSC field cannot be empty")
                return
            
            # Validar formato PSC según tipo de tarjeta
            hex_values = new_psc.split()
            expected_bytes = self.psc_length
            
            if len(hex_values) != expected_bytes:
                card_name = "SLE5542" if self.card_type == CARD_TYPE_5542 else "SLE5528"
                messagebox.showerror("Error", 
                                   f"PSC must be exactly {expected_bytes} bytes for {card_name}\n"
                                   f"Found {len(hex_values)} values, expected {expected_bytes}\n"
                                   f"Format: {' '.join(['XX'] * expected_bytes)} (e.g., {' '.join(['FF'] * expected_bytes)})")
                return
            
            # Validar cada byte PSC
            validated_bytes = []
            for i, hex_val in enumerate(hex_values):
                hex_val = hex_val.strip()
                
                # Verificar longitud exacta de 2 caracteres para un byte hex
                if len(hex_val) != 2:
                    messagebox.showerror("Error", 
                                       f"Invalid PSC byte length in position {i+1}: '{hex_val}'\n"
                                       f"Each PSC byte must be exactly 2 characters (00-FF)\n"
                                       f"Found {len(hex_val)} characters")
                    return
                
                # Verificar formato hexadecimal
                if not is_valid_hex_string(hex_val):
                    messagebox.showerror("Error", 
                                       f"Invalid hex character in PSC byte {i+1}: '{hex_val}'\n"
                                       "Only 0-9, A-F characters allowed")
                    return
                
                # Verificar rango de byte (redundante pero por seguridad)
                try:
                    byte_value = int(hex_val, 16)
                    if byte_value > 255:  # Técnicamente imposible con 2 chars
                        messagebox.showerror("Error", 
                                           f"PSC byte {i+1} too large: '{hex_val}'")
                        return
                    validated_bytes.append(f"{byte_value:02X}")
                except ValueError:
                    messagebox.showerror("Error", f"Invalid hex value in PSC: '{hex_val}'")
                    return
            
            # Reconstruir PSC validado
            validated_psc = ' '.join(validated_bytes)
            
            self.callback(validated_psc)
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"PSC validation error: {str(e)}")

class PresentPSCDialog:
    """Diálogo para presentar PSC - Corregido según especificación oficial"""
    
    def __init__(self, parent, callback, card_type=CARD_TYPE_5542):
        self.callback = callback
        self.card_type = card_type
        self.create_dialog(parent)
    
    def create_dialog(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(DIALOG_PRESENT_PSC["title"])
        
        # Configurar icono de ETSISI
        set_dialog_icon(self.dialog)
        
        # No establecer geometry fijo para auto-sizing
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=COLOR_BG_MAIN)
        
        # Configurar padding mínimo para la ventana
        self.dialog.configure(padx=20, pady=15)
        
        # Centrar con auto-sizing después de crear contenido
        self.create_content()
        center_dialog_on_parent(self.dialog, parent, auto_size=True)
        
    def create_content(self):
        """Crea el contenido del diálogo"""
        # Descripción según tipo de tarjeta
        if self.card_type == CARD_TYPE_5542:
            desc_text = "Enter PSC (Personal Security Code)\nSLE5542: Format FF FF FF (3 hex bytes, space separated)"
            default_psc = "FF FF FF"
            psc_length = 3
        else:  # CARD_TYPE_5528
            desc_text = "Enter PSC (Personal Security Code)\nSLE5528: Format FF FF (2 hex bytes, space separated)"
            default_psc = "FF FF"
            psc_length = 2
            
        desc_label = tk.Label(self.dialog, 
                             text=desc_text,
                             bg=COLOR_BG_MAIN, font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY,
                             justify=tk.CENTER)
        desc_label.pack(pady=(10, 15))
        
        # Campo de entrada con marco
        entry_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN)
        entry_frame.pack(pady=(0, 15))
        
        tk.Label(entry_frame, text="PSC:", bg=COLOR_BG_MAIN, font=FONT_NORMAL, 
                fg=COLOR_TEXT_PRIMARY).pack()
        self.psc_entry = tk.Entry(entry_frame, width=15, font=FONT_NORMAL, justify=tk.CENTER)
        self.psc_entry.pack(pady=(5, 0))
        self.psc_entry.insert(0, default_psc)
        
        # Almacenar información del tipo de tarjeta
        self.psc_length = psc_length
        
        # Botones
        button_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN)
        button_frame.pack(pady=(10, 5))
        
        tk.Button(button_frame, text="Present PSC", command=self.execute_present,
                 bg=COLOR_BUTTON_PRIMARY, fg=COLOR_TEXT_BUTTON_ENABLED, font=FONT_NORMAL, 
                 width=12).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(button_frame, text="Cancel", command=self.dialog.destroy,
                 bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_BUTTON_ENABLED, font=FONT_NORMAL, 
                 width=8).pack(side=tk.LEFT)
        
        # Bind Enter and Escape keys
        self.dialog.bind('<Return>', lambda e: self.execute_present())
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        
        # Focus en el campo de entrada
        self.psc_entry.focus()
    
    def execute_present(self):
        try:
            psc_input = self.psc_entry.get().strip()
            if not psc_input:
                messagebox.showerror("Error", "PSC cannot be empty")
                return
            
            # Validar formato PSC según tipo de tarjeta
            hex_values = psc_input.split()
            expected_bytes = self.psc_length
            
            if len(hex_values) != expected_bytes:
                card_name = "SLE5542" if self.card_type == CARD_TYPE_5542 else "SLE5528"
                messagebox.showerror("Error", 
                                   f"PSC must be exactly {expected_bytes} bytes for {card_name}\n"
                                   f"Found {len(hex_values)} values, expected {expected_bytes}\n"
                                   f"Format: {' '.join(['XX'] * expected_bytes)} (e.g., {' '.join(['FF'] * expected_bytes)})")
                return
            
            # Validar cada byte PSC
            for i, hex_val in enumerate(hex_values):
                hex_val = hex_val.strip()
                
                # Verificar longitud exacta de 2 caracteres para un byte hex
                if len(hex_val) != 2:
                    messagebox.showerror("Error", 
                                       f"Invalid PSC byte length in position {i+1}: '{hex_val}'\n"
                                       f"Each PSC byte must be exactly 2 characters (00-FF)\n"
                                       f"Found {len(hex_val)} characters")
                    return
                
                # Verificar formato hexadecimal
                if not is_valid_hex_string(hex_val):
                    messagebox.showerror("Error", 
                                       f"Invalid hex character in PSC byte {i+1}: '{hex_val}'\n"
                                       "Only 0-9, A-F characters allowed")
                    return
                
                # Verificar rango de byte (redundante pero por seguridad)
                try:
                    byte_value = int(hex_val, 16)
                    if byte_value > 255:  # Técnicamente imposible con 2 chars
                        messagebox.showerror("Error", 
                                           f"PSC byte {i+1} too large: '{hex_val}'")
                        return
                except ValueError:
                    messagebox.showerror("Error", f"Invalid hex value in PSC: '{hex_val}'")
                    return
                
            self.callback(psc_input)
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error: {str(e)}")

class WriteProtectDialog:
    """Diálogo para protección contra escritura con comparación de contenido"""
    
    def __init__(self, parent, callback, session_manager=None):
        self.callback = callback
        self.session_manager = session_manager
        self.is_1kb_card = False
        
        # Detectar si es tarjeta de 1KB (SLE5528)
        if session_manager:
            active_session = session_manager.get_active_session()
            if active_session and active_session.card_type == CARD_TYPE_5528:
                self.is_1kb_card = True
        
        self.create_dialog(parent)
    
    def create_dialog(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Write Protect")
        
        # Configurar icono de ETSISI
        set_dialog_icon(self.dialog)
        
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=COLOR_BG_MAIN, padx=20, pady=15)
        
        # Ajustar tamaño según tipo de tarjeta
        dialog_height = 600 if self.is_1kb_card else 520
        dialog_width = 520
        self.dialog.geometry(f"{dialog_width}x{dialog_height}")
        self.dialog.resizable(False, False)
        
        # Crear contenido
        self.create_content()
        
        # Centrar manualmente
        self.dialog.update_idletasks()
        
        # Obtener dimensiones de la ventana padre
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        # Calcular posición centrada
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
    def create_content(self):
        """Crea el contenido del diálogo"""
        # Título y explicación
        title_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN)
        title_frame.pack(pady=(0, 15))
        
        tk.Label(title_frame, text="Write Protect", 
                font=FONT_SECTION_TITLE, bg=COLOR_BG_MAIN, fg=COLOR_TEXT_PRIMARY).pack()
        
        # Explicación del funcionamiento
        explanation_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN)
        explanation_frame.pack(pady=(0, 15), padx=10)
        
        # Texto específico según el tipo de tarjeta
        if self.is_1kb_card:
            protection_info = "• All card addresses can be protected"
        else:
            protection_info = "• Only first two rows (0x00-0x1F) can be protected"
        
        explanation_text = (
            "This command protects addresses by comparing content:\n"
            "• Enter the data pattern you want to protect\n"
            "• Only addresses where current card content MATCHES\n"
            "  your input will be write-protected\n"
            "• Non-matching addresses remain unprotected\n"
            f"{protection_info}"
        )
        
        tk.Label(explanation_frame, text=explanation_text, 
                font=FONT_NORMAL, bg=COLOR_BG_MAIN, fg=COLOR_TEXT_PRIMARY,
                justify=tk.LEFT, wraplength=480).pack()
        
        # Separador
        separator = tk.Frame(self.dialog, height=2, bg=COLOR_TEXT_PRIMARY)
        separator.pack(fill=tk.X, pady=(10, 15), padx=20)
        
        # Campos de entrada (reutilizando lógica de WriteMemoryDialog)
        fields_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN)
        fields_frame.pack(pady=(5, 15))
        
        # Campo de página (solo para tarjetas de 1KB)
        if self.is_1kb_card:
            tk.Label(fields_frame, text="Page (0-3):", bg=COLOR_BG_MAIN, 
                    font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY).pack(pady=(0, 5))
            self.page_entry = tk.Entry(fields_frame, font=FONT_NORMAL, width=15, justify=tk.CENTER)
            self.page_entry.pack(pady=(0, 10))
            self.page_entry.insert(0, "0")
        
        tk.Label(fields_frame, text="Start address (hex):", bg=COLOR_BG_MAIN, 
                font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY).pack(pady=(0, 5))
        self.addr_entry = tk.Entry(fields_frame, font=FONT_NORMAL, width=15, justify=tk.CENTER)
        self.addr_entry.pack(pady=(0, 10))
        
        # Configuración específica por tipo de tarjeta
        if self.is_1kb_card:
            self.addr_entry.insert(0, "20")  # Tarjetas 1KB: dirección 20
        else:
            self.addr_entry.insert(0, "10")  # Tarjetas 256B: dirección 10
        
        # Frame para selección de formato
        format_frame = tk.Frame(fields_frame, bg=COLOR_BG_MAIN)
        format_frame.pack(pady=(0, 10))
        
        tk.Label(format_frame, text="Input format:", bg=COLOR_BG_MAIN, 
                font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY).pack(pady=(0, 5))
        
        # Variable para el formato seleccionado
        self.format_var = tk.StringVar(value="HEX")
        
        # Botones de radio para selección de formato
        format_buttons_frame = tk.Frame(format_frame, bg=COLOR_BG_MAIN)
        format_buttons_frame.pack()
        
        self.hex_radio = tk.Radiobutton(format_buttons_frame, text="HEX", variable=self.format_var, 
                                       value="HEX", bg=COLOR_BG_MAIN, fg=COLOR_TEXT_PRIMARY, 
                                       font=FONT_NORMAL, command=self.on_format_change)
        self.hex_radio.pack(side=tk.LEFT, padx=(0, 20))
        
        self.ascii_radio = tk.Radiobutton(format_buttons_frame, text="ASCII", variable=self.format_var, 
                                         value="ASCII", bg=COLOR_BG_MAIN, fg=COLOR_TEXT_PRIMARY, 
                                         font=FONT_NORMAL, command=self.on_format_change)
        self.ascii_radio.pack(side=tk.LEFT)
        
        # Label dinámico para descripción del formato
        self.format_label = tk.Label(fields_frame, bg=COLOR_BG_MAIN, 
                                    font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY,
                                    width=55, anchor="w", justify="left")
        self.format_label.pack(pady=(0, 5))
        
        # Campo de entrada de datos
        self.data_entry = tk.Entry(fields_frame, width=40, font=FONT_NORMAL)
        self.data_entry.pack()
        
        # Configurar formato inicial
        self.on_format_change()
        
        # Botones
        button_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN)
        button_frame.pack(pady=(10, 5))
        
        tk.Button(button_frame, text="Protect", command=self.execute_protect,
                 bg=COLOR_BUTTON_PRIMARY, fg=COLOR_TEXT_BUTTON_ENABLED, font=FONT_NORMAL,
                 width=10).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(button_frame, text="Cancel", command=self.dialog.destroy,
                 bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_BUTTON_ENABLED, font=FONT_NORMAL,
                 width=8).pack(side=tk.LEFT)
        
        # Bind Enter and Escape keys
        self.dialog.bind('<Return>', lambda e: self.execute_protect())
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        
        # Focus en el primer campo
        if self.is_1kb_card:
            self.page_entry.focus()
        else:
            self.addr_entry.focus()
    
    def on_format_change(self):
        """Actualiza la interfaz según el formato seleccionado"""
        format_type = self.format_var.get()
        
        if format_type == "HEX":
            self.format_label.config(text="Data pattern to protect (space-separated hex bytes, e.g., FF 00 A5):")
            # Limpiar y poner ejemplo hex si está vacío o tiene contenido ASCII
            current_text = self.data_entry.get()
            if not current_text or not is_valid_hex_string(current_text, allow_spaces=True):
                self.data_entry.delete(0, tk.END)
                self.data_entry.insert(0, "01 00 03 00")  # Datos para bloquear direcciones 01 y 03
        else:  # ASCII
            self.format_label.config(text="Data pattern to protect (ASCII text, e.g., HelloWorld):")
            # Limpiar y poner ejemplo ASCII si está vacío o tiene contenido hex
            current_text = self.data_entry.get()
            if not current_text or ' ' in current_text or is_valid_hex_string(current_text.replace(' ', ''), allow_spaces=False):
                self.data_entry.delete(0, tk.END)
                self.data_entry.insert(0, "Hello")
    
    def execute_protect(self):
        try:
            # Para tarjetas de 1KB, validar y procesar página
            if self.is_1kb_card:
                try:
                    page = int(self.page_entry.get())
                    if page < 0 or page > 3:
                        messagebox.showerror("Error", "Page must be between 0 and 3 for SLE5528 cards")
                        return
                except ValueError:
                    messagebox.showerror("Error", "Invalid page number. Please enter 0, 1, 2, or 3")
                    return
                
                # Validar dirección dentro de la página (0x00-0xFF)
                try:
                    page_address = int(self.addr_entry.get(), 16)
                    if page_address < 0 or page_address > 0xFF:
                        messagebox.showerror("Error", "Address within page must be between 0x00 and 0xFF")
                        return
                except ValueError:
                    messagebox.showerror("Error", "Invalid address format")
                    return
                
                # Calcular dirección absoluta: página * 256 + dirección dentro de página
                address = page * 256 + page_address
            else:
                # Para tarjetas de 256 bytes, usar dirección directamente
                address = int(self.addr_entry.get(), 16)
            
            data_str = self.data_entry.get().strip()
            
            # Validar que el campo de datos no esté vacío
            if not data_str:
                messagebox.showerror("Error", "Data pattern field cannot be empty")
                return
            
            # Procesar datos según el formato seleccionado (similar a WriteMemoryDialog)
            format_type = self.format_var.get()
            validated_bytes = []
            
            if format_type == "HEX":
                # Procesar formato HEX (con espacios)
                hex_values = data_str.split()
                
                for i, hex_val in enumerate(hex_values):
                    hex_val = hex_val.strip()
                    
                    if not hex_val:
                        continue
                    
                    if len(hex_val) != 2:
                        messagebox.showerror("Error", 
                                           f"Invalid hex byte length in position {i+1}: '{hex_val}'\n"
                                           f"Each hex byte must be exactly 2 characters (00-FF)")
                        return
                        
                    if not is_valid_hex_string(hex_val):
                        messagebox.showerror("Error", 
                                           f"Invalid hex character in byte {i+1}: '{hex_val}'\n"
                                           "Only 0-9, A-F characters allowed")
                        return
                    
                    try:
                        byte_value = int(hex_val, 16)
                        validated_bytes.append(hex_val.upper())
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid hex value: '{hex_val}'")
                        return
            
            else:  # ASCII format
                # Procesar formato ASCII (sin espacios ni caracteres de control)
                # Filtrar saltos de línea y otros caracteres de control
                cleaned_data_str = data_str.replace('\n', '').replace('\r', '').replace('\t', '')
                
                for i, char in enumerate(cleaned_data_str):
                    ascii_val = ord(char)
                    
                    if ascii_val > 255:
                        messagebox.showerror("Error", 
                                           f"Character at position {i+1} ('{char}') is not a valid ASCII character")
                        return
                    
                    hex_val = f"{ascii_val:02X}"
                    validated_bytes.append(hex_val)
            
            if not validated_bytes:
                messagebox.showerror("Error", "No valid data found")
                return
            
            # Reconstruir string validado
            validated_data_str = ' '.join(validated_bytes)
            
            # Llamar al callback con dirección y datos para comparación
            self.callback(address, validated_data_str)
            self.dialog.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid address format: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Validation error: {str(e)}")

class UserConfigDialog:
    """Diálogo de configuración de usuario"""
    
    def __init__(self, parent, callback, current_info=""):
        self.callback = callback
        self.current_info = current_info
        self.create_dialog(parent)
    
    def create_dialog(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(DIALOG_USER_CONFIG["title"])
        
        # Configurar icono de ETSISI
        set_dialog_icon(self.dialog)
        
        # Auto-sizing en lugar de tamaño fijo - centrar automáticamente
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=COLOR_BG_MAIN, padx=20, pady=15)
        
        # Crear contenido primero
        self.create_content()
        
        # Centrar con auto-sizing
        center_dialog_on_parent(self.dialog, parent, auto_size=True)
        
    def create_content(self):
        """Crea el contenido del diálogo"""
        # Mensaje explicativo con mejor formato
        info_label = tk.Label(self.dialog, text=DIALOG_USER_CONFIG["info_text"],
                             bg=COLOR_BG_MAIN, font=FONT_NORMAL, wraplength=400, 
                             justify=tk.CENTER, fg=COLOR_TEXT_PRIMARY)
        info_label.pack(pady=(5, 15))
        
        # Campo User Info con marco
        frame_user_info = tk.Frame(self.dialog, bg=COLOR_BG_MAIN)
        frame_user_info.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        user_info_label = tk.Label(frame_user_info, text="User Info:", 
                                  bg=COLOR_BG_MAIN, font=FONT_BOLD, 
                                  fg=COLOR_TEXT_PRIMARY)
        user_info_label.pack(anchor='w', pady=(0, 5))
        
        # Campo de texto grande para User Info con scroll
        text_frame = tk.Frame(frame_user_info, bg=COLOR_BG_MAIN)
        text_frame.pack(fill=tk.X)
        
        self.user_info_text = tk.Text(text_frame, height=8, width=45, font=FONT_NORMAL,
                                     wrap=tk.WORD, relief=tk.SOLID, bd=1)
        self.user_info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar para el texto
        scrollbar = tk.Scrollbar(text_frame, command=self.user_info_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.user_info_text.config(yscrollcommand=scrollbar.set)
        
        # Cargar información existente o plantilla
        if self.current_info:
            self.user_info_text.insert('1.0', self.current_info)
        else:
            # Usar plantilla por defecto
            from utils.constants import USER_INFO_TEMPLATE
            self.user_info_text.insert('1.0', USER_INFO_TEMPLATE)
        
        # Botones con mejor estilo
        button_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN)
        button_frame.pack(pady=15)
        
        ok_btn = tk.Button(button_frame, text="Save", command=self.save_config,
                          bg=COLOR_BUTTON_PRIMARY, fg=COLOR_TEXT_BUTTON_ENABLED, 
                          font=FONT_BOLD, width=12, height=1, relief=tk.FLAT)
        ok_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(button_frame, text="Cancel", command=self.dialog.destroy,
                              bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_PRIMARY, 
                              font=FONT_BOLD, width=12, height=1, relief=tk.FLAT)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Bind solo Escape key (Enter se quita para evitar cierre accidental al escribir)
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        
        # Focus en el campo de texto
        self.user_info_text.focus()
    
    def save_config(self):
        user_info = self.user_info_text.get('1.0', tk.END).strip()
        from utils.constants import USER_INFO_TEMPLATE
        
        # No guardar si es igual a la plantilla sin modificar o está vacío
        if user_info == USER_INFO_TEMPLATE.strip() or not user_info:
            user_info = ""
            
        self.callback(user_info)
        self.dialog.destroy()

class NewCardDialog:
    """Diálogo para crear una nueva tarjeta"""
    
    def __init__(self, parent, callback):
        self.callback = callback
        self.result = None
        
        # Crear ventana modal
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("New Card")
        
        # Configurar icono de ETSISI
        set_dialog_icon(self.dialog)
        
        self.dialog.geometry("450x480")  # Mucho más alto
        self.dialog.configure(bg=COLOR_BG_PANEL)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrar sobre la ventana padre
        center_dialog_on_parent(self.dialog, parent)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del diálogo"""
        # Frame del encabezado con icono y título
        header_frame = tk.Frame(self.dialog, bg=COLOR_BG_PANEL)
        header_frame.pack(fill=tk.X, pady=(20, 10), padx=20)
        
        # Frame interno para centrar el contenido
        content_frame = tk.Frame(header_frame, bg=COLOR_BG_PANEL)
        content_frame.pack(expand=True)
        
        # Icono PNG
        icon_image = load_icon_image("new_card.png", (64, 64))
        if icon_image:
            icon_label = tk.Label(content_frame, image=icon_image, bg=COLOR_BG_PANEL)
            icon_label.image = icon_image  # Mantener referencia
        else:
            # Fallback a emoji si no se puede cargar el PNG
            icon_label = tk.Label(content_frame, text="🆕", font=("Segoe UI Emoji", 32),
                                 fg=COLOR_PRIMARY_BLUE, bg=COLOR_BG_PANEL)
        icon_label.pack(side=tk.LEFT, padx=(0, 8))
        
        # Título
        title_label = tk.Label(content_frame, text="Create New Card", 
                              font=FONT_SECTION_TITLE, bg=COLOR_BG_PANEL,
                              fg=COLOR_TEXT_PRIMARY)
        title_label.pack(side=tk.LEFT)
        
        # Frame principal
        main_frame = tk.Frame(self.dialog, bg=COLOR_BG_PANEL)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Nombre de la tarjeta
        name_frame = tk.Frame(main_frame, bg=COLOR_BG_PANEL)
        name_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(name_frame, text="Card Name:", font=FONT_BOLD,
                bg=COLOR_BG_PANEL, fg=COLOR_TEXT_PRIMARY).pack(anchor='w')
        
        self.name_var = tk.StringVar(value="NewCard")
        self.name_entry = tk.Entry(name_frame, textvariable=self.name_var,
                                  font=FONT_NORMAL, width=30)
        self.name_entry.pack(fill=tk.X, pady=(5, 0))
        self.name_entry.focus()
        
        # Tipo de tarjeta
        type_frame = tk.LabelFrame(main_frame, text="Card Type", font=FONT_BOLD,
                                  bg=COLOR_BG_PANEL, fg=COLOR_TEXT_PRIMARY)
        type_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.card_type_var = tk.StringVar(value="5542")
        
        # Radio buttons para tipo
        radio_frame = tk.Frame(type_frame, bg=COLOR_BG_PANEL)
        radio_frame.pack(padx=10, pady=10)
        
        tk.Radiobutton(radio_frame, text="SLE5542 (256 bytes)", 
                      variable=self.card_type_var, value="5542",
                      font=FONT_NORMAL, bg=COLOR_BG_PANEL,
                      fg=COLOR_TEXT_PRIMARY, 
                      command=self.update_description).pack(anchor='w', pady=2)
        
        tk.Radiobutton(radio_frame, text="SLE5528 (1KB - 1024 bytes)", 
                      variable=self.card_type_var, value="5528",
                      font=FONT_NORMAL, bg=COLOR_BG_PANEL,
                      fg=COLOR_TEXT_PRIMARY,
                      command=self.update_description).pack(anchor='w', pady=2)
        
        # Descripción
        self.desc_frame = tk.Frame(main_frame, bg=COLOR_BG_PANEL, relief=tk.SUNKEN, bd=1)
        self.desc_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Label para la descripción (se actualizará dinámicamente)
        self.desc_label = tk.Label(self.desc_frame, font=FONT_SMALL,
                bg=COLOR_BG_PANEL, fg=COLOR_TEXT_PRIMARY,
                justify=tk.LEFT)
        self.desc_label.pack(padx=10, pady=8)
        
        # Actualizar descripción inicial
        self.update_description()
        
        # Botones
        button_frame = tk.Frame(main_frame, bg=COLOR_BG_PANEL)
        button_frame.pack(fill=tk.X)
        
        tk.Button(button_frame, text="Cancel", font=FONT_BOLD,
                 bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_BUTTON_ENABLED,
                 width=12, command=self.cancel).pack(side=tk.RIGHT, padx=(5, 0))

        tk.Button(button_frame, text="Create Card", font=FONT_BOLD,
                 bg=COLOR_PRIMARY_BLUE, fg=COLOR_TEXT_BUTTON_ENABLED,
                 width=12, command=self.create_card).pack(side=tk.RIGHT)        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.create_card())
        self.dialog.bind('<Escape>', lambda e: self.cancel())
    
    def update_description(self):
        """Actualiza la descripción según el tipo de tarjeta seleccionada"""
        card_type = self.card_type_var.get()
        error_counter = "3" if card_type == "5542" else "8"  # 5528 tiene 8 intentos con secuencia de bits
        default_psc = "FF FF FF" if card_type == "5542" else "FF FF"  # 5542: 3 bytes, 5528: 2 bytes
        
        desc_text = ("The card will be created with factory default settings:\n"
                    "• Memory filled with FF values\n" 
                    f"• Default PSC: {default_psc}\n"
                    f"• Error counter: {error_counter}\n"
                    "• No protection bits set")
        
        self.desc_label.config(text=desc_text)
        
    def create_card(self):
        """Crea la tarjeta con los datos especificados"""
        name = self.name_var.get().strip()
        card_type = self.card_type_var.get()
        
        if not name:
            messagebox.showerror("Error", "Please enter a card name")
            return
            
        # Resultado para callback
        self.result = {
            'name': name,
            'type': card_type,
            'action': 'create'
        }
        
        self.dialog.destroy()
        if self.callback:
            self.callback(self.result)
    
    def cancel(self):
        """Cancela la operación"""
        self.dialog.destroy()

class ConfirmationDialog:
    """Diálogo de confirmación personalizado con formato consistente"""
    
    def __init__(self, parent, title, message, icon_type="question", compact=False):
        self.result = None
        self.compact = compact
        self.create_dialog(parent, title, message, icon_type)
    
    def create_dialog(self, parent, title, message, icon_type):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.configure(bg=COLOR_BG_MAIN)
        
        # Configurar icono de ETSISI
        set_dialog_icon(self.dialog)
        
        # Hacer modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Frame principal con padding reducido si es compacto
        padding = 15 if self.compact else 30
        main_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN, padx=padding, pady=padding)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame superior con icono y mensaje
        message_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        message_frame.pack(fill=tk.X, pady=(0, 15 if self.compact else 20))
        
        # Icono PNG según el título/tipo - más pequeño si es compacto
        icon_size = (48, 48) if self.compact else (72, 72)
        icon_image = None
        if "Clear Card" in title:
            icon_image = load_icon_image("clear_card.png", icon_size)
        elif "Close Card" in title:
            icon_image = load_icon_image("close_all_cards.png", icon_size) 
        elif "New Card" in title:
            icon_image = load_icon_image("new_card.png", icon_size)
        
        if icon_image:
            icon_label = tk.Label(message_frame, image=icon_image, bg=COLOR_BG_MAIN)
            icon_label.image = icon_image  # Mantener referencia
        else:
            # Fallback a emoji si no se puede cargar el PNG - más pequeño si es compacto
            icon_text = "❓" if icon_type == "question" else "⚠️" if icon_type == "warning" else "ℹ️"
            icon_color = COLOR_PRIMARY_BLUE if icon_type == "question" else COLOR_WARNING if icon_type == "warning" else COLOR_PRIMARY_BLUE
            font_size = 24 if self.compact else 32
            icon_label = tk.Label(message_frame, text=icon_text, font=("Segoe UI Emoji", font_size),
                                 fg=icon_color, bg=COLOR_BG_MAIN)
        
        icon_label.pack(side=tk.LEFT, padx=(0, 10 if self.compact else 15))
        
        # Mensaje con fuente más pequeña si es compacto
        message_font = FONT_NORMAL if self.compact else FONT_LARGE
        wrap_length = 400 if self.compact else 350  # Más ancho para diálogos compactos
        message_label = tk.Label(message_frame, text=message, font=message_font,
                                fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN,
                                wraplength=wrap_length, justify=tk.CENTER if self.compact else tk.LEFT)
        message_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Frame de botones
        button_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        button_frame.pack()
        
        # Botones con estilo consistente - más pequeños si es compacto
        button_width = 8 if self.compact else 10
        button_font = FONT_NORMAL if self.compact else FONT_BOLD
        yes_btn = tk.Button(button_frame, text="Yes", command=self.yes_clicked,
                           bg=COLOR_BUTTON_PRIMARY, fg=COLOR_TEXT_BUTTON_ENABLED, 
                           font=button_font, width=button_width, height=1, relief=tk.FLAT)
        yes_btn.pack(side=tk.LEFT, padx=5)
        
        no_btn = tk.Button(button_frame, text="No", command=self.no_clicked,
                          bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_PRIMARY, 
                          font=button_font, width=button_width, height=1, relief=tk.FLAT)
        no_btn.pack(side=tk.LEFT, padx=5)
        
        # Bindings de teclado
        self.dialog.bind('<Return>', lambda e: self.yes_clicked())
        self.dialog.bind('<Escape>', lambda e: self.no_clicked())
        
        # Centrar y mostrar
        center_dialog_on_parent(self.dialog, parent, auto_size=True)
        
        # Focus en botón Sí por defecto
        yes_btn.focus()
    
    def yes_clicked(self):
        self.result = True
        self.dialog.destroy()
    
    def no_clicked(self):
        self.result = False
        self.dialog.destroy()
    
    def show(self):
        """Muestra el diálogo y devuelve el resultado"""
        self.dialog.wait_window()
        return self.result

class InfoDialog:
    """Diálogo de información personalizado con formato consistente"""
    
    def __init__(self, parent, title, message, icon_type="info"):
        self.create_dialog(parent, title, message, icon_type)
    
    def create_dialog(self, parent, title, message, icon_type):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.configure(bg=COLOR_BG_MAIN)
        
        # Configurar icono de ETSISI
        set_dialog_icon(self.dialog)
        
        # Hacer modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Frame principal con padding
        main_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN, padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame superior con icono y mensaje
        message_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        message_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Icono según el tipo
        if icon_type == "success":
            icon_text = "✅"
            icon_color = COLOR_SUCCESS
        elif icon_type == "error":
            icon_text = "❌"
            icon_color = COLOR_ERROR
        elif icon_type == "warning":
            icon_text = "⚠️"
            icon_color = COLOR_WARNING
        else:  # info
            icon_text = "ℹ️"
            icon_color = COLOR_PRIMARY_BLUE
        
        icon_label = tk.Label(message_frame, text=icon_text, font=("Segoe UI Emoji", 32),
                             fg=icon_color, bg=COLOR_BG_MAIN)
        icon_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # Mensaje
        message_label = tk.Label(message_frame, text=message, font=FONT_LARGE,
                                fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN,
                                wraplength=350, justify=tk.LEFT)
        message_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Botón OK
        ok_btn = tk.Button(main_frame, text="OK", command=self.dialog.destroy,
                          bg=COLOR_BUTTON_PRIMARY, fg=COLOR_TEXT_BUTTON_ENABLED, 
                          font=FONT_BOLD, width=10, height=1, relief=tk.FLAT)
        ok_btn.pack()
        
        # Bindings de teclado
        self.dialog.bind('<Return>', lambda e: self.dialog.destroy())
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        
        # Centrar y mostrar
        center_dialog_on_parent(self.dialog, parent, auto_size=True)
        
        # Focus en botón OK
        ok_btn.focus()

class ClearLogDialog:
    """Diálogo de confirmación para limpiar el log"""
    
    def __init__(self, parent, callback):
        self.callback = callback
        self.create_dialog(parent)
    
    def create_dialog(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Clear Log")
        self.dialog.configure(bg=COLOR_BG_MAIN)
        
        # Configurar icono de ETSISI
        set_dialog_icon(self.dialog)
        
        # Hacer modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Frame principal con padding
        main_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN, padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame superior con icono y mensaje
        message_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        message_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Icono PNG de advertencia
        icon_image = load_icon_image("clear_card.png", (72, 72))
        if icon_image:
            icon_label = tk.Label(message_frame, image=icon_image, bg=COLOR_BG_MAIN)
            icon_label.image = icon_image  # Mantener referencia
        else:
            # Fallback a emoji si no se puede cargar el PNG
            icon_label = tk.Label(message_frame, text="🗑️", font=("Segoe UI Emoji", 32),
                                 fg=COLOR_WARNING, bg=COLOR_BG_MAIN)
        icon_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # Mensaje
        message_label = tk.Label(message_frame, text="Do you want to clear all log content?",
                                font=FONT_LARGE, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN,
                                wraplength=350, justify=tk.LEFT)
        message_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Frame de botones
        button_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        button_frame.pack()
        
        # Botones con estilo consistente
        clear_btn = tk.Button(button_frame, text="Clear", command=self.clear_clicked,
                             bg=COLOR_WARNING, fg=COLOR_TEXT_BUTTON_ENABLED, 
                             font=FONT_BOLD, width=10, height=1, relief=tk.FLAT)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(button_frame, text="Cancel", command=self.dialog.destroy,
                              bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_PRIMARY, 
                              font=FONT_BOLD, width=10, height=1, relief=tk.FLAT)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Bindings de teclado
        self.dialog.bind('<Return>', lambda e: self.clear_clicked())
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        
        # Centrar y mostrar
        center_dialog_on_parent(self.dialog, parent, auto_size=True)
        
        # Focus en botón Cancelar por seguridad
        cancel_btn.focus()
    
    def clear_clicked(self):
        self.callback()
        self.dialog.destroy()

class OpenCardDialog:
    """Diálogo personalizado para abrir archivos de tarjeta"""
    
    def __init__(self, parent, callback):
        self.callback = callback
        self.result = None
        self.create_dialog(parent)
    
    def create_dialog(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Open Card File")
        self.dialog.configure(bg=COLOR_BG_MAIN)
        
        # Configurar icono de ETSISI
        set_dialog_icon(self.dialog)
        
        # Hacer modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Frame principal con padding
        main_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN, padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame superior con icono y título
        header_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Frame interno para centrar el contenido
        content_frame = tk.Frame(header_frame, bg=COLOR_BG_MAIN)
        content_frame.pack(expand=True)
        
        # Icono PNG
        icon_image = load_icon_image("open_card.png", (64, 64))
        if icon_image:
            icon_label = tk.Label(content_frame, image=icon_image, bg=COLOR_BG_MAIN)
            icon_label.image = icon_image  # Mantener referencia
        else:
            # Fallback a emoji si no se puede cargar el PNG
            icon_label = tk.Label(content_frame, text="📁", font=("Segoe UI Emoji", 24),
                                 fg=COLOR_PRIMARY_BLUE, bg=COLOR_BG_MAIN)
        icon_label.pack(side=tk.LEFT, padx=(0, 8))
        
        # Título
        title_label = tk.Label(content_frame, text="Select Card File to Open",
                              font=FONT_LARGE_BOLD, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        title_label.pack(side=tk.LEFT)
        
        # Frame de entrada de archivo
        file_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        file_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(file_frame, text="Path/name (without quotes):", bg=COLOR_BG_MAIN, 
                font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY).pack(anchor='w')
        
        path_frame = tk.Frame(file_frame, bg=COLOR_BG_MAIN)
        path_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.path_entry = tk.Entry(path_frame, font=FONT_NORMAL, width=50)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_btn = tk.Button(path_frame, text="Browse...", command=self.browse_file,
                              bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_PRIMARY, 
                              font=FONT_NORMAL, width=10, relief=tk.FLAT)
        browse_btn.pack(side=tk.RIGHT)
        
        # Frame de botones
        button_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        button_frame.pack(pady=10)
        
        open_btn = tk.Button(button_frame, text="Open", command=self.open_clicked,
                            bg=COLOR_BUTTON_PRIMARY, fg=COLOR_TEXT_BUTTON_ENABLED, 
                            font=FONT_BOLD, width=12, height=1, relief=tk.FLAT)
        open_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(button_frame, text="Cancel", command=self.dialog.destroy,
                              bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_PRIMARY, 
                              font=FONT_BOLD, width=12, height=1, relief=tk.FLAT)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Bindings de teclado
        self.dialog.bind('<Return>', lambda e: self.open_clicked())
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        
        # Centrar y mostrar
        center_dialog_on_parent(self.dialog, parent, auto_size=True)
        
        # Focus en entrada de texto
        self.path_entry.focus()
    
    def browse_file(self):
        """Abre el diálogo nativo para seleccionar archivo"""
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            parent=self.dialog,
            title="Select Card File",
            filetypes=[("Text files", "*.txt"), ("Card files", "*.card"), ("All files", "*.*")]
        )
        if filepath:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, filepath)
    
    def open_clicked(self):
        filepath = self.path_entry.get().strip()
        if filepath and os.path.exists(filepath):
            self.result = filepath
            self.callback(filepath)
            self.dialog.destroy()
        else:
            InfoDialog(self.dialog, "Error", "Please select a valid file path", "error")

class SaveCardDialog:
    """Diálogo personalizado para guardar archivos de tarjeta"""
    
    def __init__(self, parent, default_name, callback):
        self.callback = callback
        self.default_name = default_name
        self.result = None
        self.create_dialog(parent)
    
    def create_dialog(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Save Card File")
        self.dialog.configure(bg=COLOR_BG_MAIN)
        
        # Configurar icono de ETSISI
        set_dialog_icon(self.dialog)
        
        # Hacer modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Frame principal con padding
        main_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN, padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame superior con icono y título
        header_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Frame interno para centrar el contenido
        content_frame = tk.Frame(header_frame, bg=COLOR_BG_MAIN)
        content_frame.pack(expand=True)
        
        # Icono PNG
        icon_image = load_icon_image("save_card.png", (64, 64))
        if icon_image:
            icon_label = tk.Label(content_frame, image=icon_image, bg=COLOR_BG_MAIN)
            icon_label.image = icon_image  # Mantener referencia
        else:
            # Fallback a emoji si no se puede cargar el PNG
            icon_label = tk.Label(content_frame, text="💾", font=("Segoe UI Emoji", 24),
                                 fg=COLOR_SUCCESS, bg=COLOR_BG_MAIN)
        icon_label.pack(side=tk.LEFT, padx=(0, 8))
        
        # Título
        title_label = tk.Label(content_frame, text="Save Card File",
                              font=FONT_LARGE_BOLD, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        title_label.pack(side=tk.LEFT)
        
        # Frame de entrada de archivo
        file_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        file_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(file_frame, text="Path/name (without quotes):", bg=COLOR_BG_MAIN, 
                font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY).pack(anchor='w')
        
        path_frame = tk.Frame(file_frame, bg=COLOR_BG_MAIN)
        path_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.path_entry = tk.Entry(path_frame, font=FONT_NORMAL, width=50)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.path_entry.insert(0, f"{self.default_name}.txt")
        
        browse_btn = tk.Button(path_frame, text="Browse...", command=self.browse_file,
                              bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_PRIMARY, 
                              font=FONT_NORMAL, width=10, relief=tk.FLAT)
        browse_btn.pack(side=tk.RIGHT)
        
        # Frame de botones
        button_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        button_frame.pack(pady=10)
        
        save_btn = tk.Button(button_frame, text="Save", command=self.save_clicked,
                            bg=COLOR_BUTTON_PRIMARY, fg=COLOR_TEXT_BUTTON_ENABLED, 
                            font=FONT_BOLD, width=12, height=1, relief=tk.FLAT)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(button_frame, text="Cancel", command=self.dialog.destroy,
                              bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_PRIMARY, 
                              font=FONT_BOLD, width=12, height=1, relief=tk.FLAT)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Bindings de teclado
        self.dialog.bind('<Return>', lambda e: self.save_clicked())
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        
        # Centrar y mostrar
        center_dialog_on_parent(self.dialog, parent, auto_size=True)
        
        # Focus en entrada de texto y seleccionar el nombre sin extensión
        self.path_entry.focus()
        self.path_entry.select_range(0, len(self.default_name))
    
    def browse_file(self):
        """Abre el diálogo nativo para seleccionar ubicación de guardado"""
        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            parent=self.dialog,
            title="Save Card File",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("Card files", "*.card"), ("All files", "*.*")],
            initialfile=f"{self.default_name}.txt"
        )
        if filepath:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, filepath)
    
    def save_clicked(self):
        filepath = self.path_entry.get().strip()
        if filepath:
            self.result = filepath
            self.callback(filepath)
            self.dialog.destroy()
        else:
            InfoDialog(self.dialog, "Error", "Please enter a file name", "error")

class SaveLogDialog:
    """Diálogo personalizado para guardar archivos de log"""
    
    def __init__(self, parent, callback):
        self.callback = callback
        self.result = None
        self.create_dialog(parent)
    
    def create_dialog(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Save Command Log")
        self.dialog.configure(bg=COLOR_BG_MAIN)
        
        # Configurar icono de ETSISI
        set_dialog_icon(self.dialog)
        
        # Hacer modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Frame principal con padding
        main_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN, padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame superior con título (sin icono)
        header_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Frame interno para centrar el contenido
        content_frame = tk.Frame(header_frame, bg=COLOR_BG_MAIN)
        content_frame.pack(expand=True)
        
        # Título (sin icono)
        title_label = tk.Label(content_frame, text="Save Command Log",
                              font=FONT_LARGE_BOLD, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        title_label.pack()
        
        # Frame de entrada de archivo
        file_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        file_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(file_frame, text="Path/name (without quotes):", bg=COLOR_BG_MAIN, 
                font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY).pack(anchor='w')
        
        path_frame = tk.Frame(file_frame, bg=COLOR_BG_MAIN)
        path_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.path_entry = tk.Entry(path_frame, font=FONT_NORMAL, width=50)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.path_entry.insert(0, "command_log.txt")
        
        browse_btn = tk.Button(path_frame, text="Browse...", command=self.browse_file,
                              bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_PRIMARY, 
                              font=FONT_NORMAL, width=10, relief=tk.FLAT)
        browse_btn.pack(side=tk.RIGHT)
        
        # Frame de botones
        button_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        button_frame.pack(pady=10)
        
        save_btn = tk.Button(button_frame, text="Save", command=self.save_clicked,
                            bg=COLOR_BUTTON_PRIMARY, fg=COLOR_TEXT_BUTTON_ENABLED, 
                            font=FONT_BOLD, width=12, height=1, relief=tk.FLAT)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(button_frame, text="Cancel", command=self.dialog.destroy,
                              bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_PRIMARY, 
                              font=FONT_BOLD, width=12, height=1, relief=tk.FLAT)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Bindings de teclado
        self.dialog.bind('<Return>', lambda e: self.save_clicked())
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        
        # Centrar y mostrar
        center_dialog_on_parent(self.dialog, parent, auto_size=True)
        
        # Focus en entrada de texto y seleccionar el nombre sin extensión
        self.path_entry.focus()
        self.path_entry.select_range(0, 11)  # Seleccionar "command_log"
    
    def browse_file(self):
        """Abre el diálogo nativo para seleccionar ubicación de guardado"""
        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            parent=self.dialog,
            title="Save Command Log",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile="command_log.txt"
        )
        if filepath:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, filepath)
    
    def save_clicked(self):
        filepath = self.path_entry.get().strip()
        if filepath:
            self.result = filepath
            self.callback(filepath)
            self.dialog.destroy()
        else:
            InfoDialog(self.dialog, "Error", "Please enter a file name", "error")

class CardNameDialog:
    """Diálogo personalizado para solicitar el nombre de una tarjeta"""
    
    def __init__(self, parent, suggested_name=""):
        self.result = None
        self.create_dialog(parent, suggested_name)
    
    def create_dialog(self, parent, suggested_name):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Card Name")
        self.dialog.configure(bg=COLOR_BG_MAIN)
        
        # Configurar icono de ETSISI
        set_dialog_icon(self.dialog)
        
        # Hacer modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Frame principal con padding amplio
        main_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN, padx=40, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame superior con icono y título
        header_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Icono PNG
        icon_image = load_icon_image("new_card.png", (64, 64))
        if icon_image:
            icon_label = tk.Label(header_frame, image=icon_image, bg=COLOR_BG_MAIN)
            icon_label.image = icon_image  # Mantener referencia
        else:
            # Fallback a emoji si no se puede cargar el PNG
            icon_label = tk.Label(header_frame, text="💳", font=("Segoe UI Emoji", 24),
                                 fg=COLOR_PRIMARY_BLUE, bg=COLOR_BG_MAIN)
        icon_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # Título
        title_label = tk.Label(header_frame, text="Card Name",
                              font=FONT_LARGE_BOLD, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Mensaje explicativo
        message_label = tk.Label(main_frame, text="Enter a name for this card:",
                                font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        message_label.pack(pady=(0, 15))
        
        # Campo de entrada amplio
        self.name_entry = tk.Entry(main_frame, font=FONT_LARGE, width=50, justify='center')
        self.name_entry.pack(pady=(0, 20), ipady=8)
        
        if suggested_name:
            self.name_entry.insert(0, suggested_name)
            self.name_entry.select_range(0, tk.END)
        
        # Frame de botones
        button_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        button_frame.pack(pady=10)
        
        ok_btn = tk.Button(button_frame, text="OK", command=self.ok_clicked,
                          bg=COLOR_BUTTON_PRIMARY, fg=COLOR_TEXT_BUTTON_ENABLED, 
                          font=FONT_BOLD, width=12, height=1, relief=tk.FLAT)
        ok_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(button_frame, text="Cancel", command=self.cancel_clicked,
                              bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_PRIMARY, 
                              font=FONT_BOLD, width=12, height=1, relief=tk.FLAT)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Bindings de teclado
        self.dialog.bind('<Return>', lambda e: self.ok_clicked())
        self.dialog.bind('<Escape>', lambda e: self.cancel_clicked())
        
        # Centrar y mostrar
        center_dialog_on_parent(self.dialog, parent, auto_size=True)
        
        # Focus en el campo de entrada
        self.name_entry.focus()
        
        # Esperar a que se cierre el diálogo
        self.dialog.wait_window()
    
    def ok_clicked(self):
        name = self.name_entry.get().strip()
        if name:
            self.result = name
            self.dialog.destroy()
        else:
            InfoDialog(self.dialog, "Error", "Please enter a card name", "error")
    
    def cancel_clicked(self):
        self.result = None
        self.dialog.destroy()
    
    def get_result(self):
        """Retorna el nombre ingresado por el usuario, o None si se canceló"""
        return self.result

class ProtectionBitsDialog:
    """Diálogo para mostrar los bits de protección de la tarjeta - Específico por tipo"""
    
    def __init__(self, parent, protection_bits_data, card_type=CARD_TYPE_5542, memory_manager=None):
        self.protection_bits_data = protection_bits_data
        self.card_type = card_type
        self.memory_manager = memory_manager  # Para obtener datos reales
        self.current_page = 0  # Para navegación en SLE5528
        
        # Configurar según tipo de tarjeta
        if card_type == CARD_TYPE_5542:
            self.total_addresses = 32  # Solo primeros 32 bytes
            self.rows_per_page = 2     # 2 filas fijas (0x00-0x0F, 0x10-0x1F)
            self.total_pages = 1       # Solo 1 página
        else:  # CARD_TYPE_5528
            self.total_addresses = 1024  # Todas las direcciones
            self.rows_per_page = 4       # 4 filas por página
            self.total_pages = 16        # 1024 / 16 = 64 filas / 4 filas por página = 16 páginas
            
        self.create_dialog(parent)
    
    def _get_page_format(self, page_num):
        """Convierte número de página a formato X.Y (ej: 0->0.1, 4->1.1, 15->3.4)"""
        # Calcular grupo de 4 páginas (0-3: grupo 0, 4-7: grupo 1, etc.)
        group = page_num // 4
        # Calcular posición dentro del grupo (0-3)  
        position = (page_num % 4) + 1
        return f"{group}.{position}"
    
    def create_dialog(self, parent):
        self.dialog = tk.Toplevel(parent)
        
        # Título específico por tipo
        if self.card_type == CARD_TYPE_5542:
            title = "PROTECTION BITS BREAKDOWN - SLE5542 (256B)"
        else:
            title = "PROTECTION BITS BREAKDOWN - SLE5528 (1KB)"
            
        self.dialog.title(title)
        self.dialog.configure(bg=COLOR_BG_MAIN)
        
        # Configurar icono de ETSISI
        set_dialog_icon(self.dialog)
        
        # Hacer modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Usar auto-sizing en lugar de tamaño fijo
        self.dialog.configure(padx=15, pady=10)
        
        # Crear contenido primero
        self.create_content()
        
        # Estrategia mejorada para centrado sin parpadeo:
        # 1. Forzar cálculo de tamaño
        self.dialog.update_idletasks()
        
        # 2. Centrar directamente (sin delay)
        dialog_width = self.dialog.winfo_reqwidth()
        dialog_height = self.dialog.winfo_reqheight()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # 3. Asegurar visibilidad
        self.dialog.lift()
        self.dialog.focus_force()
        
    def create_content(self):
        """Crear el contenido del diálogo"""
        # FONDO PERMANENTE - Canvas que cubre toda la ventana
        self.background_canvas = tk.Canvas(self.dialog, bg=COLOR_BG_MAIN, highlightthickness=0)
        self.background_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Frame principal sobre el canvas
        main_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame superior con navegación (solo para SLE5528)
        if self.card_type == CARD_TYPE_5528:
            self._create_navigation_frame(main_frame)
        
        # Frame con la tabla de bits
        self.bits_frame = tk.Frame(main_frame, bg="#2B2B2B", padx=8, pady=8)
        self.bits_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Crear la tabla de bits de protección
        self._create_protection_bits_table()
        
        # Frame inferior con la tabla detallada
        detail_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        detail_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crear las tablas de detalles
        self._create_detail_tables(detail_frame)
        
        # Botón de cerrar
        close_btn = tk.Button(main_frame, text="Close", command=self.dialog.destroy,
                             bg=COLOR_BUTTON_PRIMARY, fg=COLOR_TEXT_BUTTON_ENABLED, 
                             font=FONT_BOLD, width=12, height=1, relief=tk.FLAT)
        close_btn.pack(pady=8)
        
        # Bindings
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        if self.card_type == CARD_TYPE_5528:
            self.dialog.bind('<Up>', lambda e: self.navigate_up())
            self.dialog.bind('<Down>', lambda e: self.navigate_down())
            self.dialog.bind('<Prior>', lambda e: self.navigate_up())  # Page Up
            self.dialog.bind('<Next>', lambda e: self.navigate_down())  # Page Down
        
        # Focus en botón cerrar
        close_btn.focus_set()
    
    def _create_navigation_frame(self, parent):
        """Crea el frame de navegación para SLE5528"""
        nav_frame = tk.Frame(parent, bg=COLOR_BG_MAIN)
        nav_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Información de página
        if self.card_type == CARD_TYPE_5528:
            page_text = f"Page {self._get_page_format(self.current_page)} of {self.total_pages}"
        else:
            page_text = f"Page {self.current_page + 1} of {self.total_pages}"
            
        self.page_info_label = tk.Label(nav_frame, 
                                       text=page_text,
                                       font=FONT_BOLD, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        self.page_info_label.pack()
        
        # Botones de navegación
        button_frame = tk.Frame(nav_frame, bg=COLOR_BG_MAIN)
        button_frame.pack(pady=5)
        
        self.up_btn = tk.Button(button_frame, text="▲ Previous", command=self.navigate_up,
                               bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_PRIMARY, 
                               font=FONT_NORMAL, width=10, relief=tk.FLAT)
        self.up_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.down_btn = tk.Button(button_frame, text="▼ Next", command=self.navigate_down,
                                 bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_PRIMARY, 
                                 font=FONT_NORMAL, width=10, relief=tk.FLAT)
        self.down_btn.pack(side=tk.LEFT)
        
        # Información de rango de direcciones
        self.range_info_label = tk.Label(nav_frame, 
                                        text=self._get_address_range_text(),
                                        font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        self.range_info_label.pack(pady=2)
        
        self._update_navigation_buttons()
    
    def navigate_up(self):
        """Navega hacia arriba (página anterior)"""
        if self.current_page > 0:
            self.current_page -= 1
            self._update_display()
    
    def navigate_down(self):
        """Navega hacia abajo (página siguiente)"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._update_display()
    
    def _update_display(self):
        """Actualiza la visualización después de cambiar de página"""
        # Solo actualizar el contenido sin destruir la estructura
        self._update_table_content()
        
        # Actualizar navegación
        self._update_navigation_buttons()
        
        # Forzar actualización final
        self.dialog.update_idletasks()
    
    def _update_navigation_buttons(self):
        """Actualiza el estado de los botones de navegación y la información de página"""
        if hasattr(self, 'up_btn'):
            self.up_btn.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        if hasattr(self, 'down_btn'):
            self.down_btn.config(state=tk.NORMAL if self.current_page < self.total_pages - 1 else tk.DISABLED)
        
        # Actualizar la información de página
        if hasattr(self, 'page_info_label'):
            if self.card_type == CARD_TYPE_5528:
                page_text = f"Page {self._get_page_format(self.current_page)} of {self.total_pages}"
            else:
                page_text = f"Page {self.current_page + 1} of {self.total_pages}"
            self.page_info_label.config(text=page_text)
        
        # Actualizar la información del rango de direcciones
        if hasattr(self, 'range_info_label'):
            self.range_info_label.config(text=self._get_address_range_text())
    
    def _get_address_range_text(self):
        """Obtiene el texto del rango de direcciones actual"""
        start_addr = self.current_page * self.rows_per_page * 16
        end_addr = min(start_addr + (self.rows_per_page * 16) - 1, self.total_addresses - 1)
        return f"Addresses: 0x{start_addr:03X} - 0x{end_addr:03X}"
    
    def _create_protection_bits_table(self):
        """Crea la tabla superior con los bits de protección en formato visual"""
        # Solo crear la estructura si no existe
        if not hasattr(self, 'table_created'):
            self._create_table_structure()
            self.table_created = True
        
        # Actualizar el contenido de la estructura existente
        self._update_table_content()
    
    def _create_table_structure(self):
        """Crea la estructura fija de la tabla (solo una vez)"""
        # Título
        self.title_label = tk.Label(self.bits_frame, text="PROTECTION BITS", 
                              font=("Consolas", 12, "bold"), fg="white", bg="#2B2B2B")
        self.title_label.pack(pady=(0, 10))
        
        # Frame para las filas de direcciones
        self.table_frame = tk.Frame(self.bits_frame, bg="#2B2B2B")
        self.table_frame.pack()
        
        # Crear estructura fija para el máximo número de filas posibles
        max_rows = 4 if self.card_type == CARD_TYPE_5528 else 2
        self.row_widgets = []
        
        for row in range(max_rows):
            row_frame = tk.Frame(self.table_frame, bg="#2B2B2B")
            row_frame.pack(pady=2)
            
            # Label de dirección
            addr_label = tk.Label(row_frame, text="", 
                                 font=("Consolas", 10, "bold"), fg="white", bg="#2B2B2B")
            addr_label.pack(side=tk.LEFT, padx=(0, 10))
            
            # Crear 16 celdas para esta fila
            cells = []
            for col in range(16):
                cell = tk.Label(row_frame, text="", 
                               font=("Consolas", 10, "bold"), 
                               width=3, relief=tk.RAISED, borderwidth=1)
                cell.pack(side=tk.LEFT, padx=1)
                cells.append(cell)
            
            self.row_widgets.append({
                'frame': row_frame,
                'addr_label': addr_label,
                'cells': cells
            })
    
    def _update_table_content(self):
        """Actualiza solo el contenido de la tabla existente"""
        # Calcular las filas a mostrar según el tipo y página
        if self.card_type == CARD_TYPE_5542:
            start_row = 0
            rows_to_show = 2
        else:
            start_row = self.current_page * self.rows_per_page
            rows_to_show = min(self.rows_per_page, 
                             (self.total_addresses // 16) - start_row)
        
        # Actualizar cada fila
        for row_idx in range(len(self.row_widgets)):
            row_data = self.row_widgets[row_idx]
            
            if row_idx < rows_to_show:
                # Mostrar esta fila
                current_row = start_row + row_idx
                start_addr = current_row * 16
                
                if start_addr < self.total_addresses:
                    # Actualizar label de dirección
                    row_data['addr_label'].config(text=f"{start_addr:04X} :")
                    row_data['frame'].pack(pady=2)
                    
                    # Actualizar cada celda
                    for col in range(16):
                        addr = start_addr + col
                        cell = row_data['cells'][col]
                        
                        if addr >= self.total_addresses:
                            # Celda vacía
                            cell.config(text="--", fg="gray", bg="#2B2B2B", relief=tk.FLAT)
                        else:
                            bit_value = self._get_protection_bit(addr)
                            hex_value = self._get_memory_value(addr)
                            
                            if bit_value == 0:
                                # Protegido (rojo)
                                cell.config(text=f"{hex_value:02X}", fg="white", bg="red", relief=tk.RAISED)
                            else:
                                # No protegido
                                if self.card_type == CARD_TYPE_5542:
                                    if addr < 32:
                                        cell.config(text=f"{hex_value:02X}", fg="black", bg="yellow", relief=tk.RAISED)
                                    else:
                                        cell.config(text=f"{hex_value:02X}", fg="white", bg="gray", relief=tk.RAISED)
                                else:
                                    cell.config(text=f"{hex_value:02X}", fg="black", bg="yellow", relief=tk.RAISED)
                else:
                    # Ocultar esta fila
                    row_data['frame'].pack_forget()
            else:
                # Ocultar esta fila
                row_data['frame'].pack_forget()
    
    def _create_detail_tables(self, parent):
        """Crea las tablas de detalle inferiores"""
        # Información de resumen para el tipo de tarjeta
        info_frame = tk.Frame(parent, bg=COLOR_BG_MAIN)
        info_frame.pack(fill=tk.X, pady=10)
        
        if self.card_type == CARD_TYPE_5542:
            info_text = ("SLE5542 Protection Bits:\n"
                        "• Only first 32 bytes (0x00-0x1F) can be protected\n"
                        "• 32 protection bits total (4 bytes)\n"
                        "• Red = Protected (write disabled)\n"
                        "• Yellow = Writable (write enabled)")
        else:
            info_text = ("SLE5528 Protection Bits:\n"
                        "• All 1024 bytes (0x000-0x3FF) can be protected\n"
                        "• 1024 protection bits total (128 bytes)\n"
                        "• Use navigation arrows to view different pages\n"
                        "• Red = Protected, Yellow = Writable")
        
        info_label = tk.Label(info_frame, text=info_text,
                             font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN,
                             justify=tk.LEFT)
        info_label.pack()
    
    def _get_protection_bit(self, address):
        """Obtiene el bit de protección real para una dirección específica"""
        if self.memory_manager:
            return 0 if self.memory_manager.is_protected(address) else 1
        
        # Valores por defecto según especificaciones (direcciones bloqueadas de fábrica)
        if self.card_type == CARD_TYPE_5542:
            # SLE5542: Solo primeros 32 bytes tienen protection bits
            if address >= 32:
                return 1  # Direcciones fuera de rango siempre "no protegidas"
            # Usar constantes de fábrica
            return 0 if address in FACTORY_PROTECTED_5542 else 1
        else:  # CARD_TYPE_5528
            # SLE5528: Todas las direcciones tienen protection bits
            if address >= 1024:
                return 1  # Direcciones fuera de rango
            # Usar constantes de fábrica
            return 0 if address in FACTORY_PROTECTED_5528 else 1
    
    def _get_memory_value(self, address):
        """Obtiene el valor real de memoria para una dirección específica"""
        if self.memory_manager:
            # Usar read_memory para leer un solo byte
            data = self.memory_manager.read_memory(address, 1)
            return data[0] if data else 0x00
        
        # Valores por defecto según especificaciones
        if self.card_type == CARD_TYPE_5542:
            if address >= 256:  # SLE5542 tiene 256 bytes
                return 0x00
            # Direcciones protegidas tienen valores de fábrica
            if address <= 0x03:
                return 0xFF  # Valor típico de fábrica
            return 0x00  # Memoria inicializada
        else:  # CARD_TYPE_5528
            if address >= 1024:  # SLE5528 tiene 1024 bytes
                return 0x00
            # Direcciones protegidas tienen valores de fábrica
            if address <= 0x03 or address >= 0x3FC:
                return 0xFF  # Valor típico de fábrica
            return 0x00  # Memoria inicializada


class SettingsDialog:
    """Diálogo de Settings con control de acceso administrativo"""
    
    def __init__(self, parent, main_interface):
        self.parent = parent
        self.main_interface = main_interface
        self.dialog = None
        self.admin_unlocked = False
        
        # Código de administrador
        self.admin_code = "admin2025"  # "password" admin2025 = placeholder
    
    def show(self):
        """Muestra el diálogo de Settings"""
        # Crear ventana modal
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Settings")
        self.dialog.geometry("450x550")
        self.dialog.resizable(True, True)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=COLOR_BG_MAIN)
        
        # Centrar el diálogo
        self._center_dialog()
        
        # Crear contenido
        self._create_content()
        
        # Foco inicial en el campo de admin code
        self.admin_entry.focus_set()
        
        # Manejar tecla Enter y Escape
        self.dialog.bind('<Return>', lambda e: self._check_admin_code())
        self.dialog.bind('<Escape>', lambda e: self._on_close())
        
        # Manejar cierre de ventana
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _center_dialog(self, width=420, height=520):
        """Centra el diálogo sobre la ventana padre con tamaño personalizable y más compacto"""
        # Asegurar que el padre está actualizado
        self.parent.update_idletasks()
        self.dialog.update_idletasks()
        
        # Obtener dimensiones REALES de la ventana padre
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Calcular posición centrada respecto a la ventana padre
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        # Obtener información de la pantalla donde está el padre
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        
        # Ajustar si se sale de los bordes, pero mantener cerca del padre
        x = max(parent_x - 100, min(x, parent_x + parent_width + 100 - width))
        y = max(parent_y - 50, min(y, parent_y + parent_height + 50 - height))
        
        # Aplicar geometría
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Forzar actualización
        self.dialog.update_idletasks()
    
    def _create_content(self):
        """Crea el contenido del diálogo"""
        # Frame principal con padding reducido
        main_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN, padx=15, pady=10)
        main_frame.pack(fill='both', expand=True)
        
        # Título más compacto
        title_label = tk.Label(main_frame, text="Application Settings", 
                              font=('Arial', 13, 'bold'), 
                              bg=COLOR_BG_MAIN, fg=COLOR_TEXT_PRIMARY)
        title_label.pack(pady=(0, 10))
        
        # === SECCIÓN DE CONFIGURACIÓN DE UI ===
        ui_frame = tk.LabelFrame(main_frame, text="User Interface Configuration", 
                                font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        ui_frame.pack(fill='x', pady=(0, 10))
        
        # Frame interno para UI settings con padding reducido
        ui_inner_frame = tk.Frame(ui_frame, bg=COLOR_BG_MAIN, padx=10, pady=8)
        ui_inner_frame.pack(fill='x')
        
        # === OPEN CARDS LAYOUT SUBSECTION ===
        cards_layout_frame = tk.LabelFrame(ui_inner_frame, text="Open Cards Layout", 
                                          font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        cards_layout_frame.pack(fill='x', pady=(0, 8))
        
        # Frame interno para cards layout más compacto
        cards_inner_frame = tk.Frame(cards_layout_frame, bg=COLOR_BG_MAIN, padx=8, pady=6)
        cards_inner_frame.pack(fill='x')
        
        # Variable para el layout de cards
        self.cards_layout_var = tk.StringVar(value="2_per_row")
        
        # Frame para los botones de radio más compacto
        layout_buttons_frame = tk.Frame(cards_inner_frame, bg=COLOR_BG_MAIN)
        layout_buttons_frame.pack(anchor='w', pady=(0, 3))
        
        # Opción: 2 cards por fila (4 filas) - más compacto
        radio_2_per_row = tk.Radiobutton(layout_buttons_frame, 
                                        text="2 cards per row (4 rows total)", 
                                        variable=self.cards_layout_var, 
                                        value="2_per_row",
                                        font=FONT_NORMAL, bg=COLOR_BG_MAIN, 
                                        fg=COLOR_TEXT_PRIMARY,
                                        selectcolor=COLOR_BG_PANEL,
                                        activebackground=COLOR_BG_MAIN,
                                        activeforeground=COLOR_TEXT_PRIMARY)
        radio_2_per_row.pack(anchor='w', pady=1)
        
        # Opción: 1 card por fila (8 filas) - más compacto
        radio_1_per_row = tk.Radiobutton(layout_buttons_frame, 
                                        text="1 card per row (8 rows total)", 
                                        variable=self.cards_layout_var, 
                                        value="1_per_row",
                                        font=FONT_NORMAL, bg=COLOR_BG_MAIN, 
                                        fg=COLOR_TEXT_PRIMARY,
                                        selectcolor=COLOR_BG_PANEL,
                                        activebackground=COLOR_BG_MAIN,
                                        activeforeground=COLOR_TEXT_PRIMARY)
        radio_1_per_row.pack(anchor='w', pady=1)
        
        # Botón Apply para Open Cards Layout
        apply_cards_btn = tk.Button(cards_inner_frame, text="Apply", 
                                   font=FONT_NORMAL, bg=COLOR_SUCCESS, 
                                   fg='white', padx=15, pady=3,
                                   command=self._apply_cards_layout, width=10)
        apply_cards_btn.pack(anchor='w', pady=(3, 0))
        
        # === SMALL SCREEN FORM FACTOR SUBSECTION ===
        small_screen_frame = tk.LabelFrame(ui_inner_frame, text="Small Screen Form Factor", 
                                          font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        small_screen_frame.pack(fill='x', pady=(8, 8))
        
        # Frame interno para small screen más compacto
        small_screen_inner_frame = tk.Frame(small_screen_frame, bg=COLOR_BG_MAIN, padx=8, pady=6)
        small_screen_inner_frame.pack(fill='x')
        
        # Variable para small screen form factor
        self.small_screen_var = tk.StringVar(value="deactivate")
        
        # Frame para los botones de small screen más compacto
        small_screen_buttons_frame = tk.Frame(small_screen_inner_frame, bg=COLOR_BG_MAIN)
        small_screen_buttons_frame.pack(anchor='w', pady=(0, 3))
        
        # Opción: Activate - más compacto
        radio_activate = tk.Radiobutton(small_screen_buttons_frame, 
                                       text="Activate", 
                                       variable=self.small_screen_var, 
                                       value="activate",
                                       font=FONT_NORMAL, bg=COLOR_BG_MAIN, 
                                       fg=COLOR_TEXT_PRIMARY,
                                       selectcolor=COLOR_BG_PANEL,
                                       activebackground=COLOR_BG_MAIN,
                                       activeforeground=COLOR_TEXT_PRIMARY)
        radio_activate.pack(anchor='w', pady=1)
        
        # Opción: Deactivate - más compacto
        radio_deactivate = tk.Radiobutton(small_screen_buttons_frame, 
                                         text="Deactivate", 
                                         variable=self.small_screen_var, 
                                         value="deactivate",
                                         font=FONT_NORMAL, bg=COLOR_BG_MAIN, 
                                         fg=COLOR_TEXT_PRIMARY,
                                         selectcolor=COLOR_BG_PANEL,
                                         activebackground=COLOR_BG_MAIN,
                                         activeforeground=COLOR_TEXT_PRIMARY)
        radio_deactivate.pack(anchor='w', pady=1)
        
        # Botón Apply para Small Screen Form Factor
        apply_small_screen_btn = tk.Button(small_screen_inner_frame, text="Apply", 
                                          font=FONT_NORMAL, bg=COLOR_SUCCESS, 
                                          fg='white', padx=15, pady=3,
                                          command=self._apply_small_screen_mode, width=10)
        apply_small_screen_btn.pack(anchor='w', pady=(3, 0))
        
        # === SECCIÓN ADMINISTRATIVA (ABAJO) ===
        admin_section_frame = tk.LabelFrame(main_frame, text="Administrative Settings", 
                                           font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        admin_section_frame.pack(fill='x', pady=(8, 8))
        
        # Frame interno para admin settings más compacto
        admin_inner_frame = tk.Frame(admin_section_frame, bg=COLOR_BG_MAIN, padx=10, pady=8)
        admin_inner_frame.pack(fill='x')
        
        # Label y field de Admin Code en la misma línea más compacto
        admin_code_frame = tk.Frame(admin_inner_frame, bg=COLOR_BG_MAIN)
        admin_code_frame.pack(fill='x', pady=(0, 6))
        
        admin_label = tk.Label(admin_code_frame, text="Admin Code:", 
                              font=FONT_NORMAL, bg=COLOR_BG_MAIN, 
                              fg=COLOR_TEXT_PRIMARY)
        admin_label.pack(side='left')
        
        self.admin_entry = tk.Entry(admin_code_frame, show="*", font=FONT_NORMAL, 
                                   width=15, bg='white', fg='black')
        self.admin_entry.pack(side='left', padx=(10, 10))
        
        # Botón Continue más pequeño al lado con padding reducido
        self.continue_btn = tk.Button(admin_code_frame, text="Continue", 
                                     font=FONT_NORMAL, bg=COLOR_PRIMARY_BLUE, 
                                     fg='white', padx=12, pady=3,
                                     command=self._check_admin_code, width=8)
        self.continue_btn.pack(side='left')
        
        # Frame para funciones administrativas (inicialmente oculto)
        self.admin_functions_frame = tk.Frame(admin_inner_frame, bg=COLOR_BG_MAIN)
        
        # Label de estado más compacto
        self.status_label = tk.Label(self.admin_functions_frame, 
                                    text="Access Unlocked - Key 9 Available", 
                                    font=FONT_NORMAL, bg=COLOR_BG_MAIN, 
                                    fg=COLOR_SUCCESS)
        self.status_label.pack(pady=(6, 6))
        
        # Información sobre tecla 9 más compacta
        info_text = ("Key 9 allows changing PSC on physical Smart Cards.")
        
        info_label = tk.Label(self.admin_functions_frame, text=info_text, 
                             font=FONT_NORMAL, bg=COLOR_BG_MAIN, 
                             fg=COLOR_TEXT_PRIMARY, justify='left')
        info_label.pack(pady=(0, 6))
        
        # Frame para el botón Close más compacto
        close_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        close_frame.pack(fill='x', pady=(6, 0))
        
        # Botón Close centrado más pequeño
        self.close_btn = tk.Button(close_frame, text="Close", 
                                  font=FONT_NORMAL, bg=COLOR_DISABLED_GRAY, 
                                  fg='white', padx=20, pady=5, width=10,
                                  command=self._on_close)
        self.close_btn.pack(pady=(0, 0))
    
    def _check_admin_code(self):
        """Verifica el código de administrador"""
        entered_code = self.admin_entry.get().strip()
        
        if entered_code == self.admin_code:
            self.admin_unlocked = True
            self._unlock_admin_functions()
        else:
            messagebox.showerror("Access Denied", 
                               "Invalid admin code. Access denied.")
            self.admin_entry.delete(0, tk.END)
            self.admin_entry.focus_set()
    
    def _unlock_admin_functions(self):
        """Desbloquea las funciones administrativas"""
        # Ocultar elementos de login
        self.admin_entry.configure(state='disabled')
        self.continue_btn.configure(state='disabled', bg=COLOR_DISABLED_GRAY)
        
        # Mostrar funciones administrativas
        self.admin_functions_frame.pack(fill='x')
        
        # Redimensionar la ventana para acomodar el contenido expandido
        self.dialog.after(100, self._resize_for_admin_content)
        
        # Habilitar APDU 9 en la interfaz principal
        self._enable_apdu_9()
        
        # Mensaje de confirmación
        dialog_msg = ("Admin access unlocked!\n\n"
                     "Key 9 is now available.\n"
                     "Press key 9 to change PSC on physical cards.\n\n"
                     "A new button will also appear in the Actions panel.")
        messagebox.showinfo("Access Granted", dialog_msg)
    
    def _resize_for_admin_content(self):
        """Redimensiona la ventana para mostrar todo el contenido administrativo y la vuelve a centrar"""
        # Actualizar el tamaño de la ventana
        self.dialog.update_idletasks()
        
        # Obtener la altura requerida para todo el contenido
        required_height = self.dialog.winfo_reqheight()
        
        # Usar una altura más conservadora cuando admin está activo
        new_height = max(required_height + 50, 650)  # Aumentamos un poco más el margen
        
        # Obtener dimensiones REALES de la ventana padre
        self.parent.update_idletasks()
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Calcular nueva posición centrada con el nuevo tamaño respecto al padre
        new_x = parent_x + (parent_width - 450) // 2
        new_y = parent_y + (parent_height - new_height) // 2
        
        # Ajustar si se sale de los bordes, pero mantener cerca del padre
        new_x = max(parent_x - 100, min(new_x, parent_x + parent_width + 100 - 450))
        new_y = max(parent_y - 50, min(new_y, parent_y + parent_height + 50 - new_height))
        
        # Aplicar la nueva geometría (redimensionar y recentrar)
        self.dialog.geometry(f"450x{new_height}+{new_x}+{new_y}")
        
        # Asegurar que todo el contenido sea visible
        self.dialog.update_idletasks()
    
    def _apply_cards_layout(self):
        """Aplica los cambios de Open Cards Layout"""
        selected_layout = self.cards_layout_var.get()
        layout_text = "2 cards per row" if selected_layout == "2_per_row" else "1 card per row"
        
        # Aplicar cambios de layout de cards en la interfaz principal
        cards_per_row = 2 if selected_layout == "2_per_row" else 1
        self.main_interface.update_cards_layout(cards_per_row)
        
        # Mostrar mensaje de confirmación
        messagebox.showinfo("Open Cards Layout Applied", 
                           f"Open Cards Layout updated successfully!\n\n"
                           f"Layout: {layout_text}")
    
    def _apply_small_screen_mode(self):
        """Aplica los cambios de Small Screen Form Factor"""
        selected_small_screen = self.small_screen_var.get()
        small_screen_text = "Activated" if selected_small_screen == "activate" else "Deactivated"
        
        # Verificar si se está activando Small Screen Form Factor
        if selected_small_screen == "activate":
            # Mostrar diálogo de confirmación
            confirmation = messagebox.askyesno(
                "Confirm Small Screen Mode", 
                "Are you sure you want to activate Small Screen Form Factor?\n\n"
                "This will optimize the interface for smaller displays by:\n"
                "• Reducing element sizes\n"
                "• Compacting layout\n"
                "• Hiding non-essential elements\n\n"
                "You can deactivate it anytime from Settings.",
                icon='question'
            )
            
            if not confirmation:
                # Si el usuario cancela, no aplicar cambios y mantener el diálogo abierto
                return
        
        # Aplicar cambios de small screen form factor (con silent=True para evitar mensajes duplicados)
        small_screen_active = selected_small_screen == "activate"
        success = self.main_interface.update_small_screen_mode(small_screen_active, silent=True)
        
        # Solo mostrar mensaje de éxito si se aplicaron los cambios
        if success:
            messagebox.showinfo("Small Screen Form Factor Applied", 
                               f"Small Screen Form Factor: {small_screen_text}")
            
            # Cerrar el diálogo de settings solo si se activó el Small Screen
            if selected_small_screen == "activate":
                self.dialog.destroy()
        else:
            # Si no se aplicó el cambio (ya estaba en ese estado), mostrar advertencia
            messagebox.showwarning("No Changes Applied", 
                                  f"Small Screen Form Factor is already {small_screen_text.lower()}.")
    
    def _enable_apdu_9(self):
        """Habilita la función APDU 9 en la interfaz principal"""
        # Vincular tecla 9 para APDU 9
        self.main_interface.root.bind('<Key-9>', self._execute_apdu_9)
        self.main_interface.root.bind('<KeyPress-9>', self._execute_apdu_9)
        
        # Marcar como habilitado en la interfaz principal
        self.main_interface.apdu_9_enabled = True
        
        # Crear el botón naranja permanente en la interfaz
        self.main_interface.create_apdu_9_button()
        
        # Log de habilitación
        self.main_interface.log("Key 9 (Change Physical PSC) enabled via Admin Settings", "INFO")
    
    def _execute_apdu_9(self, event=None):
        """Ejecuta APDU 9 - Cambiar PSC en tarjeta física"""
        try:
            # Importar desde physical_card_dialogs
            from ..gui.physical_card_dialogs import PhysicalCardChangePSCDialog
            
            # Cerrar el diálogo de settings si está abierto
            if self.dialog and self.dialog.winfo_exists():
                self.dialog.destroy()
            
            # Mostrar diálogo para cambiar PSC
            dialog = PhysicalCardChangePSCDialog(self.main_interface.root, self.main_interface)
            self.main_interface.log("Change Card PSC - Dialog opened via Key 9")
        except Exception as e:
            self.main_interface.log(f"Error opening Change Card PSC dialog: {e}")
            messagebox.showerror("Error", f"Error opening Change Card PSC dialog:\n{e}")
    
    def _on_close(self):
        """Maneja el cierre del diálogo"""
        if self.dialog:
            self.dialog.destroy()
