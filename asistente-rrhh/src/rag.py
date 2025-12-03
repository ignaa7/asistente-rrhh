import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain.tools.retriever import create_retriever_tool

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# --- CONSTANTES Y CONFIGURACIÓN ---
# Ruta al directorio que contendrá la base de datos vectorial
PERSIST_DIRECTORY = "db"
# Ruta al manual del empleado
DOCS_PATH = "docs/manual_empleado.md"

def _crear_y_almacenar_vectores():
    """
    Función interna para cargar el documento, dividirlo en fragmentos,
    generar embeddings y almacenarlos en una base de datos vectorial Chroma.
    Esta función solo se ejecuta si la base de datos no existe.
    """
    print("Creando nueva base de datos de vectores...")
    
    # 1. Cargar el documento markdown
    loader = UnstructuredMarkdownLoader(DOCS_PATH)
    docs = loader.load()

    # 2. Definir la estructura de encabezados para dividir el documento
    # Esto ayuda a mantener el contexto de cada fragmento.
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
    ]

    # 3. Dividir el documento en base a los encabezados
    text_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    splits = text_splitter.split_text(docs[0].page_content)

    # 4. Inicializar el modelo de embeddings (usando OpenRouter)
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small", # Modelo de embeddings recomendado
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE"),
    )

    # 5. Crear la base de datos Chroma a partir de los fragmentos
    # y configurarla para que persista en disco.
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=PERSIST_DIRECTORY
    )
    print("Base de datos de vectores creada y guardada.")
    return vectorstore

def get_retriever_tool():
    """
    Función principal que crea y devuelve una herramienta de retriever para LangChain.

    Verifica si la base de datos vectorial ya existe. Si no, la crea.
    Luego, inicializa el retriever y lo empaqueta como una herramienta
    que el agente de LangChain puede utilizar.
    
    Returns:
        Tool: Una herramienta de LangChain que el agente puede usar para buscar
              información en el manual del empleado.
    """
    # Inicializar el modelo de embeddings
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE"),
    )

    # Comprobar si la base de datos ya existe, si no, crearla
    if not os.path.exists(PERSIST_DIRECTORY):
        vectorstore = _crear_y_almacenar_vectores()
    else:
        print("Cargando base de datos de vectores existente.")
        vectorstore = Chroma(
            persist_directory=PERSIST_DIRECTORY,
            embedding_function=embeddings
        )
    
    # Crear un retriever a partir de la base de datos vectorial
    # k=2 indica que recuperaremos los 2 fragmentos más relevantes.
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

    # Crear la herramienta de retriever para el agente
    retriever_tool = create_retriever_tool(
        retriever,
        "buscador_manual_empleado",
        "Busca y devuelve información sobre las políticas de la empresa, como la política de vacaciones, teletrabajo, bajas médicas y beneficios para empleados. Úsalo para responder preguntas generales sobre normativas."
    )
    
    return retriever_tool

# --- Bloque para ejecución directa (para pruebas) ---
if __name__ == '__main__':
    print("Probando la creación de la herramienta de retriever...")
    tool = get_retriever_tool()
    print("\nHerramienta creada exitosamente:")
    print(f"Nombre: {tool.name}")
    print(f"Descripción: {tool.description}")
    
    # Prueba de búsqueda
    print("\nRealizando una búsqueda de prueba sobre 'vacaciones'...")
    test_retriever = tool.func.retriever
    results = test_retriever.invoke("cuántos días de vacaciones tengo")
    print(f"Se encontraron {len(results)} resultados.")
    for doc in results:
        print("---")
        print(doc.page_content)
