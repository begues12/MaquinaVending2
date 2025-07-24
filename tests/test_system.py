#!/usr/bin/env python3
"""
Script de prueba para verificar funcionalidad del sistema
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:17458"

def test_api():
    """Probar las nuevas APIs"""
    print("🧪 Iniciando pruebas del sistema...\n")
    
    # 1. Probar API de puertas
    print("1️⃣ Probando API de puertas...")
    try:
        response = requests.get(f"{BASE_URL}/api/doors")
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                doors = data['doors']
                print(f"   ✅ {len(doors)} puertas cargadas correctamente")
                for door_id, door in doors.items():
                    product = door.get('product')
                    if product:
                        print(f"   📦 {door_id}: {product['name']} - €{product['price']} (Stock: {product['stock']})")
                    else:
                        print(f"   📭 {door_id}: Sin producto configurado")
            else:
                print("   ❌ Error en respuesta de API")
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
    
    print()
    
    # 2. Probar modo reposición
    print("2️⃣ Probando modo reposición...")
    try:
        # Obtener estado actual
        response = requests.get(f"{BASE_URL}/api/restock/mode")
        if response.status_code == 200:
            data = response.json()
            current_mode = data['restock_mode']['active']
            print(f"   📋 Estado actual: {'ACTIVO' if current_mode else 'INACTIVO'}")
            
            # Simular presión del botón (solo Windows)
            print("   🔘 Simulando presión del botón de reposición...")
            response = requests.post(f"{BASE_URL}/api/restock/simulate")
            if response.status_code == 200:
                data = response.json()
                new_mode = data['restock_mode']
                print(f"   ✅ Modo cambiado a: {'ACTIVO' if new_mode else 'INACTIVO'}")
            else:
                print(f"   ❌ Error al simular botón: {response.status_code}")
        else:
            print(f"   ❌ Error al obtener estado: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # 3. Probar reposición (solo si modo activo)
    print("3️⃣ Probando reposición de puerta A1...")
    try:
        # Verificar que modo esté activo
        response = requests.get(f"{BASE_URL}/api/restock/mode")
        if response.status_code == 200:
            data = response.json()
            if data['restock_mode']['active']:
                # Hacer reposición
                restock_data = {
                    "quantity": 3,
                    "operator": "test_script",
                    "notes": "Prueba automática del sistema"
                }
                response = requests.post(f"{BASE_URL}/api/restock/door/A1", 
                                       json=restock_data)
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ {data['message']}")
                    print(f"   📊 Nuevo stock: {data['new_stock']}")
                else:
                    print(f"   ❌ Error en reposición: {response.status_code}")
            else:
                print("   ⚠️ Modo reposición no activo, saltando prueba")
        else:
            print(f"   ❌ Error al verificar modo: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # 4. Probar ventas del día
    print("4️⃣ Probando API de ventas...")
    try:
        response = requests.get(f"{BASE_URL}/api/sales/today")
        if response.status_code == 200:
            data = response.json()
            print(f"   📈 Ventas hoy: {data['total_sales']}")
            print(f"   💰 Total recaudado: €{data['total_amount']:.2f}")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # 5. Probar lista de productos
    print("5️⃣ Probando API de productos...")
    try:
        response = requests.get(f"{BASE_URL}/api/products")
        if response.status_code == 200:
            data = response.json()
            products = data['products']
            print(f"   📦 {len(products)} productos en base de datos")
            active_products = [p for p in products if p['active']]
            print(f"   ✅ {len(active_products)} productos activos")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n🎉 Pruebas completadas!")

if __name__ == "__main__":
    test_api()
