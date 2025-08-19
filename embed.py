import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from load_chunk import LoadandChunk

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
persist_dir = "chroma-db"

def get_vectorstore(persist_directory: str = "chroma-db", source_dir: str = "MR-releaseNotes") -> Chroma:
    """
    Load existing Chroma DB if present, otherwise build from PDFs and persist.
    """
    # If DB exists and is non-empty, load without re-embedding
    if os.path.isdir(persist_directory) and os.listdir(persist_directory):
        vs = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
        print("Chroma vector db loaded from disk")
        return vs

    # Build and persist
    document_chunks = LoadandChunk().load_and_chunk(source_dir)
    vs = Chroma.from_documents(
        documents=document_chunks,
        embedding=embeddings,
        persist_directory=persist_directory,
    )
    print("Chroma vector db built and persisted")
    return vs

# Provide a default vectorstore on import while avoiding re-embedding if persisted DB exists
vectorstore = get_vectorstore()