import streamlit as st
import anthropic
import os
import sys
import json
import re
from dotenv import load_dotenv
from pathlib import Path

# Agregar path del proyecto
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

# Cargar .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Importar AWX client
try:
    from awx_integration import AWXClient, JOB_TEMPLATES
    AWX_AVAILABLE = True
except ImportError:
    AWX_AVAILABLE = False

# Configuración de la página
st.set_page_config(
    page_title="Agente IA - Análisis de Logs + Ejecución",
    page_icon="🤖",
    layout="wide"
)

# Inicializar cliente Anthropic
@st.cache_resource
def get_client():
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

client = get_client()

# Inicializar session state
if "analisis_resultado" not in st.session_state:
    st.session_state.analisis_resultado = None
    st.session_state.variables_extraidas = {}
    st.session_state.playbook_sugerido = None

# Base de conocimiento de playbooks
PLAYBOOKS = """
=== PLAYBOOKS ANSIBLE DISPONIBLES ===

1. disk_cleanup.yml - Limpieza automática de disco con reporte
   Variables requeridas:
   - target_host: Servidor donde ejecutar
   - cleanup_paths: Lista de rutas a limpiar
   - retention_days: Días de retención de archivos
   - email_to: Email para reporte ejecutivo

2. service_restart.yml - Restart de servicios con validación
   Variables requeridas:
   - target_host: Servidor donde ejecutar
   - service_name: Nombre del servicio (httpd, postgresql, nginx, etc.)
   - service_action: Acción a ejecutar (restart, start, stop)
   - email_to: Email para reporte ejecutivo

3. oracle_health_check.yml - Diagnóstico Oracle
4. oracle_archivelog_cleanup.yml - Limpieza archivelog
5. weblogic_restart.yml - Reinicio WebLogic
6. weblogic_heap_increase.yml - Incrementar heap
7. sql_server_hardening.yml - Hardening SQL Server
"""

def analizar_log_y_extraer_variables(log_content):
    """Analiza log y extrae variables automáticamente"""
    
    prompt = f"""Eres un experto en operaciones TI con Ansible Automation Platform (AAP/AWX).

LOG A ANALIZAR:
{log_content}

PLAYBOOKS DISPONIBLES:
{PLAYBOOKS}

Realiza un análisis completo y responde en formato JSON con esta estructura EXACTA:

{{
  "diagnostico": "Descripción técnica del problema en 2-3 líneas",
  "severidad": "Crítico|Alto|Medio|Bajo",
  "playbook_recomendado": "nombre_exacto_del_playbook.yml",
  "razon_playbook": "Por qué este playbook es el indicado",
  "variables_extraidas": {{
    // Para disk_cleanup.yml:
    "target_host": "hostname extraído del log",
    "cleanup_paths": ["/var/log", "/tmp"],
    "retention_days": 7,
    "email_to": "lab.automation.tech@gmail.com",
    
    // Para service_restart.yml:
    "service_name": "nombre del servicio extraído del log (httpd, postgresql, nginx, etc.)",
    "service_action": "restart"
  }},
  "verificacion": "Qué revisar después de la ejecución"
}}

IMPORTANTE:
- Para disk_cleanup.yml: extrae las rutas llenas del log
- Para service_restart.yml: extrae el nombre del servicio que falló (httpd, postgresql, nginx, sshd, etc.)
- Detecta el servidor desde el hostname en el log
- Responde SOLO con el JSON, sin texto adicional"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        respuesta_texto = response.content[0].text
        
        # Limpiar respuesta (quitar markdown si existe)
        respuesta_texto = respuesta_texto.strip()
        if respuesta_texto.startswith("```json"):
            respuesta_texto = respuesta_texto.split("```json")[1].split("```")[0].strip()
        elif respuesta_texto.startswith("```"):
            respuesta_texto = respuesta_texto.split("```")[1].split("```")[0].strip()
        
        # Parsear JSON
        resultado = json.loads(respuesta_texto)
        return resultado, None
        
    except json.JSONDecodeError as e:
        # Fallback: devolver análisis en texto si falla el JSON
        return None, respuesta_texto
    except Exception as e:
        return None, f"Error: {str(e)}"

def formatear_analisis_visual(resultado):
    """Formatea el resultado del análisis para mostrar visualmente usando componentes Streamlit"""
    
    if not isinstance(resultado, dict):
        # Fallback para texto plano
        st.code(str(resultado), language="text")
        return
    
    # Contenedor principal con estilo
    with st.container():
        # Header
        st.markdown("### ANÁLISIS DEL INCIDENTE")
        st.markdown("---")
        
        # 1. DIAGNÓSTICO
        st.markdown("#### 1. DIAGNÓSTICO")
        diagnostico = resultado.get('diagnostico', 'No disponible')
        st.info(diagnostico)
        
        # 2. SEVERIDAD
        st.markdown("#### 2. SEVERIDAD")
        severidad = resultado.get('severidad', 'No determinada')
        
        # Color según severidad
        if severidad.lower() == 'crítico':
            st.error(f"**{severidad}**")
        elif severidad.lower() == 'alto':
            st.warning(f"**{severidad}**")
        elif severidad.lower() == 'medio':
            st.info(f"**{severidad}**")
        else:
            st.success(f"**{severidad}**")
        
        # 3. PLAYBOOK RECOMENDADO
        st.markdown("#### 3. PLAYBOOK RECOMENDADO")
        playbook = resultado.get('playbook_recomendado', 'No determinado')
        razon = resultado.get('razon_playbook', '')
        
        col1, col2 = st.columns([1, 3])
        with col1:
            st.code(playbook, language="yaml")
        with col2:
            st.markdown(f"*{razon}*")
        
        # 4. VARIABLES DETECTADAS
        st.markdown("#### 4. VARIABLES DETECTADAS")
        variables = resultado.get('variables_extraidas', {})
        
        if variables:
            # Mostrar en tabla bonita
            st.json(variables)
        else:
            st.warning("No se detectaron variables automáticamente")
        
        # 5. VERIFICACIÓN
        st.markdown("#### 5. VERIFICACIÓN POST-EJECUCIÓN")
        verificacion = resultado.get('verificacion', 'No especificada')
        st.success(verificacion)

def ejecutar_playbook_awx(playbook_name, variables):
    """Ejecuta playbook en AWX"""
    if not AWX_AVAILABLE:
        return None, "AWX client no disponible"
    
    try:
        awx = AWXClient()
        
        # Obtener template ID
        template_name = JOB_TEMPLATES.get(playbook_name, {}).get("name")
        if not template_name:
            return None, f"Template no configurado: {playbook_name}"
        
        template_id = awx.get_job_template_id(template_name)
        if not template_id:
            return None, f"Template no encontrado en AWX: {template_name}"
        
        # Lanzar job
        job_id = awx.launch_job(template_id, variables)
        if not job_id:
            return None, "Error lanzando job en AWX"
        
        return job_id, "Job lanzado exitosamente"
    
    except Exception as e:
        return None, f"Error: {str(e)}"

# ==================== INTERFAZ ====================

st.title("Agente IA - Análisis de Logs + Ejecución Automática")
st.markdown("**Análisis inteligente con extracción automática de variables**")

# Sidebar
with st.sidebar:
    st.header("Información")
    
    # Status AWX
    if AWX_AVAILABLE:
        st.success("Conexión AWX: Activa")
    else:
        st.error("Conexión AWX: No disponible")
    
    st.markdown("---")
    
    st.markdown("""
    **Capacidades:**
    - Análisis inteligente de logs
    - Extracción automática de variables
    - Ejecución automática en AWX
    - Reporte ejecutivo por email
    
    **Playbooks Disponibles:**
    - disk_cleanup.yml
    - oracle_health_check.yml
    - weblogic_restart.yml
    """)
    
    st.markdown("---")
    
    # Mostrar variables extraídas si existen
    if st.session_state.variables_extraidas:
        st.info("**Variables Auto-Detectadas:**")
        st.json(st.session_state.variables_extraidas)
    
    st.markdown("---")
    st.markdown("**Desarrollado por:** NTT Data Automation Team")

# Tabs
tab1, tab2, tab3 = st.tabs(["Pegar Log", "Logs de Ejemplo", "Ejecutar Playbook"])

with tab1:
    st.subheader("Pega tu log de error aquí")
    log_input = st.text_area(
        "Log de error:",
        height=300,
        placeholder="Pega aquí el contenido del log que deseas analizar..."
    )
    
    # Botones en columnas
    col1, col2 = st.columns([1, 5])
    with col1:
        analizar_btn = st.button("Analizar", type="primary", use_container_width=True)
    with col2:
        limpiar_btn = st.button("Limpiar", use_container_width=True)
    
    # Lógica de limpieza
    if limpiar_btn:
        st.session_state.analisis_resultado = None
        st.session_state.variables_extraidas = {}
        st.session_state.playbook_sugerido = None
        st.rerun()
    
    # RESULTADO FUERA DE LAS COLUMNAS (ancho completo)
    if analizar_btn and log_input:
        with st.spinner("Analizando log con IA y extrayendo variables..."):
            resultado, error = analizar_log_y_extraer_variables(log_input)
            
            if resultado:
                st.session_state.analisis_resultado = resultado
                st.session_state.variables_extraidas = resultado.get('variables_extraidas', {})
                st.session_state.playbook_sugerido = resultado.get('playbook_recomendado', '').replace('.yml', '')
                
                st.success("Análisis completado - Variables extraídas automáticamente")
                st.markdown("---")
                
                # Llamar función de formateo (ahora en ancho completo)
                formatear_analisis_visual(resultado)
                
                st.info("Ve a la pestaña **'Ejecutar Playbook'** - Las variables ya están pre-cargadas")
            else:
                st.error(f"Error en análisis: {error}")

with tab2:
    st.subheader("Selecciona un log de ejemplo")
    
    ejemplo = st.selectbox(
        "Escenario:",
        [
            "Linux - Disco Lleno",
            "Linux - Servicio Caído (httpd)",
            "Oracle - Error ORA-00257 (Archivelog Full)",
            "WebLogic - OutOfMemoryError"
        ]
    )
    
    # Rutas absolutas
    logs_dir = Path(__file__).parent / "logs_ejemplo"
    
    logs_map = {
        "Linux - Disco Lleno": logs_dir / "linux_disk_full.log",
        "Linux - Servicio Caído (httpd)": logs_dir / "service_failed.log",
        "Oracle - Error ORA-00257 (Archivelog Full)": logs_dir / "oracle_error.log",
        "WebLogic - OutOfMemoryError": logs_dir / "weblogic_error.log"
    }
    
    ruta_log = logs_map[ejemplo]
    
    try:
        with open(ruta_log, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        st.code(contenido, language="log")
        
        analizar_ejemplo_btn = st.button("Analizar Este Ejemplo", type="primary")
        
        # RESULTADO FUERA (ancho completo)
        if analizar_ejemplo_btn:
            with st.spinner("Analizando log con IA y extrayendo variables..."):
                resultado, error = analizar_log_y_extraer_variables(contenido)
                
                if resultado:
                    st.session_state.analisis_resultado = resultado
                    st.session_state.variables_extraidas = resultado.get('variables_extraidas', {})
                    st.session_state.playbook_sugerido = resultado.get('playbook_recomendado', '').replace('.yml', '')
                    
                    st.success("Análisis completado - Variables extraídas automáticamente")
                    st.markdown("---")
                    
                    # Llamar función de formateo (ancho completo)
                    formatear_analisis_visual(resultado)
                    
                    st.info("Ve a la pestaña **'Ejecutar Playbook'** - Las variables ya están pre-cargadas")
                else:
                    st.error(f"Error: {error}")
    
    except FileNotFoundError:
        st.error(f"Archivo no encontrado: {ruta_log}")
        st.info("Verifica que los archivos de logs existan en la carpeta logs_ejemplo/")

with tab3:
    st.subheader("Ejecutar Playbook en AWX")
    
    if not AWX_AVAILABLE:
        st.error("Cliente AWX no disponible. Verifica la configuración.")
    else:
        # Auto-seleccionar playbook si fue sugerido
        playbook_options = ["disk_cleanup", "service_restart"]
        default_index = 0
        
        if st.session_state.playbook_sugerido in playbook_options:
            default_index = playbook_options.index(st.session_state.playbook_sugerido)
        
        playbook_select = st.selectbox(
            "Playbook a ejecutar:",
            playbook_options,
            index=default_index,
            help="Playbook sugerido por el análisis de IA"
        )
        
        st.markdown("---")
        st.markdown("### Configuración de Variables")
        
        if playbook_select == "disk_cleanup":
            # Usar variables extraídas o valores por defecto
            vars_default = st.session_state.variables_extraidas if st.session_state.variables_extraidas else {
                "target_host": "localhost",
                "cleanup_paths": ["/var/log", "/tmp"],
                "retention_days": 7,
                "email_to": "lab.automation.tech@gmail.com"
            }
            
            col1, col2 = st.columns(2)
            
            with col1:
                target_host = st.text_input(
                    "Servidor destino:",
                    value=vars_default.get("target_host", "localhost"),
                    help="Auto-detectado desde el log" if st.session_state.variables_extraidas else "Hostname o IP del servidor"
                )
                
                # Convertir lista a texto con saltos de línea
                paths_default = "\n".join(vars_default.get("cleanup_paths", ["/var/log", "/tmp"]))
                
                cleanup_paths = st.text_area(
                    "Rutas a limpiar (una por línea):",
                    value=paths_default,
                    height=100,
                    help="Auto-detectadas desde el log" if st.session_state.variables_extraidas else "Rutas del filesystem"
                )
            
            with col2:
                retention_days = st.number_input(
                    "Días de retención:",
                    min_value=1,
                    max_value=90,
                    value=vars_default.get("retention_days", 7),
                    help="Archivos más antiguos serán eliminados"
                )
                
                email_to = st.text_input(
                    "Email para reporte:",
                    value=vars_default.get("email_to", "lab.automation.tech@gmail.com"),
                    help="Destinatario del reporte HTML ejecutivo"
                )
            
            # Mostrar alerta si las variables fueron auto-detectadas
            if st.session_state.variables_extraidas:
                st.success("**Variables pre-cargadas automáticamente desde el análisis de IA**")
            
            st.markdown("---")
            
            # Botón de ejecución
            if st.button("EJECUTAR PLAYBOOK EN AWX", type="primary", use_container_width=True):
                # Preparar variables
                paths_list = [p.strip() for p in cleanup_paths.split('\n') if p.strip()]
                
                extra_vars = {
                    "target_host": target_host,
                    "cleanup_paths": paths_list,
                    "retention_days": retention_days,
                    "email_to": email_to
                }
                
                with st.spinner("Lanzando job en AWX..."):
                    job_id, message = ejecutar_playbook_awx("disk_cleanup", extra_vars)
                    
                    if job_id:
                        st.success(f"{message}")
                        st.info(f"**Job ID:** {job_id}")
                        
                        # Monitorear job
                        awx = AWXClient()
                        with st.spinner("Esperando que el job termine..."):
                            status = awx.wait_for_job(job_id, timeout=300)
                        
                        if status["status"] == "successful":
                            st.success("**JOB COMPLETADO EXITOSAMENTE**")
                            st.balloons()
                            
                            # Mostrar output
                            with st.expander("📄 Ver Output del Job", expanded=True):
                                output = awx.get_job_output(job_id)
                                st.code(output, language="bash")
                            
                            st.info(f"📧 Reporte HTML enviado a: **{email_to}**")
                            
                            # Resetear variables
                            if st.button("🔄 Nuevo Análisis"):
                                st.session_state.analisis_resultado = None
                                st.session_state.variables_extraidas = {}
                                st.session_state.playbook_sugerido = None
                                st.rerun()
                        
                        elif status["status"] == "failed":
                            st.error("**JOB FALLÓ**")
                            output = awx.get_job_output(job_id)
                            st.code(output, language="bash")
                        
                        else:
                            st.warning(f"Status: {status['status']}")
                    
                    else:
                        st.error(f"{message}")

        elif playbook_select == "service_restart":
            # Usar variables extraídas o valores por defecto
            vars_default = st.session_state.variables_extraidas if st.session_state.variables_extraidas else {
                "target_host": "localhost",
                "service_name": "httpd",
                "service_action": "restart",
                "email_to": "lab.automation.tech@gmail.com"
            }
            
            col1, col2 = st.columns(2)
            
            with col1:
                target_host = st.text_input(
                    "Servidor destino:",
                    value=vars_default.get("target_host", "localhost"),
                    key="sr_target_host",
                    help="Auto-detectado desde el log" if st.session_state.variables_extraidas else "Hostname o IP del servidor"
                )
                
                service_name = st.text_input(
                    "Nombre del servicio:",
                    value=vars_default.get("service_name", "httpd"),
                    key="sr_service_name",
                    help="Auto-detectado desde el log" if st.session_state.variables_extraidas else "Nombre del servicio systemd (httpd, nginx, postgresql, etc.)"
                )
            
            with col2:
                service_action = st.selectbox(
                    "Acción a ejecutar:",
                    ["restart", "start", "stop"],
                    index=["restart", "start", "stop"].index(vars_default.get("service_action", "restart")),
                    key="sr_service_action",
                    help="Acción que se ejecutará sobre el servicio"
                )
                
                email_to = st.text_input(
                    "Email para reporte:",
                    value=vars_default.get("email_to", "lab.automation.tech@gmail.com"),
                    key="sr_email_to",
                    help="Destinatario del reporte HTML ejecutivo"
                )
            
            # Mostrar alerta si las variables fueron auto-detectadas
            if st.session_state.variables_extraidas:
                st.success("✨ **Variables pre-cargadas automáticamente desde el análisis de IA**")
            
            st.markdown("---")
            
            # Botón de ejecución
            if st.button("▶️ EJECUTAR PLAYBOOK EN AWX", type="primary", use_container_width=True, key="sr_execute"):
                # Preparar variables
                extra_vars = {
                    "target_host": target_host,
                    "service_name": service_name,
                    "service_action": service_action,
                    "email_to": email_to,
                    "email_pwd": "TU_APP_PASSWORD_AQUI"  # ← Actualiza con tu app password
                }
                
                with st.spinner("🚀 Lanzando job en AWX..."):
                    job_id, message = ejecutar_playbook_awx("service_restart", extra_vars)
                    
                    if job_id:
                        st.success(f"✅ {message}")
                        st.info(f"**Job ID:** {job_id}")
                        
                        # Monitorear job
                        awx = AWXClient()
                        with st.spinner("⏳ Esperando que el job termine..."):
                            status = awx.wait_for_job(job_id, timeout=300)
                        
                        if status["status"] == "successful":
                            st.success("✅ **JOB COMPLETADO EXITOSAMENTE**")
                            st.balloons()
                            
                            # Mostrar output
                            with st.expander("📄 Ver Output del Job", expanded=True):
                                output = awx.get_job_output(job_id)
                                st.code(output, language="bash")
                            
                            st.info(f"📧 Reporte HTML enviado a: **{email_to}**")
                        
                        elif status["status"] == "failed":
                            st.error("❌ **JOB FALLÓ**")
                            output = awx.get_job_output(job_id)
                            st.code(output, language="bash")
                        
                        else:
                            st.warning(f"⚠️ Status: {status['status']}")
                    
                    else:
                        st.error(f"❌ {message}")
# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <small>Powered by Claude Sonnet 4 + Ansible AWX | NTT Data Automation</small>
</div>
""", unsafe_allow_html=True)