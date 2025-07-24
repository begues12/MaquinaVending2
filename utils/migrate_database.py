"""
Script de migración para actualizar la base de datos
Migra de la estructura antigua a la nueva con separación de puertas y productos
"""
import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Migrar base de datos a la nueva estructura"""
    db_path = "vending_machine.db"
    
    if not Path(db_path).exists():
        logger.info("No hay base de datos existente, se creará nueva")
        return True
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si ya existe la columna door_id
        cursor.execute("PRAGMA table_info(products)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'door_id' in columns:
            logger.info("La base de datos ya está migrada")
            conn.close()
            return True
        
        logger.info("Iniciando migración de base de datos...")
        
        # 1. Hacer backup de datos existentes
        cursor.execute("SELECT * FROM products")
        old_products = cursor.fetchall()
        
        logger.info(f"Respaldando {len(old_products)} productos existentes")
        
        # 2. Renombrar tabla antigua
        cursor.execute("ALTER TABLE products RENAME TO products_old")
        
        # 3. Crear nueva estructura de tablas
        cursor.execute('''
            CREATE TABLE products (
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
        
        # 4. Migrar datos existentes
        # Mapear slots antiguos a door_ids nuevos
        slot_to_door = {
            'slot_1': 'A1',
            'slot_2': 'A2', 
            'slot_3': 'B1',
            'slot_4': 'B2'
        }
        
        # Insertar productos migrados
        for old_product in old_products:
            # old_product: (id, name, price, stock, slot, image_url, description, active, created_at, updated_at)
            old_slot = old_product[4]
            door_id = slot_to_door.get(old_slot, 'A1')  # Default a A1 si no encuentra mapping
            
            cursor.execute('''
                INSERT INTO products (name, price, stock, door_id, image_url, description, active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                old_product[1],  # name
                old_product[2],  # price
                old_product[3],  # stock
                door_id,         # door_id (nuevo)
                old_product[5],  # image_url
                old_product[6],  # description
                old_product[7],  # active
                old_product[8],  # created_at
                old_product[9]   # updated_at
            ))
        
        # 5. Migrar transacciones a sales
        cursor.execute("SELECT * FROM transactions")
        old_transactions = cursor.fetchall()
        
        logger.info(f"Migrando {len(old_transactions)} transacciones")
        
        for transaction in old_transactions:
            # transaction: (id, product_id, payment_method, amount, status, payment_id, created_at)
            # Obtener door_id del producto
            cursor.execute("SELECT door_id FROM products WHERE id = ?", (transaction[1],))
            door_result = cursor.fetchone()
            door_id = door_result[0] if door_result else 'A1'
            
            cursor.execute('''
                INSERT INTO sales (product_id, door_id, payment_method, amount, status, payment_id, quantity, dispensed, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                transaction[1],  # product_id
                door_id,         # door_id
                transaction[2],  # payment_method
                transaction[3],  # amount
                transaction[4],  # status
                transaction[5],  # payment_id
                1,               # quantity (default)
                transaction[4] == 'completed',  # dispensed
                transaction[6]   # created_at
            ))
        
        # 6. Añadir productos para las puertas restantes (G1, G2, etc.)
        new_products = [
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
        
        for door_id, name, price, stock, image, description in new_products:
            # Verificar si ya existe
            cursor.execute("SELECT id FROM products WHERE door_id = ?", (door_id,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO products (door_id, name, price, stock, image_url, description, active)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                ''', (door_id, name, price, stock, image, description))
        
        # 7. Actualizar system_logs para incluir door_id
        cursor.execute("PRAGMA table_info(system_logs)")
        log_columns = [col[1] for col in cursor.fetchall()]
        
        if 'door_id' not in log_columns:
            cursor.execute("ALTER TABLE system_logs ADD COLUMN door_id TEXT")
        
        # 8. Eliminar tabla antigua
        cursor.execute("DROP TABLE products_old")
        cursor.execute("DROP TABLE IF EXISTS transactions")  # Ya migrada a sales
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Migración completada exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error durante la migración: {e}")
        return False

if __name__ == "__main__":
    migrate_database()
