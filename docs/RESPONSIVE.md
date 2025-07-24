# Sistema Responsive - Botones de Puertas

## 📱 Descripción General

El sistema de puertas de la máquina expendedora ahora es completamente responsive, adaptándose automáticamente a cualquier tamaño de pantalla y orientación. Los botones se reorganizan dinámicamente para aprovechar al máximo el espacio disponible.

## 🎯 Características Principales

### ✅ Grid Adaptativo
- **Auto-fit**: Los botones se ajustan automáticamente al espacio disponible
- **Tamaño mínimo**: Cada botón tiene un tamaño mínimo que varía según el dispositivo
- **Máximo ancho**: En pantallas muy grandes, se limita el ancho total para mantener usabilidad

### ✅ Breakpoints Responsive

| Dispositivo | Resolución | Tamaño Mínimo | Gap | Especial |
|-------------|------------|---------------|-----|----------|
| 📱 Móvil XS | ≤ 320px | 2 columnas fijas | 4px | Ultra compacto |
| 📱 Móvil S | ≤ 576px | 80px | 6px | Optimizado táctil |
| 📱 Móvil M | ≤ 768px | 90px | 8px | Tablet pequeña |
| 📱 Tablet | ≤ 992px | 100px | 10px | Orientación mixta |
| 💻 Desktop S | ≤ 1200px | 110px | 12px | Laptop estándar |
| 💻 Desktop M | ≤ 1400px | 120px | 15px | Monitor 1080p |
| 🖥️ Desktop L | ≥ 1920px | 180px | 25px | Ultra wide, máx 1600px |

### ✅ Optimizaciones por Orientación

#### Landscape (Horizontal)
```css
@media (orientation: landscape) {
    /* Más columnas, botones más pequeños */
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
}
```

#### Portrait (Vertical)
```css
@media (orientation: portrait) {
    /* Menos columnas, botones más grandes */
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
}
```

## 🎨 Elementos Responsive

### 1. Tamaños de Fuente Escalables
```css
.door-number {
    font-size: clamp(1.5rem, 4vw, 2.5rem);
}

.door-status {
    font-size: clamp(0.6rem, 2vw, 0.75rem);
}
```

### 2. Iconos Adaptativos
```css
.door-square::before {
    width: clamp(8px, 2vw, 12px);
    height: clamp(8px, 2vw, 12px);
    top: clamp(4px, 1vw, 8px);
    right: clamp(4px, 1vw, 8px);
}
```

### 3. Interacciones Optimizadas

#### Dispositivos con Hover (Mouse)
```css
@media (hover: hover) {
    .door-square:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
    }
}
```

#### Dispositivos Táctiles
```css
@media (hover: none) {
    .door-square:active {
        transform: scale(0.95);
    }
}
```

## 📏 Comportamiento del Grid

### Algoritmo de Distribución
1. **Cálculo automático**: `grid-template-columns: repeat(auto-fit, minmax(Xpx, 1fr))`
2. **Ajuste dinámico**: El número de columnas se calcula automáticamente
3. **Distribución equitativa**: El espacio se reparte uniformemente
4. **Overflow inteligente**: Los elementos que no caben pasan a la siguiente fila

### Ejemplos Prácticos

#### Pantalla 320px (iPhone SE)
- **Configuración**: 2 columnas fijas
- **Resultado**: Máximo 2 puertas por fila
- **Gap**: 4px mínimo

#### Pantalla 768px (iPad Portrait)
- **Configuración**: `minmax(90px, 1fr)`
- **Resultado**: ~8 puertas por fila (768/90 = 8.5)
- **Gap**: 8px

#### Pantalla 1920px (Monitor FHD)
- **Configuración**: `minmax(180px, 1fr)` con máximo 1600px
- **Resultado**: ~8-9 puertas por fila (1600/180 = 8.8)
- **Gap**: 25px

## 🧪 Testing y Validación

### Archivo de Prueba
```
tests/responsive_test.html
```

Este archivo permite:
- ✅ Probar diferentes números de puertas (4-20)
- ✅ Simular resoluciones específicas
- ✅ Ver información en tiempo real
- ✅ Validar breakpoints
- ✅ Probar orientaciones

### Dispositivos Probados
- ✅ iPhone SE (320x568)
- ✅ iPhone 8 (375x667)
- ✅ iPhone 12 (390x844)
- ✅ iPad (768x1024)
- ✅ iPad Pro (1024x1366)
- ✅ Laptop (1366x768)
- ✅ Desktop FHD (1920x1080)
- ✅ Ultra Wide (2560x1440)

## 🔧 Configuración Avanzada

### Modificar Tamaños Mínimos
En `style.css`, buscar las reglas `@media` y ajustar los valores `minmax()`:

```css
@media (max-width: 768px) {
    .doors-grid {
        grid-template-columns: repeat(auto-fit, minmax(90px, 1fr));
        /*                                      ↑ Cambiar aquí */
    }
}
```

### Ajustar Gaps
```css
@media (max-width: 576px) {
    .doors-grid {
        gap: 6px; /* ← Cambiar spacing */
    }
}
```

### Personalizar Límites
```css
@media (min-width: 1920px) {
    .doors-grid {
        max-width: 1600px; /* ← Ancho máximo en pantallas grandes */
        margin: 0 auto;
    }
}
```

## 📊 Métricas de Rendimiento

### Optimizaciones Implementadas
- ✅ **CSS Grid nativo**: Mejor rendimiento que flexbox para grids
- ✅ **Clamp() para tipografía**: Escala fluida sin JavaScript
- ✅ **Media queries eficientes**: Mínimo re-cálculo
- ✅ **Touch optimizations**: Mejor UX en móviles
- ✅ **Hardware acceleration**: Transform3d para animaciones

### Compatibilidad
- ✅ **CSS Grid**: Soporte 96%+ navegadores
- ✅ **Clamp()**: Soporte 92%+ navegadores
- ✅ **@media (hover)**: Soporte 85%+ navegadores
- ✅ **Viewport units**: Soporte 98%+ navegadores

## 🚀 Casos de Uso

### 1. Máquina con 4 Puertas
```
[A1] [A2]
[B1] [B2]
```
- Móvil: 2x2 grid
- Tablet: 2x2 o 4x1
- Desktop: 4x1

### 2. Máquina con 14 Puertas
```
[A1] [A2] [B1] [B2] [C1] [C2] [D1]
[D2] [E1] [E2] [F1] [F2] [G1] [G2]
```
- Móvil: 2 columnas, 7 filas
- Tablet: 4-5 columnas, 3 filas
- Desktop: 7 columnas, 2 filas

### 3. Configuración Personalizada
El sistema se adapta automáticamente a cualquier número de puertas configuradas en `machine_config.json`.

## 📞 Solución de Problemas

### Problema: Botones muy pequeños en móvil
**Solución**: Aumentar el valor `minmax()` para móviles
```css
grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
```

### Problema: Demasiadas columnas en desktop
**Solución**: Ajustar el tamaño mínimo o agregar max-width
```css
.doors-grid {
    max-width: 1200px;
    margin: 0 auto;
}
```

### Problema: Gaps muy grandes
**Solución**: Ajustar valores de gap por breakpoint
```css
gap: clamp(4px, 1vw, 20px);
```

---

*Sistema Responsive v1.0 - Máquina Expendedora 2025*
