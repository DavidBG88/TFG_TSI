"""
Interfaz principal de CardSIM con diseño moderno basado en la imagen de referencia
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog, simpledialog
import sys
import os
import base64

# Agregar el directorio src al path para imports relativos
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from src.utils.resource_manager import get_icon_path

from src.utils.constants import *
from src.utils.app_states import AppStates, ButtonStates, CardStates
from src.core.session_manager import SessionManager
from src.core.code_improvements import CommonMessages
from .dialogs import (ReadMemoryDialog, WriteMemoryDialog, ChangePSCDialog, 
                        WriteProtectDialog, UserConfigDialog, NewCardDialog,
                        ProtectionBitsDialog, PresentPSCDialog, ConfirmationDialog,
                        InfoDialog, ClearLogDialog, OpenCardDialog, SaveCardDialog,
                        SaveLogDialog)
from .card_explorer import CardExplorer
from .physical_card_dialogs import PhysicalCardReadDialog, PhysicalCardWriteDialog

class CardSimInterface:
    """Interfaz gráfica principal de CardSIM"""
    
    def _set_window_icon(self, window):
        """Configura el icono de ETSISI para una ventana"""
        try:
            # Usar resource manager para obtener la ruta del icono
            icon_path = get_icon_path("etsisi.jpg")
            
            if os.path.exists(icon_path):
                from PIL import Image, ImageTk
                
                # Cargar y redimensionar la imagen para icono (32x32)
                image = Image.open(icon_path)
                # Redimensionar manteniendo proporción y centrando en 32x32
                image = image.resize((32, 32), Image.Resampling.LANCZOS)
                
                # Convertir a PhotoImage para Tkinter
                photo = ImageTk.PhotoImage(image)
                
                # Configurar como icono de la ventana
                window.iconphoto(True, photo)
                
                # Guardar referencia para evitar garbage collection
                if not hasattr(self, '_window_icons'):
                    self._window_icons = []
                self._window_icons.append(photo)
                
        except Exception as e:
            # Si hay algún error, usar el icono por defecto
            print(f"Warning: Could not set ETSISI icon - {e}")
    
    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        
        # Configurar icono de ETSISI para la ventana principal
        self._set_window_icon(self.root)
        
        # Ocultar ventana inicialmente para evitar parpadeo
        self.root.withdraw()
        
        # Configurar ventana 
        self.root.geometry("1400x900")
        self.root.configure(bg=COLOR_BG_MAIN)
        self.root.resizable(True, True)
        
        # Maximizar la ventana
        self.root.state('zoomed')
        
        # Configurar geometría
        self.root.update_idletasks()
        
        # Manager principal
        self.session_manager = SessionManager()
        
        # Variables de interfaz
        self.card_status_var = tk.StringVar(value=STATUS_NO_CARD_INSERTED)
        self.card_type_var = tk.StringVar(value="5528")
        self.page_var = tk.StringVar(value="P0")
        self.current_page = 0
        
        # Variable para controlar acceso administrativo
        self.apdu_9_enabled = False
        self.button_refs = {}
        self.number_label_refs = {}  # Para los números de APDU
        
        # Variables para campos inferiores
        self.user_id_var = tk.StringVar(value="User")
        self.psc_var = tk.StringVar(value="FF FF FF")
        self.error_counter_var = tk.StringVar(value="3")
        
        # Estado actual de la aplicación
        self.current_app_state = AppStates.INITIAL
        self.current_card_state = CardStates.FACTORY
        
        # Configuración actual del layout
        self.current_cards_per_row = 2  # Valor por defecto: 2 tarjetas por fila
        self.small_screen_mode = False  # Flag para modo Small Screen Form Factor
        
        self.setup_ui()
        self.update_button_states()
        self.setup_keyboard_shortcuts()  # Configurar atajos de teclado
        
        # Configurar protocolo de cierre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def safe_messagebox(self, box_type, title, message, **kwargs):
        """Muestra un messagebox de forma segura, manejando errores de cierre de aplicación"""
        try:
            # Verificar que la ventana principal aún existe
            if hasattr(self, 'root') and self.root and self.root.winfo_exists():
                if box_type == "info":
                    return messagebox.showinfo(title, message, **kwargs)
                elif box_type == "error":
                    return messagebox.showerror(title, message, **kwargs)
                elif box_type == "warning":
                    return messagebox.showwarning(title, message, **kwargs)
                elif box_type == "question":
                    return messagebox.askyesno(title, message, **kwargs)
            else:
                print(f"Application closing - Message: {title}: {message}")
        except (tk.TclError, AttributeError, KeyboardInterrupt) as e:
            # Manejar errores específicos de Tkinter cuando se cierra la aplicación
            print(f"Dialog error (application closing): {e}")
            return None
        except Exception as e:
            # Manejar cualquier otro error inesperado
            print(f"Unexpected dialog error: {e}")
            return None
        
        self.update_card_display()
        self.update_button_states()  # Estado inicial
        self.update_page_buttons()   # Estado inicial de botones de página
        self.update_cards_list()    # Lista inicial vacía
        
        # Log inicial
        self.log("CardSIM initialized - Ready to create or open cards")
        
        # Mostrar ventana una vez esté completamente configurada
        self.root.deiconify()
    
    def update_app_state(self, new_state):
        """Actualiza el estado de la aplicación y botones"""
        self.current_app_state = new_state
        self.update_button_states()
        self.log(f"App state changed to: {new_state}")
    
    def update_button_states(self):
        """Actualiza el estado de todos los botones según el estado actual con estilos visuales"""
        button_states = ButtonStates.get_all_button_states(self.current_app_state)
        
        self._update_button_visual('new_card', button_states.get('new_card', False))
        self._update_button_visual('open_card', button_states.get('open_card', False))
        self._update_button_visual('save_card', button_states.get('save_card', False))
        self._update_button_visual('clear_card', button_states.get('clear_card', False))
        self._update_button_visual('close_card', button_states.get('close_card', False))
        self._update_button_visual('user_info', button_states.get('user_config', False))
        
        self._update_button_visual('apdu_1', button_states.get('select_card', False))
        self._update_button_visual('apdu_2', button_states.get('read_memory', False))
        self._update_button_visual('apdu_3', button_states.get('present_psc', False))
        self._update_button_visual('apdu_6', button_states.get('read_error_counter', False))
        self._update_button_visual('apdu_7', button_states.get('read_protection_bits', False))
        self._update_button_visual('apdu_4', button_states.get('write_memory', False))
        self._update_button_visual('apdu_5', button_states.get('change_psc', False))
        self._update_button_visual('apdu_8', button_states.get('write_protect', False))
        
        # Actualizar botón Reset Error Counter
        self._update_button_visual('reset_error_counter', True)  # Siempre habilitado
        
        # Actualizar colores de números para tarjetas de 1KB
        self._update_number_colors()
    
    def _update_number_colors(self):
        """Actualiza los colores de los números APDU para tarjetas de 1KB"""
        active_session = self.session_manager.get_active_session()
        if not active_session:
            return
            
        # Si es tarjeta de 1KB, cambiar el color del número 5 (CHANGE PSC)
        if active_session.card_type == CARD_TYPE_5528:
            if 'num_5' in self.number_label_refs:
                num_label = self.number_label_refs['num_5']
                num_label.configure(bg=COLOR_APDU_SPECIAL, fg=COLOR_TEXT_PRIMARY)
        else:
            # Restaurar color normal para tarjetas de 256B
            if 'num_5' in self.number_label_refs:
                num_label = self.number_label_refs['num_5']
                num_label.configure(bg=COLOR_PRIMARY_BLUE, fg=COLOR_TEXT_BUTTON_ENABLED)
    
    def _update_button_visual(self, button_name, enabled):
        """Actualiza el estilo visual de un botón según su estado"""
        if button_name not in self.button_refs:
            return
            
        button = self.button_refs[button_name]
        
        if enabled:
            # Verificar si es el botón CHANGE PSC en tarjeta de 1KB (comportamiento especial)
            if button_name == 'apdu_5':  # CHANGE PSC
                active_session = self.session_manager.get_active_session()
                if active_session and active_session.card_type == CARD_TYPE_5528:
                    # Color naranja con texto negro para tarjetas de 1KB
                    button.configure(
                        state=tk.NORMAL,
                        bg=COLOR_APDU_SPECIAL,
                        fg=COLOR_TEXT_PRIMARY,  # Texto negro
                        relief=tk.RAISED,
                        cursor='hand2'
                    )
                    # Efecto hover
                    button.bind('<Enter>', lambda e: button.configure(bg='#FFB366'))
                    button.bind('<Leave>', lambda e: button.configure(bg=COLOR_APDU_SPECIAL))
                    return
            
            # Botón habilitado (comportamiento normal)
            button.configure(
                state=tk.NORMAL,
                bg=COLOR_PRIMARY_BLUE,
                fg=COLOR_TEXT_BUTTON_ENABLED,
                relief=tk.RAISED,
                cursor='hand2'
            )
            # Agregar efecto hover
            button.bind('<Enter>', lambda e: button.configure(bg=COLOR_PRIMARY_BLUE_HOVER))
            button.bind('<Leave>', lambda e: button.configure(bg=COLOR_PRIMARY_BLUE))
        else:
            # Botón deshabilitado
            button.configure(
                state=tk.DISABLED,
                bg=COLOR_DISABLED_GRAY,
                fg=COLOR_TEXT_BUTTON_DISABLED,
                relief=tk.FLAT,
                cursor='arrow'
            )
            # Remover efectos hover
            button.unbind('<Enter>')
            button.unbind('<Leave>')
    
    def setup_ui(self):
        """Configura toda la interfaz de usuario con diseño de 4 columnas"""
        # Configuración de grid principal - 4 COLUMNAS
        self.root.grid_rowconfigure(0, weight=0, minsize=550)     # Fila superior
        self.root.grid_rowconfigure(1, weight=1, minsize=150)     # Panel inferior
        
        # 4 COLUMNAS - Configuración corregida
        self.root.grid_columnconfigure(0, weight=0, minsize=250)  # Col 1: Commands
        self.root.grid_columnconfigure(1, weight=0, minsize=400)  # Col 2: Cards + Info
        self.root.grid_columnconfigure(2, weight=1, minsize=400)  # Col 3: Memory
        self.root.grid_columnconfigure(3, weight=0, minsize=80)   # Col 4: Pages
        
        # Crear los 4 paneles de columnas
        self.create_commands_panel()      # Columna 1: Commands
        self.create_cards_panel()         # Columna 2: Open Cards + Card Info
        self.create_memory_panel()        # Columna 3: Memory Content
        self.create_pages_panel()         # Columna 4: Page buttons
        self.create_bottom_panel()        # Panel inferior: Command Log
        
        # Inicializar display con mensajes informativos
        self.update_card_display()
    
    def create_commands_panel(self):
        """Columna 1: Panel de comandos principales"""
        commands_frame = tk.Frame(self.root, bg=COLOR_BG_PANEL, relief=tk.RAISED, bd=1)
        commands_frame.grid(row=0, column=0, sticky='nsew', padx=(5, 2), pady=3)
        commands_frame.grid_propagate(False)
        commands_frame.configure(width=250)
        
        # Configurar grid interno
        commands_frame.grid_rowconfigure(0, weight=0)
        commands_frame.grid_rowconfigure(1, weight=5)
        commands_frame.grid_rowconfigure(2, weight=2, minsize=120)
        commands_frame.grid_columnconfigure(0, weight=1)
        
        # COMMANDS Section
        cmd_section = tk.LabelFrame(commands_frame, text="Commands", font=FONT_SECTION_TITLE,
                                   bg=COLOR_BG_PANEL, fg=COLOR_TEXT_PRIMARY, 
                                   relief=tk.GROOVE, bd=2)
        cmd_section.grid(row=0, column=0, sticky='ew', padx=8, pady=(8, 2))
        
        # Grid de comandos 2x3
        commands_grid = tk.Frame(cmd_section, bg=COLOR_BG_PANEL)
        commands_grid.pack(fill=tk.X, padx=6, pady=4)
        
        # Fila 1
        self.button_refs['new_card'] = tk.Button(commands_grid, text="NEW CARD",
                                               command=self.new_card_dialog,
                                               bg=COLOR_PRIMARY_BLUE, fg=COLOR_TEXT_BUTTON_ENABLED, 
                                               font=FONT_BOLD, relief=tk.RAISED,
                                               width=10, height=1, cursor='hand2', bd=0)
        self.button_refs['new_card'].grid(row=0, column=0, padx=2, pady=2, sticky='ew')
        
        self.button_refs['clear_card'] = tk.Button(commands_grid, text="CLEAR CARD",
                                                 command=self.clear_card,
                                                 bg=COLOR_WARNING, fg=COLOR_TEXT_BUTTON_ENABLED, 
                                                 font=FONT_BOLD, relief=tk.RAISED,
                                                 width=10, height=1, cursor='hand2', bd=0)
        self.button_refs['clear_card'].grid(row=0, column=1, padx=2, pady=2, sticky='ew')
        
        # Fila 2  
        self.button_refs['open_card'] = tk.Button(commands_grid, text="OPEN CARD",
                                                command=self.open_card_dialog,
                                                bg=COLOR_PRIMARY_BLUE, fg=COLOR_TEXT_BUTTON_ENABLED, 
                                                font=FONT_BOLD, relief=tk.RAISED,
                                                width=10, height=1, cursor='hand2', bd=0)
        self.button_refs['open_card'].grid(row=1, column=0, padx=2, pady=2, sticky='ew')
        
        self.button_refs['save_card'] = tk.Button(commands_grid, text="SAVE CARD",
                                                command=self.save_card_dialog,
                                                bg=COLOR_PRIMARY_BLUE, fg=COLOR_TEXT_BUTTON_ENABLED, 
                                                font=FONT_BOLD, relief=tk.RAISED,
                                                width=10, height=1, cursor='hand2', bd=0)
        self.button_refs['save_card'].grid(row=1, column=1, padx=2, pady=2, sticky='ew')
        
        # Fila 3
        self.button_refs['close_card'] = tk.Button(commands_grid, text="CLOSE CARD",
                                                 command=self.close_card,
                                                 bg=COLOR_PRIMARY_BLUE, fg=COLOR_TEXT_BUTTON_ENABLED, 
                                                 font=FONT_BOLD, relief=tk.RAISED,
                                                 width=10, height=1, cursor='hand2', bd=0)
        self.button_refs['close_card'].grid(row=2, column=0, padx=2, pady=2, sticky='ew')
        
        self.button_refs['user_info'] = tk.Button(commands_grid, text="USER CONF",
                                                command=self.user_config_dialog,
                                                bg=COLOR_PRIMARY_BLUE, fg=COLOR_TEXT_BUTTON_ENABLED, 
                                                font=FONT_BOLD, relief=tk.RAISED,
                                                width=10, height=1, cursor='hand2', bd=0)
        self.button_refs['user_info'].grid(row=2, column=1, padx=2, pady=2, sticky='ew')
        
        # Configurar columnas para que se expandan
        commands_grid.grid_columnconfigure(0, weight=1)
        commands_grid.grid_columnconfigure(1, weight=1)
        
        # APDU Commands Section)
        apdus_frame = tk.LabelFrame(commands_frame, text="APDU Commands", font=FONT_SECTION_TITLE,
                                   bg=COLOR_BG_PANEL, fg=COLOR_TEXT_PRIMARY,
                                   relief=tk.GROOVE, bd=2)
        apdus_frame.grid(row=1, column=0, sticky='nsew', padx=8, pady=2)
        
        # Lista de APDUs numerados
        apdu_commands = [
            ("1", "SELECT CARD", self.select_card_apdu),
            ("2", "READ MEMORY", self.read_memory_dialog),
            ("3", "PRESENT PSC", self.present_psc),
            ("4", "WRITE MEMORY", self.write_memory_dialog),
            ("5", "CHANGE PSC", self.change_psc_dialog),
            ("6", "READ ERROR COUNTER", self.read_error_counter),
            ("7", "READ PROTECTION BITS", self.read_protection_bits),
            ("8", "WRITE PROTECT", self.write_protect_dialog)
        ]
        
        for i, (num, text, command) in enumerate(apdu_commands):
            btn_frame = tk.Frame(apdus_frame, bg=COLOR_BG_PANEL)
            btn_frame.pack(fill=tk.X, padx=4, pady=0.5)
            
            # Número con estilo
            num_label = tk.Label(btn_frame, text=num, bg=COLOR_PRIMARY_BLUE, fg=COLOR_TEXT_BUTTON_ENABLED,
                                font=FONT_BOLD, width=2, relief=tk.RAISED, bd=1)
            num_label.pack(side=tk.LEFT, padx=(0, 4))
            
            # Guardar referencia al número
            self.number_label_refs[f'num_{num}'] = num_label
            
            # Botón comando
            self.button_refs[f'apdu_{i+1}'] = tk.Button(btn_frame, text=text,
                                                      command=command,
                                                      bg=COLOR_PRIMARY_BLUE, fg=COLOR_TEXT_BUTTON_ENABLED,
                                                      font=FONT_SMALL, relief=tk.RAISED,
                                                      height=1, cursor='hand2', bd=0)
            self.button_refs[f'apdu_{i+1}'].pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # === CARD INFORMATION Section ===
        card_info_frame = tk.LabelFrame(commands_frame, text="Card Information", 
                                       font=FONT_SECTION_TITLE, bg=COLOR_BG_PANEL, 
                                       fg=COLOR_TEXT_PRIMARY, relief=tk.GROOVE, bd=2)
        card_info_frame.grid(row=2, column=0, sticky='nsew', padx=8, pady=(2, 8))
        card_info_frame.grid_rowconfigure(0, weight=1)
        card_info_frame.grid_columnconfigure(0, weight=1)
        
        # Guardar referencia para el modo small screen
        self.card_info_frame = card_info_frame
        
        # Text area para información de la tarjeta
        self.card_info_text = tk.Text(card_info_frame, font=FONT_SMALL,
                                     bg=COLOR_BG_PANEL, fg=COLOR_TEXT_PRIMARY,
                                     relief=tk.SUNKEN, bd=1, selectbackground="#FFD54F",  # Color amarillo claro para selección
                                     selectforeground="#000000",  # Texto negro al seleccionar
                                     wrap=tk.WORD, state=tk.NORMAL, height=5)
        self.card_info_text.grid(row=0, column=0, sticky='nsew', padx=4, pady=4)

    def create_cards_panel(self):
        """Columna 2: Panel de tarjetas abiertas y información"""
        cards_frame = tk.Frame(self.root, bg=COLOR_BG_PANEL, relief=tk.RAISED, bd=1)
        cards_frame.grid(row=0, column=1, sticky='nsew', padx=2, pady=3)
        cards_frame.grid_propagate(False)
        cards_frame.configure(width=400)  # Ancho correcto para 2 tarjetas por fila (default)
        
        # Configurar grid interno
        cards_frame.grid_rowconfigure(0, weight=1)
        cards_frame.grid_columnconfigure(0, weight=1)
        
        # OPEN CARDS Section
        self.open_cards_frame = tk.LabelFrame(cards_frame, text="Open Cards", font=FONT_SECTION_TITLE,
                                        bg=COLOR_BG_PANEL, fg=COLOR_TEXT_PRIMARY,
                                        relief=tk.GROOVE, bd=2)
        self.open_cards_frame.grid(row=0, column=0, sticky='nsew', padx=8, pady=(8, 4))
        self.open_cards_frame.grid_rowconfigure(0, weight=1)
        self.open_cards_frame.grid_columnconfigure(0, weight=1)
        
        # Frame para la lista de tarjetas
        list_frame = tk.Frame(self.open_cards_frame, bg=COLOR_BG_PANEL)
        list_frame.grid(row=0, column=0, sticky='nsew', padx=6, pady=6)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # CardExplorer reemplaza al Listbox
        self.card_explorer = CardExplorer(list_frame, self.on_card_select_from_explorer, self.open_cards_frame)
        
        # CARD INFORMATION SECTION se crea en create_memory_panel
    
    def update_interface_for_active_session(self):
        """Actualiza toda la interfaz basada en la sesión activa"""
        active_session = self.session_manager.get_active_session()
        
        if active_session:
            # Actualizar estado de la aplicación
            self.current_app_state = active_session.get_current_app_state()
            
            # Sincronizar página actual con la sesión (especialmente para SLE5528)
            if active_session.card_selected and active_session.card_type == CARD_TYPE_5528:
                # Asegurar que la página actual esté sincronizada con el memory_manager
                self.current_page = active_session.memory_manager.current_page
                self.page_var.set(f"P{self.current_page}")
            elif active_session.card_type == CARD_TYPE_5542:
                # Para SLE5542, siempre página 0
                self.current_page = 0
                self.page_var.set("P0")
            
            # Actualizar botones
            self.update_button_states()
            
            # Actualizar botones de página según tipo de tarjeta
            self.update_page_buttons()
            
            # Actualizar display de memoria
            self.update_card_display()
            
            # Actualizar log
            self.update_command_log_display()
            
            # Actualizar información de la tarjeta
            self.update_card_info_display()
        else:
            # No hay tarjetas abiertas
            self.current_app_state = AppStates.INITIAL
            self.update_button_states()
            self.update_page_buttons()
            self.clear_memory_display()
            self.clear_command_log_display()
    
    def clear_memory_display(self):
        """Limpia completamente el display de memoria y card info"""
        # Habilitar temporalmente todos los widgets para editarlos
        if hasattr(self, 'address_text'):
            self.address_text.config(state=tk.NORMAL)
        if hasattr(self, 'memory_text'):
            self.memory_text.config(state=tk.NORMAL)
        if hasattr(self, 'ascii_text'):
            self.ascii_text.config(state=tk.NORMAL)
        if hasattr(self, 'card_info_text'):
            self.card_info_text.config(state=tk.NORMAL)
        
        # Limpiar direcciones
        if hasattr(self, 'address_text'):
            self.address_text.delete(1.0, tk.END)
            # Configurar centrado
            self.address_text.tag_configure("center", justify='center')
            no_card_text = "ROW\\COL\n------\nNo card"
            self.address_text.insert(1.0, no_card_text, "center")
        
        # Limpiar memoria principal (HEX CONTENT)
        if hasattr(self, 'memory_text'):
            self.memory_text.delete(1.0, tk.END)
            self.memory_text.tag_configure("center", justify='center')
            self.memory_text.insert(1.0, "No card selected\n\nCreate a NEW CARD or OPEN an existing\ncard to view memory content.", "center")
        
        # Limpiar área ASCII
        if hasattr(self, 'ascii_text'):
            self.ascii_text.delete(1.0, tk.END)
            self.ascii_text.tag_configure("center", justify='center')
            self.ascii_text.insert(1.0, "No ASCII data available\n\nMemory content will appear here\nwhen a card is selected.", "center")
        
        # Limpiar información de la tarjeta
        if hasattr(self, 'card_info_text'):
            self.card_info_text.delete(1.0, tk.END)
            self.card_info_text.tag_configure("left", justify='left')
            self.card_info_text.insert(1.0, "No card information\n\nSelect or create a card to view details.", "left")
        
        # Deshabilitar edición de todos los widgets
        if hasattr(self, 'address_text'):
            self.address_text.config(state=tk.DISABLED)
        if hasattr(self, 'memory_text'):
            self.memory_text.config(state=tk.DISABLED)
        if hasattr(self, 'ascii_text'):
            self.ascii_text.config(state=tk.DISABLED)
        if hasattr(self, 'card_info_text'):
            self.card_info_text.config(state=tk.DISABLED)
        
        # Limpiar también los paneles de información inferiores
        if hasattr(self, 'psc_label'):
            self.psc_label.config(text="-- -- --", fg=COLOR_TEXT_PRIMARY)
        if hasattr(self, 'errors_label'):
            self.errors_label.config(text="--", fg=COLOR_TEXT_PRIMARY)
    
    def clear_command_log_display(self):
        """Limpia el display del command log"""
        if hasattr(self, 'log_text'):
            # Temporalmente habilitar escritura para limpiar
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            # Volver a deshabilitar escritura
            self.log_text.config(state=tk.DISABLED)
    
    def update_command_log_display(self):
        """Actualiza el display del command log con el log de la sesión activa con formato profesional"""
        if not hasattr(self, 'log_text'):
            return
            
        active_session = self.session_manager.get_active_session()
        
        # Temporalmente habilitar escritura para actualizar
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        
        # Configurar tags de formato profesional si no existen
        self._setup_log_text_tags()
        
        if active_session:
            # Procesar cada entrada del log individualmente para aplicar estilos
            for entry in active_session.command_log:
                self._insert_formatted_log_entry(entry, active_session)
            
            # Scroll al final
            self.log_text.see(tk.END)
        
        # Volver a deshabilitar escritura
        self.log_text.config(state=tk.DISABLED)
    
    def _setup_log_text_tags(self):
        """Configura los tags de formato para el text widget del log"""
        self.log_text.tag_configure("timestamp", foreground="#000000", font=("Consolas", 10, "bold"))
        self.log_text.tag_configure("cmd_icon", foreground="#000000", font=("Segoe UI Emoji", 12))
        self.log_text.tag_configure("cmd_text", foreground="#0066CC", font=("Consolas", 11, "bold"))
        self.log_text.tag_configure("apdu_icon", foreground="#040303", font=("Segoe UI Emoji", 12))
        self.log_text.tag_configure("apdu_text", foreground="#8E24AA", font=("Consolas", 11, "bold"))
        self.log_text.tag_configure("apdu_data", foreground="#7B1FA2", font=("Consolas", 11, "bold"))
        self.log_text.tag_configure("data_icon", foreground="#000000", font=("Segoe UI Emoji", 12))
        self.log_text.tag_configure("data_text", foreground="#000000", font=("Consolas", 11, "bold"))
        self.log_text.tag_configure("success_icon", foreground="#000000", font=("Segoe UI Emoji", 12))
        self.log_text.tag_configure("success_text", foreground="#2E7D32", font=("Consolas", 11, "bold"))
        self.log_text.tag_configure("warning_icon", foreground="#000000", font=("Segoe UI Emoji", 12))
        self.log_text.tag_configure("warning_text", foreground="#F57C00", font=("Consolas", 11, "bold"))
        self.log_text.tag_configure("info_icon", foreground="#000000", font=("Segoe UI Emoji", 12))
        self.log_text.tag_configure("info_text", foreground="#424242", font=("Consolas", 11, "bold"))
        self.log_text.tag_configure("error_icon", foreground="#000000", font=("Segoe UI Emoji", 12))
        self.log_text.tag_configure("error_text", foreground="#D32F2F", font=("Consolas", 11, "bold"))
        self.log_text.tag_configure("address", foreground="#000000", font=("Consolas", 11))
        self.log_text.tag_configure("hex_data", foreground="#388E3C", font=("Consolas", 11, "bold"))
        self.log_text.tag_configure("response_text", foreground="#000000", font=("Consolas", 11))
        self.log_text.tag_configure("ascii_text", foreground="#1565C0", font=("Consolas", 11, "bold"))  # Color azul para ASCII
        
        # Tags para separadores estructurados
        self.log_text.tag_configure("separator", foreground="#666666", font=("Consolas", 10, "bold"))
        self.log_text.tag_configure("error_separator", foreground="#D32F2F", font=("Consolas", 10, "bold"))
    
    def _insert_formatted_log_entry(self, entry, active_session=None):
        """Inserta una entrada de log con formato estructurado usando separadores"""
        timestamp = entry['timestamp']
        log_type = entry['type']
        message = entry['message']
        
        if log_type == "APDU_SEND":
            # Separador inicial más corto
            self.log_text.insert(tk.END, "──────────────────────── APDU COMMAND ────────────────────────\n", "separator")
            
            # Información opcional del comando si hay mensaje
            if message and message.strip():
                self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                self.log_text.insert(tk.END, "ℹ️ ", "info_icon")
                self.log_text.insert(tk.END, "INFO: ", "info_text")
                self.log_text.insert(tk.END, f"{message}\n", "info_text")
            
            # Contenido APDU principal
            if 'apdu' in entry:
                self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                self.log_text.insert(tk.END, "📋 ", "cmd_icon")
                self.log_text.insert(tk.END, "APDU: ", "cmd_text")
                self.log_text.insert(tk.END, f"{entry['apdu']}\n", "apdu_data")
                
            if 'data' in entry and message != "PRESENT PSC":
                # Datos con dirección (pero no para Present PSC)
                self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                self.log_text.insert(tk.END, "📄 ", "data_icon")
                self.log_text.insert(tk.END, f"{entry['address']:04X}", "address")
                self.log_text.insert(tk.END, ": ", "data_text")
                self.log_text.insert(tk.END, f"{entry['data']}\n", "hex_data")
                
        elif log_type == "DATA_DISPLAY":
            # Tipo especial para mostrar solo datos sin separadores adicionales
            if 'address' in entry and 'data' in entry:
                self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                self.log_text.insert(tk.END, "📄 ", "data_icon")
                self.log_text.insert(tk.END, f"{entry['address']:04X}", "address")
                self.log_text.insert(tk.END, ": ", "data_text")
                self.log_text.insert(tk.END, f"{entry['data']}\n", "hex_data")
                
        elif log_type == "APDU_RESPONSE":
            if 'sw' in entry:
                # Información opcional de la respuesta
                self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                sw_code = entry['sw']
                
                # Determinar si viene de un comando Present PSC revisando entradas previas
                is_present_psc_context = self._is_present_psc_context(active_session, entry)
                
                # Verificar diferentes tipos de éxito según el comando y contexto
                if (sw_code == "90 07" or  # Present PSC correcto (SLE5542)
                    sw_code == "90 FF" or  # Present PSC correcto (SLE5528)
                    (sw_code == "90 00" and not is_present_psc_context)):  # Éxito general solo si NO es Present PSC
                    self.log_text.insert(tk.END, "✅ ", "success_icon")
                    
                    # Mostrar datos de respuesta si están disponibles, sino solo SW
                    if 'response_data' in entry:
                        self.log_text.insert(tk.END, "RESPONSE: ", "response_text")
                        self.log_text.insert(tk.END, f"{entry['response_data']}\n", "success_text")
                        
                        # Si hay contenido ASCII, mostrarlo en una nueva línea con color diferente
                        if 'ascii_data' in entry and entry['ascii_data']:
                            self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                            self.log_text.insert(tk.END, "📝 ", "cmd_icon")
                            self.log_text.insert(tk.END, "ASCII: ", "response_text")
                            self.log_text.insert(tk.END, f"{entry['ascii_data']}\n", "ascii_text")
                        
                        # Mostrar SW en línea separada
                        self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                        self.log_text.insert(tk.END, "📋 ", "cmd_icon")
                        self.log_text.insert(tk.END, "SW: ", "response_text")
                        self.log_text.insert(tk.END, f"{sw_code}\n", "success_text")
                    else:
                        # Solo SW sin "RESPONSE:"
                        self.log_text.insert(tk.END, "SW: ", "response_text")
                        self.log_text.insert(tk.END, f"{sw_code}\n", "success_text")
                else:
                    # Incluye 90 00 en contexto de Present PSC (tarjeta bloqueada)
                    self.log_text.insert(tk.END, "⚠️ ", "warning_icon")
                    
                    # Mostrar datos de respuesta si están disponibles, sino solo SW
                    if 'response_data' in entry:
                        self.log_text.insert(tk.END, "RESPONSE: ", "response_text")
                        self.log_text.insert(tk.END, f"{entry['response_data']}\n", "warning_text")
                        
                        # Si hay contenido ASCII, mostrarlo en una nueva línea con color diferente
                        if 'ascii_data' in entry and entry['ascii_data']:
                            self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                            self.log_text.insert(tk.END, "📝 ", "cmd_icon")
                            self.log_text.insert(tk.END, "ASCII: ", "response_text")
                            self.log_text.insert(tk.END, f"{entry['ascii_data']}\n", "ascii_text")
                        
                        # Mostrar SW en línea separada
                        self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                        self.log_text.insert(tk.END, "📋 ", "cmd_icon")
                        self.log_text.insert(tk.END, "SW: ", "response_text")
                        self.log_text.insert(tk.END, f"{sw_code}\n", "warning_text")
                    else:
                        # Solo SW sin "RESPONSE:"
                        self.log_text.insert(tk.END, "SW: ", "response_text")
                        self.log_text.insert(tk.END, f"{sw_code}\n", "warning_text")

                # Separador final más corto
                self.log_text.insert(tk.END, "──────────────────────────────────────────────────────────────\n\n", "separator")
                
        elif log_type == "INFO":
            # Información general sin bordes esquinados
            self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
            self.log_text.insert(tk.END, "ℹ️  ", "info_icon")
            self.log_text.insert(tk.END, "INFO: ", "info_text")
            self.log_text.insert(tk.END, f"{message}\n\n", "info_text")

        elif log_type == "ERROR":
            # Errores sin bordes esquinados
            self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
            self.log_text.insert(tk.END, "❌ ", "error_icon")
            self.log_text.insert(tk.END, "ERROR: ", "error_text")
            self.log_text.insert(tk.END, f"{message}\n\n", "error_text")

    def update_cards_list(self):
        """Actualiza la lista de tarjetas abiertas en la interfaz (usando CardExplorer)"""
        if not hasattr(self, 'card_explorer'):
            return
        
        sessions = self.session_manager.get_all_sessions()
        active_session = self.session_manager.get_active_session()
        
        # Obtener IDs de sesiones actuales
        current_session_ids = {session.session_id for session in sessions}
        
        # Eliminar tarjetas que ya no existen en el session_manager
        cards_to_remove = []
        for card in self.card_explorer.card_data:
            if card['session_id'] not in current_session_ids:
                cards_to_remove.append(card['session_id'])
        
        for session_id in cards_to_remove:
            self.card_explorer.remove_card(session_id)
        
        # Añadir nuevas tarjetas
        for session in sessions:
            # Verificar si la tarjeta ya existe en el explorador
            card_exists = any(card['session_id'] == session.session_id for card in self.card_explorer.card_data)
            
            if not card_exists:
                # Añadir nueva tarjeta
                card_type_str = '5542' if session.card_type == CARD_TYPE_5542 else '5528'
                is_active = active_session and session.session_id == active_session.session_id
                
                success = self.card_explorer.add_card(
                    session.card_name, 
                    card_type_str, 
                    session.session_id, 
                    is_active
                )
                
                if not success:
                    # Explorer está lleno
                    from tkinter import messagebox
                    messagebox.showwarning("Card Limit", 
                                         f"Maximum cards limit reached ({self.card_explorer.max_cards}). "
                                         "Close some cards before creating new ones.")
                    break
        
        # Actualizar estados visuales
        if active_session:
            self.card_explorer.set_active_card(active_session.session_id)
        
        # Si estamos en Small Screen Mode, actualizar la lista compacta
        if getattr(self, 'small_screen_mode', False) and hasattr(self, 'compact_listbox'):
            self._populate_compact_cards_list()
    
    def update_card_info_display(self):
        """Actualiza la información mostrada de la tarjeta seleccionada"""
        active_session = self.session_manager.get_active_session()
        
        # Si hay un label de información de tarjeta, actualizarlo
        if hasattr(self, 'card_info_label'):
            if active_session:
                info_text = f"Card: {active_session.card_name} | "
                info_text += f"Type: {active_session._get_card_type_display()} | "
                info_text += f"State: {active_session.get_current_app_state()}"
                self.card_info_label.config(text=info_text)
            else:
                self.card_info_label.config(text="No cards open")
    
    def create_memory_panel(self):
        """Columna 3: Panel de contenido de memoria + Paneles PSC/Errores"""
        # Frame principal para la columna 3 (SOLO MEMORIA Y PANELES PEQUEÑOS)
        memory_frame = tk.Frame(self.root, bg=COLOR_BG_PANEL, relief=tk.RAISED, bd=1)
        memory_frame.grid(row=0, column=2, sticky='nsew', padx=2, pady=3)
        memory_frame.grid_rowconfigure(0, weight=1)  # Memoria (principal)
        memory_frame.grid_rowconfigure(1, weight=0, minsize=40)   # Paneles PSC/Errores (pequeños)
        memory_frame.grid_columnconfigure(0, weight=1)
        
        # === PANEL DE MEMORIA (PRINCIPAL) ===
        self.memory_main_frame = tk.LabelFrame(memory_frame, text="Card Memory Content", 
                                         font=FONT_SECTION_TITLE, bg=COLOR_BG_PANEL, 
                                         fg=COLOR_TEXT_PRIMARY, relief=tk.GROOVE, bd=2)
        self.memory_main_frame.grid(row=0, column=0, sticky='nsew', padx=8, pady=(8, 4))
        self.memory_main_frame.grid_rowconfigure(0, weight=1)
        
        # CONFIGURACIÓN DE 3 SUB-COLUMNAS: Direcciones | Contenido Hex | ASCII
        self.memory_main_frame.grid_columnconfigure(0, weight=0, minsize=80)   # Direcciones (ROW\COL)
        self.memory_main_frame.grid_columnconfigure(1, weight=2, minsize=360)  # Contenido Hex (peso 2)
        self.memory_main_frame.grid_columnconfigure(2, weight=1, minsize=240)  # ASCII (peso 1, expandible)
        
        # === COLUMNA 1: DIRECCIONES ===
        addr_frame = tk.Frame(self.memory_main_frame, bg=COLOR_BG_TABLE, relief=tk.RAISED, bd=1)
        addr_frame.grid(row=0, column=0, sticky='nsew', padx=(6, 1), pady=6)
        addr_frame.grid_rowconfigure(1, weight=1)
        addr_frame.grid_columnconfigure(0, weight=1)
        
        # Label para direcciones
        addr_label = tk.Label(addr_frame, text="ADDR", bg=COLOR_BG_TABLE, 
                             fg=COLOR_TEXT_TABLE, font=FONT_BOLD, anchor='center')
        addr_label.grid(row=0, column=0, sticky='ew', padx=2, pady=(2, 2))
        
        # Área de texto para direcciones (no editable, sin scroll)
        self.address_text = tk.Text(addr_frame, bg=COLOR_BG_TABLE, fg=COLOR_TEXT_TABLE,
                                   font=FONT_MONO, wrap=tk.NONE, relief=tk.FLAT,
                                   selectbackground="#FFD54F",  # Color amarillo claro para selección
                                   selectforeground="#000000",  # Texto negro al seleccionar
                                   state=tk.DISABLED, width=8, height=20,  # Ancho revertido a 8
                                   cursor='arrow', takefocus=False, spacing1=2)  # spacing1 para alineación vertical
        self.address_text.grid(row=1, column=0, sticky='nsew', padx=2, pady=(0, 2))
        
        # === COLUMNA 2: CONTENIDO HEX ===
        coords_frame = tk.Frame(self.memory_main_frame, bg=COLOR_BG_TABLE, relief=tk.RAISED, bd=1)
        coords_frame.grid(row=0, column=1, sticky='nsew', padx=1, pady=6)
        coords_frame.grid_rowconfigure(1, weight=1)
        coords_frame.grid_columnconfigure(0, weight=1)
        
        # Label para COORDENADAS
        coords_label = tk.Label(coords_frame, text="HEX CONTENT", bg=COLOR_BG_TABLE, 
                               fg=COLOR_TEXT_TABLE, font=FONT_BOLD, anchor='center')
        coords_label.grid(row=0, column=0, sticky='ew', padx=5, pady=(2, 2))
        
        # Área de texto para coordenadas (seleccionable para copiar, ancho ajustado al contenido)
        self.memory_text = tk.Text(coords_frame, bg=COLOR_BG_TABLE, fg=COLOR_TEXT_TABLE,
                                  font=FONT_MONO, wrap=tk.NONE, relief=tk.FLAT,  # Revertir a wrap=NONE
                                  insertbackground=COLOR_TEXT_TABLE, 
                                  selectbackground="#FFD54F",  # Color amarillo claro para selección
                                  selectforeground="#000000",  # Texto negro al seleccionar
                                  state=tk.NORMAL, height=20, width=47, cursor='ibeam',
                                  spacing1=2)  # spacing1 para alineación vertical
        self.memory_text.grid(row=1, column=0, sticky='ns', padx=5, pady=(0, 2))  # Revertir a sticky ns
        
        # === COLUMNA 3: ASCII ===
        ascii_frame = tk.Frame(self.memory_main_frame, bg=COLOR_BG_TABLE, relief=tk.RAISED, bd=1)
        ascii_frame.grid(row=0, column=2, sticky='nsew', padx=(1, 6), pady=6)
        ascii_frame.grid_rowconfigure(1, weight=1)
        ascii_frame.grid_columnconfigure(0, weight=1)
        
        # Label para ASCII
        ascii_label = tk.Label(ascii_frame, text="ASCII", bg=COLOR_BG_TABLE, 
                              fg=COLOR_TEXT_TABLE, font=FONT_BOLD, anchor='center')
        ascii_label.grid(row=0, column=0, sticky='ew', padx=3, pady=(2, 2))
        
        # Área de texto para ASCII
        self.ascii_text = tk.Text(ascii_frame, font=FONT_MONO,  # Cambié de FONT_MONO_SMALL a FONT_MONO
                                 bg=COLOR_BG_TABLE, fg=COLOR_TEXT_TABLE,
                                 relief=tk.FLAT, selectbackground="#FFD54F",  # Color amarillo claro para selección
                                 selectforeground="#000000",  # Texto negro al seleccionar
                                 state=tk.NORMAL, wrap=tk.NONE, width=31, height=20,  # Reducir de 32 a 31
                                 cursor='ibeam', spacing1=2)  # spacing1 agrega espacio entre líneas
        self.ascii_text.grid(row=1, column=0, sticky='ns', padx=8, pady=(0, 2))  # Revertir a sticky ns
        
        # Configurar tag para espacios no seleccionables (elide)
        self.ascii_text.tag_configure("ascii_spacing", elide=False, font=FONT_MONO)
        
        # Interceptar Ctrl+C para copiar ASCII sin espacios
        self.ascii_text.bind("<Control-c>", self._copy_ascii_without_spaces)
        self.ascii_text.bind("<Control-C>", self._copy_ascii_without_spaces)
        
        # Configurar tags de colores para la memoria
        self._configure_memory_color_tags()
        
        # === PANELES PEQUEÑOS: PSC y FALLOS ===
        info_panels_frame = tk.Frame(memory_frame, bg=COLOR_BG_PANEL)
        info_panels_frame.grid(row=1, column=0, sticky='ew', padx=8, pady=(0, 8))
        info_panels_frame.grid_columnconfigure(0, weight=1, uniform="panels")  # PSC panel proporcional
        info_panels_frame.grid_columnconfigure(1, weight=1, uniform="panels")  # Fallos panel proporcional  
        info_panels_frame.grid_columnconfigure(2, weight=1, uniform="panels")  # Reset button panel proporcional
        
        # Panel PSC actual (con borde morado y diseño mejorado)
        psc_frame = tk.LabelFrame(info_panels_frame, text="Current PSC", 
                                 font=FONT_BOLD, bg=COLOR_BG_PANEL, 
                                 fg='#9C27B0', relief=tk.RAISED, bd=2)
        psc_frame.grid(row=0, column=0, sticky='ew', padx=(0, 2))
        psc_frame.grid_propagate(False)  # Mantener tamaño fijo
        
        self.psc_label = tk.Label(psc_frame, text="-- -- --", font=FONT_HEADER,
                                 bg=COLOR_BG_PANEL, fg='#9C27B0')
        self.psc_label.pack(padx=8, pady=6)
        
        # Panel fallos restantes (diseño mejorado)
        errors_frame = tk.LabelFrame(info_panels_frame, text="Remaining Errors", 
                                    font=FONT_BOLD, bg=COLOR_BG_PANEL, 
                                    fg=COLOR_ERROR, relief=tk.RAISED, bd=2)
        errors_frame.grid(row=0, column=1, sticky='ew', padx=2)
        errors_frame.grid_propagate(False)  # Mantener tamaño fijo
        
        self.errors_label = tk.Label(errors_frame, text="---", font=FONT_HEADER,
                                    bg=COLOR_BG_PANEL, fg=COLOR_TEXT_PRIMARY)
        self.errors_label.pack(padx=8, pady=6)
        
        # Panel Reset Error Counter (con mismo formato que los otros)
        reset_frame = tk.LabelFrame(info_panels_frame, text="Reset Counter", 
                                   font=FONT_BOLD, bg=COLOR_BG_PANEL, 
                                   fg=COLOR_PRIMARY_BLUE, relief=tk.RAISED, bd=2)
        reset_frame.grid(row=0, column=2, sticky='ew', padx=(2, 0))
        reset_frame.grid_propagate(False)  # Mantener tamaño fijo
        
        self.button_refs['reset_error_counter'] = tk.Button(reset_frame, text="Reset Error Counter",
                                                           command=self.reset_error_counter,
                                                           bg=COLOR_PRIMARY_BLUE, fg=COLOR_TEXT_BUTTON_ENABLED,
                                                           font=FONT_SMALL, relief=tk.RAISED,
                                                           cursor='hand2', bd=1)
        self.button_refs['reset_error_counter'].pack(padx=8, pady=6, fill='x')  # Padding original

    def create_pages_panel(self):
        """Columna 4: Panel de botones de página"""
        pages_frame = tk.Frame(self.root, bg=COLOR_BG_PANEL, relief=tk.RAISED, bd=1)
        pages_frame.grid(row=0, column=3, sticky='nsew', padx=(2, 5), pady=3)
        pages_frame.grid_propagate(False)
        pages_frame.configure(width=80)
        
        # Guardar referencia para el modo small screen
        self.pages_frame = pages_frame
        
        # Title compacto
        title_label = tk.Label(pages_frame, text="Pages", bg=COLOR_BG_PANEL, 
                              font=FONT_BOLD, fg=COLOR_TEXT_PRIMARY)
        title_label.pack(pady=(8, 5))
        
        # Page buttons P0-P3 compactos
        self.page_buttons = []
        for i in range(4):
            btn = tk.Button(pages_frame, text=f"P{i}",
                           command=lambda p=i: self.select_page(p),
                           bg=COLOR_SUCCESS if i == 0 else COLOR_DISABLED_GRAY,
                           fg=COLOR_TEXT_BUTTON_ENABLED,
                           font=FONT_NORMAL, relief=tk.RAISED, bd=1,
                           width=4, height=1, cursor='hand2',
                           state=tk.DISABLED)  # Disabled by default
            btn.pack(pady=3, padx=5)
            self.page_buttons.append(btn)
            self.button_refs[f'page_{i}'] = btn

    def create_bottom_panel(self):
        """Panel inferior con Command Log (izquierda) y botones de acción (derecha)"""
        bottom_frame = tk.Frame(self.root, bg=COLOR_BG_PANEL, relief=tk.RAISED, bd=1)
        bottom_frame.grid(row=1, column=0, columnspan=4, sticky='nsew', padx=5, pady=(1, 5))
        bottom_frame.grid_rowconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(0, weight=1, minsize=400)  # Log más pequeño con mínimo
        bottom_frame.grid_columnconfigure(1, weight=0, minsize=120)  # Physical Cards más estrecho
        bottom_frame.grid_columnconfigure(2, weight=0, minsize=220)  # Actions más ancho
        
        # Guardar referencia para el modo small screen
        self.bottom_frame = bottom_frame
        
        # LADO IZQUIERDO: Command Log (más compacto)
        log_frame = tk.LabelFrame(bottom_frame, text="Command Log", 
                                 font=FONT_SECTION_TITLE, bg=COLOR_BG_PANEL, 
                                 fg=COLOR_TEXT_PRIMARY, relief=tk.GROOVE, bd=2)
        log_frame.grid(row=0, column=0, sticky='nsew', padx=(8, 2), pady=8)  # Menos padding derecho
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        # Log text area expandible (solo lectura) con estilo profesional cohesivo - REDUCIDO
        self.log_text = tk.Text(log_frame, font=("Consolas", 9),  # Fuente más pequeña
                               bg=COLOR_BG_PANEL, fg=COLOR_TEXT_PRIMARY, wrap=tk.WORD,
                               relief=tk.FLAT, bd=0, selectbackground="#FFD54F",  # Color amarillo claro para selección
                               insertbackground=COLOR_TEXT_PRIMARY, selectforeground="#000000",  # Texto negro al seleccionar
                               state=tk.DISABLED, cursor="arrow")
        self.log_text.grid(row=0, column=0, sticky='nsew', padx=4, pady=4)  # Padding reducido
        
        # Scrollbar para el log
        log_scroll = tk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky='ns', pady=4)  # Padding reducido
        self.log_text.configure(yscrollcommand=log_scroll.set)
        
        # CENTRO: Panel de Physical Cards (más hacia la izquierda)
        physical_cards_frame = tk.LabelFrame(bottom_frame, text="Physical Cards", 
                                           font=FONT_SECTION_TITLE, bg=COLOR_BG_PANEL, 
                                           fg=COLOR_TEXT_PRIMARY, relief=tk.GROOVE, bd=2)
        physical_cards_frame.grid(row=0, column=1, sticky='nsew', padx=(2, 2), pady=8)  # Menos padding lateral
        physical_cards_frame.grid_rowconfigure(0, weight=1)
        physical_cards_frame.grid_columnconfigure(0, weight=1)
        
        # Guardar referencia para el modo small screen
        self.physical_cards_frame = physical_cards_frame
        
        # Contenedor central para los iconos Physical Cards (más compacto)
        physical_cards_container = tk.Frame(physical_cards_frame, bg=COLOR_BG_PANEL)
        physical_cards_container.pack(expand=True, fill=tk.BOTH, padx=3, pady=3)  # Padding reducido
        
        # Crear los iconos Write Card y Read Card en el nuevo panel
        self.create_write_card_icon(physical_cards_container)
        
        # LADO DERECHO: Panel de botones de acción (más ancho)
        self.actions_container = tk.LabelFrame(bottom_frame, text="Actions", 
                                     font=FONT_SECTION_TITLE, bg=COLOR_BG_PANEL, 
                                     fg=COLOR_TEXT_PRIMARY, relief=tk.GROOVE, bd=2)
        self.actions_container.grid(row=0, column=2, sticky='nsew', padx=(2, 8), pady=8)  # Menos padding izquierdo
        self.actions_container.grid_rowconfigure(0, weight=1)
        self.actions_container.grid_columnconfigure(0, weight=1)
        
        # Frame para los botones (reorganizado en grid 3x2) - más espacio
        buttons_container = tk.Frame(self.actions_container, bg=COLOR_BG_PANEL)
        buttons_container.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)  # Más padding para mejor apariencia
        
        # Configurar grid 3 filas x 2 columnas
        buttons_container.grid_rowconfigure(0, weight=0)  # Fila 1
        buttons_container.grid_rowconfigure(1, weight=0)  # Fila 2
        buttons_container.grid_rowconfigure(2, weight=0)  # Fila 3
        buttons_container.grid_columnconfigure(0, weight=1)  # Columna 1
        buttons_container.grid_columnconfigure(1, weight=1)  # Columna 2
        
        # Guardar referencia para uso posterior
        self.buttons_scrollable_frame = buttons_container
        
        # FILA 1: Save Log (0,0) y Clear Log (0,1)
        save_log_btn = tk.Button(buttons_container, text="SAVE LOG", bg=COLOR_PRIMARY_BLUE, fg='white',
                            font=FONT_BOLD, relief=tk.RAISED, bd=2, padx=10, pady=10,  # Más alto
                            command=self.save_log_to_file, width=12, height=1)  # Añadido height
        save_log_btn.grid(row=0, column=0, padx=3, pady=3, sticky='ew')
        
        clear_log_btn = tk.Button(buttons_container, text="CLEAR LOG", bg=COLOR_DISABLED_GRAY, fg='white',
                             font=FONT_BOLD, relief=tk.RAISED, bd=2, padx=10, pady=10,  # Más alto
                             command=self.clear_log, width=12, height=1)  # Añadido height
        clear_log_btn.grid(row=0, column=1, padx=3, pady=3, sticky='ew')
        
        # FILA 2: APDUs (1,0) y Settings (1,1) - CAMBIO: Settings movido aquí
        apdus_btn = tk.Button(buttons_container, text="APDU's", bg=COLOR_PRIMARY_BLUE, fg='white',
                            font=FONT_BOLD, relief=tk.RAISED, bd=2, padx=10, pady=10,  # Más alto
                            command=self.show_apdus_reference, width=12, height=1)  # Añadido height
        apdus_btn.grid(row=1, column=0, padx=3, pady=3, sticky='ew')
        
        settings_btn = tk.Button(buttons_container, text="SETTINGS", bg=COLOR_DISABLED_GRAY, fg='white',
                                font=FONT_BOLD, relief=tk.RAISED, bd=2, padx=10, pady=10,  # Más alto
                                command=self.open_settings_dialog, width=12, height=1)  # Añadido height
        settings_btn.grid(row=1, column=1, padx=3, pady=3, sticky='ew')
        
        # FILA 3: Credits (2,0) - CAMBIO: Credits movido aquí
        credits_btn = tk.Button(buttons_container, text="CREDITS", bg=COLOR_DISABLED_GRAY, fg='white',
                               font=FONT_BOLD, relief=tk.RAISED, bd=2, padx=10, pady=10,  # Más alto
                               command=self.show_credits_image, width=12, height=1)  # Añadido height
        credits_btn.grid(row=2, column=0, padx=3, pady=3, sticky='ew')
    
    def create_write_card_icon(self, parent_frame):
        """Crea los iconos Write Card y Read Card"""
        from .dialogs import load_icon_image
        
        try:
            # Cargar icono Write Card girado (más grande para mejor visibilidad)
            write_icon_image = load_icon_image("write_card_girado.png", (72, 72))
            
            # Cargar icono Read Card específico
            read_icon_image = load_icon_image("open_card_girado.png", (72, 72))
            
            # Frame para Write Card
            write_frame = tk.Frame(parent_frame, bg=COLOR_BG_PANEL)
            write_frame.pack(pady=(5, 2), padx=8)  # Reducido espacio superior de 8 a 5, inferior de 3 a 2
            
            # Botón Write Card con icono
            write_icon_btn = tk.Button(write_frame, 
                                      image=write_icon_image,
                                      command=self.write_to_real_card,
                                      bg=COLOR_BG_PANEL,
                                      activebackground=COLOR_BG_PANEL,
                                      relief=tk.FLAT,
                                      bd=0,
                                      cursor="hand2",
                                      padx=8, pady=8)
            write_icon_btn.pack(pady=(0, 0))  # Sin padding vertical
            write_icon_btn.image = write_icon_image  # Guardar referencia
            
            # Label para Write Card
            write_label = tk.Label(write_frame, text="Write Card", 
                                 font=FONT_BOLD, bg=COLOR_BG_PANEL, 
                                 fg=COLOR_TEXT_PRIMARY)
            write_label.pack(pady=(0, 0))  # Sin padding vertical (pegado al icono)
            
            # Frame para Read Card
            read_frame = tk.Frame(parent_frame, bg=COLOR_BG_PANEL)
            read_frame.pack(pady=(2, 8), padx=8)  # Reducida separación superior de 3 a 2, inferior de 15 a 8
            
            # Botón Read Card con su propio icono
            read_icon_btn = tk.Button(read_frame, 
                                     image=read_icon_image,
                                     command=self.read_from_real_card,
                                     bg=COLOR_BG_PANEL,
                                     activebackground=COLOR_BG_PANEL,
                                     relief=tk.FLAT,
                                     bd=0,
                                     cursor="hand2",
                                     padx=8, pady=8)
            read_icon_btn.pack(pady=(0, 0))  # Sin padding vertical
            read_icon_btn.image = read_icon_image  # Guardar referencia
            
            # Label para Read Card
            read_label = tk.Label(read_frame, text="Read Card", 
                                font=FONT_BOLD, bg=COLOR_BG_PANEL, 
                                fg=COLOR_TEXT_PRIMARY)
            read_label.pack(pady=(0, 0))  # Sin padding vertical (pegado al icono)
            
        except Exception as e:
            print(f"Error loading card icons: {e}")
            # Fallback: botones de texto si no se puede cargar el icono (más grandes también)
            write_btn = tk.Button(parent_frame, text="WRITE CARD", 
                                bg=COLOR_PRIMARY_BLUE, fg='white',
                                font=FONT_BOLD, relief=tk.RAISED, bd=2, 
                                padx=10, pady=8,
                                command=self.write_to_real_card, width=14)
            write_btn.pack(pady=(8, 3), padx=8)  # Reducido espacio superior de 15 a 8
            
            read_btn = tk.Button(parent_frame, text="READ CARD", 
                               bg=COLOR_PRIMARY_BLUE, fg='white',
                               font=FONT_BOLD, relief=tk.RAISED, bd=2, 
                               padx=10, pady=8,
                               command=self.read_from_real_card, width=14)
            read_btn.pack(pady=(3, 15), padx=8)  # Reducida separación superior
    
    def on_card_select_from_explorer(self, session_id):
        """Maneja la selección de una tarjeta desde el CardExplorer"""
        self.session_manager.set_active_session(session_id)
        
        # Actualizar estado visual en el explorador
        if hasattr(self, 'card_explorer'):
            self.card_explorer.set_active_card(session_id)
        
        # Actualizar interfaz
        self.update_interface_for_active_session()
    
    def get_current_time(self):
        """Obtiene el tiempo actual formateado"""
        import datetime
        return datetime.datetime.now().strftime("%H:%M:%S")
    
    def select_page(self, page_num):
        """Selecciona una página específica para tarjetas SLE5528"""
        active_session = self.session_manager.get_active_session()
        
        # Solo permitir cambio de página si hay una sesión activa con tarjeta 1KB seleccionada
        if not active_session or not active_session.card_selected:
            return
        
        # Solo para tarjetas SLE5528 (1KB)
        if active_session.card_type != CARD_TYPE_5528:
            return
        
        # Actualizar página actual
        self.current_page = page_num
        self.page_var.set(f"P{page_num}")
        
        # Actualizar la página en el memory_manager de la sesión
        active_session.memory_manager.set_current_page(page_num)
        
        # Actualizar interfaz
        self.update_page_buttons()
        self.update_card_display()
    
    def update_page_buttons(self):
        """Actualiza el estado visual de los botones de página según la tarjeta activa"""
        active_session = self.session_manager.get_active_session()
        
        # Si no hay sesión activa O la tarjeta no está seleccionada, deshabilitar todos los botones
        if not active_session or not active_session.card_selected:
            for btn in self.page_buttons:
                btn.configure(bg=COLOR_DISABLED_GRAY, fg=COLOR_TEXT_BUTTON_DISABLED, 
                            state=tk.DISABLED, cursor='arrow')
            # Mostrar página 0 por defecto
            self.current_page = 0
            self.page_var.set("P0")
            # Actualizar también botones de Small Screen Mode si existen
            if hasattr(self, '_small_screen_page_buttons'):
                self._update_small_screen_page_buttons()
            return
        
        # Determinar si es tarjeta de 1KB (5528) o 256B (5542)
        is_1kb_card = active_session.card_type == CARD_TYPE_5528
        
        for i, btn in enumerate(self.page_buttons):
            if is_1kb_card:
                # Habilitar todos los botones para SLE5528 (1KB)
                btn.configure(state=tk.NORMAL, cursor='hand2')
                if i == self.current_page:
                    # Página actual - color destacado
                    btn.configure(bg=COLOR_SUCCESS, fg=COLOR_TEXT_BUTTON_ENABLED)
                else:
                    # Páginas disponibles - color normal
                    btn.configure(bg=COLOR_PRIMARY_BLUE, fg=COLOR_TEXT_BUTTON_ENABLED)
            else:
                # Para SLE5542 (256B) - solo página 0 disponible
                if i == 0:
                    # Solo P0 habilitado y siempre seleccionado
                    btn.configure(bg=COLOR_SUCCESS, fg=COLOR_TEXT_BUTTON_ENABLED, 
                                state=tk.NORMAL, cursor='hand2')
                    self.current_page = 0  # Forzar página 0
                    self.page_var.set("P0")
                else:
                    # P1, P2, P3 deshabilitadas
                    btn.configure(bg=COLOR_DISABLED_GRAY, fg=COLOR_TEXT_BUTTON_DISABLED, 
                                state=tk.DISABLED, cursor='arrow')
        
        # Actualizar también botones de Small Screen Mode si existen
        if hasattr(self, '_small_screen_page_buttons'):
            self._update_small_screen_page_buttons()
    
    def new_card_dialog(self):
        """Abre diálogo para crear una nueva tarjeta"""
        from src.gui.dialogs import NewCardDialog
        NewCardDialog(self.root, self.handle_new_card)
        
    def handle_new_card(self, card_data):
        """Maneja la creación de una nueva tarjeta"""
        if card_data and card_data.get('action') == 'create':
            name = card_data['name']
            card_type_str = card_data['type']
            
            # Verificar límite de tarjetas
            if hasattr(self, 'card_explorer') and self.card_explorer.is_full():
                messagebox.showwarning("Card Limit", 
                                     f"Maximum cards limit reached ({self.card_explorer.max_cards}). "
                                     "Close some cards before creating new ones.")
                return
            
            # Convertir string a constante
            card_type = CARD_TYPE_5542 if card_type_str == "5542" else CARD_TYPE_5528
            
            # Crear nueva sesión de tarjeta
            session, message = self.session_manager.create_new_card_session(name, card_type)
            
            if session:
                # Actualizar la interfaz
                self.update_cards_list()
                self.update_interface_for_active_session()
                self.log(f"New card '{name}' (SLE{card_type_str}) created successfully", "SUCCESS")
            else:
                messagebox.showerror("Error", f"Could not create card: {message}")
    
    def open_card_dialog(self):
        """Abre diálogo para cargar una tarjeta desde archivo"""
        def handle_open(filepath):
            # Extraer nombre sugerido del archivo
            suggested_name = os.path.splitext(os.path.basename(filepath))[0]
            
            # Pedir nombre de la tarjeta al usuario
            name = self.ask_card_name(suggested_name)
            if name:
                # Verificar que el nombre no esté duplicado
                if self.session_manager.get_session_by_name(name):
                    InfoDialog(self.root, "Error", f"Card name '{name}' already exists. Choose a different name.", "error")
                    return
                
                session, message = self.session_manager.open_card_from_file(filepath, name)
                
                if session:
                    self.update_cards_list()
                    # Actualizar interfaz con la sesión cargada
                    self.session_manager.set_active_session(session.session_id)
                    self.update_interface_for_active_session()
                    self.log(f"Card '{name}' loaded from file: {filepath}", "SUCCESS")
                else:
                    InfoDialog(self.root, "Error", f"Could not open card: {message}", "error")
        
        # Mostrar diálogo personalizado centrado
        OpenCardDialog(self.root, handle_open)
    
    def ask_card_name(self, suggested_name=""):
        """Solicita un nombre para la tarjeta al usuario usando el diálogo personalizado"""
        from .dialogs import CardNameDialog
        
        dialog = CardNameDialog(self.root, suggested_name)
        name = dialog.get_result()
        
        if name and name.strip():
            return name.strip()
        return None

    def open_settings_dialog(self):
        """Abre el diálogo de Settings con control de acceso administrativo"""
        from .dialogs import SettingsDialog
        
        dialog = SettingsDialog(self.root, self)
        dialog.show()

    def update_cards_layout(self, cards_per_row):
        """Actualiza el layout del panel de Open Cards y ajusta el ancho de los paneles"""
        # Guardar la configuración actual
        self.current_cards_per_row = cards_per_row
        
        # Actualizar configuración del CardExplorer con un pequeño delay
        if hasattr(self, 'card_explorer'):
            # Usar after para asegurar que la actualización se procese correctamente
            self.root.after(10, lambda: self._update_card_explorer_layout(cards_per_row))
        else:
            # Si no hay card_explorer, aplicar solo los cambios de grid
            self._apply_grid_layout(cards_per_row)
    
    def _update_card_explorer_layout(self, cards_per_row):
        """Método auxiliar para actualizar el card explorer"""
        self.card_explorer.update_layout(cards_per_row)
        # Aplicar los cambios de grid después de actualizar el card explorer
        self._apply_grid_layout(cards_per_row)
    
    def _apply_grid_layout(self, cards_per_row):
        """Aplica los cambios de layout del grid principal - RESPETANDO Small Screen Mode"""
        
        # IMPORTANTE: Si Small Screen Mode está activo, NO sobrescribir las configuraciones
        if getattr(self, 'small_screen_mode', False):
            return
        
        # NUEVO: Si estamos en contexto post-Small Screen Mode, saltarse para evitar conflictos
        if getattr(self, '_in_post_small_screen_restoration', False):
            return
        
        # Ajustar el ancho del cards_frame directamente según cards_per_row
        if hasattr(self, 'open_cards_frame'):
            cards_frame = self.open_cards_frame.master
            
            if cards_per_row == 1:
                cards_frame.grid_propagate(False)
                cards_frame.configure(width=250, height=cards_frame.winfo_height())
                self.root.grid_columnconfigure(1, weight=0, minsize=250, uniform="")
            else:
                cards_frame.grid_propagate(False)
                cards_frame.configure(width=400, height=cards_frame.winfo_height())
                self.root.grid_columnconfigure(1, weight=0, minsize=400, uniform="")
            
            cards_frame.update_idletasks()
            self.root.update_idletasks()
        
        # Ajustar pesos y tamaños mínimos de las columnas del grid principal SOLO si NO hay Small Screen Mode
        if cards_per_row == 1:
            # 1 tarjeta por fila: Open Cards más estrecho, Memory más ancho
            self.root.grid_columnconfigure(0, weight=0, minsize=250)  # Commands (sin cambio)
            self.root.grid_columnconfigure(1, weight=0, minsize=250)  # Cards + Info (reducido más: 400->250)
            self.root.grid_columnconfigure(2, weight=1, minsize=550)  # Memory (aumentado más: 400->550)
            self.root.grid_columnconfigure(3, weight=0, minsize=80)   # Pages (sin cambio)
            
            # También ajustar las columnas internas del panel de memoria para aprovechar el espacio extra
            if hasattr(self, 'memory_main_frame'):
                self.memory_main_frame.grid_columnconfigure(0, weight=0, minsize=80)   # Direcciones (sin cambio)
                self.memory_main_frame.grid_columnconfigure(1, weight=3, minsize=450)  # Contenido Hex (más ancho: peso 3, minsize 450)
                self.memory_main_frame.grid_columnconfigure(2, weight=2, minsize=320)  # ASCII (más ancho: peso 2, minsize 320)
        else:
            # 2 tarjetas por fila: distribución original
            self.root.grid_columnconfigure(0, weight=0, minsize=250)  # Commands
            self.root.grid_columnconfigure(1, weight=0, minsize=400)  # Cards + Info (original)
            self.root.grid_columnconfigure(2, weight=1, minsize=400)  # Memory (original)
            self.root.grid_columnconfigure(3, weight=0, minsize=80)   # Pages
            
            # Restaurar configuración original del panel de memoria
            if hasattr(self, 'memory_main_frame'):
                self.memory_main_frame.grid_columnconfigure(0, weight=0, minsize=80)   # Direcciones
                self.memory_main_frame.grid_columnconfigure(1, weight=2, minsize=360)  # Contenido Hex (original)
                self.memory_main_frame.grid_columnconfigure(2, weight=1, minsize=240)  # ASCII (original)
        
        # Forzar actualización del layout
        self.root.update_idletasks()
        
        # Limpiar cualquier bandera de control temporal si existe
        if hasattr(self, '_enable_grid_control_for_cards_frame'):
            delattr(self, '_enable_grid_control_for_cards_frame')
        
        self.log(f"Layout updated: {cards_per_row} card(s) per row", "INFO")

    def update_small_screen_mode(self, is_active, silent=False):
        """
        Activa o desactiva el modo Small Screen Form Factor
        
        Args:
            is_active (bool): True para activar, False para desactivar
            silent (bool): Si es True, no muestra mensajes de advertencia/info (para uso desde Settings)
        
        Returns:
            bool: True si se aplicó el cambio, False si no se aplicó (ya estaba en ese estado)
        """
        # Verificar si ya está en el estado solicitado para prevenir bugs
        if hasattr(self, 'small_screen_mode'):
            # Si ya está activo y se intenta activar de nuevo
            if self.small_screen_mode and is_active:
                if not silent:
                    messagebox.showwarning(
                        "Already Active", 
                        "Small Screen Form Factor is already activated.\n\n"
                        "To make changes, first deactivate it and then activate it again."
                    )
                return False
            
            # Si ya está desactivado y se intenta desactivar de nuevo
            if not self.small_screen_mode and not is_active:
                if not silent:
                    messagebox.showinfo(
                        "Already Deactivated", 
                        "Small Screen Form Factor is already deactivated."
                    )
                return False
        
        # Aplicar el cambio solo si es diferente al estado actual
        if is_active:
            self._activate_small_screen_mode()
        else:
            self._deactivate_small_screen_mode()
        
        return True
    
    def _activate_small_screen_mode(self):
        """Activa el modo pantalla pequeña - implementa todos los cambios de layout"""
        self.log("Small Screen Form Factor activated", "INFO")
        print("🔹 Small Screen Form Factor ACTIVATED - Aplicando cambios de layout")
        
        # Establecer flag para Small Screen Mode
        self.small_screen_mode = True
        
        # PASO 0: GUARDAR CONFIGURACIONES ORIGINALES
        self._save_original_layout_configurations()
        
        # 1. REDIMENSIONAR BOTONES ACTIONS: 2 filas x 3 columnas
        self._reconfigure_actions_layout_small()
        
        # 2. MOVER PHYSICAL CARDS DEBAJO DE PAGES
        self._move_physical_cards_small()
        
        # 3. ELIMINAR CARD INFORMATION
        self._hide_card_information()
        
        # 4. REDISEÑAR OPEN CARDS COMO PESTAÑAS
        self._redesign_open_cards_as_tabs()
        
        # 5. EXPANDIR MEMORY CONTENT
        self._expand_memory_content()
        
        # 6. EXPANDIR COMMAND LOG
        self._expand_command_log()
    
    def _save_original_layout_configurations(self):
        """Guarda las configuraciones originales del layout antes de aplicar Small Screen Mode"""
        try:
            # Guardar configuración del grid principal (root) - ESTO ES LO IMPORTANTE
            if not hasattr(self, '_original_root_grid_config'):
                self._original_root_grid_config = {
                    'col0_weight': self.root.grid_columnconfigure(0)['weight'],
                    'col1_weight': self.root.grid_columnconfigure(1)['weight'],
                    'col2_weight': self.root.grid_columnconfigure(2)['weight'],
                    'col3_weight': self.root.grid_columnconfigure(3)['weight'],
                    'col0_minsize': self.root.grid_columnconfigure(0)['minsize'],
                    'col1_minsize': self.root.grid_columnconfigure(1)['minsize'],
                    'col2_minsize': self.root.grid_columnconfigure(2)['minsize'],
                    'col3_minsize': self.root.grid_columnconfigure(3)['minsize']
                }
            
            # Guardar configuración del bottom_frame (columnas)
            if hasattr(self, 'bottom_frame') and not hasattr(self, '_original_bottom_frame_config'):
                self._original_bottom_frame_config = {
                    'col0_weight': self.bottom_frame.grid_columnconfigure(0)['weight'],
                    'col1_weight': self.bottom_frame.grid_columnconfigure(1)['weight'],
                    'col2_weight': self.bottom_frame.grid_columnconfigure(2)['weight'],
                    'col0_minsize': self.bottom_frame.grid_columnconfigure(0)['minsize'],
                    'col1_minsize': self.bottom_frame.grid_columnconfigure(1)['minsize'],
                    'col2_minsize': self.bottom_frame.grid_columnconfigure(2)['minsize']
                }
            
            # Guardar configuración del actions_container si existe
            if hasattr(self, 'actions_container') and not hasattr(self, '_original_actions_config'):
                self._original_actions_config = {
                    'width': self.actions_container.cget('width'),
                    'height': self.actions_container.cget('height')
                }
            
            # Guardar configuraciones de grid del buttons_scrollable_frame
            if hasattr(self, 'buttons_scrollable_frame') and not hasattr(self, '_original_buttons_grid_config'):
                self._original_buttons_grid_config = {
                    'row0_weight': self.buttons_scrollable_frame.grid_rowconfigure(0)['weight'],
                    'row1_weight': self.buttons_scrollable_frame.grid_rowconfigure(1)['weight'],
                    'row2_weight': self.buttons_scrollable_frame.grid_rowconfigure(2)['weight'],
                    'col0_weight': self.buttons_scrollable_frame.grid_columnconfigure(0)['weight'],
                    'col1_weight': self.buttons_scrollable_frame.grid_columnconfigure(1)['weight']
                }
            
        except Exception as e:
            print(f"  ⚠ Error guardando configuraciones originales: {e}")
            import traceback
            traceback.print_exc()
    
    def _reconfigure_actions_layout_small(self):
        """Reconfigura los botones Actions para 2 filas x 3 columnas más compactos"""
        if hasattr(self, 'buttons_scrollable_frame'):
            # Ajustar el ancho del panel Actions para Small Screen Mode
            if hasattr(self, 'actions_container'):
                self.actions_container.configure(width=270)  # Aumentado para que quepan los botones
            
            # Reconfigurar grid: 2 filas x 3 columnas
            self.buttons_scrollable_frame.grid_rowconfigure(0, weight=0)  # Fila 1
            self.buttons_scrollable_frame.grid_rowconfigure(1, weight=0)  # Fila 2
            self.buttons_scrollable_frame.grid_rowconfigure(2, weight=0)  # Remover fila 3
            
            self.buttons_scrollable_frame.grid_columnconfigure(0, weight=1)  # Columna 1
            self.buttons_scrollable_frame.grid_columnconfigure(1, weight=1)  # Columna 2
            self.buttons_scrollable_frame.grid_columnconfigure(2, weight=1)  # Columna 3 nueva
            
            # Obtener botones existentes y reposicionarlos
            buttons = []
            for child in self.buttons_scrollable_frame.winfo_children():
                if isinstance(child, tk.Button):
                    buttons.append(child)
            
            # Reposicionar botones en 2 filas x 3 columnas
            button_positions = [
                (0, 0), (0, 1), (0, 2),  # Fila 1: SAVE LOG, CLEAR LOG, APDU's
                (1, 0), (1, 1), (1, 2)   # Fila 2: SETTINGS, CREDITS, [CHANGE PSC si está habilitado]
            ]
            
            for i, button in enumerate(buttons[:6]):  # Máximo 6 botones
                if i < len(button_positions):
                    row, col = button_positions[i]
                    button.grid(row=row, column=col, padx=1, pady=1, sticky='ew')
                    # Reducir significativamente el tamaño de botones
                    button.configure(width=6, height=1, padx=3, pady=2)
                    # Mantener fuente negrita para legibilidad
                    button.configure(font=FONT_BOLD)  # Restaurar negrita
            
    
    def _move_physical_cards_small(self):
        """Crea un panel conjunto con Pages y Physical Cards en Small Screen Mode"""
        try:
            # Crear el contenedor en columna 3 (igual que el panel de prueba que funcionó)
            self._small_screen_column3_container = tk.Frame(self.root, bg=COLOR_BG_MAIN, relief=tk.FLAT, bd=0)
            self._small_screen_column3_container.grid(row=0, column=3, sticky='nsew', padx=(2, 5), pady=3)
            
            # Configurar grid del contenedor con proporciones optimizadas
            self._small_screen_column3_container.grid_rowconfigure(0, weight=0, minsize=200)  # Zona Pages (un poco más alta)
            self._small_screen_column3_container.grid_rowconfigure(1, weight=0, minsize=10)   # Separador más pequeño
            self._small_screen_column3_container.grid_rowconfigure(2, weight=1, minsize=300)  # Zona Physical Cards
            self._small_screen_column3_container.grid_columnconfigure(0, weight=1)
            
            # PASO 1: Ocultar el Pages frame original y crear los botones de páginas en el contenedor
            if hasattr(self, 'pages_frame'):
                self.pages_frame.grid_remove()  # Ocultar original
            
            # Crear la zona de Pages en el contenedor (fila 0) con espaciado optimizado
            pages_container = tk.LabelFrame(self._small_screen_column3_container, text="Pages", 
                                          font=FONT_SECTION_TITLE, bg=COLOR_BG_PANEL, 
                                          fg=COLOR_TEXT_PRIMARY, relief=tk.GROOVE, bd=2)
            pages_container.grid(row=0, column=0, sticky='nsew', padx=3, pady=(8, 2))  # Menos espacio abajo
            
            # Recrear los botones de páginas
            self._create_page_buttons_in_container(pages_container)
            
            # PASO 2: Crear un separador visual más pequeño (fila 1)
            separator_frame = tk.Frame(self._small_screen_column3_container, bg=COLOR_BG_PANEL, height=1)
            separator_frame.grid(row=1, column=0, sticky='ew', padx=3, pady=0)  # Sin padding vertical
            
            # PASO 3: Ocultar Physical Cards frame original y crear los botones en el contenedor
            if hasattr(self, 'physical_cards_frame'):
                self.physical_cards_frame.grid_remove()  # Ocultar original
            
            # Crear la zona de Physical Cards en el contenedor (fila 2) pegado al bottom
            physical_container = tk.LabelFrame(self._small_screen_column3_container, text="Physical Cards", 
                                             font=FONT_SECTION_TITLE, bg=COLOR_BG_PANEL, 
                                             fg=COLOR_TEXT_PRIMARY, relief=tk.GROOVE, bd=2)
            physical_container.grid(row=2, column=0, sticky='nsew', padx=3, pady=(2, 0))  # Sin espacio abajo
            
            # Recrear los botones de Physical Cards
            self._create_physical_card_buttons_in_container(physical_container)
            
        except Exception as e:
            self.log(f"Error implementando layout real: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_page_buttons_in_container(self, parent_container):
        """Crea los botones de páginas en el contenedor de Small Screen Mode con estilo original"""
        try:
            # Configurar grid del contenedor de páginas
            parent_container.grid_rowconfigure(0, weight=1)
            parent_container.grid_columnconfigure(0, weight=1)
            
            # Frame para los botones de páginas (sin padding extra)
            pages_grid = tk.Frame(parent_container, bg=COLOR_BG_PANEL)
            pages_grid.grid(row=0, column=0, sticky='nsew', padx=0, pady=0)
            
            # Crear los botones P0, P1, P2, P3 con el ESTILO ORIGINAL
            self._small_screen_page_buttons = []
            for i in range(4):
                # Ajustar el padding para el último botón P3
                padding_y = 3 if i < 3 else (3, 8)  # Más espacio debajo de P3
                
                btn = tk.Button(pages_grid, text=f"P{i}",
                               command=lambda p=i: self.select_page(p),
                               bg=COLOR_SUCCESS if i == 0 else COLOR_DISABLED_GRAY,
                               fg=COLOR_TEXT_BUTTON_ENABLED,
                               font=FONT_NORMAL, relief=tk.RAISED, bd=1,
                               width=4, height=1, cursor='hand2',
                               state=tk.DISABLED)  # Disabled by default como el original
                btn.pack(pady=padding_y, padx=5)  # Padding ajustado para P3
                self._small_screen_page_buttons.append(btn)
            
            # Actualizar el estado de los botones según la página actual
            self._update_small_screen_page_buttons()
            
        except Exception as e:
            self.log(f"Error creando botones de páginas: {e}")
    
    def _create_physical_card_buttons_in_container(self, parent_container):
        """Crea los botones de Physical Cards en el contenedor de Small Screen Mode"""
        try:
            # Configurar grid del contenedor de Physical Cards
            parent_container.grid_rowconfigure(0, weight=1)
            parent_container.grid_columnconfigure(0, weight=1)
            
            # Frame para los botones de Physical Cards
            physical_grid = tk.Frame(parent_container, bg=COLOR_BG_PANEL)
            physical_grid.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
            
            # Configurar grid 2x1 para los 2 botones
            physical_grid.grid_rowconfigure(0, weight=1)  # Write Card
            physical_grid.grid_rowconfigure(1, weight=1)  # Read Card
            physical_grid.grid_columnconfigure(0, weight=1)
            
            # Crear los iconos y botones de Physical Cards
            self.create_small_write_card_icons(physical_grid)
            
        except Exception as e:
            self.log(f"Error creando botones de Physical Cards: {e}")
    
    def _update_small_screen_page_buttons(self):
        """Actualiza el estado visual de los botones de páginas en Small Screen Mode"""
        if hasattr(self, '_small_screen_page_buttons'):
            active_session = self.session_manager.get_active_session()
            
            # Si no hay sesión activa o tarjeta no seleccionada, deshabilitar todos
            if not active_session or not active_session.card_selected:
                for btn in self._small_screen_page_buttons:
                    btn.configure(bg=COLOR_DISABLED_GRAY, fg=COLOR_TEXT_BUTTON_DISABLED, 
                                state=tk.DISABLED, cursor='arrow')
                return
            
            # Determinar si es tarjeta de 1KB (5528) o 256B (5542)
            is_1kb_card = active_session.card_type == CARD_TYPE_5528
            
            for i, btn in enumerate(self._small_screen_page_buttons):
                if is_1kb_card:
                    # Habilitar todos los botones para SLE5528 (1KB)
                    btn.configure(state=tk.NORMAL, cursor='hand2')
                    if i == self.current_page:
                        btn.configure(bg=COLOR_SUCCESS, fg=COLOR_TEXT_BUTTON_ENABLED)
                    else:
                        btn.configure(bg=COLOR_PRIMARY_BLUE, fg=COLOR_TEXT_BUTTON_ENABLED)
                else:
                    # Para SLE5542 (256B) - solo página 0 disponible
                    if i == 0:
                        btn.configure(bg=COLOR_SUCCESS, fg=COLOR_TEXT_BUTTON_ENABLED, 
                                    state=tk.NORMAL, cursor='hand2')
                    else:
                        btn.configure(bg=COLOR_DISABLED_GRAY, fg=COLOR_TEXT_BUTTON_DISABLED, 
                                    state=tk.DISABLED, cursor='arrow')
    
    def create_small_write_card_icons(self, parent_frame):
        """Crea iconos de Write Card y Read Card MÁS GRANDES para el modo small screen"""
        from .dialogs import load_icon_image
        
        try:
            # Configurar el frame para usar pack vertical
            parent_frame.configure(bg=COLOR_BG_PANEL)
            
            # Write Card - USAR EL ICONO CORRECTO (write_card_girado.png) y MÁS GRANDE
            write_icon = load_icon_image("write_card_girado.png", size=(70, 70))  # Icono correcto y más grande
            if write_icon:
                write_icon_label = tk.Label(parent_frame, image=write_icon, bg=COLOR_BG_PANEL, cursor='hand2')
                write_icon_label.image = write_icon
                write_icon_label.pack(pady=(15, 8), padx=2)  # Menos padding lateral
                write_icon_label.bind('<Button-1>', lambda e: self.write_to_real_card())  # Función correcta
            
            write_label = tk.Label(parent_frame, text="Write Card", bg=COLOR_BG_PANEL, 
                                  fg=COLOR_TEXT_PRIMARY, font=FONT_BOLD)  # Fuente en negrita
            write_label.pack()
            
            # Read Card - MÁS GRANDE y menos padding lateral
            read_icon = load_icon_image("open_card_girado.png", size=(70, 70))  # Más grande
            if read_icon:
                read_icon_label = tk.Label(parent_frame, image=read_icon, bg=COLOR_BG_PANEL, cursor='hand2')
                read_icon_label.image = read_icon
                read_icon_label.pack(pady=(20, 8), padx=2)  # Menos padding lateral
                read_icon_label.bind('<Button-1>', lambda e: self.read_from_real_card())  # Función correcta
            
            read_label = tk.Label(parent_frame, text="Read Card", bg=COLOR_BG_PANEL, 
                                 fg=COLOR_TEXT_PRIMARY, font=FONT_BOLD)  # Fuente en negrita
            read_label.pack()
            
        except Exception as e:
            self.log(f"Error creando iconos de Physical Cards: {e}")
            import traceback
            traceback.print_exc()
    
    def _hide_card_information(self):
        """Oculta la sección Card Information para liberar espacio"""
        if hasattr(self, 'card_info_frame'):
            try:
                self.card_info_frame.grid_forget()
            except Exception as e:
                print(f"  ⚠ Error ocultando Card Information: {e}")
    
    def _redesign_open_cards_as_tabs(self):
        """Rediseña Open Cards usando funcionalidad existente del CardExplorer adaptada"""
        try:
            # 1. OCULTAR EL CARDS_FRAME COMPLETO
            if hasattr(self, 'open_cards_frame'):
                cards_frame = self.open_cards_frame.master  # Este es el cards_frame
                if not hasattr(self, '_original_cards_frame_info'):
                    self._original_cards_frame_info = cards_frame.grid_info()
            
            # 2. CREAR PANEL COMPACTO DE PESTAÑAS EN COMMANDS (tamaño fijo)
            if hasattr(self, 'card_info_frame'):
                # Encontrar el padre de card_info_frame (commands_frame)
                commands_frame = self.card_info_frame.master
                
                if not hasattr(self, 'compact_cards_frame'):
                    # Crear frame compacto con tamaño FIJO
                    self.compact_cards_frame = tk.LabelFrame(commands_frame, text="Open Cards (Compact)", 
                                                           font=FONT_SECTION_TITLE, bg=COLOR_BG_PANEL, 
                                                           fg=COLOR_TEXT_PRIMARY, relief=tk.GROOVE, bd=2,
                                                           height=120)  # ALTURA FIJA para evitar crecimiento
                    self.compact_cards_frame.grid(row=2, column=0, sticky='ew', padx=8, pady=(2, 8))
                    self.compact_cards_frame.grid_propagate(False)  # CRÍTICO: No permitir que crezca
                    self.compact_cards_frame.grid_rowconfigure(0, weight=1)
                    self.compact_cards_frame.grid_columnconfigure(0, weight=1)
                    
                    # Frame interno scrollable (usando misma técnica que CardExplorer)
                    inner_frame = tk.Frame(self.compact_cards_frame, bg=COLOR_BG_PANEL)
                    inner_frame.grid(row=0, column=0, sticky='nsew', padx=4, pady=4)
                    inner_frame.grid_rowconfigure(0, weight=1)
                    inner_frame.grid_columnconfigure(0, weight=1)
                    
                    # Lista de tarjetas scrollable
                    self.compact_listbox = tk.Listbox(inner_frame, 
                                                     font=FONT_SMALL, 
                                                     bg=COLOR_BG_PANEL, 
                                                     fg=COLOR_TEXT_PRIMARY,
                                                     selectmode=tk.SINGLE,
                                                     height=4)  # 4 líneas máximo
                    self.compact_listbox.grid(row=0, column=0, sticky='nsew')
                    
                    # Scrollbar para la lista
                    scrollbar = tk.Scrollbar(inner_frame, orient=tk.VERTICAL)
                    scrollbar.grid(row=0, column=1, sticky='ns')
                    self.compact_listbox.config(yscrollcommand=scrollbar.set)
                    scrollbar.config(command=self.compact_listbox.yview)
                    
                    # Bind selection event
                    self.compact_listbox.bind('<<ListboxSelect>>', self._on_compact_card_select)
                
                # 3. POBLAR LA LISTA CON TARJETAS EXISTENTES
                self._populate_compact_cards_list()
            
        except Exception as e:
            print(f"  ⚠ Error rediseñando Open Cards: {e}")
            import traceback
            traceback.print_exc()
    
    def _populate_compact_cards_list(self):
        """Pobla la lista compacta usando la funcionalidad existente del CardExplorer"""
        try:
            if not hasattr(self, 'compact_listbox'):
                return
            
            # Limpiar lista existente
            self.compact_listbox.delete(0, tk.END)
            
            # NUEVO: Asegurar que el CardExplorer esté actualizado antes de poblar la lista
            if hasattr(self, 'card_explorer'):
                self.card_explorer.update_visual_states()
            
            # Usar la misma lógica que el CardExplorer para obtener tarjetas
            if hasattr(self, 'card_explorer') and hasattr(self.card_explorer, 'card_data'):
                cards_data = self.card_explorer.card_data
                active_session = self.session_manager.get_active_session()
                
                for i, card in enumerate(cards_data):
                    # Usar mismo formato que el CardExplorer
                    card_name = card.get('name', f'Card {i+1}')
                    card_type = card.get('type', 'Unknown')
                    session_id = card.get('session_id', '')
                    
                    # CORREGIDO: Verificar estado activo usando session_manager actual
                    is_active = active_session and session_id == active_session.session_id
                    
                    # Formato compacto para lista
                    display_text = f"{'▶ ' if is_active else '  '}{card_name} ({card_type})"
                    
                    # Agregar a la lista
                    self.compact_listbox.insert(tk.END, display_text)
                    
                    # Seleccionar tarjeta activa
                    if is_active:
                        self.compact_listbox.selection_set(i)
                        self.compact_listbox.see(i)
            
            # Fallback: usar session_manager directamente si CardExplorer no tiene datos
            elif hasattr(self, 'session_manager'):
                all_sessions = self.session_manager.get_all_sessions()
                active_session = self.session_manager.get_active_session()
                
                for i, session in enumerate(all_sessions):
                    is_active = active_session and session.session_id == active_session.session_id
                    display_text = f"{'▶ ' if is_active else '  '}{session.card_name} ({session.card_type})"
                    
                    self.compact_listbox.insert(tk.END, display_text)
                    
                    if is_active:
                        self.compact_listbox.selection_set(i)
                        self.compact_listbox.see(i)
            
        except Exception as e:
            print(f"  ⚠ Error poblando lista compacta: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_compact_card_select(self, event):
        """Maneja la selección de tarjetas en la lista compacta usando funcionalidad existente"""
        try:
            if not hasattr(self, 'compact_listbox'):
                return
            
            selection = self.compact_listbox.curselection()
            if not selection:
                return
            
            selected_index = selection[0]
            
            # Usar la funcionalidad existente del CardExplorer para cambiar de tarjeta
            if hasattr(self, 'card_explorer') and hasattr(self.card_explorer, 'card_data'):
                if selected_index < len(self.card_explorer.card_data):
                    card_data = self.card_explorer.card_data[selected_index]
                    session_id = card_data.get('session_id')
                    
                    # Usar el mismo método que el CardExplorer
                    if hasattr(self, 'on_card_select_from_explorer'):
                        self.on_card_select_from_explorer(session_id)
                    else:
                        # Fallback directo al session_manager
                        self.session_manager.set_active_session(session_id)
                        self.update_interface_for_active_session()
            
            # Fallback: usar session_manager directamente
            elif hasattr(self, 'session_manager'):
                all_sessions = self.session_manager.get_all_sessions()
                if selected_index < len(all_sessions):
                    session = all_sessions[selected_index]
                    self.session_manager.set_active_session(session.session_id)
                    self.update_interface_for_active_session()
            
            # CRÍTICO: Actualizar la lista compacta para mover la flechita
            self._populate_compact_cards_list()
            
        except Exception as e:
            print(f"  ⚠ Error seleccionando tarjeta compacta: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_text_tabs(self):
        """Crea las pestañas de texto para las tarjetas"""
        try:
            print("   Iniciando creación de pestañas de texto")
            
            # Limpiar pestañas existentes
            if hasattr(self, 'text_tabs_frame'):
                for widget in self.text_tabs_frame.winfo_children():
                    widget.destroy()
                print("   Pestañas existentes limpiadas")
            
            # DEBUG: Verificar que session_manager existe y tiene métodos
            if not hasattr(self, 'session_manager'):
                print("  ❌ session_manager no existe")
                return
            
            print(f"   session_manager encontrado: {type(self.session_manager)}")
            
            # Obtener todas las sesiones directamente
            try:
                all_sessions = self.session_manager.get_all_sessions()
                print(f"   get_all_sessions() retornó: {type(all_sessions)}, cantidad: {len(all_sessions) if all_sessions else 0}")
                
                if all_sessions:
                    for i, session in enumerate(all_sessions):
                        print(f"   Sesión {i}: {session.session_id} - {session.card_name} ({session.card_type})")
                else:
                    print("   all_sessions es None o vacío")
                    
            except Exception as e:
                print(f"  ❌ Error llamando get_all_sessions(): {e}")
                all_sessions = []
            
            # Obtener tarjetas del session manager
            cards = []
            if all_sessions:
                for session in all_sessions:
                    card_info = {
                        'id': session.session_id,
                        'name': session.card_name,
                        'card_type': session.card_type,
                        'memory_size': getattr(session, 'memory_size', '1K'),
                        'session': session
                    }
                    cards.append(card_info)
                    print(f"   Tarjeta añadida: {card_info['name']} ({card_info['card_type']})")
            
            print(f"   Total tarjetas procesadas: {len(cards)}")
            
            # Si no hay tarjetas, mostrar mensaje
            if not cards:
                if hasattr(self, 'text_tabs_frame'):
                    no_cards_label = tk.Label(self.text_tabs_frame, text="No cards opened",
                                             font=FONT_SMALL, bg=COLOR_BG_PANEL, fg=COLOR_TEXT_PRIMARY)
                    no_cards_label.pack(fill='x', padx=10, pady=10)
                    print("   Mensaje 'No cards opened' mostrado")
                self._update_navigation_buttons(0)
                return
            
            # Mostrar páginas de 4 tarjetas
            start_idx = self.current_tab_page * self.tabs_per_page
            end_idx = min(start_idx + self.tabs_per_page, len(cards))
            visible_cards = cards[start_idx:end_idx]
            
            print(f"   Mostrando tarjetas {start_idx}-{end_idx-1} de {len(cards)} total")
            
            # Crear botones de pestaña
            if hasattr(self, 'text_tabs_frame'):
                for i, card in enumerate(visible_cards):
                    card_name = card.get('name', f'Card{start_idx + i + 1}')
                    card_type = card.get('card_type', 'Unknown')
                    
                    # Texto simplificado para tabs
                    tab_text = f"{card_name} ({card_type})"
                    
                    # Crear botón de pestaña
                    tab_btn = tk.Button(self.text_tabs_frame, text=tab_text,
                                       command=lambda card_id=card['id']: self._select_card_tab(card_id),
                                       font=FONT_SMALL, bg=COLOR_BG_PANEL, fg=COLOR_TEXT_PRIMARY,
                                       relief=tk.RAISED, bd=1, anchor='w', height=1)
                    tab_btn.pack(fill='x', padx=2, pady=1)
                    
                    print(f"   Tab creado: {tab_text}")
            
            # Actualizar estado de botones de navegación
            self._update_navigation_buttons(len(cards))
            
            print("   Pestañas de texto creadas exitosamente")
            
        except Exception as e:
            print(f"  ❌ Error creando pestañas de texto: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_navigation_buttons(self, total_cards):
        """Actualiza el estado de los botones de navegación"""
        try:
            total_pages = (total_cards + self.tabs_per_page - 1) // self.tabs_per_page if total_cards > 0 else 0
            
            # Habilitar/deshabilitar botón anterior
            if hasattr(self, 'prev_btn'):
                self.prev_btn.configure(state='normal' if self.current_tab_page > 0 else 'disabled')
            
            # Habilitar/deshabilitar botón siguiente
            if hasattr(self, 'next_btn'):
                self.next_btn.configure(state='normal' if self.current_tab_page < total_pages - 1 else 'disabled')
                
        except Exception as e:
            print(f"  ⚠ Error actualizando botones de navegación: {e}")
    
    def _select_card_tab(self, card_id):
        """Selecciona una tarjeta desde las pestañas de texto"""
        try:
            # Cambiar a la sesión seleccionada
            self.session_manager.set_active_session(card_id)
            self.update_interface_for_active_session()
            print(f"   Tarjeta seleccionada desde pestaña: {card_id}")
        except Exception as e:
            print(f"  ⚠ Error seleccionando tarjeta: {e}")
    
    def _prev_cards(self):
        """Navegar a las tarjetas anteriores"""
        if self.current_tab_page > 0:
            self.current_tab_page -= 1
            self._create_text_tabs()
    
    def _next_cards(self):
        """Navegar a las siguientes tarjetas"""
        if hasattr(self, 'card_explorer') and hasattr(self.card_explorer, 'open_cards'):
            total_cards = len(self.card_explorer.open_cards)
            max_pages = (total_cards + self.tabs_per_page - 1) // self.tabs_per_page
            if self.current_tab_page < max_pages - 1:
                self.current_tab_page += 1
                self._create_text_tabs()
    
    def _expand_memory_content(self):
        """Expande Memory Content eliminando COMPLETAMENTE el espacio del cards_frame"""
        try:
            # SOLUCIÓN COMPLETA: Ocultar cards_frame Y eliminar su espacio reservado
            
            # PASO 1: Buscar y ocultar el cards_frame (padre de open_cards_frame)
            if hasattr(self, 'open_cards_frame'):
                cards_frame = self.open_cards_frame.master  # Este es el cards_frame
                
                # Guardar configuración original del cards_frame
                if not hasattr(self, '_original_cards_frame_width'):
                    self._original_cards_frame_width = cards_frame.cget('width')
                    self._original_cards_frame_grid = cards_frame.grid_info()
                    print(f"   Cards frame original width: {self._original_cards_frame_width}")
                
                # OCULTAR COMPLETAMENTE el cards_frame
                cards_frame.grid_forget()
                print("   Cards frame completamente ocultado (grid_forget)")
            
            # PASO 2: ELIMINAR COMPLETAMENTE el espacio de la columna 1 (cards_frame)
            # Esto es CRÍTICO - no solo ocultar el frame sino eliminar su espacio reservado
            self.root.grid_columnconfigure(0, weight=0, minsize=150)  # Commands mínimo
            self.root.grid_columnconfigure(1, weight=0, minsize=0)    # Cards frame = 0 ESPACIO
            self.root.grid_columnconfigure(2, weight=8, minsize=900)  # Memory Content MÁXIMA expansión
            self.root.grid_columnconfigure(3, weight=0, minsize=120)  # Pages/Physical Cards mínimo
            
            # PASO 3: Forzar que el Memory Content frame también se expanda completamente
            if hasattr(self, 'memory_content_frame'):
                # Asegurar que el frame de Memory Content ocupe todo el espacio disponible
                memory_info = self.memory_content_frame.grid_info()
                self.memory_content_frame.grid_configure(sticky='nsew')
                print("   Memory Content frame configurado para ocupar todo el espacio")
            
            # PASO 4: FORZAR actualización inmediata del layout
            self.root.update_idletasks()
            print("   Layout forzado a actualizarse inmediatamente")
            
            print("   Memory Content expandido al MÁXIMO eliminando COMPLETAMENTE el espacio de cards_frame")
        except Exception as e:
            print(f"  ⚠ Error expandiendo Memory Content: {e}")
            import traceback
            traceback.print_exc()
    
    def _expand_command_log(self):
        """Rebalancea el espacio entre Command Log y Actions en Small Screen Mode"""
        try:
            # Ajustar el grid del bottom_frame para balancear Command Log y Actions
            if hasattr(self, 'bottom_frame'):
                self.bottom_frame.grid_columnconfigure(0, weight=2, minsize=400)  # Command Log moderado
                self.bottom_frame.grid_columnconfigure(1, weight=0, minsize=0)    # Physical Cards completamente oculto
                self.bottom_frame.grid_columnconfigure(2, weight=1, minsize=280)  # Actions con más espacio
            print("   Command Log y Actions rebalanceados para Small Screen Mode")
        except Exception as e:
            print(f"  ⚠ Error rebalanceando Command Log y Actions: {e}")
            print(f"  ⚠ Error expandiendo Command Log: {e}")
    
    def _deactivate_small_screen_mode(self):
        """Desactiva el modo pantalla pequeña y restaura layout normal"""
        self.log("Small Screen Form Factor deactivated", "INFO")
        
        # Activar bandera para evitar conflictos en _apply_grid_layout durante la restauración
        self._in_post_small_screen_restoration = True
        
        # Desactivar flag para Small Screen Mode
        self.small_screen_mode = False
        
        try:
            # 0. RESTAURAR CONFIGURACIONES ORIGINALES DEL LAYOUT
            self._restore_original_layout_configurations()
            
            # 1. RESTAURAR BOTONES ACTIONS: 3 filas x 2 columnas
            self._restore_actions_layout()
            
            # 2. RESTAURAR PHYSICAL CARDS a su posición original
            self._restore_physical_cards()
            
            # 3. MOSTRAR CARD INFORMATION
            self._show_card_information()
            
            # 4. RESTAURAR OPEN CARDS original
            self._restore_open_cards()
            
            # 5. RESTAURAR MEMORY CONTENT tamaño original
            self._restore_memory_content()
            
            # 6. RESTAURAR COMMAND LOG tamaño original
            self._restore_command_log()
            
            # 7. APLICAR CONFIGURACIÓN ACTUAL DE CARDS_PER_ROW
            # Programar restauración específica con delay mínimo
            self.root.after(100, lambda: self._post_small_screen_layout_fix(self.current_cards_per_row))
            
            # 8. LIMPIAR CONFIGURACIONES GUARDADAS
            if hasattr(self, '_original_root_grid_config'):
                delattr(self, '_original_root_grid_config')
            
        except Exception as e:
            print(f"❌ Error restaurando layout normal: {e}")
    
    def _restore_original_layout_configurations(self):
        """Restaura las configuraciones originales del layout guardadas antes del Small Screen Mode"""
        try:
            print("   Restaurando configuraciones originales del layout")
            
            # NO restaurar configuración del grid principal (root) aquí
            # porque _apply_grid_layout() se encargará de configurarlo correctamente al final
            
            # Restaurar configuración del bottom_frame
            if hasattr(self, '_original_bottom_frame_config'):
                config = self._original_bottom_frame_config
                self.bottom_frame.grid_columnconfigure(0, weight=config['col0_weight'], minsize=config['col0_minsize'])
                self.bottom_frame.grid_columnconfigure(1, weight=config['col1_weight'], minsize=config['col1_minsize'])
                self.bottom_frame.grid_columnconfigure(2, weight=config['col2_weight'], minsize=config['col2_minsize'])
                delattr(self, '_original_bottom_frame_config')
                print(f"   bottom_frame restaurado: {config}")
            
            # Restaurar configuración del actions_container
            if hasattr(self, '_original_actions_config'):
                config = self._original_actions_config
                if hasattr(self, 'actions_container'):
                    self.actions_container.configure(width=config['width'], height=config['height'])
                delattr(self, '_original_actions_config')
                print(f"   actions_container restaurado: {config}")
            
            # Restaurar configuración del buttons_scrollable_frame grid
            if hasattr(self, '_original_buttons_grid_config'):
                config = self._original_buttons_grid_config
                self.buttons_scrollable_frame.grid_rowconfigure(0, weight=config['row0_weight'])
                self.buttons_scrollable_frame.grid_rowconfigure(1, weight=config['row1_weight'])
                self.buttons_scrollable_frame.grid_rowconfigure(2, weight=config['row2_weight'])
                self.buttons_scrollable_frame.grid_columnconfigure(0, weight=config['col0_weight'])
                self.buttons_scrollable_frame.grid_columnconfigure(1, weight=config['col1_weight'])
                # Remover configuración de tercera columna si existe
                self.buttons_scrollable_frame.grid_columnconfigure(2, weight=0)
                delattr(self, '_original_buttons_grid_config')
                print(f"   buttons grid restaurado: {config}")
            
            print("   Configuraciones originales restauradas exitosamente")
        except Exception as e:
            print(f"  ⚠ Error restaurando configuraciones originales: {e}")
            import traceback
            traceback.print_exc()
    
    def _restore_actions_layout(self):
        """Restaura los botones Actions a 3 filas x 2 columnas"""
        if hasattr(self, 'buttons_scrollable_frame'):
            try:
                # Reconfigurar grid: 3 filas x 2 columnas (original)
                self.buttons_scrollable_frame.grid_rowconfigure(0, weight=0)  # Fila 1
                self.buttons_scrollable_frame.grid_rowconfigure(1, weight=0)  # Fila 2
                self.buttons_scrollable_frame.grid_rowconfigure(2, weight=0)  # Fila 3
                self.buttons_scrollable_frame.grid_columnconfigure(0, weight=1)  # Columna 1
                self.buttons_scrollable_frame.grid_columnconfigure(1, weight=1)  # Columna 2
                self.buttons_scrollable_frame.grid_columnconfigure(2, weight=0)  # Remover columna 3
                
                # Obtener botones y reposicionarlos en layout original
                buttons = []
                for child in self.buttons_scrollable_frame.winfo_children():
                    if isinstance(child, tk.Button):
                        buttons.append(child)
                
                # Reposicionar en layout original (3x2)
                original_positions = [
                    (0, 0), (0, 1),  # Fila 1: SAVE LOG, CLEAR LOG
                    (1, 0), (1, 1),  # Fila 2: APDU's, SETTINGS
                    (2, 0), (2, 1)   # Fila 3: CREDITS, [CHANGE PSC si está habilitado]
                ]
                
                for i, button in enumerate(buttons[:6]):
                    if i < len(original_positions):
                        row, col = original_positions[i]
                        button.grid(row=row, column=col, padx=3, pady=3, sticky='ew')
                        # Restaurar tamaño original de botones
                        button.configure(width=12, height=1, padx=10, pady=10)
                
                print("   Botones Actions restaurados: 3 filas x 2 columnas")
            except Exception as e:
                print(f"  ⚠ Error restaurando botones Actions: {e}")
    
    def _restore_physical_cards(self):
        """Restaura Physical Cards y Pages a sus posiciones originales"""
        try:
            # PASO 1: Limpiar completamente el contenedor de small screen si existe
            if hasattr(self, '_small_screen_column3_container'):
                self._small_screen_column3_container.destroy()
                delattr(self, '_small_screen_column3_container')
            
            # PASO 2: Limpiar referencias a botones de small screen
            if hasattr(self, '_small_screen_page_buttons'):
                delattr(self, '_small_screen_page_buttons')
            
            # PASO 3: Asegurar que pages_frame está limpio y restaurarlo correctamente
            if hasattr(self, 'pages_frame'):
                self.pages_frame.grid_forget()  # Limpiar cualquier posición anterior
                self.pages_frame.grid(row=0, column=3, sticky='nsew', padx=(2, 5), pady=3)
            
            # PASO 4: Asegurar que physical_cards_frame está limpio y restaurarlo correctamente
            if hasattr(self, 'physical_cards_frame') and hasattr(self, 'bottom_frame'):
                self.physical_cards_frame.grid_forget()  # Limpiar cualquier posición anterior
                self.physical_cards_frame.grid(row=0, column=1, sticky='nsew', padx=(2, 2), pady=8)
            
            # PASO 5: Forzar actualización del layout
            self.root.update_idletasks()
            
        except Exception as e:
            self.log(f"Error en restauración: {e}")
            import traceback
            traceback.print_exc()
    
    def _show_card_information(self):
        """Muestra la sección Card Information"""
        if hasattr(self, 'card_info_frame'):
            try:
                self.card_info_frame.grid(row=2, column=0, sticky='nsew', padx=8, pady=(2, 8))
                print("   Card Information restaurado")
            except Exception as e:
                print(f"  ⚠ Error mostrando Card Information: {e}")
    
    def _restore_open_cards(self):
        """Restaura Open Cards a su posición y formato original"""
        try:
            # Ocultar lista compacta si existe
            if hasattr(self, 'compact_cards_frame'):
                self.compact_cards_frame.destroy()
                delattr(self, 'compact_cards_frame')
                print("   Lista compacta removida")
            
            # Ocultar pestañas de texto
            if hasattr(self, 'tabs_frame'):
                self.tabs_frame.destroy()
                delattr(self, 'tabs_frame')
            
            # Restaurar el cards_frame completo
            if hasattr(self, '_original_cards_frame_info') and hasattr(self, 'open_cards_frame'):
                cards_frame = self.open_cards_frame.master
                cards_frame.grid(**self._original_cards_frame_info)
                delattr(self, '_original_cards_frame_info')
                print("   Cards frame restaurado")
            
            print("   Open Cards tabs removidas - cards frame restaurado")
            
            print("   Open Cards restaurado")
        except Exception as e:
            print(f"  ⚠ Error restaurando Open Cards: {e}")
    
    def _restore_memory_content(self):
        """Restaura Memory Content y el cards_frame a su tamaño original"""
        try:
            # Restaurar el cards_frame que habíamos ocultado
            if hasattr(self, 'open_cards_frame'):
                cards_frame = self.open_cards_frame.master
                
                # Restaurar el cards_frame en su posición original
                if hasattr(self, '_original_cards_frame_grid'):
                    cards_frame.grid(**self._original_cards_frame_grid)
                    delattr(self, '_original_cards_frame_grid')
                
                # NO configurar width fijo - dejar que _apply_grid_layout lo controle
                print(f"   Cards frame restaurado sin width fijo")
            
            # Restaurar configuración original del grid principal
            self.root.grid_columnconfigure(2, weight=1, minsize=400)  # Memory content original
            
            print("   Memory Content y cards_frame restaurados")
        except Exception as e:
            print(f"  ⚠ Error restaurando Memory Content: {e}")
            import traceback
            traceback.print_exc()
    
    def _restore_command_log(self):
        """Restaura el tamaño original del Command Log"""
        try:
            if hasattr(self, 'bottom_frame'):
                # NO restaurar configuración del bottom_frame aquí - esto ya se hace en _restore_original_layout_configurations()
                # self.bottom_frame.grid_columnconfigure(0, weight=1, minsize=400)  # COMENTADO
                # self.bottom_frame.grid_columnconfigure(1, weight=0, minsize=120)  # COMENTADO  
                # self.bottom_frame.grid_columnconfigure(2, weight=0, minsize=220)  # COMENTADO
                pass
            
            print("   Command Log restaurado")
        except Exception as e:
            print(f"  ⚠ Error restaurando Command Log: {e}")
            import traceback
            traceback.print_exc()
            print("   Command Log restaurado")
        except Exception as e:
            print(f"  ⚠ Error restaurando Command Log: {e}")

    def create_apdu_9_button(self):
        """Crea un botón naranja permanente para APDU 9 cuando se habilita el acceso admin"""
        if hasattr(self, 'buttons_scrollable_frame') and self.buttons_scrollable_frame:
            # Detectar si estamos en Small Screen Mode
            is_small_screen = getattr(self, 'small_screen_mode', False)
            
            if is_small_screen:
                # Configuración compacta para Small Screen Mode - POSICIÓN CORREGIDA
                padx_val, pady_val = 3, 2
                width_val, height_val = 6, 1
                font_val = FONT_BOLD  # CORREGIDO: usar FONT_BOLD en lugar de FONT_NORMAL
                # Posición corregida para layout 2x3: row=1, column=2 (segunda fila, tercera columna)
                row_pos, col_pos = 1, 2
            else:
                # Configuración normal
                padx_val, pady_val = 10, 10
                width_val, height_val = 12, 1
                font_val = FONT_BOLD
                # Posición normal: row=2, column=1
                row_pos, col_pos = 2, 1
            
            # Crear botón APDU 9 con color naranja
            self.apdu_9_btn = tk.Button(self.buttons_scrollable_frame, text="CHANGE PSC", 
                                       bg='#FF8C42', fg='white',  # Color naranja
                                       font=font_val, relief=tk.RAISED, bd=2, 
                                       padx=padx_val, pady=pady_val,
                                       command=self.execute_apdu_9_dialog, width=width_val, height=height_val)
            self.apdu_9_btn.grid(row=row_pos, column=col_pos, padx=3, pady=3, sticky='ew')
            
            print(f"   Botón CHANGE PSC creado en posición ({row_pos},{col_pos}) - Small Screen: {is_small_screen}")
    
    def execute_apdu_9_dialog(self):
        """Ejecuta el diálogo de cambio de PSC físico independiente"""
        print("DEBUG: execute_apdu_9_dialog() called - Physical Card Dialog")
        if not self.apdu_9_enabled:
            messagebox.showerror("Access Denied", "Change Card PSC not available. Please enable via Settings.")
            return
        
        try:
            from .physical_card_dialogs import PhysicalCardChangePSCDialog
            dialog = PhysicalCardChangePSCDialog(self.root, self)
            self.log("Change Card PSC - Dialog opened")
        except Exception as e:
            self.log(f"Error opening Change Card PSC dialog: {e}")
            messagebox.showerror("Error", f"Error opening Change Card PSC dialog:\n{e}")

    def select_card_apdu(self):
        """APDU 1 - SELECT_CARD_TYPE - Power down/up y reset de tarjeta"""
        active_session = self.session_manager.get_active_session()
        
        if not active_session:
            messagebox.showerror("Error", CommonMessages.NO_CARD_SESSION)
            return
        
        # Mostrar diálogo de confirmación
        dialog = ConfirmationDialog(
            self.root,
            "Send APDU",
            "Send APDU - SELECT_CARD_TYPE ?",
            "question",
            compact=True
        )
        
        if not dialog.show():
            return  # Usuario canceló
        
        # Ejecutar Select Card en la sesión (esto genera el log compacto automáticamente)
        result = active_session.execute_select_card()
        
        # Actualizar display del log inmediatamente
        self.update_command_log_display()
        
        if result['success']:
            self.log(f"SELECT CARD executed successfully for '{active_session.card_name}'", "SUCCESS")
            # Actualizar interfaz
            self.update_interface_for_active_session()
        else:
            self.log(f"❌ SELECT CARD Error: {result.get('message', 'Unknown error')}")
            messagebox.showerror("Error", f"Select Card failed: {result.get('message', 'Unknown error')}")
    
    def read_error_counter(self):
        """APDU 6 - READ_PRESENTATION_ERROR_COUNTER - Lee contador de errores de presentación PSC"""
        active_session = self.session_manager.get_active_session()
        
        if not active_session:
            messagebox.showerror("Error", CommonMessages.NO_CARD_SESSION)
            return
        
        # Mostrar diálogo de confirmación
        dialog = ConfirmationDialog(
            self.root,
            "Send APDU",
            "Send APDU - READ_PRESENTATION_ERROR_COUNTER ?",
            "question",
            compact=True
        )
        
        if not dialog.show():
            return  # Usuario canceló
            
        try:
            # Ejecutar comando según manual - Corregido según tabla
            error_count = active_session.apdu_handler.error_counter
            
            # Generar APDU según tipo de tarjeta
            if active_session.memory_manager.card_type == CARD_TYPE_5542:
                apdu_cmd = "FF B1 00 00 04"  # SLE5542
            else:  # CARD_TYPE_5528
                apdu_cmd = "FF B1 00 00 03"  # SLE5528
            
            # Generar log compacto en el estilo correcto 
            active_session.add_to_log("APDU_SEND", "READ ERROR COUNTER", {
                'apdu': apdu_cmd
            })
            
            # Interpretar el contador según manual oficial
            if active_session.memory_manager.card_type == CARD_TYPE_5542:
                # SLE5542: Valores 07 (3), 03 (2), 01 (1), 00 (0)
                remaining = get_remaining_attempts_from_error_counter(error_count, CARD_TYPE_5542)
                if error_count == 0x07:
                    status_msg = f"Last verification correct (0x07 = {remaining} attempts available)"
                    counter_status = "UNLOCKED"
                elif error_count == 0x00:
                    status_msg = "Password LOCKED (0x00 = exceeded maximum retries)"
                    counter_status = "LOCKED"
                elif error_count in [0x03, 0x01]:
                    status_msg = f"Last verification FAILED (0x{error_count:02X} = {remaining} attempts remaining)"
                    counter_status = "FAILED"
                else:
                    status_msg = f"Unknown counter value: 0x{error_count:02X}"
                    counter_status = "UNKNOWN"
            else:
                # SLE5528: mantener lógica original
                if error_count == 0x7F:
                    status_msg = "Last verification correct (7 attempts available)"
                    counter_status = "UNLOCKED"
                elif error_count == 0x00:
                    status_msg = "Password LOCKED (exceeded maximum retries)"
                    counter_status = "LOCKED"
                elif error_count in [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07]:
                    remaining = get_remaining_attempts_from_error_counter(error_count, CARD_TYPE_5528)
                    status_msg = f"Last verification FAILED (0x{error_count:02X} = {remaining} attempts remaining)"
                    counter_status = "FAILED"
                else:
                    status_msg = f"Unknown counter value: 0x{error_count:02X}"
                    counter_status = "UNKNOWN"
            
            # Formatear respuesta según manual oficial
            if active_session.memory_manager.card_type == CARD_TYPE_5528:
                # SLE5528: Response format: ERRCNT DUMMY 1 DUMMY 2 SW1 SW2
                response_data = f"{error_count:02X} 00 00"
                sw_response = "90 00"
            else:
                # SLE5542: Response format: ERRCNT DUMMY 1 DUMMY 2 DUMMY 3 SW1 SW2
                # SW2 debe contener el valor del error counter
                response_data = f"{error_count:02X} 00 00 00"
                sw_response = f"90 {error_count:02X}"
            
            active_session.add_to_log("APDU_RESPONSE", f"Data: {response_data} - {status_msg}", {
                'sw': sw_response,
                'response_data': response_data,
                'sw_only': sw_response,
                'error_count': f"0x{error_count:02X}",
                'status': counter_status
            })
            
            # Actualizar display del log inmediatamente
            self.update_command_log_display()
            
        except Exception as e:
            error_msg = f"Error reading presentation error counter: {str(e)}"
            messagebox.showerror("Error", error_msg)
    
    def reset_error_counter(self):
        """Resetea el contador de errores de la tarjeta al estado original"""
        active_session = self.session_manager.get_active_session()
        
        if not active_session:
            self.safe_messagebox("error", "Error", CommonMessages.NO_CARD_SESSION)
            return
        
        try:
            # Resetear el contador de errores según el tipo de tarjeta
            if active_session.memory_manager.card_type == CARD_TYPE_5528:
                original_count = "0x7F"  # SLE5528 usa secuencia de bits comenzando con 0x7F
                attempts_text = "7 attempts (bit sequence)"
                card_type_name = "SLE5528"
            else:
                original_count = "0x07"  # SLE5542 usa secuencia 07-03-01-00
                attempts_text = "3 attempts (0x07)"
                card_type_name = "SLE5542"
            
            # CRÍTICO: Resetear el contador interno en ambos lugares ANTES de verificar estados
            if active_session.memory_manager.card_type == CARD_TYPE_5528:
                # Para SLE5528: resetear al estado inicial (índice 1, valor 0x7F)
                if hasattr(active_session.apdu_handler, 'error_counter_index'):
                    active_session.apdu_handler.error_counter_index = 1
                active_session.apdu_handler.error_counter = ERROR_COUNTER_SEQUENCE_5528[1]  # 0x7F
                active_session.memory_manager.error_counter = ERROR_COUNTER_SEQUENCE_5528[1]
            else:
                # Para SLE5542: resetear a índice 0 (valor 0x07 = 3 intentos)
                if hasattr(active_session.apdu_handler, 'error_counter_index'):
                    active_session.apdu_handler.error_counter_index = 0
                active_session.apdu_handler.error_counter = ERROR_COUNTER_SEQUENCE_5542[0]  # 0x07
                active_session.memory_manager.error_counter = ERROR_COUNTER_SEQUENCE_5542[0]
            
            # Desbloquear la tarjeta explícitamente (aunque no se usa mucho, por compatibilidad)
            active_session.is_blocked = False
            
            # Actualizar el error counter en la memoria visible (para SLE5528)
            active_session.memory_manager._update_error_counter_in_memory()
            
            # Resetear el estado de verificación PSC para permitir operaciones que lo requieran
            active_session.psc_verified = False
            
            # Verificar que la tarjeta ya no esté bloqueada
            is_still_blocked = active_session.apdu_handler.is_card_blocked()
            status_text = "UNLOCKED" if not is_still_blocked else "STILL_BLOCKED"
            
            # CRÍTICO: Actualizar el estado de la aplicación después del reset
            if not is_still_blocked:
                # Forzar actualización del estado de la aplicación
                new_state = active_session.get_current_app_state()
                self.current_app_state = new_state
            
            # Log de la operación con verificación de estado
            active_session.add_to_log("SYSTEM", f"✅ RESET ERROR COUNTER: Error Counter set to {original_count} ({attempts_text}) for {card_type_name} and card {status_text}", {
                'reset_value': original_count,
                'attempts_info': attempts_text,
                'card_type': card_type_name,
                'status': status_text,
                'is_blocked_after_reset': is_still_blocked,
                'new_app_state': self.current_app_state
            })
            
            # Actualizar la interfaz
            self.update_button_states()
            self.update_info_panels()  # Actualizar panel de Remaining Errors
            self.update_card_display()  # CRÍTICO: Actualizar HEX CONTENT y Card Information
            self.update_command_log_display()
            
            # Mensaje de confirmación limpio
            status_msg = "unlocked and ready for all operations" if not is_still_blocked else "may still be blocked - check error counter"
            success_message = f"Error counter has been reset to {original_count} ({attempts_text}).\nCard is now {status_msg}."
            
            self.safe_messagebox("info", "Reset Successful", success_message)
            
        except Exception as e:
            error_msg = f"Error resetting error counter: {str(e)}"
            self.safe_messagebox("error", "Error", error_msg)
        
    def read_protection_bits(self):
        """APDU 7 - READ_PROTECTION_BITS - Lee bits de protección para los primeros 32 bytes"""
        active_session = self.session_manager.get_active_session()
        
        if not active_session:
            messagebox.showerror("Error", CommonMessages.NO_CARD_SESSION)
            return
        
        # Mostrar diálogo de confirmación
        dialog = ConfirmationDialog(
            self.root,
            "Send APDU",
            "Send APDU - READ_PROTECTION_BITS ?",
            "question",
            compact=True
        )
        
        if not dialog.show():
            return  # Usuario canceló
            
        try:
            # Obtener bits de protección reales del memory manager
            prot_bytes = active_session.memory_manager.get_protection_bits()
            
            # Generar APDU según tipo de tarjeta - Corregido según tabla
            if active_session.memory_manager.card_type == CARD_TYPE_5542:
                apdu_cmd = "FF B2 00 00 04"  # SLE5542
            else:  # CARD_TYPE_5528  
                apdu_cmd = "FF B2 00 80 16"  # SLE5528
            
            # Generar log compacto en el estilo correcto
            active_session.add_to_log("APDU_SEND", "READ PROTECTION BITS", {
                'apdu': apdu_cmd
            })
            
            # Formatear respuesta según manual
            response_data = " ".join([f"{b:02X}" for b in prot_bytes])
            
            # Interpretar bits de protección (P1-P32)
            protected_addresses = []
            writable_addresses = []
            for byte_idx in range(4):
                for bit_idx in range(8):
                    address = byte_idx * 8 + bit_idx
                    if address < 32:  # Solo primeros 32 bytes
                        bit_value = (prot_bytes[byte_idx] >> bit_idx) & 1
                        if bit_value == 0:  # 0 = protegido
                            protected_addresses.append(f"0x{address:02X}")
                        else:  # 1 = escribible
                            writable_addresses.append(f"0x{address:02X}")
            
            # Crear resumen para el log
            if protected_addresses:
                summary = f"Protected: {', '.join(protected_addresses[:8])}{'...' if len(protected_addresses) > 8 else ''}"
            else:
                summary = "All addresses writable"
            
            # Formatear respuesta según manual oficial
            if active_session.memory_manager.card_type == CARD_TYPE_5528:
                # SLE5528: Response format: PROT 1 … PROT L SW1 SW2 (variable length)
                response_data = response_data
                sw_response = "90 00"
            else:
                # SLE5542: Response format: PROT 1 PROT 2 PROT 3 PROT 4 SW1 SW2 (4 bytes)
                response_data = response_data
                sw_response = "90 00"
            
            active_session.add_to_log("APDU_RESPONSE", f"Data: {response_data} - {summary}", {
                'sw': sw_response,
                'response_data': response_data,
                'sw_only': sw_response,
                'protection_summary': summary
            })
            
            # Actualizar display del log inmediatamente
            self.update_command_log_display()
            
            # Mostrar ventana de Protection Bits Breakdown con tipo de tarjeta
            card_type = active_session.memory_manager.card_type
            ProtectionBitsDialog(self.root, prot_bytes, card_type, active_session.memory_manager)
            
        except Exception as e:
            error_msg = f"Error reading protection bits: {str(e)}"
            messagebox.showerror("Error", error_msg)
        
    def present_psc(self):
        """APDU 3 - PRESENT PSC - Abre diálogo para presentar PSC"""
        active_session = self.session_manager.get_active_session()
        
        if not active_session:
            messagebox.showerror("Error", CommonMessages.NO_CARD_SESSION)
            return
        
        # Obtener tipo de tarjeta de la sesión activa
        card_type = active_session.memory_manager.card_type
        PresentPSCDialog(self.root, self._execute_present_psc, card_type)
    
    def _execute_present_psc(self, psc_input):
        """Ejecuta la presentación del PSC"""
        active_session = self.session_manager.get_active_session()
        
        if not active_session:
            return
            
        try:
            # Convertir PSC a bytes
            psc_parts = psc_input.upper().replace(' ', '').replace('-', '')
            if len(psc_parts) % 2 != 0:
                raise ValueError("PSC must have even number of hex digits")
            
            psc_bytes = [int(psc_parts[i:i+2], 16) for i in range(0, len(psc_parts), 2)]
            
            # Ejecutar Present PSC en la sesión (esto genera el log compacto automáticamente)
            result = active_session.execute_present_psc(psc_bytes)
            error_counter = active_session.apdu_handler.error_counter
            
            # Actualizar display del log inmediatamente
            self.update_command_log_display()
            
            if result['success']:
                messagebox.showinfo("Success", "PSC verified - Write access enabled")
                self.log(f"PSC presented successfully for '{active_session.card_name}'", "SUCCESS")
            else:
                # Mostrar estado detallado del error counter
                if error_counter == 0x00:
                    messagebox.showerror("Error", "Password LOCKED - Card is permanently blocked")
                    self.log(f"CARD BLOCKED: '{active_session.card_name}' permanently blocked - only SELECT/READ allowed", "ERROR")
                else:
                    # Formatear intentos restantes según tipo de tarjeta
                    if active_session.card_type == CARD_TYPE_5528:
                        # SLE5528: mostrar hex y decimal
                        remaining_attempts = get_remaining_attempts_from_error_counter(error_counter, CARD_TYPE_5528)
                        attempts_display = f"{error_counter:02X} ({remaining_attempts})"
                    else:
                        # SLE5542: mostrar solo decimal
                        attempts_display = str(error_counter)
                    
                    messagebox.showerror("Error", f"PSC verification failed - {attempts_display} attempts remaining")
                
            # Actualizar estado de la aplicación (crucial para habilitar APDUs de escritura)
            self.current_app_state = active_session.get_current_app_state()
            
            # Actualizar todos los elementos de la interfaz
            self.update_button_states()
            self.update_info_panels()
            
            # Para PRESENT PSC, necesitamos actualizar toda la memoria ya que el PSC puede cambiar su visibilidad
            self.update_card_display()  # Mantener completo para PRESENT PSC
            self.update_command_log_display()
                
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid PSC format: {str(e)}")
    
    def change_psc_dialog(self):
        """Abre diálogo para cambiar PSC"""
        print("DEBUG: change_psc_dialog() called - Simulator Dialog")
        active_session = self.session_manager.get_active_session()
        
        if not active_session:
            messagebox.showerror("Error", CommonMessages.NO_CARD_SESSION)
            return
        
        # Obtener tipo de tarjeta de la sesión activa
        card_type = active_session.memory_manager.card_type
        ChangePSCDialog(self.root, self.change_psc, card_type)
    
    def change_psc(self, new_psc):
        """Cambia el PSC escribiendo en las direcciones correspondientes"""
        active_session = self.session_manager.get_active_session()
        
        if not active_session:
            messagebox.showerror("Error", CommonMessages.NO_CARD_SESSION)
            return
            
        if not active_session.psc_verified:
            messagebox.showerror("Error", CommonMessages.PSC_NOT_VERIFIED)
            return
        
        try:
            # Convertir PSC de string a bytes
            psc_bytes = [int(b, 16) for b in new_psc.split()]
            
            # Validar según el tipo de tarjeta
            card_type = active_session.memory_manager.card_type
            if card_type == CARD_TYPE_5542:
                expected_bytes = 3
                card_name = "SLE5542"
                format_example = "FF FF FF"
            else:  # CARD_TYPE_5528
                expected_bytes = 2
                card_name = "SLE5528"  
                format_example = "FF FF"
            
            if len(psc_bytes) != expected_bytes:
                messagebox.showerror("Error", f"PSC must be exactly {expected_bytes} bytes for {card_name}")
                return
            
            # Ejecutar cambio de PSC usando la función específica (esto genera el log compacto automáticamente)
            result = active_session.execute_change_psc(psc_bytes)
            
            # Actualizar display del log inmediatamente
            self.update_command_log_display()
            
            if result['success']:
                self.log(f"PSC changed to: {new_psc} for '{active_session.card_name}'", "SUCCESS")
                self.update_card_display()  # Actualizar display para mostrar cambios
                self.update_button_states()
                messagebox.showinfo("Success", f"PSC changed successfully to: {new_psc}")
            else:
                messagebox.showerror("Error", result.get('message', 'PSC change failed'))
                self.log(f"PSC change failed: {result.get('message', 'Unknown error')}", "ERROR")
            
        except ValueError:
            # Error message específico del tipo de tarjeta
            card_type = active_session.memory_manager.card_type
            format_example = "FF FF FF" if card_type == CARD_TYPE_5542 else "FF FF"
            messagebox.showerror("Error", f"Invalid PSC format. Use format: {format_example}")
            self.log("PSC change failed: Invalid format", "ERROR")
        except Exception as e:
            messagebox.showerror("Error", f"PSC change failed: {str(e)}")
            self.log(f"PSC change error: {str(e)}", "ERROR")
    
    def read_memory_dialog(self):
        """Abre diálogo para leer memoria"""
        ReadMemoryDialog(self.root, self.read_memory, self.session_manager)
    
    def read_memory(self, address, length):
        """Lee memoria de la tarjeta usando el sistema de sesiones"""
        active_session = self.session_manager.get_active_session()
        
        if not active_session:
            self.safe_messagebox("error", "Error", CommonMessages.NO_CARD_SESSION)
            return
        
        # Validar parámetros de entrada
        if address < 0:
            self.safe_messagebox("error", "Error", "Address cannot be negative")
            return
            
        if length <= 0:
            self.safe_messagebox("error", "Error", "Length must be positive")
            return
            
        # Limitar la longitud a 255 bytes máximo (0xFF) para APDU
        if length > 255:
            self.safe_messagebox("error", "Error", 
                               f"Length cannot exceed 0xFF (255 bytes)\n"
                               f"Requested: 0x{length:02X} ({length} bytes), Maximum allowed: 0xFF (255 bytes)")
            return
        
        # Determinar tamaño máximo según tipo de tarjeta
        card_type = active_session.memory_manager.card_type
        max_memory_size = MEMORY_SIZE_5528 if card_type == CARD_TYPE_5528 else MEMORY_SIZE_5542
        
        # Validar que la dirección inicial esté dentro del rango
        if address >= max_memory_size:
            self.safe_messagebox("error", "Error", 
                               f"Start address 0x{address:02X} ({address}) exceeds card memory size\n"
                               f"Maximum address for this card: 0x{max_memory_size-1:02X} ({max_memory_size-1})")
            return
        
        # Validar que la operación de lectura no exceda el tamaño de la tarjeta
        end_address = address + length - 1
        if end_address >= max_memory_size:
            max_length = max_memory_size - address
            self.safe_messagebox("error", "Error", 
                               f"Read length 0x{length:02X} ({length} bytes) exceeds available memory\n"
                               f"Starting at address 0x{address:02X}, maximum 0x{max_length:02X} ({max_length} bytes) can be read\n"
                               f"End address would be 0x{end_address:02X}, but card memory ends at 0x{max_memory_size-1:02X}")
            return
            
        try:
            result = active_session.execute_read_memory(address, length)
            
            if result['success']:
                # El resultado viene del APDU handler, usar el campo 'response' 
                data = result.get('response', [])
                if data:
                    # Formatear salida profesional tipo terminal
                    self._display_read_memory_result(address, length, data)
                else:
                    self.log(f"Read memory from {address:02X}: No data returned")
                    messagebox.showinfo("Memory Read", "No data read")
                
                self.update_card_display()
                self.update_button_states()
            else:
                messagebox.showerror("Error", result.get('message', 'Read operation failed'))
                self.log(f"Read memory failed: {result.get('message', 'Unknown error')}")
        except Exception as e:
            messagebox.showerror("Error", f"Read operation failed: {str(e)}")
            self.log(f"Read memory error: {str(e)}")
    
    def _display_read_memory_result(self, start_address, length, data):
        """Muestra el resultado del Read Memory en formato profesional usando el nuevo sistema de logging"""
        active_session = self.session_manager.get_active_session()
        if not active_session:
            return
        
        # Generar APDU comando según el tipo de tarjeta
        if active_session.memory_manager.card_type == CARD_TYPE_5528:
            # Para SLE5528: FF B0 MSB LSB MEM_L
            msb = (start_address >> 8) & 0xFF
            lsb = start_address & 0xFF
            apdu_cmd = f"FF B0 {msb:02X} {lsb:02X} {length:02X}"
        else:
            # Para SLE5542: FF B0 00 address MEM_L
            apdu_cmd = f"FF B0 00 {start_address:02X} {length:02X}"
        
        # Usar SOLO el nuevo sistema de logging compacto
        active_session.add_to_log("APDU_SEND", "READ MEMORY", {
            'apdu': apdu_cmd
        })
        
        # Formatear datos para el log según el manual oficial
        if active_session.memory_manager.card_type == CARD_TYPE_5528:
            # SLE5528 (1K): Response format: BYTE 1 … BYTE N SW1 SW2
            data_hex = " ".join([f"{b:02X}" for b in data])
            response_data = data_hex
            sw_response = "90 00"
        else:
            # SLE5542 (256B): Response format: BYTE 1 … BYTE N PROT 1 PROT 2 PROT 3 PROT 4 SW1 SW2
            data_hex = " ".join([f"{b:02X}" for b in data])
            # Para 256B, agregar 4 bytes de protección (simulados como FF FF FF FF)
            prot_bytes = "FF FF FF FF"
            response_data = f"{data_hex} {prot_bytes}"
            sw_response = "90 00"
        
        # Generar contenido ASCII desde los bytes de datos
        from src.core.code_improvements import safe_hex_to_ascii
        ascii_content = "".join([safe_hex_to_ascii(f"{b:02X}") for b in data])
        
        # Log compacto mostrando los datos por separado del SW, con ASCII incluido
        active_session.add_to_log("APDU_RESPONSE", f"Data: {response_data}", {
            'sw': sw_response,
            'data_length': length,
            'address': f"0x{start_address:02X}",
            'response_data': response_data,
            'ascii_data': ascii_content,  # Agregar contenido ASCII
            'sw_only': sw_response
        })
        
        # Actualizar display del log
        self.update_command_log_display()
        
        # Mostrar también en messagebox con todo el contenido leído
        summary = f"Read Memory Result:\n"
        summary += f"Address: 0x{start_address:02X}\n"
        summary += f"Length: {length} bytes\n"
        summary += f"Status: Success (90 00)\n\n"
        summary += "Data:\n"
        
        # Mostrar todos los datos leídos sin direcciones (solo el contenido hexadecimal)
        idx = 0
        while idx < len(data):
            row_bytes = min(16, len(data) - idx)
            row_data = data[idx:idx + row_bytes]
            hex_str = " ".join(f"{b:02X}" for b in row_data)
            summary += f"{hex_str}\n"
            idx += row_bytes
        
        self.safe_messagebox("info", "Read Memory", summary)
    
    def write_memory_dialog(self):
        """Abre diálogo para escribir memoria"""
        WriteMemoryDialog(self.root, self.write_memory, self.session_manager)
    
    def write_memory(self, address, data_str):
        """Escribe datos en memoria usando el sistema de sesiones"""
        active_session = self.session_manager.get_active_session()
        
        if not active_session:
            self.safe_messagebox("error", "Error", CommonMessages.NO_CARD_SESSION)
            return
            
        if not active_session.psc_verified:
            self.safe_messagebox("error", "Error", CommonMessages.PSC_NOT_VERIFIED)
            return
        
        try:
            # Validación adicional en el procesamiento
            hex_values = data_str.split()
            data_bytes = []
            
            for hex_val in hex_values:
                if not hex_val.strip():
                    continue  # Saltar valores vacíos
                    
                byte_value = int(hex_val, 16)
                if byte_value > 255:
                    raise ValueError(f"Byte value {byte_value} (0x{hex_val}) exceeds maximum byte value (255/0xFF)")
                data_bytes.append(byte_value)
            
            if not data_bytes:
                raise ValueError("No valid hex bytes provided")
            
            # Ejecutar Write Memory en la sesión (esto genera el log compacto automáticamente)
            result = active_session.execute_write_memory(address, data_bytes)
            data_hex = " ".join([f"{b:02X}" for b in data_bytes])
            
            # Actualizar display del log inmediatamente
            self.update_command_log_display()
            
            if result['success']:
                self.update_card_display()
                self.update_button_states()
                
                # Mensaje simple de éxito
                success_msg = f"Memory written successfully\nAddress: 0x{address:02X}\nData: {data_hex}"
                self.safe_messagebox("info", "Write Memory Success", success_msg)
            else:
                # Error - la validación del diálogo ya debería haber capturado problemas de protección
                # Este error podría ser por otros motivos (PSC no verificado, etc.)
                error_message = result.get('message', 'Write operation failed')
                self.safe_messagebox("error", "Write Memory Error", f"Error: {error_message}")
                self.log(f"Write memory failed: {error_message}")
        except ValueError as e:
            error_msg = str(e)
            if "exceeds maximum" in error_msg:
                self.safe_messagebox("error", "Error", f"Invalid hex data:\n{error_msg}")
            else:
                self.safe_messagebox("error", "Error", "Invalid hex data format.\nUse space-separated hex bytes (00-FF)")
            self.log(f"Write memory failed: {error_msg}")
        except Exception as e:
            self.safe_messagebox("error", "Error", f"Write operation failed: {str(e)}")
            self.log(f"Write memory error: {str(e)}")
    
    def save_card_dialog(self):
        """Abre diálogo para guardar tarjeta"""
        active_session = self.session_manager.get_active_session()
        
        if not active_session:
            InfoDialog(self.root, "Error", CommonMessages.NO_CARD_SESSION, "error")
            return
        
        def handle_save(filepath):
            success, message = self.session_manager.save_session_to_file(active_session.session_id, filepath)
            if success:
                self.log(f"Card '{active_session.card_name}' saved to: {filepath}")
                InfoDialog(self.root, "Success", "Card saved successfully", "success")
            else:
                InfoDialog(self.root, "Error", f"Save failed: {message}", "error")
        
        # Mostrar diálogo personalizado centrado
        SaveCardDialog(self.root, active_session.card_name, handle_save)
    
    def close_card(self):
        """Cierra la tarjeta activa usando diálogo personalizado"""
        active_session = self.session_manager.get_active_session()
        
        if not active_session:
            InfoDialog(self.root, "Warning", CommonMessages.NO_CARD_SESSION, "warning")
            return
        
        # Confirmar cierre con diálogo personalizado
        dialog = ConfirmationDialog(
            self.root,
            "Close Card",
            f"Close card '{active_session.card_name}'?\n\nUnsaved changes will be lost.",
            "question"
        )
        
        if dialog.show():
            card_name = active_session.card_name
            success = self.session_manager.close_session(active_session.session_id)
            
            if success:
                self.update_cards_list()
                # NO actualizar automáticamente a otra sesión - usuario debe seleccionar manualmente
                # Solo actualizar interfaz si no queda ninguna tarjeta
                if not self.session_manager.has_active_session():
                    self.update_interface_for_active_session()
                else:
                    # Limpiar la visualización pero mantener las tarjetas disponibles
                    self.clear_memory_display()
                    self.clear_command_log_display()
                    self.current_app_state = AppStates.INITIAL
                    self.update_button_states()
                    self.update_page_buttons()
                    
                self.log(f"Card '{card_name}' closed")
            else:
                InfoDialog(self.root, "Error", "Failed to close card session", "error")
    
    def clear_card(self):
        """Limpia la tarjeta activa (resetea a estado de fábrica) usando diálogo personalizado"""
        active_session = self.session_manager.get_active_session()
        
        if not active_session:
            InfoDialog(self.root, "Error", CommonMessages.NO_CARD_SESSION, "error")
            return
        
        # Confirmar limpieza con diálogo personalizado
        dialog = ConfirmationDialog(
            self.root,
            "Clear Card",
            f"Reset card '{active_session.card_name}' to factory state?\n\nAll data will be lost.",
            "warning"
        )
        
        if dialog.show():
            # Reinicializar memoria
            active_session.memory_manager.initialize_memory(active_session.card_type)
            active_session.card_selected = False
            active_session.psc_verified = False
            # Resetear error counter según tipo de tarjeta
            if active_session.card_type == CARD_TYPE_5542:
                active_session.apdu_handler.error_counter_index = 0  # Resetear índice a 0
                active_session.apdu_handler.error_counter = ERROR_COUNTER_SEQUENCE_5542[0]  # 0x07 (3 attempts)
            else:  # CARD_TYPE_5528
                active_session.apdu_handler.error_counter_index = 1  # Resetear índice a 1
                active_session.apdu_handler.error_counter = ERROR_COUNTER_SEQUENCE_5528[1]  # 0x7F (7 attempts)
            
            self.update_interface_for_active_session()
            # Solo usar self.log() para evitar duplicación
            self.log(f"Card '{active_session.card_name}' cleared - Reset to factory state")
    
    def write_protect_dialog(self):
        """Abre diálogo para protección contra escritura"""
        WriteProtectDialog(self.root, self.write_protect, self.session_manager)
    
    def write_protect(self, address, data_pattern):
        """APDU 8 - WRITE_PROTECTION_MEMORY_CARD - Protege direcciones por comparación de contenido"""
        active_session = self.session_manager.get_active_session()
        
        if not active_session:
            messagebox.showerror("Error", CommonMessages.NO_CARD_SESSION)
            return
            
        if not active_session.psc_verified:
            messagebox.showerror("Error", CommonMessages.PSC_NOT_VERIFIED)
            return
        
        try:
            # Convertir patrón de datos a bytes
            pattern_bytes = []
            for hex_byte in data_pattern.split():
                pattern_bytes.append(int(hex_byte, 16))
            
            pattern_length = len(pattern_bytes)
            
            # Validar que no exceda los límites de memoria
            memory_size = active_session.memory_manager.get_memory_size()
            if address + pattern_length > memory_size:
                raise ValueError(f"Pattern extends beyond card memory (max address: 0x{memory_size-1:02X})")
            
            # RESTRICCIÓN ESPECÍFICA PARA SLE5542 (256B): Solo las dos primeras filas (0x00-0x1F)
            if active_session.card_type == CARD_TYPE_5542:
                max_protectable_address = 0x1F  # Solo las dos primeras filas
                if address > max_protectable_address:
                    raise ValueError(f"SLE5542 cards can only protect addresses 0x00-0x{max_protectable_address:02X} (first two rows)")
                if address + pattern_length - 1 > max_protectable_address:
                    max_length = max_protectable_address - address + 1
                    raise ValueError(f"Pattern extends beyond protectable area for SLE5542\n"
                                   f"Maximum protectable address: 0x{max_protectable_address:02X}\n"
                                   f"Starting at 0x{address:02X}, maximum pattern length: {max_length} bytes")
            
            # Leer contenido actual de la tarjeta en el rango especificado
            current_data = active_session.memory_manager.read_memory(address, pattern_length)
            if not current_data:
                raise ValueError(f"Cannot read data starting at address 0x{address:02X}")
            
            # Comparar contenido actual con el patrón
            protected_addresses = []
            for i, (current_byte, pattern_byte) in enumerate(zip(current_data, pattern_bytes)):
                current_addr = address + i
                if current_byte == pattern_byte:
                    # Coincidencia encontrada - proteger esta dirección
                    active_session.memory_manager.set_protection_bit(current_addr)
                    protected_addresses.append(current_addr)
            
            # Generar log detallado con APDU corregido según tipo de tarjeta
            pattern_str = ' '.join(f"{b:02X}" for b in pattern_bytes)
            current_str = ' '.join(f"{b:02X}" for b in current_data)
            
            # Generar APDU según tipo de tarjeta - Corregido según tabla
            if active_session.memory_manager.card_type == CARD_TYPE_5542:
                # SLE5542: FF D1 00 @ #B
                apdu_cmd = f"FF D1 00 {address:02X} {pattern_length:02X} {pattern_str}"
            else:  # CARD_TYPE_5528
                # SLE5528: FF D1 #P @ #B (usar MSB/LSB para dirección)
                msb = (address >> 8) & 0xFF
                lsb = address & 0xFF
                apdu_cmd = f"FF D1 {msb:02X} {lsb:02X} {pattern_length:02X} {pattern_str}"
            
            active_session.add_to_log("APDU_SEND", "WRITE PROTECTION", {
                'apdu': apdu_cmd,
                'description': f"Compare pattern with current content"
            })
            
            if protected_addresses:
                protected_str = ', '.join(f"0x{addr:02X}" for addr in protected_addresses)
                active_session.add_to_log("APDU_RESPONSE", 
                    f"Protection applied to {len(protected_addresses)} matching addresses: {protected_str}", {
                    'sw': "90 00",
                    'details': f"Pattern: {pattern_str} | Current: {current_str}"
                })
                
                # Actualizar display del log y memoria
                self.update_command_log_display()
                self.update_card_display()
                
                messagebox.showinfo("Write Protection Complete", 
                    f"Protected {len(protected_addresses)} addresses where content matched:\n{protected_str}\n\n"
                    f"Pattern: {pattern_str}\n"
                    f"Current: {current_str}")
            else:
                active_session.add_to_log("APDU_RESPONSE", 
                    "No addresses protected - no content matches found", {
                    'sw': "90 00",
                    'details': f"Pattern: {pattern_str} | Current: {current_str}"
                })
                
                # Actualizar display del log
                self.update_command_log_display()
                
                messagebox.showinfo("Write Protection Complete", 
                    f"No addresses were protected.\n\n"
                    f"Pattern: {pattern_str}\n"
                    f"Current: {current_str}\n\n"
                    f"No matching content found in the specified range.")
            
        except Exception as e:
            error_msg = f"Write protection failed: {str(e)}"
            active_session.add_to_log("ERROR", error_msg)
            self.update_command_log_display()
            messagebox.showerror("Error", error_msg)
    
    def user_config_dialog(self):
        """Abre diálogo de configuración de usuario"""
        from src.utils.user_config import user_config_manager
        # Usar la configuración global persistente
        current_info = user_config_manager.user_info
        UserConfigDialog(self.root, self.set_user_config, current_info)
    
    def set_user_config(self, user_info):
        """Configura información de usuario"""
        from src.utils.user_config import user_config_manager
        
        # Guardar en la configuración global persistente
        user_config_manager.user_info = user_info
        
        # También actualizar la sesión activa si existe
        active_session = self.session_manager.get_active_session()
        if active_session:
            active_session.user_info = user_info
            active_session.save_session_state()
            # Solo usar self.log() para evitar duplicación
            self.log(f"User configuration updated for '{active_session.card_name}': {user_info}")
        else:
            self.log("User configuration updated (global)")
        
        InfoDialog(self.root, "Success", "User configuration saved successfully", "success")
    
    def show_apdus(self):
        """Muestra información sobre APDUs disponibles"""
        active_session = self.session_manager.get_active_session()
        
        if active_session:
            card_type = active_session._get_card_type_display()
            info = f"APDU Commands for {card_type}:\n\n"
        else:
            info = "APDU Commands:\n\n"
        
        info += ("1. SELECT CARD - Initialize card communication\n"
                "2. READ MEMORY - Read data from card memory\n"
                "3. PRESENT PSC - Present Personal Security Code\n"
                "4. WRITE MEMORY - Write data to card memory (requires PSC)\n"
                "5. CHANGE PSC - Change Personal Security Code (requires PSC)\n"
                "6. READ ERROR COUNTER - Read remaining PSC attempts\n"
                "7. READ PROTECTION BITS - Read write protection status\n"
                "8. WRITE PROTECT - Set write protection (requires PSC)")
        
        messagebox.showinfo("APDU Commands", info)
        self.log("APDU information displayed")
    
    def on_card_type_change(self):
        """Maneja el cambio de tipo de tarjeta"""
        card_type = self.card_type_var.get()
        # Esta función ya no hace nada útil con el nuevo sistema de sesiones
        # El tipo se maneja al crear la tarjeta, no al cambiar
        self.log(f"Card type changed to: {card_type}")
        self.update_page_buttons()
    
    def update_card_display(self):
        """Actualiza la visualización de memoria con datos de la sesión activa y colores"""
        # Habilitar edición temporalmente
        if hasattr(self, 'address_text'):
            self.address_text.config(state=tk.NORMAL)
        self.memory_text.config(state=tk.NORMAL)
        self.card_info_text.config(state=tk.NORMAL)
        self.ascii_text.config(state=tk.NORMAL)
        
        # Limpiar contenido previo
        if hasattr(self, 'address_text'):
            self.address_text.delete(1.0, tk.END)
        self.memory_text.delete(1.0, tk.END)
        self.card_info_text.delete(1.0, tk.END)
        self.ascii_text.delete(1.0, tk.END)
        
        # Configurar tags de colores y centrado
        self._setup_color_tags()
        self._setup_address_text_formatting()
        
        active_session = self.session_manager.get_active_session()
        
        if not active_session:
            if hasattr(self, 'address_text'):
                no_card_text = "ROW\\COL\n" + "-"*8 + "\nNo card"
                self._format_address_content(no_card_text)
            self._insert_status_message('memory_text', "No card selected\n\nCreate a NEW CARD or OPEN an existing\ncard to view memory content.")
            self._insert_status_message('ascii_text', "No ASCII data available\n\nMemory content will appear here\nwhen a card is selected.")
            self._insert_status_message('card_info_text', "No card information available\n\nSelect or create a card to view details.", "left")
            
            # Actualizar nuevos paneles cuando no hay tarjeta
            if hasattr(self, 'psc_label'):
                self.psc_label.config(text="-- -- --", fg='#9C27B0')  # Morado también cuando no hay tarjeta
            if hasattr(self, 'errors_label'):
                self.errors_label.config(text="--", fg=COLOR_TEXT_PRIMARY)
        else:
            # Obtener datos de memoria con colores
            display_data = active_session.get_memory_display_data_with_colors()
            
            # === CONTENIDO DE LA MATRIZ TIPO TABLA ===
            address_content = ""
            
            # COLUMNA IZQUIERDA: Header para cada tipo de tarjeta
            if active_session.card_type == CARD_TYPE_5528:
                # Para tarjetas 1K
                address_content += "ROW\\COL\n"
                address_content += "------\n"
            else:
                # Para tarjetas 256B
                address_content += "ROW\\COL\n"
                address_content += "------\n"
            
            # CONTENIDO HEX: Cabecera de columnas + datos (SIN espacios iniciales)
            header_line = "00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F\n"
            self.memory_text.insert(tk.END, header_line)
            self.memory_text.insert(tk.END, "-" * 47 + "\n")  # Línea separadora ajustada (47 chars)
            
            # ASCII: Header con 1 espacio entre cada columna
            ascii_header = "0 1 2 3 4 5 6 7 8 9 A B C D E F\n"
            self.ascii_text.insert(tk.END, ascii_header)
            self.ascii_text.insert(tk.END, "-------------------------------\n")
            
            # DATOS de cada fila (EXACTAMENTE 16 filas, sin extra) CON COLORES
            for i, row_data in enumerate(display_data):
                if i >= 16:  # Forzar máximo 16 filas
                    break
                    
                # Columna 1: Direcciones de fila centradas (sin espacios extras)
                address_content += f"{row_data['address']}\n"
                
                # Columna 2: Contenido hex con colores
                for j, hex_byte in enumerate(row_data['hex_bytes']):
                    if j > 0:
                        self.memory_text.insert(tk.END, " ")
                    
                    # Insertar byte con color específico
                    start_pos = self.memory_text.index(tk.INSERT)
                    self.memory_text.insert(tk.END, hex_byte['value'])
                    end_pos = self.memory_text.index(tk.INSERT)
                    
                    # Aplicar color basado en el estado de la dirección
                    color_tag = self._get_color_tag_name(hex_byte['color'])
                    self.memory_text.tag_add(color_tag, start_pos, end_pos)
                
                # Solo agregar salto de línea si no es la última fila
                if i < len(display_data) - 1:
                    self.memory_text.insert(tk.END, "\n")
                
                # Columna 3: ASCII con colores (espacios marcados con tag especial)
                for j, ascii_char in enumerate(row_data['ascii_chars']):
                    # Agregar espacio con tag especial antes de cada carácter (excepto el primero)
                    if j > 0:
                        space_start = self.ascii_text.index(tk.INSERT)
                        self.ascii_text.insert(tk.END, " ")  # 1 espacio
                        space_end = self.ascii_text.index(tk.INSERT)
                        self.ascii_text.tag_add("ascii_spacing", space_start, space_end)  # Marcar espacio
                    
                    # Insertar caracter ASCII con color específico
                    start_pos = self.ascii_text.index(tk.INSERT)
                    self.ascii_text.insert(tk.END, ascii_char['char'])
                    end_pos = self.ascii_text.index(tk.INSERT)
                    
                    # Aplicar el mismo color que el hex correspondiente
                    color_tag = self._get_color_tag_name(ascii_char['color'])
                    self.ascii_text.tag_add(color_tag, start_pos, end_pos)
                
                # Solo agregar salto de línea si no es la última fila
                if i < len(display_data) - 1:
                    self.ascii_text.insert(tk.END, "\n")
            
            # Información de la tarjeta
            card_info_content = ""
            card_info_content += f"Card: {active_session.card_name}\n"
            card_info_content += f"Type: {active_session._get_card_type_display()}\n"
            card_info_content += f"Status: {'Selected' if active_session.card_selected else 'Created'}\n"
            card_info_content += f"PSC: {'Verified' if active_session.psc_verified else 'Not presented'}\n"
            
            # Error Counter con formato apropiado según tipo de tarjeta
            if active_session.card_type == CARD_TYPE_5528:
                remaining_attempts = get_remaining_attempts_from_error_counter(active_session.apdu_handler.error_counter, CARD_TYPE_5528)
                error_counter_display = f"0x{active_session.apdu_handler.error_counter:02X} ({remaining_attempts} attempts)"
            else:
                # SLE5542: mostrar formato hex (attempts) - ej: 07 (3), 03 (2), 01 (1), 00 (0)
                remaining_attempts = get_remaining_attempts_from_error_counter(active_session.apdu_handler.error_counter, CARD_TYPE_5542)
                error_counter_display = f"0x{active_session.apdu_handler.error_counter:02X} ({remaining_attempts} attempts)"
            card_info_content += f"Error Counter: {error_counter_display}"  # Sin \n al final
            
            # Insertar contenido en cada área
            if hasattr(self, 'address_text'):
                self._format_address_content(address_content)
            self.card_info_text.insert(tk.END, card_info_content, "left")
            
            # Actualizar nuevos paneles
            if hasattr(self, 'psc_label'):
                current_psc = active_session.get_current_psc()
                # Usar morado para coincidir con las direcciones PSC en la memoria
                self.psc_label.config(text=current_psc, fg='#9C27B0')
            
            if hasattr(self, 'errors_label'):
                errors_remaining = active_session.apdu_handler.error_counter
                
                if active_session.card_type == CARD_TYPE_5528:
                    # Para SLE5528: mostrar valor hexadecimal y intentos restantes
                    if errors_remaining <= 0:
                        color = COLOR_CARD_BLOCKED
                        display_text = "00 (0)"  # Bloqueada
                    else:
                        # Calcular intentos restantes
                        remaining_attempts = get_remaining_attempts_from_error_counter(errors_remaining, CARD_TYPE_5528)
                        display_text = f"{errors_remaining:02X} ({remaining_attempts})"
                        # Color rojo si quedan pocos intentos (≤2)
                        color = COLOR_ERROR if remaining_attempts <= 2 else COLOR_TEXT_PRIMARY
                else:
                    # Para SLE5542: mostrar valor hexadecimal y intentos restantes (07 (3) - 03 (2) - 01 (1) - 00 (0))
                    remaining_attempts = get_remaining_attempts_from_error_counter(errors_remaining, CARD_TYPE_5542)
                    display_text = f"{errors_remaining:02X} ({remaining_attempts})"
                    
                    if errors_remaining == 0x00:
                        color = COLOR_CARD_BLOCKED  # Bloqueada
                    elif remaining_attempts <= 1:
                        color = COLOR_ERROR  # Color rojo si queda 1 o 0 intentos
                    else:
                        color = COLOR_TEXT_PRIMARY
                        
                self.errors_label.config(text=display_text, fg=color)
        
        # Deshabilitar edición (excepto address_text que se mantiene disabled)
        if hasattr(self, 'address_text'):
            self.address_text.config(state=tk.DISABLED)
        self.memory_text.config(state=tk.DISABLED)
        self.card_info_text.config(state=tk.DISABLED)
        self.ascii_text.config(state=tk.DISABLED)
    
    def _setup_color_tags(self):
        """Configura los tags de color para los widgets de texto"""
        # Tags para memory_text
        self.memory_text.tag_configure("readonly", foreground=COLOR_MEMORY_READONLY)
        self.memory_text.tag_configure("writable", foreground=COLOR_MEMORY_WRITABLE)
        self.memory_text.tag_configure("modified", foreground=COLOR_MEMORY_MODIFIED)
        self.memory_text.tag_configure("protected", foreground=COLOR_MEMORY_PROTECTED)
        self.memory_text.tag_configure("psc", foreground=COLOR_MEMORY_PSC)
        
        # Tags para ascii_text (mismos colores)
        self.ascii_text.tag_configure("readonly", foreground=COLOR_MEMORY_READONLY)
        self.ascii_text.tag_configure("writable", foreground=COLOR_MEMORY_WRITABLE)
        self.ascii_text.tag_configure("modified", foreground=COLOR_MEMORY_MODIFIED)
        self.ascii_text.tag_configure("protected", foreground=COLOR_MEMORY_PROTECTED)
        self.ascii_text.tag_configure("psc", foreground=COLOR_MEMORY_PSC)
    
    def _setup_address_text_formatting(self):
        """Configura el formato centrado para todos los widgets de texto"""
        # Configurar centrado para direcciones
        if hasattr(self, 'address_text'):
            self.address_text.tag_configure("center", justify='center')
        
        # Configurar centrado para memoria (mensajes de estado)
        if hasattr(self, 'memory_text'):
            self.memory_text.tag_configure("center", justify='center')
        
        # Configurar centrado para ASCII (mensajes de estado)
        if hasattr(self, 'ascii_text'):
            self.ascii_text.tag_configure("center", justify='center')
        
        # Configurar alineación izquierda para información de tarjeta
        if hasattr(self, 'card_info_text'):
            self.card_info_text.tag_configure("left", justify='left')
    
    def _format_address_content(self, address_content):
        """Formatea e inserta el contenido de direcciones con centrado"""
        if hasattr(self, 'address_text'):
            self.address_text.insert(tk.END, address_content, "center")
    
    def _insert_status_message(self, widget_name, message, alignment="center"):
        """Inserta un mensaje de estado con la alineación especificada en el widget"""
        widget = getattr(self, widget_name, None)
        if widget:
            tag = "left" if alignment == "left" else "center"
            widget.insert(tk.END, message, tag)
    
    def _get_color_tag_name(self, color):
        """Convierte un color hex a nombre de tag"""
        if color == COLOR_MEMORY_READONLY:
            return "readonly"
        elif color == COLOR_MEMORY_MODIFIED:
            return "modified"
        elif color == COLOR_MEMORY_PROTECTED:
            return "protected"
        elif color == COLOR_MEMORY_PSC:
            return "psc"
        else:
            return "writable"
    
    def _configure_memory_color_tags(self):
        """Configura los tags de colores para los widgets de memoria"""
        # Configurar tags para memory_text (sin negrita)
        self.memory_text.tag_configure("readonly", foreground=COLOR_MEMORY_READONLY, font=FONT_MONO)
        self.memory_text.tag_configure("modified", foreground=COLOR_MEMORY_MODIFIED, font=FONT_MONO)
        self.memory_text.tag_configure("protected", foreground=COLOR_MEMORY_PROTECTED, font=FONT_MONO)
        self.memory_text.tag_configure("psc", foreground=COLOR_MEMORY_PSC, font=FONT_MONO)
        self.memory_text.tag_configure("writable", foreground=COLOR_MEMORY_WRITABLE, font=FONT_MONO)
        
        # Configurar tags para ascii_text (sin negrita)
        self.ascii_text.tag_configure("readonly", foreground=COLOR_MEMORY_READONLY, font=FONT_MONO)
        self.ascii_text.tag_configure("modified", foreground=COLOR_MEMORY_MODIFIED, font=FONT_MONO)
        self.ascii_text.tag_configure("protected", foreground=COLOR_MEMORY_PROTECTED, font=FONT_MONO)
        self.ascii_text.tag_configure("psc", foreground=COLOR_MEMORY_PSC, font=FONT_MONO)
        self.ascii_text.tag_configure("writable", foreground=COLOR_MEMORY_WRITABLE, font=FONT_MONO)
    
    def _copy_ascii_without_spaces(self, event=None):
        """
        Intercepta Ctrl+C en el widget ASCII y copia el contenido sin espacios de visualización.
        Los espacios de datos reales (0x20) se preservan detectando grupos de 3 espacios consecutivos
        (donde el del medio es un espacio real y los otros dos son de visualización).
        """
        try:
            # Obtener el texto seleccionado
            selected_text = self.ascii_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            
            # Procesar línea por línea
            lines = selected_text.split('\n')
            cleaned_lines = []
            
            for line in lines:
                # Reemplazar grupos de 3 espacios por un marcador temporal
                # En el visor: "H e l l o   W o r l d" (3 espacios entre 'o' y 'W')
                # El del medio es un espacio real (0x20)
                
                # Procesar grupos de 3 o más espacios
                result = []
                i = 0
                while i < len(line):
                    # Verificar si hay 3 espacios consecutivos
                    if i + 2 < len(line) and line[i:i+3] == '   ':
                        # 3 espacios = 1 visual + 1 dato + 1 visual
                        # Preservar 1 espacio (el dato)
                        result.append(' ')
                        i += 3
                    elif line[i] == ' ':
                        # Espacio simple de visualización - ignorar
                        i += 1
                    else:
                        # Carácter normal - preservar
                        result.append(line[i])
                        i += 1
                
                cleaned_line = ''.join(result)
                
                # Añadir todas las líneas, incluso vacías (puntos)
                # porque representan continuidad de memoria
                cleaned_lines.append(cleaned_line)
            
            # Unir las líneas SIN separador
            # Las líneas del visor son continuación de memoria, no palabras separadas
            # "HOLA QUE TAL EST" + "AS.........." = "HOLA QUE TAL ESTAS.........."
            cleaned_text = ''.join(cleaned_lines)
            
            # Copiar al clipboard usando self.root
            self.root.clipboard_clear()
            self.root.clipboard_append(cleaned_text)
            
            # Retornar "break" para prevenir el comportamiento por defecto de Ctrl+C
            return "break"
            
        except tk.TclError:
            # No hay selección, no hacer nada
            return "break"
    
    def log(self, message, log_type="INFO"):
        """Añade un mensaje al log general de la aplicación con formato profesional"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Solo agregar al log de la sesión activa si existe, sin duplicar
        active_session = self.session_manager.get_active_session()
        if active_session:
            active_session.add_to_log(log_type, message)
            self.update_command_log_display()
        else:
            # Si no hay sesión activa, mostrar en log general temporal con formato
            if hasattr(self, 'log_text'):
                # Configurar tags si es necesario
                self._setup_log_text_tags()
                
                # Temporalmente habilitar escritura
                self.log_text.config(state=tk.NORMAL)
                
                # Insertar con formato según el tipo
                if log_type == "ERROR":
                    self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                    self.log_text.insert(tk.END, "❌ ", "error_icon")
                    self.log_text.insert(tk.END, "ERROR: ", "error_text")
                    self.log_text.insert(tk.END, f"{message}\n", "error_text")
                elif log_type == "SUCCESS":
                    self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                    self.log_text.insert(tk.END, "✅ ", "success_icon")
                    self.log_text.insert(tk.END, "SUCCESS: ", "success_text")
                    self.log_text.insert(tk.END, f"{message}\n", "success_text")
                elif log_type == "WARNING":
                    self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                    self.log_text.insert(tk.END, "⚠️  ", "warning_icon")
                    self.log_text.insert(tk.END, "WARNING: ", "warning_text")
                    self.log_text.insert(tk.END, f"{message}\n", "warning_text")
                else:  # INFO
                    self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                    self.log_text.insert(tk.END, "ℹ️  ", "info_icon")
                    self.log_text.insert(tk.END, "INFO: ", "info_text")
                    self.log_text.insert(tk.END, f"{message}\n", "info_text")
                
                self.log_text.see(tk.END)
                # Volver a deshabilitar escritura
                self.log_text.config(state=tk.DISABLED)
                self.log_text.config(state=tk.DISABLED)

    def save_log_to_file(self):
        """Guarda el log actual en un archivo .txt"""
        active_session = self.session_manager.get_active_session()
        if not active_session or not active_session.command_log:
            InfoDialog(self.root, "Warning", "No log available to save", "warning")
            return
            
        def handle_save(filename):
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"CardSIM - Command Log\n")
                    f.write(f"Tarjeta: {active_session.card_name}\n")
                    f.write(f"Tipo: {active_session._get_card_type_display()}\n")
                    f.write(f"Generado: {self.get_current_time()}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for log_entry in active_session.command_log:
                        f.write(f"[{log_entry['timestamp']}] {log_entry['type']}: {log_entry['message']}\n")
                
                self.log(f"Command log guardado en: {filename}")
                InfoDialog(self.root, "Success", f"Log saved successfully to {filename}", "success")
            except Exception as e:
                self.log(f"Error al guardar log: {str(e)}")
                InfoDialog(self.root, "Error", f"Could not save log: {str(e)}", "error")
        
        # Mostrar diálogo personalizado centrado
        SaveLogDialog(self.root, handle_save)
    
    def clear_log(self):
        """Limpia el log de la sesión activa usando diálogo personalizado"""
        active_session = self.session_manager.get_active_session()
        if active_session:
            dialog = ConfirmationDialog(
                self.root,
                "Confirm",
                "Are you sure you want to clear the entire log?\n\nThis action cannot be undone.",
                "warning"
            )
            
            if dialog.show():
                active_session.command_log = []
                active_session.save_session_state()
                self.update_command_log_display()
                self.log("Command log cleared")
        else:
            InfoDialog(self.root, "Warning", "No active session available", "warning")
    
    def show_apdus_reference(self):
        """Muestra una ventana con las imágenes de teoría sobre APDUs"""
        try:
            from PIL import Image, ImageTk
            import os
            
            apdus_window = tk.Toplevel(self.root)
            apdus_window.title("APDU Commands - Visual Theory")
            apdus_window.configure(bg=COLOR_BG_PANEL)
            apdus_window.resizable(True, True)
            
            # Hacer modal respecto a la ventana principal
            apdus_window.transient(self.root)
            apdus_window.grab_set()
            
            # Centrar respecto a la ventana principal (funciona en múltiples pantallas)
            self.root.update_idletasks()
            apdus_window.update_idletasks()
            
            # Obtener posición y tamaño de la ventana principal
            main_x = self.root.winfo_rootx()
            main_y = self.root.winfo_rooty()
            main_width = self.root.winfo_width()
            main_height = self.root.winfo_height()
            
            # Tamaño de la nueva ventana
            dialog_width = 1000
            dialog_height = 700
            
            # Calcular posición centrada respecto a la ventana principal
            pos_x = main_x + (main_width - dialog_width) // 2
            pos_y = main_y + (main_height - dialog_height) // 2
            
            # Aplicar geometría
            apdus_window.geometry(f"{dialog_width}x{dialog_height}+{pos_x}+{pos_y}")
            
            # Configurar icono de ETSISI
            self._set_window_icon(apdus_window)
            
            # Crear frame principal con scroll
            main_frame = tk.Frame(apdus_window, bg=COLOR_BG_PANEL)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Crear canvas y scrollbar
            canvas = tk.Canvas(main_frame, bg=COLOR_BG_PANEL, highlightthickness=0)
            scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg=COLOR_BG_PANEL)
            
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            
            # Título
            title_label = tk.Label(scrollable_frame, text="APDU Commands - Visual Theory", 
                                  font=FONT_HEADER, bg=COLOR_BG_PANEL, fg=COLOR_TEXT_PRIMARY)
            title_label.pack(pady=(0, 20))
            
            # Lista de imágenes en el orden especificado
            image_files = [
                "apdus.jpg",
                "sle5542.jpg", 
                "sle5528.jpg",
                "select_card.jpg",
                "read_memory.jpg",
                "present_psc.jpg",
                "write_memory.jpg",
                "change_psc.jpg",
                "read_errorcounter.jpg",
                "read_protbits.jpg",
                "write_protect.jpg"
            ]
            
            # Cargar y mostrar cada imagen
            for image_file in image_files:
                try:
                    # Construir ruta absoluta a la imagen
                    image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                            "assets", "teoria", image_file)
                    
                    if os.path.exists(image_path):
                        # Cargar imagen
                        original_image = Image.open(image_path)
                        
                        # Redimensionar para que se vea bien (máximo 900px de ancho)
                        max_width = 900
                        if original_image.width > max_width:
                            ratio = max_width / original_image.width
                            new_height = int(original_image.height * ratio)
                            image = original_image.resize((max_width, new_height), Image.Resampling.LANCZOS)
                        else:
                            image = original_image
                        
                        # Convertir a PhotoImage
                        photo = ImageTk.PhotoImage(image)
                        
                        # Crear label para la imagen
                        image_label = tk.Label(scrollable_frame, image=photo, bg=COLOR_BG_PANEL)
                        image_label.image = photo  # Mantener referencia
                        image_label.pack(pady=10)
                        
                        # Agregar separador visual entre imágenes
                        separator = tk.Frame(scrollable_frame, height=2, bg=COLOR_PRIMARY_BLUE)
                        separator.pack(fill=tk.X, padx=50, pady=5)
                        
                    else:
                        # Si no se encuentra la imagen, mostrar mensaje de error
                        error_label = tk.Label(scrollable_frame, 
                                             text=f"⚠️ Imagen no encontrada: {image_file}",
                                             font=FONT_BOLD, bg=COLOR_BG_PANEL, fg="red")
                        error_label.pack(pady=5)
                        
                except Exception as e:
                    # Si hay error cargando una imagen específica, mostrar mensaje
                    error_label = tk.Label(scrollable_frame, 
                                         text=f"❌ Error cargando {image_file}: {str(e)}",
                                         font=FONT_BOLD, bg=COLOR_BG_PANEL, fg="red")
                    error_label.pack(pady=5)
            
            # Actualizar región de scroll después de agregar todas las imágenes
            scrollable_frame.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
            
            # Habilitar scroll con rueda del ratón SOLO cuando el cursor está sobre el canvas
            def _on_mousewheel(event):
                # Verificar que el canvas aún existe antes de hacer scroll
                try:
                    if canvas.winfo_exists():
                        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                except tk.TclError:
                    # El canvas fue destruido, ignorar el evento
                    pass
            
            # Vincular eventos solo al canvas, no globalmente
            def _bind_mousewheel(event):
                canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
            def _unbind_mousewheel(event):
                canvas.unbind_all("<MouseWheel>")
                
            # Limpiar binding cuando se cierre la ventana
            def _on_window_close():
                try:
                    canvas.unbind_all("<MouseWheel>")
                except:
                    pass
                apdus_window.destroy()
            
            # Vincular/desvincular cuando el mouse entra/sale del canvas
            canvas.bind('<Enter>', _bind_mousewheel)
            canvas.bind('<Leave>', _unbind_mousewheel)
            
            # Configurar el protocolo de cierre de ventana
            apdus_window.protocol("WM_DELETE_WINDOW", _on_window_close)
            
            # Configurar tecla Escape para cerrar
            apdus_window.bind('<Escape>', lambda e: _on_window_close())
            
            # Asegurar que la ventana tenga foco para las teclas
            apdus_window.after(100, lambda: apdus_window.focus_force())
            
            # Botón cerrar al final
            close_btn = tk.Button(scrollable_frame, text="Cerrar", bg=COLOR_PRIMARY_BLUE, fg='white',
                                 font=FONT_BOLD, relief=tk.RAISED, bd=2, padx=20, pady=5,
                                 command=_on_window_close)
            close_btn.pack(pady=20)
            
        except ImportError:
            # Fallback si PIL no está disponible
            tk.messagebox.showerror("Error", "PIL/Pillow no está instalado. No se pueden mostrar las imágenes.")
        except Exception as e:
            tk.messagebox.showerror("Error", f"Error mostrando imágenes: {str(e)}")
    
    def show_credits_image(self):
        """Muestra una ventana con la imagen de créditos"""
        credits_window = tk.Toplevel(self.root)
        credits_window.title("CardSIM - Credits")
        
        # Configurar icono de ETSISI
        self._set_window_icon(credits_window)
        
        # Configurar ventana con estilo moderno
        credits_window.configure(bg='#1e1e1e')  # Fondo oscuro moderno
        credits_window.resizable(False, False)
        credits_window.transient(self.root)  # Hacer modal respecto a la ventana principal
        credits_window.grab_set()  # Capturar eventos
        
        # Configurar atributos de ventana para mejor apariencia
        try:
            # Intentar quitar la barra de título para un look más limpio
            credits_window.overrideredirect(False)  # Mantener controles de ventana
            credits_window.attributes('-alpha', 0.0)  # Empezar invisible para efecto de fade-in
        except:
            pass
        
        try:
            # Cargar imagen de créditos
            credits_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'icons', 'credits.png')
            credits_path = os.path.abspath(credits_path)
            
            if os.path.exists(credits_path):
                from PIL import Image, ImageTk, ImageFilter, ImageEnhance
                original_image = Image.open(credits_path)
                
                # Definir tamaño máximo para la ventana de créditos (reducido)
                max_width = 550
                max_height = 400
                
                # Calcular proporción de redimensionamiento
                width_ratio = max_width / original_image.width
                height_ratio = max_height / original_image.height
                scale_ratio = min(width_ratio, height_ratio, 1.0)
                
                # Redimensionar con mejor calidad
                if scale_ratio < 1.0:
                    new_width = int(original_image.width * scale_ratio)
                    new_height = int(original_image.height * scale_ratio)
                    image = original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                else:
                    image = original_image
                
                # Mejorar la imagen: aumentar contraste y nitidez
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.1)  # Aumentar contraste ligeramente
                
                enhancer = ImageEnhance.Sharpness(image)
                image = enhancer.enhance(1.2)  # Aumentar nitidez
                
                # Crear imagen con borde redondeado (efecto visual) - padding reducido
                padding = 10
                frame_width = image.width + (padding * 2)
                frame_height = image.height + (padding * 2)
                
                # Ajustar ventana al tamaño total incluyendo controles (ajustado para botón más alto)
                window_height = frame_height + 75  # Ligeramente más espacio para botón más alto
                credits_window.geometry(f"{frame_width}x{window_height}")
                
                # CENTRADO SIMPLIFICADO Y EFECTIVO
                def center_window():
                    # Esperar a que la ventana esté completamente renderizada
                    credits_window.update()
                    self.root.update()
                    
                    # Obtener dimensiones de la ventana principal
                    parent_x = self.root.winfo_rootx()
                    parent_y = self.root.winfo_rooty()
                    parent_w = self.root.winfo_width()
                    parent_h = self.root.winfo_height()
                    
                    # Obtener dimensiones de la ventana de créditos
                    dialog_w = credits_window.winfo_width()
                    dialog_h = credits_window.winfo_height()
                    
                    # Calcular posición centrada
                    pos_x = parent_x + (parent_w - dialog_w) // 2
                    pos_y = parent_y + (parent_h - dialog_h) // 2
                    
                    # Mover la ventana a la posición calculada
                    credits_window.wm_geometry(f"{dialog_w}x{dialog_h}+{pos_x}+{pos_y}")
                
                # Esperar más tiempo antes de centrar (100ms)
                credits_window.after(100, center_window)
                
                # Frame principal con gradiente simulado
                main_frame = tk.Frame(credits_window, bg='#1e1e1e')
                main_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
                
                # Frame para la imagen con borde y sombra simulada
                image_frame = tk.Frame(main_frame, bg='#404040', relief=tk.RAISED, bd=1)
                image_frame.pack(pady=5)
                
                # Frame interior para la imagen (efecto de marco)
                inner_frame = tk.Frame(image_frame, bg='#ffffff', padx=padding, pady=padding)
                inner_frame.pack(padx=3, pady=3)
                
                # Mostrar imagen
                photo = ImageTk.PhotoImage(image)
                image_label = tk.Label(inner_frame, image=photo, bg='#ffffff', relief=tk.FLAT)
                image_label.image = photo  # Mantener referencia
                image_label.pack()
                
                # Frame para los botones con mejor estilo
                button_frame = tk.Frame(main_frame, bg='#1e1e1e')
                button_frame.pack(pady=(10, 8), fill=tk.X)
                
                # Botón cerrar
                close_btn = tk.Button(button_frame, text="✕ Close", 
                                     bg='#0e639c', fg='#ffffff',
                                     font=('Segoe UI', 9, 'bold'), 
                                     relief=tk.FLAT, bd=0, padx=20, pady=10,
                                     activebackground='#1177bb', activeforeground='#ffffff',
                                     cursor='hand2',
                                     command=credits_window.destroy)
                close_btn.pack(expand=True)  # Centrar el botón
                
                # Efecto hover para el botón
                def on_enter(e):
                    close_btn.config(bg='#1177bb')
                def on_leave(e):
                    close_btn.config(bg='#0e639c')
                
                close_btn.bind("<Enter>", on_enter)
                close_btn.bind("<Leave>", on_leave)
                
                # Información adicional pequeña (espaciado reducido)
                info_label = tk.Label(main_frame, text="David Balenzategui García • Universidad Politécnica de Madrid", 
                                    font=('Segoe UI', 7), fg='#888888', bg='#1e1e1e')
                info_label.pack(pady=(0, 5))  # Espaciado mínimo
                
                # Efecto de fade-in
                def fade_in(alpha=0.0):
                    if alpha < 1.0:
                        try:
                            credits_window.attributes('-alpha', alpha)
                            credits_window.after(20, lambda: fade_in(alpha + 0.05))
                        except:
                            pass
                
                credits_window.after(50, fade_in)
                
            else:
                # Ventana de error mejorada
                credits_window.configure(bg='#2d2d30')
                credits_window.geometry("450x180")
                
                error_frame = tk.Frame(credits_window, bg='#2d2d30')
                error_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
                
                error_icon = tk.Label(error_frame, text="⚠", font=('Segoe UI', 24), 
                                    fg='#ffcc02', bg='#2d2d30')
                error_icon.pack(pady=(0, 10))
                
                tk.Label(error_frame, text="Error: No se pudo cargar la imagen de créditos", 
                        font=('Segoe UI', 10), bg='#2d2d30', fg='#ff6b6b').pack()
                
                tk.Label(error_frame, text=f"Ruta buscada: {credits_path}", 
                        font=('Segoe UI', 8), bg='#2d2d30', fg='#888888').pack(pady=(5, 0))
                
                close_btn = tk.Button(error_frame, text="Cerrar", 
                                     bg='#0e639c', fg='#ffffff',
                                     font=('Segoe UI', 10, 'bold'), relief=tk.FLAT,
                                     padx=20, pady=5, command=credits_window.destroy)
                close_btn.pack(pady=15)
                
        except Exception as e:
            # Ventana de error de excepción mejorada
            credits_window.configure(bg='#2d2d30')
            credits_window.geometry("500x200")
            
            error_frame = tk.Frame(credits_window, bg='#2d2d30')
            error_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            error_icon = tk.Label(error_frame, text="❌", font=('Segoe UI', 24), 
                                fg='#ff6b6b', bg='#2d2d30')
            error_icon.pack(pady=(0, 10))
            
            tk.Label(error_frame, text=f"Error al cargar créditos:", 
                    font=('Segoe UI', 10, 'bold'), bg='#2d2d30', fg='#ff6b6b').pack()
            
            tk.Label(error_frame, text=str(e), 
                    font=('Segoe UI', 9), bg='#2d2d30', fg='#cccccc').pack(pady=(5, 0))
            
            close_btn = tk.Button(error_frame, text="Cerrar", 
                                 bg='#0e639c', fg='#ffffff',
                                 font=('Segoe UI', 10, 'bold'), relief=tk.FLAT,
                                 padx=20, pady=5, command=credits_window.destroy)
            close_btn.pack(pady=15)
        
        # Configurar teclas de acceso rápido
        def close_window(event=None):
            # Efecto fade-out antes de cerrar
            def fade_out(alpha=1.0):
                if alpha > 0.0:
                    try:
                        credits_window.attributes('-alpha', alpha)
                        credits_window.after(15, lambda: fade_out(alpha - 0.1))
                    except:
                        credits_window.destroy()
                else:
                    credits_window.destroy()
            
            fade_out()
        
        credits_window.bind('<Escape>', close_window)
        credits_window.bind('<Return>', close_window)
        credits_window.protocol("WM_DELETE_WINDOW", close_window)
        
        # Enfocar la ventana
        credits_window.focus_set()
    
    def setup_keyboard_shortcuts(self):
        """Configura los atajos de teclado"""
        # Escape para alternar entre maximizado y ventana normal
        self.root.bind('<Escape>', self.toggle_maximized)
        # F11 para pantalla completa real (sin barra de tareas)
        self.root.bind('<F11>', self.toggle_real_fullscreen)
        # Alt+F4 para cerrar
        self.root.bind('<Alt-F4>', lambda e: self.root.quit())
        
        # Variables para detectar combinaciones de teclas
        self.key_p_pressed = False
        self.key_c_pressed = False
        
        # Binding general de teclas para manejar combinaciones
        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.bind('<KeyRelease>', self.on_key_release)
    
    def on_key_press(self, event):
        """Maneja las pulsaciones de teclas"""
        if event.keysym == 'p':
            self.key_p_pressed = True
        elif event.keysym in ['c', 'C']:
            self.key_c_pressed = True
        elif self.key_p_pressed and event.keysym in ['0', '1', '2', '3']:
            # Combinación p+número para cambiar páginas
            page_num = int(event.keysym)
            self.select_page(page_num)
            # NO resetear key_p_pressed aquí para permitir múltiples cambios
        elif self.key_c_pressed and event.keysym in ['1', '2', '3', '4', '5', '6', '7', '8']:
            # Combinación c+número para cambiar tarjetas
            card_num = int(event.keysym)
            self.select_card_by_number(card_num)
            # NO resetear key_c_pressed aquí para permitir múltiples cambios
        elif not self.key_p_pressed and not self.key_c_pressed and event.keysym in ['1', '2', '3', '4', '5', '6', '7', '8']:
            # Teclas numéricas para APDUs (solo si ni p ni c están presionadas)
            number = int(event.keysym)
            self.execute_apdu_by_number(number)
    
    def on_key_release(self, event):
        """Maneja las liberaciones de teclas"""
        if event.keysym == 'p':
            self.key_p_pressed = False
        elif event.keysym in ['c', 'C']:
            self.key_c_pressed = False
    
    def execute_apdu_by_number(self, number):
        """Ejecuta un comando APDU basado en el número de tecla presionada"""
        # Mapeo de números a comandos APDU
        apdu_commands = {
            1: self.select_card_apdu,
            2: self.read_memory_dialog,
            3: self.present_psc,
            4: self.write_memory_dialog,
            5: self.change_psc_dialog,
            6: self.read_error_counter,
            7: self.read_protection_bits,
            8: self.write_protect_dialog
        }
        
        # Verificar si el número está en el rango válido
        if number in apdu_commands:
            # Verificar si el botón está habilitado antes de ejecutar
            button_key = f'apdu_{number}'
            if button_key in self.button_refs:
                button = self.button_refs[button_key]
                if str(button['state']) != 'disabled':
                    # Ejecutar el comando directamente sin log adicional
                    try:
                        apdu_commands[number]()
                    except Exception as e:
                        self.log(f"Error executing APDU {number}: {str(e)}")
                else:
                    self.log(f"APDU {number} is disabled")
    
    def select_card_by_number(self, card_num):
        """Selecciona una tarjeta basada en el slot número (1-8)"""
        # Verificar si hay un explorador de tarjetas
        if not hasattr(self, 'card_explorer') or not self.card_explorer:
            return  # No hay explorador, no hacer nada
        
        # El número de slot (1-8) corresponde al índice (0-7) del slot
        slot_index = card_num - 1
        
        # Buscar la tarjeta que esté en el slot especificado
        found_card = None
        for card_info in self.card_explorer.card_data:
            if card_info['slot_index'] == slot_index:
                found_card = card_info
                break
        
        if found_card:
            session_id = found_card['session_id']
            # Cambiar a la tarjeta especificada
            self.session_manager.set_active_session(session_id)
            
            # Actualizar estado visual en el explorador
            self.card_explorer.set_active_card(session_id)
            
            # Actualizar interfaz
            self.update_interface_for_active_session()
        # Si el slot no tiene tarjeta, no hacer nada (como especificaste)
    
    def toggle_maximized(self, event=None):
        """Alterna entre modo maximizado y ventana normal"""
        current_state = self.root.state()
        if current_state == 'zoomed':
            # Está maximizada, cambiar a ventana normal
            self.root.state('normal')
            self.root.geometry("1400x900")
        else:
            # Está en ventana normal, maximizar
            self.root.state('zoomed')
    
    def toggle_real_fullscreen(self, event=None):
        """Alterna pantalla completa real (oculta barra de tareas)"""
        current_fullscreen = self.root.attributes('-fullscreen')
        if current_fullscreen:
            # Salir de pantalla completa real y volver a maximizado
            self.root.attributes('-fullscreen', False)
            self.root.state('zoomed')
        else:
            # Entrar en pantalla completa real
            self.root.attributes('-fullscreen', True)
    
    def toggle_fullscreen(self, event=None):
        """Función mantenida para compatibilidad - usa toggle_maximized"""
        self.toggle_maximized(event)
    
    def write_to_real_card(self):
        """Escribe la tarjeta simulada a una tarjeta física"""
        try:
            dialog = PhysicalCardWriteDialog(self.root, self.session_manager)
        except Exception as e:
            self.log(f"Error opening Write Card dialog: {e}")
            messagebox.showerror("Error", f"Error opening Write Card dialog:\n{e}")
    
    def read_from_real_card(self):
        """Lee una tarjeta física y crea una nueva sesión"""
        try:
            dialog = PhysicalCardReadDialog(self.root, self.session_manager)
            result, session_id = dialog.show()
            
            if result:
                # Si se creó una nueva tarjeta exitosamente, actualizar la lista
                self.update_cards_list()
                
                # Si se creó una tarjeta nueva (no solo lectura), seleccionarla automáticamente
                if session_id:
                    self.on_card_select_from_explorer(session_id)
                
        except Exception as e:
            self.log(f"Error opening Read Card dialog: {e}")
            messagebox.showerror("Error", f"Error opening Read Card dialog:\n{e}")
    
    def run(self):
        """Ejecuta la aplicación"""
        self.root.mainloop()
    
    def on_closing(self):
        """Maneja el cierre de la aplicación"""
        try:
            # Destruir todos los diálogos toplevel primero
            if hasattr(self, 'root') and self.root:
                for child in self.root.winfo_children():
                    if isinstance(child, tk.Toplevel):
                        try:
                            child.destroy()
                        except Exception:
                            pass
            
            # Cleanup de sesiones si es necesario
            if hasattr(self, 'session_manager'):
                self.session_manager.close_all_sessions()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            try:
                # Cerrar la aplicación
                if hasattr(self, 'root') and self.root:
                    self.root.quit()
                    self.root.destroy()
            except Exception as e:
                print(f"Error during final cleanup: {e}")
                # Forzar salida si no se puede cerrar normalmente
                import sys
                sys.exit(0)
    
    def _is_present_psc_context(self, active_session, current_entry):
        """Determina si la respuesta actual viene de un comando Present PSC"""
        if not active_session or not hasattr(active_session, 'command_log'):
            return False
            
        # Buscar en las últimas entradas para encontrar un APDU_SEND con PRESENT PSC
        # Buscar hacia atrás desde el final del log
        current_index = -1
        for i, entry in enumerate(active_session.command_log):
            if entry is current_entry:
                current_index = i
                break
                
        if current_index >= 0:
            # Buscar hacia atrás desde la entrada actual
            for i in range(current_index - 1, -1, -1):
                entry = active_session.command_log[i]
                if entry['type'] == 'APDU_SEND':
                    return 'PRESENT PSC' in entry.get('message', '')
                elif entry['type'] == 'APDU_RESPONSE':
                    # Si encontramos otra respuesta antes, no es el contexto correcto
                    break
        return False
    
    def update_info_panels(self):
        """Actualiza solo los paneles de información (PSC y Error Counter) sin tocar la memoria"""
        active_session = self.session_manager.get_active_session()
        
        if not active_session:
            if hasattr(self, 'psc_label'):
                self.psc_label.config(text="-- -- --", fg='#9C27B0')
            if hasattr(self, 'errors_label'):
                self.errors_label.config(text="---", fg=COLOR_TEXT_PRIMARY)
            return
        
        # Actualizar PSC panel
        if hasattr(self, 'psc_label'):
            current_psc = active_session.get_current_psc()
            self.psc_label.config(text=current_psc, fg='#9C27B0')
        
        # Actualizar Error Counter panel
        if hasattr(self, 'errors_label'):
            errors_remaining = active_session.apdu_handler.error_counter
            
            if active_session.card_type == CARD_TYPE_5528:
                # Para SLE5528: mostrar valor hexadecimal y intentos restantes
                if errors_remaining <= 0:
                    color = COLOR_CARD_BLOCKED
                    display_text = "00 (0)"  # Bloqueada
                else:
                    # Calcular intentos restantes
                    remaining_attempts = get_remaining_attempts_from_error_counter(errors_remaining, CARD_TYPE_5528)
                    display_text = f"{errors_remaining:02X} ({remaining_attempts})"
                    # Color rojo si quedan pocos intentos (≤2)
                    color = COLOR_ERROR if remaining_attempts <= 2 else COLOR_TEXT_PRIMARY
            else:
                # Para SLE5542: mostrar valor hexadecimal y intentos restantes (07 (3) - 03 (2) - 01 (1) - 00 (0))
                remaining_attempts = get_remaining_attempts_from_error_counter(errors_remaining, CARD_TYPE_5542)
                display_text = f"{errors_remaining:02X} ({remaining_attempts})"
                
                if errors_remaining == 0x00:
                    color = COLOR_CARD_BLOCKED  # Bloqueada
                elif remaining_attempts <= 1:
                    color = COLOR_ERROR  # Color rojo si queda 1 o 0 intentos
                else:
                    color = COLOR_TEXT_PRIMARY
                    
            self.errors_label.config(text=display_text, fg=color)

    def _post_small_screen_layout_fix(self, cards_per_row):
        """Método simple para restaurar el layout después del Small Screen Mode"""
        try:
            # Desactivar la bandera para permitir que _apply_grid_layout funcione
            if hasattr(self, '_in_post_small_screen_restoration'):
                delattr(self, '_in_post_small_screen_restoration')
            
            # Solo llamar a _apply_grid_layout
            self._apply_grid_layout(cards_per_row)
            
            # Forzar reorganización del CardExplorer después del Small Screen Mode
            if hasattr(self, 'card_explorer'):
                self.card_explorer.canvas.update_idletasks()
                self.card_explorer.canvas.configure(scrollregion=self.card_explorer.canvas.bbox("all"))
                
                if hasattr(self.card_explorer, 'icons_frame'):
                    for widget in self.card_explorer.icons_frame.winfo_children():
                        widget.update_idletasks()
                    self.card_explorer.icons_frame.update_idletasks()
            
            self.root.update_idletasks()
            
        except Exception as e:
            print(f"❌ Error restaurando layout: {e}")
            import traceback
            traceback.print_exc()
