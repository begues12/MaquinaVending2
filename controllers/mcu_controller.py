#!/usr/bin/env python3
"""
Controlador MCU para Máquina de Vending
Maneja comunicación con microcontrolador para:
- Procesamiento de pagos
- Control de puertas
- Sensores
- Estados del sistema
- Comunicación serie/UART
"""

import json
import time
import threading
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("⚠️  Módulo serial no disponible. Usar modo simulación.")


class MCUCommand(Enum):
    """Comandos disponibles para el MCU"""
    # Sistema
    PING = "PING"
    STATUS = "STATUS"
    RESET = "RESET"
    VERSION = "VERSION"
    
    # Pagos
    PAYMENT_START = "PAY_START"
    PAYMENT_STATUS = "PAY_STATUS"
    PAYMENT_CANCEL = "PAY_CANCEL"
    PAYMENT_CONFIRM = "PAY_CONFIRM"
    
    # Puertas
    DOOR_OPEN = "DOOR_OPEN"
    DOOR_CLOSE = "DOOR_CLOSE"
    DOOR_STATUS = "DOOR_STATUS"
    
    # Sensores
    SENSOR_READ = "SENSOR_READ"
    SENSOR_STATUS = "SENSOR_STATUS"
    
    # Restock
    RESTOCK_MODE = "RESTOCK_MODE"
    RESTOCK_STATUS = "RESTOCK_STATUS"
    
    # Estados
    SET_LED = "SET_LED"
    BUZZER = "BUZZER"
    DISPLAY_MSG = "DISPLAY_MSG"


class MCUStatus(Enum):
    """Estados del MCU"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    BUSY = "busy"
    READY = "ready"


class PaymentMethod(Enum):
    """Métodos de pago soportados por el MCU"""
    CASH = "cash"
    CARD = "card"
    CONTACTLESS = "contactless"
    MOBILE = "mobile"


@dataclass
class MCUResponse:
    """Respuesta del MCU"""
    success: bool
    command: str
    data: Dict[str, Any]
    timestamp: datetime
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class PaymentTransaction:
    """Transacción de pago"""
    transaction_id: str
    method: PaymentMethod
    amount: float
    currency: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    door_id: Optional[str] = None
    error_code: Optional[str] = None


class MCUController:
    """Controlador principal del MCU"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Estado del MCU
        self.status = MCUStatus.DISCONNECTED
        self.connected = False
        self.last_ping = None
        
        # Comunicación serie
        self.serial_port = None
        self.port_name = config.get('port', '/dev/ttyUSB0')
        self.baudrate = config.get('baudrate', 115200)
        self.timeout = config.get('timeout', 5)
        
        # Transacciones
        self.current_transaction: Optional[PaymentTransaction] = None
        self.transaction_history: List[PaymentTransaction] = []
        
        # Callbacks y eventos
        self.event_callbacks: Dict[str, List[Callable]] = {}
        
        # Threads
        self.monitoring_thread = None
        self.stop_monitoring = False
        
        # Buffer de comandos
        self.command_queue = []
        self.response_buffer = []
        
        self.logger.info("MCU Controller inicializado")
    
    # ===== CONEXIÓN Y COMUNICACIÓN =====
    
    def connect(self) -> bool:
        """Conectar al MCU"""
        try:
            if not SERIAL_AVAILABLE:
                self.logger.warning("Modo simulación - Serial no disponible")
                self.status = MCUStatus.CONNECTED
                self.connected = True
                return True
            
            self.status = MCUStatus.CONNECTING
            self.logger.info(f"Conectando a MCU en {self.port_name}...")
            
            self.serial_port = serial.Serial(
                port=self.port_name,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            
            time.sleep(2)  # Esperar estabilización
            
            # Verificar conexión con PING
            if self._send_command(MCUCommand.PING):
                self.status = MCUStatus.CONNECTED
                self.connected = True
                self._start_monitoring()
                self.logger.info("✅ MCU conectado correctamente")
                return True
            else:
                self.disconnect()
                return False
                
        except Exception as e:
            self.logger.error(f"Error conectando MCU: {e}")
            self.status = MCUStatus.ERROR
            return False
    
    def disconnect(self):
        """Desconectar del MCU"""
        self.stop_monitoring = True
        self.connected = False
        self.status = MCUStatus.DISCONNECTED
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.logger.info("MCU desconectado")
    
    def _send_command(self, command: MCUCommand, data: Dict[str, Any] = None) -> Optional[MCUResponse]:
        """Enviar comando al MCU"""
        try:
            if not self.connected and command != MCUCommand.PING:
                return None
            
            # Construir mensaje
            message = {
                'cmd': command.value,
                'data': data or {},
                'timestamp': datetime.now().isoformat(),
                'id': int(time.time() * 1000) % 10000
            }
            
            if SERIAL_AVAILABLE and self.serial_port:
                # Envío real por serie
                json_msg = json.dumps(message) + '\n'
                self.serial_port.write(json_msg.encode())
                self.serial_port.flush()
                
                # Leer respuesta
                response_line = self.serial_port.readline().decode().strip()
                if response_line:
                    response_data = json.loads(response_line)
                    return self._parse_response(response_data)
            else:
                # Modo simulación
                return self._simulate_response(command, data)
                
        except Exception as e:
            self.logger.error(f"Error enviando comando {command}: {e}")
            return None
    
    def _simulate_response(self, command: MCUCommand, data: Dict[str, Any] = None) -> MCUResponse:
        """Simular respuesta del MCU para desarrollo"""
        simulation_data = {
            MCUCommand.PING: {'pong': True, 'timestamp': time.time()},
            MCUCommand.STATUS: {
                'system': 'ready',
                'doors': {'A1': 'closed', 'A2': 'closed'},
                'sensors': {'door_sensor_A1': True},
                'payment': 'idle'
            },
            MCUCommand.VERSION: {'version': '1.0.0', 'build': '20250728'},
            MCUCommand.PAYMENT_START: {'transaction_id': f'tx_{int(time.time())}', 'status': 'started'},
            MCUCommand.DOOR_OPEN: {'door_id': data.get('door_id') if data else 'A1', 'status': 'opening'},
        }
        
        return MCUResponse(
            success=True,
            command=command.value,
            data=simulation_data.get(command, {}),
            timestamp=datetime.now()
        )
    
    def _parse_response(self, response_data: Dict[str, Any]) -> MCUResponse:
        """Parsear respuesta del MCU"""
        return MCUResponse(
            success=response_data.get('success', False),
            command=response_data.get('command', ''),
            data=response_data.get('data', {}),
            timestamp=datetime.fromisoformat(response_data.get('timestamp', datetime.now().isoformat())),
            error_code=response_data.get('error_code'),
            error_message=response_data.get('error_message')
        )
    
    # ===== SISTEMA Y MONITOREO =====
    
    def _start_monitoring(self):
        """Iniciar hilo de monitoreo"""
        self.stop_monitoring = False
        self.monitoring_thread = threading.Thread(target=self._monitor_mcu, daemon=True)
        self.monitoring_thread.start()
    
    def _monitor_mcu(self):
        """Monitorear estado del MCU"""
        while not self.stop_monitoring and self.connected:
            try:
                # Ping periódico
                response = self._send_command(MCUCommand.PING)
                if response and response.success:
                    self.last_ping = datetime.now()
                    self.status = MCUStatus.READY
                else:
                    self.logger.warning("Ping fallido al MCU")
                    if self.status != MCUStatus.ERROR:
                        self.status = MCUStatus.ERROR
                
                # Monitorear transacción activa
                if self.current_transaction:
                    self._monitor_payment()
                
                time.sleep(5)  # Ping cada 5 segundos
                
            except Exception as e:
                self.logger.error(f"Error en monitoreo MCU: {e}")
                time.sleep(10)
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado completo del MCU"""
        response = self._send_command(MCUCommand.STATUS)
        
        base_status = {
            'controller_status': self.status.value,
            'connected': self.connected,
            'last_ping': self.last_ping.isoformat() if self.last_ping else None,
            'current_transaction': self.current_transaction.__dict__ if self.current_transaction else None,
            'port': self.port_name,
            'baudrate': self.baudrate
        }
        
        if response and response.success:
            base_status.update(response.data)
        
        return base_status
    
    def get_version(self) -> Optional[Dict[str, str]]:
        """Obtener versión del MCU"""
        response = self._send_command(MCUCommand.VERSION)
        return response.data if response and response.success else None
    
    # ===== GESTIÓN DE PAGOS =====
    
    def start_payment(self, amount: float, currency: str = "EUR", 
                     method: PaymentMethod = PaymentMethod.CONTACTLESS,
                     door_id: str = None) -> Optional[PaymentTransaction]:
        """Iniciar transacción de pago"""
        try:
            if self.current_transaction:
                self.logger.warning("Ya hay una transacción activa")
                return None
            
            transaction_id = f"tx_{int(time.time() * 1000)}"
            
            # Crear transacción
            transaction = PaymentTransaction(
                transaction_id=transaction_id,
                method=method,
                amount=amount,
                currency=currency,
                status='started',
                started_at=datetime.now(),
                door_id=door_id
            )
            
            # Enviar comando al MCU
            payment_data = {
                'transaction_id': transaction_id,
                'amount': amount,
                'currency': currency,
                'method': method.value,
                'door_id': door_id
            }
            
            response = self._send_command(MCUCommand.PAYMENT_START, payment_data)
            
            if response and response.success:
                self.current_transaction = transaction
                self.logger.info(f"Pago iniciado: {transaction_id} - {amount} {currency}")
                self._trigger_event('payment_started', transaction)
                return transaction
            else:
                self.logger.error("Error iniciando pago en MCU")
                return None
                
        except Exception as e:
            self.logger.error(f"Error iniciando pago: {e}")
            return None
    
    def get_payment_status(self) -> Optional[Dict[str, Any]]:
        """Obtener estado del pago actual"""
        if not self.current_transaction:
            return None
        
        response = self._send_command(MCUCommand.PAYMENT_STATUS)
        
        if response and response.success:
            status_data = response.data
            # Actualizar transacción
            if 'status' in status_data:
                self.current_transaction.status = status_data['status']
            
            return {
                'transaction': self.current_transaction.__dict__,
                'mcu_status': status_data
            }
        
        return {'transaction': self.current_transaction.__dict__}
    
    def cancel_payment(self) -> bool:
        """Cancelar pago actual"""
        if not self.current_transaction:
            return False
        
        response = self._send_command(MCUCommand.PAYMENT_CANCEL, {
            'transaction_id': self.current_transaction.transaction_id
        })
        
        if response and response.success:
            self.current_transaction.status = 'cancelled'
            self.current_transaction.completed_at = datetime.now()
            self._finalize_transaction()
            self.logger.info("Pago cancelado")
            return True
        
        return False
    
    def confirm_payment(self) -> bool:
        """Confirmar pago completado"""
        if not self.current_transaction:
            return False
        
        response = self._send_command(MCUCommand.PAYMENT_CONFIRM, {
            'transaction_id': self.current_transaction.transaction_id
        })
        
        if response and response.success:
            self.current_transaction.status = 'completed'
            self.current_transaction.completed_at = datetime.now()
            self._finalize_transaction()
            self.logger.info("Pago confirmado")
            return True
        
        return False
    
    def _monitor_payment(self):
        """Monitorear pago activo"""
        if not self.current_transaction:
            return
        
        # Timeout de transacción (5 minutos)
        if (datetime.now() - self.current_transaction.started_at).seconds > 300:
            self.logger.warning("Timeout de transacción")
            self.cancel_payment()
            return
        
        # Verificar estado en MCU
        status = self.get_payment_status()
        if status and 'mcu_status' in status:
            mcu_status = status['mcu_status'].get('status', '')
            
            if mcu_status == 'completed':
                self.confirm_payment()
                self._trigger_event('payment_completed', self.current_transaction)
            elif mcu_status == 'failed':
                self.current_transaction.status = 'failed'
                self.current_transaction.error_code = status['mcu_status'].get('error_code')
                self._finalize_transaction()
                self._trigger_event('payment_failed', self.current_transaction)
    
    def _finalize_transaction(self):
        """Finalizar transacción actual"""
        if self.current_transaction:
            self.transaction_history.append(self.current_transaction)
            self.current_transaction = None
    
    # ===== CONTROL DE PUERTAS =====
    
    def open_door(self, door_id: str, duration: float = 30.0) -> bool:
        """Abrir puerta específica"""
        response = self._send_command(MCUCommand.DOOR_OPEN, {
            'door_id': door_id,
            'duration': duration
        })
        
        if response and response.success:
            self.logger.info(f"Puerta {door_id} abierta")
            self._trigger_event('door_opened', {'door_id': door_id, 'duration': duration})
            return True
        
        return False
    
    def close_door(self, door_id: str) -> bool:
        """Cerrar puerta específica"""
        response = self._send_command(MCUCommand.DOOR_CLOSE, {
            'door_id': door_id
        })
        
        if response and response.success:
            self.logger.info(f"Puerta {door_id} cerrada")
            self._trigger_event('door_closed', {'door_id': door_id})
            return True
        
        return False
    
    def get_door_status(self, door_id: str = None) -> Dict[str, Any]:
        """Obtener estado de puertas"""
        data = {'door_id': door_id} if door_id else {}
        response = self._send_command(MCUCommand.DOOR_STATUS, data)
        
        return response.data if response and response.success else {}
    
    # ===== SENSORES =====
    
    def read_sensor(self, sensor_id: str) -> Optional[Any]:
        """Leer sensor específico"""
        response = self._send_command(MCUCommand.SENSOR_READ, {
            'sensor_id': sensor_id
        })
        
        if response and response.success:
            return response.data.get('value')
        
        return None
    
    def get_all_sensors(self) -> Dict[str, Any]:
        """Obtener estado de todos los sensores"""
        response = self._send_command(MCUCommand.SENSOR_STATUS)
        return response.data if response and response.success else {}
    
    # ===== RESTOCK =====
    
    def enable_restock_mode(self) -> bool:
        """Activar modo restock"""
        response = self._send_command(MCUCommand.RESTOCK_MODE, {'enabled': True})
        
        if response and response.success:
            self.logger.info("Modo restock activado")
            self._trigger_event('restock_enabled', {})
            return True
        
        return False
    
    def disable_restock_mode(self) -> bool:
        """Desactivar modo restock"""
        response = self._send_command(MCUCommand.RESTOCK_MODE, {'enabled': False})
        
        if response and response.success:
            self.logger.info("Modo restock desactivado")
            self._trigger_event('restock_disabled', {})
            return True
        
        return False
    
    # ===== UTILIDADES =====
    
    def set_led(self, led_id: str, color: str, brightness: int = 100) -> bool:
        """Controlar LEDs"""
        response = self._send_command(MCUCommand.SET_LED, {
            'led_id': led_id,
            'color': color,
            'brightness': brightness
        })
        
        return response and response.success
    
    def buzzer(self, frequency: int = 1000, duration: float = 0.5) -> bool:
        """Activar buzzer"""
        response = self._send_command(MCUCommand.BUZZER, {
            'frequency': frequency,
            'duration': duration
        })
        
        return response and response.success
    
    def display_message(self, message: str, duration: float = 5.0) -> bool:
        """Mostrar mensaje en display del MCU"""
        response = self._send_command(MCUCommand.DISPLAY_MSG, {
            'message': message,
            'duration': duration
        })
        
        return response and response.success
    
    # ===== EVENTOS =====
    
    def add_event_callback(self, event: str, callback: Callable):
        """Agregar callback para evento"""
        if event not in self.event_callbacks:
            self.event_callbacks[event] = []
        self.event_callbacks[event].append(callback)
    
    def _trigger_event(self, event: str, data: Any):
        """Disparar evento"""
        if event in self.event_callbacks:
            for callback in self.event_callbacks[event]:
                try:
                    callback(data)
                except Exception as e:
                    self.logger.error(f"Error en callback {event}: {e}")
    
    # ===== UTILIDADES DE DESARROLLO =====
    
    def list_ports(self) -> List[str]:
        """Listar puertos serie disponibles"""
        if not SERIAL_AVAILABLE:
            return ["/dev/ttyUSB0", "/dev/ttyACM0", "COM1", "COM3"]
        
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    
    def test_connection(self, port: str = None) -> Dict[str, Any]:
        """Probar conexión en puerto específico"""
        test_port = port or self.port_name
        
        try:
            if not SERIAL_AVAILABLE:
                return {
                    'success': True,
                    'message': 'Modo simulación',
                    'port': test_port
                }
            
            test_serial = serial.Serial(test_port, self.baudrate, timeout=2)
            test_serial.close()
            
            return {
                'success': True,
                'message': 'Puerto disponible',
                'port': test_port
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
                'port': test_port
            }
    
    def get_transaction_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtener historial de transacciones"""
        return [tx.__dict__ for tx in self.transaction_history[-limit:]]
    
    def reset_mcu(self) -> bool:
        """Resetear MCU"""
        response = self._send_command(MCUCommand.RESET)
        
        if response and response.success:
            self.logger.info("MCU reseteado")
            return True
        
        return False


# Instancia global (se inicializa en la aplicación principal)
mcu_controller = None


def initialize_mcu_controller(config: Dict[str, Any]) -> MCUController:
    """Inicializar controlador MCU"""
    global mcu_controller
    mcu_controller = MCUController(config)
    return mcu_controller


def get_mcu_controller() -> Optional[MCUController]:
    """Obtener instancia del controlador MCU"""
    return mcu_controller


# Ejemplo de uso:
if __name__ == "__main__":
    # Configuración de ejemplo
    config = {
        'port': '/dev/ttyUSB0',
        'baudrate': 115200,
        'timeout': 5
    }
    
    # Inicializar
    mcu = MCUController(config)
    
    # Conectar
    if mcu.connect():
        print("✅ MCU conectado")
        
        # Obtener estado
        status = mcu.get_status()
        print(f"Estado: {status}")
        
        # Ejemplo de pago
        transaction = mcu.start_payment(5.50, "EUR", PaymentMethod.CONTACTLESS, "A1")
        if transaction:
            print(f"Pago iniciado: {transaction.transaction_id}")
            
            # Simular confirmación después de 3 segundos
            time.sleep(3)
            if mcu.confirm_payment():
                print("✅ Pago confirmado")
        
        # Desconectar
        mcu.disconnect()
    else:
        print("❌ Error conectando MCU")
