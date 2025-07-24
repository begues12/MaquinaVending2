"""
Controlador de configuración de la máquina expendedora
Maneja la carga y actualización de la configuración desde JSON
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

class MachineConfigManager:
    def __init__(self, config_path: str = "machine_config.json"):
        self.config_path = Path(config_path)
        self.config = {}
        self.load_config()
    
    def load_config(self) -> bool:
        """Cargar configuración desde archivo JSON"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info("Configuración cargada correctamente")
                return True
            else:
                logger.error(f"Archivo de configuración no encontrado: {self.config_path}")
                return False
        except Exception as e:
            logger.error(f"Error al cargar configuración: {e}")
            return False
    
    def save_config(self) -> bool:
        """Guardar configuración al archivo JSON"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info("Configuración guardada correctamente")
            return True
        except Exception as e:
            logger.error(f"Error al guardar configuración: {e}")
            return False
    
    def get_doors(self) -> Dict[str, Any]:
        """Obtener configuración de todas las puertas (solo info física)"""
        return self.config.get('doors', {})
    
    def get_door(self, door_id: str) -> Optional[Dict[str, Any]]:
        """Obtener configuración física de una puerta específica"""
        doors = self.get_doors()
        return doors.get(door_id)
    
    def get_door_with_product(self, door_id: str) -> Optional[Dict[str, Any]]:
        """Obtener puerta con información del producto desde base de datos"""
        from database import db_manager
        
        # Obtener configuración física de la puerta
        door_config = self.get_door(door_id)
        if not door_config:
            return None
        
        # Obtener producto desde base de datos
        product = db_manager.get_product_by_door(door_id)
        
        # Combinar información
        door_info = door_config.copy()
        door_info['product'] = product
        door_info['status'] = self._calculate_door_status(door_config, product)
        
        return door_info
    
    def get_all_doors_with_products(self) -> Dict[str, Any]:
        """Obtener todas las puertas con información de productos"""
        doors = {}
        for door_id in self.get_doors().keys():
            doors[door_id] = self.get_door_with_product(door_id)
        return doors
    
    def _calculate_door_status(self, door_config: Dict, product: Optional[Dict]) -> str:
        """Calcular estado de la puerta basado en configuración y producto"""
        if not product:
            return 'no_product'
        
        if not product.get('active', True):
            return 'disabled'
        
        if door_config.get('door_open', False):
            return 'door_open'
        
        stock = product.get('stock', 0)
        min_stock = product.get('min_stock', 0)
        
        if stock <= 0:
            return 'out_of_stock'
        elif stock <= min_stock:
            return 'low_stock'
        else:
            return 'available'
    
    def update_door_sensor(self, door_id: str, door_open: bool) -> bool:
        """Actualizar estado del sensor de puerta"""
        try:
            if door_id in self.config.get('doors', {}):
                self.config['doors'][door_id]['door_open'] = door_open
                self.config['doors'][door_id]['last_maintenance'] = datetime.now().isoformat()
                
                # Registrar evento en base de datos
                from database import db_manager
                action = 'door_opened' if door_open else 'door_closed'
                db_manager.log_door_maintenance(door_id, action, 'sensor_update')
                
                self.save_config()
                return True
            return False
        except Exception as e:
            logger.error(f"Error al actualizar sensor de puerta {door_id}: {e}")
            return False
    
    def update_door_status(self, door_id: str, status: str) -> bool:
        """Actualizar estado de una puerta"""
        try:
            if door_id in self.config.get('doors', {}):
                self.config['doors'][door_id]['status'] = status
                if status == 'dispensing':
                    self.config['doors'][door_id]['last_dispensed'] = datetime.now().isoformat()
                return self.save_config()
            return False
        except Exception as e:
            logger.error(f"Error al actualizar estado de puerta {door_id}: {e}")
            return False
    
    def update_door_stock(self, door_id: str, new_stock: int) -> bool:
        """Actualizar stock de una puerta"""
        try:
            if door_id in self.config.get('doors', {}):
                door = self.config['doors'][door_id]
                door['product']['stock'] = new_stock
                
                # Actualizar estado según stock
                if new_stock <= 0:
                    door['status'] = 'out_of_stock'
                    door['requires_restock'] = True
                elif door['status'] == 'out_of_stock' and new_stock > 0:
                    door['status'] = 'available'
                    door['requires_restock'] = False
                
                return self.save_config()
            return False
        except Exception as e:
            logger.error(f"Error al actualizar stock de puerta {door_id}: {e}")
            return False
    
    def block_door(self, door_id: str) -> bool:
        """Bloquear una puerta hasta reposición"""
        return self.update_door_status(door_id, 'blocked')
    
    def unblock_door(self, door_id: str) -> bool:
        """Desbloquear una puerta después de reposición"""
        return self.update_door_status(door_id, 'available')
    
    def get_available_doors(self) -> Dict[str, Any]:
        """Obtener solo las puertas disponibles"""
        doors = self.get_doors()
        return {door_id: door for door_id, door in doors.items() 
                if door.get('status') == 'available' and door.get('product', {}).get('stock', 0) > 0}
    
    def get_machine_settings(self) -> Dict[str, Any]:
        """Obtener configuración general de la máquina"""
        return self.config.get('machine', {})
    
    def get_payment_methods(self) -> Dict[str, Any]:
        """Obtener métodos de pago habilitados"""
        return self.config.get('payment_methods', {})
    
    def get_display_settings(self) -> Dict[str, Any]:
        """Obtener configuración de pantalla"""
        return self.config.get('display', {})
    
    def is_maintenance_mode(self) -> bool:
        """Verificar si está en modo mantenimiento"""
        return self.config.get('security', {}).get('maintenance_mode', False)
    
    def set_maintenance_mode(self, enabled: bool) -> bool:
        """Activar/desactivar modo mantenimiento"""
        try:
            if 'security' not in self.config:
                self.config['security'] = {}
            self.config['security']['maintenance_mode'] = enabled
            return self.save_config()
        except Exception as e:
            logger.error(f"Error al cambiar modo mantenimiento: {e}")
            return False
    
    def dispense_product(self, door_id: str) -> Dict[str, Any]:
        """Procesar dispensado de producto"""
        try:
            door = self.get_door(door_id)
            if not door:
                return {'success': False, 'error': 'Puerta no encontrada'}
            
            if door['status'] != 'available':
                return {'success': False, 'error': f'Puerta no disponible: {door["status"]}'}
            
            if door['product']['stock'] <= 0:
                return {'success': False, 'error': 'Sin stock'}
            
            # Marcar como dispensando
            self.update_door_status(door_id, 'dispensing')
            
            # Reducir stock
            new_stock = door['product']['stock'] - 1
            self.update_door_stock(door_id, new_stock)
            
            # Si no queda stock, bloquear hasta reposición
            if new_stock <= 0:
                self.block_door(door_id)
            else:
                # Volver a disponible
                self.update_door_status(door_id, 'available')
            
            return {
                'success': True,
                'door_id': door_id,
                'product': door['product'],
                'remaining_stock': new_stock,
                'gpio_pin': door['gpio_pin']
            }
            
        except Exception as e:
            logger.error(f"Error al dispensar producto de {door_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def restock_door(self, door_id: str, quantity: int) -> bool:
        """Reabastecer una puerta"""
        try:
            door = self.get_door(door_id)
            if not door:
                return False
            
            current_stock = door['product']['stock']
            new_stock = current_stock + quantity
            
            # Actualizar stock y desbloquear
            self.update_door_stock(door_id, new_stock)
            
            if door['status'] in ['blocked', 'out_of_stock']:
                self.unblock_door(door_id)
            
            logger.info(f"Puerta {door_id} reabastecida: {current_stock} -> {new_stock}")
            return True
            
        except Exception as e:
            logger.error(f"Error al reabastecer puerta {door_id}: {e}")
            return False
    
    def get_doors_needing_restock(self) -> Dict[str, Any]:
        """Obtener puertas que necesitan reabastecimiento"""
        doors = self.get_doors()
        return {door_id: door for door_id, door in doors.items() 
                if door.get('requires_restock', False) or door.get('product', {}).get('stock', 0) <= 2}
    
    def get_secret_sequence_config(self) -> Dict[str, Any]:
        """Obtener configuración de la secuencia secreta"""
        restock_config = self.config.get('machine', {}).get('restock_mode', {})
        return restock_config.get('secret_sequence', {
            'enabled': False,
            'sequence': [],
            'timeout': 5,
            'max_attempts': 3
        })
    
    def is_secret_sequence_enabled(self) -> bool:
        """Verificar si la secuencia secreta está habilitada"""
        sequence_config = self.get_secret_sequence_config()
        return sequence_config.get('enabled', False)
    
    def get_secret_sequence(self) -> List[str]:
        """Obtener la secuencia secreta de puertas"""
        sequence_config = self.get_secret_sequence_config()
        return sequence_config.get('sequence', [])
    
    def get_sequence_timeout(self) -> int:
        """Obtener timeout para la secuencia en segundos"""
        sequence_config = self.get_secret_sequence_config()
        return sequence_config.get('timeout', 5)
    
    def get_max_sequence_attempts(self) -> int:
        """Obtener máximo número de intentos de secuencia"""
        sequence_config = self.get_secret_sequence_config()
        return sequence_config.get('max_attempts', 3)


# Instancia global del manejador de configuración
config_manager = MachineConfigManager()
