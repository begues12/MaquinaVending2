class VendingMachineSimple {
    constructor() {
        this.selectedDoor = null;
        this.doorsData = window.doors || {};
        this.config = window.machineConfig || {};
        this.screensaverTimeout = null;
        this.screensaverDelay = (this.config.display?.screensaver_timeout || 30) * 1000;
        this.currentLanguage = localStorage.getItem('vendingLanguage') || 'es';
        this.languageSelector = null;
        
        // Sistema de secuencia secreta táctil
        this.restockSequence = [];
        this.restockTimeout = null;
        this.restockProgressDiv = null;
        this.expectedSequence = ['A1', 'B2', 'C3', 'D4']; // Secuencia que forma una diagonal
        
        this.init();
    }

    init() {
        this.setupScreensaver();
        this.generateDoorsGrid();
        this.setupEventListeners();
        this.updateSystemStatus();
        this.startScreensaverTimer();
    }

    setupScreensaver() {
        const screensaver = document.getElementById('screensaver');
        const mainApp = document.getElementById('main-app');
        
        // Click en screensaver para mostrar selector de idioma
        screensaver.addEventListener('click', () => {
            this.showLanguageSelector();
        });
        
        screensaver.addEventListener('touchstart', () => {
            this.showLanguageSelector();
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

    exitScreensaver() {
        const screensaver = document.getElementById('screensaver');
        const mainApp = document.getElementById('main-app');
        
        screensaver.style.display = 'none';
        mainApp.style.display = 'flex';
        this.startScreensaverTimer();
        
        // Aplicar idioma seleccionado al cargar
        this.updateLanguageInterface();
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
        
        console.log(`🌍 Idioma cambiado a: ${this.currentLanguage}`);
    }

    // Función helper para obtener texto traducido
    t(key) {
        return window.t ? window.t(key, this.currentLanguage) : key;
    }

    generateDoorsGrid() {
        const grid = document.getElementById('doors-grid');
        grid.innerHTML = '';

        // Obtener todas las puertas disponibles dinámicamente
        const doorIds = Object.keys(this.doorsData);
        
        // Calcular el número de columnas basado en la cantidad de puertas
        let columns = 3; // Por defecto 3 columnas
        if (doorIds.length <= 4) columns = 2;
        if (doorIds.length <= 2) columns = 1;
        if (doorIds.length > 9) columns = 4;
        if (doorIds.length > 12) columns = 5;
        
        // Aplicar grid dinámico
        grid.style.gridTemplateColumns = `repeat(${columns}, 1fr)`;
        
        // Generar puertas en orden
        doorIds.sort().forEach(doorId => {
            const door = this.doorsData[doorId];
            const doorSquare = this.createDoorSquare(doorId, door);
            grid.appendChild(doorSquare);
        });
    }

    createDoorSquare(doorId, doorData) {
        const square = document.createElement('div');
        square.className = 'door-square';
        square.dataset.doorId = doorId;
        
        // Determinar estado de la puerta
        let status = 'available';
        let statusText = 'Disponible';
        
        if (doorData.status === 'blocked') {
            status = 'blocked';
            statusText = 'Bloqueado';
        } else if (doorData.product.stock <= 0) {
            status = 'out-of-stock';
            statusText = 'Sin stock';
        }
        
        square.classList.add(status);
        
        square.innerHTML = `
            <div class="door-number">${doorId}</div>
            <div class="door-status">${statusText}</div>
        `;
        
        // Event listener para selección - SIEMPRE permitir click para secuencia secreta
        square.addEventListener('click', () => this.selectDoor(doorId, doorData));
        
        return square;
    }

    selectDoor(doorId, doorData) {
        // Verificar secuencia secreta primero - SIEMPRE
        this.checkSecretSequence(doorId);
        
        // Solo proceder con la compra si la puerta está disponible
        if (doorData.status !== 'available' || doorData.product.stock <= 0) {
            // Para puertas no disponibles, solo verificamos secuencia secreta
            console.log(`Puerta ${doorId} no disponible para compra, pero verificada para secuencia secreta`);
            return;
        }
        
        // Resetear selección anterior
        this.clearSelection();
        
        // Marcar puerta seleccionada
        const doorSquare = document.querySelector(`[data-door-id="${doorId}"]`);
        doorSquare.classList.add('selected');
        
        this.selectedDoor = doorId;
        
        // Mostrar modal de producto
        this.showProductModal(doorId, doorData);
        
        // Reiniciar timer de screensaver
        this.startScreensaverTimer();
    }

    showProductModal(doorId, doorData) {
        // Actualizar información del modal (solo precio y puerta)
        document.getElementById('modal-door-number').textContent = doorId;
        document.getElementById('modal-product-price').textContent = doorData.product.price.toFixed(2);
        
        // Actualizar badge de stock
        const stockBadge = document.getElementById('modal-stock-badge');
        if (doorData.product.stock > 0) {
            stockBadge.innerHTML = '<i class="bi bi-check-circle"></i> En stock';
            stockBadge.className = 'badge bg-success fs-6';
        } else {
            stockBadge.innerHTML = '<i class="bi bi-x-circle"></i> Sin stock';
            stockBadge.className = 'badge bg-danger fs-6';
        }
        
        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById('productModal'));
        modal.show();
        
        // Guardar referencia del modal para uso posterior
        this.currentModal = modal;
    }

    showDoorInfo(doorId, doorData) {
        // Esta función ya no se usa, mantenida para compatibilidad
        // La nueva implementación usa showProductModal
    }

    clearSelection() {
        // Limpiar selección visual
        document.querySelectorAll('.door-square.selected').forEach(square => {
            square.classList.remove('selected');
        });
        
        // Cerrar modal si está abierto
        if (this.currentModal) {
            this.currentModal.hide();
            this.currentModal = null;
        }
        
        this.selectedDoor = null;
    }

    setupEventListeners() {
        // Botón continuar compra desde el modal de producto
        document.getElementById('modal-continue-purchase').addEventListener('click', () => {
            this.showContactlessModal();
        });
        
        // Eventos del modal de producto
        document.getElementById('productModal').addEventListener('hidden.bs.modal', () => {
            // Limpiar selección cuando se cierra el modal
            this.clearSelection();
            this.startScreensaverTimer();
        });

        // Botón de pago contactless
        document.getElementById('contactless-pay-btn').addEventListener('click', () => {
            this.processContactlessPayment();
        });

        // Detectar actividad para resetear screensaver
        ['click', 'mousemove', 'keydown', 'touchstart'].forEach(event => {
            document.addEventListener(event, () => {
                this.startScreensaverTimer();
            });
        });
    }

    showContactlessModal() {
        if (!this.selectedDoor) return;
        
        const doorData = this.doorsData[this.selectedDoor];
        document.getElementById('contactless-total').textContent = `€${doorData.product.price.toFixed(2)}`;
        
        const modal = new bootstrap.Modal(document.getElementById('contactlessModal'));
        modal.show();
        
        this.startScreensaverTimer();
    }

    async processContactlessPayment() {
        if (!this.selectedDoor) return;

        const doorData = this.doorsData[this.selectedDoor];
        
        try {
            // Mostrar estado de procesamiento TPV
            document.getElementById('contactless-processing').style.display = 'block';
            document.getElementById('contactless-processing').innerHTML = `
                <div class="spinner-border text-primary mb-2"></div>
                <p>Comunicando con TPV...</p>
                <small class="text-muted">Procesando pago contactless</small>
            `;
            document.getElementById('contactless-pay-btn').disabled = true;

            let paymentData = {
                door_id: this.selectedDoor,
                payment_method: 'contactless',
                payment_data: {
                    amount: doorData.product.price
                }
            };

            const response = await fetch('/api/purchase', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(paymentData)
            });

            const result = await response.json();
            
            // Cerrar modal de contactless
            bootstrap.Modal.getInstance(document.getElementById('contactlessModal')).hide();
            
            // Mostrar modal de dispensando
            this.showDispensingModal();
            
            // Simular tiempo de dispensado
            setTimeout(() => {
                bootstrap.Modal.getInstance(document.getElementById('dispensingModal')).hide();
                
                if (result.success) {
                    this.showSuccessResult(result);
                    this.updateDoorAfterPurchase(this.selectedDoor, result);
                } else {
                    this.showErrorResult(result.error);
                }
            }, 2000);

        } catch (error) {
            console.error('Error al procesar pago contactless:', error);
            bootstrap.Modal.getInstance(document.getElementById('contactlessModal')).hide();
            this.showErrorResult('Error de comunicación con TPV. Intenta de nuevo.');
        } finally {
            // Resetear estado del modal
            document.getElementById('contactless-processing').style.display = 'none';
            document.getElementById('contactless-pay-btn').disabled = false;
        }
    }

    showDispensingModal() {
        const modal = new bootstrap.Modal(document.getElementById('dispensingModal'));
        modal.show();
    }

    showSuccessResult(result) {
        const modal = new bootstrap.Modal(document.getElementById('statusModal'));
        
        document.getElementById('status-title').textContent = '¡Compra Exitosa!';
        document.getElementById('status-icon').innerHTML = '<i class="bi bi-check-circle-fill text-success" style="font-size: 3rem;"></i>';
        document.getElementById('status-message').innerHTML = `
            <h5>Producto dispensado</h5>
            <p>Puerta: <strong>${this.selectedDoor}</strong></p>
            <p>Recoge tu producto de la bandeja inferior</p>
            <div class="mt-3">
                <small class="text-muted">Stock restante: ${result.remaining_stock || 'N/A'}</small><br>
                <small class="text-info">Regresando a la pantalla principal en 3 segundos...</small>
            </div>
        `;
        
        modal.show();
        
        // Auto-cerrar después de 3 segundos y regresar a página principal
        setTimeout(() => {
            modal.hide();
            this.clearSelection();
            this.returnToMainScreen();
        }, 3000);
    }

    showErrorResult(error) {
        const modal = new bootstrap.Modal(document.getElementById('statusModal'));
        
        document.getElementById('status-title').textContent = 'Error en la Compra';
        document.getElementById('status-icon').innerHTML = '<i class="bi bi-x-circle-fill text-danger" style="font-size: 3rem;"></i>';
        document.getElementById('status-message').innerHTML = `
            <h5>No se pudo completar la compra</h5>
            <p>${error}</p>
            <div class="mt-3">
                <small class="text-muted">Intenta de nuevo o selecciona otra puerta</small><br>
                <small class="text-info">Regresando a la pantalla principal en 3 segundos...</small>
            </div>
        `;
        
        modal.show();
        
        // Auto-cerrar después de 3 segundos y regresar a página principal
        setTimeout(() => {
            modal.hide();
            this.clearSelection();
            this.returnToMainScreen();
        }, 3000);
    }

    updateDoorAfterPurchase(doorId, result) {
        // Actualizar datos locales inmediatamente para feedback visual
        if (this.doorsData[doorId] && this.doorsData[doorId].product) {
            // Decrementar stock
            if (this.doorsData[doorId].product.stock > 0) {
                this.doorsData[doorId].product.stock -= 1;
            }
            
            // Actualizar estado basado en el nuevo stock
            if (this.doorsData[doorId].product.stock <= 0) {
                this.doorsData[doorId].status = 'out_of_stock';
            } else if (this.doorsData[doorId].product.stock <= this.doorsData[doorId].product.min_stock) {
                this.doorsData[doorId].status = 'low_stock';
            }
            
            // Actualizar visualmente la puerta afectada
            this.updateDoorDisplay(doorId);
        }
        
        console.log(`Stock actualizado localmente para puerta ${doorId}:`, this.doorsData[doorId]);
    }

    updateDoorDisplay(doorId) {
        const doorElement = document.querySelector(`[data-door-id="${doorId}"]`);
        if (!doorElement) return;

        const doorData = this.doorsData[doorId];
        if (!doorData || !doorData.product) return;

        // Actualizar información del producto
        const stockElement = doorElement.querySelector('.stock-info');
        const statusElement = doorElement.querySelector('.door-status');
        
        if (stockElement) {
            stockElement.textContent = `Stock: ${doorData.product.stock}`;
        }
        
        if (statusElement) {
            // Remover clases de estado previas
            doorElement.classList.remove('available', 'out_of_stock', 'low_stock', 'blocked');
            
            // Aplicar nueva clase de estado
            doorElement.classList.add(doorData.status);
            
            // Actualizar texto de estado
            let statusText = 'Disponible';
            if (doorData.status === 'out_of_stock') {
                statusText = 'Sin stock';
            } else if (doorData.status === 'low_stock') {
                statusText = 'Stock bajo';
            } else if (doorData.status === 'blocked') {
                statusText = 'Bloqueada';
            }
            statusElement.textContent = statusText;
        }
    }

    updateSystemStatus() {
        let availableCount = 0;
        let emptyCount = 0;
        
        Object.values(this.doorsData).forEach(door => {
            if (door.status === 'available' && door.product.stock > 0) {
                availableCount++;
            } else if (door.product.stock <= 0) {
                emptyCount++;
            }
        });
        
        // Verificar que los elementos existen antes de actualizarlos
        const availableCountEl = document.getElementById('available-doors-count');
        if (availableCountEl) {
            availableCountEl.textContent = availableCount;
        }
        
        const emptyCountEl = document.getElementById('empty-doors-count');
        if (emptyCountEl) {
            emptyCountEl.textContent = emptyCount;
        }
        
        const statusIndicator = document.getElementById('system-status-indicator');
        if (statusIndicator) {
            if (availableCount === 0) {
                statusIndicator.textContent = 'Sin productos';
                statusIndicator.className = 'badge bg-danger';
            } else {
                statusIndicator.textContent = 'Operativo';
                statusIndicator.className = 'badge bg-success';
            }
        }
    }

    startScreensaverTimer() {
        if (this.screensaverTimeout) {
            clearTimeout(this.screensaverTimeout);
        }
        
        this.screensaverTimeout = setTimeout(() => {
            this.activateScreensaver();
        }, this.screensaverDelay);
    }

    activateScreensaver() {
        const screensaver = document.getElementById('screensaver');
        const mainApp = document.getElementById('main-app');
        
        // Limpiar cualquier selección
        this.clearSelection();
        
        // Mostrar screensaver
        screensaver.style.display = 'flex';
        mainApp.style.display = 'none';
    }

    async loadDoors() {
        try {
            const response = await fetch('/api/doors');
            const data = await response.json();
            
            if (data.success) {
                this.doorsData = data.doors;
                console.log('Datos de puertas actualizados desde servidor');
            } else {
                console.error('Error al cargar datos de puertas:', data.error);
            }
        } catch (error) {
            console.error('Error al comunicar con servidor:', error);
        }
    }

    returnToMainScreen() {
        // Asegurar que todas las selecciones estén limpias
        this.clearSelection();
        
        // Actualizar datos de puertas desde el servidor
        this.loadDoors().then(() => {
            // Regenerar grid con datos actualizados
            this.generateDoorsGrid();
            this.updateSystemStatus();
        });
        
        // Reiniciar temporizador del salvapantallas
        this.startScreensaverTimer();
        
        console.log('Regresando a pantalla principal con datos actualizados');
    }

    // Método para testing GPIO
    async testDispense(doorId) {
        try {
            const response = await fetch(`/api/test/dispense/${doorId}`, {
                method: 'POST'
            });
            const result = await response.json();
            
            if (result.success) {
                console.log(`Test dispensado exitoso para puerta ${doorId}`);
                this.showSuccessResult({
                    remaining_stock: 'Test'
                });
            } else {
                console.error(`Error en test dispensado: ${result.error}`);
            }
        } catch (error) {
            console.error('Error al probar dispensado:', error);
        }
    }

    async checkSecretSequence(doorId) {
        // Verificar si es parte de la secuencia esperada
        const currentPosition = this.restockSequence.length;
        const expectedDoor = this.expectedSequence[currentPosition];
        
        // Si no es la puerta esperada, resetear secuencia (a menos que sea la primera)
        if (doorId !== expectedDoor) {
            if (doorId === this.expectedSequence[0]) {
                // Reiniciar secuencia
                this.restockSequence = [doorId];
                this.showRestockProgress();
                this.resetRestockTimeout();
            } else {
                // Resetear si no es la primera puerta
                this.resetRestockSequence();
            }
            return;
        }
        
        // Agregar a la secuencia
        this.restockSequence.push(doorId);
        this.updateRestockProgress();
        this.resetRestockTimeout();
        
        // Verificar si la secuencia está completa
        if (this.restockSequence.length === this.expectedSequence.length) {
            this.completeRestockSequence();
        }
    }
    
    showRestockProgress() {
        // Eliminar progreso anterior si existe
        this.hideRestockProgress();
        
        this.restockProgressDiv = document.createElement('div');
        this.restockProgressDiv.id = 'restock-progress-touch';
        this.restockProgressDiv.style.cssText = `
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
        
        this.restockProgressDiv.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <i class="bi bi-gear-fill" style="font-size: 24px; margin-right: 10px;"></i>
                <strong style="font-size: 18px;">Modo Restock</strong>
            </div>
            <div style="margin-bottom: 10px;">
                Progreso: <span id="sequence-progress">${this.restockSequence.length}/${this.expectedSequence.length}</span>
            </div>
            <div style="margin-bottom: 10px;">
                Secuencia: <span id="sequence-display" style="font-family: monospace; background: rgba(255,255,255,0.2); padding: 5px; border-radius: 5px;">${this.restockSequence.join(' → ')}</span>
            </div>
            <div style="color: #ffeb3b;">
                Siguiente: <strong id="next-door" style="font-size: 20px;">${this.expectedSequence[this.restockSequence.length] || 'Completo'}</strong>
            </div>
            <div style="margin-top: 15px; font-size: 12px; opacity: 0.8;">
                Toca las puertas en orden: ${this.expectedSequence.join(' → ')}
            </div>
        `;
        
        document.body.appendChild(this.restockProgressDiv);
    }
    
    updateRestockProgress() {
        const progressSpan = document.getElementById('sequence-progress');
        const sequenceSpan = document.getElementById('sequence-display');
        const nextDoorSpan = document.getElementById('next-door');
        
        if (progressSpan) progressSpan.textContent = `${this.restockSequence.length}/${this.expectedSequence.length}`;
        if (sequenceSpan) sequenceSpan.textContent = this.restockSequence.join(' → ');
        if (nextDoorSpan) nextDoorSpan.textContent = this.expectedSequence[this.restockSequence.length] || 'Completo';
    }
    
    hideRestockProgress() {
        if (this.restockProgressDiv) {
            this.restockProgressDiv.remove();
            this.restockProgressDiv = null;
        }
    }
    
    resetRestockTimeout() {
        if (this.restockTimeout) {
            clearTimeout(this.restockTimeout);
        }
        this.restockTimeout = setTimeout(() => {
            this.resetRestockSequence();
        }, 5000); // 5 segundos para completar cada paso
    }
    
    resetRestockSequence() {
        this.restockSequence = [];
        if (this.restockTimeout) {
            clearTimeout(this.restockTimeout);
        }
        this.hideRestockProgress();
    }
    
    completeRestockSequence() {
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
                ¡Modo Restock Activado!
            </div>
            <div style="opacity: 0.9;">
                Redirigiendo a panel de administración...
            </div>
        `;
        
        document.body.appendChild(successDiv);
        
        // Resetear estado
        this.resetRestockSequence();
        
        // Redirigir después de 2 segundos
        setTimeout(() => {
            window.location.href = '/restock';
        }, 2000);
    }

}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.vendingMachine = new VendingMachineSimple();
    console.log('Sistema de máquina expendedora simple inicializado');
});
