"""
Script de prueba para el sistema de hardware
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controllers.hardware_controller import hardware_controller
import time

def test_hardware_system():
    """Probar el sistema de hardware completo"""
    
    print("🔧 PRUEBA DEL SISTEMA DE HARDWARE")
    print("=" * 50)
    
    # 1. Verificar inicialización
    print("1. Verificando inicialización del hardware...")
    if hardware_controller.initialized:
        print("✅ Hardware inicializado correctamente")
        if hasattr(hardware_controller, 'GPIO_AVAILABLE'):
            print(f"📡 GPIO disponible: {'Sí' if hardware_controller.GPIO_AVAILABLE else 'No (modo simulación)'}")
    else:
        print("❌ Error en inicialización del hardware")
        return False
    
    # 2. Obtener estado de todas las puertas
    print("\n2. Obteniendo estado de todas las puertas...")
    doors_state = hardware_controller.get_all_doors_state()
    
    if doors_state:
        print(f"📊 Encontradas {len(doors_state)} puertas configuradas:")
        for door_id, state in doors_state.items():
            print(f"   🚪 {door_id}: GPIO {state['gpio_pin']}, Sensor {state['sensor_pin']}")
            print(f"      Estado: {'🔓 Abierta' if state['is_open'] else '🔒 Cerrada'}")
            print(f"      Relé: {'⚡ Activo' if state['relay_active'] else '💤 Inactivo'}")
    else:
        print("❌ No se pudieron obtener estados de las puertas")
        return False
    
    # 3. Probar una puerta específica
    test_door = list(doors_state.keys())[0]  # Tomar la primera puerta
    print(f"\n3. Probando puerta {test_door}...")
    
    # Registrar callback para eventos
    def door_callback(door_id, is_open):
        print(f"🔔 Evento: Puerta {door_id} {'abierta' if is_open else 'cerrada'}")
    
    hardware_controller.register_door_callback(test_door, door_callback)
    
    # Probar apertura
    print(f"🔓 Abriendo puerta {test_door}...")
    success = hardware_controller.open_door(test_door)
    
    if success:
        print("✅ Comando de apertura enviado correctamente")
        print("⏳ Esperando 3 segundos para que se complete la operación...")
        time.sleep(3.5)  # Esperar más que la duración del relé
        
        # Verificar estado después de la operación
        final_state = hardware_controller.get_door_state(test_door)
        print(f"📊 Estado final - Relé activo: {final_state['relay_active']}")
    else:
        print("❌ Error al abrir la puerta")
    
    # 4. Probar parada de emergencia
    print("\n4. Probando parada de emergencia...")
    hardware_controller.emergency_stop()
    print("✅ Parada de emergencia ejecutada")
    
    # 5. Limpiar callbacks
    hardware_controller.unregister_door_callback(test_door)
    
    print("\n🎉 PRUEBA COMPLETADA")
    print("=" * 50)
    print("RESUMEN:")
    print(f"✅ Hardware {'disponible' if hardware_controller.initialized else 'no disponible'}")
    print(f"📊 {len(doors_state)} puertas configuradas")
    print("💡 Revisa los logs para más detalles")
    
    return True

def test_individual_door():
    """Probar una puerta individualmente"""
    doors_state = hardware_controller.get_all_doors_state()
    door_list = list(doors_state.keys())
    
    if not door_list:
        print("❌ No hay puertas configuradas")
        return
    
    print("\n🚪 PUERTAS DISPONIBLES:")
    for i, door_id in enumerate(door_list, 1):
        print(f"{i}. {door_id}")
    
    try:
        choice = input("\nEscoge el número de la puerta a probar (Enter para cancelar): ").strip()
        if not choice:
            return
            
        door_index = int(choice) - 1
        if 0 <= door_index < len(door_list):
            door_id = door_list[door_index]
            
            print(f"\n🧪 Probando puerta {door_id}...")
            success = hardware_controller.test_door(door_id)
            
            if success:
                print(f"✅ Prueba de puerta {door_id} exitosa")
            else:
                print(f"❌ Prueba de puerta {door_id} falló")
        else:
            print("❌ Número de puerta inválido")
            
    except ValueError:
        print("❌ Entrada inválida")
    except KeyboardInterrupt:
        print("\n⏹️ Prueba cancelada")

def interactive_menu():
    """Menú interactivo para pruebas"""
    while True:
        print("\n" + "=" * 50)
        print("🔧 MENÚ DE PRUEBAS DE HARDWARE")
        print("=" * 50)
        print("1. Prueba completa del sistema")
        print("2. Probar puerta individual")
        print("3. Ver estado de todas las puertas")
        print("4. Parada de emergencia")
        print("5. Salir")
        print("-" * 50)
        
        try:
            choice = input("Escoge una opción (1-5): ").strip()
            
            if choice == "1":
                test_hardware_system()
            elif choice == "2":
                test_individual_door()
            elif choice == "3":
                doors_state = hardware_controller.get_all_doors_state()
                print("\n📊 ESTADO DE TODAS LAS PUERTAS:")
                for door_id, state in doors_state.items():
                    print(f"🚪 {door_id}:")
                    print(f"   GPIO Relé: {state['gpio_pin']}")
                    print(f"   GPIO Sensor: {state['sensor_pin']}")
                    print(f"   Estado: {'🔓 Abierta' if state['is_open'] else '🔒 Cerrada'}")
                    print(f"   Relé: {'⚡ Activo' if state['relay_active'] else '💤 Inactivo'}")
                    if state['last_opened']:
                        print(f"   Última apertura: {time.ctime(state['last_opened'])}")
                    print()
            elif choice == "4":
                if input("⚠️ ¿Confirmas parada de emergencia? (y/N): ").lower().startswith('y'):
                    hardware_controller.emergency_stop()
                    print("🛑 Parada de emergencia ejecutada")
            elif choice == "5":
                print("👋 ¡Hasta luego!")
                break
            else:
                print("❌ Opción inválida")
                
        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas del sistema de hardware...")
    
    # Verificar que el hardware controller se inicialice
    if not hardware_controller.initialized:
        print("❌ Error: No se pudo inicializar el controlador de hardware")
        print("💡 Verifica la configuración en machine_config.json")
        sys.exit(1)
    
    try:
        interactive_menu()
    finally:
        # Limpiar recursos
        print("🧹 Limpiando recursos...")
        hardware_controller.cleanup()
