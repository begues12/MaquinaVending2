"""
Sistema de pagos integrado
Soporta Stripe y PayPal
"""
import logging
import stripe
import paypalrestsdk
from typing import Dict, Any, Optional
from config import Config

logger = logging.getLogger(__name__)

class PaymentProcessor:
    def __init__(self):
        self.stripe_enabled = bool(Config.STRIPE_SECRET_KEY)
        self.paypal_enabled = bool(Config.PAYPAL_CLIENT_ID and Config.PAYPAL_CLIENT_SECRET)
        
        self._init_stripe()
        self._init_paypal()
    
    def _init_stripe(self):
        """Inicializar Stripe"""
        if self.stripe_enabled:
            stripe.api_key = Config.STRIPE_SECRET_KEY
            logger.info("Stripe inicializado correctamente")
        else:
            logger.warning("Stripe no configurado - faltan claves API")
    
    def _init_paypal(self):
        """Inicializar PayPal"""
        if self.paypal_enabled:
            paypalrestsdk.configure({
                "mode": Config.PAYPAL_MODE,
                "client_id": Config.PAYPAL_CLIENT_ID,
                "client_secret": Config.PAYPAL_CLIENT_SECRET
            })
            logger.info("PayPal inicializado correctamente")
        else:
            logger.warning("PayPal no configurado - faltan credenciales")
    
    def create_stripe_payment_intent(self, amount: int, currency: str = 'eur', 
                                   description: str = 'Compra en máquina expendedora') -> Dict[str, Any]:
        """Crear un payment intent de Stripe"""
        if not self.stripe_enabled:
            return {'error': 'Stripe no está configurado'}
        
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,  # Cantidad en centavos
                currency=currency,
                description=description,
                automatic_payment_methods={'enabled': True}
            )
            
            return {
                'success': True,
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Error de Stripe: {e}")
            return {'error': str(e)}
    
    def confirm_stripe_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """Confirmar un pago de Stripe"""
        if not self.stripe_enabled:
            return {'error': 'Stripe no está configurado'}
        
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if intent.status == 'succeeded':
                return {
                    'success': True,
                    'status': 'completed',
                    'amount': intent.amount,
                    'currency': intent.currency
                }
            else:
                return {
                    'success': False,
                    'status': intent.status
                }
                
        except stripe.error.StripeError as e:
            logger.error(f"Error al confirmar pago Stripe: {e}")
            return {'error': str(e)}
    
    def create_paypal_payment(self, amount: float, currency: str = 'EUR',
                            description: str = 'Compra en máquina expendedora') -> Dict[str, Any]:
        """Crear un pago de PayPal"""
        if not self.paypal_enabled:
            return {'error': 'PayPal no está configurado'}
        
        try:
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {"payment_method": "paypal"},
                "redirect_urls": {
                    "return_url": "http://localhost:5000/payment/paypal/success",
                    "cancel_url": "http://localhost:5000/payment/paypal/cancel"
                },
                "transactions": [{
                    "item_list": {
                        "items": [{
                            "name": "Producto de máquina expendedora",
                            "sku": "vending_product",
                            "price": str(amount),
                            "currency": currency,
                            "quantity": 1
                        }]
                    },
                    "amount": {
                        "total": str(amount),
                        "currency": currency
                    },
                    "description": description
                }]
            })
            
            if payment.create():
                approval_url = None
                for link in payment.links:
                    if link.rel == "approval_url":
                        approval_url = link.href
                        break
                
                return {
                    'success': True,
                    'payment_id': payment.id,
                    'approval_url': approval_url
                }
            else:
                logger.error(f"Error al crear pago PayPal: {payment.error}")
                return {'error': payment.error}
                
        except Exception as e:
            logger.error(f"Error PayPal: {e}")
            return {'error': str(e)}
    
    def execute_paypal_payment(self, payment_id: str, payer_id: str) -> Dict[str, Any]:
        """Ejecutar un pago de PayPal"""
        if not self.paypal_enabled:
            return {'error': 'PayPal no está configurado'}
        
        try:
            payment = paypalrestsdk.Payment.find(payment_id)
            
            if payment.execute({"payer_id": payer_id}):
                return {
                    'success': True,
                    'status': 'completed',
                    'payment_id': payment_id
                }
            else:
                logger.error(f"Error al ejecutar pago PayPal: {payment.error}")
                return {'error': payment.error}
                
        except Exception as e:
            logger.error(f"Error al ejecutar pago PayPal: {e}")
            return {'error': str(e)}
    
    def process_cash_payment(self, amount: float, received: float) -> Dict[str, Any]:
        """Simular procesamiento de pago en efectivo"""
        if received < amount:
            return {
                'success': False,
                'error': 'Monto insuficiente',
                'amount_needed': amount,
                'amount_received': received,
                'missing': amount - received
            }
        
        change = received - amount
        
        return {
            'success': True,
            'status': 'completed',
            'amount': amount,
            'received': received,
            'change': change
        }
    
    def get_payment_methods(self) -> Dict[str, bool]:
        """Obtener métodos de pago disponibles"""
        return {
            'stripe': self.stripe_enabled,
            'paypal': self.paypal_enabled,
            'cash': True  # Siempre disponible en una máquina expendedora
        }


# Instancia global del procesador de pagos
payment_processor = PaymentProcessor()
