import streamlit as st
import anthropic
import os
from dotenv import load_dotenv

# Cargar .env desde la raíz del proyecto
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configuración de la página
st.set_page_config(
    page_title="Agente IA - Análisis de Logs",
    page_icon="",
    layout="wide"
)

# Inicializar cliente
@st.cache_resource
def get_client():
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

client = get_client()

# Base de conocimiento
PLAYBOOKS = """
=== PLAYBOOKS ANSIBLE DISPONIBLES ===

1. oracle_health_check.yml - Diagnóstico Oracle
2. oracle_archivelog_cleanup.yml - Limpieza archivelog
3. weblogic_restart.yml - Reinicio WebLogic
4. weblogic_heap_increase.yml - Incrementar heap
5. disk_cleanup.yml - Limpieza de disco
6. service_restart.yml - Reinicio servicios Linux
7. sql_server_hardening.yml - Hardening SQL Server
8. emergency_notification.yml - Notificaciones
"""

def analizar_log(log_content):
    prompt = f"""Eres un experto en operaciones TI con Ansible Automation Platform (AAP/AWX).

LOG:
{log_content}

PLAYBOOKS:
{PLAYBOOKS}

Analiza y proporciona:

1. **DIAGNÓSTICO** (2-3 líneas concisas)
   - Qué pasó y causa raíz

2. **SEVERIDAD**
   - Crítico/Alto/Medio/Bajo
   - Impacto en producción

3. **SOLUCIÓN**
   - Qué playbook ejecutar y por qué

4. **EJECUCIÓN EN AAP/AWX**
   Instrucciones paso a paso desde la interfaz web:
```
   1. Templates → Buscar "[nombre_template]"
   2. Click Launch
   3. Extra Variables:
      variable1: valor1
      variable2: valor2
   4. Inventario: [nombre_inventario]
   5. Limit: [hosts_específicos] (si aplica)
   6. Launch
```

5. **VERIFICACIÓN**
   - Qué revisar después
   - Cómo confirmar resolución

Responde en español, técnico pero claro. Formato para operadores de AAP/AWX, en tu respuesta no entregue emoticones o iconos."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error: {str(e)}"

# INTERFAZ
st.title("Agente IA - Análisis de Logs")
st.markdown("**Análisis inteligente de logs con recomendaciones de playbooks Ansible**")

# Sidebar con información
with st.sidebar:
    st.header("Información")
    st.markdown("""
    **Casos de uso:**
    - Errores de Oracle Database
    - Problemas de WebLogic
    - Disco lleno en servidores
    - Fallos de servicios Linux
    
    **Capacidades:**
    - Diagnóstico automático
    - Recomendación de playbooks
    - Generación de comandos AWX
    """)
    
    st.markdown("---")
    st.markdown("**Desarrollado por:** NTT Data Automation Team")

# Tabs para diferentes modos
tab1, tab2 = st.tabs(["Pegar Log", "Logs de Ejemplo"])

with tab1:
    st.subheader("Pega tu log de error aquí")
    log_input = st.text_area(
        "Log de error:",
        height=300,
        placeholder="Pega aquí el contenido del log que deseas analizar..."
    )
    
    col1, col2 = st.columns([1, 5])
    with col1:
        analizar_btn = st.button("Analizar", type="primary", use_container_width=True)
    with col2:
        limpiar_btn = st.button("Limpiar", use_container_width=True)
    
    if limpiar_btn:
        st.rerun()
    
    if analizar_btn and log_input:
        with st.spinner("Analizando log con IA..."):
            resultado = analizar_log(log_input)
            st.success("Análisis completado")
            st.markdown("---")
            st.markdown(resultado)

with tab2:
    st.subheader("Selecciona un log de ejemplo")
    
    ejemplo_seleccionado = st.selectbox(
        "Escenario:",
        [
            "Oracle - Error ORA-00257 (Archivelog Full)",
            "WebLogic - OutOfMemoryError",
            "Linux - Disco Lleno"
        ]
    )
    
    # Cargar contenido según selección
    logs_ejemplo = {
        "Oracle - Error ORA-00257 (Archivelog Full)": "logs_ejemplo/oracle_error.log",
        "WebLogic - OutOfMemoryError": "logs_ejemplo/weblogic_error.log",
        "Linux - Disco Lleno": "logs_ejemplo/linux_disk_full.log"
    }
    
    ruta_log = logs_ejemplo[ejemplo_seleccionado]
    
    try:
        with open(ruta_log, 'r', encoding='utf-8') as f:
            contenido_ejemplo = f.read()
        
        st.code(contenido_ejemplo, language="log")
        
        if st.button("Analizar Este Ejemplo", type="primary"):
            with st.spinner("Analizando log con IA..."):
                resultado = analizar_log(contenido_ejemplo)
                st.success("Análisis completado")
                st.markdown("---")
                st.markdown(resultado)
    
    except FileNotFoundError:
        st.error(f"No se encontró el archivo: {ruta_log}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <small>Powered by Claude Sonnet 4 | Anthropic API</small>
</div>
""", unsafe_allow_html=True)
