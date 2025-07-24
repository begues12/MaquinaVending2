# Instrucciones de Instalación - Máquina Expendedora v2.0

## 🚀 Instalación Rápida

### Windows
```bash
cd setup
install.bat
```

### Linux/Mac
```bash
cd setup
chmod +x install.sh
./install.sh
```

## 📋 Instalación Manual

### 1. Requisitos Previos
- **Python 3.8+** - [Descargar aquí](https://www.python.org/downloads/)
- **pip** (incluido con Python)
- **Git** (opcional)

### 2. Preparar Entorno

#### Windows
```cmd
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
venv\Scripts\activate

# Actualizar pip
python -m pip install --upgrade pip
```

#### Linux/Mac
```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip
```

### 3. Instalar Dependencias
```bash
# Desde la carpeta setup/
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
```bash
# Copiar archivo de ejemplo
cp setup/.env.example .env

# Editar configuraciones
nano .env  # o tu editor preferido
```

### 5. Configuraciones Importantes

#### Para Desarrollo (Windows)
```env
PLATFORM=windows
GPIO_ENABLED=False
FLASK_DEBUG=True
```

#### Para Producción (Raspberry Pi)
```env
PLATFORM=raspberry
GPIO_ENABLED=True
FLASK_DEBUG=False
```

#### Pagos Stripe (Opcional)
```env
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
```

#### Pagos PayPal (Opcional)
```env
PAYPAL_CLIENT_ID=your_client_id
PAYPAL_CLIENT_SECRET=your_secret
PAYPAL_MODE=sandbox  # o 'live' para producción
```

## 🔧 Dependencias Específicas

### Para Raspberry Pi
```bash
# Instalar dependencias GPIO
pip install RPi.GPIO gpiozero

# Dependencias sistema (si es necesario)
sudo apt-get update
sudo apt-get install python3-dev python3-pip
```

### Para TPV (Terminal Punto de Venta)
```bash
# Dependencia para comunicación serial
pip install pyserial
```

## ✅ Verificar Instalación

```python
# Ejecutar test básico
python -c "
import flask, webview, requests
from controllers.gpio_controller import gpio_controller
print('✅ Instalación correcta')
"
```

## 🚀 Ejecutar Aplicación

### Desarrollo
```bash
python app.py
```

### Producción
```bash
python run.py
```

## 🐛 Solución de Problemas

### Error: Python no encontrado
- Instalar Python desde python.org
- Añadir Python al PATH del sistema

### Error: pip no encontrado
```bash
python -m ensurepip --upgrade
```

### Error: Dependencias no instalan
```bash
# Actualizar pip
pip install --upgrade pip setuptools wheel

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

### Error: GPIO en Windows
- Normal para desarrollo
- Usar `PLATFORM=windows` y `GPIO_ENABLED=False`

### Error: Permisos en Linux
```bash
# Dar permisos a scripts
chmod +x setup/install.sh
chmod +x setup/start.sh

# Si hay problemas con GPIO
sudo usermod -a -G gpio $USER
```

## 📚 Recursos Adicionales

- [Documentación Python](https://docs.python.org/3/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [PyWebView Guide](https://pywebview.flowrl.com/)
- [Raspberry Pi GPIO](https://www.raspberrypi.org/documentation/usage/gpio/)
