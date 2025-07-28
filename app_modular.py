"""
Aplicación Flask principal para la máquina expendedora
Aplicación modular con blueprints organizados por funcionalidad
"""
import logging
import time
import webview
import random
import string
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from config import Config
from database import db_manager
from controllers.payment_system import payment_processor
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
    """Peticion para procesar una compra"""
    # De momento devuelve siempre true
    try:
        data = request.get_json()
        if not data or 'door_id' not in data:
            return jsonify({'success': False, 'error': 'Datos de compra inválidos'}), 400
        
        door_id = data['door_id']
        product = db_manager.get_product_by_door(door_id)

        if not product:
            return jsonify({'success': False, 'error': 'Producto no encontrado'}), 404

        # Abre solicitud con el tpv
        amount = product['price']
        transaction_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        payment_id = payment_processor.create_payment(amount, transaction_id, 'contactless', door_id)
        if not payment_id:
            return jsonify({'success': False, 'error': 'Error al procesar el pago'}), 500
        
        # Simula el pago exitoso
        # Y espera respuesta de tarjeta acercada al tpv de momento simulado
        random_response = random.choice(['APPROVED', 'DECLINED'])
        
        # Usar importación local para evitar circular imports
        from routes.payment_routes import tpv_controller
        response = tpv_controller.process_contactless_payment(amount)
        
        if response['success']:
            status = response['status']
            
            if status == 'approved':
                # Procesar resultado exitoso
                logger.info(f"Pago aprobado para {product['name']} en puerta {door_id}")
            else:
                logger.warning(f"Pago rechazado para {product['name']} en puerta {door_id}")
    
    except Exception as e:
        logger.error(f"Error al procesar compra: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
            fullscreen=False,
            easy_drag=False,
            frameless=False
        )
        
        logger.info("Iniciando aplicación modular...")
        webview.start(debug=Config.FLASK_ENV == 'development')
        
    except Exception as e:
        logger.error(f"Error al iniciar la aplicación: {e}")
    finally:
        logger.info("Aplicación cerrada")

if __name__ == '__main__':
    start_app()
