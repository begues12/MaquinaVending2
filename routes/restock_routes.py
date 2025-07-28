"""
Rutas relacionadas con modo reposición y administración
"""
import logging
from flask import Blueprint, request, jsonify
from controllers.restock_controller import restock_controller
from database import db_manager
from config import Config

# Crear blueprint
restock_bp = Blueprint('restock', __name__)
logger = logging.getLogger(__name__)

@restock_bp.route('/api/restock/click', methods=['POST'])
def process_screen_click():
    """Procesar clic en pantalla para activación de modo restock"""
    try:
        result = restock_controller.process_screen_click()
        return jsonify({'success': True, **result})
    except Exception as e:
        logger.error(f"Error al procesar clic de activación: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@restock_bp.route('/api/restock/click/status', methods=['GET'])
def get_click_activation_status():
    """Obtener estado del sistema de activación por clics"""
    try:
        status = restock_controller.get_click_activation_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        logger.error(f"Error al obtener estado de activación por clics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@restock_bp.route('/api/restock/sequence', methods=['POST'])
def check_secret_sequence():
    """Verificar secuencia secreta para acceso a modo reposición"""
    data    = request.get_json()
    door_id = data.get('door_id')
    
    if not door_id:
        return jsonify({'success': False, 'error': 'door_id requerido'}), 400
    
    try:
        result = restock_controller.process_door_selection(door_id)
        return jsonify({'success': True, **result})
    except Exception as e:
        logger.error(f"Error al procesar secuencia secreta: {e}")
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500

@restock_bp.route('/api/restock/sequence/status', methods=['GET'])
def get_sequence_status():
    """Obtener estado de la secuencia secreta"""
    try:
        status = restock_controller.get_sequence_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        logger.error(f"Error al obtener estado de secuencia: {e}")
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500

@restock_bp.route('/api/restock/mode', methods=['GET'])
def get_restock_mode():
    """Obtener estado del modo reposición"""
    status = restock_controller.get_restock_status()
    return jsonify({'success': True, 'restock_mode': status})

@restock_bp.route('/api/restock/toggle', methods=['POST'])
def toggle_restock_mode():
    """Alternar modo reposición"""
    active = restock_controller.toggle_restock_mode()
    return jsonify({
        'success': True, 
        'restock_mode': active,
        'message': 'Modo reposición activado' if active else 'Modo reposición desactivado'
    })

@restock_bp.route('/api/restock/simulate', methods=['POST'])
def simulate_restock_button():
    """Simular presión del botón de reposición (para Windows)"""
    active = restock_controller.simulate_button_press()
    return jsonify({
        'success': True, 
        'restock_mode': active,
        'message': 'Botón de reposición simulado'
    })

@restock_bp.route('/api/restock/button/check', methods=['GET'])
def check_physical_button():
    """Verificar estado del botón físico de restock (pin 16)"""
    try:
        button_pressed = restock_controller.check_physical_button()
        button_handled = False
        
        # Si el botón está presionado, manejar la presión
        if button_pressed:
            button_handled = restock_controller.handle_button_press()
        
        return jsonify({
            'success': True,
            'button_pressed': button_pressed,
            'button_handled': button_handled,
            'redirect_requested': restock_controller.is_redirect_requested()['redirect_requested']
        })
    except Exception as e:
        logger.error(f"Error verificando botón físico de restock: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@restock_bp.route('/api/restock/redirect-status', methods=['GET'])
def get_restock_redirect_status():
    """Verificar si se ha solicitado redirección al panel de restock"""
    redirect_info = restock_controller.is_redirect_requested()
    return jsonify({
        'success': True,
        'redirect_requested': redirect_info['redirect_requested'],
        'redirect_timestamp': redirect_info['redirect_timestamp']
    })

@restock_bp.route('/api/restock/clear-redirect', methods=['POST'])
def clear_restock_redirect():
    """Limpiar solicitud de redirección al panel de restock"""
    success = restock_controller.clear_redirect_request()
    return jsonify({
        'success': success,
        'message': 'Solicitud de redirección limpiada' if success else 'Error al limpiar redirección'
    })

@restock_bp.route('/api/restock/door/<door_id>', methods=['POST'])
def restock_door_endpoint(door_id):
    """Reabastecer una puerta (solo en modo reposición)"""
    if not restock_controller.is_restock_mode_active():
        return jsonify({'success': False, 'error': 'Modo reposición no activo'}), 403
    
    data        = request.get_json()
    quantity    = data.get('quantity', 1) if data else 1
    operator    = data.get('operator', 'admin') if data else 'admin'
    notes       = data.get('notes', '') if data else ''
    
    try:
        success = restock_controller.restock_door(door_id, quantity, operator, notes)
        if success:
            # Obtener información actualizada
            product = db_manager.get_product_by_door(door_id)
            return jsonify({
                'success'   : True,
                'message'   : f'Puerta {door_id} reabastecida con {quantity} unidades',
                'new_stock' : product['stock'] if product else 0
            })
        else:
            return jsonify({'success': False, 'error': 'Error al reabastecer'}), 500
            
    except Exception as e:
        logger.error(f"Error al reabastecer puerta {door_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@restock_bp.route('/api/restock/product/<door_id>', methods=['PUT'])
def update_product_in_door(door_id):
    """Actualizar producto en una puerta (solo en modo reposición)"""
    if not restock_controller.is_restock_mode_active():
        return jsonify({'success': False, 'error': 'Modo reposición no activo'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Datos requeridos'}), 400
    
    try:
        if restock_controller.update_product_in_door(door_id, data):
            return jsonify({
                'success'   : True,
                'message'   : f'Producto en puerta {door_id} actualizado'
            })
        else:
            return jsonify({'success': False, 'error': 'Error al actualizar producto'}), 500
            
    except Exception as e:
        logger.error(f"Error al actualizar producto en puerta {door_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@restock_bp.route('/api/test/gpio-button', methods=['POST'])
def test_gpio_button():
    """Simular presión del botón GPIO Pin 16 (solo en modo desarrollo)"""
    try:
        # Solo permitir en modo desarrollo
        if Config.FLASK_ENV != 'development':
            return jsonify({'success': False, 'error': 'Solo disponible en modo desarrollo'}), 403
        
        # Simular la presión del botón GPIO Pin 16
        restock_controller.simulate_button_press()
        logger.info("Botón GPIO Pin 16 simulado desde interfaz de desarrollo")
        
        return jsonify({
            'success': True,
            'message': 'Botón GPIO Pin 16 simulado correctamente'
        })
        
    except Exception as e:
        logger.error(f"Error simulando botón GPIO Pin 16: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
