#!/bin/bash
# Script de inicio rápido para Linux/Mac
# Máquina Expendedora v2.0

echo "🚀 Iniciando Máquina Expendedora v2.0..."

# Verificar si existe entorno virtual
if [ ! -f "../venv/bin/activate" ]; then
    echo "❌ Entorno virtual no encontrado."
    echo "📥 Ejecuta primero: ./setup/install.sh"
    exit 1
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source ../venv/bin/activate

# Ir al directorio principal
cd ..

# Verificar archivo .env
if [ ! -f ".env" ]; then
    echo "⚠️  Archivo .env no encontrado."
    echo "📝 Copiando configuración por defecto..."
    cp setup/.env.example .env
    echo "ℹ️  Edita el archivo .env con tus configuraciones."
fi

# Ejecutar aplicación
echo "🏃‍♂️ Ejecutando aplicación..."
python run.py
