#!/usr/bin/env python3
"""
Endpoint de prueba simple para verificar el botón del pin 16
"""

from flask import Flask, jsonify
from controllers.hardware_controller import hardware_controller
from controllers.restock_controller import restock_controller

app = Flask(__name__)

@app.route('/test/button', methods=['GET'])
def test_button():
    """Endpoint de prueba para el botón"""
    try:
        # Test hardware
        hardware_state = hardware_controller.get_restock_button_state()
        hardware_pressed = hardware_controller.is_restock_button_pressed()
        
        # Test restock
        restock_pressed = restock_controller.check_physical_button()
        
        # Test integration
        if restock_pressed:
            restock_controller.handle_button_press()
        
        redirect_info = restock_controller.is_redirect_requested()
        
        return jsonify({
            'success': True,
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'hardware': {
                'state': hardware_state,
                'pressed': hardware_pressed
            },
            'restock': {
                'pressed': restock_pressed,
                'redirect_info': redirect_info
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🧪 Test server para botón pin 16")
    print("Visita: http://localhost:5001/test/button")
    app.run(debug=True, port=5001)
