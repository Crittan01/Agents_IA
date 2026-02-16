import streamlit as st
import anthropic
import os
import sys
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
    st.warning("Módulo AWX no disponible. Instalando dependencias...")

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
if "job_launched" not in st.session_state:
    st.session_state.job_launched = False
    st.session_state.job_id = None
    st.session_state.playbook_suggested = None

# Base de conocimiento de playbooks
PLAYBOOKS = """
=== PLAYBOOKS ANSIBLE DISPONIBLES ===

1. disk_cleanup.yml - Limpieza automática de disco con reporte
   Variables: target_host, cleanup_paths, retention_days, email_to
   
2. oracle_health_check.yml - Diagnóstico Oracle
3. oracle_archivelog_cleanup.yml - Limpieza archivelog
4. weblogic_restart.yml - Reinicio WebLogic
5. weblogic_heap_increase.yml - Incrementar heap
6. service_restart.yml - Reinicio servicios Linux
7. sql_server_hardening.yml - Hardening SQL Server
"""

def analizar_log(log_content):
    """Analiza log y sugiere playbook"""
    prompt = f"""Eres un experto en operaciones TI con Ansible Automation Platform (AAP/AWX).

LOG:
{log_content}

PLAYBOOKS:
{PLAYBOOKS}

Analiza y proporciona:

1. **DIAGNÓSTICO** (2-3 líneas concisas)
2. **SEVERIDAD** (Crítico/Alto/Medio/Bajo)
3. **PLAYBOOK RECOMENDADO** 
   - Nombre exacto del playbook
   - Por qué es el indicado
4. **VARIABLES REQUERIDAS**
   - Lista las variables que necesita el playbook
5. **VERIFICACIÓN POST-EJECUCIÓN**

Responde en español, técnico pero claro. Sin emojis."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error: {str(e)}"

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

st.title("🤖 Agente IA - Análisis de Logs + Ejecución Automática")
st.markdown("**Análisis inteligente con capacidad de ejecución en AWX**")

# Sidebar
with st.sidebar:
    st.header("📋 Información")
    
    # Status AWX
    if AWX_AVAILABLE:
        st.success("✅ Conexión AWX: Activa")
    else:
        st.error("❌ Conexión AWX: No disponible")
    
    st.markdown("---")
    
    st.markdown("""
    **Capacidades:**
    - Análisis inteligente de logs
    - Sugerencia de playbooks
    - Ejecución automática en AWX
    - Reporte ejecutivo por email
    
    **Playbooks con Ejecución:**
    - ✅ disk_cleanup.yml
    - 🔜 oracle_health_check.yml
    - 🔜 weblogic_restart.yml
    """)
    
    st.markdown("---")
    st.markdown("**Desarrollado por:** NTT Data Automation Team")

# Tabs
tab1, tab2, tab3 = st.tabs(["📝 Pegar Log", "📁 Logs de Ejemplo", "🚀 Ejecutar Playbook"])

with tab1:
    st.subheader("Pega tu log de error aquí")
    log_input = st.text_area(
        "Log de error:",
        height=300,
        placeholder="Pega aquí el contenido del log..."
    )
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔍 Analizar", type="primary", use_container_width=True):
            if log_input:
                with st.spinner("Analizando log con IA..."):
                    resultado = analizar_log(log_input)
                    st.success("✅ Análisis completado")
                    st.markdown("---")
                    st.markdown(resultado)
                    
                    # Detectar playbook sugerido
                    if "disk_cleanup" in resultado.lower():
                        st.session_state.playbook_suggested = "disk_cleanup"
                        st.info("💡 Playbook detectado: **disk_cleanup.yml** - Puedes ejecutarlo en la pestaña 'Ejecutar Playbook'")
    
    with col2:
        if st.button("🗑️ Limpiar", use_container_width=True):
            st.rerun()

with tab2:
    st.subheader("Selecciona un log de ejemplo")
    
    ejemplo = st.selectbox(
        "Escenario:",
        [
            "Linux - Disco Lleno",
            "Oracle - Error ORA-00257 (Archivelog Full)",
            "WebLogic - OutOfMemoryError"
        ]
    )
    
    logs_map = {
        "Linux - Disco Lleno": "logs_ejemplo/linux_disk_full.log",
        "Oracle - Error ORA-00257 (Archivelog Full)": "logs_ejemplo/oracle_error.log",
        "WebLogic - OutOfMemoryError": "logs_ejemplo/weblogic_error.log"
    }
    
    try:
        with open(logs_map[ejemplo], 'r') as f:
            contenido = f.read()
        
        st.code(contenido, language="log")
        
        if st.button("🔍 Analizar Este Ejemplo", type="primary"):
            with st.spinner("Analizando..."):
                resultado = analizar_log(contenido)
                st.success("✅ Análisis completado")
                st.markdown("---")
                st.markdown(resultado)
                
                if "disk_cleanup" in resultado.lower() or "disco lleno" in ejemplo.lower():
                    st.session_state.playbook_suggested = "disk_cleanup"
                    st.info("💡 Ve a la pestaña 'Ejecutar Playbook' para lanzar disk_cleanup.yml")
    
    except FileNotFoundError:
        st.error(f"❌ Archivo no encontrado: {logs_map[ejemplo]}")

with tab3:
    st.subheader("🚀 Ejecutar Playbook en AWX")
    
    if not AWX_AVAILABLE:
        st.error("❌ Cliente AWX no disponible. Verifica la configuración.")
    else:
        playbook_select = st.selectbox(
            "Playbook a ejecutar:",
            ["disk_cleanup"],
            help="Más playbooks próximamente"
        )
        
        st.markdown("---")
        st.markdown("### Configuración de Variables")
        
        if playbook_select == "disk_cleanup":
            col1, col2 = st.columns(2)
            
            with col1:
                target_host = st.text_input(
                    "Servidor destino:",
                    value="localhost",
                    help="Hostname o IP del servidor"
                )
                
                cleanup_paths = st.text_area(
                    "Rutas a limpiar (una por línea):",
                    value="/var/log\n/tmp",
                    height=100
                )
            
            with col2:
                retention_days = st.number_input(
                    "Días de retención:",
                    min_value=1,
                    max_value=90,
                    value=7,
                    help="Archivos más antiguos serán eliminados"
                )
                
                email_to = st.text_input(
                    "Email para reporte:",
                    value="manager@example.com",
                    help="Destinatario del reporte HTML"
                )
            
            st.markdown("---")
            
            # Botón de ejecución
            if st.button("▶️ EJECUTAR PLAYBOOK EN AWX", type="primary", use_container_width=True):
                # Preparar variables
                paths_list = [p.strip() for p in cleanup_paths.split('\n') if p.strip()]
                
                extra_vars = {
                    "target_host": target_host,
                    "cleanup_paths": paths_list,
                    "retention_days": retention_days,
                    "email_to": email_to
                }
                
                with st.spinner("🚀 Lanzando job en AWX..."):
                    job_id, message = ejecutar_playbook_awx("disk_cleanup", extra_vars)
                    
                    if job_id:
                        st.session_state.job_launched = True
                        st.session_state.job_id = job_id
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