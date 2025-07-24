"""
Modelo de base de datos para la máquina expendedora
"""
import sqlite3
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self.init_database()
    
    def get_connection(self):
        """Obtener conexión a la base de datos"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Inicializar la base de datos con las tablas necesarias"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Tabla de productos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    stock INTEGER NOT NULL DEFAULT 0,
                    door_id TEXT UNIQUE NOT NULL,
                    image_url TEXT,
                    description TEXT,
                    active BOOLEAN DEFAULT 1,
                    min_stock INTEGER DEFAULT 0,
                    max_stock INTEGER DEFAULT 10,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de ventas/transacciones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    door_id TEXT NOT NULL,
                    payment_method TEXT NOT NULL,
                    amount REAL NOT NULL,
                    status TEXT NOT NULL,
                    payment_id TEXT,
                    quantity INTEGER DEFAULT 1,
                    dispensed BOOLEAN DEFAULT 0,
                    dispensed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')
            
            # Tabla de reposiciones/stock
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS restocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    door_id TEXT NOT NULL,
                    quantity_added INTEGER NOT NULL,
                    previous_stock INTEGER,
                    new_stock INTEGER,
                    operator TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')
            
            # Tabla de mantenimiento de puertas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS door_maintenance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    door_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    status TEXT,
                    notes TEXT,
                    operator TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de logs del sistema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    module TEXT,
                    door_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de configuración
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
            # Insertar productos de ejemplo si no existen
            self._insert_sample_data()
            
            logger.info("Base de datos inicializada correctamente")
            
        except Exception as e:
            logger.error(f"Error al inicializar la base de datos: {e}")
    
    def _insert_sample_data(self):
        """Insertar datos de ejemplo"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Verificar si ya hay productos
            cursor.execute("SELECT COUNT(*) FROM products")
            if cursor.fetchone()[0] > 0:
                conn.close()
                return
            
            # Productos de ejemplo para las 14 puertas
            sample_products = [
                ('A1', 'Coca Cola', 1.5, 0, '/static/images/coca_cola.jpg', 'Refresco de cola clásico'),
                ('A2', 'Pepsi', 1.5, 5, '/static/images/pepsi.jpg', 'Refresco de cola alternativo'),
                ('B1', 'Agua Mineral', 1.0, 8, '/static/images/agua.jpg', 'Agua mineral natural'),
                ('B2', 'Snickers', 2.0, 0, '/static/images/snickers.jpg', 'Barrita de chocolate y cacahuetes'),
                ('C1', 'Kit Kat', 1.8, 6, '/static/images/kitkat.jpg', 'Barrita de chocolate con galleta'),
                ('C2', 'Twix', 1.8, 4, '/static/images/twix.jpg', 'Barrita de caramelo y galleta'),
                ('D1', 'Chocolate', 2.5, 3, '/static/images/chocolate.jpg', 'Tableta de chocolate'),
                ('D2', 'Chips', 1.5, 0, '/static/images/chips.jpg', 'Patatas fritas'),
                ('E1', 'Galletas', 1.2, 0, '/static/images/galletas.jpg', 'Paquete de galletas'),
                ('E2', 'Chicles', 0.5, 10, '/static/images/chicles.jpg', 'Chicles de menta'),
                ('F1', 'Agua con Gas', 1.0, 5, '/static/images/agua_con_gas.jpg', 'Agua mineral con gas'),
                ('F2', 'Fanta', 1.5, 0, '/static/images/fanta.jpg', 'Refresco de naranja'),
                ('G1', 'Red Bull', 2.0, 3, '/static/images/redbull.jpg', 'Bebida energética'),
                ('G2', 'Sprite', 1.5, 7, '/static/images/sprite.jpg', 'Refresco de lima-limón')
            ]
            
            for door_id, name, price, stock, image, description in sample_products:
                cursor.execute('''
                    INSERT INTO products (door_id, name, price, stock, image_url, description, active)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                ''', (door_id, name, price, stock, image, description))
            
            conn.commit()
            conn.close()
            
            logger.info("Datos de ejemplo insertados correctamente")
            
        except Exception as e:
            logger.error(f"Error al insertar datos de ejemplo: {e}")
    
    # Métodos para productos
    def get_product_by_door(self, door_id: str) -> Optional[Dict]:
        """Obtener producto por ID de puerta"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, price, stock, door_id, image_url, description, active, min_stock, max_stock
                FROM products WHERE door_id = ? AND active = 1
            ''', (door_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'name': result[1],
                    'price': result[2],
                    'stock': result[3],
                    'door_id': result[4],
                    'image_url': result[5],
                    'description': result[6],
                    'active': result[7],
                    'min_stock': result[8],
                    'max_stock': result[9]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error al obtener producto para puerta {door_id}: {e}")
            return None
    
    def get_all_products(self) -> List[Dict]:
        """Obtener todos los productos activos"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, price, stock, door_id, image_url, description, active, min_stock, max_stock
                FROM products WHERE active = 1 ORDER BY door_id
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            products = []
            for result in results:
                products.append({
                    'id': result[0],
                    'name': result[1],
                    'price': result[2],
                    'stock': result[3],
                    'door_id': result[4],
                    'image_url': result[5],
                    'description': result[6],
                    'active': result[7],
                    'min_stock': result[8],
                    'max_stock': result[9]
                })
            
            return products
            
        except Exception as e:
            logger.error(f"Error al obtener productos: {e}")
            return []
    
    def update_product(self, door_id: str, **kwargs) -> bool:
        """Actualizar producto"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Construir query dinámicamente
            updates = []
            values = []
            
            allowed_fields = ['name', 'price', 'stock', 'image_url', 'description', 'active', 'min_stock', 'max_stock']
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    updates.append(f"{field} = ?")
                    values.append(value)
            
            if not updates:
                return False
            
            values.append(door_id)
            updates.append("updated_at = CURRENT_TIMESTAMP")
            
            query = f"UPDATE products SET {', '.join(updates)} WHERE door_id = ?"
            cursor.execute(query, values)
            
            conn.commit()
            conn.close()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error al actualizar producto {door_id}: {e}")
            return False
    
    def decrease_stock(self, door_id: str, quantity: int = 1) -> bool:
        """Decrementar stock de producto"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE products 
                SET stock = stock - ?, updated_at = CURRENT_TIMESTAMP
                WHERE door_id = ? AND stock >= ?
            ''', (quantity, door_id, quantity))
            
            conn.commit()
            conn.close()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error al decrementar stock de {door_id}: {e}")
            return False

    # Métodos para ventas
    def create_sale(self, door_id: str, payment_method: str, amount: float, 
                    product_id: int = None, payment_id: str = None) -> int:
        """Crear una nueva venta"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sales (product_id, door_id, payment_method, amount, status, payment_id, quantity)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (product_id, door_id, payment_method, amount, 'pending', payment_id, 1))
            
            sale_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return sale_id
            
        except Exception as e:
            logger.error(f"Error al crear venta: {e}")
            return None
    
    def update_sale_status(self, sale_id: int, status: str, dispensed: bool = False) -> bool:
        """Actualizar estado de venta"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if dispensed:
                cursor.execute('''
                    UPDATE sales 
                    SET status = ?, dispensed = ?, dispensed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, dispensed, sale_id))
            else:
                cursor.execute('''
                    UPDATE sales 
                    SET status = ?
                    WHERE id = ?
                ''', (status, sale_id))
            
            conn.commit()
            conn.close()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error al actualizar venta {sale_id}: {e}")
            return False
    
    def get_sales_by_date(self, date: str = None) -> List[Dict]:
        """Obtener ventas por fecha"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if date:
                cursor.execute('''
                    SELECT s.*, p.name as product_name
                    FROM sales s
                    LEFT JOIN products p ON s.product_id = p.id
                    WHERE DATE(s.created_at) = ?
                    ORDER BY s.created_at DESC
                ''', (date,))
            else:
                cursor.execute('''
                    SELECT s.*, p.name as product_name
                    FROM sales s
                    LEFT JOIN products p ON s.product_id = p.id
                    WHERE DATE(s.created_at) = DATE('now')
                    ORDER BY s.created_at DESC
                ''')
            
            results = cursor.fetchall()
            conn.close()
            
            sales = []
            for result in results:
                sales.append({
                    'id': result[0],
                    'product_id': result[1],
                    'door_id': result[2],
                    'payment_method': result[3],
                    'amount': result[4],
                    'status': result[5],
                    'payment_id': result[6],
                    'quantity': result[7],
                    'dispensed': result[8],
                    'dispensed_at': result[9],
                    'created_at': result[10],
                    'product_name': result[11] if len(result) > 11 else None
                })
            
            return sales
            
        except Exception as e:
            logger.error(f"Error al obtener ventas: {e}")
            return []
    
    # Métodos para reposición
    def create_restock(self, door_id: str, quantity_added: int, 
                      operator: str = None, notes: str = None) -> bool:
        """Registrar reposición"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Obtener stock actual
            cursor.execute('SELECT id, stock FROM products WHERE door_id = ?', (door_id,))
            result = cursor.fetchone()
            
            if not result:
                return False
            
            product_id, current_stock = result
            new_stock = current_stock + quantity_added
            
            # Registrar reposición
            cursor.execute('''
                INSERT INTO restocks (product_id, door_id, quantity_added, previous_stock, new_stock, operator, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (product_id, door_id, quantity_added, current_stock, new_stock, operator, notes))
            
            # Actualizar stock
            cursor.execute('''
                UPDATE products 
                SET stock = ?, updated_at = CURRENT_TIMESTAMP
                WHERE door_id = ?
            ''', (new_stock, door_id))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error al registrar reposición: {e}")
            return False
    
    # Métodos para mantenimiento de puertas
    def log_door_maintenance(self, door_id: str, action: str, status: str = None, 
                           notes: str = None, operator: str = None) -> bool:
        """Registrar mantenimiento de puerta"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO door_maintenance (door_id, action, status, notes, operator)
                VALUES (?, ?, ?, ?, ?)
            ''', (door_id, action, status, notes, operator))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error al registrar mantenimiento: {e}")
            return False
    
    # Métodos para logs del sistema
    def log_system_event(self, level: str, message: str, module: str = None, door_id: str = None) -> bool:
        """Registrar evento del sistema"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_logs (level, message, module, door_id)
                VALUES (?, ?, ?, ?)
            ''', (level, message, module, door_id))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error al registrar log del sistema: {e}")
            return False


# Instancia global del manejador de base de datos
db_manager = DatabaseManager()
