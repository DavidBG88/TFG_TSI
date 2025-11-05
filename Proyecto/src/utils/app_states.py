"""
Estados de la aplicación para control de interfaz
"""

class AppStates:
    """Enumera los diferentes estados de la aplicación"""
    
    # Estados principales
    INITIAL = "initial"                   # Al iniciar - solo New/Open/UserConf
    CARD_LOADED = "card_loaded"           # Tarjeta cargada - solo Select Card
    CARD_SELECTED = "card_selected"       # Select Card ejecutado - APDUs básicas
    PSC_PRESENTED = "psc_presented"       # PSC correcto - APDUs completas
    CARD_BLOCKED = "card_blocked"         # Tarjeta bloqueada - solo SELECT y READ
    
    # Sub-estados
    NO_CARDS = "no_cards"                 # Sin tarjetas abiertas
    MULTIPLE_CARDS = "multiple_cards"     # Múltiples tarjetas abiertas

class ButtonStates:
    """Define qué botones están habilitados en cada estado"""
    
    # Definición de estados de botones
    STATES = {
        AppStates.INITIAL: {
            # Comandos de archivo - SOLO ESTOS 3 HABILITADOS AL INICIO
            'new_card': True,      #  NEW CARD
            'open_card': True,     #  OPEN CARD
            'save_card': False,    #  SAVE CARD
            'clear_card': False,   #  CLEAR CARD
            'close_card': False,   #  CLOSE CARD

            # APDUs - TODOS DESHABILITADOS AL INICIO
            'select_card': False,           #  SELECT CARD
            'read_memory': False,           #  READ MEMORY
            'present_psc': False,           #  PRESENT PSC
            'write_memory': False,          #  WRITE MEMORY
            'change_psc': False,            #  CHANGE PSC
            'read_error_counter': False,    #  READ ERROR COUNTER
            'read_protection_bits': False,  #  READ PROTECTION BITS
            'write_protect': False,         #  WRITE PROTECT
            
            # Configuración
            'user_config': True    #  USER CONF
        },
        
        AppStates.CARD_LOADED: {
            'new_card': True,
            'open_card': True,
            'save_card': True,
            'clear_card': True,
            'close_card': True,
            
            'select_card': True,
            'read_memory': False,
            'present_psc': False,
            'write_memory': False,
            'change_psc': False,
            'read_error_counter': False,
            'read_protection_bits': False, #  READ PROTECTION BITS
            'write_protect': False,        #  WRITE PROTECT
            
            # Configuración
            'user_config': True            #  USER CONF (sigue habilitado)
        },
        
        AppStates.CARD_SELECTED: {
            # Comandos de archivo
            'new_card': True,
            'open_card': True,
            'save_card': True,
            'clear_card': True,
            'close_card': True,
            
            # APDUs básicas (sin PSC)
            'select_card': True,
            'read_memory': True,
            'present_psc': True,
            'read_error_counter': True,
            'read_protection_bits': True,
            'write_memory': False,      # Requiere PSC
            'change_psc': False,        # Requiere PSC
            'write_protect': False,     # Requiere PSC
            
            # Configuración
            'user_config': True
        },
        
        AppStates.PSC_PRESENTED: {
            # Comandos de archivo
            'new_card': True,
            'open_card': True,
            'save_card': True,
            'clear_card': True,
            'close_card': True,
            
            # APDUs completas (con PSC)
            'select_card': True,
            'read_memory': True,
            'present_psc': True,
            'read_error_counter': True,
            'read_protection_bits': True,
            'write_memory': True,
            'change_psc': True,
            'write_protect': True,
            
            # Configuración
            'user_config': True
        },
        
        AppStates.CARD_BLOCKED: {
            # Comandos de archivo
            'new_card': True,
            'open_card': True,
            'save_card': True,
            'clear_card': True,
            'close_card': True,
            
            # Solo SELECT y READ permitidos cuando está bloqueada
            'select_card': True,           #  SELECT CARD
            'read_memory': True,           #  READ MEMORY
            'read_error_counter': True,    #  READ ERROR COUNTER
            'present_psc': False,          #  PRESENT PSC (bloqueado)
            'write_memory': False,         #  WRITE MEMORY (bloqueado)
            'change_psc': False,           #  CHANGE PSC (bloqueado)
            'read_protection_bits': True,  #  READ PROTECTION BITS
            'write_protect': False,        #  WRITE PROTECT (bloqueado)
            
            # Configuración
            'user_config': True
        }
    }
    
    @classmethod
    def get_button_state(cls, app_state, button_name):
        """Obtiene el estado de un botón específico"""
        return cls.STATES.get(app_state, {}).get(button_name, False)
    
    @classmethod
    def get_all_button_states(cls, app_state):
        """Obtiene todos los estados de botones para un estado de app"""
        return cls.STATES.get(app_state, {})

class CardStates:
    """Estados específicos de las tarjetas"""
    
    FACTORY = "factory"           # Estado de fábrica
    INITIALIZED = "initialized"   # Inicializada pero sin seleccionar
    SELECTED = "selected"         # Seleccionada (Select Card ejecutado)
    PSC_VERIFIED = "psc_verified" # PSC presentado correctamente
    BLOCKED = "blocked"           # Tarjeta bloqueada (error counter = 0)