#!/usr/bin/env python
import sys
import os

print("Testing payment_routes step by step...")

try:
    print("Step 1: Basic imports")
    import logging
    import time
    from flask import Blueprint, request, jsonify
    print("Flask imports OK")
    
    print("Step 2: Custom imports")
    from database import db_manager
    print("database import OK")
    
    from controllers.tpv_controller import TPVController
    print("tpv_controller import OK")
    
    from controllers.hardware_controller import hardware_controller
    print("hardware_controller import OK")
    
    print("Step 3: Creating blueprint")
    payment_bp = Blueprint('payment', __name__)
    print("Blueprint created OK")
    
    print("Step 4: Testing full module import")
    try:
        exec(open('routes/payment_routes.py').read())
        print("Full module execution OK")
    except Exception as e:
        print(f"Error executing full module: {e}")
        import traceback
        traceback.print_exc()
    
except Exception as e:
    print(f"Error in step-by-step test: {e}")
    import traceback
    traceback.print_exc()
