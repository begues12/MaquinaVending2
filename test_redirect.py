#!/usr/bin/env python3
"""
Test script para verificar la funcionalidad de redirección
"""
import requests
import json
import time

base_url = "http://127.0.0.1:57788"

def test_development_mode():
    """Verificar modo desarrollo"""
    try:
        response = requests.get(f"{base_url}/api/config/development")
        if response.status_code == 200:
            data = response.json()
            print(f"Modo desarrollo: {data}")
            return data.get('development_mode', False)
        else:
            print(f"Error verificando modo desarrollo: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error conectando con la aplicación: {e}")
        return False

def test_gpio_simulation():
    """Simular presión del botón GPIO"""
    try:
        response = requests.post(f"{base_url}/api/test/gpio-button")
        if response.status_code == 200:
            data = response.json()
            print(f"Simulación GPIO: {data}")
            return True
        else:
            print(f"Error simulando GPIO: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error simulando GPIO: {e}")
        return False

def test_redirect_status():
    """Verificar estado de redirección"""
    try:
        response = requests.get(f"{base_url}/api/restock/redirect-status")
        if response.status_code == 200:
            data = response.json()
            print(f"Estado redirección: {data}")
            return data
        else:
            print(f"Error verificando redirección: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error verificando redirección: {e}")
        return None

def main():
    print("=== Test de Redirección GPIO ===\n")
    
    # 1. Verificar modo desarrollo
    print("1. Verificando modo desarrollo...")
    if not test_development_mode():
        print("❌ Modo desarrollo no activo")
        return
    print("✅ Modo desarrollo activo\n")
    
    # 2. Verificar estado inicial
    print("2. Estado inicial de redirección...")
    initial_status = test_redirect_status()
    if not initial_status:
        print("❌ No se pudo obtener estado inicial")
        return
    print(f"✅ Estado inicial: {initial_status}\n")
    
    # 3. Simular botón GPIO
    print("3. Simulando presión del botón GPIO...")
    if not test_gpio_simulation():
        print("❌ Error simulando GPIO")
        return
    print("✅ GPIO simulado correctamente\n")
    
    # 4. Verificar nuevo estado
    print("4. Verificando nuevo estado de redirección...")
    time.sleep(1)  # Esperar un poco
    new_status = test_redirect_status()
    if not new_status:
        print("❌ No se pudo obtener nuevo estado")
        return
    
    print(f"✅ Nuevo estado: {new_status}")
    
    if new_status.get('redirect_requested'):
        print("🎉 Redirección solicitada correctamente!")
    else:
        print("❌ La redirección no se activó")

if __name__ == "__main__":
    main()
