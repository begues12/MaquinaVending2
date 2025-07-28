#!/usr/bin/env python
import logging
from flask import Blueprint

# Crear blueprint
payment_bp = Blueprint('payment', __name__)
logger = logging.getLogger(__name__)

print("payment_bp created successfully")
