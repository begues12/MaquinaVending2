"""
Script de instalación para dependencias de hardware
"""
import subprocess
import sys
import platform

def install_packages():
    """Instalar paquetes necesarios para el control de hardware"""
    
    packages = []
    
    # Detectar plataforma
    if platform.system() == "Linux":
        # En Raspberry Pi, instalar RPi.GPIO
        packages.extend([
            "RPi.GPIO",
            "gpiozero"  # Alternativa más moderna
        ])
    
    # Paquetes comunes para todas las plataformas
    packages.extend([
        "psutil",  # Ya instalado, pero por si acaso
        "pyserial"  # Para comunicación con TPV si es necesario
    ])
    
    print("🔧 Instalando dependencias de hardware...")
    
    for package in packages:
        try:
            print(f"📦 Instalando {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} instalado correctamente")
        except subprocess.CalledProcessError:
            print(f"⚠️ Error instalando {package} - puede que no sea necesario en esta plataforma")
    
    print("\n🎉 Instalación completada!")
    print("\nNOTA: Si estás en Raspberry Pi y tienes errores con GPIO,")
    print("ejecuta el programa con 'sudo python app.py'")

if __name__ == "__main__":
    install_packages()
