#!/usr/bin/env python3
"""
Script de prueba para verificar la detección del botón en el pin 16
y la integración con el sistema de restock
"""

import sys
import time
import requests
from controllers.hardware_controller import hardware_controller
from controllers.restock_controller import restock_controller

def test_hardware_button():
    """Probar el botón usando hardware_controller"""
    print("=== Test del Hardware Controller ===")
    
    # Obtener información del botón
    button_state = hardware_controller.get_restock_button_state()
    print(f"Estado del botón (hardware): {button_state}")
    
    if not button_state.get('initialized', False):
        print("❌ Error: Botón no inicializado en hardware_controller")
        if 'error' in button_state:
            print(f"   Error: {button_state['error']}")
        return False
    
    print("✅ Botón inicializado correctamente en hardware_controller")
    return True

def test_restock_integration():
    """Probar la integración con restock_controller"""
    print("\n=== Test del Restock Controller ===")
    
    # Verificar integración
    button_pressed = restock_controller.check_physical_button()
    print(f"Botón presionado (restock): {button_pressed}")
    
    # Probar manejo de presión
    if button_pressed:
        handled = restock_controller.handle_button_press()
        print(f"Presión manejada: {handled}")
        
        # Verificar estado de redirección
        redirect_info = restock_controller.is_redirect_requested()
        print(f"Redirección solicitada: {redirect_info}")
    
    return True

def test_endpoints():
    """Probar los endpoints HTTP"""
    print("\n=== Test de Endpoints HTTP ===")
    
    base_url = "http://localhost:5000"
    
    try:
        # Test endpoint hardware
        print("Probando /api/hardware/restock-button/state...")
        response = requests.get(f"{base_url}/api/hardware/restock-button/state")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Hardware endpoint: {data}")
        else:
            print(f"❌ Hardware endpoint error: {response.status_code}")
    
        # Test endpoint restock  
        print("Probando /api/restock/button/check...")
        response = requests.get(f"{base_url}/api/restock/button/check")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Restock endpoint: {data}")
        else:
            print(f"❌ Restock endpoint error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor. ¿Está ejecutándose Flask?")
        return False
    except Exception as e:
        print(f"❌ Error en endpoints: {e}")
        return False
    
    return True

def monitor_button():
    """Monitorear el botón en tiempo real"""
    print("\n=== Monitoreo en Tiempo Real ===")
    print("🔘 Monitoreando botón (presiona Ctrl+C para salir)")
    print("   Presiona el botón conectado al pin 16...")
    
    try:
        last_state = False
        last_redirect = False
        
        while True:
            # Verificar estado del botón
            current_state = hardware_controller.is_restock_button_pressed()
            
            # Verificar estado de redirección
            redirect_info = restock_controller.is_redirect_requested()
            current_redirect = redirect_info.get('redirect_requested', False)
            
            # Mostrar cambios de estado
            if current_state != last_state:
                if current_state:
                    print("🔴 BOTÓN PRESIONADO")
                    # Manejar presión
                    restock_controller.handle_button_press()
                else:
                    print("⚪ Botón liberado")
                last_state = current_state
            
            if current_redirect != last_redirect:
                if current_redirect:
                    print("🚀 REDIRECCIÓN SOLICITADA")
                    print(f"   Timestamp: {redirect_info.get('redirect_timestamp')}")
                else:
                    print("🔄 Redirección limpiada")
                last_redirect = current_redirect
            
            time.sleep(0.1)  # Check every 100ms
            
    except KeyboardInterrupt:
        print("\n\n✅ Monitoreo finalizado")

def main():
    """Función principal de prueba"""
    print("🔧 Script de Prueba del Botón de Restock (Pin 16)")
    print("=" * 50)
    
    # Pruebas paso a paso
    hardware_ok = test_hardware_button()
    if not hardware_ok:
        print("\n❌ Test de hardware falló, abortando...")
        return
    
    integration_ok = test_restock_integration()
    if not integration_ok:
        print("\n❌ Test de integración falló, abortando...")
        return
    
    endpoints_ok = test_endpoints()
    
    print("\n" + "=" * 50)
    print("📊 Resumen de pruebas:")
    print(f"   Hardware Controller: {'✅' if hardware_ok else '❌'}")
    print(f"   Restock Integration: {'✅' if integration_ok else '❌'}")
    print(f"   HTTP Endpoints: {'✅' if endpoints_ok else '❌'}")
    
    if hardware_ok and integration_ok:
        print("\n¿Iniciar monitoreo en tiempo real? (y/n): ", end="")
        if input().lower().startswith('y'):
            monitor_button()

if __name__ == "__main__":
    main()
