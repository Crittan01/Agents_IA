import streamlit as st
import anthropic
import os
from dotenv import load_dotenv
from datetime import datetime
from knowledge_base import (
    PLAYBOOKS_DISPONIBLES, 
    ARBOL_DIAGNOSTICO, 
    PREGUNTAS_DIAGNOSTICO,
    COMANDOS_UTILES
)

# Cargar .env desde la raíz del proyecto
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configuración de la página
st.set_page_config(
    page_title="Agente IA - Asistente de Troubleshooting IA",
    page_icon="🩺",
    layout="wide"
)

# Inicializar cliente Anthropic
@st.cache_resource
def get_client():
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

client = get_client()

# Inicializar session state para el chat
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.diagnostico_activo = False
    st.session_state.contexto = {}

# Función para construir el contexto del sistema
def get_system_context():
    return f"""Eres un experto senior en troubleshooting de infraestructura TI con más de 15 años de experiencia.

Tu especialidad es diagnosticar problemas en:
- Oracle Database (11g, 12c, 19c)
- WebLogic Application Server
- SQL Server
- PostgreSQL con Patroni
- Servidores Linux (RHEL, SUSE)
- Infraestructura en OCI

METODOLOGÍA DE DIAGNÓSTICO:
1. Escucha el síntoma inicial del operador
2. Haz preguntas específicas y guiadas para entender el problema
3. Descarta causas una por una siguiendo árbol de decisión
4. Cuando identifiques el root cause, sugiere el playbook específico
5. Proporciona comandos útiles para validación

PLAYBOOKS DISPONIBLES:
{format_playbooks()}

ESTILO DE COMUNICACIÓN:
- Preguntas claras y específicas
- Una pregunta a la vez
- Lenguaje técnico pero comprensible
- Directo y enfocado en resolver
- Sin suposiciones, valida todo

IMPORTANTE:
- Nunca asumas información, siempre pregunta
- Si el operador no sabe algo, guíalo en cómo obtener esa información
- Proporciona comandos específicos cuando sea necesario
- Enfócate en llegar al root cause rápidamente
"""

def format_playbooks():
    """Formatea los playbooks disponibles para el contexto"""
    formatted = ""
    for categoria, playbooks in PLAYBOOKS_DISPONIBLES.items():
        formatted += f"\n{categoria.upper()}:\n"
        for nombre, desc in playbooks.items():
            formatted += f"  - {nombre}: {desc}\n"
    return formatted

def llamar_agente_ia(historial_conversacion):
    """Llama al agente con el historial completo de la conversación"""
    
    # Preparar mensajes para la API
    messages = []
    for msg in historial_conversacion:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            system=get_system_context(),
            messages=messages
        )
        return response.content[0].text
    except Exception as e:
        return f"Error al conectar con el asistente: {str(e)}"

def generar_reporte_troubleshooting():
    """Genera un reporte resumen del troubleshooting realizado"""
    
    historial_texto = "\n".join([
        f"{'OPERADOR' if msg['role'] == 'user' else 'ASISTENTE'}: {msg['content']}"
        for msg in st.session_state.messages
    ])
    
    prompt = f"""Genera un reporte técnico de troubleshooting basado en esta conversación:

{historial_texto}

El reporte debe incluir:

1. RESUMEN EJECUTIVO (2-3 líneas)
2. SÍNTOMA INICIAL
3. PROCESO DE DIAGNÓSTICO (paso a paso)
4. ROOT CAUSE IDENTIFICADO
5. SOLUCIÓN APLICADA O RECOMENDADA
6. PLAYBOOK UTILIZADO (si aplica)
7. TIEMPO DE DIAGNÓSTICO
8. RECOMENDACIONES PARA PREVENCIÓN

Formato profesional, en español, para documentación de incidentes."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error generando reporte: {str(e)}"

# ==================== INTERFAZ ====================

st.title("Agente IA - Asistente Interactivo de Troubleshooting")
st.markdown("**Diagnóstico guiado para incidentes de infraestructura**")

# Sidebar con información y comandos útiles
with st.sidebar:
    st.header("Información")
    
    # Botón para nuevo diagnóstico
    if st.button("Nuevo Diagnóstico", use_container_width=True):
        st.session_state.messages = []
        st.session_state.diagnostico_activo = False
        st.session_state.contexto = {}
        st.rerun()
    
    st.markdown("---")
    
    # Estadísticas de la sesión
    if st.session_state.messages:
        num_preguntas = len([m for m in st.session_state.messages if m["role"] == "user"])
        num_respuestas = len([m for m in st.session_state.messages if m["role"] == "assistant"])
        st.metric("Mensajes intercambiados", num_preguntas + num_respuestas)
        st.metric("Preguntas realizadas", num_preguntas)
    
    st.markdown("---")
    
    # Comandos útiles expandibles
    with st.expander("Comandos Útiles", expanded=False):
        tecnologia = st.selectbox("Tecnología:", ["Oracle", "Linux", "WebLogic"])
        
        if tecnologia == "Oracle":
            st.code(COMANDOS_UTILES["oracle"]["sesiones_activas"], language="sql")
            st.code(COMANDOS_UTILES["oracle"]["tablespaces"], language="sql")
        elif tecnologia == "Linux":
            st.code(COMANDOS_UTILES["linux"]["disco_uso"], language="bash")
            st.code(COMANDOS_UTILES["linux"]["procesos_top"], language="bash")
        elif tecnologia == "WebLogic":
            st.markdown(COMANDOS_UTILES["weblogic"]["datasources"])
    
    st.markdown("---")
    st.markdown("**Desarrollado por:** NTT Data Automation Team")

# Área principal - Chat
st.markdown("### Conversación de Diagnóstico")

# Mostrar historial de mensajes
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Mensaje de bienvenida si es la primera vez
if not st.session_state.messages:
    with st.chat_message("assistant"):
        mensaje_bienvenida = """Hola, soy tu asistente de troubleshooting.

Describe el problema que estás experimentando y te ayudaré a diagnosticarlo paso a paso.

**Ejemplos de síntomas:**
- "La aplicación está muy lenta"
- "No puedo conectarme a la base de datos"
- "El disco está lleno en el servidor"
- "WebLogic se cayó y no levanta"
- "Los usuarios reportan errores al guardar"

¿Qué problema estás teniendo?"""
        st.markdown(mensaje_bienvenida)
        st.session_state.messages.append({
            "role": "assistant",
            "content": mensaje_bienvenida
        })

# Input del usuario
if prompt := st.chat_input("Describe el problema o responde la pregunta..."):
    # Agregar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Mostrar mensaje del usuario
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Obtener respuesta del asistente
    with st.chat_message("assistant"):
        with st.spinner("Analizando..."):
            respuesta = llamar_agente_ia(st.session_state.messages)
            st.markdown(respuesta)
            st.session_state.messages.append({
                "role": "assistant",
                "content": respuesta
            })

# Botón para generar reporte al final
if len(st.session_state.messages) > 4:  # Al menos 2 intercambios
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col2:
        if st.button("Generar Reporte", use_container_width=True):
            with st.spinner("Generando reporte de troubleshooting..."):
                reporte = generar_reporte_troubleshooting()
                st.session_state.reporte_generado = reporte
    
    with col3:
        if st.button("Descargar Chat", use_container_width=True):
            chat_texto = "\n\n".join([
                f"{'[OPERADOR]' if msg['role'] == 'user' else '[ASISTENTE]'}\n{msg['content']}"
                for msg in st.session_state.messages
            ])
            st.download_button(
                label="Descargar TXT",
                data=chat_texto,
                file_name=f"troubleshooting_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

# Mostrar reporte si fue generado
if "reporte_generado" in st.session_state and st.session_state.reporte_generado:
    st.markdown("---")
    st.markdown("### Reporte de Troubleshooting")
    st.markdown(st.session_state.reporte_generado)
    
    st.download_button(
        label="Descargar Reporte",
        data=st.session_state.reporte_generado,
        file_name=f"reporte_troubleshooting_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain",
        use_container_width=True
    )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <small>Powered by Claude Sonnet 4 | Troubleshooting Assistant</small>
</div>
""", unsafe_allow_html=True)