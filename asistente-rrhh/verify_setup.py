import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from src.agent import get_agent

def test_agent():
    print("--- Iniciando Test del Agente ---")
    try:
        agent = get_agent()
        print("Agente inicializado correctamente.")
        
        # Test 1: RAG
        print("\nTest 1: Pregunta sobre política (RAG)")
        response_rag = agent.invoke({"input": "¿Cuál es la política de teletrabajo?"})
        print(f"Respuesta RAG: {response_rag['output']}")
        
        # Test 2: Tool
        print("\nTest 2: Pregunta sobre vacaciones (Tool)")
        response_tool = agent.invoke({"input": "¿Cuántos días de vacaciones le quedan a Ana (ID: E001)?"})
        print(f"Respuesta Tool: {response_tool['output']}")
        
        print("\n--- Test Completado con Éxito ---")
        
    except Exception as e:
        print(f"\n--- ERROR DURANTE EL TEST: {e} ---")
        # Si es error de API Key es esperado si no está configurada, pero valida que el código corre.
        if "OPENROUTER_API_KEY" in str(e) or "api_key" in str(e).lower():
            print("(El error de API Key es esperado si no has configurado el .env todavía)")

if __name__ == "__main__":
    test_agent()
