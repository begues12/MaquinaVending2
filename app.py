"""
Aplicación Flask principal para la máquina expendedora
"""
import logging
import webview
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from config import Config
from database import db_manager
from controllers.payment_system import payment_processor
from controllers.gpio_controller import gpio_controller
from machine_config import config_manager
from controllers.tpv_controller import TPVController
from controllers.restock_controller import restock_controller
from controllers.sales_history_controller import sales_history_controller
from controllers.hardware_controller import hardware_controller

# Inicializar controlador TPV
tpv_controller = TPVController()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Rutas principales
@app.route('/')
def index():
    """Página principal de la máquina expendedora"""
    machine_config  = config_manager.config
    doors           = config_manager.get_all_doors_with_products()
    restock_status  = restock_controller.get_restock_status()
    
    return render_template('index.html', 
                         config=machine_config,
                         doors=doors,
                         restock_mode=restock_status['active'])

@app.route('/restock')
def restock_panel():
    """Panel de administración para reposición"""
    return render_template('restock.html', config=config_manager.config)

@app.route('/api/doors')
def get_doors():
    """API para obtener todas las puertas con productos"""
    return jsonify({'success': True, 'doors': config_manager.get_all_doors_with_products()})

@app.route('/api/door/<door_id>')
def get_door(door_id):
    """API para obtener una puerta específica con producto"""
    door = config_manager.get_door_with_product(door_id)
    if door:
        return jsonify({'success': True, 'door': door})
    else:
        return jsonify({'success': False, 'error': 'Puerta no encontrada'}), 404

# Ruta principal de compra
@app.route('/api/purchase', methods=['POST'])
def process_purchase():
    """Procesar compra completa con nueva configuración"""
    data = request.get_json()
    
    if not data or 'door_id' not in data:
        return jsonify({'error': 'ID de puerta requerido'}), 400
    
    door_id         = data['door_id']
    payment_method  = data.get('payment_method', 'contactless')

    try:
        # Verificar que la puerta existe y obtener producto
        door_config = config_manager.get_door(door_id)
        if not door_config:
            return jsonify({'success': False, 'error': 'Puerta no encontrada'}), 404
        
        product = db_manager.get_product_by_door(door_id)
        if not product:
            return jsonify({'success': False, 'error': 'No hay producto configurado en esta puerta'}), 404
        
        if product['stock'] <= 0:
            return jsonify({'success': False, 'error': 'Sin stock'}), 400
        
        if not product['active']:
            return jsonify({'success': False, 'error': 'Producto no disponible'}), 400
        
        amount = product['price']
        
        # Procesar pago según método
        payment_result = None
        if payment_method == 'contactless':
            # Usar TPV para pago contactless
            payment_result = tpv_controller.process_contactless_payment(amount)
        else:
            return jsonify({'success': False, 'error': 'Método de pago no soportado'}), 400
        
        if not payment_result or not payment_result.get('success'):
            return jsonify({
                'success': False, 
                'error': 'Error en el pago',
                'details': payment_result.get('error', 'Error desconocido')
            }), 400
        
        # Crear registro de venta
        sale_id = db_manager.create_sale(
            door_id         = door_id,
            product_id      = product['id'],
            payment_method  = payment_method,
            amount          = amount,
            payment_id      = payment_result.get('payment_id')
        )
        
        if not sale_id:
            return jsonify({'success': False, 'error': 'Error al registrar venta'}), 500
        
        # Dispensar producto usando el nuevo sistema de hardware
        dispense_result = hardware_controller.open_door(door_id)
        
        if dispense_result:
            # Actualizar stock y estado de venta
            db_manager.decrease_stock(door_id, 1)
            db_manager.update_sale_status(sale_id, 'completed', dispensed=True)
            
            # Log del evento
            db_manager.log_system_event(
                'INFO',
                f'Venta completada: {product["name"]} - €{amount}',
                'purchase_controller',
                door_id
            )
            
            return jsonify({
                'success'       : True,
                'message'       : 'Compra realizada con éxito',
                'sale_id'       : sale_id,
                'product'       : product['name'],
                'amount'        : amount,
                'payment_method': payment_method
            })
        else:
            # Error al dispensar - revertir venta
            db_manager.update_sale_status(sale_id, 'failed')
            
            return jsonify({
                'success'   : False,
                'error'     : 'Error al dispensar producto. Contacte con soporte.',
                'sale_id'   : sale_id
            }), 500
            
    except Exception as e:
        logger.error(f"Error en proceso de compra: {e}")
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500

# Rutas para modo reposición
@app.route('/api/restock/click', methods=['POST'])
def process_screen_click():
    """Procesar clic en pantalla para activación de modo restock"""
    try:
        result = restock_controller.process_screen_click()
        return jsonify({'success': True, **result})
    except Exception as e:
        logger.error(f"Error al procesar clic de activación: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/restock/click/status', methods=['GET'])
def get_click_activation_status():
    """Obtener estado del sistema de activación por clics"""
    try:
        status = restock_controller.get_click_activation_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        logger.error(f"Error al obtener estado de activación por clics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/restock/sequence', methods=['POST'])
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

@app.route('/api/restock/sequence/status', methods=['GET'])
def get_sequence_status():
    """Obtener estado de la secuencia secreta"""
    try:
        status = restock_controller.get_sequence_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        logger.error(f"Error al obtener estado de secuencia: {e}")
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500

@app.route('/api/restock/mode', methods=['GET'])
def get_restock_mode():
    """Obtener estado del modo reposición"""
    status = restock_controller.get_restock_status()
    return jsonify({'success': True, 'restock_mode': status})

@app.route('/api/restock/toggle', methods=['POST'])
def toggle_restock_mode():
    """Alternar modo reposición"""
    active = restock_controller.toggle_restock_mode()
    return jsonify({
        'success': True, 
        'restock_mode': active,
        'message': 'Modo reposición activado' if active else 'Modo reposición desactivado'
    })

@app.route('/api/restock/simulate', methods=['POST'])
def simulate_restock_button():
    """Simular presión del botón de reposición (para Windows)"""
    active = restock_controller.simulate_button_press()
    return jsonify({
        'success': True, 
        'restock_mode': active,
        'message': 'Botón de reposición simulado'
    })

@app.route('/api/restock/redirect-status', methods=['GET'])
def get_restock_redirect_status():
    """Verificar si se ha solicitado redirección al panel de restock"""
    redirect_info = restock_controller.is_redirect_requested()
    return jsonify({
        'success': True,
        'redirect_requested': redirect_info['redirect_requested'],
        'redirect_timestamp': redirect_info['redirect_timestamp']
    })

@app.route('/api/restock/clear-redirect', methods=['POST'])
def clear_restock_redirect():
    """Limpiar solicitud de redirección al panel de restock"""
    success = restock_controller.clear_redirect_request()
    return jsonify({
        'success': success,
        'message': 'Solicitud de redirección limpiada' if success else 'Error al limpiar redirección'
    })

@app.route('/api/restock/door/<door_id>', methods=['POST'])
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

@app.route('/api/restock/product/<door_id>', methods=['PUT'])
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

# Rutas de testing y administración
@app.route('/api/test/dispense/<door_id>', methods=['POST'])
def test_dispense(door_id):
    """Dispensar producto directamente (para testing)"""
    try:
        door_config = config_manager.get_door(door_id)
        if not door_config:
            return jsonify({'success': False, 'error': 'Puerta no encontrada'}), 404
        
        # Activar GPIO para testing
        gpio_success = gpio_controller.dispense_product(door_config['gpio_pin'])
        
        if gpio_success:
            logger.info(f"Test dispensado - Puerta: {door_id}")
            return jsonify({
                'success'   : True, 
                'message'   : f'Test dispensado ejecutado para puerta {door_id}',
                'gpio_pin'  : door_config.get('gpio_pin')
            })
        else:
            return jsonify({'success': False, 'error': 'Error al activar GPIO'}), 500
            
    except Exception as e:
        logger.error(f"Error en test dispensado: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test/gpio-button', methods=['POST'])
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

@app.route('/api/config/development')
def get_development_config():
    """Obtener configuración de modo desarrollo"""
    return jsonify({
        'success': True,
        'development_mode': Config.FLASK_ENV == 'development',
        'debug_mode': Config.FLASK_DEBUG
    })

# Rutas de información y estadísticas
@app.route('/api/sales/today')
def get_today_sales():
    """Obtener ventas del día"""
    try:
        sales = db_manager.get_sales_by_date()
        total_amount = sum(sale['amount'] for sale in sales if sale['status'] == 'completed')
        
        return jsonify({
            'success'       : True,
            'sales'         : sales,
            'total_sales'   : len([s for s in sales if s['status'] == 'completed']),
            'total_amount'  : total_amount
        })
        
    except Exception as e:
        logger.error(f"Error al obtener ventas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products')
def get_all_products():
    """Obtener todos los productos"""
    try:
        products = db_manager.get_all_products()
        return jsonify({'success': True, 'products': products})
        
    except Exception as e:
        logger.error(f"Error al obtener productos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tpv/test', methods=['POST'])
def test_tpv():
    """Probar conexión con TPV"""
    try:
        result = tpv_controller.test_connection()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error al probar TPV: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tpv/status', methods=['GET'])
def get_tpv_status():
    """Obtener estado del TPV"""
    try:
        status = tpv_controller.get_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        logger.error(f"Error al obtener estado TPV: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Rutas de configuración y estado de máquina
@app.route('/api/machine/config', methods=['GET'])
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

@app.route('/api/machine/doors', methods=['GET'])
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

@app.route('/api/machine/door/<door_id>', methods=['GET'])
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

@app.route('/api/machine/status', methods=['GET'])
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

# Rutas de sistema
@app.route('/api/system/status')
def system_status():
    """Estado del sistema"""
    gpio_status = gpio_controller.get_pins_status()
    payment_methods = payment_processor.get_payment_methods()
    
    return jsonify({
        'success': True,
        'gpio': gpio_status,
        'payments': payment_methods,
        'platform': Config.PLATFORM
    })

@app.route('/api/system/transactions')
def get_transactions():
    """Obtener transacciones recientes"""
    transactions = db_manager.get_transactions(50)
    return jsonify({'success': True, 'transactions': transactions})

# Rutas para historial de ventas
@app.route('/api/sales/history')
def get_sales_history():
    """Obtener historial de ventas con filtros opcionales"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = int(request.args.get('limit', 100))
    
    try:
        sales = sales_history_controller.get_sales_history(start_date, end_date, limit)
        return jsonify({'success': True, 'sales': sales})
    except Exception as e:
        logger.error(f"Error al obtener historial de ventas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sales/summary')
def get_sales_summary():
    """Obtener resumen de ventas con estadísticas"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        summary = sales_history_controller.get_sales_summary(start_date, end_date)
        return jsonify({'success': True, 'summary': summary})
    except Exception as e:
        logger.error(f"Error al obtener resumen de ventas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sales/export/csv')
def export_sales_csv():
    """Exportar historial de ventas a CSV"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        filepath = sales_history_controller.export_sales_to_csv(start_date, end_date)
        return jsonify({
            'success': True, 
            'message': 'Archivo CSV generado exitosamente',
            'filepath': filepath
        })
    except Exception as e:
        logger.error(f"Error al exportar CSV: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sales/export/json')
def export_sales_json():
    """Exportar resumen de ventas a JSON"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        filepath = sales_history_controller.export_summary_to_json(start_date, end_date)
        return jsonify({
            'success': True, 
            'message': 'Archivo JSON generado exitosamente',
            'filepath': filepath
        })
    except Exception as e:
        logger.error(f"Error al exportar JSON: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/usb/detect')
def detect_usb():
    """Detectar unidades USB conectadas"""
    try:
        usb_drives = sales_history_controller.detect_usb_drives()
        return jsonify({
            'success': True,
            'usb_drives': usb_drives,
            'count': len(usb_drives)
        })
    except Exception as e:
        logger.error(f"Error al detectar USB: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sales/export/usb', methods=['POST'])
def export_to_usb():
    """Exportar historial de ventas a USB automáticamente"""
    data = request.get_json()
    start_date = data.get('start_date') if data else None
    end_date = data.get('end_date') if data else None
    
    try:
        result = sales_history_controller.auto_export_to_usb(start_date, end_date)
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al exportar a USB: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Funciones auxiliares para integración con nuevo sistema de configuración
# === RUTAS DE HARDWARE ===

@app.route('/api/hardware/door/<door_id>/open', methods=['POST'])
def open_door_hardware(door_id):
    """Abrir puerta usando el sistema de hardware (relé)"""
    try:
        # Verificar modo restock
        restock_status = restock_controller.get_restock_status()
        if not restock_status['active']:
            return jsonify({
                'success': False,
                'error': 'Acceso denegado - modo restock requerido'
            }), 403
        
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

@app.route('/api/hardware/door/<door_id>/state', methods=['GET'])
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

@app.route('/api/hardware/doors/state', methods=['GET'])
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

@app.route('/api/hardware/door/<door_id>/test', methods=['POST'])
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

@app.route('/api/hardware/doors/test', methods=['POST'])
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

@app.route('/api/hardware/emergency-stop', methods=['POST'])
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

# Rutas para gestión de tiempos de apertura de puertas
@app.route('/api/door/<door_id>/open-time', methods=['GET'])
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

@app.route('/api/door/<door_id>/open-time', methods=['PUT'])
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

@app.route('/api/doors/open-times', methods=['GET'])
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

@app.route('/api/doors/open-times', methods=['PUT'])
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

# Función de compra legacy mantenida para compatibilidad
def process_purchase_legacy(slot: str, payment_method: str, payment_id: str = None) -> dict:
    """Procesar una compra (función de compatibilidad con sistema anterior)"""
    try:
        # Convertir slot a door_id
        door_id = slot.replace('slot_', '') if slot.startswith('slot_') else slot
        
        # Usar el nuevo sistema de configuración
        result = config_manager.dispense_product(door_id)
        if result['success']:
            gpio_success = gpio_controller.dispense_product(f"slot_{door_id}")
            
            if gpio_success:
                # Registrar transacción en la base de datos para historial
                product_info = result['product']
                db_manager.add_transaction(
                    product_id=0,  # ID temporal para el nuevo sistema
                    quantity=1,
                    amount=product_info['price'],
                    payment_method=payment_method,
                    payment_reference=payment_id or 'N/A'
                )
                
                logger.info(f"Compra completada - Puerta: {door_id}, Método: {payment_method}")
                
                return {
                    'success': True,
                    'message': 'Producto dispensado correctamente',
                    'product': product_info,
                    'remaining_stock': result['remaining_stock']
                }
            else:
                # Revertir cambios en caso de error GPIO
                door = config_manager.get_door(door_id)
                config_manager.update_door_stock(door_id, door['product']['stock'])
                return {'success': False, 'error': 'Error en dispensado GPIO'}
        else:
            return {'success': False, 'error': result['error']}
            
    except Exception as e:
        logger.error(f"Error en process_purchase_legacy: {e}")
        return {'success': False, 'error': str(e)}

# Funciones auxiliares
def process_purchase(slot: str, payment_method: str, payment_id: str = None) -> dict:
    """Procesar una compra completa - MIGRADO AL NUEVO SISTEMA"""
    # Redirigir al nuevo sistema basado en configuración
    return process_purchase_legacy(slot, payment_method, payment_id)

# Función para iniciar la aplicación
def start_app():
    """Iniciar la aplicación con PyWebView"""
    try:
        # Configurar PyWebView
        webview.create_window(
            'Floradomicilio.com',
            app,
            width=Config.WINDOW_WIDTH,
            height=Config.WINDOW_HEIGHT,
            resizable=True,
            fullscreen=True
        )
        
        logger.info("Iniciando aplicación...")
        webview.start(debug=Config.FLASK_ENV == 'development')
        
    except Exception as e:
        logger.error(f"Error al iniciar la aplicación: {e}")
    finally:
        # Cleanup
        gpio_controller.cleanup()

if __name__ == '__main__':
    if Config.PLATFORM == 'windows':
        # En Windows, usar PyWebView
        start_app()
    else:
        # En Raspberry Pi, ejecutar Flask directamente
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.FLASK_ENV == 'development'
        )
