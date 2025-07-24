/**
 * Sistema de máquina expendedora con interfaz visual
 * Maneja salvapantallas, selección de puertas, pagos y GPIO
 */

class VendingMachineVisual {
    constructor() {
        this.config = window.machineConfig || {};
        this.doors = window.doors || {};
        this.selectedDoor = null;
        this.screensaverTimeout = null;
        this.cashInserted = 0;
        this.lastActivity = Date.now();
        this.restockModeActive = false;
        this.restockKeySequence = [];
        this.restockKeyTimeout = null;
        this.currentLanguage = localStorage.getItem('vendingLanguage') || 'es';
        this.languageSelector = null;
        
        this.init();
    }

    init() {
        this.setupScreensaver();
        this.setupEventListeners();
        this.generateMachineDoors();
        this.loadSystemStatus();
        
        // Actualizar estado cada 10 segundos
        setInterval(() => this.updateSystemStatus(), 10000);
        
        // Verificar inactividad cada segundo
        setInterval(() => this.checkInactivity(), 1000);
    }

    setupScreensaver() {
        const screensaver = document.getElementById('screensaver');
        const mainApp = document.getElementById('main-app');
        
        // Mostrar salvapantallas al inicio
        screensaver.style.display = 'flex';
        mainApp.style.display = 'none';
        
        // Salir del salvapantallas con selección de idioma
        screensaver.addEventListener('click', () => this.showLanguageSelector());
        screensaver.addEventListener('touchstart', () => this.showLanguageSelector());
        
        document.addEventListener('keydown', (e) => {
            if (screensaver.style.display !== 'none') {
                this.showLanguageSelector();
            }
        });
    }

    showLanguageSelector() {
        // Eliminar selector anterior si existe
        this.hideLanguageSelector();
        
        this.languageSelector = document.createElement('div');
        this.languageSelector.id = 'language-selector';
        this.languageSelector.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            z-index: 20000;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            color: white;
            animation: fadeIn 0.3s ease-out;
        `;
        
        this.languageSelector.innerHTML = `
            <style>
                @keyframes fadeIn {
                    from { opacity: 0; transform: scale(0.9); }
                    to { opacity: 1; transform: scale(1); }
                }
                .language-btn {
                    background: rgba(255, 255, 255, 0.2);
                    border: 2px solid rgba(255, 255, 255, 0.3);
                    border-radius: 20px;
                    color: white;
                    font-size: 24px;
                    font-weight: 600;
                    padding: 20px 40px;
                    margin: 15px;
                    min-width: 280px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    backdrop-filter: blur(10px);
                    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 15px;
                }
                .language-btn:hover {
                    background: rgba(255, 255, 255, 0.3);
                    border-color: rgba(255, 255, 255, 0.6);
                    transform: translateY(-5px);
                    box-shadow: 0 12px 40px rgba(0,0,0,0.3);
                }
                .language-btn:active {
                    transform: translateY(-2px);
                }
                .language-flag {
                    font-size: 32px;
                    margin-right: 10px;
                }
                .language-title {
                    font-size: 48px;
                    font-weight: 700;
                    margin-bottom: 20px;
                    text-shadow: 0 4px 8px rgba(0,0,0,0.3);
                }
                .language-subtitle {
                    font-size: 18px;
                    opacity: 0.9;
                    margin-bottom: 40px;
                    text-align: center;
                    max-width: 500px;
                }
            </style>
            <div class="language-title">🌍 Selecciona tu idioma</div>
            <div class="language-subtitle">Choose your language • Tria el teu idioma • Selecciona tu idioma</div>
            
            <div class="language-options">
                <button class="language-btn" data-lang="ca">
                    <span class="language-flag">🏴</span>
                    <span>Català</span>
                </button>
                
                <button class="language-btn" data-lang="es">
                    <span class="language-flag">🇪🇸</span>
                    <span>Español</span>
                </button>
                
                <button class="language-btn" data-lang="en">
                    <span class="language-flag">🇬🇧</span>
                    <span>English</span>
                </button>
            </div>
            
            <div style="position: absolute; bottom: 30px; font-size: 14px; opacity: 0.7;">
                Toca fuera para cancelar • Touch outside to cancel • Toca fora per cancel·lar
            </div>
        `;
        
        document.body.appendChild(this.languageSelector);
        
        // Event listeners para los botones de idioma
        this.languageSelector.querySelectorAll('.language-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const lang = btn.dataset.lang;
                this.selectLanguage(lang);
            });
        });
        
        // Click fuera para cancelar
        this.languageSelector.addEventListener('click', (e) => {
            if (e.target === this.languageSelector) {
                this.hideLanguageSelector();
                this.exitScreensaver();
            }
        });
    }

    selectLanguage(language) {
        this.currentLanguage = language;
        localStorage.setItem('vendingLanguage', language);
        
        // Mostrar confirmación
        const confirmDiv = document.createElement('div');
        confirmDiv.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(40, 167, 69, 0.95);
            color: white;
            padding: 30px 50px;
            border-radius: 20px;
            font-size: 24px;
            font-weight: 600;
            z-index: 25000;
            text-align: center;
            box-shadow: 0 15px 35px rgba(0,0,0,0.3);
            backdrop-filter: blur(15px);
        `;
        
        const messages = {
            'ca': '✓ Català seleccionat',
            'es': '✓ Español seleccionado', 
            'en': '✓ English selected'
        };
        
        confirmDiv.textContent = messages[language];
        document.body.appendChild(confirmDiv);
        
        // Limpiar y continuar
        setTimeout(() => {
            confirmDiv.remove();
            this.hideLanguageSelector();
            this.exitScreensaver();
            this.updateLanguageInterface();
        }, 1500);
    }

    hideLanguageSelector() {
        if (this.languageSelector) {
            this.languageSelector.remove();
            this.languageSelector = null;
        }
    }

    updateLanguageInterface() {
        // Usar el sistema de traducciones global
        const t = (key) => window.t ? window.t(key, this.currentLanguage) : key;
        
        // Actualizar título principal
        const selectDoorTitle = document.querySelector('h4');
        if (selectDoorTitle) {
            selectDoorTitle.innerHTML = `<i class="bi bi-grid-3x3"></i> ${t('select_door')}`;
        }
        
        // Actualizar instrucciones
        const instruction = document.querySelector('.text-muted');
        if (instruction) {
            instruction.textContent = t('click_number');
        }
        
        // Actualizar salvapantallas
        const screensaverTitle = document.querySelector('.screensaver-title');
        if (screensaverTitle) {
            screensaverTitle.textContent = t('screensaver_title');
        }
        
        const screensaverSubtitle = document.querySelector('.screensaver-subtitle');
        if (screensaverSubtitle) {
            screensaverSubtitle.textContent = t('screensaver_subtitle');
        }
        
        // Actualizar modales si existen
        this.updateModalTexts();
        
        console.log(`🌍 Idioma cambiado a: ${this.currentLanguage}`);
    }
    
    updateModalTexts() {
        const t = (key) => window.t ? window.t(key, this.currentLanguage) : key;
        
        // Modal de producto
        const productModalTitle = document.querySelector('#productModal .modal-title');
        if (productModalTitle) {
            productModalTitle.textContent = t('product_details');
        }
        
        // Botones del modal
        const buyBtn = document.querySelector('#buy-product-btn');
        if (buyBtn) {
            buyBtn.textContent = t('buy_product');
        }
        
        const cancelBtn = document.querySelector('#cancel-selection');
        if (cancelBtn) {
            cancelBtn.textContent = t('cancel');
        }
        
        // Modal de dispensando
        const dispensingText = document.querySelector('#dispensingModal .modal-body p');
        if (dispensingText) {
            dispensingText.textContent = t('please_wait');
        }
    }
    
    // Función helper para obtener texto traducido
    t(key) {
        return window.t ? window.t(key, this.currentLanguage) : key;
    }

    exitScreensaver() {
        const screensaver = document.getElementById('screensaver');
        const mainApp = document.getElementById('main-app');
        
        screensaver.style.display = 'none';
        mainApp.style.display = 'flex';
        mainApp.classList.add('fade-in');
        
        this.resetActivity();
    }

    activateScreensaver() {
        const screensaver = document.getElementById('screensaver');
        const mainApp = document.getElementById('main-app');
        
        // Limpiar selección actual
        this.clearSelection();
        
        screensaver.style.display = 'flex';
        mainApp.style.display = 'none';
    }

    checkInactivity() {
        const timeout = (this.config.machine?.screensaver_timeout || 30) * 1000;
        if (Date.now() - this.lastActivity > timeout) {
            this.activateScreensaver();
        }
    }

    resetActivity() {
        this.lastActivity = Date.now();
    }

    setupEventListeners() {
        // Actividad del usuario
        document.addEventListener('click', () => this.resetActivity());
        document.addEventListener('keydown', (e) => {
            this.resetActivity();
            this.handleRestockKeySequence(e);
        });
        document.addEventListener('touchstart', () => this.resetActivity());

        // Botones principales
        document.getElementById('buy-product-btn')?.addEventListener('click', () => {
            this.showPaymentModal();
        });

        document.getElementById('cancel-selection')?.addEventListener('click', () => {
            this.clearSelection();
        });

        // Métodos de pago
        document.querySelectorAll('.payment-method-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const method = e.target.closest('.payment-method-btn').dataset.method;
                this.selectPaymentMethod(method);
            });
        });

        // Botones de efectivo
        document.getElementById('cash-exact-btn')?.addEventListener('click', () => {
            this.processExactCash();
        });

        document.getElementById('cash-complete-btn')?.addEventListener('click', () => {
            this.completeCashPayment();
        });

        // Botón de tarjeta
        document.getElementById('card-pay-btn')?.addEventListener('click', () => {
            this.processCardPayment();
        });
    }

    handleRestockKeySequence(event) {
        // Sistema dual: Teclado para desarrollo, táctil para producción
        if (this.restockModeActive) return;

        // Método de teclado (solo en desarrollo)
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            // Primera tecla de la secuencia: Ctrl + Shift + R
            if (event.ctrlKey && event.shiftKey && event.key === 'R') {
                event.preventDefault();
                this.restockKeySequence = ['R'];
                this.showRestockProgress();
                this.resetRestockTimeout();
                return;
            }

            // Continuar secuencia si ya empezó
            if (this.restockKeySequence.length > 0) {
                event.preventDefault();
                const expectedKeys = ['R', 'S', 'T', 'K'];
                const nextKey = expectedKeys[this.restockKeySequence.length];

                if (event.key.toUpperCase() === nextKey) {
                    this.restockKeySequence.push(event.key.toUpperCase());
                    this.updateRestockProgress();
                    this.resetRestockTimeout();

                    // Secuencia completa
                    if (this.restockKeySequence.length === 4) {
                        this.activateRestockMode();
                    }
                } else {
                    this.resetRestockSequence();
                }
            }
        }
    }

    // Nuevo método para secuencia táctil
    checkTouchRestockSequence(doorId) {
        if (this.restockModeActive) return;
        
        const expectedSequence = ['A1', 'B2', 'C3', 'D4'];
        const currentPosition = this.restockKeySequence.length;
        const expectedDoor = expectedSequence[currentPosition];
        
        // Si no es la puerta esperada, resetear secuencia (a menos que sea la primera)
        if (doorId !== expectedDoor) {
            if (doorId === expectedSequence[0]) {
                // Reiniciar secuencia
                this.restockKeySequence = [doorId];
                this.showTouchRestockProgress();
                this.resetRestockTimeout();
            } else {
                // Resetear si no es la primera puerta
                this.resetRestockSequence();
            }
            return;
        }
        
        // Agregar a la secuencia
        this.restockKeySequence.push(doorId);
        this.updateTouchRestockProgress();
        this.resetRestockTimeout();
        
        // Verificar si la secuencia está completa
        if (this.restockKeySequence.length === expectedSequence.length) {
            this.completeTouchRestockSequence();
        }
    }
    
    showTouchRestockProgress() {
        // Eliminar progreso anterior si existe
        this.hideRestockProgress();
        
        const progressDiv = document.createElement('div');
        progressDiv.id = 'restock-progress';
        progressDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(13, 110, 253, 0.95);
            color: white;
            padding: 20px;
            border-radius: 15px;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 16px;
            z-index: 10000;
            min-width: 280px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
            border: 2px solid rgba(255,255,255,0.2);
        `;
        
        const expectedSequence = ['A1', 'B2', 'C3', 'D4'];
        progressDiv.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <i class="bi bi-gear-fill" style="font-size: 24px; margin-right: 10px;"></i>
                <strong style="font-size: 18px;">${this.t('restock_mode')}</strong>
            </div>
            <div style="margin-bottom: 10px;">
                ${this.t('sequence_progress')}: <span id="sequence-progress">${this.restockKeySequence.length}/${expectedSequence.length}</span>
            </div>
            <div style="margin-bottom: 10px;">
                Secuencia: <span id="sequence-display" style="font-family: monospace; background: rgba(255,255,255,0.2); padding: 5px; border-radius: 5px;">${this.restockKeySequence.join(' → ')}</span>
            </div>
            <div style="color: #ffeb3b;">
                ${this.t('next_door')}: <strong id="next-door" style="font-size: 20px;">${expectedSequence[this.restockKeySequence.length] || this.t('completed')}</strong>
            </div>
            <div style="margin-top: 15px; font-size: 12px; opacity: 0.8;">
                ${this.t('touch_sequence')}: ${expectedSequence.join(' → ')}
            </div>
        `;
        
        document.body.appendChild(progressDiv);
    }
    
    updateTouchRestockProgress() {
        const progressSpan = document.getElementById('sequence-progress');
        const sequenceSpan = document.getElementById('sequence-display');
        const nextDoorSpan = document.getElementById('next-door');
        
        const expectedSequence = ['A1', 'B2', 'C3', 'D4'];
        
        if (progressSpan) progressSpan.textContent = `${this.restockKeySequence.length}/${expectedSequence.length}`;
        if (sequenceSpan) sequenceSpan.textContent = this.restockKeySequence.join(' → ');
        if (nextDoorSpan) nextDoorSpan.textContent = expectedSequence[this.restockKeySequence.length] || 'Completo';
    }
    
    completeTouchRestockSequence() {
        this.hideRestockProgress();
        
        // Mostrar mensaje de éxito
        const successDiv = document.createElement('div');
        successDiv.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(25, 135, 84, 0.95);
            color: white;
            padding: 30px;
            border-radius: 20px;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 20px;
            z-index: 10001;
            text-align: center;
            box-shadow: 0 15px 35px rgba(0,0,0,0.3);
            backdrop-filter: blur(15px);
            border: 2px solid rgba(255,255,255,0.2);
        `;
        
        successDiv.innerHTML = `
            <div style="margin-bottom: 20px;">
                <i class="bi bi-check-circle-fill" style="font-size: 48px;"></i>
            </div>
            <div style="font-size: 24px; font-weight: bold; margin-bottom: 10px;">
                ${this.t('restock_activated')}
            </div>
            <div style="opacity: 0.9;">
                ${this.t('activating_admin_panel') || 'Activando panel de administración...'}
            </div>
        `;
        
        document.body.appendChild(successDiv);
        
        // Resetear estado
        this.resetRestockSequence();
        
        // Activar modo restock después de 2 segundos
        setTimeout(() => {
            successDiv.remove();
            this.activateRestockMode();
        }, 2000);
    }

    resetRestockTimeout() {
        if (this.restockKeyTimeout) {
            clearTimeout(this.restockKeyTimeout);
        }
        this.restockKeyTimeout = setTimeout(() => {
            this.resetRestockSequence();
        }, 3000); // 3 segundos para completar la secuencia
    }

    resetRestockSequence() {
        this.restockKeySequence = [];
        if (this.restockKeyTimeout) {
            clearTimeout(this.restockKeyTimeout);
        }
        this.hideRestockProgress();
    }

    showRestockProgress() {
        const progressDiv = document.createElement('div');
        progressDiv.id = 'restock-progress';
        progressDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 15px;
            border-radius: 10px;
            font-family: monospace;
            font-size: 14px;
            z-index: 10000;
            min-width: 200px;
        `;
        progressDiv.innerHTML = `
            <div><strong>Modo Restock</strong></div>
            <div>Secuencia: <span id="sequence-display">R</span></div>
            <div>Siguiente: <span id="next-key">S</span></div>
        `;
        document.body.appendChild(progressDiv);
    }

    updateRestockProgress() {
        const sequenceDisplay = document.getElementById('sequence-display');
        const nextKeyDisplay = document.getElementById('next-key');
        
        if (sequenceDisplay && nextKeyDisplay) {
            sequenceDisplay.textContent = this.restockKeySequence.join('');
            
            const remainingKeys = ['R', 'S', 'T', 'K'];
            const nextKey = remainingKeys[this.restockKeySequence.length];
            nextKeyDisplay.textContent = nextKey || 'Completado';
        }
    }

    hideRestockProgress() {
        const progressDiv = document.getElementById('restock-progress');
        if (progressDiv) {
            progressDiv.remove();
        }
    }

    activateRestockMode() {
        this.restockModeActive = true;
        this.hideRestockProgress();
        
        // Mostrar interfaz de restock
        this.showRestockInterface();
        
        console.log('🔧 Modo Restock Activado');
    }

    showRestockInterface() {
        // Crear modal de restock
        const restockModal = document.createElement('div');
        restockModal.id = 'restockModal';
        restockModal.className = 'modal fade';
        restockModal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-warning">
                        <h5 class="modal-title">🔧 Modo Restock Activado</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-info">
                            <strong>Funciones disponibles:</strong>
                            <ul class="mb-0 mt-2">
                                <li>Click en cualquier puerta para dispensar producto</li>
                                <li>Doble click para resetear stock a 10 unidades</li>
                                <li>Ctrl + Click para marcar como sin stock</li>
                            </ul>
                        </div>
                        <div id="restock-doors-grid" class="row g-3">
                            <!-- Se generará dinámicamente -->
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Salir del Modo Restock</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(restockModal);
        
        // Generar grid de puertas para restock
        this.generateRestockDoorsGrid();
        
        // Mostrar modal
        const modal = new bootstrap.Modal(restockModal);
        modal.show();
        
        // Limpiar al cerrar
        restockModal.addEventListener('hidden.bs.modal', () => {
            this.restockModeActive = false;
            this.resetRestockSequence();
            restockModal.remove();
        });
    }

    generateRestockDoorsGrid() {
        const container = document.getElementById('restock-doors-grid');
        if (!container) return;

        container.innerHTML = '';

        Object.values(this.doors).forEach(door => {
            const col = document.createElement('div');
            col.className = 'col-md-4 col-sm-6';
            
            col.innerHTML = `
                <div class="card restock-door-card" data-door-id="${door.id}">
                    <div class="card-body text-center">
                        <h6 class="card-title">Puerta ${door.id}</h6>
                        <p class="card-text small">${door.product.name}</p>
                        <div class="badge ${door.product.stock > 0 ? 'bg-success' : 'bg-danger'} mb-2">
                            Stock: ${door.product.stock}
                        </div>
                        <div class="d-grid gap-2">
                            <button class="btn btn-sm btn-primary dispense-btn">Dispensar</button>
                            <button class="btn btn-sm btn-success restock-btn">Restock (10)</button>
                            <button class="btn btn-sm btn-danger empty-btn">Vaciar</button>
                        </div>
                    </div>
                </div>
            `;
            
            // Event listeners para las acciones de restock
            const card = col.querySelector('.restock-door-card');
            const dispenseBtn = col.querySelector('.dispense-btn');
            const restockBtn = col.querySelector('.restock-btn');
            const emptyBtn = col.querySelector('.empty-btn');
            
            dispenseBtn.addEventListener('click', () => this.restockDispense(door.id));
            restockBtn.addEventListener('click', () => this.restockRefill(door.id));
            emptyBtn.addEventListener('click', () => this.restockEmpty(door.id));
            
            container.appendChild(col);
        });
    }

    async restockDispense(doorId) {
        try {
            const response = await fetch(`/api/test/dispense/${doorId}`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showStatusMessage('restock_mode', 'product_dispensed', 'success', { doorId });
                this.updateDoorStock(doorId, -1);
                this.generateRestockDoorsGrid();
            } else {
                this.showStatusMessage('error', result.error, 'error');
            }
        } catch (error) {
            this.showStatusMessage('error', error.message, 'error');
        }
    }

    async restockRefill(doorId) {
        try {
            const response = await fetch(`/api/restock/${doorId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ stock: 10 })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showStatusMessage('restock_mode', 'slot_refilled', 'success', { doorId });
                this.updateDoorStock(doorId, 10, true);
                this.generateRestockDoorsGrid();
                this.generateMachineDoors();
            } else {
                this.showStatusMessage('error', result.error, 'error');
            }
        } catch (error) {
            this.showStatusMessage('error', error.message, 'error');
        }
    }

    async restockEmpty(doorId) {
        try {
            const response = await fetch(`/api/restock/${doorId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ stock: 0 })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showStatusMessage('Restock', `Slot ${doorId} vaciado`, 'warning');
                this.updateDoorStock(doorId, 0, true);
                this.generateRestockDoorsGrid();
                this.generateMachineDoors();
            } else {
                this.showStatusMessage('Error', result.error, 'error');
            }
        } catch (error) {
            this.showStatusMessage('Error', error.message, 'error');
        }
    }

    updateDoorStock(doorId, change, absolute = false) {
        if (this.doors[doorId]) {
            if (absolute) {
                this.doors[doorId].product.stock = change;
            } else {
                this.doors[doorId].product.stock = Math.max(0, this.doors[doorId].product.stock + change);
            }
            
            // Actualizar estado
            if (this.doors[doorId].product.stock === 0) {
                this.doors[doorId].status = 'out_of_stock';
            } else {
                this.doors[doorId].status = 'available';
            }
        }
    }

    generateMachineDoors() {
        const doorsContainer = document.getElementById('product-doors');
        if (!doorsContainer) return;

        // Limpiar contenido existente
        doorsContainer.innerHTML = '';

        Object.values(this.doors).forEach(door => {
            const doorGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            doorGroup.setAttribute('class', `product-door ${door.status}`);
            doorGroup.setAttribute('data-door-id', door.id);
            doorGroup.style.cursor = door.status === 'available' ? 'pointer' : 'not-allowed';

            // Puerta principal
            const doorRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            doorRect.setAttribute('x', door.position.x);
            doorRect.setAttribute('y', door.position.y);
            doorRect.setAttribute('width', door.position.width);
            doorRect.setAttribute('height', door.position.height);
            doorRect.setAttribute('rx', '5');
            doorRect.setAttribute('fill', this.getDoorColor(door.status));
            doorRect.setAttribute('stroke', '#34495e');
            doorRect.setAttribute('stroke-width', '2');

            // Etiqueta de la puerta
            const doorLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            doorLabel.setAttribute('x', door.position.x + door.position.width / 2);
            doorLabel.setAttribute('y', door.position.y + 20);
            doorLabel.setAttribute('class', 'door-label');
            doorLabel.setAttribute('fill', 'white');
            doorLabel.textContent = door.id;

            // Nombre del producto
            const productName = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            productName.setAttribute('x', door.position.x + door.position.width / 2);
            productName.setAttribute('y', door.position.y + 40);
            productName.setAttribute('class', 'door-price');
            productName.setAttribute('fill', 'white');
            productName.textContent = door.product.name.substring(0, 8);

            // Precio
            const productPrice = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            productPrice.setAttribute('x', door.position.x + door.position.width / 2);
            productPrice.setAttribute('y', door.position.y + door.position.height - 10);
            productPrice.setAttribute('class', 'door-price');
            productPrice.setAttribute('fill', 'white');
            productPrice.setAttribute('font-weight', 'bold');
            productPrice.textContent = `€${door.product.price.toFixed(2)}`;

            // Stock indicator
            if (door.product.stock <= 2 && door.product.stock > 0) {
                const stockWarning = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                stockWarning.setAttribute('cx', door.position.x + door.position.width - 10);
                stockWarning.setAttribute('cy', door.position.y + 10);
                stockWarning.setAttribute('r', '5');
                stockWarning.setAttribute('fill', '#ffc107');
                doorGroup.appendChild(stockWarning);
            }

            doorGroup.appendChild(doorRect);
            doorGroup.appendChild(doorLabel);
            doorGroup.appendChild(productName);
            doorGroup.appendChild(productPrice);

            // Event listener para selección
            if (door.status === 'available') {
                doorGroup.addEventListener('click', () => this.selectDoor(door.id));
            }

            doorsContainer.appendChild(doorGroup);
        });
    }

    getDoorColor(status) {
        const colors = this.config.display?.door_states || {
            'available': '#28a745',
            'selected': '#007bff',
            'out_of_stock': '#dc3545',
            'blocked': '#6c757d',
            'dispensing': '#ffc107'
        };
        return colors[status] || colors['available'];
    }

    selectDoor(doorId) {
        // Verificar secuencia táctil de restock PRIMERO (siempre)
        this.checkTouchRestockSequence(doorId);
        
        const door = this.doors[doorId];
        if (!door || door.status !== 'available') return;

        // Limpiar selección anterior
        this.clearSelection();

        this.selectedDoor = door;

        // Actualizar visuales
        this.updateDoorVisuals(doorId, 'selected');
        this.showSelectedDoorInfo(door);

        this.resetActivity();
    }

    clearSelection() {
        if (this.selectedDoor) {
            this.updateDoorVisuals(this.selectedDoor.id, this.selectedDoor.status);
            this.selectedDoor = null;
        }

        document.getElementById('selected-door-info').style.display = 'none';
        document.getElementById('cancel-selection').style.display = 'none';
        document.getElementById('instructions').style.display = 'block';
    }

    updateDoorVisuals(doorId, status) {
        const doorElement = document.querySelector(`[data-door-id="${doorId}"]`);
        if (!doorElement) return;

        const rect = doorElement.querySelector('rect');
        if (rect) {
            rect.setAttribute('fill', this.getDoorColor(status));
        }

        doorElement.className = `product-door ${status}`;
    }

    showSelectedDoorInfo(door) {
        const infoPanel = document.getElementById('selected-door-info');
        const cancelBtn = document.getElementById('cancel-selection');
        const instructions = document.getElementById('instructions');

        // Actualizar información
        document.getElementById('selected-product-image').src = door.product.image || '/static/images/placeholder.jpg';
        document.getElementById('selected-product-name').textContent = door.product.name;
        document.getElementById('selected-product-description').textContent = door.product.description || 'Producto disponible';
        document.getElementById('selected-product-price').textContent = `€${door.product.price.toFixed(2)}`;
        document.getElementById('selected-product-stock').textContent = door.product.stock;

        // Mostrar/ocultar elementos
        infoPanel.style.display = 'block';
        cancelBtn.style.display = 'block';
        instructions.style.display = 'none';

        infoPanel.classList.add('slide-up');
    }

    showPaymentModal() {
        if (!this.selectedDoor) return;

        const modal = new bootstrap.Modal(document.getElementById('paymentModal'));
        modal.show();
        this.resetActivity();
    }

    selectPaymentMethod(method) {
        const paymentModal = bootstrap.Modal.getInstance(document.getElementById('paymentModal'));
        paymentModal?.hide();

        switch (method) {
            case 'cash':
                this.showCashModal();
                break;
            case 'card':
                this.showCardModal();
                break;
            case 'contactless':
                this.processContactlessPayment();
                break;
        }
    }

    showCashModal() {
        if (!this.selectedDoor) return;

        this.cashInserted = 0;
        this.updateCashDisplay();
        this.generateCashDenominations();

        const modal = new bootstrap.Modal(document.getElementById('cashModal'));
        modal.show();
    }

    generateCashDenominations() {
        const container = document.getElementById('cash-denominations');
        const denominations = this.config.payment_methods?.cash?.accepts || [0.05, 0.10, 0.20, 0.50, 1.00, 2.00, 5.00, 10.00, 20.00];

        container.innerHTML = '';

        denominations.forEach(value => {
            const col = document.createElement('div');
            col.className = 'col-4 mb-2';

            const btn = document.createElement('button');
            btn.className = 'btn btn-outline-secondary cash-denomination w-100';
            btn.dataset.value = value;
            btn.innerHTML = `€${value.toFixed(2)}`;

            btn.addEventListener('click', () => this.insertCash(value));

            col.appendChild(btn);
            container.appendChild(col);
        });
    }

    insertCash(amount) {
        this.cashInserted += amount;
        this.updateCashDisplay();

        // Marcar denominación como insertada
        const btn = document.querySelector(`[data-value="${amount}"]`);
        if (btn) {
            btn.classList.add('inserted');
            setTimeout(() => btn.classList.remove('inserted'), 1000);
        }

        this.resetActivity();
    }

    updateCashDisplay() {
        const total = this.selectedDoor.product.price;
        const remaining = Math.max(0, total - this.cashInserted);
        const change = Math.max(0, this.cashInserted - total);

        document.getElementById('cash-total').textContent = `€${total.toFixed(2)}`;
        document.getElementById('cash-inserted').textContent = `€${this.cashInserted.toFixed(2)}`;
        
        if (remaining > 0) {
            document.getElementById('cash-remaining').innerHTML = `Faltan: <span class="text-danger">€${remaining.toFixed(2)}</span>`;
        } else {
            document.getElementById('cash-remaining').innerHTML = `<span class="text-success">Cantidad suficiente</span>`;
        }

        // Mostrar cambio
        const changeAlert = document.getElementById('cash-change-alert');
        if (change > 0) {
            document.getElementById('cash-change').textContent = `€${change.toFixed(2)}`;
            changeAlert.style.display = 'block';
        } else {
            changeAlert.style.display = 'none';
        }

        // Habilitar botones
        document.getElementById('cash-exact-btn').disabled = this.cashInserted !== total;
        document.getElementById('cash-complete-btn').disabled = this.cashInserted < total;
    }

    processExactCash() {
        this.completeCashPayment();
    }

    async completeCashPayment() {
        if (!this.selectedDoor || this.cashInserted < this.selectedDoor.product.price) return;

        try {
            const modal = bootstrap.Modal.getInstance(document.getElementById('cashModal'));
            modal?.hide();

            await this.processPurchase('cash', {
                amount: this.selectedDoor.product.price,
                received: this.cashInserted,
                change: this.cashInserted - this.selectedDoor.product.price
            });

        } catch (error) {
            this.showStatusMessage('Error', 'Error al procesar pago en efectivo', 'error');
        }
    }

    showCardModal() {
        // Implementar integración con Stripe u otro procesador
        const modal = new bootstrap.Modal(document.getElementById('cardModal'));
        modal.show();
    }

    async processCardPayment() {
        // Implementar pago con tarjeta
        this.showStatusMessage('Info', 'Pago con tarjeta no implementado aún', 'warning');
    }

    async processContactlessPayment() {
        // Implementar pago sin contacto
        this.showStatusMessage('Info', 'Pago sin contacto no disponible', 'warning');
    }

    async processPurchase(paymentMethod, paymentData) {
        if (!this.selectedDoor) return;

        // Mostrar modal de dispensando
        const dispensingModal = new bootstrap.Modal(document.getElementById('dispensingModal'));
        dispensingModal.show();

        try {
            // Llamar al backend para procesar la compra
            const response = await fetch('/api/purchase', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    door_id: this.selectedDoor.id,
                    payment_method: paymentMethod,
                    payment_data: paymentData
                })
            });

            const result = await response.json();
            dispensingModal.hide();

            if (result.success) {
                // Actualizar estado de la puerta
                if (result.new_status) {
                    this.doors[this.selectedDoor.id].status = result.new_status;
                    this.doors[this.selectedDoor.id].product.stock = result.remaining_stock || 0;
                }

                this.showStatusMessage(
                    '¡Éxito!', 
                    `Producto dispensado. ${paymentData.change > 0 ? `Cambio: €${paymentData.change.toFixed(2)}` : ''}`, 
                    'success'
                );

                // Limpiar selección y regenerar puertas
                this.clearSelection();
                this.generateMachineDoors();
                this.updateSystemStatus();

            } else {
                this.showStatusMessage('Error', result.error || 'Error al dispensar producto', 'error');
            }

        } catch (error) {
            dispensingModal.hide();
            this.showStatusMessage('Error', 'Error de comunicación con el servidor', 'error');
        }
    }

    showStatusMessage(titleKey, messageKey, type, params = {}) {
        const modal = document.getElementById('statusModal');
        const titleEl = document.getElementById('status-title');
        const iconEl = document.getElementById('status-icon');
        const messageEl = document.getElementById('status-message');

        // Traducir título y mensaje
        const title = this.t(titleKey) || titleKey;
        let message = this.t(messageKey) || messageKey;
        
        // Reemplazar parámetros en el mensaje
        Object.keys(params).forEach(key => {
            message = message.replace(`{${key}}`, params[key]);
        });

        titleEl.textContent = title;
        messageEl.textContent = message;

        // Icono según tipo
        const icons = {
            'success': '<i class="bi bi-check-circle-fill text-success" style="font-size: 3rem;"></i>',
            'error': '<i class="bi bi-x-circle-fill text-danger" style="font-size: 3rem;"></i>',
            'warning': '<i class="bi bi-exclamation-triangle-fill text-warning" style="font-size: 3rem;"></i>',
            'info': '<i class="bi bi-info-circle-fill text-info" style="font-size: 3rem;"></i>'
        };

        iconEl.innerHTML = icons[type] || icons['info'];

        const statusModal = new bootstrap.Modal(modal);
        statusModal.show();

        this.resetActivity();
    }

    async loadSystemStatus() {
        try {
            // Cargar configuración actualizada
            const configResponse = await fetch('/api/machine/config');
            if (configResponse.ok) {
                const configData = await configResponse.json();
                this.doors = configData.doors || this.doors;
                this.generateMachineDoors();
            }

            this.updateSystemStatus();
        } catch (error) {
            console.error('Error cargando estado del sistema:', error);
        }
    }

    updateSystemStatus() {
        const availableDoors = Object.values(this.doors).filter(d => d.status === 'available').length;
        const restockNeeded = Object.values(this.doors).filter(d => d.requires_restock || d.product.stock <= 2).length;

        document.getElementById('available-doors-count').textContent = availableDoors;
        document.getElementById('restock-doors-count').textContent = restockNeeded;

        const statusIndicator = document.getElementById('system-status-indicator');
        if (availableDoors === 0) {
            statusIndicator.textContent = 'Sin stock';
            statusIndicator.className = 'badge bg-danger';
        } else if (restockNeeded > 0) {
            statusIndicator.textContent = 'Advertencia';
            statusIndicator.className = 'badge bg-warning';
        } else {
            statusIndicator.textContent = 'Operativo';
            statusIndicator.className = 'badge bg-success';
        }
    }

    // Función para testing de GPIO
    async testDispense(doorId) {
        try {
            const response = await fetch(`/api/test/dispense/${doorId}`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showStatusMessage('Test GPIO', `Producto dispensado del slot ${doorId}`, 'success');
            } else {
                this.showStatusMessage('Error', result.error, 'error');
            }
        } catch (error) {
            this.showStatusMessage('Error', error.message, 'error');
        }
    }
}

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.vendingMachine = new VendingMachineVisual();
    
    // Atajos para testing en desarrollo
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log('🔧 Modo desarrollo activado');
        console.log('📋 Comandos disponibles:');
        console.log('  vendingMachine.testDispense("A1") - Probar dispensado');
        console.log('  vendingMachine.exitScreensaver() - Salir del salvapantallas');
        console.log('  vendingMachine.activateScreensaver() - Activar salvapantallas');
        console.log('🔐 Modo Restock (Desarrollo):');
        console.log('  Ctrl+Shift+R, luego R-S-T-K - Activar modo restock');
        console.log('🔐 Modo Restock (Producción):');
        console.log('  Tocar puertas en orden: A1 → B2 → C3 → D4');
        
        // Atajos de teclado para testing
        window.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey) {
                switch(e.key) {
                    case 'S':
                        e.preventDefault();
                        window.vendingMachine.activateScreensaver();
                        break;
                    case 'T':
                        e.preventDefault();
                        window.vendingMachine.testDispense('A1');
                        break;
                }
            }
        });
    } else {
        console.log('🔐 Modo Restock Táctil:');
        console.log('  Tocar puertas en orden: A1 → B2 → C3 → D4');
    }
});
