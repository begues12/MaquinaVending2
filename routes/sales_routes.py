"""
Rutas relacionadas con ventas, historial y exportación
"""
import logging
from flask import Blueprint, request, jsonify
from database import db_manager
from controllers.sales_history_controller import sales_history_controller

# Crear blueprint
sales_bp = Blueprint('sales', __name__)
logger = logging.getLogger(__name__)

@sales_bp.route('/api/sales/today')
def get_today_sales():
    """Obtener ventas del día"""
    try:
        sales = db_manager.get_sales_by_date()
        total_amount = sum(sale['amount'] for sale in sales if sale['status'] == 'completed')
        
        return jsonify({
            'success'       : True,
            'sales'         : sales,
            'total_sales'   : len([s for s in sales if s['status'] == 'completed']),
            'total_amount'  : total_amount
        })
        
    except Exception as e:
        logger.error(f"Error al obtener ventas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sales_bp.route('/api/sales/history')
def get_sales_history():
    """Obtener historial de ventas con filtros opcionales"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = int(request.args.get('limit', 100))
    
    try:
        sales = sales_history_controller.get_sales_history(start_date, end_date, limit)
        return jsonify({'success': True, 'sales': sales})
    except Exception as e:
        logger.error(f"Error al obtener historial de ventas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sales_bp.route('/api/sales/summary')
def get_sales_summary():
    """Obtener resumen de ventas con estadísticas"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        summary = sales_history_controller.get_sales_summary(start_date, end_date)
        return jsonify({'success': True, 'summary': summary})
    except Exception as e:
        logger.error(f"Error al obtener resumen de ventas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sales_bp.route('/api/sales/export/csv')
def export_sales_csv():
    """Exportar historial de ventas a CSV"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        filepath = sales_history_controller.export_sales_to_csv(start_date, end_date)
        return jsonify({
            'success': True, 
            'message': 'Archivo CSV generado exitosamente',
            'filepath': filepath
        })
    except Exception as e:
        logger.error(f"Error al exportar CSV: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sales_bp.route('/api/sales/export/json')
def export_sales_json():
    """Exportar resumen de ventas a JSON"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        filepath = sales_history_controller.export_summary_to_json(start_date, end_date)
        return jsonify({
            'success': True, 
            'message': 'Archivo JSON generado exitosamente',
            'filepath': filepath
        })
    except Exception as e:
        logger.error(f"Error al exportar JSON: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sales_bp.route('/api/usb/detect')
def detect_usb():
    """Detectar unidades USB conectadas"""
    # Simulación: siempre acepta un USB ficticio
    usb_drives = [
        {
            'name': 'USB_SIMULADO',
            'mount_point': '/media/usb_simulado',
            'size': '16GB',
            'filesystem': 'FAT32'
        }
    ]
    return jsonify({
        'success': True,
        'usb_drives': usb_drives,
        'count': len(usb_drives)
    })

@sales_bp.route('/api/sales/export/usb', methods=['POST'])
def export_to_usb():
    """Exportar historial de ventas a USB automáticamente"""
    data = request.get_json()
    start_date = data.get('start_date') if data else None
    end_date = data.get('end_date') if data else None
    
    try:
        result = sales_history_controller.auto_export_to_usb(start_date, end_date)
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al exportar a USB: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
