import sys
import os

# Añadir src al path
sys.path.append(os.path.join(os.getcwd(), "src"))

from rag import get_retriever

print("Iniciando prueba de RAG con nuevos documentos...")

try:
    retriever = get_retriever()
    
    # Preguntas de prueba sobre los nuevos temas
    preguntas = [
        "¿Cuánto pagan por kilometraje?",
        "¿Cuál es el código de vestimenta?",
        "¿Cuándo es la revisión salarial?",
        "¿Tengo presupuesto para cursos?"
    ]
    
    for p in preguntas:
        print(f"\nPregunta: {p}")
        docs = retriever.invoke(p)
        if docs:
            print(f"✅ Respuesta encontrada en: {docs[0].metadata.get('source', 'Desconocido')}")
            print(f"Fragmento: {docs[0].page_content[:150]}...")
        else:
            print("❌ No se encontraron documentos.")
            
except Exception as e:
    print(f"❌ Error: {e}")
