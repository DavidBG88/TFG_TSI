
import tkinter as tk
from src.utils.constants import (
    COLOR_BG_MAIN, COLOR_BG_PANEL, COLOR_PRIMARY_BLUE, COLOR_TEXT_PRIMARY,
    FONT_HEADER, FONT_NORMAL, FONT_BOLD, FONT_SMALL, 
    CARD_TYPE_5542, CARD_TYPE_5528, COLOR_WARNING, PSC_ADDRESS_5528
)
from src.utils.resource_manager import get_icon_path

class CreateCardFromReadDialog:
    """Diálogo para crear una nueva tarjeta con contenido leído de tarjeta física"""
    
    def __init__(self, parent, session_manager, card_data, card_type, update_callback=None, psc_bytes=None):
        self.parent = parent
        self.session_manager = session_manager
        self.card_data = card_data
        self.card_type = card_type
        self.update_callback = update_callback
        self.psc_bytes = psc_bytes  # PSC personalizado usado para leer la tarjeta
        print(f"DEBUG: CreateCardFromReadDialog recibió PSC: {[f'{b:02X}' for b in psc_bytes] if psc_bytes else 'None'}")
        self.dialog = None
        self.result = None
        self.created_session_id = None  # Para almacenar el ID de la sesión creada
        
        # Crear y mostrar el diálogo
        self.create_dialog()
        
    def create_dialog(self):
        """Crear la ventana del diálogo"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Create Card from Read Data")
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
        title_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Icono de tarjeta
        icon_label = tk.Label(title_frame, text="💳", font=("Segoe UI Emoji", 24),
                             fg=COLOR_PRIMARY_BLUE, bg=COLOR_BG_MAIN)
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Título
        title_label = tk.Label(title_frame, text="Create Card from Read Data", 
                              font=FONT_HEADER, bg=COLOR_BG_MAIN,
                              fg=COLOR_TEXT_PRIMARY)
        title_label.pack(side=tk.LEFT)
        
        # Información de la tarjeta leída
        info_frame = tk.LabelFrame(main_frame, text="Source Card Information", 
                                  font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        card_type_str = "SLE5542" if self.card_type == CARD_TYPE_5542 else "SLE5528"
        size_str = "256 bytes" if self.card_type == CARD_TYPE_5542 else "1024 bytes"
        
        info_text = f"Card Type: {card_type_str}\n"
        info_text += f"Size: {size_str}\n"
        info_text += f"Data Length: {len(self.card_data)} bytes\n"
        info_text += f"First 8 bytes: {' '.join([f'{b:02X}' for b in self.card_data[:8]])}"
        
        info_label = tk.Label(info_frame, text=info_text, font=FONT_NORMAL,
                             bg=COLOR_BG_MAIN, fg=COLOR_TEXT_PRIMARY, justify=tk.LEFT)
        info_label.pack(padx=15, pady=10)
        
        # Nombre de la nueva tarjeta
        name_frame = tk.LabelFrame(main_frame, text="New Card Name", 
                                  font=FONT_NORMAL, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN)
        name_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.name_var = tk.StringVar(value=f"ReadCard_{card_type_str}")
        self.name_entry = tk.Entry(name_frame, textvariable=self.name_var,
                                  font=FONT_NORMAL, width=30)
        self.name_entry.pack(padx=15, pady=10, fill=tk.X)
        self.name_entry.focus()
        self.name_entry.select_range(0, tk.END)
        
        # Advertencia sobre direcciones de fábrica
        warning_frame = tk.Frame(main_frame, bg=COLOR_BG_PANEL, relief=tk.RAISED, bd=1)
        warning_frame.pack(fill=tk.X, pady=(0, 20))
        
        warning_text = "⚠️ Note: Factory addresses and security areas will be properly configured\n"
        warning_text += "for the new card type with appropriate PSC and error counter settings."
        
        warning_label = tk.Label(warning_frame, text=warning_text, font=FONT_SMALL,
                                bg=COLOR_BG_PANEL, fg=COLOR_TEXT_PRIMARY, justify=tk.LEFT)
        warning_label.pack(padx=10, pady=8)
        
        # Botones
        button_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(button_frame, text="Cancel", font=FONT_NORMAL,
                 bg=COLOR_BG_PANEL, fg=COLOR_TEXT_PRIMARY,
                 width=12, command=self.cancel).pack(side=tk.RIGHT, padx=(10, 0))
        
        tk.Button(button_frame, text="Create Card", font=FONT_BOLD,
                 bg=COLOR_PRIMARY_BLUE, fg="white", 
                 width=12, command=self.create_card).pack(side=tk.RIGHT)
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.create_card())
        self.dialog.bind('<Escape>', lambda e: self.cancel())
        
        # Centrar diálogo
        self.dialog.geometry("550x500")
        self.dialog.update_idletasks()
        
        # Centrar en la pantalla
        x = (self.dialog.winfo_screenwidth() // 2) - (550 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"550x500+{x}+{y}")
    
    def create_card(self):
        """Crear la nueva tarjeta con el contenido leído"""
        name = self.name_var.get().strip()
        
        # Validar nombre
        if not name:
            tk.messagebox.showerror("Error", "Please enter a card name.", parent=self.dialog)
            return
        
        # Verificar que el nombre no esté en uso
        if self.session_manager.get_session_by_name(name) is not None:
            tk.messagebox.showerror("Error", f"A card named '{name}' already exists.\nPlease choose a different name.", parent=self.dialog)
            return
        
        try:
            # Crear nueva sesión con el tipo de tarjeta leído
            session, message = self.session_manager.create_new_card_session(name, self.card_type)
            
            if session:
                # Cargar los datos leídos en la nueva sesión
                session.memory_manager.load_from_data(self.card_data)
                
                # Si se usó un PSC personalizado durante la lectura, aplicarlo a la nueva tarjeta
                if self.psc_bytes is not None:
                    try:
                        print(f"DEBUG: Aplicando PSC personalizado: {[f'{b:02X}' for b in self.psc_bytes]}")
                        # Aplicar el PSC personalizado directamente en el registro interno o memoria
                        if self.card_type == CARD_TYPE_5542:
                            # SLE5542: PSC en registro interno (no en memoria visible)
                            session.memory_manager.internal_psc_5542 = list(self.psc_bytes)
                            print(f"DEBUG: SLE5542 - PSC guardado en registro interno: {session.memory_manager.internal_psc_5542}")
                        else:  # CARD_TYPE_5528
                            # SLE5528: PSC en memoria visible (direcciones 0x000-0x001)
                            for i, byte_val in enumerate(self.psc_bytes):
                                addr = PSC_ADDRESS_5528 + i
                                session.memory_manager.memory_data[addr] = f"{byte_val:02X}"
                            print(f"DEBUG: SLE5528 - PSC guardado en memoria en 0x{PSC_ADDRESS_5528:03X}")
                        
                        # Marcar que el PSC ha sido cambiado
                        session.psc_has_been_changed = True
                        print(f"DEBUG: PSC aplicado exitosamente")
                    except Exception as e:
                        print(f"WARNING: Could not apply custom PSC: {e}")
                else:
                    print("DEBUG: No hay PSC personalizado para aplicar")
                
                # Asegurar que las direcciones de fábrica estén bloqueadas
                if hasattr(session.memory_manager, 'ensure_factory_locked'):
                    session.memory_manager.ensure_factory_locked()
                
                # Almacenar el session_id para devolverlo
                self.created_session_id = session.session_id
                
                # Llamar al callback para actualizar la interfaz principal
                if self.update_callback:
                    self.update_callback()
                
                self.result = True
                tk.messagebox.showinfo("Success", f"Card '{name}' created successfully with read data!", parent=self.dialog)
                self.dialog.destroy()
            else:
                tk.messagebox.showerror("Error", f"Could not create card: {message}", parent=self.dialog)
                
        except Exception as e:
            tk.messagebox.showerror("Error", f"Error creating card: {str(e)}", parent=self.dialog)
    
    def cancel(self):
        """Cancelar operación"""
        self.result = False
        self.dialog.destroy()
    
    def show(self):
        """Mostrar diálogo y devolver resultado y session_id"""
        self.dialog.wait_window()
        return self.result, self.created_session_id
