#!/bin/bash
# Script para solucionar el error de base de datos solo lectura en Raspberry Pi
# Uso: sudo bash fix_db_permissions.sh

# Ruta de la base de datos (ajusta si usas otra)
DB_PATH="/home/pi/MaquinaVending2/database.db"
DB_DIR="/home/pi/MaquinaVending2"

# 1. Crear el archivo si no existe
if [ ! -f "$DB_PATH" ]; then
    touch "$DB_PATH"
fi

# 2. Dar permisos de escritura al archivo y al directorio
chmod 666 "$DB_PATH"
chmod 777 "$DB_DIR"

# 3. Mostrar permisos actuales
ls -l "$DB_PATH"
ls -ld "$DB_DIR"

echo "Permisos corregidos. Si el error persiste, verifica que la partición no esté montada como solo lectura."
