#!/usr/bin/env python3
"""
Script para poblar la base de datos con productos de ejemplo
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db_manager

def populate_sample_products():
    """Crear productos de ejemplo para las puertas"""
    
    sample_products = [
        {
            'name': 'Rosas Rojas (3 unidades)',
            'price': 15.50,
            'stock': 5,
            'door_id': 'A1',
            'description': 'Hermosas rosas rojas frescas, perfectas para regalar',
            'min_stock': 1,
            'max_stock': 10
        },
        {
            'name': 'Tulipanes Amarillos (5 unidades)',
            'price': 12.00,
            'stock': 8,
            'door_id': 'A2',
            'description': 'Tulipanes amarillos brillantes, símbolo de amistad',
            'min_stock': 2,
            'max_stock': 15
        },
        {
            'name': 'Girasoles (2 unidades)',
            'price': 8.75,
            'stock': 6,
            'door_id': 'B1',
            'description': 'Girasoles grandes y radiantes para alegrar cualquier día',
            'min_stock': 1,
            'max_stock': 8
        },
        {
            'name': 'Margaritas Blancas (6 unidades)',
            'price': 10.25,
            'stock': 4,
            'door_id': 'B2',
            'description': 'Margaritas blancas delicadas, perfectas para bouquets',
            'min_stock': 1,
            'max_stock': 10
        },
        {
            'name': 'Lirios Blancos (3 unidades)',
            'price': 18.50,
            'stock': 3,
            'door_id': 'C1',
            'description': 'Elegantes lirios blancos para ocasiones especiales',
            'min_stock': 1,
            'max_stock': 6
        },
        {
            'name': 'Claveles Rosa (4 unidades)',
            'price': 7.25,
            'stock': 7,
            'door_id': 'C2',
            'description': 'Claveles rosa suaves y fragantes',
            'min_stock': 2,
            'max_stock': 12
        }
    ]
    
    print("Poblando base de datos con productos de ejemplo...")
    
    for product in sample_products:
        try:
            existing = db_manager.get_product_by_door(product['door_id'])
            if existing:
                print(f"Actualizando producto existente en puerta {product['door_id']}: {product['name']}")
                # Remove door_id from the update data
                update_data = {k: v for k, v in product.items() if k != 'door_id'}
                db_manager.update_product(product['door_id'], **update_data)
            else:
                print(f"Creando nuevo producto en puerta {product['door_id']}: {product['name']}")
                db_manager.create_product(product)
        except Exception as e:
            print(f"Error al crear/actualizar producto {product['door_id']}: {e}")
    
    print("\n¡Base de datos poblada exitosamente!")
    
    # Mostrar resumen
    print("\nProductos creados:")
    for door_id in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
        product = db_manager.get_product_by_door(door_id)
        if product:
            print(f"  {door_id}: {product['name']} - €{product['price']:.2f} (Stock: {product['stock']})")
        else:
            print(f"  {door_id}: Sin producto")

if __name__ == '__main__':
    populate_sample_products()
