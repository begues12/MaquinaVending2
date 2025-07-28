"""
Aplicación Flask principal para la máquina expendedora
Aplicación modular con blueprints organizados por funcionalidad
Optimizada para Raspberry Pi con Flask puro
"""
import logging
import time
import random
import string
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from config import Config
from database import db_manager
from machine_config import config_manager
from controllers.restock_controller import restock_controller

# Importar blueprints
from routes.payment_routes import payment_bp
from routes.hardware_routes import hardware_bp
from routes.restock_routes import restock_bp
from routes.system_routes import system_bp
from routes.sales_routes import sales_bp

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

# Registrar blueprints
app.register_blueprint(payment_bp)
app.register_blueprint(hardware_bp)
app.register_blueprint(restock_bp)
app.register_blueprint(system_bp)
app.register_blueprint(sales_bp)

# Rutas principales de la aplicación
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

# Ruta principal de compra (legacy - mantener para compatibilidad)
@app.route('/api/purchase', methods=['POST'])
def process_contactless():
    """Peticion para procesar una compra - Ruta legacy redirigida al nuevo sistema"""
    try:
        data = request.get_json()
        if not data or 'door_id' not in data:
            return jsonify({'success': False, 'error': 'Datos de compra inválidos'}), 400
        
        door_id = data['door_id']
        product = db_manager.get_product_by_door(door_id)

        if not product:
            return jsonify({'success': False, 'error': 'Producto no encontrado'}), 404

        if product['stock'] <= 0:
            return jsonify({'success': False, 'error': 'Producto sin stock'}), 400

        # Redirigir al nuevo sistema de pagos modular
        logger.info(f"Ruta legacy /api/purchase redirigida a nuevo sistema para puerta {door_id}")
        
        # Usar importación local para evitar circular imports
        from routes.payment_routes import tpv_controller
        amount = product['price']
        
        # Usar el nuevo flujo de dos pasos
        response = tpv_controller.init_payment(amount, door_id)
        
        if response['success']:
            return jsonify({
                'success': True,
                'status': 'payment_initiated',
                'payment_id': response['payment_id'],
                'amount': amount,
                'door_id': door_id,
                'message': 'Pago iniciado - usar /api/check_payment_status para seguimiento',
                'legacy_redirect': True
            })
        else:
            return jsonify({
                'success': False,
                'error': response.get('error', 'Error iniciando pago'),
                'legacy_redirect': True
            })
    
    except Exception as e:
        logger.error(f"Error al procesar compra legacy: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Función para iniciar la aplicación
def start_app():
    """Iniciar la aplicación Flask para Raspberry Pi"""
    try:
        logger.info("Iniciando Máquina Expendedora v2.0")
        logger.info(f"Plataforma: raspberry")
        logger.info(f"GPIO habilitado: {Config.GPIO_ENABLED}")
        
        # Inicializar base de datos
        db_manager.init_db()
        
        # Cargar configuración de máquina
        config_manager.load_config()
        
        logger.info("Iniciando servidor Flask (Raspberry Pi)")
        
        # Iniciar servidor Flask
        app.run(
            host='0.0.0.0',  # Escuchar en todas las interfaces para Raspberry Pi
            port=5000,
            debug=Config.FLASK_ENV == 'development',
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"Error al iniciar la aplicación: {e}")
        raise
    finally:
        logger.info("Aplicación cerrada")

if __name__ == '__main__':
    start_app()
