# Máquina Expendedora v2.0

Un sistema completo y escalable para máquinas expendedoras que funciona tanto en Windows (para desarrollo) como en Raspberry Pi (para producción).

## 🚀 Características

- **Backend Flask** con PyWebView para interfaz nativa
- **Sistema de pagos integrado** (Stripe, PayPal, Efectivo)
- **Abstracción GPIO** compatible Windows/Raspberry Pi
- **Base de datos SQLite** para productos y transacciones
- **Interfaz web responsive** con Bootstrap
- **Fácilmente escalable** y modular

## 📁 Estructura del Proyecto

```
MaquinaVending2/
├── 📁 controllers/           # Controladores del sistema
│   ├── gpio_controller.py    # Control de GPIO y dispensadores
│   ├── tpv_controller.py     # Control de terminal TPV
│   ├── restock_controller.py # Control de modo reposición
│   └── payment_system.py     # Sistema de pagos
├── 📁 setup/                 # Scripts de instalación y configuración
│   ├── install.bat           # Instalador para Windows
│   ├── install.sh            # Instalador para Linux/Mac
│   ├── start-windows.bat     # Inicio rápido Windows
│   ├── start-linux.sh        # Inicio rápido Linux/Mac
│   ├── requirements.txt      # Dependencias Python
│   ├── .env                  # Variables de entorno
│   ├── .env.example          # Ejemplo de configuración
│   └── INSTALL.md            # Guía detallada de instalación
├── 📁 utils/                 # Utilidades y scripts auxiliares
│   ├── utils.py              # Utilidades de mantenimiento
│   ├── migrate_database.py   # Script de migración de BD
│   └── check_stock.py        # Script verificación de stock
├── 📁 tests/                 # Archivos de prueba
│   └── test_system.py        # Tests del sistema
├── 📁 templates/             # Plantillas HTML
│   └── index.html
├── 📁 static/                # Archivos estáticos
│   ├── css/style.css
│   ├── js/vending-machine-simple.js
│   └── images/               # Imágenes de productos
├── 📁 database/              # Base de datos
├── app.py                    # Aplicación Flask principal
├── run.py                    # Script de inicio
├── config.py                 # Configuración del sistema
├── database.py               # Manejo de base de datos
├── machine_config.py         # Configuración de máquina
├── machine_config.json       # Config JSON de puertas/hardware
└── README.md                 # Documentación
```

## 🛠️ Instalación

### 🚀 Instalación Rápida (Recomendada)

#### Windows
```bash
cd setup
install.bat
```

#### Linux/Mac  
```bash
cd setup
chmod +x install.sh
./install.sh
```

### 📋 Instalación Manual

### Requisitos Previos

- Python 3.8 o superior
- pip (administrador de paquetes de Python)

### 1. Clonar o Descargar el Proyecto

```bash
# Si tienes el proyecto en un repositorio
git clone <url-del-repositorio>
cd MaquinaVending2

# O simplemente navega a la carpeta del proyecto
cd "C:\Users\afuentes\Documents\MaquinaVending2"
```

### 2. Crear Entorno Virtual (Recomendado)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
# Desde la carpeta setup/
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Copia y edita el archivo de configuración:

```bash
# Copiar archivo de ejemplo
cp setup/.env.example .env

# Editar con tus configuraciones
# Windows: notepad .env
# Linux/Mac: nano .env
```

```env
# Configuración de pagos - Stripe
STRIPE_PUBLISHABLE_KEY=pk_test_tu_clave_publica_stripe
STRIPE_SECRET_KEY=sk_test_tu_clave_secreta_stripe

# Configuración de pagos - PayPal
PAYPAL_CLIENT_ID=tu_client_id_paypal
PAYPAL_CLIENT_SECRET=tu_client_secret_paypal
PAYPAL_MODE=sandbox  # sandbox o live

# Configuración GPIO
PLATFORM=windows  # windows o raspberry
GPIO_ENABLED=False  # True para Raspberry Pi
```

## 🏃‍♂️ Ejecutar la Aplicación

### 🚀 Inicio Rápido

#### Windows
```bash
cd setup
start-windows.bat
```

#### Linux/Mac
```bash
cd setup
chmod +x start-linux.sh
./start-linux.sh
```

### 📋 Inicio Manual

### En Windows (Desarrollo)

```bash
python run.py
```

Esto abrirá la aplicación en una ventana nativa usando PyWebView.

### En Raspberry Pi (Producción)

1. Cambiar configuración en `.env`:
```env
PLATFORM=raspberry
GPIO_ENABLED=True
```

2. Instalar dependencias GPIO:
```bash
pip install RPi.GPIO gpiozero
```

3. Ejecutar:
```bash
python run.py
```

## 🔧 Configuración

### Productos

Los productos se configuran automáticamente en la base de datos al primer inicio. Puedes modificarlos editando el método `_insert_sample_data()` en `database.py`.

### Pines GPIO (Raspberry Pi)

Los pines están configurados en `gpio_controller.py`:

- **Dispensadores**: Pines 18, 19, 20, 21 (slots 1-4)
- **Sensores**: Pines 2, 3 (monedas y productos)

### Pagos

#### Stripe
1. Crear cuenta en [Stripe](https://stripe.com)
2. Obtener claves API (test/live)
3. Configurar en `.env`

#### PayPal
1. Crear aplicación en [PayPal Developer](https://developer.paypal.com)
2. Obtener Client ID y Secret
3. Configurar en `.env`

## 🧪 Testing

### Probar GPIO (Modo Simulación)

En la consola del navegador:
```javascript
// Dispensar producto del slot 1
vendingMachine.testDispense('slot_1');

// O usar atajos de teclado
// Ctrl + 1-4 para dispensar de cada slot
```

### Probar Pagos

- **Tarjetas de prueba Stripe**: `4242424242424242`
- **PayPal Sandbox**: Usar credenciales de sandbox

## 📚 API Endpoints

### Productos
- `GET /api/products` - Obtener todos los productos
- `GET /api/product/<slot>` - Obtener producto por slot

### Pagos
- `POST /api/payment/stripe/create` - Crear payment intent
- `POST /api/payment/stripe/confirm` - Confirmar pago
- `POST /api/payment/paypal/create` - Crear pago PayPal
- `POST /api/payment/paypal/execute` - Ejecutar pago PayPal
- `POST /api/payment/cash` - Procesar pago efectivo

### Sistema
- `GET /api/system/status` - Estado del sistema
- `GET /api/system/transactions` - Transacciones recientes
- `POST /api/dispense/<slot>` - Dispensar producto (testing)

## 🔄 Escalabilidad

### Añadir Nuevos Métodos de Pago

1. Crear clase en `payment_system.py`
2. Añadir rutas en `app.py`
3. Actualizar frontend en `app.js`

### Añadir Más Slots

1. Actualizar configuración GPIO en `gpio_controller.py`
2. Añadir productos en `database.py`
3. Actualizar interfaz si es necesario

### Funcionalidades Adicionales

- Autenticación de administrador
- Panel de administración web
- Integración con sistemas de inventario
- Notificaciones push
- Analytics y reportes

## 🐛 Solución de Problemas

### Error: Módulos no encontrados
```bash
pip install -r requirements.txt
```

### Error: Base de datos no encontrada
La base de datos se crea automáticamente al primer inicio.

### Error: GPIO en Windows
Es normal, usa el modo simulación para desarrollo.

### Error: Pagos no funcionan
Verifica las claves API en `.env` y la conectividad a internet.

## 📝 Logs

Los logs se guardan en `vending_machine.log` y también se muestran en consola.

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 📞 Soporte

Para soporte o preguntas, crear un issue en el repositorio del proyecto.

---

**¡Máquina Expendedora v2.0 - Sistema escalable y robusto! 🥤🍫**
