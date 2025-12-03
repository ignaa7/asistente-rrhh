import streamlit as st
from src.agent import create_agent_executor

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Asistente de RRHH", page_icon="🤖", layout="centered")

# --- ESTADO DE LA SESIÓN ---
# El estado de la sesión de Streamlit nos permite mantener información
# entre diferentes interacciones del usuario.

# Inicializar el historial de chat si no existe.
# 'messages' será una lista de diccionarios, cada uno con un 'role' y 'content'.
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! Soy tu asistente de RRHH. ¿En qué puedo ayudarte hoy sobre nuestras políticas o tus vacaciones?"}
    ]

# Inicializar el ejecutor del agente.
# Esto previene que el agente se recargue cada vez que el usuario interactúa
# con la UI, lo que mejora significativamente el rendimiento.
if "agent_executor" not in st.session_state:
    with st.spinner("Iniciando el asistente, por favor espera..."):
        # La función create_agent_executor() viene de nuestro módulo 'agent.py'
        st.session_state.agent_executor = create_agent_executor()


# --- TÍTULO Y DESCRIPCIÓN ---
st.title("🤖 Asistente Virtual de RRHH")
st.caption("Puedo responder preguntas sobre el manual del empleado o consultar tus días de vacaciones.")

# --- MOSTRAR HISTORIAL DE CHAT ---
# Itera sobre todos los mensajes guardados en el estado de la sesión
# y los muestra en la interfaz.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- ENTRADA DEL USUARIO ---
# Crea un campo de entrada de chat anclado en la parte inferior de la página.
if prompt := st.chat_input("Escribe tu pregunta aquí..."):
    # 1. Añadir y mostrar el mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Obtener y mostrar la respuesta del asistente
    with st.chat_message("assistant"):
        # Muestra un indicador de que el asistente está "pensando"
        with st.spinner("Pensando..."):
            # Invocar al agente con la pregunta del usuario
            response = st.session_state.agent_executor.invoke({
                "input": prompt,
                # El historial de chat se podría incluir aquí si el agente
                # lo necesitara para mantener contexto en conversaciones largas.
                "chat_history": [] 
            })
            
            # Extraer y mostrar la respuesta
            assistant_response = response.get("output", "No he podido encontrar una respuesta.")
            st.markdown(assistant_response)
    
    # 3. Añadir la respuesta del asistente al historial
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
