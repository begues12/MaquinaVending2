# Sistema de Control de Hardware - Máquina Expendedora

## 📋 Descripción General

El sistema de control de hardware permite gestionar los relés y sensores de las puertas de la máquina expendedora. Está diseñado para:

- ✅ Activar relés para abrir puertas
- ✅ Detectar cuando las puertas se cierran mediante sensores
- ✅ Funcionar tanto en Raspberry Pi como en modo simulación
- ✅ Registrar eventos y mantener historial
- ✅ Proporcionar controles de seguridad

## 🔧 Configuración de Hardware

### Configuración en `machine_config.json`

Cada puerta debe tener configurados dos pines GPIO:

```json
{
  "doors": {
    "A1": {
      "id": "A1",
      "gpio_pin": 18,      // Pin para controlar el relé
      "sensor_pin": 17,    // Pin para leer el sensor de puerta
      "door_open": false,
      "last_maintenance": null
    }
  }
}
```

### Esquema de Conexión

#### Relés (Salidas)
- **GPIO Pin**: Controla un relé que abre la puerta
- **Lógica**: 
  - `HIGH` (1) = Relé activado (puerta se abre)
  - `LOW` (0) = Relé desactivado (puerta cerrada)
- **Duración**: 3 segundos por defecto

#### Sensores (Entradas)
- **Sensor Pin**: Lee el estado de la puerta
- **Lógica**:
  - `HIGH` (1) = Puerta abierta
  - `LOW` (0) = Puerta cerrada
- **Pull-up**: Activado internamente

### Diagrama de Conexión

```
Raspberry Pi                    Relé                    Puerta
GPIO 18 ---------> Relé IN -----> Cerradura -----> Puerta
GPIO 17 <--------- Sensor <------ Reed Switch <---- Puerta

Pull-up interno en GPIO 17
```

## 🚀 Uso del Sistema

### 1. Desde la Interfaz Web

Accede al panel de restock y ve a la pestaña "🔧 Control Hardware":

- **Actualizar Estado**: Obtiene el estado actual de todas las puertas
- **Abrir Puerta**: Activa el relé de una puerta específica
- **Probar Puerta**: Prueba relé y sensor de una puerta
- **Probar Todas**: Prueba todas las puertas secuencialmente
- **Parada de Emergencia**: Detiene todos los relés inmediatamente

### 2. Desde la API

#### Abrir Puerta
```bash
POST /api/hardware/door/A1/open
```

#### Obtener Estado
```bash
GET /api/hardware/door/A1/state
GET /api/hardware/doors/state
```

#### Probar Funcionamiento
```bash
POST /api/hardware/door/A1/test
POST /api/hardware/doors/test
```

#### Parada de Emergencia
```bash
POST /api/hardware/emergency-stop
```

### 3. Desde Código Python

```python
from controllers.hardware_controller import hardware_controller

# Abrir puerta
success = hardware_controller.open_door('A1')

# Obtener estado
state = hardware_controller.get_door_state('A1')

# Registrar callback para eventos
def on_door_event(door_id, is_open):
    print(f"Puerta {door_id} {'abierta' if is_open else 'cerrada'}")

hardware_controller.register_door_callback('A1', on_door_event)

# Probar puerta
success = hardware_controller.test_door('A1')

# Parada de emergencia
hardware_controller.emergency_stop()
```

## 🧪 Pruebas

### Script de Pruebas
```bash
python tests/test_hardware.py
```

Este script ofrece un menú interactivo para:
- Probar el sistema completo
- Probar puertas individuales
- Ver estado en tiempo real
- Ejecutar parada de emergencia

### Verificación Manual

1. **Verificar GPIO**: `gpio readall` (en Raspberry Pi)
2. **Comprobar pines**: Usar multímetro en los pines de relé
3. **Probar sensores**: Abrir/cerrar puertas manualmente

## 🔍 Monitoreo y Logs

### Estados de Puerta

Cada puerta mantiene:
- **is_open**: Estado actual (abierta/cerrada)
- **relay_active**: Si el relé está activo
- **last_opened**: Timestamp de última apertura
- **last_closed**: Timestamp de último cierre

### Logs del Sistema

Los eventos se registran automáticamente:
```
INFO - Puerta A1 abierta
INFO - Activando relé para puerta A1 (pin 18)
INFO - Relé de puerta A1 desactivado
WARNING - Ejecutando parada de emergencia
ERROR - Error abriendo puerta A1: descripción
```

## ⚙️ Configuración Avanzada

### Tiempos de Relé

Modificar en `hardware_controller.py`:
```python
self.relay_duration = 3.0  # Segundos
```

### Rebote de Sensores

Ajustar debounce en milisegundos:
```python
self.sensor_debounce = 200  # Milisegundos
```

### Modo Simulación

En sistemas sin GPIO (Windows/Mac), el sistema funciona en modo simulación:
- Los comandos se imprimen en consola
- Los sensores siempre reportan "cerrado"
- Útil para desarrollo y pruebas

## 🔒 Seguridad

### Protecciones Implementadas

1. **Modo Restock**: Solo funciona en modo reposición activo
2. **Timeout de Relé**: Los relés se desactivan automáticamente
3. **Parada de Emergencia**: Detiene todos los relés inmediatamente
4. **Verificación de Estado**: Evita activar relés ya activos
5. **Manejo de Errores**: Todos los errores se capturan y registran

### Recomendaciones

- ✅ Usar fusibles en las líneas de alimentación
- ✅ Relés con contactos adecuados para la carga
- ✅ Optoacopladores para aislamiento
- ✅ Cables blindados para sensores
- ✅ Tierra común entre Raspberry Pi y relés

## 🛠️ Solución de Problemas

### Problemas Comunes

#### 1. "GPIO no disponible"
```bash
sudo apt-get update
sudo apt-get install python3-rpi.gpio
```

#### 2. "Permission denied"
```bash
sudo python app.py
# O agregar usuario al grupo gpio:
sudo usermod -a -G gpio $USER
```

#### 3. "Relé no responde"
- Verificar conexiones
- Comprobar voltaje de alimentación
- Revisar estado de fusibles
- Usar multímetro en el pin GPIO

#### 4. "Sensor no detecta cambios"
- Verificar cableado del sensor
- Comprobar pull-up interno
- Revisar posición del reed switch
- Verificar que no hay interferencias

### Comandos Útiles

```bash
# Ver estado de GPIO (Raspberry Pi)
gpio readall

# Monitorear logs en tiempo real
tail -f logs/hardware.log

# Probar GPIO manualmente
gpio mode 18 out
gpio write 18 1  # Activar
gpio write 18 0  # Desactivar

# Leer sensor
gpio mode 17 in
gpio read 17
```

## 📞 Soporte

En caso de problemas con el hardware:

1. Revisar logs del sistema
2. Ejecutar script de pruebas
3. Verificar configuración de pines
4. Comprobar alimentación eléctrica
5. Contactar soporte técnico con logs detallados

---

*Documentación generada para Máquina Expendedora v2.0 - Sistema de Hardware*
