"""
Diálogos para operaciones con tarjetas físicas
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from src.utils.constants import *
from src.utils.resource_manager import get_icon_path
from src.core.physical_card_handler import PhysicalCardHandler
from src.core.session_manager import SessionManager

class PhysicalCardReadDialog:
    """Diálogo para leer datos de una tarjeta física"""
    
    def __init__(self, parent, session_manager):
        self.parent = parent
        self.session_manager = session_manager
        self.handler = PhysicalCardHandler()
        self.dialog = None
        self.result = None
        
        # Variables para datos leídos
        self.read_data = None
        self.read_card_type = None
        self.read_psc_bytes = None  # PSC usado para leer la tarjeta
        self.created_session_id = None  # Para almacenar el ID de la sesión creada
        
        # Variables de control
        self.card_type_var = tk.StringVar(value=CARD_TYPE_5542)
        self.status_text = tk.StringVar(value="Ready to read physical card")
        self.progress_var = tk.DoubleVar()
        
        # Variables para PSC
        self.psc_type_var = tk.StringVar(value="factory")  # "factory" o "custom"
        self.custom_psc_var = tk.StringVar(value="")
        
        # Callback para actualizar interfaz cuando cambie el tipo de tarjeta
        self.card_type_var.trace('w', self.on_card_type_change)
        
        # Crear y mostrar el diálogo
        self.create_dialog()
        
    def create_dialog(self):
        """Crear la ventana del diálogo"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Read Physical Card")
        self.dialog.configure(bg=COLOR_BG_MAIN)
        self.dialog.resizable(False, False)
        
        # Configurar icono y modal
        try:
            self.dialog.iconbitmap(get_icon_path("etsisi"))
        except:
            pass
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Frame principal con padding
        main_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN, padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título con icono
        self.create_header(main_frame)

        # Información de lectores
        self.create_reader_info(main_frame)        # Configuración
        self.create_configuration(main_frame)
        
        # Área de progreso
        self.create_progress_area(main_frame)
        
        # Botones
        self.create_buttons(main_frame)
        
        # Actualizar estado inicial
        self.update_status()
        
        # Centrar diálogo
        self.center_dialog()
        
    def create_header(self, parent):
        """Crear cabecera con título e icono"""
        header_frame = tk.Frame(parent, bg=COLOR_BG_MAIN)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Título
        title_label = tk.Label(header_frame, text="Read Physical Smart Card", 
                              font=FONT_HEADER, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        title_label.pack()
        
        # Subtítulo
        subtitle_label = tk.Label(header_frame, text="Import data from a physical smart card to a new virtual card session", 
                                 font=FONT_NORMAL, fg=COLOR_TEXT_DISABLED, bg=COLOR_BG_MAIN)
        subtitle_label.pack(pady=(5, 0))
        
    def create_reader_info(self, parent):
        """Crear sección de información de lectores"""
        reader_frame = tk.LabelFrame(parent, text="Available Card Readers", 
                                   font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        reader_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Lista de lectores con scrollbar
        list_frame = tk.Frame(reader_frame, bg=COLOR_BG_MAIN)
        list_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        self.reader_listbox = tk.Listbox(list_frame, height=3, font=FONT_NORMAL,
                                        bg=COLOR_BG_PANEL, fg=COLOR_TEXT_PRIMARY,
                                        selectbackground=COLOR_PRIMARY_BLUE,
                                        selectforeground="white",
                                        activestyle='none',  # Mantener selección visible cuando no tiene foco
                                        relief=tk.FLAT, bd=1,
                                        exportselection=False)  # Importante: mantener selección al perder foco
        self.reader_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.reader_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.reader_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Botón refresh
        refresh_btn = tk.Button(reader_frame, text="🔄 Refresh Readers", 
                               command=self.refresh_readers,
                               bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_PRIMARY, 
                               font=FONT_NORMAL, relief=tk.FLAT, padx=20)
        refresh_btn.pack(pady=(0, 10))
        
    def create_configuration(self, parent):
        """Crear sección de configuración"""
        config_frame = tk.LabelFrame(parent, text="Card Configuration", 
                                   font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        config_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Frame interno para el tipo de tarjeta
        type_frame = tk.Frame(config_frame, bg=COLOR_BG_MAIN)
        type_frame.pack(pady=10, fill=tk.X)
        
        # Label "Card Type:" en rojo y negrita
        card_type_label = tk.Label(type_frame, text="Card Type:", font=("Arial", 10, "bold"), 
                fg="red", bg=COLOR_BG_MAIN)
        card_type_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Radiobuttons para tipo de tarjeta
        rb_frame = tk.Frame(type_frame, bg=COLOR_BG_MAIN)
        rb_frame.pack(side=tk.LEFT)
        
        tk.Radiobutton(rb_frame, text="SLE5542 (256B)", variable=self.card_type_var, 
                      value=CARD_TYPE_5542, font=("Arial", 10, "bold"), 
                      fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN,
                      selectcolor=COLOR_BG_PANEL, activebackground=COLOR_BG_MAIN).pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Radiobutton(rb_frame, text="SLE5528 (1K)", variable=self.card_type_var, 
                      value=CARD_TYPE_5528, font=("Arial", 10, "bold"), 
                      fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN,
                      selectcolor=COLOR_BG_PANEL, activebackground=COLOR_BG_MAIN).pack(side=tk.LEFT)
        
        # Separator
        separator = tk.Frame(config_frame, height=1, bg=COLOR_BG_PANEL)
        separator.pack(fill=tk.X, padx=10, pady=(5, 10))
        
    def create_progress_area(self, parent):
        """Crear área de progreso"""
        progress_frame = tk.LabelFrame(parent, text="Operation Status", 
                                     font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Etiqueta de estado
        self.status_label = tk.Label(progress_frame, textvariable=self.status_text,
                                    font=FONT_NORMAL, fg=COLOR_TEXT_DISABLED, bg=COLOR_BG_MAIN)
        self.status_label.pack(pady=(10, 5))
        
        # Barra de progreso
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Custom.Horizontal.TProgressbar", 
                       background=COLOR_PRIMARY_BLUE,
                       troughcolor=COLOR_BG_PANEL,
                       borderwidth=0,
                       lightcolor=COLOR_PRIMARY_BLUE,
                       darkcolor=COLOR_PRIMARY_BLUE)
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                          maximum=100, style="Custom.Horizontal.TProgressbar")
        self.progress_bar.pack(fill=tk.X, padx=10, pady=(0, 10))
        
    def create_buttons(self, parent):
        """Crear botones del diálogo"""
        button_frame = tk.Frame(parent, bg=COLOR_BG_MAIN)
        button_frame.pack()
        
        # Botón Default Read (sin PSC)
        self.default_read_btn = tk.Button(button_frame, text="Default Read", 
                                         command=lambda: self.start_read(use_psc=False),
                                         bg=COLOR_BUTTON_PRIMARY, fg=COLOR_TEXT_BUTTON_ENABLED, 
                                         font=FONT_BOLD, width=13, height=1, relief=tk.FLAT,
                                         cursor="hand2")
        self.default_read_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón Custom PSC
        self.custom_psc_btn = tk.Button(button_frame, text="Custom PSC Read", 
                                       command=self.show_custom_psc_dialog,
                                       bg=COLOR_PRIMARY_BLUE, fg=COLOR_TEXT_BUTTON_ENABLED, 
                                       font=FONT_BOLD, width=15, height=1, relief=tk.FLAT,
                                       cursor="hand2")
        self.custom_psc_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón cancelar
        cancel_btn = tk.Button(button_frame, text="Cancel", 
                              command=self.cancel,
                              bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_PRIMARY, 
                              font=FONT_NORMAL, width=10, height=1, relief=tk.FLAT)
        cancel_btn.pack(side=tk.LEFT)
        
        # Bindings de teclado
        self.dialog.bind('<Escape>', lambda e: self.cancel())
        
        # Asegurar que el diálogo tenga foco para las teclas
        self.dialog.after(100, lambda: self.dialog.focus_force())
        
    def center_dialog(self):
        """Centrar el diálogo en la ventana padre"""
        self.dialog.update_idletasks()
        
        # Obtener dimensiones
        dialog_width = self.dialog.winfo_reqwidth()
        dialog_height = self.dialog.winfo_reqheight()
        
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Calcular posición centrada
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    def on_card_type_change(self, *args):
        """Callback cuando cambia el tipo de tarjeta"""
        # Ya no necesitamos actualizar labels de PSC
        pass
    

    
    
    def update_status(self):
        """Actualizar estado de la librería y lectores"""
        # Verificar estado de pyscard
        if self.handler.check_smartcard_library():
            self.refresh_readers()
        else:
            self.default_read_btn.config(state=tk.DISABLED)
            self.custom_psc_btn.config(state=tk.DISABLED)
    
    def refresh_readers(self):
        """Refrescar lista de lectores"""
        try:
            self.reader_listbox.delete(0, tk.END)
            readers = self.handler.get_available_readers()
            
            if readers:
                for reader in readers:
                    self.reader_listbox.insert(tk.END, reader)
                # Asegurar selección automática con un pequeño delay
                self.dialog.after(50, lambda: self.reader_listbox.selection_set(0))
                self.dialog.after(60, lambda: self.reader_listbox.activate(0))
                # Mantener la selección persistente
                self.dialog.after(100, self.ensure_selection_persistent)
                self.status_text.set(f"Found {len(readers)} reader(s)")
            else:
                self.reader_listbox.insert(tk.END, "No card readers found")
                self.default_read_btn.config(state=tk.DISABLED)
                self.custom_psc_btn.config(state=tk.DISABLED)
                self.status_text.set("No card readers detected")
                
        except Exception as e:
            logging.error(f"Error refreshing readers: {e}")
            self.status_text.set("Error detecting readers")
    
    def ensure_selection_persistent(self):
        """Asegurar que la selección se mantenga persistente"""
        try:
            # Solo aplicar si hay elementos en la lista y es un lector válido
            if self.reader_listbox.size() > 0:
                first_item = self.reader_listbox.get(0)
                if not first_item.startswith("No card readers"):  # Es un lector válido
                    # Forzar selección y configurar el listbox para mantenerla
                    self.reader_listbox.selection_set(0)
                    self.reader_listbox.activate(0)
                    self.reader_listbox.see(0)
                    
                    # Bind para evitar que se pierda la selección al hacer clic fuera
                    self.reader_listbox.bind('<FocusOut>', self.on_listbox_focus_out)
                    
        except Exception as e:
            print(f"Error ensuring selection persistent: {e}")
    
    def on_listbox_focus_out(self, event):
        """Mantener selección cuando el listbox pierde el foco"""
        try:
            # Restaurar la selección después de un breve delay
            self.dialog.after(50, lambda: self.restore_selection_if_needed())
        except Exception as e:
            print(f"Error in focus out handler: {e}")
    
    def restore_selection_if_needed(self):
        """Restaurar selección si se ha perdido"""
        try:
            if (self.reader_listbox.size() > 0 and 
                not self.reader_listbox.curselection() and
                not self.reader_listbox.get(0).startswith("No card readers")):
                self.reader_listbox.selection_set(0)
                self.reader_listbox.activate(0)
        except Exception as e:
            print(f"Error restoring selection: {e}")
    
    
    def show_custom_psc_dialog(self):
        """Mostrar diálogo para introducir PSC personalizado"""
        # Crear diálogo modal
        psc_dialog = tk.Toplevel(self.dialog)
        psc_dialog.title("Enter Custom PSC")
        psc_dialog.configure(bg=COLOR_BG_MAIN)
        psc_dialog.resizable(False, False)
        
        # Configurar icono
        try:
            psc_dialog.iconbitmap(get_icon_path("etsisi"))
        except:
            pass
        
        psc_dialog.transient(self.dialog)
        psc_dialog.grab_set()
        
        # Frame principal
        main_frame = tk.Frame(psc_dialog, bg=COLOR_BG_MAIN, padx=30, pady=20)
        main_frame.pack()
        
        # Título
        title_label = tk.Label(main_frame, text="Enter Custom PSC", 
                              font=FONT_HEADER, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        title_label.pack(pady=(0, 15))
        
        # Determinar tipo de tarjeta
        card_type = self.card_type_var.get()
        if isinstance(card_type, str):
            card_type = int(card_type)
        
        # Información
        if card_type == CARD_TYPE_5542:
            info_text = "Enter 3 hex bytes (e.g., FF FF FF)"
            expected_bytes = 3
        else:
            info_text = "Enter 2 hex bytes (e.g., FF FF)"
            expected_bytes = 2
        
        info_label = tk.Label(main_frame, text=info_text, 
                             font=FONT_NORMAL, fg=COLOR_TEXT_DISABLED, bg=COLOR_BG_MAIN)
        info_label.pack(pady=(0, 10))
        
        # Campo de entrada
        psc_var = tk.StringVar()
        psc_entry = tk.Entry(main_frame, textvariable=psc_var, font=FONT_NORMAL, width=25)
        psc_entry.pack(pady=(0, 20))
        psc_entry.focus_set()
        
        # Variable para resultado
        result = [None]
        
        def on_ok():
            psc_str = psc_var.get().strip()
            hex_parts = psc_str.split()
            
            # Validar formato
            if len(hex_parts) != expected_bytes:
                messagebox.showerror("Invalid PSC", 
                                   f"Please enter exactly {expected_bytes} hex bytes separated by spaces.",
                                   parent=psc_dialog)
                return
            
            try:
                psc_bytes = []
                for part in hex_parts:
                    if part:
                        # Eliminar espacios y convertir
                        value = int(part, 16)
                        if value < 0 or value > 255:
                            raise ValueError(f"Byte value out of range: {value}")
                        psc_bytes.append(value)
                
                result[0] = psc_bytes
                psc_dialog.destroy()
                
            except ValueError as e:
                messagebox.showerror("Invalid PSC", 
                                   f"Invalid hex format. Please enter hex bytes (00-FF) separated by spaces.\n\nError: {e}",
                                   parent=psc_dialog)
        
        def on_cancel():
            result[0] = None
            psc_dialog.destroy()
        
        # Botones
        button_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        button_frame.pack()
        
        ok_btn = tk.Button(button_frame, text="OK", command=on_ok,
                          bg=COLOR_BUTTON_PRIMARY, fg=COLOR_TEXT_BUTTON_ENABLED,
                          font=FONT_BOLD, width=10, height=1, relief=tk.FLAT, cursor="hand2")
        ok_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_btn = tk.Button(button_frame, text="Cancel", command=on_cancel,
                              bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_PRIMARY,
                              font=FONT_NORMAL, width=10, height=1, relief=tk.FLAT)
        cancel_btn.pack(side=tk.LEFT)
        
        # Bindings
        psc_dialog.bind('<Return>', lambda e: on_ok())
        psc_dialog.bind('<Escape>', lambda e: on_cancel())
        
        # Centrar diálogo
        psc_dialog.update_idletasks()
        width = psc_dialog.winfo_reqwidth()
        height = psc_dialog.winfo_reqheight()
        x = (psc_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (psc_dialog.winfo_screenheight() // 2) - (height // 2)
        psc_dialog.geometry(f"+{x}+{y}")
        
        # Esperar a que se cierre
        psc_dialog.wait_window()
        
        # Si se introdujo un PSC válido, iniciar lectura
        if result[0] is not None:
            self.start_read(use_psc=True, custom_psc=result[0])
    
    def start_read(self, use_psc=False, custom_psc=None):
        """Iniciar lectura en hilo separado"""
        if not self.reader_listbox.curselection():
            messagebox.showwarning("No Reader Selected", 
                                 "Please select a card reader from the list.")
            return
        
        selected_reader = self.reader_listbox.get(self.reader_listbox.curselection()[0])
        
        if "No card readers found" in selected_reader:
            messagebox.showwarning("No Reader Available", 
                                 "No card readers are available.")
            return
        
        # Deshabilitar botones durante la operación
        self.default_read_btn.config(state=tk.DISABLED)
        self.custom_psc_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.status_text.set("Starting read operation...")
        
        # Iniciar lectura en hilo separado
        thread = threading.Thread(target=self.read_card_thread, 
                                 args=(selected_reader, self.card_type_var.get(), use_psc, custom_psc))
        thread.daemon = True
        thread.start()
    
    def read_card_thread(self, reader_name, card_type, use_psc=False, custom_psc=None):
        """Ejecutar lectura de tarjeta en hilo separado"""
        try:
            # Convertir card_type a entero si es string
            if isinstance(card_type, str):
                card_type = int(card_type)
            
            # Conectar al lector
            self.status_text.set("Connecting to reader...")
            self.progress_var.set(20)
            
            if not self.handler.connect_to_reader(reader_name):
                self.status_text.set("Failed to connect to reader")
                self.default_read_btn.config(state=tk.NORMAL)
                self.custom_psc_btn.config(state=tk.NORMAL)
                return
            
            # Leer tarjeta
            self.status_text.set("Reading card data...")
            self.progress_var.set(50)
            
            # Determinar PSC a usar
            if use_psc and custom_psc:
                # Modo Custom PSC - usar el PSC proporcionado
                psc_bytes = custom_psc
                self.read_psc_bytes = psc_bytes  # Guardar para crear la tarjeta virtual
                print(f"DEBUG: Custom PSC usado para lectura: {[f'{b:02X}' for b in psc_bytes]}")
            else:
                # Modo Default Read - NO presentar PSC (usar None)
                psc_bytes = None
                self.read_psc_bytes = None  # No guardar PSC
                print(f"DEBUG: Default Read - Sin PSC")
            
            data, error_counter = self.handler.read_full_card(card_type, psc_bytes)
            
            if data:
                self.progress_var.set(80)
                self.status_text.set("Card data read successfully!")
                
                # Almacenar los datos leídos para uso posterior
                self.read_data = data
                self.read_card_type = card_type
                
                # SIEMPRE crear una nueva tarjeta con los datos leídos
                # No sobreescribir la sesión actual
                self.progress_var.set(100)
                self.status_text.set("Creating new card from read data...")
                
                # Mostrar diálogo para crear nueva tarjeta después de la lectura exitosa
                self.dialog.after(1000, lambda: self.show_create_card_option(data))
            else:
                # Error en la lectura
                if use_psc and error_counter is not None:
                    # Si se usó Custom PSC y hay Error Counter, mostrarlo
                    self.status_text.set("PSC verification failed")
                    self.dialog.after(500, lambda: self.show_psc_read_error_dialog(error_counter, card_type))
                else:
                    self.status_text.set("Failed to read card data")
                    self.default_read_btn.config(state=tk.NORMAL)
                    self.custom_psc_btn.config(state=tk.NORMAL)
                
        except Exception as e:
            logging.error(f"Error in read operation: {e}")
            self.status_text.set(f"Error: {str(e)}")
            self.default_read_btn.config(state=tk.NORMAL)
            self.custom_psc_btn.config(state=tk.NORMAL)
        finally:
            self.handler.disconnect()
    
    def interpret_error_counter(self, error_counter, card_type):
        """Interpreta el Error Counter según el tipo de tarjeta"""
        if error_counter is None:
            return "Error Counter: N/A", "black"
        
        # Contar bits en 1 para obtener intentos restantes (cada bit = 1 intento)
        def count_bits(value):
            """Cuenta el número de bits en 1 en un byte"""
            count = 0
            while value:
                count += value & 1
                value >>= 1
            return count
        
        remaining_attempts = count_bits(error_counter)
        
        if card_type == CARD_TYPE_5528:  # SLE5528
            if error_counter == 0xFF:
                return "✅ PSC Verification: Successful\n(0xFF = 7 attempts remaining)", "#2E7D32"  # Verde
            elif error_counter == 0x00:
                return "🔒 PSC Status: LOCKED\n(0x00 = 0 attempts - max retries exceeded)", "#C62828"  # Rojo
            else:
                binary = format(error_counter, '08b')
                return f"PSC Verification Failed\nRemaining attempts: {remaining_attempts}\n(0x{error_counter:02X} = {binary})", "#D84315"  # Naranja-Rojo
        else:  # SLE5542
            if error_counter == 0x07:
                return "✅ PSC Verification: Correct\n(0x07 = 3 attempts remaining)", "#2E7D32"  # Verde
            elif error_counter == 0x00:
                return "🔒 PSC Status: LOCKED\n(0x00 = 0 attempts - max retries exceeded)", "#C62828"  # Rojo
            else:
                binary = format(error_counter, '08b')
                return f"PSC Verification Failed\nRemaining attempts: {remaining_attempts}\n(0x{error_counter:02X} = {binary})", "#D84315"  # Naranja-Rojo
    
    def show_psc_read_error_dialog(self, error_counter, card_type):
        """Muestra diálogo de error crítico de PSC durante lectura con Error Counter destacado"""
        # Crear ventana de diálogo personalizada
        error_dialog = tk.Toplevel(self.dialog)
        error_dialog.title("PSC Read Error")
        error_dialog.configure(bg=COLOR_BG_MAIN)
        error_dialog.resizable(False, False)
        
        # Configurar icono
        try:
            error_dialog.iconbitmap(get_icon_path("etsisi"))
        except:
            pass
        
        error_dialog.transient(self.dialog)
        error_dialog.grab_set()
        
        # Frame principal con más ancho
        main_frame = tk.Frame(error_dialog, bg=COLOR_BG_MAIN, padx=40, pady=20)
        main_frame.pack()
        
        # Icono de error crítico
        error_icon_label = tk.Label(main_frame, text="🚨", font=("Segoe UI Emoji", 48), bg=COLOR_BG_MAIN)
        error_icon_label.pack(pady=(0, 10))
        
        # Título en rojo - CENTRADO
        title_label = tk.Label(main_frame, text="PSC READ ERROR", 
                              font=("Segoe UI", 16, "bold"), fg="#C62828", bg=COLOR_BG_MAIN)
        title_label.pack(pady=(0, 15))
        
        # Mensaje de error - CENTRADO con más ancho
        card_type_name = "SLE5528" if card_type == CARD_TYPE_5528 else "SLE5542"
        error_message = f"PSC verification failed during read operation for {card_type_name}."
        error_label = tk.Label(main_frame, text=error_message, font=FONT_NORMAL, 
                              fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN, justify=tk.CENTER, wraplength=500)
        error_label.pack(pady=(0, 10))
        
        # Advertencia adicional - ya estaba centrada
        warning_label = tk.Label(main_frame, 
                                text="⚠️ Please verify the PSC before retrying\nto avoid permanently blocking the card.",
                                font=FONT_NORMAL, fg="#D84315", bg=COLOR_BG_MAIN, justify=tk.CENTER)
        warning_label.pack(pady=(0, 15))
        
        # Separador
        separator = tk.Frame(main_frame, height=2, bg=COLOR_TEXT_DISABLED)
        separator.pack(fill=tk.X, pady=10)
        
        # Error Counter con formato destacado en ROJO y NEGRITA - CENTRADO
        counter_msg, _ = self.interpret_error_counter(error_counter, card_type)
        
        counter_label = tk.Label(main_frame, text=counter_msg, 
                                font=("Segoe UI", 13, "bold"), 
                                fg="#C62828", bg=COLOR_BG_MAIN, justify=tk.CENTER)
        counter_label.pack(pady=(5, 15))
        
        # Botón OK
        ok_btn = tk.Button(main_frame, text="OK", command=lambda: self.close_error_dialog(error_dialog),
                          bg="#C62828", fg="white",
                          font=FONT_BOLD, width=12, height=1, relief=tk.FLAT, cursor="hand2")
        ok_btn.pack()
        
        # Centrar diálogo
        error_dialog.update_idletasks()
        width = error_dialog.winfo_width()
        height = error_dialog.winfo_height()
        x = (error_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (error_dialog.winfo_screenheight() // 2) - (height // 2)
        error_dialog.geometry(f"+{x}+{y}")
    
    def close_error_dialog(self, dialog):
        """Cerrar diálogo de error y rehabilitar botones"""
        dialog.destroy()
        self.default_read_btn.config(state=tk.NORMAL)
        self.custom_psc_btn.config(state=tk.NORMAL)
    
    def analyze_card_data(self, data, card_type):
        """Analizar si la tarjeta tiene datos significativos vs tarjeta limpia de fábrica"""
        if not data:
            return False, "Empty data"
        
        try:
            # Convertir datos a lista de bytes si es necesario
            if isinstance(data, str):
                # Si es string hex, convertir a bytes
                data = bytes.fromhex(data.replace(' ', ''))
            elif isinstance(data, list):
                data = bytes(data)
            
            # Definir SOLO las áreas que deberían estar en FF en una tarjeta limpia
            if card_type == CARD_TYPE_5542:
                # Para SLE5542: Solo el área de datos de usuario (0x20-0xEF) debe ser FF
                # Las primeras dos filas (0x00-0x1F) contienen info de fábrica y son normales
                user_data_start = 0x20  # 32 - Inicio del área de datos de usuario
                user_data_end = 0xEF    # 239 - Final del área de datos de usuario
                # No verificar 0xF0-0xFF porque son áreas de seguridad/protección
            else:  # CARD_TYPE_5528
                # Para SLE5528: Similar, pero área más grande
                # Primeras direcciones tienen info de fábrica, solo verificar área de usuario
                user_data_start = 0x20   # 32
                user_data_end = 0x3F7    # 1015
            
            # Verificar si tenemos suficientes datos
            if len(data) < user_data_end:
                user_data_end = len(data) - 1
            
            # Contar SOLO bytes en el área de datos de usuario que no sean FF
            modified_bytes = 0
            total_checked_bytes = 0
            
            # Verificar SOLO el área de datos de usuario (donde debería haber FF)
            if user_data_start < len(data):
                for addr in range(user_data_start, min(user_data_end + 1, len(data))):
                    total_checked_bytes += 1
                    if data[addr] != 0xFF:
                        modified_bytes += 1
            
            # Calcular porcentaje de bytes modificados
            if total_checked_bytes > 0:
                percentage = (modified_bytes / total_checked_bytes) * 100
            else:
                percentage = 0
            
            # Considerar tarjeta "con datos" si tiene cualquier byte modificado en el área de usuario
            has_data = modified_bytes > 0
            
            analysis = f"Non-FF bytes in user area: {modified_bytes}/{total_checked_bytes} ({percentage:.1f}%)"
            
            return has_data, analysis
            
        except Exception as e:
            return False, f"Error analyzing data: {str(e)}"
    
    def show_create_card_option(self, read_data):
        """Mostrar opción de crear tarjeta con datos leídos"""
        try:
            # Analizar si la tarjeta tiene datos significativos
            card_type = self.determine_card_type(read_data)
            has_data, analysis = self.analyze_card_data(read_data, card_type)
            
            if has_data:
                message = ("Would you like to create a new card with the data read from the physical card?\n\n"
                          f"Warning: This card appears to contain data!\n"
                          f"Analysis: {analysis}\n\n"
                          "The card may have been previously programmed or used.")
                title = "Read Completed - Card Contains Data"
            else:
                message = ("Would you like to create a new card with the data read from the physical card?\n\n"
                          f"Note: This appears to be a factory-clean card.\n"
                          f"Analysis: {analysis}")
                title = "Read Completed - Clean Card"
            
            # Usar diálogo personalizado en lugar de messagebox
            result = self.show_custom_confirmation_dialog(title, message)
            
            if result:
                self.show_create_card_dialog(read_data)
            
        except Exception as e:
            print(f"Error showing create card option: {e}")
            messagebox.showerror("Error", f"Error showing options: {str(e)}", parent=self.dialog)
    
    def show_custom_confirmation_dialog(self, title, message):
        """Mostrar diálogo de confirmación personalizado con estilo de la aplicación"""
        # Crear ventana de diálogo
        confirm_dialog = tk.Toplevel(self.dialog)
        confirm_dialog.title(title)
        confirm_dialog.configure(bg=COLOR_BG_MAIN)
        confirm_dialog.resizable(False, False)
        confirm_dialog.transient(self.dialog)
        confirm_dialog.grab_set()
        
        # Variable para almacenar el resultado
        result = [False]  # Lista para permitir modificación en funciones anidadas
        
        # Frame principal
        main_frame = tk.Frame(confirm_dialog, bg=COLOR_BG_MAIN, padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Icono y título
        header_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Icono
        icon_text = "⚠️" if "Warning" in message else "ℹ️"
        icon_label = tk.Label(header_frame, text=icon_text, font=("Segoe UI Emoji", 24),
                             bg=COLOR_BG_MAIN)
        icon_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # Título
        title_label = tk.Label(header_frame, text=title, font=FONT_HEADER,
                              fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        title_label.pack(side=tk.LEFT)
        
        # Mensaje
        message_label = tk.Label(main_frame, text=message, font=FONT_NORMAL,
                               fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN,
                               justify=tk.LEFT, wraplength=500)
        message_label.pack(pady=(0, 30))
        
        # Frame de botones
        button_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        button_frame.pack(fill=tk.X)
        
        def on_yes():
            result[0] = True
            confirm_dialog.destroy()
        
        def on_no():
            result[0] = False
            confirm_dialog.destroy()
        
        # Botón Yes (azul, estilo principal)
        yes_btn = tk.Button(button_frame, text="Yes", command=on_yes,
                           bg=COLOR_PRIMARY_BLUE, fg=COLOR_TEXT_BUTTON_ENABLED,
                           font=FONT_BOLD, relief=tk.FLAT, padx=30, pady=8,
                           cursor="hand2")
        yes_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Hover effects for Yes button
        def on_yes_enter(e):
            yes_btn.config(bg=COLOR_PRIMARY_BLUE_HOVER)
        def on_yes_leave(e):
            yes_btn.config(bg=COLOR_PRIMARY_BLUE)
        
        yes_btn.bind("<Enter>", on_yes_enter)
        yes_btn.bind("<Leave>", on_yes_leave)
        
        # Botón No (gris, estilo secundario)
        no_btn = tk.Button(button_frame, text="No", command=on_no,
                          bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_PRIMARY,
                          font=FONT_NORMAL, relief=tk.FLAT, padx=30, pady=8,
                          cursor="hand2")
        no_btn.pack(side=tk.RIGHT)
        
        # Centrar diálogo relativo a la ventana padre
        confirm_dialog.update_idletasks()
        width = confirm_dialog.winfo_reqwidth()
        height = confirm_dialog.winfo_reqheight()
        
        parent_x = self.dialog.winfo_rootx()
        parent_y = self.dialog.winfo_rooty()
        parent_width = self.dialog.winfo_width()
        parent_height = self.dialog.winfo_height()
        
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        confirm_dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Configurar tecla Escape para cerrar
        def on_escape(event):
            result[0] = False
            confirm_dialog.destroy()
        
        # Configurar tecla Enter para Yes
        def on_enter(event):
            result[0] = True
            confirm_dialog.destroy()
        
        confirm_dialog.bind("<Escape>", on_escape)
        confirm_dialog.bind("<Return>", on_enter)
        
        # Enfocar botón Yes por defecto
        yes_btn.focus_set()
        
        # Esperar hasta que se cierre el diálogo
        confirm_dialog.wait_window()
        
        return result[0]
    
    def show_create_card_dialog(self, read_data):
        """Mostrar diálogo para crear nueva tarjeta con contenido leído"""
        try:
            from gui.create_card_dialog import CreateCardFromReadDialog
            
            # Cerrar el diálogo actual
            self.dialog.withdraw()
            
            # Crear diálogo personalizado para tarjeta con contenido leído
            # Pasar también el PSC usado para la lectura
            print(f"DEBUG: Pasando PSC al diálogo de creación: {[f'{b:02X}' for b in self.read_psc_bytes] if self.read_psc_bytes else 'None'}")
            dialog = CreateCardFromReadDialog(self.parent, self.session_manager, 
                                            read_data, self.determine_card_type(read_data),
                                            psc_bytes=self.read_psc_bytes)
            result, session_id = dialog.show()
            
            if result:
                # Si se creó la tarjeta exitosamente, almacenar el session_id y cerrar el diálogo principal
                self.created_session_id = session_id
                self.success_close()
            else:
                # Si se canceló, volver a mostrar el diálogo principal
                self.dialog.deiconify()
                
        except Exception as e:
            print(f"Error showing create card dialog: {e}")
            messagebox.showerror("Error", f"Error al crear tarjeta: {str(e)}", parent=self.dialog)
            # Volver a mostrar el diálogo principal si hay error
            self.dialog.deiconify()
    
    def determine_card_type(self, data):
        """Determinar el tipo de tarjeta basado en el tamaño de los datos"""
        if len(data) <= MEMORY_SIZE_5542:
            return CARD_TYPE_5542
        else:
            return CARD_TYPE_5528
    
    def success_close(self):
        """Cerrar diálogo tras éxito"""
        self.result = True
        self.dialog.destroy()
    
    def cancel(self):
        """Cancelar operación"""
        self.result = False
        self.dialog.destroy()
    
    def show(self):
        """Mostrar diálogo y devolver resultado y session_id si se creó una tarjeta"""
        self.dialog.wait_window()
        return self.result, self.created_session_id


class PhysicalCardWriteDialog:
    """Diálogo para escribir datos a una tarjeta física"""
    
    def __init__(self, parent, session_manager):
        self.parent = parent
        self.session_manager = session_manager
        self.handler = PhysicalCardHandler()
        self.dialog = None
        self.result = None
        
        # Variables de control
        self.status_text = tk.StringVar(value="Ready to write to physical card")
        self.progress_var = tk.DoubleVar()
        
        # Variables de PSC
        self.psc_type_var = tk.StringVar(value="factory")
        self.custom_psc_var = tk.StringVar(value="")
        
        # Variables para Error Counter
        self.last_error_counter = None
        self.last_card_type = None
        
        # Crear y mostrar el diálogo
        self.create_dialog()
        
    def create_dialog(self):
        """Crear la ventana del diálogo"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Write Physical Card")
        self.dialog.configure(bg=COLOR_BG_MAIN)
        self.dialog.resizable(False, False)
        
        # Configurar icono y modal
        try:
            self.dialog.iconbitmap(get_icon_path("etsisi"))
        except:
            pass
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Frame principal con padding
        main_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN, padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título con icono
        self.create_header(main_frame)
        
        # 1. Available Card Readers
        self.create_reader_info(main_frame)
        
        # 2. Current Session Data
        self.create_session_info(main_frame)

        # 3. PSC Configuration
        self.create_psc_configuration(main_frame)
        
        # 4. Operation Status
        self.create_progress_area(main_frame)
        
        # Botones
        self.create_buttons(main_frame)
        
        # Actualizar estado inicial
        self.update_status()
        
        # Centrar diálogo
        self.center_dialog()
        
        # Forzar actualización de lectores después de crear la interfaz
        self.dialog.after(100, self.refresh_readers)
        
    def create_header(self, parent):
        """Crear cabecera con título e icono"""
        header_frame = tk.Frame(parent, bg=COLOR_BG_MAIN)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Título
        title_label = tk.Label(header_frame, text="Write Physical Smart Card", 
                              font=FONT_HEADER, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        title_label.pack()
        
        # Subtítulo
        subtitle_label = tk.Label(header_frame, text="Write current session data to a physical card", 
                                 font=FONT_NORMAL, fg=COLOR_TEXT_DISABLED, bg=COLOR_BG_MAIN)
        subtitle_label.pack(pady=(5, 0))
        
    def create_session_info(self, parent):
        """Crear sección de información de la sesión"""
        info_frame = tk.LabelFrame(parent, text="Current Session Data", 
                                 font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.session_info_label = tk.Label(info_frame, font=FONT_NORMAL, 
                                          fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN,
                                          justify=tk.LEFT)
        self.session_info_label.pack(pady=10, anchor=tk.W)
        
    def create_reader_info(self, parent):
        """Crear sección de información de lectores"""
        reader_frame = tk.LabelFrame(parent, text="Available Card Readers", 
                                   font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        reader_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Lista de lectores con scrollbar
        list_frame = tk.Frame(reader_frame, bg=COLOR_BG_MAIN)
        list_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        self.reader_listbox = tk.Listbox(list_frame, height=3, font=FONT_NORMAL,
                                        bg=COLOR_BG_PANEL, fg=COLOR_TEXT_PRIMARY,
                                        selectbackground=COLOR_PRIMARY_BLUE,
                                        selectforeground="white",
                                        activestyle='none',  # Mantener selección visible cuando no tiene foco
                                        relief=tk.FLAT, bd=1,
                                        exportselection=False)  # Importante: mantener selección al perder foco
        self.reader_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.reader_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.reader_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Botón refresh
        refresh_btn = tk.Button(reader_frame, text="🔄 Refresh Readers", 
                               command=self.refresh_readers,
                               bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_PRIMARY, 
                               font=FONT_NORMAL, relief=tk.FLAT, padx=20)
        refresh_btn.pack(pady=(0, 10))
        
    def create_progress_area(self, parent):
        """Crear área de progreso"""
        progress_frame = tk.LabelFrame(parent, text="Operation Status", 
                                     font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Etiqueta de estado
        self.status_label = tk.Label(progress_frame, textvariable=self.status_text,
                                    font=FONT_NORMAL, fg=COLOR_TEXT_DISABLED, bg=COLOR_BG_MAIN)
        self.status_label.pack(pady=(10, 5))
        
        # Barra de progreso
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Custom.Horizontal.TProgressbar", 
                       background=COLOR_PRIMARY_BLUE,
                       troughcolor=COLOR_BG_PANEL,
                       borderwidth=0,
                       lightcolor=COLOR_PRIMARY_BLUE,
                       darkcolor=COLOR_PRIMARY_BLUE)
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                          maximum=100, style="Custom.Horizontal.TProgressbar")
        self.progress_bar.pack(fill=tk.X, padx=10, pady=(0, 10))
        
    def create_buttons(self, parent):
        """Crear botones del diálogo"""
        button_frame = tk.Frame(parent, bg=COLOR_BG_MAIN)
        button_frame.pack()
        
        # Botón escribir
        self.write_btn = tk.Button(button_frame, text="Write Card", 
                                  command=self.start_write,
                                  bg=COLOR_BUTTON_PRIMARY, fg=COLOR_TEXT_BUTTON_ENABLED, 
                                  font=FONT_BOLD, width=12, height=1, relief=tk.FLAT,
                                  cursor="hand2")
        self.write_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón cancelar
        cancel_btn = tk.Button(button_frame, text="Cancel", 
                              command=self.cancel,
                              bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_PRIMARY, 
                              font=FONT_NORMAL, width=10, height=1, relief=tk.FLAT)
        cancel_btn.pack(side=tk.LEFT)
        
        # Bindings de teclado
        self.dialog.bind('<Return>', lambda e: self.start_write())
        self.dialog.bind('<Escape>', lambda e: self.cancel())
        
        # Asegurar que el diálogo tenga foco para las teclas
        self.dialog.after(100, lambda: self.dialog.focus_force())
        
    def center_dialog(self):
        """Centrar el diálogo en la ventana padre"""
        self.dialog.update_idletasks()
        
        # Usar ancho fijo más pequeño para una ventana más compacta
        dialog_width = 480  # Reducido de ancho automático
        dialog_height = self.dialog.winfo_reqheight()
        
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Calcular posición centrada
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    def update_status(self):
        """Actualizar estado de la librería, lectores y sesión"""
        # Verificar sesión activa
        session = self.session_manager.get_active_session()
        if not session:
            self.session_info_label.config(text="❌ No active session available")
            self.write_btn.config(state=tk.DISABLED)
            return
        
        # Mostrar información de la sesión
        card_type = session.memory_manager.card_type
        memory_size = len(session.memory_manager.memory_data)
        
        info_text = f"✅ Card Type: {card_type}\n"
        info_text += f"✅ Memory Size: {memory_size} bytes\n"
        info_text += f"✅ Data ready for writing"
        
        self.session_info_label.config(text=info_text)
        
        # Actualizar labels del Factory PSC según tipo de tarjeta
        self.on_card_type_change()
        
        # Verificar estado de pyscard
        if self.handler.check_smartcard_library():
            self.refresh_readers()
        else:
            self.write_btn.config(state=tk.DISABLED)
    
    def refresh_readers(self):
        """Refrescar lista de lectores"""
        try:
            self.reader_listbox.delete(0, tk.END)
            readers = self.handler.get_available_readers()
            
            if readers:
                for reader in readers:
                    self.reader_listbox.insert(tk.END, reader)
                # Asegurar selección automática con un pequeño delay
                self.dialog.after(50, lambda: self.reader_listbox.selection_set(0))
                self.dialog.after(60, lambda: self.reader_listbox.activate(0))
                # Mantener la selección persistente
                self.dialog.after(100, self.ensure_selection_persistent)
                self.status_text.set(f"Found {len(readers)} reader(s)")
            else:
                self.reader_listbox.insert(tk.END, "No card readers found")
                self.write_btn.config(state=tk.DISABLED)
                self.status_text.set("No card readers detected")
                
        except Exception as e:
            logging.error(f"Error refreshing readers: {e}")
            self.status_text.set("Error detecting readers")
    
    def ensure_selection_persistent(self):
        """Asegurar que la selección se mantenga persistente"""
        try:
            # Solo aplicar si hay elementos en la lista y es un lector válido
            if self.reader_listbox.size() > 0:
                first_item = self.reader_listbox.get(0)
                if not first_item.startswith("No card readers"):  # Es un lector válido
                    # Forzar selección y configurar el listbox para mantenerla
                    self.reader_listbox.selection_set(0)
                    self.reader_listbox.activate(0)
                    self.reader_listbox.see(0)
                    
                    # Bind para evitar que se pierda la selección al hacer clic fuera
                    self.reader_listbox.bind('<FocusOut>', self.on_listbox_focus_out)
                    
        except Exception as e:
            print(f"Error ensuring selection persistent: {e}")
    
    def on_listbox_focus_out(self, event):
        """Mantener selección cuando el listbox pierde el foco"""
        try:
            # Restaurar la selección después de un breve delay
            self.dialog.after(50, lambda: self.restore_selection_if_needed())
        except Exception as e:
            print(f"Error in focus out handler: {e}")
    
    def restore_selection_if_needed(self):
        """Restaurar selección si se ha perdido"""
        try:
            if (self.reader_listbox.size() > 0 and 
                not self.reader_listbox.curselection() and
                not self.reader_listbox.get(0).startswith("No card readers")):
                self.reader_listbox.selection_set(0)
                self.reader_listbox.activate(0)
        except Exception as e:
            print(f"Error restoring selection: {e}")
    
    def start_write(self):
        """Iniciar escritura en hilo separado"""
        if not self.reader_listbox.curselection():
            messagebox.showwarning("No Reader Selected", 
                                 "Please select a card reader from the list.")
            return
        
        selected_reader = self.reader_listbox.get(self.reader_listbox.curselection()[0])
        
        if "No card readers found" in selected_reader:
            messagebox.showwarning("No Reader Available", 
                                 "No card readers are available.")
            return
        
        # Confirmar escritura
        result = messagebox.askyesno("Confirm Write Operation", 
                                   "This will overwrite the data on the physical card.\n\n"
                                   "Are you sure you want to continue?",
                                   icon='warning')
        if not result:
            return
        
        # Deshabilitar botones durante la operación
        self.write_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.status_text.set("Starting write operation...")
        
        # Iniciar escritura en hilo separado
        thread = threading.Thread(target=self.write_card_thread, args=(selected_reader,))
        thread.daemon = True
        thread.start()
    
    def write_card_thread(self, reader_name):
        """Ejecutar escritura de tarjeta en hilo separado"""
        try:
            # Obtener datos de la sesión
            session = self.session_manager.get_active_session()
            if not session:
                self.status_text.set("No active session available")
                self.write_btn.config(state=tk.NORMAL)
                return
            
            memory_manager = session.memory_manager
            card_type = memory_manager.card_type
            
            # Convertir card_type a entero si es string (por si acaso)
            if isinstance(card_type, str):
                card_type = int(card_type)
            
            # Obtener PSC seleccionado por el usuario
            try:
                psc_bytes = self.get_psc_bytes()
            except ValueError as e:
                self.status_text.set(f"PSC Error: {str(e)}")
                self.write_btn.config(state=tk.NORMAL)
                return
            
            # Convertir datos del memory manager a formato bytes
            memory_data_hex = memory_manager.get_memory_dump()
            
            # Conectar al lector
            self.status_text.set("Connecting to reader...")
            self.progress_var.set(20)
            
            if not self.handler.connect_to_reader(reader_name):
                self.status_text.set("Failed to connect to reader")
                self.write_btn.config(state=tk.NORMAL)
                return
            
            # Escribir tarjeta con PSC del usuario
            self.status_text.set("Writing user data area (skipping protected regions)...")
            self.progress_var.set(50)
            
            success, message, error_counter = self.handler.write_full_card(memory_data_hex, card_type, psc_bytes)
            
            # Guardar error_counter para usarlo en los diálogos
            self.last_error_counter = error_counter
            self.last_card_type = card_type
            
            if success:
                self.progress_var.set(100)
                self.status_text.set("Write operation completed successfully")
                
                # Cerrar diálogo y mostrar ventana de éxito con Error Counter
                self.success_close()
            else:
                # Mostrar status básico
                self.status_text.set("Write operation failed")
                
                # Detectar errores específicos y mostrar diálogo de error correspondiente
                if "PSC verification failed" in message:
                    # Error crítico de PSC - mostrar diálogo de error
                    self.dialog.after(500, lambda: self.show_psc_error_dialog(message))
                elif "PSC incorrecto" in message or "PSC" in message:
                    self.dialog.after(500, lambda: self.show_error_dialog("PSC Error", message))
                elif "Tamaño de datos incorrecto" in message:
                    self.dialog.after(500, lambda: self.show_error_dialog("Data Size Error", message))
                elif "Error seleccionando tarjeta" in message:
                    self.dialog.after(500, lambda: self.show_error_dialog("Card Selection Error", message))
                else:
                    self.dialog.after(500, lambda: self.show_error_dialog("Write Failed", message))
                
        except Exception as e:
            logging.error(f"Error in write operation: {e}")
            self.status_text.set(f"Error: {str(e)}")
            self.write_btn.config(state=tk.NORMAL)
        finally:
            self.handler.disconnect()
    
    def success_close(self):
        """Cerrar diálogo tras éxito mostrando confirmación con Error Counter"""
        # Obtener información de la sesión
        session = self.session_manager.get_active_session()
        card_name = session.card_name if session else "Unknown"
        card_type = session.memory_manager.card_type if session else "Unknown"
        card_type_name = "SLE5542" if card_type == CARD_TYPE_5542 else "SLE5528"
        
        # Crear diálogo personalizado con Error Counter destacado
        self.show_success_dialog_with_counter(card_name, card_type_name)
        
        self.result = True
        self.dialog.destroy()
    
    def cancel(self):
        """Cancelar operación"""
        self.result = False
        self.dialog.destroy()
    
    def interpret_error_counter(self, error_counter, card_type):
        """Interpreta el Error Counter según el tipo de tarjeta"""
        if error_counter is None:
            return "Error Counter: N/A", "black"
        
        # Contar bits en 1 para obtener intentos restantes (cada bit = 1 intento)
        def count_bits(value):
            """Cuenta el número de bits en 1 en un byte"""
            count = 0
            while value:
                count += value & 1
                value >>= 1
            return count
        
        remaining_attempts = count_bits(error_counter)
        
        if card_type == CARD_TYPE_5528:  # SLE5528
            if error_counter == 0xFF:
                return "✅ PSC Verification: Successful\n(0x7F = 7 attempts remaining)", "#2E7D32"  # Verde
            elif error_counter == 0x00:
                return "🔒 PSC Status: LOCKED\n(0x00 = 0 attempts - max retries exceeded)", "#C62828"  # Rojo
            else:
                binary = format(error_counter, '08b')
                return f"PSC Verification Failed\nRemaining attempts: {remaining_attempts}\n(0x{error_counter:02X} = {binary})", "#D84315"  # Naranja-Rojo
        else:  # SLE5542
            if error_counter == 0x07:
                return "✅ PSC Verification: Correct\n(0x07 = 3 attempts remaining)", "#2E7D32"  # Verde
            elif error_counter == 0x00:
                return "🔒 PSC Status: LOCKED\n(0x00 = 0 attempts - max retries exceeded)", "#C62828"  # Rojo
            else:
                binary = format(error_counter, '08b')
                return f"PSC Verification Failed\nRemaining attempts: {remaining_attempts}\n(0x{error_counter:02X} = {binary})", "#D84315"  # Naranja-Rojo
    
    def show_success_dialog_with_counter(self, card_name, card_type_name):
        """Muestra diálogo de éxito con Error Counter destacado"""
        # Crear ventana de diálogo personalizada
        success_dialog = tk.Toplevel(self.dialog)
        success_dialog.title("Write Successful")
        success_dialog.configure(bg=COLOR_BG_MAIN)
        success_dialog.resizable(False, False)
        
        # Configurar icono
        try:
            success_dialog.iconbitmap(get_icon_path("etsisi"))
        except:
            pass
        
        success_dialog.transient(self.dialog)
        success_dialog.grab_set()
        
        # Frame principal
        main_frame = tk.Frame(success_dialog, bg=COLOR_BG_MAIN, padx=30, pady=20)
        main_frame.pack()
        
        # Icono de éxito
        success_label = tk.Label(main_frame, text="✅", font=("Segoe UI Emoji", 48), bg=COLOR_BG_MAIN)
        success_label.pack(pady=(0, 10))
        
        # Título
        title_label = tk.Label(main_frame, text="Card Written Successfully!", 
                              font=FONT_HEADER, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        title_label.pack(pady=(0, 15))
        
        # Información de la tarjeta
        info_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        info_frame.pack(pady=(0, 15))
        
        info_text = f"Card Name: {card_name}\nCard Type: {card_type_name}\n\nAll data has been transferred to the physical card."
        info_label = tk.Label(info_frame, text=info_text, font=FONT_NORMAL, 
                             fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN, justify=tk.LEFT)
        info_label.pack()
        
        # Separador
        separator = tk.Frame(main_frame, height=2, bg=COLOR_TEXT_DISABLED)
        separator.pack(fill=tk.X, pady=10)
        
        # Error Counter con formato destacado
        counter_msg, counter_color = self.interpret_error_counter(self.last_error_counter, self.last_card_type)
        
        counter_label = tk.Label(main_frame, text=counter_msg, 
                                font=("Segoe UI", 11, "bold"), 
                                fg=counter_color, bg=COLOR_BG_MAIN, justify=tk.LEFT)
        counter_label.pack(pady=(5, 15))
        
        # Botón OK
        ok_btn = tk.Button(main_frame, text="OK", command=success_dialog.destroy,
                          bg=COLOR_BUTTON_PRIMARY, fg=COLOR_TEXT_BUTTON_ENABLED,
                          font=FONT_BOLD, width=12, height=1, relief=tk.FLAT, cursor="hand2")
        ok_btn.pack()
        
        # Centrar diálogo
        success_dialog.update_idletasks()
        width = success_dialog.winfo_width()
        height = success_dialog.winfo_height()
        x = (success_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (success_dialog.winfo_screenheight() // 2) - (height // 2)
        success_dialog.geometry(f"+{x}+{y}")
        
        # Binding de teclas para cerrar el diálogo (después de centrar y antes de dar foco)
        success_dialog.bind('<Return>', lambda e: success_dialog.destroy())
        success_dialog.bind('<Escape>', lambda e: success_dialog.destroy())
        
        # Dar foco al diálogo para que los bindings funcionen
        success_dialog.focus_force()
        
        # Esperar a que el usuario cierre el diálogo
        success_dialog.wait_window()
    
    def show_error_dialog(self, title, error_message):
        """Muestra diálogo de error con Error Counter destacado"""
        # Crear ventana de diálogo personalizada
        error_dialog = tk.Toplevel(self.dialog)
        error_dialog.title(title)
        error_dialog.configure(bg=COLOR_BG_MAIN)
        error_dialog.resizable(False, False)
        
        # Configurar icono
        try:
            error_dialog.iconbitmap(get_icon_path("etsisi"))
        except:
            pass
        
        error_dialog.transient(self.dialog)
        error_dialog.grab_set()
        
        # Frame principal
        main_frame = tk.Frame(error_dialog, bg=COLOR_BG_MAIN, padx=30, pady=20)
        main_frame.pack()
        
        # Icono de error
        error_icon_label = tk.Label(main_frame, text="❌", font=("Segoe UI Emoji", 48), bg=COLOR_BG_MAIN)
        error_icon_label.pack(pady=(0, 10))
        
        # Título
        title_label = tk.Label(main_frame, text=title, 
                              font=FONT_HEADER, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        title_label.pack(pady=(0, 15))
        
        # Mensaje de error
        error_label = tk.Label(main_frame, text=error_message, font=FONT_NORMAL, 
                              fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN, justify=tk.LEFT, wraplength=400)
        error_label.pack(pady=(0, 15))
        
        # Separador
        separator = tk.Frame(main_frame, height=2, bg=COLOR_TEXT_DISABLED)
        separator.pack(fill=tk.X, pady=10)
        
        # Error Counter con formato destacado en ROJO y NEGRITA
        counter_msg, counter_color = self.interpret_error_counter(self.last_error_counter, self.last_card_type)
        
        # Si hay error, forzar color rojo para destacar
        if self.last_error_counter is not None and self.last_error_counter not in [0x07, 0xFF]:
            counter_color = "#C62828"  # Rojo fuerte
        
        counter_label = tk.Label(main_frame, text=counter_msg, 
                                font=("Segoe UI", 12, "bold"), 
                                fg=counter_color, bg=COLOR_BG_MAIN, justify=tk.LEFT)
        counter_label.pack(pady=(5, 15))
        
        # Botón OK
        ok_btn = tk.Button(main_frame, text="OK", command=error_dialog.destroy,
                          bg=COLOR_BUTTON_PRIMARY, fg=COLOR_TEXT_BUTTON_ENABLED,
                          font=FONT_BOLD, width=12, height=1, relief=tk.FLAT, cursor="hand2")
        ok_btn.pack()
        
        # Centrar diálogo
        error_dialog.update_idletasks()
        width = error_dialog.winfo_width()
        height = error_dialog.winfo_height()
        x = (error_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (error_dialog.winfo_screenheight() // 2) - (height // 2)
        error_dialog.geometry(f"+{x}+{y}")
        
        # Rehabilitar botón después de cerrar el diálogo
        error_dialog.wait_window()
        self.write_btn.config(state=tk.NORMAL)
    
    def show_psc_error_dialog(self, error_message):
        """Muestra diálogo de error crítico de PSC con Error Counter destacado"""
        # Crear ventana de diálogo personalizada
        error_dialog = tk.Toplevel(self.dialog)
        error_dialog.title("CRITICAL PSC Error")
        error_dialog.configure(bg=COLOR_BG_MAIN)
        error_dialog.resizable(False, False)
        
        # Configurar icono
        try:
            error_dialog.iconbitmap(get_icon_path("etsisi"))
        except:
            pass
        
        error_dialog.transient(self.dialog)
        error_dialog.grab_set()
        
        # Frame principal con más ancho
        main_frame = tk.Frame(error_dialog, bg=COLOR_BG_MAIN, padx=40, pady=20)
        main_frame.pack()
        
        # Icono de error crítico
        error_icon_label = tk.Label(main_frame, text="🚨", font=("Segoe UI Emoji", 48), bg=COLOR_BG_MAIN)
        error_icon_label.pack(pady=(0, 10))
        
        # Título en rojo - CENTRADO
        title_label = tk.Label(main_frame, text="CRITICAL PSC ERROR", 
                              font=("Segoe UI", 16, "bold"), fg="#C62828", bg=COLOR_BG_MAIN)
        title_label.pack(pady=(0, 15))
        
        # Mensaje de error - CENTRADO con más ancho
        error_label = tk.Label(main_frame, text=error_message, font=FONT_NORMAL, 
                              fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN, justify=tk.CENTER, wraplength=500)
        error_label.pack(pady=(0, 10))
        
        # Advertencia adicional - ya estaba centrada
        warning_label = tk.Label(main_frame, 
                                text="⚠️ Please check the PSC manually before retrying\nto avoid permanently blocking the card.",
                                font=FONT_NORMAL, fg="#D84315", bg=COLOR_BG_MAIN, justify=tk.CENTER)
        warning_label.pack(pady=(0, 15))
        
        # Separador
        separator = tk.Frame(main_frame, height=2, bg=COLOR_TEXT_DISABLED)
        separator.pack(fill=tk.X, pady=10)
        
        # Error Counter con formato destacado en ROJO y NEGRITA - CENTRADO
        counter_msg, _ = self.interpret_error_counter(self.last_error_counter, self.last_card_type)
        
        counter_label = tk.Label(main_frame, text=counter_msg, 
                                font=("Segoe UI", 13, "bold"), 
                                fg="#C62828", bg=COLOR_BG_MAIN, justify=tk.CENTER)
        counter_label.pack(pady=(5, 15))
        
        # Botón OK
        ok_btn = tk.Button(main_frame, text="OK", command=lambda: [error_dialog.destroy(), self.cancel()],
                          bg="#C62828", fg="white",
                          font=FONT_BOLD, width=12, height=1, relief=tk.FLAT, cursor="hand2")
        ok_btn.pack()
        
        # Centrar diálogo
        error_dialog.update_idletasks()
        width = error_dialog.winfo_width()
        height = error_dialog.winfo_height()
        x = (error_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (error_dialog.winfo_screenheight() // 2) - (height // 2)
        error_dialog.geometry(f"+{x}+{y}")
    
    def show(self):
        """Mostrar diálogo y devolver resultado"""
        self.dialog.wait_window()
        return self.result
    
    def create_psc_configuration(self, parent):
        """Crear sección de configuración PSC"""
        config_frame = tk.LabelFrame(parent, text="PSC Configuration", 
                                   font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        config_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Frame para PSC
        psc_frame = tk.Frame(config_frame, bg=COLOR_BG_MAIN)
        psc_frame.pack(pady=10, fill=tk.X)

        # Frame para radiobuttons de PSC
        psc_rb_frame = tk.Frame(psc_frame, bg=COLOR_BG_MAIN)
        psc_rb_frame.pack(fill=tk.X, pady=(5, 0))        # Factory PSC
        factory_frame = tk.Frame(psc_rb_frame, bg=COLOR_BG_MAIN)
        factory_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.factory_rb = tk.Radiobutton(factory_frame, text="Factory PSC", 
                                        variable=self.psc_type_var, value="factory",
                                        font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN,
                                        selectcolor=COLOR_BG_PANEL, activebackground=COLOR_BG_MAIN,
                                        command=self.on_psc_type_change)
        self.factory_rb.pack(side=tk.LEFT)
        
        self.factory_value_label = tk.Label(factory_frame, text="(FF FF FF)", 
                                           font=FONT_SMALL, fg=COLOR_TEXT_DISABLED, bg=COLOR_BG_MAIN)
        self.factory_value_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Custom PSC
        custom_frame = tk.Frame(psc_rb_frame, bg=COLOR_BG_MAIN)
        custom_frame.pack(fill=tk.X)
        
        self.custom_rb = tk.Radiobutton(custom_frame, text="Custom PSC", 
                                       variable=self.psc_type_var, value="custom",
                                       font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN,
                                       selectcolor=COLOR_BG_PANEL, activebackground=COLOR_BG_MAIN,
                                       command=self.on_psc_type_change)
        self.custom_rb.pack(side=tk.LEFT)
        
        self.custom_psc_entry = tk.Entry(custom_frame, textvariable=self.custom_psc_var,
                                        font=FONT_NORMAL, width=20, state='disabled')
        self.custom_psc_entry.pack(side=tk.LEFT, padx=(10, 5))
        
        self.custom_help_label = tk.Label(custom_frame, text="(hex bytes, e.g., FF FF FF)", 
                             font=FONT_SMALL, fg=COLOR_TEXT_DISABLED, bg=COLOR_BG_MAIN)
        self.custom_help_label.pack(side=tk.LEFT)
    
    def on_psc_type_change(self):
        """Manejar cambio de tipo de PSC"""
        if self.psc_type_var.get() == "factory":
            self.custom_psc_entry.config(state='disabled')
        else:
            self.custom_psc_entry.config(state='normal')
    
    def on_card_type_change(self):
        """Actualizar valores factory según tipo de tarjeta"""
        session = self.session_manager.get_active_session()
        if session:
            card_type = session.memory_manager.card_type
            # Convertir card_type a entero si es string
            if isinstance(card_type, str):
                card_type = int(card_type)
            
            if card_type == CARD_TYPE_5542:
                self.factory_value_label.config(text="(FF FF FF)")
                self.custom_help_label.config(text="(hex bytes, e.g., FF FF FF)")
            else:  # SLE5528
                self.factory_value_label.config(text="(FF FF)")
                self.custom_help_label.config(text="(hex bytes, e.g., FF FF)")
    
    def get_psc_bytes(self):
        """Obtener bytes del PSC seleccionado"""
        if self.psc_type_var.get() == "factory":
            # Obtener tipo de tarjeta de la sesión
            session = self.session_manager.get_active_session()
            if session:
                card_type = session.memory_manager.card_type
                # Convertir card_type a entero si es string
                if isinstance(card_type, str):
                    card_type = int(card_type)
                
                if card_type == CARD_TYPE_5542:
                    return [0xFF, 0xFF, 0xFF]
                else:  # SLE5528
                    return [0xFF, 0xFF]
            else:
                return [0xFF, 0xFF, 0xFF]  # Por defecto
        else:
            # PSC personalizado
            session = self.session_manager.get_active_session()
            card_type = CARD_TYPE_5542  # Por defecto
            if session:
                card_type = session.memory_manager.card_type
                # Convertir card_type a entero si es string
                if isinstance(card_type, str):
                    card_type = int(card_type)
            
            expected_length = 3 if card_type == CARD_TYPE_5542 else 2
            
            psc_str = self.custom_psc_var.get().strip()
            hex_parts = psc_str.split()
            
            psc_bytes = []
            for part in hex_parts:
                if part:
                    try:
                        byte_val = int(part, 16)
                        if 0 <= byte_val <= 255:
                            psc_bytes.append(byte_val)
                        else:
                            raise ValueError(f"Byte value out of range: {part}")
                    except ValueError:
                        raise ValueError(f"Invalid hex byte: {part}")
            
            if len(psc_bytes) != expected_length:
                raise ValueError(f"PSC must be {expected_length} bytes for {card_type}")
            
            return psc_bytes


class PhysicalCardChangePSCDialog:
    """Diálogo para cambiar PSC en una tarjeta física"""
    
    def __init__(self, parent, main_interface):
        self.parent = parent
        self.main_interface = main_interface
        self.handler = PhysicalCardHandler()
        self.dialog = None
        
        # Variables de control
        self.card_type_var = tk.StringVar(value=str(CARD_TYPE_5542))
        self.status_text = tk.StringVar(value="Ready to change PSC on physical card")
        
        # Variables para PSCs
        self.current_psc_var = tk.StringVar(value="")
        self.new_psc_var = tk.StringVar(value="")
        
        # Callback para actualizar interfaz cuando cambie el tipo de tarjeta
        self.card_type_var.trace('w', self.on_card_type_change)
        
        # Crear y mostrar el diálogo
        self.create_dialog()
        
    def create_dialog(self):
        """Crear la ventana del diálogo"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Change Card PSC")
        self.dialog.configure(bg=COLOR_BG_MAIN)
        self.dialog.resizable(False, False)
        
        # Configurar icono
        try:
            self.dialog.iconbitmap(get_icon_path("etsisi"))
        except:
            pass
            
        # Hacer modal respecto a la ventana principal - IGUAL QUE APDUs
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Manejar tecla Escape y Enter
        self.dialog.bind('<Escape>', lambda e: self.close_dialog())
        self.dialog.bind('<Return>', lambda e: self.execute_change_psc())
        
        # Frame principal con padding
        main_frame = tk.Frame(self.dialog, bg=COLOR_BG_MAIN, padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título con icono
        self.create_header(main_frame)
        
        # Información de lectores
        self.create_reader_info(main_frame)
        
        # Configuración del tipo de tarjeta
        self.create_card_type_selection(main_frame)
        
        # Configuración de PSCs
        self.create_psc_configuration(main_frame)
        
        # Área de progreso
        self.create_progress_area(main_frame)
        
        # Botones
        self.create_buttons(main_frame)
        
        # Actualizar estado inicial
        self.update_status()
        
        # Centrar usando EXACTAMENTE el mismo método que APDUs
        self._center_like_apdus()
        
        # Forzar actualización de lectores
        self.dialog.after(100, self.refresh_readers)
        
        # Dar foco
        self.dialog.after(100, lambda: self.dialog.focus_force())
    
    def _center_like_apdus(self):
        """Centrar usando exactamente el mismo método que el diálogo de APDUs"""
        # Centrar respecto a la ventana principal (funciona en múltiples pantallas)
        self.parent.update_idletasks()
        self.dialog.update_idletasks()
        
        # Obtener posición y tamaño de la ventana principal
        main_x = self.parent.winfo_rootx()
        main_y = self.parent.winfo_rooty()
        main_width = self.parent.winfo_width()
        main_height = self.parent.winfo_height()
        
        # Obtener tamaño del diálogo
        dialog_width = self.dialog.winfo_reqwidth()
        dialog_height = self.dialog.winfo_reqheight()
        
        # Calcular posición centrada respecto a la ventana principal
        pos_x = main_x + (main_width - dialog_width) // 2
        pos_y = main_y + (main_height - dialog_height) // 2
        
        # Aplicar geometría
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{pos_x}+{pos_y}")
        
        print(f"DEBUG: Parent at ({main_x}, {main_y}) size {main_width}x{main_height}")
        print(f"DEBUG: Dialog size {dialog_width}x{dialog_height} positioned at ({pos_x}, {pos_y})")
        
    def create_header(self, parent):
        """Crear cabecera con título e icono"""
        header_frame = tk.Frame(parent, bg=COLOR_BG_MAIN)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Título
        title_label = tk.Label(header_frame, text="Change Physical Card PSC", 
                              font=FONT_HEADER, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        title_label.pack()
        
        # Subtítulo
        subtitle_label = tk.Label(header_frame, text="Change the PSC of a physical smart card", 
                                 font=FONT_NORMAL, fg=COLOR_TEXT_DISABLED, bg=COLOR_BG_MAIN)
        subtitle_label.pack(pady=(5, 0))
        
    def create_reader_info(self, parent):
        """Crear sección de información de lectores"""
        reader_frame = tk.LabelFrame(parent, text="Available Card Readers", 
                                   font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        reader_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Lista de lectores con scrollbar
        list_frame = tk.Frame(reader_frame, bg=COLOR_BG_MAIN)
        list_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        self.reader_listbox = tk.Listbox(list_frame, height=3, font=FONT_NORMAL,
                                        bg=COLOR_BG_PANEL, fg=COLOR_TEXT_PRIMARY,
                                        selectbackground=COLOR_PRIMARY_BLUE,
                                        selectforeground="white",
                                        activestyle='none',  # Mantener selección visible cuando no tiene foco
                                        relief=tk.FLAT, bd=1,
                                        exportselection=False)  # Importante: mantener selección al perder foco
        self.reader_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.reader_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.reader_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Botón refresh
        refresh_btn = tk.Button(reader_frame, text="🔄 Refresh Readers", 
                               command=self.refresh_readers,
                               bg=COLOR_BUTTON_SECONDARY, fg=COLOR_TEXT_PRIMARY, 
                               font=FONT_NORMAL, relief=tk.FLAT, padx=20)
        refresh_btn.pack(pady=(0, 10))
    
    def refresh_readers(self):
        """Actualizar lista de lectores"""
        try:
            # Limpiar lista
            self.reader_listbox.delete(0, tk.END)
            
            # Obtener lectores disponibles
            readers = self.handler.get_available_readers()
            
            if readers:
                for reader in readers:
                    self.reader_listbox.insert(tk.END, reader)
                # Asegurar selección automática con un pequeño delay
                self.dialog.after(50, lambda: self.reader_listbox.selection_set(0))
                self.dialog.after(60, lambda: self.reader_listbox.activate(0))
                # Mantener la selección persistente
                self.dialog.after(100, self.ensure_selection_persistent)
            else:
                self.reader_listbox.insert(tk.END, "⚠ No card readers detected")
                
        except Exception as e:
            self.reader_listbox.delete(0, tk.END)
            self.reader_listbox.insert(tk.END, f"⚠ Error: {str(e)}")
    
    def ensure_selection_persistent(self):
        """Asegurar que la selección se mantenga persistente"""
        try:
            # Solo aplicar si hay elementos en la lista y es un lector válido
            if self.reader_listbox.size() > 0:
                first_item = self.reader_listbox.get(0)
                if not first_item.startswith("⚠"):  # Es un lector válido
                    # Forzar selección y configurar el listbox para mantenerla
                    self.reader_listbox.selection_set(0)
                    self.reader_listbox.activate(0)
                    self.reader_listbox.see(0)
                    
                    # Bind para evitar que se pierda la selección al hacer clic fuera
                    self.reader_listbox.bind('<FocusOut>', self.on_listbox_focus_out)
                    
        except Exception as e:
            print(f"Error ensuring selection persistent: {e}")
    
    def on_listbox_focus_out(self, event):
        """Mantener selección cuando el listbox pierde el foco"""
        try:
            # Restaurar la selección después de un breve delay
            self.dialog.after(50, lambda: self.restore_selection_if_needed())
        except Exception as e:
            print(f"Error in focus out handler: {e}")
    
    def restore_selection_if_needed(self):
        """Restaurar selección si se ha perdido"""
        try:
            if (self.reader_listbox.size() > 0 and 
                not self.reader_listbox.curselection() and
                not self.reader_listbox.get(0).startswith("⚠")):
                self.reader_listbox.selection_set(0)
                self.reader_listbox.activate(0)
        except Exception as e:
            print(f"Error restoring selection: {e}")
    
    def create_card_type_selection(self, parent):
        """Crear sección de selección de tipo de tarjeta"""
        config_frame = tk.LabelFrame(parent, text="Card Configuration", 
                                   font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        config_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Frame interno para el tipo de tarjeta
        type_frame = tk.Frame(config_frame, bg=COLOR_BG_MAIN)
        type_frame.pack(pady=10, fill=tk.X)
        
        # Label "Card Type:" en rojo y negrita
        card_type_label = tk.Label(type_frame, text="Card Type:", font=("Arial", 10, "bold"), 
                fg="red", bg=COLOR_BG_MAIN)
        card_type_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Radiobuttons para tipo de tarjeta
        rb_frame = tk.Frame(type_frame, bg=COLOR_BG_MAIN)
        rb_frame.pack(side=tk.LEFT)
        
        tk.Radiobutton(rb_frame, text="SLE5542 (256B)", variable=self.card_type_var, 
                      value=str(CARD_TYPE_5542), font=("Arial", 10, "bold"), 
                      fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN,
                      selectcolor=COLOR_BG_PANEL, activebackground=COLOR_BG_MAIN).pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Radiobutton(rb_frame, text="SLE5528 (1K)", variable=self.card_type_var, 
                      value=str(CARD_TYPE_5528), font=("Arial", 10, "bold"), 
                      fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN,
                      selectcolor=COLOR_BG_PANEL, activebackground=COLOR_BG_MAIN).pack(side=tk.LEFT)
    
    def create_psc_configuration(self, parent):
        """Crear sección de configuración de PSCs"""
        psc_frame = tk.LabelFrame(parent, text="PSC Configuration", 
                                font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        psc_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Frame interno
        inner_frame = tk.Frame(psc_frame, bg=COLOR_BG_MAIN, padx=10, pady=10)
        inner_frame.pack(fill=tk.X)
        
        # Obtener longitud de PSC según tipo de tarjeta
        card_type = int(self.card_type_var.get())
        if card_type == CARD_TYPE_5542:
            psc_length_text = "3 bytes"
            placeholder_current = "FF FF FF"
            placeholder_new = "12 34 56"
        else:
            psc_length_text = "2 bytes"
            placeholder_current = "FF FF"
            placeholder_new = "12 34"
        
        # Campo PSC actual
        current_label = tk.Label(inner_frame, text=f"Current PSC:", 
                               font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        current_label.pack(anchor='w', pady=(0, 5))
        
        current_entry_frame = tk.Frame(inner_frame, bg=COLOR_BG_MAIN)
        current_entry_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.current_psc_entry = tk.Entry(current_entry_frame, textvariable=self.current_psc_var,
                                         font=FONT_NORMAL, width=20, bg='white', fg='black')
        self.current_psc_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        self.current_help_label = tk.Label(current_entry_frame, text=f"(hex bytes, e.g., {placeholder_current})", 
                                    font=FONT_SMALL, fg=COLOR_TEXT_DISABLED, bg=COLOR_BG_MAIN)
        self.current_help_label.pack(side=tk.LEFT)
        
        # Campo nuevo PSC
        new_label = tk.Label(inner_frame, text=f"New PSC:", 
                           font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        new_label.pack(anchor='w', pady=(0, 5))
        
        new_entry_frame = tk.Frame(inner_frame, bg=COLOR_BG_MAIN)
        new_entry_frame.pack(fill=tk.X)
        
        self.new_psc_entry = tk.Entry(new_entry_frame, textvariable=self.new_psc_var,
                                     font=FONT_NORMAL, width=20, bg='white', fg='black')
        self.new_psc_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        self.new_help_label = tk.Label(new_entry_frame, text=f"(hex bytes, e.g., {placeholder_new})", 
                                font=FONT_SMALL, fg=COLOR_TEXT_DISABLED, bg=COLOR_BG_MAIN)
        self.new_help_label.pack(side=tk.LEFT)
        
        # Inicializar placeholders
        self.current_psc_entry.insert(0, placeholder_current)
        self.new_psc_entry.insert(0, placeholder_new)
    
    def create_progress_area(self, parent):
        """Crear área de progreso"""
        progress_frame = tk.LabelFrame(parent, text="Operation Status", 
                                     font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Frame interno
        inner_frame = tk.Frame(progress_frame, bg=COLOR_BG_MAIN, padx=10, pady=10)
        inner_frame.pack(fill=tk.X)
        
        # Status text
        self.status_label = tk.Label(inner_frame, textvariable=self.status_text,
                                   font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        self.status_label.pack(anchor='w')
    
    def create_buttons(self, parent):
        """Crear botones de acción"""
        button_frame = tk.Frame(parent, bg=COLOR_BG_MAIN)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Botón Cancel
        cancel_btn = tk.Button(button_frame, text="Cancel", font=FONT_BOLD,
                              bg=COLOR_DISABLED_GRAY, fg='white', padx=20, pady=8,
                              command=self.close_dialog, width=12)
        cancel_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Botón Change PSC
        self.change_btn = tk.Button(button_frame, text="CHANGE PSC", font=FONT_BOLD,
                                   bg=COLOR_PRIMARY_BLUE, fg='white', padx=20, pady=8,
                                   command=self.execute_change_psc, width=12)
        self.change_btn.pack(side=tk.RIGHT)
    
    def on_card_type_change(self, *args):
        """Callback cuando cambia el tipo de tarjeta"""
        self.update_psc_placeholders()
        self.update_status()
    
    def update_psc_placeholders(self):
        """Actualizar placeholders según el tipo de tarjeta"""
        card_type = int(self.card_type_var.get())
        
        if card_type == CARD_TYPE_5542:
            placeholder_current = "FF FF FF"
            placeholder_new = "12 34 56"
        else:
            placeholder_current = "FF FF"
            placeholder_new = "12 34"
        
        # Actualizar placeholders si están vacíos o contienen el placeholder anterior
        if hasattr(self, 'current_psc_entry'):
            current_value = self.current_psc_entry.get().strip()
            if not current_value or current_value in ["FF FF FF", "FF FF"]:
                self.current_psc_entry.delete(0, tk.END)
                self.current_psc_entry.insert(0, placeholder_current)
        
        if hasattr(self, 'new_psc_entry'):
            new_value = self.new_psc_entry.get().strip()
            if not new_value or new_value in ["12 34 56", "12 34"]:
                self.new_psc_entry.delete(0, tk.END)
                self.new_psc_entry.insert(0, placeholder_new)
        
        # Actualizar los labels de ayuda con los placeholders correctos
        if hasattr(self, 'current_help_label'):
            self.current_help_label.config(text=f"(hex bytes, e.g., {placeholder_current})")
        
        if hasattr(self, 'new_help_label'):
            self.new_help_label.config(text=f"(hex bytes, e.g., {placeholder_new})")
    
    def update_status(self):
        """Actualizar estado del diálogo"""
        card_type = int(self.card_type_var.get())
        card_name = "SLE5542" if card_type == CARD_TYPE_5542 else "SLE5528"
        self.status_text.set(f"Ready to change PSC on {card_name} card")
    
    def validate_psc_inputs(self):
        """Validar las entradas de PSC"""
        from src.core.code_improvements import is_valid_hex_string
        
        current_psc = self.current_psc_var.get().strip().replace(' ', '')
        new_psc = self.new_psc_var.get().strip().replace(' ', '')
        card_type = int(self.card_type_var.get())
        
        # Determinar longitud esperada
        expected_length = 3 if card_type == CARD_TYPE_5542 else 2
        length_name = "3" if card_type == CARD_TYPE_5542 else "2"
        
        # Validar PSC actual
        if not is_valid_hex_string(current_psc, allow_spaces=False) or len(current_psc) != expected_length * 2:
            messagebox.showerror("Invalid Input", 
                               f"Current PSC must be exactly {length_name} hex bytes ({expected_length*2} characters)")
            self.current_psc_entry.focus_set()
            return False
        
        # Validar nuevo PSC
        if not is_valid_hex_string(new_psc, allow_spaces=False) or len(new_psc) != expected_length * 2:
            messagebox.showerror("Invalid Input", 
                               f"New PSC must be exactly {length_name} hex bytes ({expected_length*2} characters)")
            self.new_psc_entry.focus_set()
            return False
        
        # Verificar que son diferentes
        if current_psc.upper() == new_psc.upper():
            messagebox.showerror("Invalid Input", 
                               "New PSC must be different from current PSC")
            self.new_psc_entry.focus_set()
            return False
        
        return True
    
    def format_psc_for_display(self, psc_hex):
        """Formatear PSC para mostrar con espacios entre bytes"""
        # Remover espacios existentes
        psc_clean = psc_hex.replace(' ', '')
        # Añadir espacios cada 2 caracteres
        return ' '.join(psc_clean[i:i+2] for i in range(0, len(psc_clean), 2))
    
    def execute_change_psc(self):
        """Ejecutar cambio de PSC"""
        if not self.validate_psc_inputs():
            return
        
        current_psc = self.current_psc_var.get().strip().replace(' ', '')
        new_psc = self.new_psc_var.get().strip().replace(' ', '')
        card_type = int(self.card_type_var.get())
        card_name = "SLE5542" if card_type == CARD_TYPE_5542 else "SLE5528"
        
        # Formatear PSCs para mostrar
        current_psc_display = self.format_psc_for_display(current_psc)
        new_psc_display = self.format_psc_for_display(new_psc)
        
        # Confirmación final
        confirm_msg = (f"Change PSC on Physical {card_name} Card?\n\n"
                      f"Current PSC: {current_psc_display}\n"
                      f"New PSC: {new_psc_display}")
        
        if not messagebox.askyesno("Confirm PSC Change", confirm_msg):
            return
        
        # Ejecutar en hilo separado para no bloquear la UI
        threading.Thread(target=self._perform_psc_change, 
                        args=(current_psc, new_psc, card_type, card_name), 
                        daemon=True).start()
    
    def _perform_psc_change(self, current_psc, new_psc, card_type, card_name):
        """Realizar el cambio de PSC en hilo separado"""
        try:
            # Actualizar UI
            self.change_btn.configure(state='disabled')
            self.status_text.set("Connecting to card reader...")
            
            # 0. CONECTAR AL LECTOR
            # Verificar que hay un lector seleccionado
            if not self.reader_listbox.curselection():
                raise Exception("No card reader selected")
            
            selected_reader = self.reader_listbox.get(self.reader_listbox.curselection()[0])
            if "No card readers found" in selected_reader:
                raise Exception("No valid card reader available")
            
            # Conectar al lector seleccionado
            self.status_text.set(f"Step 0/4: Connecting to {selected_reader}...")
            if not self.handler.connect_to_reader(selected_reader):
                raise Exception(f"Failed to connect to reader: {selected_reader}")
            
            # 1. SELECT CARD TYPE
            self.status_text.set(f"Step 1/4: Selecting {card_name} card...")
            
            success, message = self.handler.select_card(card_type)
            if not success:
                raise Exception(f"SELECT CARD failed: {message}")
            
            # 2. PRESENT CURRENT PSC
            self.status_text.set("Step 2/4: Presenting current PSC...")
            
            # Convertir PSC a lista de bytes
            current_psc_bytes = [int(current_psc[i:i+2], 16) for i in range(0, len(current_psc), 2)]
            success, message, error_counter = self.handler.present_psc(card_type, current_psc_bytes)
            if not success:
                raise Exception(f"PRESENT PSC failed: {message}")
            
            # 3. CHANGE PSC
            self.status_text.set("Step 3/4: Changing to new PSC...")
            
            # Convertir nuevo PSC a lista de bytes
            new_psc_bytes = [int(new_psc[i:i+2], 16) for i in range(0, len(new_psc), 2)]
            success, message = self.handler.change_psc(card_type, new_psc_bytes)
            if not success:
                raise Exception(f"CHANGE PSC failed: {message}")
            
            # 4. DESCONECTAR
            self.status_text.set("Step 4/4: Disconnecting...")
            self.handler.disconnect()
            
            # Éxito
            self.status_text.set("PSC changed successfully!")
            
            # Log en la interfaz principal
            current_psc_display = self.format_psc_for_display(current_psc)
            new_psc_display = self.format_psc_for_display(new_psc)
            self.main_interface.log(f"PSC changed successfully on {card_name} card: {current_psc_display} → {new_psc_display}", "SUCCESS")
            
            # Mostrar mensaje de éxito en un diálogo propio con botón Cerrar
            def show_success_dialog():
                current_psc_display = self.format_psc_for_display(current_psc)
                new_psc_display = self.format_psc_for_display(new_psc)

                dialog = tk.Toplevel(self.dialog)
                dialog.title("PSC Change Successful")
                dialog.configure(bg=COLOR_BG_MAIN)
                dialog.resizable(False, False)
                dialog.transient(self.dialog)
                dialog.grab_set()

                # Cerrar con Escape o la X
                def close():
                    dialog.destroy()
                    self.close_dialog()
                dialog.protocol("WM_DELETE_WINDOW", close)
                dialog.bind('<Escape>', lambda e: close())

                # Frame principal
                main_frame = tk.Frame(dialog, bg=COLOR_BG_MAIN, padx=30, pady=20)
                main_frame.pack(fill=tk.BOTH, expand=True)

                # Icono y título
                icon_label = tk.Label(main_frame, text="✅", font=("Segoe UI Emoji", 32), bg=COLOR_BG_MAIN)
                icon_label.pack(pady=(0, 10))
                title_label = tk.Label(main_frame, text="PSC changed successfully!", font=FONT_HEADER, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
                title_label.pack(pady=(0, 10))

                # Mensaje
                msg = f"Card Type: {card_name}\nOld PSC: {current_psc_display}\nNew PSC: {new_psc_display}"
                msg_label = tk.Label(main_frame, text=msg, font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN, justify=tk.LEFT)
                msg_label.pack(pady=(0, 20))

                # Botón Cerrar
                close_btn = tk.Button(main_frame, text="Cerrar", command=close, bg=COLOR_PRIMARY_BLUE, fg="white", font=FONT_BOLD, padx=30, pady=8, relief=tk.FLAT, cursor="hand2")
                close_btn.pack()
                close_btn.focus_set()

                # Centrar el diálogo relativo a la ventana padre
                dialog.update_idletasks()
                width = dialog.winfo_reqwidth()
                height = dialog.winfo_reqheight()
                
                parent_x = self.dialog.winfo_rootx()
                parent_y = self.dialog.winfo_rooty()
                parent_width = self.dialog.winfo_width()
                parent_height = self.dialog.winfo_height()
                
                x = parent_x + (parent_width - width) // 2
                y = parent_y + (parent_height - height) // 2
                dialog.geometry(f"{width}x{height}+{x}+{y}")

            self.parent.after(0, show_success_dialog)
            
        except Exception as e:
            error_message = str(e)
            self.status_text.set(f"Error: {error_message}")
            
            # Log del error
            self.main_interface.log(f"PSC change failed: {error_message}", "ERROR")
            
            # Mostrar error
            self.parent.after(0, lambda: messagebox.showerror("PSC Change Failed", 
                                                             f"Failed to change PSC: {error_message}"))
        finally:
            # Reactivar botón
            self.parent.after(0, lambda: self.change_btn.configure(state='normal'))
    
    def close_dialog(self):
        """Cerrar el diálogo"""
        if self.dialog:
            self.dialog.destroy()
