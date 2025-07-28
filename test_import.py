#!/usr/bin/env python
try:
    import routes.payment_routes as pr
    print("Import successful")
    print("Attributes:", dir(pr))
    if hasattr(pr, 'payment_bp'):
        print("payment_bp found!")
    else:
        print("payment_bp NOT found")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
