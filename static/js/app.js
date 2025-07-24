/**
 * JavaScript para la máquina expendedora
 * Maneja la interfaz de usuario, pagos y comunicación con el backend
 */

class VendingMachine {
    constructor() {
        this.selectedProduct = null;
        this.stripe = null;
        this.stripeElements = null;
        this.stripeCard = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadSystemStatus();
        this.initStripe();
        
        // Actualizar estado cada 30 segundos
        setInterval(() => this.loadSystemStatus(), 30000);
    }

    setupEventListeners() {
        // Selección de productos
        document.querySelectorAll('.select-product-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const card = e.target.closest('.product-card');
                this.selectProduct(card);
            });
        });

        // Métodos de pago
        document.querySelectorAll('.payment-method-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const method = e.target.dataset.method;
                this.processPayment(method);
            });
        });

        // Cancelar selección
        document.getElementById('cancel-selection').addEventListener('click', () => {
            this.cancelSelection();
        });

        // Pago en efectivo
        document.getElementById('cash-received').addEventListener('input', (e) => {
            this.calculateChange();
        });

        document.getElementById('cash-pay-btn').addEventListener('click', () => {
            this.processCashPayment();
        });

        // Pago con Stripe
        document.getElementById('stripe-pay-btn').addEventListener('click', () => {
            this.processStripePayment();
        });
    }

    initStripe() {
        // Inicializar Stripe solo si está disponible
        if (window.Stripe && document.querySelector('[data-method="stripe"]')) {
            this.stripe = Stripe('pk_test_tu_clave_publica_stripe'); // Usar variable de entorno
            this.stripeElements = this.stripe.elements();
            
            this.stripeCard = this.stripeElements.create('card', {
                style: {
                    base: {
                        fontSize: '16px',
                        color: '#424770',
                        '::placeholder': {
                            color: '#aab7c4',
                        },
                    },
                },
            });
        }
    }

    selectProduct(card) {
        // Remover selección anterior
        document.querySelectorAll('.product-card').forEach(c => c.classList.remove('selected'));
        
        // Seleccionar nuevo producto
        card.classList.add('selected');
        
        this.selectedProduct = {
            id: card.dataset.id,
            slot: card.dataset.slot,
            price: parseFloat(card.dataset.price),
            name: card.querySelector('.card-title').textContent,
            description: card.querySelector('.card-text').textContent
        };

        this.showSelectedProduct();
    }

    showSelectedProduct() {
        const selectedDiv = document.getElementById('selected-product');
        const paymentDiv = document.getElementById('payment-methods');

        if (this.selectedProduct) {
            document.getElementById('selected-name').textContent = this.selectedProduct.name;
            document.getElementById('selected-description').textContent = this.selectedProduct.description;
            document.getElementById('selected-price').textContent = `€${this.selectedProduct.price.toFixed(2)}`;
            document.getElementById('selected-slot').textContent = this.selectedProduct.slot;

            selectedDiv.style.display = 'block';
            paymentDiv.style.display = 'block';
            
            selectedDiv.classList.add('fade-in');
            paymentDiv.classList.add('fade-in');
        }
    }

    cancelSelection() {
        document.querySelectorAll('.product-card').forEach(c => c.classList.remove('selected'));
        document.getElementById('selected-product').style.display = 'none';
        document.getElementById('payment-methods').style.display = 'none';
        this.selectedProduct = null;
    }

    async processPayment(method) {
        if (!this.selectedProduct) {
            this.showMessage('Error', 'No hay producto seleccionado', 'danger');
            return;
        }

        switch (method) {
            case 'stripe':
                this.showStripeModal();
                break;
            case 'paypal':
                await this.processPayPalPayment();
                break;
            case 'cash':
                this.showCashModal();
                break;
        }
    }

    showStripeModal() {
        const modal = new bootstrap.Modal(document.getElementById('stripeModal'));
        
        // Montar el elemento de tarjeta si no está montado
        if (this.stripeCard && !this.stripeCard._mounted) {
            this.stripeCard.mount('#stripe-card-element');
        }
        
        modal.show();
    }

    async processStripePayment() {
        if (!this.stripe || !this.stripeCard) {
            this.showMessage('Error', 'Stripe no está disponible', 'danger');
            return;
        }

        try {
            // Deshabilitar botón
            const payBtn = document.getElementById('stripe-pay-btn');
            payBtn.disabled = true;
            payBtn.innerHTML = '<span class="spinner"></span> Procesando...';

            // Crear payment intent
            const response = await fetch('/api/payment/stripe/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    amount: this.selectedProduct.price,
                    description: `${this.selectedProduct.name} - Slot ${this.selectedProduct.slot}`
                })
            });

            const { client_secret, error } = await response.json();

            if (error) {
                throw new Error(error);
            }

            // Confirmar pago
            const { error: stripeError, paymentIntent } = await this.stripe.confirmCardPayment(client_secret, {
                payment_method: {
                    card: this.stripeCard
                }
            });

            if (stripeError) {
                throw new Error(stripeError.message);
            }

            // Confirmar en el backend
            const confirmResponse = await fetch('/api/payment/stripe/confirm', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    payment_intent_id: paymentIntent.id,
                    slot: this.selectedProduct.slot
                })
            });

            const result = await confirmResponse.json();

            if (result.success) {
                bootstrap.Modal.getInstance(document.getElementById('stripeModal')).hide();
                this.showMessage('¡Éxito!', 'Pago procesado correctamente. Dispensando producto...', 'success');
                this.cancelSelection();
                this.refreshProducts();
            } else {
                throw new Error(result.error || 'Error al procesar el pago');
            }

        } catch (error) {
            document.getElementById('stripe-errors').textContent = error.message;
        } finally {
            // Rehabilitar botón
            const payBtn = document.getElementById('stripe-pay-btn');
            payBtn.disabled = false;
            payBtn.innerHTML = 'Pagar';
        }
    }

    async processPayPalPayment() {
        try {
            const response = await fetch('/api/payment/paypal/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    amount: this.selectedProduct.price,
                    description: `${this.selectedProduct.name} - Slot ${this.selectedProduct.slot}`
                })
            });

            const result = await response.json();

            if (result.success && result.approval_url) {
                // Abrir ventana de PayPal
                window.open(result.approval_url, 'paypal', 'width=600,height=600');
                this.showMessage('PayPal', 'Completar pago en la ventana de PayPal', 'info');
            } else {
                throw new Error(result.error || 'Error al crear pago PayPal');
            }

        } catch (error) {
            this.showMessage('Error', error.message, 'danger');
        }
    }

    showCashModal() {
        document.getElementById('cash-price').textContent = `€${this.selectedProduct.price.toFixed(2)}`;
        document.getElementById('cash-received').value = '';
        document.getElementById('cash-change').style.display = 'none';
        
        const modal = new bootstrap.Modal(document.getElementById('cashModal'));
        modal.show();
    }

    calculateChange() {
        const received = parseFloat(document.getElementById('cash-received').value) || 0;
        const price = this.selectedProduct.price;
        const changeDiv = document.getElementById('cash-change');
        const payBtn = document.getElementById('cash-pay-btn');

        if (received >= price) {
            const change = received - price;
            document.getElementById('change-amount').textContent = `€${change.toFixed(2)}`;
            changeDiv.style.display = 'block';
            payBtn.disabled = false;
        } else {
            changeDiv.style.display = 'none';
            payBtn.disabled = true;
        }
    }

    async processCashPayment() {
        const received = parseFloat(document.getElementById('cash-received').value);
        
        if (!received || received < this.selectedProduct.price) {
            this.showMessage('Error', 'Cantidad insuficiente', 'danger');
            return;
        }

        try {
            const response = await fetch('/api/payment/cash', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    amount: this.selectedProduct.price,
                    received: received,
                    slot: this.selectedProduct.slot
                })
            });

            const result = await response.json();

            if (result.success) {
                bootstrap.Modal.getInstance(document.getElementById('cashModal')).hide();
                
                const change = result.change > 0 ? `Cambio: €${result.change.toFixed(2)}` : 'Sin cambio';
                this.showMessage('¡Pago Completado!', `${change}. Dispensando producto...`, 'success');
                
                this.cancelSelection();
                this.refreshProducts();
            } else {
                throw new Error(result.error || 'Error al procesar pago en efectivo');
            }

        } catch (error) {
            this.showMessage('Error', error.message, 'danger');
        }
    }

    showMessage(title, message, type = 'info') {
        document.getElementById('status-title').textContent = title;
        document.getElementById('status-message').innerHTML = `
            <div class="alert alert-${type}" role="alert">
                ${message}
            </div>
        `;
        
        const modal = new bootstrap.Modal(document.getElementById('statusModal'));
        modal.show();
    }

    async loadSystemStatus() {
        try {
            const response = await fetch('/api/system/status');
            const data = await response.json();

            if (data.success) {
                this.updateSystemStatus(data);
            }
        } catch (error) {
            console.error('Error al cargar estado del sistema:', error);
        }
    }

    updateSystemStatus(data) {
        const statusDiv = document.getElementById('system-status');
        
        const html = `
            <div class="status-item">
                <span>Plataforma:</span>
                <span>${data.platform} <span class="status-indicator status-online"></span></span>
            </div>
            <div class="status-item">
                <span>GPIO:</span>
                <span>${data.gpio.gpio_enabled ? 'Activo' : 'Simulación'} 
                    <span class="status-indicator ${data.gpio.gpio_enabled ? 'status-online' : 'status-warning'}"></span>
                </span>
            </div>
            <div class="status-item">
                <span>Stripe:</span>
                <span>${data.payments.stripe ? 'Activo' : 'Inactivo'} 
                    <span class="status-indicator ${data.payments.stripe ? 'status-online' : 'status-offline'}"></span>
                </span>
            </div>
            <div class="status-item">
                <span>PayPal:</span>
                <span>${data.payments.paypal ? 'Activo' : 'Inactivo'} 
                    <span class="status-indicator ${data.payments.paypal ? 'status-online' : 'status-offline'}"></span>
                </span>
            </div>
        `;
        
        statusDiv.innerHTML = html;
    }

    async refreshProducts() {
        try {
            const response = await fetch('/api/products');
            const data = await response.json();

            if (data.success) {
                // Recargar la página para actualizar el stock
                // En una implementación más avanzada, solo actualizarías los elementos afectados
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            }
        } catch (error) {
            console.error('Error al actualizar productos:', error);
        }
    }

    // Método para testing del GPIO
    async testDispense(slot) {
        try {
            const response = await fetch(`/api/dispense/${slot}`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showMessage('Test GPIO', `Producto dispensado del slot ${slot}`, 'success');
            } else {
                this.showMessage('Error', result.error, 'danger');
            }
        } catch (error) {
            this.showMessage('Error', error.message, 'danger');
        }
    }
}

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.vendingMachine = new VendingMachine();
    
    // Añadir algunos shortcuts para testing (solo en desarrollo)
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log('Modo desarrollo activado');
        console.log('Usa vendingMachine.testDispense("slot_1") para probar GPIO');
        
        // Shortcut para test rápido
        window.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key >= '1' && e.key <= '4') {
                e.preventDefault();
                const slot = `slot_${e.key}`;
                window.vendingMachine.testDispense(slot);
            }
        });
    }
});
