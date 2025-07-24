# Sistema de Popup Central - Interfaz de Producto

## 📱 Descripción General

El sistema ahora muestra un **popup central** en lugar del panel lateral cuando el usuario selecciona una puerta. Esta mejora proporciona una experiencia más moderna y centrada en el producto.

## 🎯 Características Principales

### ✅ Modal Centrado
- **Posición**: Centro absoluto de la pantalla
- **Backdrop**: Fondo oscuro que bloquea la interacción con otros elementos
- **Responsive**: Se adapta a cualquier tamaño de pantalla
- **Escape**: Se puede cerrar con ESC, clic fuera, o botón X

### ✅ Información Detallada del Producto
- **Imagen**: Muestra imagen del producto si está disponible
- **Nombre**: Título prominente del producto
- **Descripción**: Texto descriptivo del producto
- **Precio**: Destacado en verde con símbolo de euro
- **Stock**: Badge visual del estado de disponibilidad

### ✅ Diseño Mejorado
- **Layout responsive**: 2 columnas en desktop, 1 columna en móvil
- **Visual hierarchy**: Información organizada por importancia
- **Colores consistentes**: Sigue la paleta de la aplicación
- **Animaciones**: Transiciones suaves para mejor UX

## 🔧 Implementación Técnica

### Estructura HTML
```html
<div class="modal fade" id="productModal">
    <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content">
            <div class="modal-header bg-primary text-white">
                <h4>Puerta <span id="modal-door-number"></span></h4>
            </div>
            <div class="modal-body">
                <div class="row">
                    <div class="col-md-6">
                        <!-- Imagen del producto -->
                        <div class="product-image-container">
                            <img id="modal-product-image" />
                            <i class="bi bi-box-seam" /> <!-- Fallback -->
                        </div>
                    </div>
                    <div class="col-md-6">
                        <!-- Información del producto -->
                        <h3 id="modal-product-name"></h3>
                        <p id="modal-product-description"></p>
                        <div class="price-display">
                            <h2>€<span id="modal-product-price"></span></h2>
                        </div>
                        <span id="modal-stock-badge"></span>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-outline-secondary">Cancelar</button>
                <button class="btn btn-primary">Pagar Contactless</button>
            </div>
        </div>
    </div>
</div>
```

### JavaScript Principal
```javascript
showProductModal(doorId, doorData) {
    // Actualizar información del modal
    document.getElementById('modal-door-number').textContent = doorId;
    document.getElementById('modal-product-name').textContent = doorData.product.name;
    document.getElementById('modal-product-description').textContent = doorData.product.description;
    document.getElementById('modal-product-price').textContent = doorData.product.price.toFixed(2);
    
    // Manejar imagen del producto
    const productImage = document.getElementById('modal-product-image');
    if (doorData.product.image_url) {
        productImage.src = doorData.product.image_url;
        productImage.style.display = 'block';
    } else {
        productImage.style.display = 'none';
        // Mostrar icono por defecto
    }
    
    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById('productModal'));
    modal.show();
}
```

### Estilos CSS Destacados
```css
/* Modal de Producto */
#productModal .modal-dialog {
    max-width: 600px;
}

.product-image-container {
    min-height: 200px;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.price-display {
    background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
    border-radius: 15px;
    padding: 20px;
    text-align: center;
}

.price-display h2 {
    font-size: 2.5rem;
    font-weight: bold;
    color: #28a745;
}
```

## 📱 Responsive Design

### Desktop (≥768px)
```
┌─────────────────────────────────────────┐
│               Puerta A1                 │
├─────────────────┬───────────────────────┤
│                 │  Producto XYZ         │
│    [Imagen]     │  Descripción...       │
│                 │  ┌─────────────────┐  │
│                 │  │     €2.50       │  │
│                 │  └─────────────────┘  │
│                 │  [✓ En stock]         │
├─────────────────┴───────────────────────┤
│    [Cancelar]  [Pagar Contactless]     │
└─────────────────────────────────────────┘
```

### Móvil (≤768px)
```
┌───────────────────────┐
│      Puerta A1        │
├───────────────────────┤
│     [Imagen]          │
│                       │
│   Producto XYZ        │
│   Descripción...      │
│   ┌─────────────────┐ │
│   │     €2.50       │ │
│   └─────────────────┘ │
│   [✓ En stock]        │
├───────────────────────┤
│ [Cancelar] [Pagar]    │
└───────────────────────┘
```

## 🎨 Estados Visuales

### Stock Disponible
- **Badge**: Verde con ✓ "En stock"
- **Botón**: Habilitado para pagar
- **Precio**: Destacado en verde

### Sin Stock
- **Badge**: Rojo con ✗ "Sin stock"
- **Botón**: Deshabilitado
- **Precio**: Tachado

### Imagen de Producto
- **Con imagen**: Muestra la imagen escalada
- **Sin imagen**: Icono de caja por defecto
- **Error de carga**: Fallback al icono

## 🔄 Flujo de Usuario

1. **Usuario hace clic en puerta**
   - Se valida disponibilidad
   - Se ejecuta secuencia secreta (silenciosamente)
   - Se marca puerta como seleccionada

2. **Se abre el modal**
   - Animación de entrada suave
   - Información del producto cargada
   - Foco en el modal

3. **Usuario revisa información**
   - Ve imagen, nombre, descripción
   - Confirma precio
   - Verifica disponibilidad

4. **Usuario toma decisión**
   - **Continuar**: Clic en "Pagar Contactless"
   - **Cancelar**: Clic en "Cancelar", X, o ESC

5. **Modal se cierra**
   - Animación de salida
   - Selección se limpia
   - Timer de screensaver se reinicia

## ⚡ Ventajas del Nuevo Sistema

### Vs. Panel Lateral Anterior

| Aspecto | Panel Lateral | Modal Central |
|---------|---------------|---------------|
| **Visibilidad** | Parcial | Completa |
| **Foco** | Dividido | Centrado |
| **Espacio** | Limitado | Amplio |
| **Móvil** | Problemático | Optimizado |
| **Información** | Básica | Detallada |
| **UX** | Tradicional | Moderna |

### Beneficios Específicos
- ✅ **Mayor prominencia**: El producto es el foco principal
- ✅ **Más información**: Espacio para descripción e imagen
- ✅ **Mejor móvil**: Layout optimizado para pantallas pequeñas
- ✅ **Interacción clara**: Botones prominentes y bien definidos
- ✅ **Escape intuitivo**: Múltiples formas de cancelar

## 🔧 Configuración

### Habilitar/Deshabilitar Modal
En `vending-machine-simple.js`:
```javascript
// Para volver al panel lateral (no recomendado)
showDoorInfo(doorId, doorData) {
    // Código del panel lateral...
}

// Para usar modal (actual)
showProductModal(doorId, doorData) {
    // Código del modal...
}
```

### Personalizar Diseño
En `style.css`:
```css
/* Cambiar tamaño máximo del modal */
#productModal .modal-dialog {
    max-width: 800px; /* Más ancho */
}

/* Cambiar altura mínima */
#productModal .modal-body {
    min-height: 400px; /* Más alto */
}

/* Personalizar colores del precio */
.price-display {
    background: linear-gradient(135deg, #your-color-1, #your-color-2);
}
```

### Agregar Información Adicional
Puedes agregar más campos al modal editando:
1. **HTML**: Agregar elementos en `templates/index.html`
2. **JavaScript**: Actualizar `showProductModal()` 
3. **CSS**: Estilos para nuevos elementos

## 🧪 Testing

### Casos de Prueba
1. **Puerta disponible**: Modal muestra correctamente
2. **Puerta sin stock**: Badge y botón reflejan estado
3. **Con imagen**: Se carga y escala correctamente
4. **Sin imagen**: Muestra icono por defecto
5. **Responsive**: Se adapta en móvil y desktop
6. **Cancelación**: Todos los métodos funcionan
7. **Secuencia secreta**: Sigue funcionando silenciosamente

### Navegadores Soportados
- ✅ Chrome 90+
- ✅ Firefox 90+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ Móviles modernos

---

*Sistema de Popup v1.0 - Máquina Expendedora 2025*
