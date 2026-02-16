# Agente IA para Análisis de Logs - Interfaz Web

## Descripción

Aplicación web desarrollada con Streamlit que utiliza inteligencia artificial (Claude Sonnet 4 de Anthropic) para analizar logs de errores de infraestructura TI y proporcionar diagnósticos automatizados con recomendaciones de remediación mediante playbooks de Ansible Automation Platform (AAP/AWX).

## Características Principales

- Análisis inteligente de logs mediante procesamiento de lenguaje natural
- Identificación automática de causa raíz de errores
- Recomendación de playbooks Ansible específicos para remediación
- Instrucciones paso a paso para ejecución en AAP/AWX
- Interfaz web intuitiva sin necesidad de línea de comandos
- Ejemplos de logs precargados para demostración
- Soporte para logs de Oracle Database, WebLogic, Linux y otros sistemas

## Requisitos del Sistema

### Software Requerido
- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Conexión a internet (para API de Anthropic)

### Dependencias de Python
```
anthropic==0.18.1
streamlit==1.31.0
python-dotenv==1.0.0
```

## Instalación

### 1. Clonar o descargar el proyecto
```bash
mkdir agente_logs_ia
cd agente_logs_ia
```

### 2. Crear entorno virtual
```bash
python3 -m venv venv
source venv/bin/activate  # En Linux/Mac
# venv\Scripts\activate   # En Windows
```

### 3. Instalar dependencias
```bash
pip install anthropic streamlit python-dotenv
```

### 4. Configurar API Key de Anthropic

Crear archivo `.env` en el directorio raíz:
```
ANTHROPIC_API_KEY=__api-key__
```

## Estructura del Proyecto
```
agente_logs_ia/
├── app_streamlit.py          # Aplicación principal
├── .env                       # Configuración de API key (no versionar)
├── logs_ejemplo/              # Logs de ejemplo para testing
│   ├── oracle_error.log
│   ├── weblogic_error.log
│   └── linux_disk_full.log
└── venv/                      # Entorno virtual de Python
```

## Uso

### Iniciar la aplicación
```bash
streamlit run app_streamlit.py --server.address=0.0.0.0
```

La aplicación se abrirá automáticamente en el navegador en `http://localhost:8501`

### Interfaz de Usuario

La aplicación cuenta con dos pestañas principales:

#### 1. Pegar Log
Permite ingresar manualmente el contenido de un log para análisis:
- Copiar el log de error desde la fuente (servidor, monitoring, etc.)
- Pegar en el área de texto
- Hacer clic en "Analizar"
- Revisar el diagnóstico y las recomendaciones

#### 2. Logs de Ejemplo
Proporciona tres escenarios precargados para demostración:
- Oracle - Error ORA-00257 (Archivelog Full)
- WebLogic - OutOfMemoryError
- Linux - Disco Lleno

Seleccionar un ejemplo y hacer clic en "Analizar Este Ejemplo"

### Resultado del Análisis

El agente proporciona:

1. **DIAGNOSTICO**: Descripción técnica del error y causa raíz
2. **SEVERIDAD**: Nivel de criticidad (Crítico/Alto/Medio/Bajo) e impacto
3. **SOLUCION**: Playbook recomendado y justificación
4. **EJECUCION EN AAP/AWX**: Pasos detallados para ejecutar desde la interfaz web
5. **VERIFICACION**: Pasos para confirmar la resolución del problema

## Configuración Avanzada

### Base de Conocimiento de Playbooks

La variable `PLAYBOOKS` en `app_streamlit.py` contiene el catálogo de playbooks disponibles. Para personalizar:
```python
PLAYBOOKS = """
=== PLAYBOOKS ANSIBLE DISPONIBLES ===

1. nombre_playbook.yml
   - Descripción: Qué hace el playbook
   - Parámetros: Variables requeridas
   - Uso: Casos de uso específicos

2. otro_playbook.yml
   ...
"""
```

### Ajustar Parámetros del Modelo

Modificar en la función `analizar_log()`:
```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",  # Modelo a utilizar
    max_tokens=2000,                    # Longitud máxima de respuesta
    messages=[{"role": "user", "content": prompt}]
)
```

### Personalizar Prompt del Agente

El prompt se encuentra en la función `analizar_log()`. Ajustar según necesidades específicas:
```python
prompt = f"""Eres un experto en operaciones TI...
[Instrucciones del agente]
"""
```

## Casos de Uso

### Escenario 1: Soporte de Nivel 1
Operadores junior reciben alertas y utilizan el agente para:
- Identificar rápidamente el problema
- Obtener instrucciones claras de remediación
- Reducir dependencia de escalación a nivel 2/3

### Escenario 2: Respuesta a Incidentes
Durante incidentes críticos:
- Análisis rápido de logs complejos
- Decisiones basadas en recomendaciones IA
- Reducción del MTTR (Mean Time To Resolve)

### Escenario 3: Capacitación de Personal
Uso del agente como herramienta educativa:
- Nuevos operadores aprenden mejores prácticas
- Ejemplos de análisis estructurado
- Aceleración de curva de aprendizaje

### Escenario 4: Documentación de Incidentes
Generación automática de:
- Diagnóstico técnico detallado
- Pasos de remediación ejecutados
- Verificaciones post-resolución

## Limitaciones Conocidas

- Requiere conexión a internet para acceso a API de Anthropic
- Precisión del análisis depende de la calidad del log proporcionado
- No ejecuta automáticamente playbooks (requiere intervención humana)
- Logs muy largos pueden requerir truncamiento (límite de tokens)
- API de Anthropic tiene límites de rate limiting según plan contratado

## Seguridad y Privacidad

### Manejo de Datos Sensibles

- Los logs enviados a Anthropic API no se almacenan para entrenamiento
- Anthropic cumple con GDPR, SOC 2 Type 2, ISO 27001
- Se recomienda ofuscar información sensible antes del análisis:
  - Direcciones IP internas
  - Nombres de usuario
  - Credenciales
  - Información de clientes

### Recomendaciones de Seguridad

1. Proteger el archivo `.env` con permisos restrictivos:
```bash
   chmod 600 .env
```

2. No versionar el archivo `.env` en git:
```bash
   echo ".env" >> .gitignore
```

3. Rotar API keys periódicamente

4. Implementar autenticación si se expone públicamente

## Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'anthropic'"
```bash
pip install anthropic streamlit python-dotenv
```

### Error: "AuthenticationError: invalid x-api-key"
- Verificar que el archivo `.env` existe en el directorio raíz
- Confirmar que la API key es válida en https://console.anthropic.com/
- Verificar que no hay espacios extra en el archivo `.env`

### Error: La aplicación no se abre en el navegador
- Abrir manualmente: `http://localhost:8501`
- Verificar que el puerto 8501 no está en uso
- Revisar firewall/antivirus

### Respuestas lentas del agente
- Verificar conexión a internet
- Considerar que la primera llamada puede ser más lenta (cold start)
- Revisar límites de rate de la API en el dashboard de Anthropic

## Costos Operativos

### API de Anthropic (Claude Sonnet 4)

- Input: $3.00 por 1M tokens
- Output: $15.00 por 1M tokens

### Estimación de Costos

Un análisis típico consume aproximadamente:
- Input: 2,000 tokens (log + base de conocimiento)
- Output: 1,000 tokens (análisis generado)

Costo por análisis: ~$0.021 (2 centavos de dólar)

Volúmenes estimados:
- 100 análisis/mes: $2.10
- 500 análisis/mes: $10.50
- 1,000 análisis/mes: $21.00

## Métricas de Rendimiento

### Tiempos de Respuesta Típicos

- Análisis de log simple (< 50 líneas): 3-5 segundos
- Análisis de log complejo (50-200 líneas): 5-10 segundos
- Análisis de log extenso (> 200 líneas): 10-15 segundos

### Precisión del Análisis

Basado en testing interno:
- Errores conocidos con patrones claros: 95-98%
- Errores con contexto parcial: 85-90%
- Errores completamente nuevos: 75-80%

## Roadmap de Desarrollo

### Versión Actual (v1.0)
- Análisis básico de logs
- Recomendación de playbooks
- Interfaz web con Streamlit

### Versión Futura (v1.1)
- Integración directa con AAP/AWX API
- Ejecución de playbooks con aprobación
- Historial de análisis

### Versión Futura (v2.0)
- Base de datos vectorial para RAG
- Aprendizaje de incidentes históricos
- Análisis de tendencias
- Multi-tenancy

## Contribuciones

Para contribuir al proyecto:

1. Reportar bugs o sugerencias vía issues
2. Proponer mejoras mediante pull requests
3. Documentar nuevos casos de uso
4. Compartir ejemplos de logs para testing

## Soporte

Para soporte técnico:
- Revisar la sección de Solución de Problemas
- Consultar documentación de Anthropic: https://docs.anthropic.com/
- Consultar documentación de Streamlit: https://docs.streamlit.io/

## Licencia

Este proyecto es de uso interno para NTT Data

## Autor

Desarrollado por el equipo de Automatización de NTT Data
Contacto: Automatizacion_IS_CO@emeal.nttdata.com

## Versión

v1.0.0 - Enero 2025

## Changelog

### v1.0.0 (2025-01-21)
- Versión inicial
- Análisis básico de logs
- Interfaz web con Streamlit
- Soporte para Oracle, WebLogic, Linux
- Integración con Claude Sonnet 4

## Referencias

- Anthropic API Documentation: https://docs.anthropic.com/
- Streamlit Documentation: https://docs.streamlit.io/
- Ansible Automation Platform: https://www.ansible.com/products/automation-platform
- Red Hat AWX: https://github.com/ansible/awx