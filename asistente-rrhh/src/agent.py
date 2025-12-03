import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_hub import pull
from langchain.agents import create_openai_tools_agent, AgentExecutor

# --- Importación de herramientas locales ---
from src.tools import calcular_vacaciones
from src.rag import get_retriever_tool

# Cargar variables de entorno desde el archivo .env
load_dotenv()

def create_agent_executor():
    """
    Crea y configura el agente principal y su ejecutor.

    Esta función realiza los siguientes pasos:
    1.  Inicializa el modelo de lenguaje (LLM) a través de OpenRouter.
    2.  Obtiene las herramientas disponibles (cálculo de vacaciones y búsqueda en manual).
    3.  Descarga un prompt pre-configurado desde LangChain Hub.
    4.  Crea el agente combinando el LLM, las herramientas y el prompt.
    5.  Envuelve el agente en un AgentExecutor para poder invocarlo.

    Returns:
        AgentExecutor: El ejecutor del agente, listo para procesar consultas.
    """
    print("Inicializando el agente...")

    # 1. Inicializar el LLM
    # Se utiliza el modelo Llama 3.1 de Meta a través de OpenRouter.
    # Es necesario tener OPENAI_API_KEY y OPENAI_API_BASE configurados en .env.
    llm = ChatOpenAI(
        model="meta-llama/llama-3.1-8b-instruct",
        temperature=0,  # Temperatura 0 para respuestas más predecibles
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE"),
    )

    # 2. Obtener las herramientas
    # La herramienta de retriever se obtiene de nuestro módulo RAG.
    # La herramienta de cálculo de vacaciones se importa directamente.
    retriever_tool = get_retriever_tool()
    tools = [retriever_tool, calcular_vacaciones]
    
    print(f"Herramientas cargadas: {[tool.name for tool in tools]}")

    # 3. Descargar el prompt desde LangChain Hub
    # Este prompt está diseñado para que los modelos de OpenAI (y compatibles)
    # funcionen bien como agentes con herramientas.
    prompt = pull("hwchase17/openai-functions-agent")

    # 4. Crear el agente
    # Combina el LLM, el prompt y las herramientas en un agente funcional.
    agent = create_openai_tools_agent(llm, tools, prompt)

    # 5. Crear el AgentExecutor
    # El executor es el que realmente corre el agente, llama a las herramientas
    # y gestiona el flujo de la conversación.
    # `verbose=True` es útil para depuración, muestra los pasos del agente.
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True
    )

    print("Agente inicializado correctamente.")
    return agent_executor

# --- Bloque para ejecución directa (para pruebas) ---
if __name__ == '__main__':
    # Este bloque permite probar el agente directamente desde la consola.
    executor = create_agent_executor()
    
    print("\n--- Probando el agente ---")
    print("Puedes hacer preguntas como:")
    print("- ¿Cuál es la política de teletrabajo?")
    print("- ¿Cuántos días de vacaciones le quedan a Ana (ID E001)?")
    print("- ¿Y a Carlos? su id es E002")
    
    while True:
        try:
            query = input("\nIntroduce tu pregunta (o 'salir' para terminar): ")
            if query.lower() == 'salir':
                break
            
            # Invocar el agente con la pregunta y un historial de chat vacío
            response = executor.invoke({
                "input": query,
                "chat_history": [] 
            })
            
            print("\nRespuesta del agente:")
            print(response["output"])

        except KeyboardInterrupt:
            print("\nSaliendo...")
            break
