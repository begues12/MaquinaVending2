class VendingMachineSimple {
    constructor() {
        this.selectedDoor = null;
        this.doorsData = window.doors || {};
        this.config = window.machineConfig || {};
        this.screensaverTimeout = null;
        this.screensaverDelay = (this.config.display?.screensaver_timeout || 30) * 1000;
        this.currentLanguage = localStorage.getItem('vendingLanguage') || 'es';
        this.languageSelector = null;
        this.doorCountdownInterval = null; // Para el countdown de puerta abierta
        
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
        this.startRedirectMonitoring();
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
        
        // Detectar si el salvapantallas está en modo oscuro
        const isDarkTheme = this.config.machine?.screensaver?.background_style === 'dark';
        
        this.languageSelector = document.createElement('div');
        this.languageSelector.id = 'language-selector';
        
        if (isDarkTheme) {
            this.languageSelector.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: linear-gradient(45deg, #0f0f23, #1a1a2e, #16213e);
                background-size: 400% 400%;
                animation: gradientShift 15s ease infinite, fadeIn 0.3s ease-out;
                z-index: 20000;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                color: white;
            `;
        } else {
            this.languageSelector.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: linear-gradient(45deg, #f8f9fa, #e9ecef, #dee2e6, #ced4da);
                background-size: 400% 400%;
                animation: gradientShift 15s ease infinite, fadeIn 0.3s ease-out;
                z-index: 20000;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                color: #343a40;
            `;
        }
        
        this.languageSelector.innerHTML = `
            <style>
                @keyframes fadeIn {
                    from { opacity: 0; transform: scale(0.9); }
                    to { opacity: 1; transform: scale(1); }
                }
                @keyframes gradientShift {
                    0% { background-position: 0% 50%; }
                    50% { background-position: 100% 50%; }
                    100% { background-position: 0% 50%; }
                }
                .language-btn {
                    ${isDarkTheme ? `
                        background: rgba(255, 255, 255, 0.2);
                        border: 2px solid rgba(0, 212, 255, 0.6);
                        color: white;
                        box-shadow: 0 8px 32px rgba(0, 212, 255, 0.2);
                    ` : `
                        background: rgba(255, 255, 255, 0.8);
                        border: 2px solid #007bff;
                        color: #495057;
                        box-shadow: 0 8px 32px rgba(0, 123, 255, 0.2);
                    `}
                    border-radius: 20px;
                    font-size: 24px;
                    font-weight: 600;
                    padding: 20px 40px;
                    margin: 15px;
                    min-width: 280px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    backdrop-filter: blur(10px);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 15px;
                }
                .language-btn:hover {
                    ${isDarkTheme ? `
                        background: rgba(0, 212, 255, 0.3);
                        border-color: #00d4ff;
                        box-shadow: 0 12px 40px rgba(0, 212, 255, 0.4);
                    ` : `
                        background: #007bff;
                        color: white;
                        border-color: #0056b3;
                        box-shadow: 0 12px 40px rgba(0, 123, 255, 0.4);
                    `}
                    transform: translateY(-5px);
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
                    ${isDarkTheme ? `
                        text-shadow: 0 4px 8px rgba(0, 212, 255, 0.5);
                        color: white;
                    ` : `
                        text-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
                        color: #495057;
                    `}
                }
                .language-subtitle {
                    font-size: 18px;
                    opacity: 0.8;
                    margin-bottom: 40px;
                    text-align: center;
                    max-width: 500px;
                    ${isDarkTheme ? `
                        color: rgba(255, 255, 255, 0.8);
                    ` : `
                        color: #6c757d;
                    `}
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
            
            <div style="position: absolute; bottom: 30px; font-size: 14px; opacity: 0.7; color: ${isDarkTheme ? 'rgba(255, 255, 255, 0.7)' : '#6c757d'};">
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
            background: rgba(255, 255, 255, 0.95);
            color: #28a745;
            border: 2px solid #28a745;
            padding: 30px 50px;
            border-radius: 20px;
            font-size: 24px;
            font-weight: 600;
            z-index: 25000;
            text-align: center;
            box-shadow: 0 15px 35px rgba(40, 167, 69, 0.3);
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
        
        // No mostrar estado de activación - mantener silencioso
    }

    async checkRestockActivationStatus() {
        try {
            const response = await fetch('/api/restock/click/status');
            const result = await response.json();
            
            if (result.success && result.status.phase !== 'idle') {
                const status = result.status;
                let message = '';
                
                switch (status.phase) {
                    case 'first_clicks':
                        message = `🔄 Activación en progreso: ${status.clicks_count}/${status.sequence_config.first_phase} clics`;
                        print(`Activación en progreso: ${status.clicks_count}/${status.sequence_config.first_phase} clics`);
                        break;
                    case 'waiting_pause':
                        const pauseDuration = status.pause_duration || 0;
                        const isValid = status.pause_valid;
                        message = `⏳ Esperando pausa: ${pauseDuration.toFixed(1)}s ${isValid ? '✅' : '⏱️'}`;
                        print(`Esperando pausa: ${pauseDuration.toFixed(1)}s ${isValid ? '✅' : '⏱️'}`);
                        break;
                    case 'second_clicks':
                        message = `🔄 Segunda fase: ${status.clicks_count}/${status.sequence_config.second_phase} clics`;
                        print(`Segunda fase: ${status.clicks_count}/${status.sequence_config.second_phase} clics`);
                        break;
                }
                
                if (message) {
                    this.showRestockNotification(message, 'info', 5000);
                }
            }
        } catch (error) {
            console.error('Error al verificar estado de activación:', error);
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

        // Salvapantallas principal
        const screensaverTitle = document.querySelector('.screensaver-title');
        if (screensaverTitle) {
            screensaverTitle.textContent = t('screensaver_title');
        }
        const screensaverSubtitle = document.querySelector('.screensaver-subtitle');
        if (screensaverSubtitle) {
            screensaverSubtitle.textContent = t('screensaver_subtitle');
        }

        // Salvapantallas de puerta abierta
        const doorOpenSubtitle = document.querySelector('.door-open-subtitle');
        if (doorOpenSubtitle) {
            // Ejemplo: "¡Puerta <span id='door-open-number'></span> Abierta!"
            doorOpenSubtitle.innerHTML = `${t('door_number') || 'Puerta'} <span id="door-open-number"></span> ${t('open') || 'Abierta'}!`;
        }
        const doorOpenMessage = document.querySelector('.door-open-message');
        if (doorOpenMessage) {
            doorOpenMessage.textContent = t('take_product') || 'Retira tu producto de la bandeja';
        }
        const progressText = document.querySelector('.progress-text');
        if (progressText) {
            progressText.textContent = t('time_to_close') || 'Tiempo restante para cerrar la puerta';
        }
        const doorOpenFooter = document.querySelector('.door-open-footer p');
        if (doorOpenFooter) {
            doorOpenFooter.textContent = t('auto_close') || 'La puerta se cerrará automáticamente';
        }

        // Modal de producto
        const modalTitle = document.querySelector('#productModal .modal-title');
        if (modalTitle) {
            modalTitle.innerHTML = `<i class="bi bi-door-open"></i> ${t('door_number') || 'Puerta'} <span id="modal-door-number"></span>`;
        }
        const priceDisplay = document.querySelector('#productModal .price-display p.text-muted');
        if (priceDisplay) {
            priceDisplay.textContent = t('price_with_tax') || 'Precio con IVA incluido';
        }
        const stockBadge = document.getElementById('modal-stock-badge');
        if (stockBadge) {
            if (stockBadge.classList.contains('bg-success')) {
                stockBadge.innerHTML = `<i class="bi bi-check-circle"></i> ${t('in_stock') || 'En stock'}`;
            } else {
                stockBadge.innerHTML = `<i class="bi bi-x-circle"></i> ${t('out_of_stock') || 'Sin stock'}`;
            }
        }
        const cancelBtn = document.querySelector('#productModal .btn-outline-secondary');
        if (cancelBtn) {
            cancelBtn.innerHTML = `<i class="bi bi-x-circle"></i> ${t('cancel') || 'Cancelar'}`;
        }
        const confirmBtn = document.getElementById('modal-continue-purchase');
        if (confirmBtn) {
            confirmBtn.innerHTML = `<i class="bi bi-wifi"></i> ${t('confirm_purchase') || 'Confirmar Compra'}`;
        }

        // Modal de pago contactless
        const contactlessTitle = document.querySelector('#contactlessModal .modal-title');
        if (contactlessTitle) {
            contactlessTitle.textContent = t('contactless_payment') || 'Pago Sin Contacto';
        }
        const contactlessTotal = document.querySelector('#contactlessModal h2');
        if (contactlessTotal) {
            contactlessTotal.innerHTML = `${t('total_to_pay') || 'Total a pagar'}: <span id="contactless-total" class="text-success"></span>`;
        }
        const contactlessAlert = document.querySelector('#contactlessModal .alert-info h4');
        if (contactlessAlert) {
            contactlessAlert.innerHTML = `<i class="bi bi-credit-card"></i> ${t('bring_card') || 'Acerca tu tarjeta'}`;
        }
        const contactlessAlertP = document.querySelector('#contactlessModal .alert-info p');
        if (contactlessAlertP) {
            contactlessAlertP.textContent = t('put_card_near_reader') || 'Coloca tu tarjeta contactless cerca del lector TPV';
        }
        const contactlessAlertSmall = document.querySelector('#contactlessModal .alert-info small');
        if (contactlessAlertSmall) {
            contactlessAlertSmall.textContent = t('auto_payment') || 'El pago se procesará automáticamente';
        }
        const contactlessCancelBtn = document.querySelector('#contactlessModal .btn-secondary');
        if (contactlessCancelBtn) {
            contactlessCancelBtn.textContent = t('cancel') || 'Cancelar';
        }
        const contactlessPayBtn = document.getElementById('contactless-pay-btn');
        if (contactlessPayBtn) {
            contactlessPayBtn.innerHTML = `<i class="bi bi-wifi"></i> ${t('start_payment') || 'Iniciar Pago'}`;
        }

        // Modal de dispensando
        const dispensingTitle = document.querySelector('#dispensingModal h5');
        if (dispensingTitle) {
            dispensingTitle.textContent = t('dispensing_product') || 'Dispensando producto...';
        }
        const dispensingMsg = document.querySelector('#dispensingModal p');
        if (dispensingMsg) {
            dispensingMsg.textContent = t('please_wait') || 'Por favor espera mientras preparamos tu producto';
        }

        // Modal de estado/resultado
        const statusTitle = document.getElementById('status-title');
        if (statusTitle) {
            statusTitle.textContent = t('status') || 'Estado';
        }
        const statusAcceptBtn = document.querySelector('#statusModal .btn-primary');
        if (statusAcceptBtn) {
            statusAcceptBtn.textContent = t('accept') || 'Aceptar';
        }

        // Otros textos pueden añadirse aquí según sea necesario

        console.log(`🌍 Idioma cambiado a: ${this.currentLanguage}`);
    }

    // Función helper para obtener texto traducido
    t(key) {
        return window.t ? window.t(key, this.currentLanguage) : key;
    }

    generateDoorsGrid() {
        const grid = document.getElementById('doors-grid');
        grid.innerHTML = '';

        // Obtener configuración de la grid desde config
        const gridConfig = this.config.display_grid || {
            max_rows: 3,
            max_cols: 5,
            show_empty_spaces: true,
            empty_space_text: "Próximamente"
        };

        // Configurar CSS Grid
        grid.style.gridTemplateColumns = `repeat(${gridConfig.max_cols}, 1fr)`;
        grid.style.gridTemplateRows = `repeat(${gridConfig.max_rows}, 1fr)`;
        grid.style.gap = '15px';
        grid.style.padding = '20px';

        // Crear matriz de posiciones
        const positionMatrix = {};
        
        // Llenar matriz con puertas configuradas
        Object.values(this.doorsData).forEach(door => {
            if (door.position && door.position.row && door.position.col) {
                const key = `${door.position.row}-${door.position.col}`;
                positionMatrix[key] = door;
            }
        });

        // Generar grid completa
        for (let row = 1; row <= gridConfig.max_rows; row++) {
            for (let col = 1; col <= gridConfig.max_cols; col++) {
                const key = `${row}-${col}`;
                const door = positionMatrix[key];
                
                if (door) {
                    // Crear puerta real
                    const doorSquare = this.createDoorSquare(door.id, door);
                    doorSquare.style.gridRow = row;
                    doorSquare.style.gridColumn = col;
                    grid.appendChild(doorSquare);
                } else {
                    // Crear espacio vacío simple
                    const emptySquare = document.createElement('div');
                    emptySquare.className = 'door-square empty-space';
                    emptySquare.style.gridRow = row;
                    emptySquare.style.gridColumn = col;
                    emptySquare.innerHTML = ''; // Completamente vacío
                    grid.appendChild(emptySquare);
                }
            }
        }
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
        } else if (doorData.product && doorData.product.stock <= 0) {
            status = 'out-of-stock';
            statusText = 'Sin stock';
        }
        
        square.classList.add(status);
        
        // Usar display_name como texto principal
        const displayName = doorData.display_name || doorId;
        
        square.innerHTML = `
            <div class="door-number">${displayName}</div>
            <div class="door-status">${statusText}</div>
        `;
        
        // Event listener para selección - SIEMPRE permitir click para secuencia secreta
        square.addEventListener('click', () => this.selectDoor(doorId, doorData));
        
        return square;
    }

    selectDoor(doorId, doorData) {
        // Verificar secuencia secreta primero - SIEMPRE
        this.checkSecretSequence(doorId);
        
        // Solo proceder con la compra si la puerta está disponible y tiene producto
        if (doorData.status !== 'available' || !doorData.product || doorData.product.stock <= 0) {
            // Para puertas no disponibles, solo verificamos secuencia secreta
            console.log(`Puerta ${doorId} no disponible para compra, pero verificada para secuencia secreta`);
            return;
        }
        
        this.clearSelection();
        
        const doorSquare = document.querySelector(`[data-door-id="${doorId}"]`);
        doorSquare.classList.add('selected');
        
        this.selectedDoor = doorId;
        
        this.showProductModal(doorId, doorData);
        
        this.startScreensaverTimer();
    }

    showProductModal(doorId, doorData) {
        if (!doorData.product) {
            console.error(`No hay producto configurado para la puerta ${doorId}`);
            return;
        }
        
        document.getElementById('modal-door-number').textContent = doorId;
        document.getElementById('modal-product-price').textContent = doorData.product.price.toFixed(2);
        
        const stockBadge = document.getElementById('modal-stock-badge');
        if (doorData.product.stock > 0) {
            stockBadge.innerHTML = '<i class="bi bi-check-circle"></i> En stock';
            stockBadge.className = 'badge bg-success fs-6';
        } else {
            stockBadge.innerHTML = '<i class="bi bi-x-circle"></i> Sin stock';
            stockBadge.className = 'badge bg-danger fs-6';
        }
        
        const modal = new bootstrap.Modal(document.getElementById('productModal'));
        modal.show();
        
        this.currentModal = modal;
    }

    showDoorInfo(doorId, doorData) {
    }

    clearSelection() {

        document.querySelectorAll('.door-square.selected').forEach(square => {
            square.classList.remove('selected');
        });
        
        if (this.currentModal) {
            this.currentModal.hide();
            this.currentModal = null;
        }
        
        this.selectedDoor = null;
    }

    setupEventListeners() {

        document.getElementById('modal-continue-purchase').addEventListener('click', () => {
            this.showContactlessModal();
        });
        
        document.getElementById('productModal').addEventListener('hidden.bs.modal', () => {
            this.clearSelection();
            this.startScreensaverTimer();
        });

        document.getElementById('contactless-pay-btn').addEventListener('click', () => {
            this.processContactlessPayment();
        });

        document.addEventListener('click', (e) => {
            if (!document.querySelector('.modal.show') && 
                document.getElementById('main-app').style.display !== 'none') {
                this.processRestockActivationClick();
            }
        });

        ['mousemove', 'keydown', 'touchstart'].forEach(event => {
            document.addEventListener(event, () => {
                this.startScreensaverTimer();
            });
        });

        // Botón de prueba para salvapantallas de puerta (desarrollo)
        const devDoorTest = document.getElementById('dev-door-test');
        if (devDoorTest) {
            devDoorTest.addEventListener('click', () => {
                console.log('Probando salvapantallas de puerta abierta...');
                this.selectedDoor = 'A1'; // Simular puerta seleccionada
                this.showDoorOpenScreensaver('A1', 10); // 10 segundos de prueba
            });
            
            // Mostrar en modo desarrollo
            if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                devDoorTest.style.display = 'block';
            }
        }
    }

    async processRestockActivationClick() {
        try {
            const response = await fetch('/api/restock/click', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.handleRestockActivationResponse(result);
            } else {
                console.error('Error en activación de restock:', result.error);
            }
        } catch (error) {
            console.error('Error al procesar clic de activación:', error);
        }
    }

    handleRestockActivationResponse(result) {
        
        switch (result.phase) {
            case 'first_clicks':

                break;
                
            case 'waiting_pause':


                break;
                
            case 'second_clicks':

       
            case 'completed':

            if (result.restock_activated) {
                  
                    setTimeout(() => {
                        window.location.href = '/restock';
                    }, 1000);
                }
                break;
                
            case 'failed':

                break;
        }
    }

    showRestockNotification(message, type = 'info', duration = 3000) {
        // Crear contenedor de notificación si no existe
        let container = document.getElementById('restock-notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'restock-notification-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                pointer-events: none;
            `;
            document.body.appendChild(container);
        }

        // Crear notificación
        const notification = document.createElement('div');
        notification.className = `restock-notification restock-${type}`;
        notification.style.cssText = `
            background: ${type === 'success' ? '#28a745' : 
                        type === 'error' ? '#dc3545' : 
                        type === 'warning' ? '#ffc107' : '#007bff'};
            color: ${type === 'warning' ? '#000' : '#fff'};
            padding: 15px 25px;
            border-radius: 10px;
            margin-bottom: 10px;
            font-size: 16px;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            transform: translateX(100%);
            transition: all 0.3s ease;
            pointer-events: auto;
            max-width: 350px;
            word-wrap: break-word;
        `;
        notification.textContent = message;

        container.appendChild(notification);

        // Animar entrada
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 10);

        // Programar eliminación
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, duration);
    }

    hideRestockNotification() {
        const container = document.getElementById('restock-notification-container');
        if (container) {
            container.innerHTML = '';
        }
    }

    showContactlessModal() {
        if (!this.selectedDoor) return;
        
        const doorData = this.doorsData[this.selectedDoor];
        if (!doorData.product) {
            console.error(`No hay producto configurado para la puerta ${this.selectedDoor}`);
            return;
        }
        
        document.getElementById('contactless-total').textContent = `€${doorData.product.price.toFixed(2)}`;
        
        const modal = new bootstrap.Modal(document.getElementById('contactlessModal'));
        modal.show();
        
        this.startScreensaverTimer();
    }

    // Mostrar overlay de bloqueo TPV
    showTPVBlockOverlay() {
        const overlay = document.getElementById('tpv-block-overlay');
        if (overlay) overlay.style.display = 'block';
    }
    // Ocultar overlay de bloqueo TPV
    hideTPVBlockOverlay() {
        const overlay = document.getElementById('tpv-block-overlay');
        if (overlay) overlay.style.display = 'none';
    }

    async processContactlessPayment() {
        if (!this.selectedDoor) return;

        const doorData = this.doorsData[this.selectedDoor];
        if (!doorData.product) {
            console.error(`No hay producto configurado para la puerta ${this.selectedDoor}`);
            return;
        }
        
        try {
            // Mostrar overlay de bloqueo
            this.showTPVBlockOverlay();
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
                
                // Ocultar overlay de bloqueo
                this.hideTPVBlockOverlay();
                
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
            // Ocultar overlay de bloqueo
            this.hideTPVBlockOverlay();
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
        // Ocultar cualquier modal abierto
        const openModals = document.querySelectorAll('.modal.show');
        openModals.forEach(modal => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        });
        
        // Obtener tiempo de apertura de puerta desde la configuración
        const doorData = this.doorsData[this.selectedDoor];
        let doorOpenTime = 10; // Tiempo por defecto en segundos
        
        if (doorData && doorData.open_time) {
            doorOpenTime = Math.round(doorData.open_time);
        }
        
        console.log('Datos de puerta:', doorData);
        console.log('Tiempo de apertura configurado:', doorOpenTime, 'segundos');
        
        // Mostrar salvapantallas de puerta abierta
        this.showDoorOpenScreensaver(this.selectedDoor, doorOpenTime);
    }

    // Mostrar salvapantallas de puerta abierta con countdown
    showDoorOpenScreensaver(doorId, openTimeSeconds) {
        // Ocultar la aplicación principal
        document.getElementById('main-app').style.display = 'none';
        
        // Configurar y mostrar salvapantallas de puerta abierta
        // Usar door-open-number que es el que existe en el HTML
        document.getElementById('door-open-number').textContent = this.doorsData[doorId]?.display_name || doorId;
        document.getElementById('door-timer-seconds').textContent = openTimeSeconds;
        
        const doorOpenScreen = document.getElementById('door-open-screensaver');
        doorOpenScreen.style.display = 'flex';
        
        // Detener el timer del salvapantallas normal
        if (this.screensaverTimeout) {
            clearTimeout(this.screensaverTimeout);
            this.screensaverTimeout = null;
        }
        
        // Iniciar countdown
        this.startDoorCountdown(openTimeSeconds);
        
        console.log(`Mostrando salvapantallas de puerta abierta para ${doorId} por ${openTimeSeconds} segundos`);
    }

    // Iniciar countdown de puerta abierta
    startDoorCountdown(totalSeconds) {
        console.log('Iniciando countdown con', totalSeconds, 'segundos');
        
        // Limpiar countdown previo si existe
        if (this.doorCountdownInterval) {
            clearInterval(this.doorCountdownInterval);
            console.log('Limpiando countdown previo...');
        }
        
        let remainingSeconds = totalSeconds;
        const timerElement = document.getElementById('door-timer-seconds');
        const progressBar = document.getElementById('door-progress-bar');
        
        if (!timerElement || !progressBar) {
            console.error('No se encontraron elementos del timer:', {
                timerElement: !!timerElement,
                progressBar: !!progressBar
            });
            return;
        }
        
        // Configurar valores iniciales
        timerElement.textContent = remainingSeconds;
        progressBar.style.width = '100%';
        progressBar.style.background = '#0d6efd';
        
        console.log('Elementos encontrados, iniciando interval...');
        
        this.doorCountdownInterval = setInterval(() => {
            remainingSeconds--;
            console.log('Countdown:', remainingSeconds);
            
            // Actualizar timer
            timerElement.textContent = remainingSeconds;
            
            // Actualizar barra de progreso
            const progressPercentage = (remainingSeconds / totalSeconds) * 100;
            progressBar.style.width = `${progressPercentage}%`;
            
            // Cambiar color de la barra según el tiempo restante
            if (progressPercentage > 50) {
                progressBar.style.background = '#0d6efd';
            } else if (progressPercentage > 25) {
                progressBar.style.background = '#ffc107';
            } else {
                progressBar.style.background = '#dc3545';
            }
            
            // Cuando llega a 0, ocultar salvapantallas y mostrar agradecimiento
            if (remainingSeconds <= 0) {
                console.log('Countdown terminado, limpiando...');
                clearInterval(this.doorCountdownInterval);
                this.doorCountdownInterval = null;
                // Llamada para cerrar la puerta en el backend
                if (this.selectedDoor) {
                    fetch(`/api/door/close/${this.selectedDoor}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        console.log('Puerta cerrada:', data);
                    })
                    .catch(error => {
                        console.error('Error al cerrar la puerta:', error);
                    });
                }
                this.hideDoorOpenScreensaver();
                
                // Mostrar salvapantallas de agradecimiento breve
                setTimeout(() => {
                    this.showBriefThankYou();
                }, 500);
            }
        }, 1000);
    }

    // Ocultar salvapantallas de puerta abierta
    hideDoorOpenScreensaver() {
        const doorOpenScreen = document.getElementById('door-open-screensaver');
        doorOpenScreen.style.display = 'none';
        
        // Limpiar countdown si está activo
        if (this.doorCountdownInterval) {
            clearInterval(this.doorCountdownInterval);
            this.doorCountdownInterval = null;
            console.log('Countdown limpiado al ocultar salvapantallas');
        }
        
        console.log('Ocultando salvapantallas de puerta abierta');
    }

    // Mostrar breve mensaje de agradecimiento
    showBriefThankYou() {
        // Crear overlay temporal
        const thankYouOverlay = document.createElement('div');
        thankYouOverlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 50%, #dee2e6 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            animation: fadeIn 0.5s ease-out;
        `;
        
        thankYouOverlay.innerHTML = `
            <div style="text-align: center; color: #212529;">
                <i class="bi bi-check-circle-fill" style="font-size: 4rem; margin-bottom: 20px; color: #28a745;"></i>
                <h1 style="font-size: 3rem; font-weight: bold; margin-bottom: 10px; color: #212529;">¡Gracias!</h1>
                <p style="font-size: 1.5rem; color: #6c757d;">Esperamos verte pronto</p>
            </div>
        `;
        
        document.body.appendChild(thankYouOverlay);
        
        // Quitar después de 3 segundos y volver al salvapantallas principal
        setTimeout(() => {
            thankYouOverlay.remove();
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
            if (door.status === 'available' && door.product && door.product.stock > 0) {
                availableCount++;
            } else if (!door.product || door.product.stock <= 0) {
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

        // Cerrar cualquier modal abierto
        document.querySelectorAll('.modal.show').forEach(modal => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) bsModal.hide();
        });

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
        
        // Ocultar el salvapantallas de puerta abierta si está visible
        const doorOpenScreen = document.getElementById('door-open-screensaver');
        if (doorOpenScreen) {
            doorOpenScreen.style.display = 'none';
        }
        
        // Mostrar inmediatamente el salvapantallas principal
        const screensaver = document.getElementById('screensaver');
        const mainApp = document.getElementById('main-app');
        
        screensaver.style.display = 'flex';
        mainApp.style.display = 'none';
        
        // Actualizar datos de puertas desde el servidor
        this.loadDoors().then(() => {
            // Regenerar grid con datos actualizados
            this.generateDoorsGrid();
            this.updateSystemStatus();
        });
        
        console.log('Regresando al salvapantallas principal');
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

    // Monitorear redirecciones desde botón GPIO
    startRedirectMonitoring() {
        console.log('Iniciando monitoreo de redirecciones GPIO...');
        
        // Verificar cada 2 segundos si hay una solicitud de redirección
        setInterval(async () => {
            try {
                const response = await fetch('/api/restock/redirect-status');
                if (response.ok) {
                    const data = await response.json();
                    
                    // Debug temporal
                    if (data.redirect_requested) {
                        console.log('Estado de redirección:', data);
                    }
                    
                    if (data.redirect_requested && data.success) {
                        console.log('Redirección solicitada por botón GPIO, dirigiendo a restock...');
                        
                        // Limpiar la solicitud de redirección
                        await fetch('/api/restock/clear-redirect', { method: 'POST' });
                        
                        // Redirigir a la página de restock
                        window.location.href = '/restock';
                    }
                }
            } catch (error) {
                console.error('Error verificando redirección GPIO:', error);
            }
        }, 2000);
    }

    // Inicializar botón flotante de desarrollo
    async initDevelopmentButton() {
        try {
            // Verificar si estamos en modo desarrollo
            const response = await fetch('/api/config/development');
            if (response.ok) {
                const data = await response.json();
                
                if (data.development_mode) {
                    const devButton = document.getElementById('dev-gpio-button');
                    if (devButton) {
                        devButton.style.display = 'flex';
                        devButton.addEventListener('click', this.simulateGpioButton.bind(this));
                        console.log('Botón de desarrollo GPIO activado');
                    }
                }
            }
        } catch (error) {
            console.error('Error inicializando botón de desarrollo:', error);
        }
    }

    // Simular presión del botón GPIO
    async simulateGpioButton() {
        const button = document.getElementById('dev-gpio-button');
        
        try {
            // Efecto visual de presión
            button.classList.add('pressed');
            
            // Llamar al endpoint de simulación
            const response = await fetch('/api/test/gpio-button', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('Botón GPIO Pin 16 simulado:', data.message);
                
                // Mostrar notificación temporal con número de pin
                this.showDevNotification('GPIO Pin 16 simulado!', 'success');
            } else {
                const error = await response.json();
                console.error('Error simulando GPIO Pin 16:', error.error);
                this.showDevNotification('Error al simular Pin 16', 'error');
            }
            
        } catch (error) {
            console.error('Error en simulación de GPIO Pin 16:', error);
            this.showDevNotification('Error de conexión', 'error');
        } finally {
            // Quitar efecto visual después de 500ms
            setTimeout(() => {
                button.classList.remove('pressed');
            }, 500);
        }
    }

    // Mostrar notificación de desarrollo
    showDevNotification(message, type = 'info') {
        // Crear notificación temporal
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#007bff'};
            color: white;
            border-radius: 4px;
            z-index: 1001;
            font-size: 14px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transition: all 0.3s ease;
            transform: translateX(400px);
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Animar entrada
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 10);
        
        // Quitar después de 3 segundos
        setTimeout(() => {
            notification.style.transform = 'translateX(400px)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.vendingMachine = new VendingMachineSimple();
    
    // Iniciar monitoreo de botón GPIO para redirección
    window.vendingMachine.startRedirectMonitoring();
    
    // Inicializar botón de desarrollo si estamos en modo desarrollo
    window.vendingMachine.initDevelopmentButton();
    
    console.log('Sistema de máquina expendedora simple inicializado con monitoreo GPIO');
});
