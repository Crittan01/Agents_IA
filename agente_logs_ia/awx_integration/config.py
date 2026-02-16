# awx_integration/config.py
"""
Configuración para conexión con AWX/AAP
"""

# Configuración del servidor AWX
AWX_CONFIG = {
    "base_url": "http://oracle9awx.labrhel.com/",
    "username": "admin",  # Cambiar por tu usuario
    "password": "awx123",  # Cambiar por tu password
    "verify_ssl": False  # False para HTTP, True para HTTPS
}

# Job Templates configurados en AWX
JOB_TEMPLATES = {
    "disk_cleanup": {
        "name": "Disk Cleanup - Agente IA",  # Nombre en AWX
        "id": None,  # Se obtiene automáticamente
        "required_vars": [
            "target_host",      # Servidor donde ejecutar
            "cleanup_paths",    # Rutas a limpiar (lista)
            "retention_days",   # Días de retención
            "email_to"          # Email para reporte
        ]
    }
}

# Configuración de email (para el playbook)
EMAIL_CONFIG = {
    "smtp_host": "smtp.gmail.com",  # Cambiar según tu servidor
    "smtp_port": 587,
    "smtp_user": "lab.automation.tech@gmail.com",
    "smtp_password": "Lj3635084*",  # App password de Gmail
    "from_email": "lab.automation.tech@gmail.com"
}