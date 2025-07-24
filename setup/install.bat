@echo off
REM Script de instalación para Windows
REM Máquina Expendedora v2.0

echo 🚀 Iniciando instalación de Máquina Expendedora v2.0...

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python no está instalado. Por favor instálalo primero.
    echo 📥 Descarga Python desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python encontrado

REM Crear entorno virtual
echo 📦 Creando entorno virtual...
python -m venv ..\venv

REM Activar entorno virtual
echo 🔧 Activando entorno virtual...
call ..\venv\Scripts\activate.bat

REM Actualizar pip
echo ⬆️  Actualizando pip...
python -m pip install --upgrade pip

REM Instalar dependencias
echo 📥 Instalando dependencias...
pip install -r requirements.txt

REM Copiar archivo de configuración
echo ⚙️  Configurando variables de entorno...
if not exist "..\.env" (
    copy .env ..\.env
    echo 📝 Archivo .env copiado. Edítalo con tus configuraciones.
) else (
    echo ℹ️  Archivo .env ya existe.
)

REM Verificar instalación
echo 🔍 Verificando instalación...
cd ..
python -c "
try:
    import flask, webview, requests
    print('✅ Todas las dependencias instaladas correctamente')
except ImportError as e:
    print(f'❌ Error: {e}')
    exit(1)
"

echo.
echo 🎉 ¡Instalación completada!
echo.
echo 📝 Próximos pasos:
echo 1. Edita el archivo .env con tus configuraciones
echo 2. Para ejecutar: python run.py
echo 3. Para desarrollo: python app.py
echo.
echo 📚 Lee el README.md para más información
echo.
pause
