# Script de inicio para la máquina expendedora
# Ejecuta la aplicación según la plataforma

import sys
import os
import logging
from config import Config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vending_machine.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def check_dependencies():
    """Verificar que todas las dependencias estén instaladas"""
    required_packages = [
        ('flask', 'flask'), 
        ('flask_cors', 'flask-cors'), 
        ('webview', 'pywebview'), 
        ('requests', 'requests'), 
        ('dotenv', 'python-dotenv'), 
        ('stripe', 'stripe')
    ]
    
    missing_packages = []
    
    for module_name, package_name in required_packages:
        try:
            __import__(module_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        logger.error(f"Paquetes faltantes: {', '.join(missing_packages)}")
        logger.info("Instala los paquetes con: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Función principal"""
    logger.info("Iniciando Máquina Expendedora v2.0")
    logger.info(f"Plataforma: {Config.PLATFORM}")
    logger.info(f"GPIO habilitado: {Config.GPIO_ENABLED}")
    
    # Verificar dependencias
    if not check_dependencies():
        sys.exit(1)
    
    try:
        # Importar y ejecutar la aplicación
        from app import app, start_app
        
        if Config.PLATFORM == 'windows':
            logger.info("Iniciando con PyWebView (Windows)")
            start_app()
        else:
            logger.info("Iniciando servidor Flask (Raspberry Pi)")
            app.run(
                host=Config.HOST,
                port=Config.PORT,
                debug=Config.FLASK_ENV == 'development'
            )
            
    except KeyboardInterrupt:
        logger.info("Aplicación terminada por el usuario")
    except Exception as e:
        logger.error(f"Error al iniciar la aplicación: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
