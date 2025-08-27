import os
import logging
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from app.load_chunk import LoadandChunk
from dotenv import load_dotenv
load_dotenv()


logger = logging.getLogger(__name__)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def get_vectorstore(pdf_dir: str, html_dir: str, html_file: str, persist_directory: str = "chroma-db", ) -> Chroma:
   
    if os.path.isdir(persist_directory) and os.listdir(persist_directory):
        vs = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
        logger.info("Chroma vector db loaded from disk from '%s'", persist_directory)
        return vs
    
    load = LoadandChunk()
    document_chunks = load.load_chunk_pdf(pdf_dir)

    all_docs = document_chunks 

    vs = Chroma.from_documents(
        documents=all_docs,
        embedding=embeddings,
        persist_directory=persist_directory,
    )
    logger.info("Chroma vector db built and persisted to '%s' (docs=%d)", persist_directory, len(all_docs))
    return vs


_DEFAULT_PDF_DIR = os.getenv("PDF_DIR", "none")
_DEFAULT_HTML_DIR = os.getenv("HTML_DIR", "none")
_DEFAULT_HTML_FILE = os.getenv("HTML_FILE", "none")
_DEFAULT_DB_DIR = os.getenv("DB_DIR", "chroma-db")
vectorstore = get_vectorstore(_DEFAULT_PDF_DIR, _DEFAULT_HTML_DIR, _DEFAULT_HTML_FILE, _DEFAULT_DB_DIR)