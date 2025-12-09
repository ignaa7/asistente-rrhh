import os
import pickle
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
DB_PATH = os.path.join(BASE_DIR, "faiss_db")

def get_retriever():
    """
    Inicializa y devuelve el retriever configurado.
    Si la base de datos ya existe, la carga. Si no, la crea.
    Usa Hybrid Search (BM25 + FAISS) para mejor precisión.
    """
    # 1. Usar Embeddings Multilingües más potentes
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    
    # Verificamos si ya existe la DB persistida
    index_path = os.path.join(DB_PATH, "index")
    
    # NOTA: Para desarrollo, forzamos la recreación si hay nuevos archivos
    if os.path.exists(index_path + ".faiss"):
        print("Cargando base de datos vectorial existente...")
        vectorstore = FAISS.load_local(
            DB_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
        
        # Necesitamos cargar los documentos originales para BM25 también
        # En un sistema real, guardaríamos el índice BM25 persistido también
        # Aquí lo reconstruimos rápido (es memoria)
        docs = _load_docs()
        splits = _split_docs(docs)
        
    else:
        print("Inicializando base de datos vectorial...")
        docs = _load_docs()
        splits = _split_docs(docs)
        
        vectorstore = FAISS.from_documents(
            documents=splits,
            embedding=embeddings
        )
        
        # Guardar la base de datos
        os.makedirs(DB_PATH, exist_ok=True)
        vectorstore.save_local(DB_PATH)
    
    # 2. Configurar Retrievers
    # BM25 (Keyword Search)
    bm25_retriever = BM25Retriever.from_documents(splits)
    bm25_retriever.k = 3
    
    # FAISS (Semantic Search)
    faiss_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    # 3. Ensemble (Hybrid Search)
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, faiss_retriever],
        weights=[0.5, 0.5]
    )
    
    return ensemble_retriever

def _load_docs():
    """Helper para cargar documentos"""
    if not os.path.exists(DOCS_DIR):
        raise FileNotFoundError(f"No se encontró el directorio de documentación en: {DOCS_DIR}")
        
    docs = []
    for filename in os.listdir(DOCS_DIR):
        if filename.endswith(".md"):
            file_path = os.path.join(DOCS_DIR, filename)
            loader = UnstructuredMarkdownLoader(file_path)
            docs.extend(loader.load())
    
    if not docs:
        raise ValueError("No se encontraron documentos .md en el directorio docs/")
    return docs

def _split_docs(docs):
    """Helper para dividir documentos"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    return text_splitter.split_documents(docs)

if __name__ == "__main__":
    # Test simple
    retriever = get_retriever()
    docs = retriever.invoke("teletrabajo")
    print(f"Documentos recuperados: {len(docs)}")
    print(docs[0].page_content)
