/**
 * Sistema de traducciones para la máquina expendedora
 * Soporte para Catalán, Español e Inglés
 */

const TRANSLATIONS = {
    'ca': {
        // Salvapantallas
        'screensaver_title': 'Floradomicilio.com',
        'screensaver_subtitle': 'Prem qualsevol lloc per començar',
        // Interfaz principal
        'welcome': 'Benvingut',
        'select_door': 'Selecciona una porta',
        'click_number': 'Fes clic al número de porta per veure el preu',
        'instructions': 'Toca una porta per veure els detalls del producte',
        // Estados de puertas
        'available': 'Disponible',
        'out_of_stock': 'Sense estoc',
        'blocked': 'Bloquejat',
        'selected': 'Seleccionat',
        'dispensing': 'Dispensant',
        // Modal de producto
        'product_details': 'Detalls del producte',
        'door_number': 'Porta',
        'door': 'Porta',
        'price': 'Preu',
        'stock': 'Estoc',
        'buy_product': 'Comprar producte',
        'cancel': 'Cancel·lar',
        // Métodos de pago
        'payment_method': 'Mètode de pagament',
        'cash': 'Efectiu',
        'card': 'Targeta',
        'contactless': 'Sense contacte',
        'confirm_purchase': 'Confirmar compra',
        'start_payment': 'Iniciar pagament',
        'contactless_payment': 'Pagament sense contacte',
        'total_to_pay': 'Total a pagar',
        'bring_card': 'Acosta la targeta',
        'put_card_near_reader': 'Col·loca la targeta contactless prop del lector TPV',
        'auto_payment': 'El pagament es processarà automàticament',
        'open': 'oberta',
        'take_product': 'Retira el teu producte de la safata',
        'time_to_close': 'Temps restant per tancar la porta',
        'auto_close': 'La porta es tancarà automàticament',
        'price_with_tax': 'Preu amb IVA inclòs',
        'in_stock': 'En estoc',
        'status': 'Estat',
        'accept': 'Acceptar',
        // Pago en efectiu
        'cash_payment': 'Pagament en efectiu',
        'total_amount': 'Import total',
        'inserted_amount': 'Import inserit',
        'remaining_amount': 'Import restant',
        'change': 'Canvi',
        'exact_amount': 'Import exacte',
        'complete_payment': 'Completar pagament',
        // Estados
        'dispensing_product': 'Dispensant producte',
        'please_wait': 'Si us plau, espera mentre preparem el teu producte',
        'success': 'Èxit!',
        'error': 'Error',
        'warning': 'Advertència',
        'info': 'Informació',
        // Sistema
        'system_status': 'Estat del sistema',
        'operational': 'Operatiu',
        'no_stock': 'Sense estoc',
        'available_doors': 'Portes disponibles',
        'restock_needed': 'Necessita reposició',
        // Modo restock
        'restock_mode': 'Mode reposició',
        'restock_activated': 'Mode reposició activat!',
        'sequence_progress': 'Progrés de la seqüència',
        'next_door': 'Següent porta',
        'touch_sequence': 'Toca les portes en ordre',
        'completed': 'Completat',
        'product_dispensed': 'Producte dispensat del slot {doorId}',
        'slot_refilled': 'Slot {doorId} reomplert a 10 unitats',
        'slot_emptied': 'Slot {doorId} buidat',
        'test_gpio': 'Test GPIO',
        'cash_payment_error': 'Error al processar pagament en efectiu',
        'card_not_implemented': 'Pagament amb targeta no implementat encara',
        'contactless_not_available': 'Pagament sense contacte no disponible',
        'product_dispensed_success': 'Producte dispensat. {change}',
        'change_amount': 'Canvi: €{amount}',
        'dispense_error': 'Error al dispensar producte',
        'communication_error': 'Error de comunicació amb el servidor',
        // Monedas
        'coins': 'Monedes',
        'bills': 'Bitllets'
        ,
        // Otros
        'processing_payment': 'Processant pagament...',
        'thank_you': 'Gràcies per la teva compra!',
        'seconds_to_close': 'Segons',
        'see_you_soon': 'Esperem veure’t aviat!',
    },
    'es': {
        // Salvapantallas
        'screensaver_title': 'Floradomicilio.com',
        'screensaver_subtitle': 'Presiona cualquier lugar para comenzar',
        // Interfaz principal
        'welcome': 'Bienvenido',
        'select_door': 'Selecciona una puerta',
        'click_number': 'Haz clic en el número de puerta para ver el precio',
        'instructions': 'Toca una puerta para ver los detalles del producto',
        // Estados de puertas
        'available': 'Disponible',
        'out_of_stock': 'Sin stock',
        'blocked': 'Bloqueado',
        'selected': 'Seleccionado',
        'dispensing': 'Dispensando',
        // Modal de producto
        'product_details': 'Detalles del producto',
        'door_number': 'Puerta',
        'door': 'Puerta',
        'price': 'Precio',
        'stock': 'Stock',
        'buy_product': 'Comprar producto',
        'cancel': 'Cancelar',
        // Métodos de pago
        'payment_method': 'Método de pago',
        'cash': 'Efectivo',
        'card': 'Tarjeta',
        'contactless': 'Sin contacto',
        'confirm_purchase': 'Confirmar compra',
        'start_payment': 'Iniciar pago',
        'contactless_payment': 'Pago sin contacto',
        'total_to_pay': 'Total a pagar',
        'bring_card': 'Acerca tu tarjeta',
        'put_card_near_reader': 'Coloca tu tarjeta contactless cerca del lector TPV',
        'auto_payment': 'El pago se procesará automáticamente',
        'open': 'abierta',
        'take_product': 'Retira tu producto de la bandeja',
        'time_to_close': 'Tiempo restante para cerrar la puerta',
        'auto_close': 'La puerta se cerrará automáticamente',
        'price_with_tax': 'Precio con IVA incluido',
        'in_stock': 'En stock',
        'status': 'Estado',
        'accept': 'Aceptar',
        // Pago en efectivo
        'cash_payment': 'Pago en efectivo',
        'total_amount': 'Importe total',
        'inserted_amount': 'Importe insertado',
        'remaining_amount': 'Importe restante',
        'change': 'Cambio',
        'exact_amount': 'Importe exacto',
        'complete_payment': 'Completar pago',
        // Estados
        'dispensing_product': 'Dispensando producto',
        'please_wait': 'Por favor espera mientras preparamos tu producto',
        'success': '¡Éxito!',
        'error': 'Error',
        'warning': 'Advertencia',
        'info': 'Información',
        // Sistema
        'system_status': 'Estado del sistema',
        'operational': 'Operativo',
        'no_stock': 'Sin stock',
        'available_doors': 'Puertas disponibles',
        'restock_needed': 'Necesita reposición',
        // Modo restock
        'restock_mode': 'Modo restock',
        'restock_activated': '¡Modo restock activado!',
        'sequence_progress': 'Progreso de secuencia',
        'next_door': 'Siguiente puerta',
        'touch_sequence': 'Toca las puertas en orden',
        'completed': 'Completo',
        'product_dispensed': 'Producto dispensado del slot {doorId}',
        'slot_refilled': 'Slot {doorId} rellenado a 10 unidades',
        'slot_emptied': 'Slot {doorId} vaciado',
        'test_gpio': 'Test GPIO',
        'cash_payment_error': 'Error al procesar pago en efectivo',
        'card_not_implemented': 'Pago con tarjeta no implementado aún',
        'contactless_not_available': 'Pago sin contacto no disponible',
        'product_dispensed_success': 'Producto dispensado. {change}',
        'change_amount': 'Cambio: €{amount}',
        'dispense_error': 'Error al dispensar producto',
        'communication_error': 'Error de comunicación con el servidor',
        // Monedas
        'coins': 'Monedas',
        'bills': 'Billetes'
        ,
        // Otros
        'processing_payment': 'Procesando pago...',
        'thank_you': '¡Gracias por tu compra!',
        'seconds_to_close': 'Segundos',
        'see_you_soon': '¡Esperamos verte pronto!'
    ,
    'processing_purchase': 'Procesando compra...'
    },
    'en': {
        // Salvapantallas
        'screensaver_title': 'Floradomicilio.com',
        'screensaver_subtitle': 'Press anywhere to start',
        // Interfaz principal
        'welcome': 'Welcome',
        'select_door': 'Select a door',
        'click_number': 'Click door number to see price',
        'instructions': 'Touch a door to see product details',
        // Estados de puertas
        'available': 'Available',
        'out_of_stock': 'Out of stock',
        'blocked': 'Blocked',
        'selected': 'Selected',
        'dispensing': 'Dispensing',
        // Modal de producto
        'product_details': 'Product details',
        'door_number': 'Door',
        'door': 'Door',
        'price': 'Price',
        'stock': 'Stock',
        'buy_product': 'Buy product',
        'cancel': 'Cancel',
        // Métodos de pago
        'payment_method': 'Payment method',
        'cash': 'Cash',
        'card': 'Card',
        'contactless': 'Contactless',
        'confirm_purchase': 'Confirm purchase',
        'start_payment': 'Start payment',
        'contactless_payment': 'Contactless payment',
        'total_to_pay': 'Total to pay',
        'bring_card': 'Bring your card',
        'put_card_near_reader': 'Place your contactless card near the TPV reader',
        'auto_payment': 'Payment will be processed automatically',
        'open': 'open',
        'take_product': 'Take your product from the tray',
        'time_to_close': 'Time left to close the door',
        'auto_close': 'The door will close automatically',
        'price_with_tax': 'Price including VAT',
        'in_stock': 'In stock',
        'status': 'Status',
        'accept': 'Accept',
        // Pago en efectivo
        'cash_payment': 'Cash payment',
        'total_amount': 'Total amount',
        'inserted_amount': 'Inserted amount',
        'remaining_amount': 'Remaining amount',
        'change': 'Change',
        'exact_amount': 'Exact amount',
        'complete_payment': 'Complete payment',
        // Estados
        'dispensing_product': 'Dispensing product',
        'please_wait': 'Please wait while we prepare your product',
        'success': 'Success!',
        'error': 'Error',
        'warning': 'Warning',
        'info': 'Information',
        // Sistema
        'system_status': 'System status',
        'operational': 'Operational',
        'no_stock': 'No stock',
        'available_doors': 'Available doors',
        'restock_needed': 'Restock needed',
        // Modo restock
        'restock_mode': 'Restock mode',
        'restock_activated': 'Restock mode activated!',
        'sequence_progress': 'Sequence progress',
        'next_door': 'Next door',
        'touch_sequence': 'Touch doors in order',
        'completed': 'Complete',
        'product_dispensed': 'Product dispensed from slot {doorId}',
        'slot_refilled': 'Slot {doorId} refilled to 10 units',
        'slot_emptied': 'Slot {doorId} emptied',
        'test_gpio': 'GPIO Test',
        'cash_payment_error': 'Error processing cash payment',
        'card_not_implemented': 'Card payment not implemented yet',
        'contactless_not_available': 'Contactless payment not available',
        'product_dispensed_success': 'Product dispensed. {change}',
        'change_amount': 'Change: €{amount}',
        'dispense_error': 'Error dispensing product',
        'communication_error': 'Server communication error',
        // Monedas
        'coins': 'Coins',
        'bills': 'Bills'
        ,
        // Others
        'processing_payment': 'Processing payment...',
        'thank_you': 'Thank you for your purchase!',
        'seconds_to_close': 'Seconds',
        'see_you_soon': 'We hope to see you soon!',
        'processing_purchase': 'Processing purchase...'
    }
};

// Función helper para obtener traducciones
function t(key, lang = 'es') {
    return TRANSLATIONS[lang]?.[key] || TRANSLATIONS['es'][key] || key;
}

// Exportar para uso global
if (typeof window !== 'undefined') {
    window.TRANSLATIONS = TRANSLATIONS;
    window.t = t;
}
