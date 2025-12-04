import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
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
    # 1. Configurar LLM (OpenRouter)
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY no está configurada en el archivo .env")

    llm = ChatOpenAI(
        model="meta-llama/llama-3.1-8b-instruct",
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
    
    tools = [rag_tool, calcular_vacaciones]

    # 3. Configurar Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Eres un asistente de RRHH útil y amable. Usa las herramientas disponibles para responder a las preguntas de los empleados. Si no sabes la respuesta, dilo honestamente."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    # 4. Crear Agente
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # 5. Crear Executor
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    return agent_executor
