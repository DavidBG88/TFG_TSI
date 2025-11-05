#!/usr/bin/env python3
"""
Explorador de tarjetas con iconos para CardSIM
Reemplaza la lista simple con una vista de iconos organizada en grid
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import sys

# Agregar src al path para imports
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from src.utils.constants import *
from src.core.code_improvements import load_icon_safe

class CardExplorer:
    """Explorador visual de tarjetas con iconos organizados en grid"""
    
    def __init__(self, parent_frame, card_select_callback, panel_frame=None):
        self.parent_frame = parent_frame
        self.card_select_callback = card_select_callback
        self.panel_frame = panel_frame  # Frame padre para el scroll
        
        # Grid configuration: 4 filas x 2 columnas = 8 tarjetas máximo
        self.max_cards = 8
        self.grid_cols = 2
        self.grid_rows = 4
        
        # Configuración visual mejorada
        self.slot_width = 80
        self.slot_height = 100
        
        # Lista de botones de tarjetas
        self.card_buttons = []
        self.card_data = []  # Lista de datos de las tarjetas
        
        # Cargar iconos
        self.load_icons()
        
        # Crear interfaz
        self.setup_ui()
        
    def load_icons(self):
        """Carga los iconos de tarjetas con tamaño consistente"""
        self.icons = {}
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets', 'icons')
        
        icon_size = (120, 85)

        icon_files = {
            '5542': '256b_card.png',  # SLE5542 = 256 bytes
            '5528': '1k_card.png',    # SLE5528 = 1KB
        }
        
        for icon_key, filename in icon_files.items():
            icon_path = os.path.join(icons_dir, filename)
            loaded_icon = load_icon_safe(icon_path, icon_size, create_placeholder=True)
            if loaded_icon:
                self.icons[icon_key] = loaded_icon
    
    def setup_ui(self):
        """Configura la interfaz del explorador con scroll (igual que el panel de Logs)"""
        # Frame principal que contendrá el canvas y scrollbar
        self.main_frame = tk.Frame(self.parent_frame, bg=COLOR_BG_PANEL)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Configurar grid para canvas y scrollbar
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Canvas scrollable (igual que el log_text en el panel de Logs)
        self.canvas = tk.Canvas(self.main_frame, bg=COLOR_BG_PANEL, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky='nsew', padx=4, pady=4)
        
        # Scrollbar vertical (igual que en el panel de Logs)
        scrollbar = tk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar.grid(row=0, column=1, sticky='ns', pady=2)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Frame interno para los iconos (dentro del canvas)
        self.icons_frame = tk.Frame(self.canvas, bg=COLOR_BG_PANEL)
        
        # Añadir el frame al canvas
        self.canvas_frame_id = self.canvas.create_window((0, 0), window=self.icons_frame, anchor="nw")
        
        # Configurar eventos para actualizar el scroll region
        self.icons_frame.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
        # Configurar scroll con rueda del ratón
        self._setup_mouse_scroll()
        
        # Crear grid de slots vacíos
        self.create_empty_slots()
    
    def _on_frame_configure(self, event):
        """Actualizar scroll region cuando el contenido cambie de tamaño"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_canvas_configure(self, event):
        """Actualizar el ancho del frame interno cuando el canvas cambie de tamaño"""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_frame_id, width=canvas_width)
    
    def _setup_mouse_scroll(self):
        """Configurar scroll con rueda del ratón (igual que el panel de Logs)"""
        def _bind_to_mousewheel(widget):
            widget.bind("<MouseWheel>", self._on_mousewheel)
            widget.bind("<Button-4>", self._on_mousewheel)
            widget.bind("<Button-5>", self._on_mousewheel)
            
        _bind_to_mousewheel(self.canvas)
        _bind_to_mousewheel(self.icons_frame)
        
        # Aplicar a todos los widgets hijos
        for child in self.icons_frame.winfo_children():
            _bind_to_mousewheel(child)
    
    def _on_mousewheel(self, event):
        """Manejar eventos de rueda del ratón"""
        if event.delta:
            delta = -1 * (event.delta / 120)
        else:
            delta = -1 if event.num == 4 else 1
        self.canvas.yview_scroll(int(delta), "units")
    
    def create_empty_slots(self):
        """Crea los slots vacíos del grid con tamaños fijos"""
        # Ajustar ancho según número de columnas
        slot_width = 280 if self.grid_cols == 1 else 140 

        for i in range(self.max_cards):
            row = i // self.grid_cols
            col = i % self.grid_cols
            
            # Frame para cada slot con tamaños completamente fijos
            slot_frame = tk.Frame(self.icons_frame, bg=COLOR_BG_PANEL, 
                                 width=slot_width, height=120, relief=tk.FLAT, bd=0)
            
            # Ajustar posicionamiento según el layout
            if self.grid_cols == 1:
                # Para 1 columna: centrar el slot con espaciado normal
                slot_frame.grid(row=row, column=col, padx=20, pady=2, sticky='')
            else:
                # Para 2 columnas: posicionamiento normal
                slot_frame.grid(row=row, column=col, padx=2, pady=1, sticky='')

            slot_frame.grid_propagate(False)  # Evita que el frame cambie de tamaño
            slot_frame.pack_propagate(False)  # Evita que el contenido interno cambie el frame
            
            # Label vacío (placeholder)
            empty_label = tk.Label(slot_frame, text="Empty\nSlot", 
                                  font=FONT_TINY, bg=COLOR_BG_PANEL, 
                                  fg=COLOR_TEXT_DISABLED)
            empty_label.pack(expand=True)
            
            # Configurar scroll del ratón para el slot vacío
            slot_frame.bind("<MouseWheel>", self._on_mousewheel)
            slot_frame.bind("<Button-4>", self._on_mousewheel)
            slot_frame.bind("<Button-5>", self._on_mousewheel)
            empty_label.bind("<MouseWheel>", self._on_mousewheel)
            empty_label.bind("<Button-4>", self._on_mousewheel)
            empty_label.bind("<Button-5>", self._on_mousewheel)
            
            self.card_buttons.append(None)  # Placeholder
        
        # Configurar peso de columnas para centrado
        for col in range(self.grid_cols):
            self.icons_frame.grid_columnconfigure(col, weight=1)
        
        # Configurar filas con altura fija y uniforme
        for row in range(self.grid_rows):
            self.icons_frame.grid_rowconfigure(row, weight=0, minsize=108, uniform="row")
    
    def add_card(self, card_name, card_type, session_id, is_active=False):
        """Añade una nueva tarjeta al explorador en el primer slot disponible"""
        if len(self.card_data) >= self.max_cards:
            return False  # No hay espacio
        
        # Buscar el primer slot vacío (None en card_buttons)
        slot_index = -1
        for i in range(self.max_cards):
            if self.card_buttons[i] is None:
                slot_index = i
                break
        
        if slot_index == -1:
            return False  # No se encontró slot vacío
        
        row = slot_index // self.grid_cols
        col = slot_index % self.grid_cols
        
        # Datos de la tarjeta
        card_info = {
            'name': card_name,
            'type': card_type,
            'session_id': session_id,
            'is_active': is_active,
            'slot_index': slot_index
        }
        self.card_data.append(card_info)
        
        # Obtener slot frame existente
        slot_frame = None
        for child in self.icons_frame.grid_slaves():
            info = child.grid_info()
            if info['row'] == row and info['column'] == col:
                slot_frame = child
                break
        
        if slot_frame:
            # Limpiar slot manteniendo las propiedades del frame
            for widget in slot_frame.winfo_children():
                widget.destroy()
            
            # Asegurar que las propiedades del frame se mantengan
            slot_width = 280 if self.grid_cols == 1 else 140  # Ajustar ancho según layout
            slot_frame.configure(width=slot_width, height=120)
            slot_frame.grid_propagate(False)
            slot_frame.pack_propagate(False)
            
            # Determinar icono según tipo de tarjeta
            icon_key = card_type  # '5542' o '5528'
            
            # Determinar estilo según estado activo
            bg_color = COLOR_PRIMARY_BLUE if is_active else COLOR_BG_PANEL
            fg_color = 'white' if is_active else COLOR_TEXT_PRIMARY
            border_width = 3 if is_active else 1
            
            # Crear botón con icono - sin bordes
            icon_image = self.icons.get(icon_key)
            
            btn = tk.Button(slot_frame, 
                           image=icon_image,
                           text=card_name,
                           compound=tk.TOP,
                           font=FONT_TINY,
                           bg=bg_color,
                           fg=fg_color,
                           relief=tk.FLAT,
                           bd=0,
                           highlightthickness=0 if not is_active else 2,
                           highlightcolor='white' if is_active else None,
                           command=lambda sid=session_id: self.select_card(sid))
            btn.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
            
            # Configurar scroll del ratón para el nuevo botón
            btn.bind("<MouseWheel>", self._on_mousewheel)
            btn.bind("<Button-4>", self._on_mousewheel)
            btn.bind("<Button-5>", self._on_mousewheel)
            
            # Mantener referencia fuerte a la imagen para evitar garbage collection
            btn.image = icon_image
            
            self.card_buttons[slot_index] = btn
            
        return True
    
    def remove_card(self, session_id):
        """Elimina una tarjeta del explorador y restaura slot vacío"""
        # Encontrar la tarjeta a eliminar
        card_to_remove = None
        for card in self.card_data:
            if card['session_id'] == session_id:
                card_to_remove = card
                break
        
        if card_to_remove is None:
            return False
        
        # Encontrar el botón correspondiente al slot
        slot_index = card_to_remove['slot_index']
        if slot_index < len(self.card_buttons) and self.card_buttons[slot_index]:
            # Limpiar el botón existente manteniendo propiedades del frame
            button = self.card_buttons[slot_index]
            slot_frame = button.master
            
            # Destruir el botón actual
            button.destroy()
            
            # Asegurar que las propiedades del frame se mantengan
            slot_frame.configure(width=140, height=120)
            slot_frame.grid_propagate(False)
            slot_frame.pack_propagate(False)
            
            # Crear label vacío de reemplazo
            empty_label = tk.Label(slot_frame, text="Empty\nSlot", 
                                  font=FONT_TINY, bg=COLOR_BG_PANEL, 
                                  fg=COLOR_TEXT_DISABLED)
            empty_label.pack(expand=True)
            
            # Resetear el botón en la lista
            self.card_buttons[slot_index] = None
        
        # Remover de card_data
        self.card_data.remove(card_to_remove)
        
        return True
    
    def select_card(self, session_id):
        """Selecciona una tarjeta por session_id"""
        if self.card_select_callback:
            self.card_select_callback(session_id)
    
    def set_active_card(self, session_id):
        """Marca una tarjeta como activa"""
        for i, card in enumerate(self.card_data):
            if card['session_id'] == session_id:
                card['is_active'] = True
            else:
                card['is_active'] = False
        
        # Actualizar visualización
        self.update_visual_states()
    
    def update_visual_states(self):
        """Actualiza los estados visuales de las tarjetas"""
        for i, card in enumerate(self.card_data):
            if i < len(self.card_buttons) and self.card_buttons[card['slot_index']]:
                btn = self.card_buttons[card['slot_index']]
                
                # Usar icono según tipo de tarjeta
                icon_key = card['type']  # '5542' o '5528'
                
                # Actualizar icono
                if icon_key in self.icons and self.icons[icon_key]:
                    btn.config(image=self.icons[icon_key])
                
                # Actualizar estilo visual para tarjeta activa
                if card['is_active']:
                    btn.config(bg=COLOR_PRIMARY_BLUE, 
                              fg='white',
                              relief=tk.FLAT,
                              bd=0,
                              highlightthickness=2,
                              highlightcolor='white')
                else:
                    btn.config(bg=COLOR_BG_PANEL, 
                              fg=COLOR_TEXT_PRIMARY,
                              relief=tk.FLAT,
                              bd=0,
                              highlightthickness=0)
                
                # Actualizar estilo del botón
                if card['is_active']:
                    btn.config(bg=COLOR_PRIMARY_BLUE, fg=COLOR_TEXT_BUTTON_ENABLED, relief=tk.SUNKEN)
                else:
                    btn.config(bg=COLOR_BG_PANEL, fg=COLOR_TEXT_PRIMARY, relief=tk.RAISED)
    
    def get_card_count(self):
        """Retorna el número de tarjetas abiertas"""
        return len(self.card_data)
    
    def is_full(self):
        """Verifica si el explorador está lleno"""
        return len(self.card_data) >= self.max_cards

    def update_layout(self, cards_per_row):
        """Actualiza el layout del grid según la configuración"""
        # Guardar datos actuales de las tarjetas
        current_cards = self.card_data.copy()
        
        # Actualizar configuración del grid
        self.grid_cols = cards_per_row
        self.grid_rows = 8 if cards_per_row == 1 else 4
        
        # Limpiar grid actual
        self.card_buttons = []
        self.card_data = []
        
        # Destruir widgets existentes en icons_frame
        for widget in self.icons_frame.winfo_children():
            widget.destroy()
        
        # Forzar actualización después de destruir widgets
        self.icons_frame.update_idletasks()
        
        # Recrear el grid con la nueva configuración
        self.create_empty_slots()
        
        # Forzar actualización después de crear slots
        self.icons_frame.update_idletasks()
        
        # Restaurar las tarjetas existentes
        for card_info in current_cards:
            self.add_card(
                card_info['name'], 
                card_info['type'], 
                card_info['session_id'], 
                card_info['is_active']
            )
        
        # Actualizar scroll region y forzar redibujado
        if hasattr(self, 'canvas'):
            self.canvas.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            self.canvas.update()
