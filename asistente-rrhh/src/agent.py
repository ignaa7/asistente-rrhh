import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools.retriever import create_retriever_tool
from src.rag import get_retriever
from src.tools import calcular_vacaciones

# Cargar variables de entorno
load_dotenv()

def get_agent():
    """
    Configura y devuelve el AgentExecutor listo para usar.
    """
    # 1. Configurar LLM (Google Gemini)
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY no está configurada en el archivo .env")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
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
    
    tools = [rag_tool, calcular_vacaciones]

    # 3. Configurar Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Eres un asistente de RRHH útil y amable. 

Cuando un empleado te haga una pregunta:
1. Usa las herramientas disponibles para buscar la información necesaria
2. Lee CUIDADOSAMENTE la información que te devuelven las herramientas
3. Responde basándote en esa información de forma clara y directa
4. Si la información recuperada responde la pregunta, úsala para dar una respuesta completa

IMPORTANTE: Si la herramienta te devuelve información relevante, NO digas que no tienes información. Usa lo que te devuelve la herramienta para responder."""),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    # 4. Crear Agente
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # 5. Crear Executor
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    return agent_executor
