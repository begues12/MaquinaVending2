"""
Utilidades para mantenimiento y administración del sistema
"""
import logging
import json
from datetime import datetime, timedelta
from database import db_manager
from config import Config

logger = logging.getLogger(__name__)

class MaintenanceUtils:
    """Utilidades de mantenimiento para la máquina expendedora"""
    
    @staticmethod
    def backup_database(backup_path: str = None) -> bool:
        """Crear backup de la base de datos"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"database/backup_vending_{timestamp}.db"
        
        try:
            import shutil
            shutil.copy2(Config.DATABASE_PATH, backup_path)
            logger.info(f"Backup creado en: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Error al crear backup: {e}")
            return False
    
    @staticmethod
    def generate_sales_report(days: int = 7) -> dict:
        """Generar reporte de ventas"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Fecha de inicio
            start_date = datetime.now() - timedelta(days=days)
            
            # Ventas por día
            cursor.execute('''
                SELECT DATE(created_at) as date, COUNT(*) as sales, SUM(amount) as revenue
                FROM transactions 
                WHERE status = 'completed' AND created_at >= ?
                GROUP BY DATE(created_at)
                ORDER BY date
            ''', (start_date,))
            
            daily_sales = [dict(zip([col[0] for col in cursor.description], row)) 
                          for row in cursor.fetchall()]
            
            # Productos más vendidos
            cursor.execute('''
                SELECT p.name, COUNT(*) as quantity, SUM(t.amount) as revenue
                FROM transactions t
                JOIN products p ON t.product_id = p.id
                WHERE t.status = 'completed' AND t.created_at >= ?
                GROUP BY p.id, p.name
                ORDER BY quantity DESC
                LIMIT 10
            ''', (start_date,))
            
            top_products = [dict(zip([col[0] for col in cursor.description], row)) 
                           for row in cursor.fetchall()]
            
            # Métodos de pago
            cursor.execute('''
                SELECT payment_method, COUNT(*) as transactions, SUM(amount) as revenue
                FROM transactions 
                WHERE status = 'completed' AND created_at >= ?
                GROUP BY payment_method
            ''', (start_date,))
            
            payment_methods = [dict(zip([col[0] for col in cursor.description], row)) 
                              for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'period': f'{days} días',
                'start_date': start_date.isoformat(),
                'end_date': datetime.now().isoformat(),
                'daily_sales': daily_sales,
                'top_products': top_products,
                'payment_methods': payment_methods
            }
            
        except Exception as e:
            logger.error(f"Error al generar reporte: {e}")
            return {}
    
    @staticmethod
    def check_low_stock(threshold: int = 5) -> list:
        """Verificar productos con stock bajo"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, stock, slot
                FROM products 
                WHERE active = 1 AND stock <= ?
                ORDER BY stock ASC
            ''', (threshold,))
            
            low_stock = [dict(zip([col[0] for col in cursor.description], row)) 
                        for row in cursor.fetchall()]
            
            conn.close()
            return low_stock
            
        except Exception as e:
            logger.error(f"Error al verificar stock: {e}")
            return []
    
    @staticmethod
    def update_product_stock(product_id: int, new_stock: int) -> bool:
        """Actualizar stock de un producto"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE products 
                SET stock = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_stock, product_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                logger.info(f"Stock actualizado para producto {product_id}: {new_stock}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error al actualizar stock: {e}")
            return False
    
    @staticmethod
    def get_system_health() -> dict:
        """Obtener estado de salud del sistema"""
        health = {
            'timestamp': datetime.now().isoformat(),
            'database': 'ok',
            'gpio': 'ok',
            'payments': {
                'stripe': 'unknown',
                'paypal': 'unknown'
            },
            'storage': 'ok',
            'warnings': [],
            'errors': []
        }
        
        try:
            # Verificar base de datos
            products = db_manager.get_all_products()
            if not products:
                health['warnings'].append('No hay productos configurados')
            
            # Verificar stock bajo
            low_stock = MaintenanceUtils.check_low_stock()
            if low_stock:
                health['warnings'].append(f'{len(low_stock)} productos con stock bajo')
            
            # Verificar espacio en disco (simplificado)
            import os
            db_size = os.path.getsize(Config.DATABASE_PATH) if os.path.exists(Config.DATABASE_PATH) else 0
            if db_size > 100 * 1024 * 1024:  # 100MB
                health['warnings'].append('Base de datos grande (>100MB)')
            
        except Exception as e:
            health['errors'].append(f'Error verificando salud: {str(e)}')
            health['database'] = 'error'
        
        return health
    
    @staticmethod
    def cleanup_old_logs(days: int = 30) -> bool:
        """Limpiar logs antiguos"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM system_logs 
                WHERE created_at < ?
            ''', (cutoff_date,))
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Eliminados {deleted} logs antiguos")
            return True
            
        except Exception as e:
            logger.error(f"Error al limpiar logs: {e}")
            return False


class AdminAPI:
    """API administrativa para la máquina expendedora"""
    
    @staticmethod
    def add_product(name: str, price: float, stock: int, slot: str, 
                   description: str = '', image_url: str = '') -> dict:
        """Añadir nuevo producto"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO products (name, price, stock, slot, description, image_url, active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (name, price, stock, slot, description, image_url))
            
            product_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Producto añadido: {name} (ID: {product_id})")
            return {'success': True, 'product_id': product_id}
            
        except Exception as e:
            logger.error(f"Error al añadir producto: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def update_product(product_id: int, **kwargs) -> dict:
        """Actualizar producto existente"""
        try:
            valid_fields = ['name', 'price', 'stock', 'description', 'image_url', 'active']
            updates = {k: v for k, v in kwargs.items() if k in valid_fields}
            
            if not updates:
                return {'success': False, 'error': 'No hay campos válidos para actualizar'}
            
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [product_id]
            
            cursor.execute(f'''
                UPDATE products 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', values)
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                logger.info(f"Producto {product_id} actualizado")
                return {'success': True}
            else:
                return {'success': False, 'error': 'Producto no encontrado'}
                
        except Exception as e:
            logger.error(f"Error al actualizar producto: {e}")
            return {'success': False, 'error': str(e)}


# Instancias globales
maintenance = MaintenanceUtils()
admin_api = AdminAPI()
