#!/bin/bash
# Script de instalación para Linux/Mac
# Máquina Expendedora v2.0

echo "🚀 Iniciando instalación de Máquina Expendedora v2.0..."

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado. Por favor instálalo primero."
    exit 1
fi

echo "✅ Python 3 encontrado"

# Crear entorno virtual
echo "📦 Creando entorno virtual..."
python3 -m venv ../venv

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source ../venv/bin/activate

# Actualizar pip
echo "⬆️  Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
echo "📥 Instalando dependencias..."
pip install -r requirements.txt

# Copiar archivo de configuración
echo "⚙️  Configurando variables de entorno..."
if [ ! -f ../.env ]; then
    cp .env ../.env
    echo "📝 Archivo .env copiado. Edítalo con tus configuraciones."
else
    echo "ℹ️  Archivo .env ya existe."
fi

# Verificar instalación
echo "🔍 Verificando instalación..."
cd ..
python -c "
try:
    import flask, webview, requests
    print('✅ Todas las dependencias instaladas correctamente')
except ImportError as e:
    print(f'❌ Error: {e}')
    exit(1)
"

echo ""
echo "🎉 ¡Instalación completada!"
echo ""
echo "📝 Próximos pasos:"
echo "1. Edita el archivo .env con tus configuraciones"
echo "2. Para ejecutar: python run.py"
echo "3. Para desarrollo: python app.py"
echo ""

echo "📚 Lee el README.md para más información"

# Configurar inicio automático en Raspberry Pi (LXDE/PIXEL)
echo ""
echo "⚡ Configurando inicio automático al encender la Raspberry Pi..."
AUTOSTART_DIR=~/.config/autostart
mkdir -p "$AUTOSTART_DIR"
# Iniciar la base de datos antes del programa principal
cat > "$AUTOSTART_DIR/maquina-vending.desktop" <<EOL
[Desktop Entry]
Type=Application
Name=Maquina Vending
Exec=bash -c 'cd $(pwd)/..; python3 utils/migrate_database.py; python3 run.py'
X-GNOME-Autostart-enabled=true
EOL
echo "✅ El programa y la base de datos se iniciarán automáticamente al arrancar la Raspberry Pi."
echo "Puedes editar o eliminar ~/.config/autostart/maquina-vending.desktop si lo deseas."
