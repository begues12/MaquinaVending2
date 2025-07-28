"""
Controlador de Hardware para Relés y Sensores de Puertas
Gestiona la apertura de puertas mediante relés y detecta el cierre con sensores
"""
import time
import threading
import logging
logger = logging.getLogger(__name__)
from typing import Dict, Optional, Callable
import json
from gpiozero import OutputDevice, Button
import os

# Intentar importar RPi.GPIO, si no está disponible (desarrollo), usar mock
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("RPi.GPIO no disponible - usando modo simulación")
    
    # Mock para desarrollo sin Raspberry Pi
    class MockGPIO:
        BCM = "BCM"
        OUT = "OUT"
        IN = "IN"
        PUD_UP = "PUD_UP"
        PUD_DOWN = "PUD_DOWN"
        HIGH = 1
        LOW = 0
        RISING = "RISING"
        FALLING = "FALLING"
        BOTH = "BOTH"
        
        _pin_states = {}  # Simular estados de pines
        
        @staticmethod
        def setmode(mode): 
            print(f"SIMULACIÓN GPIO: Modo configurado a {mode}")
        
        @staticmethod
        def setwarnings(warnings): 
            print(f"SIMULACIÓN GPIO: Warnings = {warnings}")
        
        @staticmethod
        def setup(pin, mode, pull_up_down=None): 
            MockGPIO._pin_states[pin] = MockGPIO.LOW
            print(f"SIMULACIÓN GPIO: Pin {pin} configurado como {mode}")
        
        @staticmethod
        def output(pin, state): 
            MockGPIO._pin_states[pin] = state
            estado_texto = "HIGH" if state == MockGPIO.HIGH else "LOW"
            print(f"SIMULACIÓN GPIO: Pin {pin} -> {estado_texto} ({'Relé ACTIVADO' if state == MockGPIO.HIGH else 'Relé DESACTIVADO'})")
        
        @staticmethod
        def input(pin): 
            return MockGPIO._pin_states.get(pin, MockGPIO.LOW)
        
        @staticmethod
        def add_event_detect(pin, edge, callback=None, bouncetime=None): 
            print(f"SIMULACIÓN GPIO: Event detect configurado en pin {pin}")
        
        @staticmethod
        def remove_event_detect(pin): 
            print(f"SIMULACIÓN GPIO: Event detect removido del pin {pin}")
        
        @staticmethod
        def cleanup(): 
            MockGPIO._pin_states.clear()
            print("SIMULACIÓN GPIO: Cleanup completado")
    
    GPIO = MockGPIO()

class HardwareController:
    
    
    def __init__(self, config_path: str = "machine_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.logger = logging.getLogger(__name__)
        # Estados de las puertas
        self.door_states = {}
        self.door_timers = {}
        self.door_callbacks = {}
        # Diccionario para OutputDevice por puerta
        self.door_relays = {}
        # Configuración de relés (valor por defecto, se puede sobrescribir por puerta)
        self.default_relay_duration = 3.0  # Segundos por defecto
        self.sensor_debounce = 200  # Milisegundos de rebote para sensores
        # Botón de restock
        self.restock_button = None
        # Estado de inicialización
        self.initialized = False
        # Inicializar GPIO y relés al crear la instancia
        self._initialize_gpio()
        
    def _load_config(self) -> dict:
        """Cargar configuración desde archivo JSON"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error cargando configuración: {e}")
            return {}
    
    def _save_config(self):
        """Guardar configuración actual al archivo"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error guardando configuración: {e}")
    
    def _initialize_gpio(self):
        """Inicializar configuración de GPIO y crear OutputDevice por puerta"""
        try:
            # Limpiar recursos GPIO antes de inicializar (evita 'GPIO busy' en reinicios)
            try:
                GPIO.cleanup()
                self.logger.info("GPIO cleanup ejecutado antes de inicializar relés")
            except Exception as e:
                self.logger.warning(f"Error en GPIO cleanup previo: {e}")

            doors_config = self.config.get('doors', {})
            self.logger.info(f"Puertas cargadas desde config: {list(doors_config.keys())}")
            for door_id, door_info in doors_config.items():
                self.logger.info(f"Puerta {door_id} -> gpio_pin: {door_info.get('gpio_pin')}")
            # Inicializar estados de puertas y relés
            for door_id, door_info in doors_config.items():
                self.door_states[door_id] = {
                    'is_open': False,
                    'relay_active': False,
                    'last_opened': None,
                    'last_closed': None
                }
                gpio_pin = door_info.get('gpio_pin')
                # Permitir configurar active_high por puerta, por defecto False (relé desactivado al iniciar)
                active_high = door_info.get('active_high', False)
                if gpio_pin is not None:
                    try:
                        self.logger.info(f"Creando OutputDevice para puerta {door_id} en pin {gpio_pin} (active_high={active_high})")
                        self.door_relays[door_id] = OutputDevice(gpio_pin, active_high=active_high, initial_value=False)
                        self.door_relays[door_id].off()
                        self.logger.info(f"OutputDevice creado y apagado para puerta {door_id} en pin {gpio_pin}")
                    except Exception as e:
                        self.logger.error(f"Error creando OutputDevice para puerta {door_id} en pin {gpio_pin}: {e}")
                        # Crear relé simulado como fallback
                        try:
                            simulated_relay = self._create_simulated_relay(door_id, gpio_pin)
                            self.door_relays[door_id] = simulated_relay
                            self.logger.info(f"Relé simulado creado para puerta {door_id} en pin {gpio_pin}")
                        except Exception as fallback_error:
                            self.logger.error(f"Error creando relé simulado para puerta {door_id}: {fallback_error}")
                else:
                    self.logger.warning(f"Puerta {door_id} no tiene gpio_pin configurado, no se crea OutputDevice")
         
            # Inicializar botón de restock si está configurado
            self._initialize_restock_button()
            
            self.initialized = True
            self.logger.info("GPIO inicializado correctamente y relés creados por puerta")
        except Exception as e:
            self.initialized = False
            self.logger.error(f"Error inicializando GPIO: {e}")
    
    def _initialize_restock_button(self):
        """Inicializar botón de restock si está habilitado"""
        try:
            restock_config = self.config.get('machine', {}).get('restock_mode', {})
            if restock_config.get('enabled', False):
                gpio_pin = restock_config.get('gpio_pin')
                if gpio_pin:
                    self.logger.info(f"Inicializando botón de restock en pin {gpio_pin}")
                    try:
                        # Crear botón con pull-up interno (botón conectado a GND)
                        self.restock_button = Button(gpio_pin, pull_up=True, bounce_time=0.1)
                        self.logger.info(f"Botón de restock inicializado en pin {gpio_pin}")
                    except Exception as e:
                        self.logger.error(f"Error creando botón de restock en pin {gpio_pin}: {e}")
                        self.restock_button = None
                else:
                    self.logger.warning("Restock habilitado pero sin gpio_pin configurado")
            else:
                self.logger.info("Modo restock deshabilitado")
        except Exception as e:
            self.logger.error(f"Error inicializando botón de restock: {e}")
            self.restock_button = None
    
    def is_restock_button_pressed(self) -> bool:
        """Verificar si el botón de restock está presionado"""
        try:
            if self.restock_button is not None:
                # El botón devuelve True cuando está presionado (conectado a GND con pull-up)
                is_pressed = self.restock_button.is_pressed
                if is_pressed:
                    self.logger.debug("Botón de restock presionado")
                return is_pressed
            else:
                self.logger.debug("Botón de restock no inicializado")
                return False
        except Exception as e:
            self.logger.error(f"Error leyendo estado del botón de restock: {e}")
            return False
    
    def get_restock_button_state(self) -> dict:
        """Obtener información completa del estado del botón de restock"""
        try:
            if self.restock_button is not None:
                return {
                    'initialized': True,
                    'is_pressed': self.restock_button.is_pressed,
                    'pin': self.config.get('machine', {}).get('restock_mode', {}).get('gpio_pin'),
                    'enabled': self.config.get('machine', {}).get('restock_mode', {}).get('enabled', False)
                }
            else:
                return {
                    'initialized': False,
                    'is_pressed': False,
                    'pin': self.config.get('machine', {}).get('restock_mode', {}).get('gpio_pin'),
                    'enabled': self.config.get('machine', {}).get('restock_mode', {}).get('enabled', False),
                    'error': 'Botón no inicializado'
                }
        except Exception as e:
            self.logger.error(f"Error obteniendo estado del botón de restock: {e}")
            return {
                'initialized': False,
                'is_pressed': False,
                'error': str(e)
            }
    
    def get_pins_status(self) -> Dict[str, int]:
        """Obtener el estado actual de los pines GPIO"""
        if not self.initialized:
            self.logger.warning("GPIO no inicializado, retornando estado vacío")
            return {}
        
        status = {}
        for door_id, device in self.door_relays.items():
            try:
                status[door_id] = device.value
            except Exception as e:
                self.logger.error(f"Error obteniendo estado de {door_id}: {e}")
                status[door_id] = None
        return status
    
    
    
    def _sensor_callback(self, door_id: str, channel: int):
        """Callback para eventos de sensores de puerta"""
        try:
            doors_config = self.config.get('doors', {})
            door_info = doors_config.get(door_id, {})
            sensor_pin = door_info.get('sensor_pin')
            
            if not sensor_pin:
                return
                
            # Leer estado del sensor (LOW = puerta cerrada, HIGH = puerta abierta)
            sensor_state = GPIO.input(sensor_pin) if GPIO_AVAILABLE else 0
            is_open = sensor_state == GPIO.HIGH if GPIO_AVAILABLE else False
            
            previous_state = self.door_states.get(door_id, {}).get('is_open', False)
            
            # Solo procesar si hay cambio de estado
            if is_open != previous_state:
                current_time = time.time()
                
                self.door_states[door_id]['is_open'] = is_open
                
                if is_open:
                    self.door_states[door_id]['last_opened'] = current_time
                    self.logger.info(f"Puerta {door_id} abierta")
                else:
                    self.door_states[door_id]['last_closed'] = current_time
                    self.logger.info(f"Puerta {door_id} cerrada")
                
                # Actualizar configuración
                self.config['doors'][door_id]['door_open'] = is_open
                self._save_config()
                
                # Ejecutar callback si existe
                if door_id in self.door_callbacks:
                    callback = self.door_callbacks[door_id]
                    threading.Thread(
                        target=callback, 
                        args=(door_id, is_open),
                        daemon=True
                    ).start()
                    
        except Exception as e:
            self.logger.error(f"Error en callback de sensor {door_id}: {e}")
    
    def get_door_open_time(self, door_id: str) -> float:
        """
        Obtener el tiempo de apertura configurado para una puerta específica
        
        Args:
            door_id: ID de la puerta
            
        Returns:
            float: Tiempo en segundos que la puerta debe permanecer abierta
        """
        doors_config = self.config.get('doors', {})
        door_info = doors_config.get(door_id, {})
        
        # Prioridad: tiempo específico de puerta > configuración global > valor por defecto
        door_time = door_info.get('open_time')
        if door_time is not None:
            return float(door_time)
        
        # Si no hay tiempo específico, usar configuración global
        machine_config = self.config.get('machine', {})
        door_settings = machine_config.get('door_settings', {})
        global_time = door_settings.get('default_open_time')
        if global_time is not None:
            return float(global_time)
        
        # Valor por defecto
        return self.default_relay_duration
    
    def set_door_open_time(self, door_id: str, open_time: float) -> bool:
        """
        Configurar el tiempo de apertura para una puerta específica
        
        Args:
            door_id: ID de la puerta
            open_time: Tiempo en segundos (debe estar entre min_open_time y max_open_time)
            
        Returns:
            bool: True si se configuró correctamente
        """
        try:
            # Validar límites
            machine_config = self.config.get('machine', {})
            door_settings = machine_config.get('door_settings', {})
            min_time = door_settings.get('min_open_time', 1.0)
            max_time = door_settings.get('max_open_time', 10.0)
            
            if not (min_time <= open_time <= max_time):
                self.logger.error(f"Tiempo de apertura {open_time}s fuera del rango permitido ({min_time}-{max_time}s)")
                return False
            
            # Actualizar configuración
            doors_config = self.config.get('doors', {})
            if door_id not in doors_config:
                self.logger.error(f"Puerta {door_id} no encontrada")
                return False
            
            doors_config[door_id]['open_time'] = float(open_time)
            self._save_config()
            
            self.logger.info(f"Tiempo de apertura para puerta {door_id} configurado a {open_time}s")
            return True
            
        except Exception as e:
            self.logger.error(f"Error configurando tiempo de apertura para {door_id}: {e}")
            return False

    def _create_simulated_relay(self, door_id: str, gpio_pin: int):
        """Crear un relé simulado para testing en Windows/desarrollo"""
        class SimulatedRelay:
            def __init__(self, door_id, gpio_pin):
                self.door_id = door_id
                self.gpio_pin = gpio_pin
                self.is_on = False
                
            def on(self):
                self.is_on = True
                print(f"SIMULACIÓN RELÉ: Puerta {self.door_id} (pin {self.gpio_pin}) -> ACTIVADO")
                
            def off(self):
                self.is_on = False
                print(f"SIMULACIÓN RELÉ: Puerta {self.door_id} (pin {self.gpio_pin}) -> DESACTIVADO")
                
            @property
            def value(self):
                return 1 if self.is_on else 0
        
        return SimulatedRelay(door_id, gpio_pin)


    def open_door(self, door_id: str) -> bool:
        """
        Activar relé para abrir una puerta específica y cerrarlo automáticamente tras el tiempo configurado
        """
        try:
            doors_config    = self.config.get('doors', {})
            door_info       = doors_config.get(door_id)
            if not door_info:
                print(f"Puerta {door_id} no encontrada en configuración")
                self.logger.error(f"Puerta {door_id} no encontrada en configuración")
                return False
            gpio_pin = door_info.get('gpio_pin')
            if not gpio_pin:
                print(f"Puerta {door_id} no tiene gpio_pin configurado")
                self.logger.error(f"Puerta {door_id} no tiene gpio_pin configurado")
                return False
            if door_id not in self.door_relays:
                print(f"Relé no configurado para puerta {door_id}")
                self.logger.error(f"Relé no configurado para puerta {door_id}")
                return False
            rele = self.door_relays[door_id]
            if not rele:
                print(f"Relé no encontrado para puerta {door_id}")
                self.logger.error(f"Relé no encontrado para puerta {door_id}")
                return False

            # Activar relé
            rele.on()
            print(f"Relé activado para puerta {door_id} (pin {gpio_pin})")
            self.logger.info(f"Relé activado para puerta {door_id} (pin {gpio_pin})")


            return True
        except Exception as e:
            print(f"Error abriendo puerta {door_id}: {e}")
            self.logger.error(f"Error abriendo puerta {door_id}: {e}")
            return False

    def close_door(self, door_id: str) -> bool:
        """
        Cerrar una puerta específica, desactivando el relé y actualizando el estado
        """
        if door_id not in self.door_relays:
            self.logger.error(f"Puerta {door_id} no encontrada")
            return False
        
        try:
            rele = self.door_relays[door_id]
            rele.off()  # Desactivar relé
            self.logger.info(f"Relé desactivado para puerta {door_id}")
            
            # Actualizar estado
            self.door_states[door_id]['is_open'] = False
            self.door_states[door_id]['relay_active'] = False
            self.door_states[door_id]['last_closed'] = time.time()
            
            # Actualizar configuración
            self.config['doors'][door_id]['door_open'] = False
            self._save_config()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error cerrando puerta {door_id}: {e}")
            return False
    
    def _activate_relay_matrix(self, gpio_pin: int, relay_index: int, door_id: str) -> bool:
        """
        Activar un relé específico en una matriz de relés
        Implementa protocolo de selección por índice
        """
        try:
            if GPIO_AVAILABLE:
                # Protocolo para matriz de relés:
                # 1. Enviar pulso de selección (índice en binario)
                # 2. Activar pin principal
                # 3. Enviar pulso de confirmación
                
                # Convertir índice a binario (ejemplo: índice 3 = 011)
                binary_index = format(relay_index, '08b')  # 8 bits
                
                # Enviar bits de selección
                for bit in binary_index:
                    GPIO.output(gpio_pin, GPIO.HIGH if bit == '1' else GPIO.LOW)
                    time.sleep(0.001)  # 1ms por bit
                
                # Pulso final de activación
                GPIO.output(gpio_pin, GPIO.HIGH)
                time.sleep(0.005)  # 5ms de pulso de activación
                GPIO.output(gpio_pin, GPIO.LOW)
                time.sleep(0.001)  # Pausa
                GPIO.output(gpio_pin, GPIO.HIGH)  # Mantener activo
                
            else:
                print(f"SIMULACIÓN: Activando relé matriz puerta {door_id} en pin {gpio_pin}, índice {relay_index}")
                print(f"SIMULACIÓN: Protocolo matriz - Enviando selección binaria: {format(relay_index, '08b')}")
                print(f"SIMULACIÓN: Protocolo matriz - Relé {relay_index} ACTIVADO")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error activando relé matriz {door_id}: {str(e)}")
            return False

    def _deactivate_relay(self, door_id: str, gpio_pin: int, relay_index: int = 0, is_matrix: bool = False):
        """Desactivar relé después del tiempo especificado"""
        try:
            if is_matrix:
                self.logger.info(f"Desactivando relé matriz para puerta {door_id} (pin {gpio_pin}, índice {relay_index})")
                self._deactivate_relay_matrix(gpio_pin, relay_index, door_id)
            else:
                self.logger.info(f"Desactivando relé simple para puerta {door_id} (pin {gpio_pin})")
                self._deactivate_relay_simple(gpio_pin, door_id)
            
            # Marcar relé como inactivo
            if door_id in self.door_states:
                self.door_states[door_id]['relay_active'] = False
                self.door_states[door_id]['last_closed'] = time.time()
                
            # Limpiar timer
            if door_id in self.door_timers:
                del self.door_timers[door_id]
                
            self.logger.info(f"Relé de puerta {door_id} desactivado exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error desactivando relé {door_id}: {str(e)}")
            # Asegurar que el estado se marque como inactivo incluso si hay error
            if door_id in self.door_states:
                self.door_states[door_id]['relay_active'] = False

    def _deactivate_relay_simple(self, gpio_pin: int, door_id: str):
        """Desactivar un relé simple"""
        try:
            if GPIO_AVAILABLE:
                GPIO.output(gpio_pin, GPIO.LOW)
            else:
                print(f"SIMULACIÓN: Desactivando relé simple puerta {door_id} en pin {gpio_pin}")
        except Exception as e:
            self.logger.error(f"Error desactivando relé simple {door_id}: {str(e)}")

    def _deactivate_relay_matrix(self, gpio_pin: int, relay_index: int, door_id: str):
        """Desactivar un relé específico en matriz"""
        try:
            if GPIO_AVAILABLE:
                # Protocolo de desactivación para matriz
                # Enviar comando de desactivación específico
                binary_index = format(relay_index, '08b')
                
                # Enviar bits de selección
                for bit in binary_index:
                    GPIO.output(gpio_pin, GPIO.HIGH if bit == '1' else GPIO.LOW)
                    time.sleep(0.001)
                
                # Pulso de desactivación
                GPIO.output(gpio_pin, GPIO.LOW)
                time.sleep(0.005)
                GPIO.output(gpio_pin, GPIO.HIGH)
                time.sleep(0.001)
                GPIO.output(gpio_pin, GPIO.LOW)  # Estado final desactivado
                
            else:
                print(f"SIMULACIÓN: Desactivando relé matriz puerta {door_id} en pin {gpio_pin}, índice {relay_index}")
                print(f"SIMULACIÓN: Protocolo matriz - Relé {relay_index} DESACTIVADO")
                
        except Exception as e:
            self.logger.error(f"Error desactivando relé matriz {door_id}: {str(e)}")
    
    def get_all_doors_state(self) -> Dict[str, Dict]:
        """Obtener estado de todas las puertas"""
        states = {}
        doors_config = self.config.get('doors', {})
        
        for door_id in doors_config.keys():
            states[door_id] = self.get_door_state(door_id)
            
        return states
    
    def register_door_callback(self, door_id: str, callback: Callable[[str, bool], None]):
        """
        Registrar callback para eventos de puerta
        
        Args:
            door_id: ID de la puerta
            callback: Función a llamar cuando cambie el estado (door_id, is_open)
        """
        self.door_callbacks[door_id] = callback
        self.logger.info(f"Callback registrado para puerta {door_id}")
    
    def unregister_door_callback(self, door_id: str):
        """Desregistrar callback para una puerta"""
        if door_id in self.door_callbacks:
            del self.door_callbacks[door_id]
            self.logger.info(f"Callback desregistrado para puerta {door_id}")
    
    def test_door(self, door_id: str) -> bool:
        """
        Probar funcionamiento de una puerta (relé y sensor)
        
        Args:
            door_id: ID de la puerta a probar
            
        Returns:
            bool: True si la prueba fue exitosa
        """
        try:
            self.logger.info(f"Iniciando prueba de puerta {door_id}")
            
            # Verificar configuración
            door_info = self.config.get('doors', {}).get(door_id)
            if not door_info:
                self.logger.error(f"Puerta {door_id} no encontrada")
                return False
            
            # Probar apertura
            if not self.open_door(door_id):
                self.logger.error(f"Error en prueba de apertura de puerta {door_id}")
                return False
            
            # Verificar estado del sensor
            sensor_pin = door_info.get('sensor_pin')
            if sensor_pin and GPIO_AVAILABLE:
                sensor_state = GPIO.input(sensor_pin)
                self.logger.info(f"Estado del sensor de puerta {door_id}: {sensor_state}")
            
            self.logger.info(f"Prueba de puerta {door_id} completada exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error en prueba de puerta {door_id}: {e}")
            return False
    
    def test_relay_matrix(self, gpio_pin: int) -> Dict[str, bool]:
        """
        Probar todas las puertas que comparten una matriz de relés
        
        Args:
            gpio_pin: Pin GPIO de la matriz a probar
            
        Returns:
            Dict con resultados de cada puerta
        """
        results = {}
        matrix_info = self.get_relay_matrix_info(gpio_pin)
        
        self.logger.info(f"Probando matriz de relés en pin {gpio_pin}")
        self.logger.info(f"Puertas en matriz: {[d['door_id'] for d in matrix_info['doors']]}")
        
        for door_info in matrix_info['doors']:
            door_id = door_info['door_id']
            try:
                self.logger.info(f"Probando puerta {door_id} (índice {door_info['relay_index']}, matriz: {door_info['is_matrix']})")
                results[door_id] = self.test_door(door_id)
                time.sleep(1)  # Pausa entre pruebas
            except Exception as e:
                self.logger.error(f"Error probando puerta {door_id}: {str(e)}")
                results[door_id] = False
        
        return results

    def validate_matrix_configuration(self) -> Dict[str, list]:
        """
        Validar la configuración de matrices de relés
        
        Returns:
            Dict con información de validación
        """
    
    
    def cleanup(self):
        """Limpiar todos los recursos: timers, OutputDevice, GPIO, y diccionarios internos"""
        try:
            # Cancelar todos los timers
            for timer in self.door_timers.values():
                try:
                    timer.cancel()
                except Exception as e:
                    self.logger.warning(f"Error cancelando timer: {e}")
            self.door_timers.clear()

            # Cerrar todos los OutputDevice
            for rel in self.door_relays.values():
                try:
                    print(f"Cerrando OutputDevice para puerta {rel.pin}")
                    rel.close()
                except Exception as e:
                    self.logger.warning(f"Error cerrando OutputDevice: {e}")
            self.door_relays.clear()

            # Cerrar botón de restock si existe
            if self.restock_button is not None:
                try:
                    self.logger.info("Cerrando botón de restock")
                    self.restock_button.close()
                    self.restock_button = None
                except Exception as e:
                    self.logger.warning(f"Error cerrando botón de restock: {e}")

            # Limpiar estados y callbacks
            self.door_states.clear()
            self.door_callbacks.clear()

            # Limpiar recursos de gpiozero (OutputDevice)
            try:
                for rel in self.door_relays.values():
                    if hasattr(rel, 'close'):
                        rel.close()
            except Exception as e:
                self.logger.warning(f"Error cerrando OutputDevice (gpiozero): {e}")

            self.logger.info("Limpieza de todos los recursos de hardware completada")
        except Exception as e:
            self.logger.error(f"Error en limpieza: {e}")
            self.logger.error(f"Error en limpieza: {e}")
    
    def __del__(self):
        """Destructor - limpiar recursos"""
        self.cleanup()

# Instancia global del controlador
hardware_controller = HardwareController()