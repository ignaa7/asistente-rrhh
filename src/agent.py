from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.retriever import create_retriever_tool
from langchain.memory import ConversationSummaryBufferMemory
from src.rag import get_retriever
from src.tools import calcular_vacaciones, solicitar_vacaciones, reportar_baja_medica, consultar_nomina, actualizar_baja_medica, consultar_bajas_medicas, consultar_solicitudes_vacaciones
import streamlit as st

# Cargar variables de entorno (Managed by Streamlit Secrets)

def get_agent(memory=None, user_context=None):
    """
    Configura y devuelve el AgentExecutor listo para usar.
    
    Args:
        memory: Objeto de memoria conversacional (ConversationBufferMemory). 
                Si no se proporciona, se crea uno nuevo.
        user_context: Diccionario con información del usuario logueado.
                     Ejemplo: {"id": "E001", "nombre": "Ana", "cargo": "Desarrolladora"}
    """
    # 1. Configurar LLM (OpenRouter con GPT-3.5-turbo)
    # Usar st.secrets para obtener la clave API
    try:
        api_key = st.secrets["OPENROUTER_API_KEY"]
    except KeyError:
        raise ValueError("OPENROUTER_API_KEY no está configurada en los secrets de Streamlit (.streamlit/secrets.toml o deployment secrets)")

    llm = ChatOpenAI(
        model="openai/gpt-3.5-turbo",
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0
    )

    # 2. Configurar Herramientas
    # Herramienta RAG
    retriever = get_retriever()
    rag_tool = create_retriever_tool(
        retriever,
        "buscar_politicas_rrhh",
        "Busca información sobre políticas de recursos humanos, teletrabajo, bajas médicas y beneficios en el manual del empleado."
    )
    
    tools = [rag_tool, calcular_vacaciones, solicitar_vacaciones, reportar_baja_medica, actualizar_baja_medica, consultar_bajas_medicas, consultar_solicitudes_vacaciones, consultar_nomina]

    # 3. Configurar Memoria si no se proporciona
    if memory is None:
        from langchain.memory import ConversationBufferMemory
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )

    # 4. Configurar Prompt con contexto del usuario
    # Construir información del usuario para el sistema
    from datetime import datetime
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    
    user_info = f"FECHA ACTUAL: {fecha_actual}\n"
    if user_context:
        user_info += f"""
INFORMACIÓN DEL USUARIO ACTUAL:
- Nombre: {user_context['nombre']}
- ID de Empleado: {user_context['id']}
- Cargo: {user_context['cargo']}
- Vacaciones totales: {user_context['vacaciones_totales']} días
- Vacaciones usadas: {user_context['vacaciones_usadas']} días
- Vacaciones restantes: {user_context['vacaciones_totales'] - user_context['vacaciones_usadas']} días

IMPORTANTE: El usuario ya está autenticado en el sistema. Cuando use herramientas que requieren id_empleado, 
usa automáticamente '{user_context['id']}' sin pedírselo al usuario. El usuario NO necesita decirte su ID.
Dirígete al usuario por su nombre ({user_context['nombre']}) de forma natural y cercana.
"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""Eres un asistente de RRHH útil y amable. 

{user_info}

Cuando un empleado te haga una pregunta:
1. Recuerda el contexto de la conversación actual y la información del usuario logueado
2. Usa las herramientas disponibles para buscar la información necesaria
3. Lee CUIDADOSAMENTE la información que te devuelven las herramientas
4. Responde basándote en esa información de forma clara y directa
5. Si la información recuperada responde la pregunta, úsala para dar una respuesta completa

IMPORTANTE: Si la herramienta te devuelve información relevante, NO digas que no tienes información. Usa lo que te devuelve la herramienta para responder.

================================================================================
CRITICAL INSTRUCTION: LANGUAGE DETECTION
================================================================================
You MUST detect the language of the user's LAST message and respond in THAT SAME LANGUAGE.
This instruction OVERRIDES all others regarding language.

- User: "Hola" -> You: "Hola..." (Spanish)
- User: "Hello" -> You: "Hello..." (English)
- User: "Je veux des vacances" -> You: "Bien sûr, je peux vous aider..." (French)
- User: "Guten Morgen" -> You: "Guten Morgen..." (German)

DO NOT RESPOND IN SPANISH IF THE USER SPEAKS FRENCH/ENGLISH/ETC.
TRANSLATE YOUR FINAL ANSWER TO THE USER'S LANGUAGE.
================================================================================"""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    # 5. Crear Agente
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # 6. Crear Executor con memoria
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        memory=memory,
        verbose=True
    )
    
    return agent_executor
