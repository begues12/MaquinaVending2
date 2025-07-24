"""
Controlador para el modo reposición de la máquina expendedora
"""
import logging
import platform
import time
from datetime import datetime
from typing import Dict, Optional, List, Any
from machine_config import config_manager
from database import db_manager

logger = logging.getLogger(__name__)

class RestockController:
    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        self.restock_mode = False
        self.restock_pin = config_manager.config.get('machine', {}).get('restock_mode', {}).get('gpio_pin', 16)
        
        # Secuencia secreta (legacy - mantener por compatibilidad)
        self.secret_sequence_enabled = config_manager.is_secret_sequence_enabled()
        self.secret_sequence = config_manager.get_secret_sequence()
        self.sequence_timeout = config_manager.get_sequence_timeout()
        self.max_attempts = config_manager.get_max_sequence_attempts()
        
        # Nuevo sistema de activación por clics
        self.click_activation_enabled = True
        self.click_sequence = {
            'first_phase': 5,       # 5 clics iniciales
            'pause_min': 2.0,       # Mínimo 2 segundos de pausa (más fácil)
            'pause_max': 10.0,      # Máximo 10 segundos de pausa (muy flexible)
            'second_phase': 5,      # 5 clics finales
            'click_timeout': 3.0,   # Tiempo máximo entre clics (3 segundos, muy fácil)
            'total_timeout': 30.0   # Tiempo total máximo para toda la secuencia
        }
        
        # Estado del sistema de clics
        self.click_state = {
            'phase': 'idle',        # idle, first_clicks, waiting_pause, second_clicks, completed
            'clicks_count': 0,
            'last_click_time': None,
            'sequence_start_time': None,
            'pause_start_time': None,
            'failed_attempts': 0,
            'max_failed_attempts': 10  # Más intentos permitidos
        }
        
        # Estado de la secuencia secreta (legacy)
        self.current_sequence = []
        self.sequence_start_time = None
        self.failed_attempts = 0
        
        if not self.is_windows:
            try:
                import RPi.GPIO as GPIO
                self.GPIO = GPIO
                self._setup_gpio()
            except ImportError:
                logger.warning("RPi.GPIO no disponible. Funcionando en modo simulación.")
                self.GPIO = None
        else:
            logger.info("Modo reposición inicializado (Windows - simulación)")
            self.GPIO = None
        
        if self.secret_sequence_enabled:
            logger.info(f"Secuencia secreta habilitada: {len(self.secret_sequence)} pasos")
        
        logger.info(f"Sistema de activación por clics habilitado: {self.click_sequence['first_phase']}+pausa+{self.click_sequence['second_phase']} clics")
    
    def _setup_gpio(self):
        """Configurar GPIO para el botón de reposición"""
        if self.GPIO:
            try:
                self.GPIO.setmode(self.GPIO.BCM)
                self.GPIO.setup(self.restock_pin, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)
                
                # Configurar interrupción para detectar presión del botón
                self.GPIO.add_event_detect(
                    self.restock_pin, 
                    self.GPIO.FALLING, 
                    callback=self._button_pressed_callback,
                    bouncetime=300
                )
                
                logger.info(f"GPIO configurado para modo reposición en pin {self.restock_pin}")
                
            except Exception as e:
                logger.error(f"Error al configurar GPIO para reposición: {e}")
    
    def _button_pressed_callback(self, channel):
        """Callback cuando se presiona el botón de reposición"""
        logger.info("Botón de reposición presionado")
        self.toggle_restock_mode()
    
    def toggle_restock_mode(self) -> bool:
        """Alternar modo reposición"""
        self.restock_mode = not self.restock_mode
        
        if self.restock_mode:
            # Activar modo reposición
            config_manager.config['machine']['restock_mode']['enabled'] = True
            config_manager.config['machine']['restock_mode']['activated_at'] = datetime.now().isoformat()
            
            # Registrar en logs
            db_manager.log_system_event(
                'INFO', 
                'Modo reposición activado', 
                'restock_controller'
            )
            
            logger.info("Modo reposición ACTIVADO")
            
        else:
            # Desactivar modo reposición
            config_manager.config['machine']['restock_mode']['enabled'] = False
            config_manager.config['machine']['restock_mode']['activated_at'] = None
            
            # Registrar en logs
            db_manager.log_system_event(
                'INFO', 
                'Modo reposición desactivado', 
                'restock_controller'
            )
            
            logger.info("Modo reposición DESACTIVADO")
        
        # Guardar configuración
        config_manager.save_config()
        
        return self.restock_mode
    
    def is_restock_mode_active(self) -> bool:
        """Verificar si el modo reposición está activo"""
        return self.restock_mode or config_manager.config.get('machine', {}).get('restock_mode', {}).get('enabled', False)
    
    def activate_restock_mode(self) -> bool:
        """Activar modo reposición manualmente"""
        if not self.restock_mode:
            return self.toggle_restock_mode()
        return True
    
    def deactivate_restock_mode(self) -> bool:
        """Desactivar modo reposición manualmente"""
        if self.restock_mode:
            return not self.toggle_restock_mode()
        return True
    
    def simulate_button_press(self) -> bool:
        """Simular presión del botón (para Windows/testing)"""
        logger.info("Simulando presión del botón de reposición")
        self.toggle_restock_mode()
        return self.restock_mode
    
    def get_restock_status(self) -> Dict:
        """Obtener estado del modo reposición"""
        return {
            'active': self.is_restock_mode_active(),
            'activated_at': config_manager.config.get('machine', {}).get('restock_mode', {}).get('activated_at'),
            'gpio_pin': self.restock_pin,
            'platform': 'Windows' if self.is_windows else 'Raspberry Pi'
        }
    
    def update_product_in_door(self, door_id: str, product_data: Dict) -> bool:
        """Actualizar producto en una puerta (solo en modo reposición)"""
        if not self.is_restock_mode_active():
            logger.warning(f"Intento de actualizar producto {door_id} sin modo reposición activo")
            return False
        
        try:
            # Actualizar producto en base de datos
            success = db_manager.update_product(door_id, **product_data)
            
            if success:
                # Registrar cambio
                db_manager.log_door_maintenance(
                    door_id, 
                    'product_update', 
                    'success',
                    f"Producto actualizado: {product_data.get('name', 'N/A')}",
                    'restock_operator'
                )
                
                logger.info(f"Producto en puerta {door_id} actualizado: {product_data}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error al actualizar producto en puerta {door_id}: {e}")
            return False
    
    def restock_door(self, door_id: str, quantity: int, operator: str = None, notes: str = None) -> bool:
        """Reabastecer una puerta (solo en modo reposición)"""
        if not self.is_restock_mode_active():
            logger.warning(f"Intento de reposición en puerta {door_id} sin modo reposición activo")
            return False
        
        try:
            # Registrar reposición en base de datos
            success = db_manager.create_restock(
                door_id, 
                quantity, 
                operator or 'restock_operator', 
                notes
            )
            
            if success:
                logger.info(f"Reposición exitosa en puerta {door_id}: +{quantity} unidades")
                
                # Registrar mantenimiento
                db_manager.log_door_maintenance(
                    door_id, 
                    'restock', 
                    'success',
                    f"Añadidas {quantity} unidades. {notes or ''}",
                    operator or 'restock_operator'
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Error al reabastecer puerta {door_id}: {e}")
            return False
    
    def process_screen_click(self) -> Dict[str, Any]:
        """
        Procesar clic en pantalla para activación de modo restock
        Secuencia: 5 clics + pausa 5-6s + 5 clics
        """
        if not self.click_activation_enabled:
            return {'activation_system': 'disabled'}
        
        current_time = time.time()
        
        # Verificar timeout total
        if (self.click_state['sequence_start_time'] and 
            current_time - self.click_state['sequence_start_time'] > self.click_sequence['total_timeout']):
            logger.debug("Timeout total de secuencia de clics - reiniciando")
            self._reset_click_sequence()
        
        # Procesar según la fase actual
        if self.click_state['phase'] == 'idle':
            return self._start_click_sequence(current_time)
        
        elif self.click_state['phase'] == 'first_clicks':
            return self._process_first_clicks(current_time)
        
        elif self.click_state['phase'] == 'waiting_pause':
            return self._process_during_pause(current_time)
        
        elif self.click_state['phase'] == 'second_clicks':
            return self._process_second_clicks(current_time)
        
        else:
            self._reset_click_sequence()
            return {'phase': 'error', 'message': 'Estado inválido - secuencia reiniciada'}
    
    def _start_click_sequence(self, current_time: float) -> Dict[str, Any]:
        """Iniciar nueva secuencia de clics"""
        self.click_state.update({
            'phase': 'first_clicks',
            'clicks_count': 1,
            'last_click_time': current_time,
            'sequence_start_time': current_time,
            'pause_start_time': None
        })
        
        logger.debug("Iniciando secuencia de activación por clics - Primera fase")
        return {
            'phase': 'first_clicks',
            'clicks_count': 1,
            'clicks_needed': self.click_sequence['first_phase'],
            'message': f'Clic 1/{self.click_sequence["first_phase"]} - Continúa haciendo clic'
        }
    
    def _process_first_clicks(self, current_time: float) -> Dict[str, Any]:
        """Procesar clics de la primera fase"""
        # Verificar timeout entre clics
        if current_time - self.click_state['last_click_time'] > self.click_sequence['click_timeout']:
            logger.debug("Timeout entre clics - reiniciando secuencia")
            self._reset_click_sequence()
            return self._start_click_sequence(current_time)
        
        self.click_state['clicks_count'] += 1
        self.click_state['last_click_time'] = current_time
        
        if self.click_state['clicks_count'] >= self.click_sequence['first_phase']:
            # Primera fase completada - iniciar pausa
            self.click_state.update({
                'phase': 'waiting_pause',
                'pause_start_time': current_time
            })
            
            logger.debug("Primera fase completada - Esperando pausa de 5-6 segundos")
            return {
                'phase': 'waiting_pause',
                'message': 'Primera fase completada. Espera 5-6 segundos antes de continuar.',
                'pause_min': self.click_sequence['pause_min'],
                'pause_max': self.click_sequence['pause_max']
            }
        else:
            return {
                'phase': 'first_clicks',
                'clicks_count': self.click_state['clicks_count'],
                'clicks_needed': self.click_sequence['first_phase'],
                'message': f'Clic {self.click_state["clicks_count"]}/{self.click_sequence["first_phase"]} - Continúa'
            }
    
    def _process_during_pause(self, current_time: float) -> Dict[str, Any]:
        """Procesar clic durante la pausa (debe esperar)"""
        pause_duration = current_time - self.click_state['pause_start_time']
        
        if pause_duration < self.click_sequence['pause_min']:
            # Clic muy temprano - reiniciar
            logger.debug(f"Clic muy temprano durante pausa ({pause_duration:.1f}s) - reiniciando")
            self._reset_click_sequence()
            return {
                'phase': 'failed',
                'message': f'Debes esperar al menos {self.click_sequence["pause_min"]} segundos. Reiniciando...',
                'failed_attempts': self._increment_failed_attempts()
            }
        
        elif pause_duration > self.click_sequence['pause_max']:
            # Pausa muy larga - reiniciar
            logger.debug(f"Pausa muy larga ({pause_duration:.1f}s) - reiniciando")
            self._reset_click_sequence()
            return {
                'phase': 'failed',
                'message': f'Pausa demasiado larga ({pause_duration:.1f}s). Máximo {self.click_sequence["pause_max"]}s. Reiniciando...',
                'failed_attempts': self._increment_failed_attempts()
            }
        
        else:
            # Pausa correcta - iniciar segunda fase
            self.click_state.update({
                'phase': 'second_clicks',
                'clicks_count': 1,
                'last_click_time': current_time
            })
            
            logger.debug(f"Pausa correcta ({pause_duration:.1f}s) - Iniciando segunda fase")
            return {
                'phase': 'second_clicks',
                'clicks_count': 1,
                'clicks_needed': self.click_sequence['second_phase'],
                'message': f'¡Perfecto! Pausa de {pause_duration:.1f}s. Clic 1/{self.click_sequence["second_phase"]} de la segunda fase'
            }
    
    def _process_second_clicks(self, current_time: float) -> Dict[str, Any]:
        """Procesar clics de la segunda fase"""
        # Verificar timeout entre clics
        if current_time - self.click_state['last_click_time'] > self.click_sequence['click_timeout']:
            logger.debug("Timeout entre clics en segunda fase - reiniciando")
            self._reset_click_sequence()
            return {
                'phase': 'failed',
                'message': 'Tiempo agotado entre clics. Reiniciando secuencia...',
                'failed_attempts': self._increment_failed_attempts()
            }
        
        self.click_state['clicks_count'] += 1
        self.click_state['last_click_time'] = current_time
        
        if self.click_state['clicks_count'] >= self.click_sequence['second_phase']:
            # Secuencia completada - activar modo restock
            logger.info("¡Secuencia de activación por clics completada! Activando modo restock")
            self._reset_click_sequence()
            self.activate_restock_mode()
            
            return {
                'phase': 'completed',
                'restock_activated': True,
                'message': '¡Secuencia completada! Modo restock activado.',
                'success': True
            }
        else:
            return {
                'phase': 'second_clicks',
                'clicks_count': self.click_state['clicks_count'],
                'clicks_needed': self.click_sequence['second_phase'],
                'message': f'Clic {self.click_state["clicks_count"]}/{self.click_sequence["second_phase"]} - ¡Casi listo!'
            }
    
    def _increment_failed_attempts(self) -> int:
        """Incrementar contador de intentos fallidos"""
        self.click_state['failed_attempts'] += 1
        
        if self.click_state['failed_attempts'] >= self.click_state['max_failed_attempts']:
            # Solo bloquear después de muchos fallos consecutivos
            logger.warning(f"Muchos intentos fallidos ({self.click_state['max_failed_attempts']}) - pausa temporal de 5 segundos")
            self._reset_click_sequence()
            # Esperar solo 5 segundos antes de permitir nuevos intentos
            self.click_state['blocked_until'] = time.time() + 5
            self.click_state['failed_attempts'] = 0  # Resetear contador
            
        return self.click_state['failed_attempts']
    
    def _reset_click_sequence(self):
        """Resetear estado de secuencia de clics"""
        self.click_state.update({
            'phase': 'idle',
            'clicks_count': 0,
            'last_click_time': None,
            'sequence_start_time': None,
            'pause_start_time': None
        })
    
    def get_click_activation_status(self) -> Dict[str, Any]:
        """Obtener estado del sistema de activación por clics"""
        current_time = time.time()
        
        # Verificar si está bloqueado
        blocked_until = self.click_state.get('blocked_until', 0)
        is_blocked = current_time < blocked_until
        
        status = {
            'enabled': self.click_activation_enabled,
            'phase': self.click_state['phase'],
            'clicks_count': self.click_state['clicks_count'],
            'failed_attempts': self.click_state['failed_attempts'],
            'max_failed_attempts': self.click_state['max_failed_attempts'],
            'is_blocked': is_blocked,
            'sequence_config': self.click_sequence
        }
        
        if is_blocked:
            status['blocked_time_remaining'] = blocked_until - current_time
        
        if self.click_state['phase'] == 'waiting_pause' and self.click_state['pause_start_time']:
            pause_duration = current_time - self.click_state['pause_start_time']
            status['pause_duration'] = pause_duration
            status['pause_valid'] = (self.click_sequence['pause_min'] <= pause_duration <= self.click_sequence['pause_max'])
        
        return status
        """Procesar selección de puerta para secuencia secreta"""
        if not self.secret_sequence_enabled or self.restock_mode:
            return {'sequence_active': False}
        
        current_time = time.time()
        
        # Iniciar nueva secuencia si es necesario
        if not self.current_sequence or not self.sequence_start_time:
            self.current_sequence = []
            self.sequence_start_time = current_time
            logger.debug("Iniciando nueva secuencia secreta")
        
        # Verificar timeout
        if current_time - self.sequence_start_time > self.sequence_timeout:
            logger.debug("Timeout de secuencia secreta - reiniciando")
            self.current_sequence = []
            self.sequence_start_time = current_time
        
        # Añadir puerta a la secuencia
        self.current_sequence.append(door_id)
        logger.debug(f"Secuencia actual: {self.current_sequence}")
        
        # Verificar si coincide hasta ahora
        expected_sequence = self.secret_sequence[:len(self.current_sequence)]
        
        if self.current_sequence == expected_sequence:
            # Secuencia correcta hasta ahora
            if len(self.current_sequence) == len(self.secret_sequence):
                # Secuencia completa correcta
                logger.info("¡Secuencia secreta completada! Activando modo reposición")
                self._reset_sequence()
                self.activate_restock_mode()
                return {
                    'sequence_active': False,
                    'sequence_completed': True,
                    'restock_activated': True,
                    'message': 'Modo reposición activado por secuencia secreta'
                }
            else:
                # Secuencia en progreso
                return {
                    'sequence_active': True,
                    'sequence_progress': len(self.current_sequence),
                    'sequence_total': len(self.secret_sequence),
                    'message': f'Secuencia en progreso: {len(self.current_sequence)}/{len(self.secret_sequence)}'
                }
        else:
            # Secuencia incorrecta
            self.failed_attempts += 1
            logger.warning(f"Secuencia incorrecta. Intento {self.failed_attempts}/{self.max_attempts}")
            
            if self.failed_attempts >= self.max_attempts:
                logger.warning("Máximo de intentos de secuencia alcanzado. Bloqueando temporalmente.")
                self._reset_sequence()
                return {
                    'sequence_active': False,
                    'sequence_failed': True,
                    'blocked': True,
                    'message': 'Demasiados intentos fallidos. Acceso bloqueado temporalmente.'
                }
            
            self._reset_sequence()
            return {
                'sequence_active': False,
                'sequence_failed': True,
                'attempts_left': self.max_attempts - self.failed_attempts,
                'message': f'Secuencia incorrecta. Intentos restantes: {self.max_attempts - self.failed_attempts}'
            }
    
    def _reset_sequence(self):
        """Resetear estado de secuencia secreta"""
        self.current_sequence = []
        self.sequence_start_time = None
    
    def get_sequence_status(self) -> Dict[str, Any]:
        """Obtener estado actual de la secuencia secreta"""
        if not self.secret_sequence_enabled:
            return {'enabled': False}
        
        return {
            'enabled': True,
            'sequence_length': len(self.secret_sequence),
            'current_progress': len(self.current_sequence) if self.current_sequence else 0,
            'failed_attempts': self.failed_attempts,
            'max_attempts': self.max_attempts,
            'timeout': self.sequence_timeout,
            'time_remaining': max(0, self.sequence_timeout - (time.time() - self.sequence_start_time)) if self.sequence_start_time else self.sequence_timeout
        }
    
    def cleanup(self):
        """Limpiar recursos GPIO al cerrar"""
        if self.GPIO and not self.is_windows:
            try:
                self.GPIO.cleanup()
                logger.info("GPIO limpiado correctamente")
            except Exception as e:
                logger.error(f"Error al limpiar GPIO: {e}")


# Instancia global del controlador de reposición
restock_controller = RestockController()
