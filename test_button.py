#!/usr/bin/env python3
"""
Script de prueba para verificar la detección del botón en el pin 16
"""

import sys
import time
from controllers.hardware_controller import hardware_controller

def test_restock_button():
    """Probar el botón de restock"""
    print("=== Test del Botón de Restock (Pin 16) ===")
    
    # Obtener información del botón
    button_state = hardware_controller.get_restock_button_state()
    print(f"Estado del botón: {button_state}")
    
    if not button_state.get('initialized', False):
        print("❌ Error: Botón no inicializado")
        if 'error' in button_state:
            print(f"   Error: {button_state['error']}")
        return
    
    print("✅ Botón inicializado correctamente")
    print(f"   Pin: {button_state.get('pin')}")
    print(f"   Habilitado: {button_state.get('enabled')}")
    
    print("\n🔘 Monitoreando botón (presiona Ctrl+C para salir)")
    print("   Presiona el botón conectado al pin 16...")
    
    try:
        last_state = False
        while True:
            current_state = hardware_controller.is_restock_button_pressed()
            
            if current_state != last_state:
                if current_state:
                    print("🔴 BOTÓN PRESIONADO")
                else:
                    print("⚪ Botón liberado")
                last_state = current_state
            
            time.sleep(0.1)  # Check every 100ms
            
    except KeyboardInterrupt:
        print("\n\n✅ Test finalizado")

if __name__ == "__main__":
    test_restock_button()
