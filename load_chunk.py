from langchain_community.document_loaders import PyPDFDirectoryLoader
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter

class LoadandChunk:
    def __init__(self):
        pass

    def load(self):
        pass

    def load_and_chunk(self, pdf_dir):

        if not os.path.exists(os.path.join(os.getcwd(), pdf_dir)):
            raise FileNotFoundError(f"Directory not found: {os.path.join(os.getcwd(), pdf_dir)}")
                                    
        dir_path = os.path.join(os.getcwd(), pdf_dir)               
        loader = PyPDFDirectoryLoader(dir_path)
        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=128)
        document_chunks = splitter.split_documents(docs)

        print(f"Loaded {len(document_chunks)} chunks from PDF")
        return document_chunks