"""
Controlador para comunicación con TPV (Terminal Punto de Venta)
Maneja comunicación serial para pagos contactless
"""
import logging
import time
from typing import Dict, Any, Optional
from config import Config

logger = logging.getLogger(__name__)

class TPVController:
    def __init__(self):
        self.platform = Config.PLATFORM
        self.tpv_enabled = True  # Habilitar TPV por defecto
        self.port = None
        self.serial_config = {
            'port': '/dev/ttyUSB0',  # Puerto serial para Raspberry Pi
            'baudrate': 9600,
            'timeout': 5
        }
        
        if self.platform == 'raspberry' and self.tpv_enabled:
            self._init_raspberry_tpv()
        else:
            self._init_tpv_simulation()
    
    def _init_raspberry_tpv(self):
        """Inicializar comunicación serial real para Raspberry Pi"""
        try:
            import serial
            self.serial = serial
            logger.info("TPV real inicializado para Raspberry Pi")
            
        except ImportError:
            logger.error("Librería pyserial no encontrada. Cambiando a modo simulación.")
            self._init_tpv_simulation()
    
    def _init_tpv_simulation(self):
        """Inicializar simulación de TPV para Windows"""
        class SimulatedTPV:
            def __init__(self):
                self.is_connected = True
            
            def write(self, data):
                logger.info(f"TPV Simulado - Enviando: {data}")
                return len(data)
            
            def readline(self):
                # Simular respuesta exitosa del TPV
                return ":OK:APPROVED:12345:\n".encode()
            
            def close(self):
                logger.info("TPV Simulado - Conexión cerrada")
        
        self.serial = None
        self.simulated_tpv = SimulatedTPV()
        logger.info("TPV simulado inicializado (Windows)")
    
    def process_contactless_payment(self, amount: float) -> Dict[str, Any]:
        """
        Procesar pago contactless a través del TPV
        
        Args:
            amount: Monto a cobrar en euros
            
        Returns:
            Dict con resultado del pago
        """
        try:
            # Convertir euros a céntimos
            amount_cents = int(amount * 100)
            
            logger.info(f"Iniciando pago contactless por €{amount:.2f} ({amount_cents} céntimos)")
            
            if self.platform == 'raspberry' and self.tpv_enabled:
                return self._process_real_payment(amount_cents)
            else:
                return self._process_simulated_payment(amount_cents)
                
        except Exception as e:
            logger.error(f"Error al procesar pago contactless: {e}")
            return {
                'success': False,
                'error': f'Error de comunicación con TPV: {str(e)}',
                'amount': amount,
                'transaction_id': None
            }
    
    def _process_real_payment(self, amount_cents: int) -> Dict[str, Any]:
        """Procesar pago real con TPV físico"""
        tpv = None
        try:
            # Abrir puerto serial
            tpv = self.serial.Serial(
                self.serial_config['port'],
                baudrate=self.serial_config['baudrate'],
                timeout=self.serial_config['timeout']
            )
            
            logger.info(f"Conexión TPV establecida en {self.serial_config['port']}")
            
            # Enviar comando de cobro al TPV
            comando = f":SALE:{amount_cents:06d}:\n".encode()
            tpv.write(comando)
            
            logger.info(f"Comando enviado al TPV: {comando.decode().strip()}")
            
            # Esperar respuesta
            respuesta = tpv.readline()
            respuesta_str = respuesta.decode().strip()
            
            logger.info(f"Respuesta del TPV: {respuesta_str}")
            
            # Parsear respuesta del TPV
            return self._parse_tpv_response(respuesta_str, amount_cents / 100)
            
        except Exception as e:
            logger.error(f"Error en comunicación TPV: {e}")
            return {
                'success': False,
                'error': f'Error de comunicación serial: {str(e)}',
                'amount': amount_cents / 100,
                'transaction_id': None
            }
        finally:
            if tpv:
                tpv.close()
                logger.info("Conexión TPV cerrada")
    
    def _process_simulated_payment(self, amount_cents: int) -> Dict[str, Any]:
        """Procesar pago simulado para testing"""
        try:
            # Simular tiempo de procesamiento
            time.sleep(2)
            
            # Simular comando al TPV
            comando = f":SALE:{amount_cents:06d}:\n"
            logger.info(f"TPV Simulado - Comando: {comando.strip()}")
            
            # Simular respuesta exitosa
            respuesta = ":OK:APPROVED:12345:\n"
            logger.info(f"TPV Simulado - Respuesta: {respuesta.strip()}")
            
            return self._parse_tpv_response(respuesta, amount_cents / 100)
            
        except Exception as e:
            logger.error(f"Error en simulación TPV: {e}")
            return {
                'success': False,
                'error': f'Error en simulación: {str(e)}',
                'amount': amount_cents / 100,
                'transaction_id': None
            }
            
    def init_payment(self, amount: float) -> Dict[str, Any]:
        """
        Iniciar un pago contactless
        
        Args:
            amount: Monto a cobrar en euros
            
        Returns:
            Dict con resultado del pago
        """
        if not self.tpv_enabled:
            return {
                'success': False,
                'error': 'TPV no habilitado',
                'amount': amount,
                'transaction_id': None
            }
        
        return re
    
    def _parse_tpv_response(self, response: str, amount: float) -> Dict[str, Any]:
        """
        Parsear respuesta del TPV
        
        Formato esperado: :STATUS:RESULT:TRANSACTION_ID:
        Ejemplo: :OK:APPROVED:12345:
        """
        try:
            parts = response.strip().split(':')
            
            if len(parts) >= 4:
                status = parts[1]
                result = parts[2]
                transaction_id = parts[3]
                
                if status == 'OK' and result == 'APPROVED':
                    return {
                        'success': True,
                        'status': 'approved',
                        'amount': amount,
                        'transaction_id': transaction_id,
                        'payment_method': 'contactless',
                        'timestamp': time.time()
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Pago rechazado: {result}',
                        'amount': amount,
                        'transaction_id': transaction_id
                    }
            else:
                return {
                    'success': False,
                    'error': 'Respuesta TPV inválida',
                    'amount': amount,
                    'transaction_id': None
                }
                
        except Exception as e:
            logger.error(f"Error al parsear respuesta TPV: {e}")
            return {
                'success': False,
                'error': f'Error al interpretar respuesta: {str(e)}',
                'amount': amount,
                'transaction_id': None
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """Probar conexión con el TPV"""
        try:
            if self.platform == 'raspberry' and self.tpv_enabled:
                # Probar conexión real
                tpv = self.serial.Serial(
                    self.serial_config['port'],
                    baudrate=self.serial_config['baudrate'],
                    timeout=2
                )
                
                # Enviar comando de test
                test_cmd = ":TEST:\n".encode()
                tpv.write(test_cmd)
                
                response = tpv.readline()
                tpv.close()
                
                return {
                    'success': True,
                    'message': 'Conexión TPV exitosa',
                    'response': response.decode().strip()
                }
            else:
                # Simulación
                return {
                    'success': True,
                    'message': 'TPV simulado funcionando correctamente',
                    'response': ':OK:TEST:READY:'
                }
                
        except Exception as e:
            logger.error(f"Error al probar conexión TPV: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Error de conexión con TPV'
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado del controlador TPV"""
        return {
            'platform': self.platform,
            'tpv_enabled': self.tpv_enabled,
            'serial_config': self.serial_config,
            'connection_status': 'simulated' if self.platform == 'windows' else 'real'
        }
