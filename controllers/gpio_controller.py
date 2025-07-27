"""
Controlador GPIO para Máquina Expendedora
Compatible con Windows (simulación) y Raspberry Pi (GPIO real)
Maneja dispensadores y sensores de puertas dinámicamente desde configuración JSON
"""
import logging
import time
from typing import Dict, Any
from config import Config

logger = logging.getLogger(__name__)


class GPIOController:
    """Controlador principal para manejo de GPIO"""
    
    def __init__(self):
        self.platform = Config.PLATFORM
        self.gpio_enabled = Config.GPIO_ENABLED
        self.pins_status = {}
        self.dispensers = {}
        self.hardware_initialized = False
        # Preferir gpiozero en Raspberry Pi
        self._init_gpiozero()
    
    def _load_door_config(self) -> Dict[str, int]:
        """Cargar configuración de puertas desde JSON (solo dispensadores)"""
        try:
            from machine_config import config_manager
            doors = config_manager.get_doors()
            door_pins = {}
            for door_id, door_config in doors.items():
                if 'gpio_pin' in door_config:
                    door_pins[door_id] = door_config['gpio_pin']
            logger.info(f"Configuración cargada: {len(door_pins)} dispensadores")
            return door_pins
        except Exception as e:
            logger.error(f"Error al cargar configuración de puertas: {e}")
            return {}
    
    def _init_gpiozero(self):
        """Inicializar GPIO usando gpiozero para Raspberry Pi (solo dispensadores)"""
        try:
            from gpiozero import OutputDevice
            # Cargar configuración de puertas
            door_pins = self._load_door_config()
            error_detected = False
            # Configurar dispensadores
            for door_id, pin in door_pins.items():
                try:
                    from machine_config import config_manager
                    door_config = config_manager.get_door(door_id)
                    active_high = door_config.get('active_high', False)
                    self.dispensers[door_id] = OutputDevice(pin, active_high=active_high, initial_value=False)
                    self.dispensers[door_id].off()  # Apagar relé al iniciar
                    logger.info(f"Dispensador OutputDevice configurado: {door_id} -> Pin {pin} (active_high={active_high})")
                except Exception as e:
                    logger.error(f"Error al configurar dispensador {door_id} en pin {pin}: {e} [{type(e).__name__}]")
                    error_detected = True
            if error_detected:
                logger.error("Hardware no inicializado correctamente: revisa los errores anteriores en el log.")
            else:
                self.hardware_initialized = True
                logger.info("GPIO (gpiozero) inicializado correctamente.")
        except ImportError:
            self.hardware_initialized = False
            logger.error("Librería gpiozero no encontrada. Cambiando a modo simulación.")
            self._init_windows_simulation()
    
    def _init_windows_simulation(self):
        """Inicializar simulación para Windows (solo dispensadores)"""
        door_pins = self._load_door_config()
        for door_id, pin in door_pins.items():
            self.dispensers[door_id] = MockGPIOPin(f'LED_{pin}')
            logger.info(f"Dispensador simulado configurado: {door_id} -> Pin {pin}")
        logger.info("Modo simulación GPIO inicializado (Windows)")
    
    def dispense_product(self, door_id: str) -> bool:
        """Dispensar producto de una puerta específica
        Args:
            door_id: Identificador de la puerta (ej: 'A1', 'B2')
        Returns:
            bool: True si el dispensado fue exitoso
        """
        try:
            dispenser = self.dispensers.get(door_id)
            if dispenser is None:
                logger.warning(f"Dispensador no configurado para puerta: {door_id}")
                return False

            if self.platform == 'raspberry' and self.gpio_enabled:
                # Asegurarse que el relé está apagado antes de activar
                dispenser.off()
                time.sleep(0.05)
                dispenser.on()
                time.sleep(0.5)  # Tiempo para dispensar
                dispenser.off()
            else:
                # Simulación en Windows
                dispenser.activate()

            logger.info(f"Producto dispensado de la puerta: {door_id}")
            return True

        except Exception as e:
            logger.error(f"Error al dispensar producto de la puerta {door_id}: {e}")
            return False
    
    # Método de sensor eliminado: los sensores no deben funcionar
    
    def get_pins_status(self) -> Dict[str, Any]:
        """Obtener estado actual de todos los pines (solo dispensadores)"""
        status = {
            'platform': self.platform,
            'gpio_enabled': self.gpio_enabled,
            'dispensers': {}
        }
        for door_id, dispenser in self.dispensers.items():
            if hasattr(dispenser, 'get_status'):
                status['dispensers'][door_id] = dispenser.get_status()
            else:
                status['dispensers'][door_id] = {'door_id': door_id, 'available': True}
        return status
    
    def cleanup(self):
        """Limpiar recursos GPIO al finalizar"""
        if self.platform == 'raspberry' and self.gpio_enabled:
            try:
                # Cerrar todos los dispositivos gpiozero
                for dispenser in self.dispensers.values():
                    if hasattr(dispenser, 'close'):
                        dispenser.close()

                for sensor in self.sensors.values():
                    if hasattr(sensor, 'close'):
                        sensor.close()

                logger.info("GPIO cleanup completado (gpiozero)")
            except Exception as e:
                logger.error(f"Error durante GPIO cleanup: {e}")
        else:
            logger.info("GPIO cleanup completado (modo simulación)")


class MockGPIOPin:
    """Simulador de pin GPIO para desarrollo en Windows"""
    
    def __init__(self, pin_name: str):
        self.pin_name = pin_name
        self.state = False
        self.active = False
    
    def activate(self):
        """Simular activación del pin (dispensado)"""
        self.active = True
        logger.info(f"[SIMULACIÓN] Pin {self.pin_name} activado")
        # Simular breve activación
        time.sleep(0.1)
        self.active = False
    
    def read(self) -> bool:
        """Simular lectura del pin (sensor)"""
        # Simular diferentes estados para testing
        import random
        value = random.choice([True, False])
        logger.debug(f"[SIMULACIÓN] Pin {self.pin_name} leído: {value}")
        return value
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado del pin simulado"""
        return {
            'pin_name': self.pin_name,
            'state': self.state,
            'active': self.active,
            'simulated': True
        }


# Instancia global del controlador GPIO
gpio_controller = GPIOController()
