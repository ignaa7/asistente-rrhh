import streamlit as st
from src.agent import get_agent
from langchain.memory import ConversationSummaryBufferMemory
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

st.set_page_config(page_title="Asistente RRHH", page_icon="👔")

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

# Inicializar memoria conversacional (solo una vez)
if "memory" not in st.session_state:
    try:
        # Crear LLM para la memoria
        api_key = os.getenv("GOOGLE_API_KEY")
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0
        )
        
        # Crear memoria con resumen + buffer
        st.session_state.memory = ConversationSummaryBufferMemory(
            llm=llm,
            max_token_limit=1000,  # Mantiene resumen + últimos mensajes hasta 1000 tokens
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

# Mostrar mensajes del historial
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input del usuario
if prompt := st.chat_input("¿En qué puedo ayudarte hoy?"):
    # Guardar y mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generar respuesta
    with st.chat_message("assistant"):
        try:
            # El agente ahora usa la memoria automáticamente
            response = st.session_state.agent.invoke({"input": prompt})
            output_text = response["output"]
            st.markdown(output_text)
            
            # Guardar respuesta en historial de Streamlit
            st.session_state.messages.append({"role": "assistant", "content": output_text})
            
        except Exception as e:
            st.error(f"Ocurrió un error: {e}")
