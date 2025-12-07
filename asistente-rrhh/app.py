import streamlit as st
from src.agent import get_agent
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

st.set_page_config(
    page_title="Asistente RRHH",
    page_icon="👔",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================== MAIN CONTENT ====================
st.title("👔 Asistente Virtual de RRHH")
st.markdown("""
Bienvenido al asistente de RRHH. Puedes preguntarme sobre:
- **Políticas de la empresa** (vacaciones, teletrabajo, bajas...)
- **Tus días de vacaciones** (necesitaré tu ID de empleado, ej: E001, E002)
- **Solicitar vacaciones o reportar bajas médicas**

💡 *Ahora recuerdo el contexto de nuestra conversación*
""")

# Inicializar historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Inicializar avatares
if "user_avatar" not in st.session_state:
    st.session_state.user_avatar = "👤"  # Emoji por defecto, se puede cambiar por imagen

if "assistant_avatar" not in st.session_state:
    st.session_state.assistant_avatar = "🤖"  # Emoji por defecto

# ==================== SIDEBAR ====================
with st.sidebar:
    st.title("👔 Asistente RRHH")
    st.markdown("---")
    
    # Botón para limpiar historial con confirmación
    st.subheader("⚙️ Opciones")
    
    if st.button("🗑️ Limpiar Historial", use_container_width=True):
        st.session_state.show_confirm_clear = True
    
    # Diálogo de confirmación
    if st.session_state.get("show_confirm_clear", False):
        st.warning("⚠️ ¿Estás seguro de que quieres borrar todo el historial?")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Sí", use_container_width=True):
                # Limpiar TODO: historial visual + memoria del agente
                st.session_state.messages = []
                
                # Reinicializar memoria simple
                st.session_state.memory = ConversationBufferMemory(
                    memory_key="chat_history",
                    return_messages=True,
                    output_key="output"
                )
                
                # Reinicializar agente con nueva memoria
                st.session_state.agent = get_agent(memory=st.session_state.memory)
                st.session_state.show_confirm_clear = False
                st.rerun()
        
        with col2:
            if st.button("❌ No", use_container_width=True):
                st.session_state.show_confirm_clear = False
                st.rerun()
    
    st.markdown("---")
    
    # Botones para exportar conversación
    st.subheader("📥 Exportar Conversación")
    
    if st.session_state.messages:
        from datetime import datetime
        
        # Generar contenido para exportar
        def generar_contenido_txt():
            """Genera el contenido en formato .txt"""
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            num_mensajes = len(st.session_state.messages)
            
            contenido = f"CONVERSACIÓN CON ASISTENTE DE RRHH\n"
            contenido += f"Exportado: {timestamp}\n"
            contenido += f"Total de mensajes: {num_mensajes}\n"
            contenido += f"{'='*60}\n\n"
            
            for i, msg in enumerate(st.session_state.messages, 1):
                rol = "USUARIO" if msg["role"] == "user" else "ASISTENTE"
                contenido += f"[{i}] {rol}:\n"
                contenido += f"{msg['content']}\n\n"
                contenido += f"{'-'*60}\n\n"
            
            return contenido
        
        def generar_contenido_md():
            """Genera el contenido en formato .md"""
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            num_mensajes = len(st.session_state.messages)
            
            contenido = f"# Conversación con Asistente de RRHH\n\n"
            contenido += f"**Exportado:** {timestamp}  \n"
            contenido += f"**Total de mensajes:** {num_mensajes}\n\n"
            contenido += f"---\n\n"
            
            for i, msg in enumerate(st.session_state.messages, 1):
                if msg["role"] == "user":
                    contenido += f"## 👤 Usuario (Mensaje {i})\n\n"
                else:
                    contenido += f"## 🤖 Asistente (Mensaje {i})\n\n"
                
                contenido += f"{msg['content']}\n\n"
                contenido += f"---\n\n"
            
            return contenido
        
        # Botón para exportar como .txt
        contenido_txt = generar_contenido_txt()
        st.download_button(
            label="📄 Exportar como TXT",
            data=contenido_txt,
            file_name=f"conversacion_rrhh_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
        
        # Botón para exportar como .md
        contenido_md = generar_contenido_md()
        st.download_button(
            label="📝 Exportar como MD",
            data=contenido_md,
            file_name=f"conversacion_rrhh_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )
    else:
        st.info("💬 No hay conversación para exportar todavía")
    
    st.markdown("---")
    
    # Preguntas Frecuentes (FAQs)
    st.subheader("❓ Preguntas Frecuentes")
    st.markdown("*Haz click para preguntar:*")
    
    faqs = [
        ("📅 Días de vacaciones", "¿Cuántos días de vacaciones tengo?"),
        ("✈️ Solicitar vacaciones", "¿Cómo solicito vacaciones?"),
        ("🏠 Política teletrabajo", "¿Cuál es la política de teletrabajo?"),
        ("🏥 Reportar baja médica", "¿Cómo reporto una baja médica?"),
        ("🎁 Beneficios", "¿Qué beneficios tengo como empleado?")
    ]
    
    for label, question in faqs:
        if st.button(label, use_container_width=True):
            # Guardar la pregunta seleccionada para procesarla
            st.session_state.faq_question = question
            st.rerun()


# Inicializar memoria conversacional (solo una vez)
if "memory" not in st.session_state:
    try:
        # Crear memoria conversacional simple (sin conteo de tokens)
        st.session_state.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )
    except Exception as e:
        st.error(f"Error al inicializar la memoria: {e}")
        st.stop()

# Inicializar agente (solo una vez) con la memoria
if "agent" not in st.session_state:
    try:
        with st.spinner("Iniciando el sistema..."):
            st.session_state.agent = get_agent(memory=st.session_state.memory)
    except Exception as e:
        st.error(f"Error al iniciar el agente: {e}")
        st.stop()

# Mostrar mensajes del historial con avatares
for message in st.session_state.messages:
    avatar = st.session_state.user_avatar if message["role"] == "user" else st.session_state.assistant_avatar
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Procesar pregunta FAQ si existe
if st.session_state.get("faq_question"):
    prompt = st.session_state.faq_question
    st.session_state.faq_question = None  # Limpiar después de usar
    
    # Guardar y mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=st.session_state.user_avatar):
        st.markdown(prompt)
    
    # Generar respuesta
    with st.chat_message("assistant", avatar=st.session_state.assistant_avatar):
        try:
            with st.spinner("Pensando..."):
                response = st.session_state.agent.invoke({"input": prompt})
                output_text = response["output"]
                st.markdown(output_text)
                
                # Guardar respuesta en historial de Streamlit
                st.session_state.messages.append({"role": "assistant", "content": output_text})
                st.rerun()  # Forzar actualización del sidebar
        except Exception as e:
            st.error(f"Ocurrió un error: {e}")

# Input del usuario
if prompt := st.chat_input("¿En qué puedo ayudarte hoy?"):
    # Guardar y mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=st.session_state.user_avatar):
        st.markdown(prompt)

    # Generar respuesta
    with st.chat_message("assistant", avatar=st.session_state.assistant_avatar):
        try:
            with st.spinner("Pensando..."):
                # El agente ahora usa la memoria automáticamente
                response = st.session_state.agent.invoke({"input": prompt})
                output_text = response["output"]
                st.markdown(output_text)
                
                # Guardar respuesta en historial de Streamlit
                st.session_state.messages.append({"role": "assistant", "content": output_text})
                st.rerun()  # Forzar actualización del sidebar
                
        except Exception as e:
            st.error(f"Ocurrió un error: {e}")
