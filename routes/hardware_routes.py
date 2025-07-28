"""
Rutas relacionadas con hardware y control de puertas
"""
import logging
from flask import Blueprint, request, jsonify
from controllers.hardware_controller import hardware_controller
from controllers.restock_controller import restock_controller
from machine_config import config_manager

# Crear blueprint
hardware_bp = Blueprint('hardware', __name__)
logger = logging.getLogger(__name__)

@hardware_bp.route('/api/hardware/door/<door_id>/open', methods=['POST'])
def open_door_hardware(door_id):
    """Abrir puerta usando el sistema de hardware (relé)"""
    try:
        # Abrir puerta
        success = hardware_controller.open_door(door_id)
        
        if success:
            logger.info(f"Puerta {door_id} abierta via hardware")
            return jsonify({
                'success': True,
                'message': f'Puerta {door_id} abierta',
                'door_id': door_id
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Error al abrir puerta {door_id}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error abriendo puerta {door_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@hardware_bp.route('/api/hardware/door/<door_id>/close', methods=['POST'])
def close_door_hardware(door_id):
    """Cerrar puerta usando el sistema de hardware (relé)"""
    try:
        # Cerrar puerta
        success = hardware_controller.close_door(door_id)
        
        if success:
            logger.info(f"Puerta {door_id} cerrada via hardware")
            return jsonify({
                'success': True,
                'message': f'Puerta {door_id} cerrada',
                'door_id': door_id
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Error al cerrar puerta {door_id}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error cerrando puerta {door_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@hardware_bp.route('/api/hardware/door/<door_id>/state', methods=['GET'])
def get_door_hardware_state(door_id):
    """Obtener estado de hardware de una puerta"""
    try:
        state = hardware_controller.get_door_state(door_id)
        return jsonify({
            'success': True,
            'door_state': state
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de puerta {door_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@hardware_bp.route('/api/hardware/doors/state', methods=['GET'])
def get_all_doors_hardware_state():
    """Obtener estado de hardware de todas las puertas"""
    try:
        states = hardware_controller.get_all_doors_state()
        return jsonify({
            'success': True,
            'doors_state': states
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de puertas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@hardware_bp.route('/api/hardware/door/<door_id>/test', methods=['POST'])
def test_door_hardware(door_id):
    """Probar funcionamiento de una puerta (relé y sensor)"""
    try:
        # Verificar modo restock
        restock_status = restock_controller.get_restock_status()
        if not restock_status['active']:
            return jsonify({
                'success': False,
                'error': 'Acceso denegado - modo restock requerido'
            }), 403
        
        success = hardware_controller.test_door(door_id)
        
        return jsonify({
            'success': success,
            'message': f'Prueba de puerta {door_id} {"exitosa" if success else "fallida"}',
            'door_id': door_id
        })
        
    except Exception as e:
        logger.error(f"Error probando puerta {door_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@hardware_bp.route('/api/hardware/doors/test', methods=['POST'])
def test_all_doors_hardware():
    """Probar funcionamiento de todas las puertas"""
    try:
        # Verificar modo restock
        restock_status = restock_controller.get_restock_status()
        if not restock_status['active']:
            return jsonify({
                'success': False,
                'error': 'Acceso denegado - modo restock requerido'
            }), 403
        
        results = hardware_controller.test_all_doors()
        
        return jsonify({
            'success': True,
            'test_results': results,
            'total_doors': len(results),
            'successful_tests': sum(1 for result in results.values() if result)
        })
        
    except Exception as e:
        logger.error(f"Error probando puertas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@hardware_bp.route('/api/hardware/emergency-stop', methods=['POST'])
def emergency_stop_hardware():
    """Parada de emergencia - detener todos los relés"""
    try:
        hardware_controller.emergency_stop()
        
        logger.warning("Parada de emergencia ejecutada")
        return jsonify({
            'success': True,
            'message': 'Parada de emergencia ejecutada'
        })
        
    except Exception as e:
        logger.error(f"Error en parada de emergencia: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@hardware_bp.route('/api/hardware/restock-button/state', methods=['GET'])
def get_restock_button_state():
    """Obtener estado del botón de restock"""
    try:
        button_state = hardware_controller.get_restock_button_state()
        
        return jsonify({
            'success': True,
            'button_state': button_state
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado del botón de restock: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@hardware_bp.route('/api/hardware/restock-button/check', methods=['GET'])
def check_restock_button_pressed():
    """Verificar si el botón de restock está presionado"""
    try:
        is_pressed = hardware_controller.is_restock_button_pressed()
        
        return jsonify({
            'success': True,
            'is_pressed': is_pressed,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error verificando botón de restock: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Rutas para gestión de tiempos de apertura de puertas
@hardware_bp.route('/api/door/<door_id>/open-time', methods=['GET'])
def get_door_open_time(door_id):
    """Obtener el tiempo de apertura configurado para una puerta"""
    try:
        open_time = hardware_controller.get_door_open_time(door_id)
        
        return jsonify({
            'success': True,
            'door_id': door_id,
            'open_time': open_time
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo tiempo de apertura para {door_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@hardware_bp.route('/api/door/<door_id>/open-time', methods=['PUT'])
def set_door_open_time(door_id):
    """Configurar el tiempo de apertura para una puerta específica"""
    try:
        # Verificar modo restock
        restock_status = restock_controller.get_restock_status()
        if not restock_status['active']:
            return jsonify({
                'success': False,
                'error': 'Acceso denegado - modo restock requerido'
            }), 403
        
        data = request.get_json()
        if not data or 'open_time' not in data:
            return jsonify({
                'success': False,
                'error': 'Campo open_time requerido'
            }), 400
        
        open_time = float(data['open_time'])
        success = hardware_controller.set_door_open_time(door_id, open_time)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Tiempo de apertura configurado a {open_time}s para puerta {door_id}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Error configurando tiempo de apertura'
            }), 400
            
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Valor de tiempo inválido'
        }), 400
    except Exception as e:
        logger.error(f"Error configurando tiempo de apertura para {door_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@hardware_bp.route('/api/doors/open-times', methods=['GET'])
def get_all_door_open_times():
    """Obtener tiempos de apertura de todas las puertas"""
    try:
        door_times = {}
        for door_id in config_manager.get_door_ids():
            door_times[door_id] = hardware_controller.get_door_open_time(door_id)
        
        # También incluir configuración global
        config = config_manager.get_config()
        door_settings = config.get('machine', {}).get('door_settings', {})
        
        return jsonify({
            'success': True,
            'door_times': door_times,
            'global_settings': door_settings
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo tiempos de apertura: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@hardware_bp.route('/api/doors/open-times', methods=['PUT'])
def set_multiple_door_open_times():
    """Configurar tiempos de apertura para múltiples puertas"""
    try:
        # Verificar modo restock
        restock_status = restock_controller.get_restock_status()
        if not restock_status['active']:
            return jsonify({
                'success': False,
                'error': 'Acceso denegado - modo restock requerido'
            }), 403
        
        data = request.get_json()
        if not data or 'door_times' not in data:
            return jsonify({
                'success': False,
                'error': 'Campo door_times requerido'
            }), 400
        
        results = {}
        errors = []
        
        for door_id, open_time in data['door_times'].items():
            try:
                success = hardware_controller.set_door_open_time(door_id, float(open_time))
                results[door_id] = success
                if not success:
                    errors.append(f"Error configurando puerta {door_id}")
            except Exception as e:
                results[door_id] = False
                errors.append(f"Error en puerta {door_id}: {str(e)}")
        
        return jsonify({
            'success': len(errors) == 0,
            'results': results,
            'errors': errors
        })
        
    except Exception as e:
        logger.error(f"Error configurando múltiples tiempos de apertura: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@hardware_bp.route('/api/hardware/debug', methods=['GET'])
def debug_hardware():
    """Endpoint temporal para debuggear el estado de los relés"""
    try:
        # Obtener estado de los relés
        door_relays = hardware_controller.door_relays
        
        relays_info = {}
        for door_id, relay in door_relays.items():
            relays_info[door_id] = {
                'type': type(relay).__name__,
                'has_relay': relay is not None,
                'methods': [method for method in dir(relay) if not method.startswith('_')],
                'gpio_pin': getattr(relay, 'gpio_pin', 'unknown')
            }
        
        return jsonify({
            'success': True,
            'total_relays': len(door_relays),
            'initialized': hardware_controller.initialized,
            'relays': relays_info
        })
        
    except Exception as e:
        logger.error(f"Error en debug de hardware: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
