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
        "name": "Disk Cleanup - Agente IA",
        "id": None,
        "required_vars": ["target_host", "cleanup_paths", "retention_days", "email_to"]
    },
    "service_restart": {
        "name": "Service Restart - Agente IA",
        "id": None,
        "required_vars": ["target_host", "service_name", "service_action", "email_to"]
    }
}

# Configuración de email (para el playbook)
EMAIL_CONFIG = {
    "smtp_host": "smtp.gmail.com",  # según tu servidor
    "smtp_port": 587,
    "smtp_user": "lab.automation.tech@gmail.com",
    "smtp_password": "hlyp lvml uqjo sagh",  # App password de Gmail
    "from_email": "lab.automation.tech@gmail.com"
}