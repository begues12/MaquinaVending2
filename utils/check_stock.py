#!/usr/bin/env python3
"""Script para verificar el stock actual de productos"""

from database import DatabaseManager

def check_stock_status():
    """Verificar el estado actual del stock y ventas"""
    db = DatabaseManager()
    
    print("=== ESTADO ACTUAL DEL STOCK ===")
    print("Door ID | Producto      | Precio | Stock | Estado")
    print("--------|---------------|--------|-------|--------")
    
    # Obtener todos los productos
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT door_id, name, price, stock, active, min_stock
        FROM products
        ORDER BY door_id
    ''')
    
    for row in cursor.fetchall():
        door_id, name, price, stock, active, min_stock = row
        
        # Determinar estado
        estado = "Activo"
        if not active:
            estado = "Inactivo"
        elif stock <= 0:
            estado = "Sin stock"
        elif stock <= min_stock:
            estado = "Stock bajo"
            
        print(f"{door_id:7} | {name:13} | €{price:5.2f} | {stock:5} | {estado}")
    
    conn.close()
    
    # Mostrar ventas recientes
    print("\n=== VENTAS RECIENTES ===")
    cursor = db.get_connection().cursor()
    cursor.execute('''
        SELECT s.created_at, s.door_id, p.name, s.amount, s.status
        FROM sales s
        JOIN products p ON s.product_id = p.id
        ORDER BY s.created_at DESC
        LIMIT 10
    ''')
    
    print("Fecha/Hora          | Door | Producto     | Importe | Estado")
    print("--------------------|------|--------------|---------|----------")
    
    for row in cursor.fetchall():
        created_at, door_id, name, amount, status = row
        print(f"{created_at:19} | {door_id:4} | {name:12} | €{amount:6.2f} | {status}")
    
    db.get_connection().close()

if __name__ == "__main__":
    check_stock_status()
