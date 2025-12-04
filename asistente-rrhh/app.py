import streamlit as st
from src.agent import get_agent

st.set_page_config(page_title="Asistente RRHH", page_icon="👔")

st.title("👔 Asistente Virtual de RRHH")
st.markdown("""
Bienvenido al asistente de RRHH. Puedes preguntarme sobre:
- **Políticas de la empresa** (vacaciones, teletrabajo, bajas...)
- **Tus días de vacaciones** (necesitaré tu ID de empleado, ej: E001, E002)
""")

# Inicializar historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Inicializar agente (solo una vez)
if "agent" not in st.session_state:
    try:
        with st.spinner("Iniciando el sistema..."):
            st.session_state.agent = get_agent()
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
            response = st.session_state.agent.invoke({"input": prompt})
            output_text = response["output"]
            st.markdown(output_text)
            
            # Guardar respuesta en historial
            st.session_state.messages.append({"role": "assistant", "content": output_text})
        except Exception as e:
            st.error(f"Ocurrió un error: {e}")
