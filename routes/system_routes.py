"""
Rutas relacionadas con sistema, configuración y estado general
"""
import logging
from flask import Blueprint, request, jsonify
from config import Config
from database import db_manager
from controllers.payment_system import payment_processor
from controllers.hardware_controller import hardware_controller
from machine_config import config_manager

# Crear blueprint
system_bp = Blueprint('system', __name__)
logger = logging.getLogger(__name__)

@system_bp.route('/api/doors')
def get_doors():
    """API para obtener todas las puertas con productos"""
    return jsonify({'success': True, 'doors': config_manager.get_all_doors_with_products()})

@system_bp.route('/api/door/<door_id>')
def get_door(door_id):
    """API para obtener una puerta específica con producto"""
    door = config_manager.get_door_with_product(door_id)
    if door:
        return jsonify({'success': True, 'door': door})
    else:
        return jsonify({'success': False, 'error': 'Puerta no encontrada'}), 404

@system_bp.route('/api/products')
def get_all_products():
    """Obtener todos los productos"""
    try:
        products = db_manager.get_all_products()
        return jsonify({'success': True, 'products': products})
        
    except Exception as e:
        logger.error(f"Error al obtener productos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@system_bp.route('/api/config/development')
def get_development_config():
    """Obtener configuración de modo desarrollo"""
    return jsonify({
        'success': True,
        'development_mode': Config.FLASK_ENV == 'development',
        'debug_mode': Config.FLASK_DEBUG
    })

@system_bp.route('/api/machine/config', methods=['GET'])
def get_machine_config():
    """Obtener configuración completa de la máquina"""
    try:
        config = config_manager.get_config()
        return jsonify({
            'success': True,
            'config': config
        })
    except Exception as e:
        logger.error(f"Error al obtener configuración: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@system_bp.route('/api/machine/doors', methods=['GET'])
def get_doors_info():
    """Obtener información de todas las puertas"""
    try:
        doors_info = {}
        for door_id in config_manager.get_door_ids():
            doors_info[door_id] = config_manager.get_door(door_id)
        
        return jsonify({
            'success': True,
            'doors': doors_info,
            'total_doors': len(doors_info)
        })
    except Exception as e:
        logger.error(f"Error al obtener información de puertas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@system_bp.route('/api/machine/door/<door_id>', methods=['GET'])
def get_door_info(door_id):
    """Obtener información específica de una puerta"""
    try:
        door = config_manager.get_door(door_id)
        if door:
            return jsonify({
                'success': True,
                'door': door
            })
        else:
            return jsonify({'success': False, 'error': 'Puerta no encontrada'}), 404
    except Exception as e:
        logger.error(f"Error al obtener puerta {door_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@system_bp.route('/api/machine/status', methods=['GET'])
def get_machine_status():
    """Obtener estado general de la máquina"""
    try:
        config = config_manager.get_config()
        doors_summary = {}
        available_count = 0
        
        for door_id in config_manager.get_door_ids():
            door = config_manager.get_door(door_id)
            doors_summary[door_id] = {
                'status': door['status'],
                'stock': door['product']['stock'],
                'product_name': door['product']['name']
            }
            if door['status'] == 'available' and door['product']['stock'] > 0:
                available_count += 1
        
        return jsonify({
            'success': True,
            'system_status': 'maintenance' if config.get('maintenance_mode', False) else 'operational',
            'doors_summary': doors_summary,
            'available_doors': available_count,
            'total_doors': len(doors_summary),
            'display_config': config.get('display', {}),
            'payment_methods': config.get('payment_methods', {}),
            'last_updated': config.get('last_updated', 'unknown')
        })
    except Exception as e:
        logger.error(f"Error al obtener estado de máquina: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@system_bp.route('/api/system/status')
def system_status():
    """Estado del sistema"""
    gpio_status = hardware_controller.get_pins_status()
    payment_methods = payment_processor.get_payment_methods()
    
    return jsonify({
        'success': True,
        'gpio': gpio_status,
        'payments': payment_methods,
        'platform': Config.PLATFORM
    })

@system_bp.route('/api/system/transactions')
def get_transactions():
    """Obtener transacciones recientes"""
    transactions = db_manager.get_transactions(50)
    return jsonify({'success': True, 'transactions': transactions})
