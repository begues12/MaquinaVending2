@echo off
REM Script de inicio rápido para Windows
REM Máquina Expendedora v2.0

echo 🚀 Iniciando Máquina Expendedora v2.0...

REM Verificar si existe entorno virtual
if not exist "..\venv\Scripts\activate.bat" (
    echo ❌ Entorno virtual no encontrado.
    echo 📥 Ejecuta primero: setup\install.bat
    pause
    exit /b 1
)

REM Activar entorno virtual
echo 🔧 Activando entorno virtual...
call ..\venv\Scripts\activate.bat

REM Ir al directorio principal
cd ..

REM Verificar archivo .env
if not exist ".env" (
    echo ⚠️  Archivo .env no encontrado.
    echo 📝 Copiando configuración por defecto...
    copy setup\.env.example .env
    echo ℹ️  Edita el archivo .env con tus configuraciones.
)

REM Ejecutar aplicación
echo 🏃‍♂️ Ejecutando aplicación...
python run.py

pause
