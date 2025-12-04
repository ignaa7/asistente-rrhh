import os
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_PATH = os.path.join(BASE_DIR, "docs", "manual_empleado.md")
DB_PATH = os.path.join(BASE_DIR, "chroma_db")

def get_retriever():
    """
    Inicializa y devuelve el retriever configurado.
    Si la base de datos ya existe, la carga. Si no, la crea.
    """
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Verificamos si ya existe la DB persistida (comprobación básica de directorio)
    # Para este MVP, recrearemos la DB si no existe, o la cargaremos.
    # En producción, idealmente se verifica si hay contenido o se actualiza.
    
    if not os.path.exists(DB_PATH) or not os.listdir(DB_PATH):
        print("Inicializando base de datos vectorial...")
        if not os.path.exists(DOCS_PATH):
            raise FileNotFoundError(f"No se encontró el manual en: {DOCS_PATH}")
            
        loader = UnstructuredMarkdownLoader(DOCS_PATH)
        docs = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(docs)
        
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=DB_PATH
        )
    else:
        print("Cargando base de datos vectorial existente...")
        vectorstore = Chroma(
            persist_directory=DB_PATH,
            embedding_function=embeddings
        )
    
    # Devolvemos el retriever
    return vectorstore.as_retriever(search_kwargs={"k": 3})

if __name__ == "__main__":
    # Test simple
    retriever = get_retriever()
    docs = retriever.invoke("teletrabajo")
    print(f"Documentos recuperados: {len(docs)}")
    print(docs[0].page_content)
