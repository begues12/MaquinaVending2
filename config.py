import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # Flask config
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Base de datos
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or 'database/vending_machine.db'
    
    # Configuración de pagos
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID')
    PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET')
    PAYPAL_MODE = os.environ.get('PAYPAL_MODE', 'sandbox')
        
    FULLSCREEN_MODE = False  # Cambiar a True para iniciar en fullscreen

    # Configuración del sistema
    PLATFORM = os.environ.get('PLATFORM', 'raspberry')
    GPIO_ENABLED = os.environ.get('GPIO_ENABLED', 'False').lower() == 'true'
    
    # Configuración del servidor
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', 5000))
    WINDOW_WIDTH = int(os.environ.get('WINDOW_WIDTH', 1024))
    WINDOW_HEIGHT = int(os.environ.get('WINDOW_HEIGHT', 768))
