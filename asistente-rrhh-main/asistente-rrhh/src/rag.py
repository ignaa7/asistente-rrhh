import os
import pickle
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_PATH = os.path.join(BASE_DIR, "docs", "manual_empleado.md")
DB_PATH = os.path.join(BASE_DIR, "faiss_db")

def get_retriever():
    """
    Inicializa y devuelve el retriever configurado.
    Si la base de datos ya existe, la carga. Si no, la crea.
    """
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Verificamos si ya existe la DB persistida
    index_path = os.path.join(DB_PATH, "index")
    
    if os.path.exists(index_path + ".faiss"):
        print("Cargando base de datos vectorial existente...")
        vectorstore = FAISS.load_local(
            DB_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
    else:
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
        
        vectorstore = FAISS.from_documents(
            documents=splits,
            embedding=embeddings
        )
        
        # Guardar la base de datos
        os.makedirs(DB_PATH, exist_ok=True)
        vectorstore.save_local(DB_PATH)
    
    # Devolvemos el retriever
    return vectorstore.as_retriever(search_kwargs={"k": 3})

if __name__ == "__main__":
    # Test simple
    retriever = get_retriever()
    docs = retriever.invoke("teletrabajo")
    print(f"Documentos recuperados: {len(docs)}")
    print(docs[0].page_content)
