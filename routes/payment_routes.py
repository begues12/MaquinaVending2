import logging
import time
from flask import Blueprint, request, jsonify
from database import db_manager
from controllers.tpv_controller import TPVController

# Crear blueprint
payment_bp = Blueprint("payment", __name__)
logger = logging.getLogger(__name__)

# Inicializar controlador TPV
tpv_controller = TPVController()

@payment_bp.route("/api/process_payment", methods=["POST"])
def process_payment():
    """Iniciar proceso de pago contactless en el TPV o consultar estado si se envía payment_id"""
    data = request.get_json()
    logger.info(f"Datos recibidos en /api/process_payment: {data}")
    
    if not data:
        return jsonify({"success": False, "error": "No se recibieron datos"}), 400
    
    # Si se envía payment_id, redirigir a consulta de estado
    if "payment_id" in data:
        logger.info("Detectado payment_id en /api/process_payment - redirigiendo a consulta de estado")
        payment_id = data["payment_id"]
        door_id = data.get("door_id")
        
        try:
            # Redirigir internamente a la función de consulta de estado
            response = tpv_controller.check_payment_status(payment_id)
            logger.info(f"Respuesta del TPV controller: {response}")
            
            # Procesar respuesta completa si el pago fue aprobado
            if response.get("success") and response.get("status") == "approved" and door_id:
                try:
                    product = db_manager.get_product_by_door(door_id)
                    if product:
                        # Registrar transacción en base de datos
                        transaction_id = response.get("transaction_id", f"TXN_{door_id}_{int(time.time())}")
                        sale_id = db_manager.create_sale(
                            door_id=door_id,
                            payment_method="contactless",
                            amount=product["price"],
                            product_id=product["id"],
                            payment_id=payment_id
                        )
                        
                        if sale_id:
                            # Actualizar estado de la venta a completada
                            db_manager.update_sale_status(sale_id, "completed", dispensed=True)
                        
                        # Actualizar stock
                        db_manager.decrease_stock(door_id, 1)
                        
                        response.update({
                            "message": "Pago aprobado - producto a dispensar",
                            "transaction_id": transaction_id,
                            "amount": product["price"],
                            "door_id": door_id,
                            "hardware_success": True,
                            "redirected_from": "process_payment"
                        })
                except Exception as e:
                    logger.error(f"Error procesando transacción completada: {e}")
                    response.update({
                        "error": f"Pago aprobado pero error dispensando: {str(e)}",
                        "processing_error": True
                    })
            
            return jsonify(response)
            
        except Exception as e:
            logger.error(f"Error consultando estado de pago {payment_id}: {e}")
            return jsonify({
                "success": False,
                "error": f"Error consultando estado del pago: {str(e)}",
                "payment_id": payment_id
            }), 500
    
    # Si no hay payment_id, debe haber door_id para iniciar pago
    if "door_id" not in data:
        return jsonify({
            "success": False, 
            "error": f"Se requiere door_id (para iniciar pago) o payment_id (para consultar estado)"
        }), 400
    
    try:
        door_id = data["door_id"]
        
        # Obtener información del producto
        product = db_manager.get_product_by_door(door_id)
        if not product:
            return jsonify({"success": False, "error": "Producto no encontrado"}), 404
        
        if product["stock"] <= 0:
            return jsonify({"success": False, "error": "Producto sin stock"}), 400
        
        amount = product["price"]
        logger.info(f"Iniciando proceso de pago: {amount}€ para puerta {door_id}")
        
        # Inicializar pago en el TPV
        response = tpv_controller.init_payment(amount, door_id)
        
        if response["success"]:
            return jsonify({
                "success": True,
                "status": "payment_initiated",
                "payment_id": response["payment_id"],
                "amount": amount,
                "door_id": door_id,
                "message": "Pago iniciado - esperando tarjeta contactless"
            })
        else:
            return jsonify({
                "success": False,
                "status": "init_error",
                "error": f"Error iniciando pago: {response.get('error', 'Error de comunicación con TPV')}"
            })
        
    except Exception as e:
        logger.error(f"Error procesando inicio de pago para puerta {door_id}: {e}")
        return jsonify({
            "success": False,
            "status": "error",
            "error": f"Error interno: {str(e)}"
        }), 500

@payment_bp.route("/api/check_payment_status", methods=["POST"])
def check_payment_status():
    """Consultar estado del pago en el TPV"""
    data = request.get_json()
    logger.info(f"Datos recibidos en /api/check_payment_status: {data}")
    
    if not data:
        return jsonify({"success": False, "error": "No se recibieron datos"}), 400
    
    if "payment_id" not in data:
        return jsonify({
            "success": False, 
            "error": f"payment_id requerido. Datos recibidos: {list(data.keys()) if data else 'None'}"
        }), 400
    
    try:
        payment_id = data["payment_id"]
        door_id = data.get("door_id")
        
        logger.info(f"Consultando estado de pago {payment_id}")
        
        # Consultar estado en el TPV
        response = tpv_controller.check_payment_status(payment_id)
        
        if response["success"]:
            status = response["status"]
            
            if status == "approved":
                # Pago aprobado - completar transacción
                logger.info(f"Pago aprobado para payment_id {payment_id}")
                
                # Obtener información del producto para completar la transacción
                if door_id:
                    product = db_manager.get_product_by_door(door_id)
                    if product:
                        # Registrar transacción en base de datos
                        transaction_id = response.get("transaction_id", f"TXN_{door_id}_{int(time.time())}")
                        sale_id = db_manager.create_sale(
                            door_id=door_id,
                            payment_method="contactless",
                            amount=product["price"],
                            product_id=product["id"],
                            payment_id=payment_id
                        )
                        
                        if sale_id:
                            # Actualizar estado de la venta a completada
                            db_manager.update_sale_status(sale_id, "completed", dispensed=True)
                        
                        # Actualizar stock
                        db_manager.decrease_stock(door_id, 1)
                        
                        return jsonify({
                            "success": True,
                            "status": "approved",
                            "message": "Pago aprobado - producto a dispensar",
                            "transaction_id": transaction_id,
                            "amount": product["price"],
                            "door_id": door_id,
                            "hardware_success": True
                        })
                
                return jsonify({
                    "success": True,
                    "status": "approved",
                    "message": "Pago aprobado",
                    "transaction_id": response.get("transaction_id"),
                    "payment_id": payment_id
                })
            
            elif status == "declined":
                # Pago rechazado
                logger.warning(f"Pago rechazado para payment_id {payment_id}")
                return jsonify({
                    "success": False,
                    "status": "declined",
                    "error": response.get("message", "Pago rechazado por el banco"),
                    "payment_id": payment_id
                })
            
            elif status == "pending":
                # Pago aún pendiente
                return jsonify({
                    "success": True,
                    "status": "pending",
                    "message": "Pago en proceso - esperando respuesta",
                    "payment_id": payment_id
                })
            
            elif status == "timeout":
                # Timeout del pago
                logger.warning(f"Timeout en pago {payment_id}")
                return jsonify({
                    "success": False,
                    "status": "timeout",
                    "error": "Tiempo de espera agotado",
                    "payment_id": payment_id
                })
            
            else:
                # Estado desconocido
                return jsonify({
                    "success": False,
                    "status": "unknown",
                    "error": f"Estado desconocido: {status}",
                    "payment_id": payment_id
                })
        else:
            # Error consultando estado
            logger.error(f"Error consultando estado de pago {payment_id}: {response.get('error')}")
            return jsonify({
                "success": False,
                "status": "check_error",
                "error": f"Error consultando estado: {response.get('error', 'Error de comunicación')}"
            })
        
    except Exception as e:
        logger.error(f"Error consultando estado de pago {payment_id}: {e}")
        return jsonify({
            "success": False,
            "status": "error",
            "error": f"Error interno: {str(e)}"
        }), 500
