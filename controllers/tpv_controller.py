"""
Controlador para comunicación con TPV (Terminal Punto de Venta)
Maneja comunicación serial para pagos contactless
"""
import logging
import time
import random
import string
from typing import Dict, Any, Optional
from config import Config

logger = logging.getLogger(__name__)

class TPVController:
    def __init__(self):
        self.platform = Config.PLATFORM
        self.simulate_payments = Config.SIMULATE_PAYMENTS
        self.tpv_enabled = Config.TPV_ENABLED
        self.port = None
        self.serial_config = {
            'port': '/dev/ttyUSB0',  # Puerto serial para Raspberry Pi
            'baudrate': 9600,
            'timeout': 5
        }
        
        # Almacenar pagos pendientes
        self.pending_payments = {}
        
        if not self.simulate_payments and self.tpv_enabled:
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
            
            if not self.simulate_payments and self.tpv_enabled:
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
            
    def init_payment(self, amount: float, door_id: str = None) -> Dict[str, Any]:
        """
        Iniciar un pago contactless en el TPV
        
        Args:
            amount: Monto a cobrar en euros
            door_id: ID de la puerta (opcional, para tracking)
            
        Returns:
            Dict con resultado de la inicialización del pago
        """
        try:
            if not self.tpv_enabled:
                return {
                    'success': False,
                    'error': 'TPV no habilitado',
                    'amount': amount
                }
            
            # Generar payment_id único
            payment_id = self._generate_payment_id()
            
            # Convertir euros a céntimos
            amount_cents = int(amount * 100)
            
            logger.info(f"Iniciando pago {payment_id} por €{amount:.2f} para puerta {door_id}")
            
            if not self.simulate_payments and self.tpv_enabled:
                result = self._init_real_payment(payment_id, amount_cents, door_id)
            else:
                result = self._init_simulated_payment(payment_id, amount_cents, door_id)
            
            if result['success']:
                # Almacenar información del pago pendiente
                self.pending_payments[payment_id] = {
                    'amount': amount,
                    'door_id': door_id,
                    'status': 'pending',
                    'created_at': time.time(),
                    'amount_cents': amount_cents
                }
                
                logger.info(f"Pago {payment_id} iniciado exitosamente")
                
            return result
            
        except Exception as e:
            logger.error(f"Error al iniciar pago: {e}")
            return {
                'success': False,
                'error': f'Error iniciando pago: {str(e)}',
                'amount': amount
            }
    
    def check_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Consultar estado de un pago en el TPV
        
        Args:
            payment_id: ID del pago a consultar
            
        Returns:
            Dict con estado del pago
        """
        try:
            if payment_id not in self.pending_payments:
                return {
                    'success': False,
                    'error': 'Payment ID no encontrado',
                    'payment_id': payment_id
                }
            
            payment_info = self.pending_payments[payment_id]
            
            logger.info(f"Consultando estado del pago {payment_id}")
            
            if not self.simulate_payments and self.tpv_enabled:
                result = self._check_real_payment_status(payment_id, payment_info)
            else:
                result = self._check_simulated_payment_status(payment_id, payment_info)
            
            # Actualizar estado del pago
            if result['success'] and result['status'] in ['approved', 'declined', 'timeout']:
                # Pago completado (exitoso o fallido), remover de pendientes
                if payment_id in self.pending_payments:
                    del self.pending_payments[payment_id]
                    logger.info(f"Pago {payment_id} completado y removido de pendientes")
            
            return result
            
        except Exception as e:
            logger.error(f"Error consultando estado de pago {payment_id}: {e}")
            return {
                'success': False,
                'error': f'Error consultando estado: {str(e)}',
                'payment_id': payment_id
            }
    
    def _generate_payment_id(self) -> str:
        """Generar ID único para el pago"""
        timestamp = int(time.time())
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"PAY_{timestamp}_{random_part}"
    
    def _init_real_payment(self, payment_id: str, amount_cents: int, door_id: str) -> Dict[str, Any]:
        """Inicializar pago real con TPV físico"""
        tpv = None
        try:
            # Abrir puerto serial
            tpv = self.serial.Serial(
                self.serial_config['port'],
                baudrate=self.serial_config['baudrate'],
                timeout=self.serial_config['timeout']
            )
            
            logger.info(f"Conexión TPV establecida para pago {payment_id}")
            
            # Enviar comando de inicialización de pago
            comando = f":INIT_PAYMENT:{payment_id}:{amount_cents:06d}:\n".encode()
            tpv.write(comando)
            
            logger.info(f"Comando enviado al TPV: {comando.decode().strip()}")
            
            # Esperar respuesta de inicialización
            respuesta = tpv.readline()
            respuesta_str = respuesta.decode().strip()
            
            logger.info(f"Respuesta del TPV: {respuesta_str}")
            
            # Parsear respuesta de inicialización
            if ":INIT_OK:" in respuesta_str:
                return {
                    'success': True,
                    'payment_id': payment_id,
                    'status': 'initiated',
                    'message': 'Pago iniciado en TPV - esperando tarjeta'
                }
            else:
                return {
                    'success': False,
                    'error': f'Error iniciando pago en TPV: {respuesta_str}',
                    'payment_id': payment_id
                }
            
        except Exception as e:
            logger.error(f"Error en inicialización TPV: {e}")
            return {
                'success': False,
                'error': f'Error de comunicación serial: {str(e)}',
                'payment_id': payment_id
            }
        finally:
            if tpv:
                tpv.close()
                logger.info("Conexión TPV cerrada")
    
    def _init_simulated_payment(self, payment_id: str, amount_cents: int, door_id: str) -> Dict[str, Any]:
        """Inicializar pago simulado para testing"""
        try:
            # Simular comando de inicialización
            comando = f":INIT_PAYMENT:{payment_id}:{amount_cents:06d}:\n"
            logger.info(f"TPV Simulado - Comando init: {comando.strip()}")
            
            # Simular respuesta exitosa
            respuesta = f":INIT_OK:{payment_id}:\n"
            logger.info(f"TPV Simulado - Respuesta init: {respuesta.strip()}")
            
            return {
                'success': True,
                'payment_id': payment_id,
                'status': 'initiated',
                'message': 'Pago simulado iniciado - esperando tarjeta'
            }
            
        except Exception as e:
            logger.error(f"Error en simulación init TPV: {e}")
            return {
                'success': False,
                'error': f'Error en simulación: {str(e)}',
                'payment_id': payment_id
            }
    
    def _check_real_payment_status(self, payment_id: str, payment_info: Dict) -> Dict[str, Any]:
        """Consultar estado de pago real con TPV físico"""
        tpv = None
        try:
            # Abrir puerto serial
            tpv = self.serial.Serial(
                self.serial_config['port'],
                baudrate=self.serial_config['baudrate'],
                timeout=self.serial_config['timeout']
            )
            
            # Enviar comando de consulta de estado
            comando = f":CHECK_STATUS:{payment_id}:\n".encode()
            tpv.write(comando)
            
            logger.info(f"Consultando estado TPV: {comando.decode().strip()}")
            
            # Esperar respuesta
            respuesta = tpv.readline()
            respuesta_str = respuesta.decode().strip()
            
            logger.info(f"Respuesta estado TPV: {respuesta_str}")
            
            # Parsear respuesta de estado
            return self._parse_status_response(respuesta_str, payment_id, payment_info)
            
        except Exception as e:
            logger.error(f"Error consultando estado TPV: {e}")
            return {
                'success': False,
                'error': f'Error de comunicación serial: {str(e)}',
                'payment_id': payment_id
            }
        finally:
            if tpv:
                tpv.close()
    
    def _check_simulated_payment_status(self, payment_id: str, payment_info: Dict) -> Dict[str, Any]:
        """Consultar estado de pago simulado"""
        try:
            # Simular progreso del pago basado en tiempo transcurrido
            elapsed_time = time.time() - payment_info['created_at']
            
            # Simular comando de consulta
            comando = f":CHECK_STATUS:{payment_id}:\n"
            logger.info(f"TPV Simulado - Consulta estado: {comando.strip()}")
            
            if elapsed_time < 3:
                # Primeros 3 segundos: pending
                respuesta = f":STATUS:{payment_id}:PENDING:\n"
                status = 'pending'
            elif elapsed_time < 8:
                # Entre 3-8 segundos: simular aprobación (90% éxito)
                if random.random() < 0.9:
                    transaction_id = f"TXN_{payment_id}_{int(time.time())}"
                    respuesta = f":STATUS:{payment_id}:APPROVED:{transaction_id}:\n"
                    status = 'approved'
                else:
                    respuesta = f":STATUS:{payment_id}:DECLINED:CARD_ERROR:\n"
                    status = 'declined'
            else:
                # Más de 8 segundos: timeout
                respuesta = f":STATUS:{payment_id}:TIMEOUT:\n"
                status = 'timeout'
            
            logger.info(f"TPV Simulado - Respuesta estado: {respuesta.strip()}")
            
            return self._parse_status_response(respuesta, payment_id, payment_info)
            
        except Exception as e:
            logger.error(f"Error en simulación estado TPV: {e}")
            return {
                'success': False,
                'error': f'Error en simulación: {str(e)}',
                'payment_id': payment_id
            }
    
    def _parse_status_response(self, response: str, payment_id: str, payment_info: Dict) -> Dict[str, Any]:
        """Parsear respuesta de estado del TPV"""
        try:
            parts = response.strip().split(':')
            logger.info(f"Parseando respuesta TPV: {parts}")
            
            # Formato esperado: :STATUS:payment_id:APPROVED:transaction_id:
            # parts[0] = '' (vacío por el : inicial)
            # parts[1] = 'STATUS'
            # parts[2] = payment_id
            # parts[3] = status (APPROVED/DECLINED/PENDING/TIMEOUT)
            # parts[4] = transaction_id o razón (opcional)
            
            if len(parts) >= 4 and parts[1] == 'STATUS' and parts[2] == payment_id:
                status = parts[3]
                
                if status == 'APPROVED':
                    transaction_id = parts[4] if len(parts) > 4 else f"TXN_{payment_id}"
                    return {
                        'success': True,
                        'status': 'approved',
                        'payment_id': payment_id,
                        'transaction_id': transaction_id,
                        'amount': payment_info['amount'],
                        'message': 'Pago aprobado exitosamente'
                    }
                elif status == 'DECLINED':
                    reason = parts[4] if len(parts) > 4 else 'UNKNOWN'
                    return {
                        'success': False,
                        'status': 'declined',
                        'payment_id': payment_id,
                        'message': f'Pago rechazado: {reason}'
                    }
                elif status == 'PENDING':
                    return {
                        'success': True,
                        'status': 'pending',
                        'payment_id': payment_id,
                        'message': 'Pago en proceso - esperando tarjeta'
                    }
                elif status == 'TIMEOUT':
                    return {
                        'success': False,
                        'status': 'timeout',
                        'payment_id': payment_id,
                        'message': 'Tiempo de espera agotado'
                    }
                else:
                    return {
                        'success': False,
                        'status': 'unknown',
                        'payment_id': payment_id,
                        'message': f'Estado desconocido: {status}'
                    }
            else:
                logger.error(f"Respuesta TPV con formato inválido: {response}")
                logger.error(f"Parts: {parts}, Expected payment_id: {payment_id}")
                return {
                    'success': False,
                    'error': f'Respuesta TPV inválida para consulta de estado. Formato recibido: {response[:50]}...',
                    'payment_id': payment_id
                }
                
        except Exception as e:
            logger.error(f"Error parseando respuesta de estado: {e}")
            return {
                'success': False,
                'error': f'Error interpretando respuesta: {str(e)}',
                'payment_id': payment_id
            } 
    
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
            if not self.simulate_payments and self.tpv_enabled:
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
            'simulate_payments': self.simulate_payments,
            'tpv_enabled': self.tpv_enabled,
            'serial_config': self.serial_config,
            'connection_status': 'simulated' if self.simulate_payments else 'real'
        }
