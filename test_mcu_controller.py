#!/usr/bin/env python3
"""
Script de pruebas para el Controlador MCU
Prueba todas las funcionalidades sin implementar en producción
"""

import json
import time
import threading
from datetime import datetime
from controllers.mcu_controller import MCUController, PaymentMethod, MCUCommand

def load_mcu_config():
    """Cargar configuración del MCU"""
    try:
        with open('mcu_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config['mcu']
    except Exception as e:
        print(f"Error cargando configuración: {e}")
        return {
            'connection': {
                'port': '/dev/ttyUSB0',
                'baudrate': 115200,
                'timeout': 5
            }
        }

def test_basic_connection():
    """Probar conexión básica"""
    print("\n🔧 === PRUEBA DE CONEXIÓN BÁSICA ===")
    
    config = load_mcu_config()
    mcu = MCUController(config['connection'])
    
    # Listar puertos disponibles
    ports = mcu.list_ports()
    print(f"Puertos disponibles: {ports}")
    
    # Probar conexión
    test_result = mcu.test_connection()
    print(f"Prueba de conexión: {test_result}")
    
    # Conectar
    if mcu.connect():
        print("✅ Conexión exitosa")
        
        # Obtener versión
        version = mcu.get_version()
        print(f"Versión MCU: {version}")
        
        # Obtener estado
        status = mcu.get_status()
        print(f"Estado completo: {json.dumps(status, indent=2, default=str)}")
        
        mcu.disconnect()
        return True
    else:
        print("❌ Error en conexión")
        return False

def test_payment_flow():
    """Probar flujo completo de pago"""
    print("\n💳 === PRUEBA DE FLUJO DE PAGO ===")
    
    config = load_mcu_config()
    mcu = MCUController(config['connection'])
    
    if not mcu.connect():
        print("❌ No se pudo conectar para prueba de pago")
        return False
    
    try:
        # Configurar callback de eventos
        def on_payment_event(data):
            print(f"🔔 Evento de pago: {data}")
        
        mcu.add_event_callback('payment_started', on_payment_event)
        mcu.add_event_callback('payment_completed', on_payment_event)
        mcu.add_event_callback('payment_failed', on_payment_event)
        
        # Iniciar pago
        print("Iniciando pago de 5.50 EUR...")
        transaction = mcu.start_payment(5.50, "EUR", PaymentMethod.CONTACTLESS, "A1")
        
        if transaction:
            print(f"✅ Transacción iniciada: {transaction.transaction_id}")
            print(f"   Método: {transaction.method.value}")
            print(f"   Cantidad: {transaction.amount} {transaction.currency}")
            
            # Monitorear pago durante 10 segundos
            for i in range(10):
                status = mcu.get_payment_status()
                if status:
                    print(f"   Estado ({i+1}s): {status['transaction']['status']}")
                    
                    # Simular confirmación en el segundo 5
                    if i == 4:
                        print("   💳 Simulando pago exitoso...")
                        if mcu.confirm_payment():
                            print("   ✅ Pago confirmado")
                            break
                
                time.sleep(1)
            
            # Si no se confirmó, cancelar
            if mcu.current_transaction:
                print("   ⏰ Timeout - cancelando pago...")
                mcu.cancel_payment()
        
        else:
            print("❌ Error iniciando transacción")
        
        # Mostrar historial
        history = mcu.get_transaction_history()
        print(f"\n📊 Historial de transacciones: {len(history)} transacciones")
        for tx in history[-3:]:  # Últimas 3
            print(f"   {tx['transaction_id']}: {tx['status']} - {tx['amount']} {tx['currency']}")
        
        return True
        
    finally:
        mcu.disconnect()

def test_door_control():
    """Probar control de puertas"""
    print("\n🚪 === PRUEBA DE CONTROL DE PUERTAS ===")
    
    config = load_mcu_config()
    mcu = MCUController(config['connection'])
    
    if not mcu.connect():
        print("❌ No se pudo conectar para prueba de puertas")
        return False
    
    try:
        # Configurar callbacks
        def on_door_event(data):
            print(f"🔔 Evento puerta: {data}")
        
        mcu.add_event_callback('door_opened', on_door_event)
        mcu.add_event_callback('door_closed', on_door_event)
        
        # Probar puertas A1, A2, B1
        doors_to_test = ["A1", "A2", "B1"]
        
        for door_id in doors_to_test:
            print(f"\nProbando puerta {door_id}:")
            
            # Estado inicial
            status = mcu.get_door_status(door_id)
            print(f"   Estado inicial: {status}")
            
            # Abrir puerta
            if mcu.open_door(door_id, 5.0):
                print(f"   ✅ Puerta {door_id} abierta")
                
                # Esperar 2 segundos
                time.sleep(2)
                
                # Verificar estado
                status = mcu.get_door_status(door_id)
                print(f"   Estado después de abrir: {status}")
                
                # Cerrar puerta
                if mcu.close_door(door_id):
                    print(f"   ✅ Puerta {door_id} cerrada")
                else:
                    print(f"   ❌ Error cerrando puerta {door_id}")
            else:
                print(f"   ❌ Error abriendo puerta {door_id}")
        
        # Estado de todas las puertas
        all_doors = mcu.get_door_status()
        print(f"\n📊 Estado de todas las puertas:")
        print(json.dumps(all_doors, indent=2))
        
        return True
        
    finally:
        mcu.disconnect()

def test_sensors():
    """Probar lectura de sensores"""
    print("\n📡 === PRUEBA DE SENSORES ===")
    
    config = load_mcu_config()
    mcu = MCUController(config['connection'])
    
    if not mcu.connect():
        print("❌ No se pudo conectar para prueba de sensores")
        return False
    
    try:
        # Sensores a probar
        sensors_to_test = ["door_sensor_A1", "door_sensor_A2", "temp_sensor", "humidity_sensor"]
        
        print("Leyendo sensores individuales:")
        for sensor_id in sensors_to_test:
            value = mcu.read_sensor(sensor_id)
            print(f"   {sensor_id}: {value}")
        
        # Leer todos los sensores
        print("\nEstado de todos los sensores:")
        all_sensors = mcu.get_all_sensors()
        print(json.dumps(all_sensors, indent=2))
        
        return True
        
    finally:
        mcu.disconnect()

def test_restock_mode():
    """Probar modo restock"""
    print("\n📦 === PRUEBA DE MODO RESTOCK ===")
    
    config = load_mcu_config()
    mcu = MCUController(config['connection'])
    
    if not mcu.connect():
        print("❌ No se pudo conectar para prueba de restock")
        return False
    
    try:
        # Configurar callbacks
        def on_restock_event(data):
            print(f"🔔 Evento restock: {data}")
        
        mcu.add_event_callback('restock_enabled', on_restock_event)
        mcu.add_event_callback('restock_disabled', on_restock_event)
        
        # Activar modo restock
        print("Activando modo restock...")
        if mcu.enable_restock_mode():
            print("✅ Modo restock activado")
            
            # Esperar 3 segundos
            time.sleep(3)
            
            # Desactivar modo restock
            print("Desactivando modo restock...")
            if mcu.disable_restock_mode():
                print("✅ Modo restock desactivado")
            else:
                print("❌ Error desactivando modo restock")
        else:
            print("❌ Error activando modo restock")
        
        return True
        
    finally:
        mcu.disconnect()

def test_utilities():
    """Probar utilidades (LEDs, buzzer, display)"""
    print("\n💡 === PRUEBA DE UTILIDADES ===")
    
    config = load_mcu_config()
    mcu = MCUController(config['connection'])
    
    if not mcu.connect():
        print("❌ No se pudo conectar para prueba de utilidades")
        return False
    
    try:
        # Probar LEDs
        print("Probando LEDs...")
        colors = ["red", "green", "blue", "white"]
        for color in colors:
            if mcu.set_led("status_led", color, 80):
                print(f"   ✅ LED {color} activado")
                time.sleep(0.5)
            else:
                print(f"   ❌ Error con LED {color}")
        
        # Apagar LED
        mcu.set_led("status_led", "off", 0)
        
        # Probar buzzer
        print("\nProbando buzzer...")
        frequencies = [1000, 1500, 2000]
        for freq in frequencies:
            if mcu.buzzer(freq, 0.3):
                print(f"   ✅ Buzzer {freq}Hz")
                time.sleep(0.5)
            else:
                print(f"   ❌ Error buzzer {freq}Hz")
        
        # Probar display
        print("\nProbando display...")
        messages = ["Prueba MCU", "Sistema OK", "Vending Ready"]
        for msg in messages:
            if mcu.display_message(msg, 2.0):
                print(f"   ✅ Display: '{msg}'")
                time.sleep(2.5)
            else:
                print(f"   ❌ Error display: '{msg}'")
        
        return True
        
    finally:
        mcu.disconnect()

def test_stress_test():
    """Prueba de estrés - múltiples operaciones"""
    print("\n⚡ === PRUEBA DE ESTRÉS ===")
    
    config = load_mcu_config()
    mcu = MCUController(config['connection'])
    
    if not mcu.connect():
        print("❌ No se pudo conectar para prueba de estrés")
        return False
    
    try:
        start_time = time.time()
        operations = 0
        
        print("Ejecutando 50 operaciones variadas...")
        
        for i in range(50):
            operation_type = i % 5
            
            if operation_type == 0:
                # Status check
                mcu.get_status()
                operations += 1
            elif operation_type == 1:
                # Door status
                mcu.get_door_status()
                operations += 1
            elif operation_type == 2:
                # Sensor reading
                mcu.get_all_sensors()
                operations += 1
            elif operation_type == 3:
                # LED control
                mcu.set_led("status_led", "blue", 50)
                operations += 1
            elif operation_type == 4:
                # Version check
                mcu.get_version()
                operations += 1
            
            if i % 10 == 0:
                print(f"   Progreso: {i+1}/50 operaciones")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Prueba completada:")
        print(f"   Operaciones: {operations}")
        print(f"   Tiempo: {duration:.2f} segundos")
        print(f"   Ops/seg: {operations/duration:.2f}")
        
        return True
        
    finally:
        mcu.disconnect()

def test_monitoring():
    """Probar sistema de monitoreo"""
    print("\n📊 === PRUEBA DE MONITOREO ===")
    
    config = load_mcu_config()
    mcu = MCUController(config['connection'])
    
    if not mcu.connect():
        print("❌ No se pudo conectar para prueba de monitoreo")
        return False
    
    try:
        print("Monitoreando durante 15 segundos...")
        
        start_time = time.time()
        while time.time() - start_time < 15:
            status = mcu.get_status()
            print(f"   Estado MCU: {status['controller_status']} | "
                  f"Conectado: {status['connected']} | "
                  f"Último ping: {status['last_ping']}")
            time.sleep(3)
        
        print("✅ Monitoreo completado")
        return True
        
    finally:
        mcu.disconnect()

def main():
    """Función principal de pruebas"""
    print("🚀 === SUITE DE PRUEBAS CONTROLADOR MCU ===")
    print("Esto probará todas las funcionalidades sin implementar en producción")
    
    tests = [
        ("Conexión Básica", test_basic_connection),
        ("Flujo de Pago", test_payment_flow),
        ("Control de Puertas", test_door_control),
        ("Sensores", test_sensors),
        ("Modo Restock", test_restock_mode),
        ("Utilidades", test_utilities),
        ("Prueba de Estrés", test_stress_test),
        ("Monitoreo", test_monitoring)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ PASÓ" if result else "❌ FALLÓ"
            print(f"{status} - {test_name}")
        except Exception as e:
            results[test_name] = False
            print(f"❌ ERROR - {test_name}: {e}")
    
    # Resumen final
    print(f"\n{'='*60}")
    print("📊 RESUMEN DE PRUEBAS:")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"   {status} {test_name}")
    
    print(f"\nResultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! El controlador MCU está listo.")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisar implementación.")

if __name__ == "__main__":
    main()
