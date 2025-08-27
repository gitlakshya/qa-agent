from langchain_community.document_loaders import PyPDFDirectoryLoader
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredHTMLLoader
import logging

logger = logging.getLogger(__name__)


class LoadandChunk:
    def load(self):
        pass

    def load_chunk_html(self, dir_path, filename):
        file_path = os.path.join(dir_path, filename)
        full_path = os.path.join(os.getcwd(), file_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {full_path}")

        loader = UnstructuredHTMLLoader(full_path)
        html_docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=128)
        html_chunks = splitter.split_documents(html_docs)
        
        # Filter out empty chunks with more validation
        html_chunks = [chunk for chunk in html_chunks if 
                      chunk.page_content and 
                      chunk.page_content.strip() and 
                      len(chunk.page_content.strip()) > 10]

        logger.info("Loaded %d HTML chunks from '%s'", len(html_chunks), full_path)
        if not html_chunks:
            logger.warning("No valid chunks found in HTML file: %s", full_path)
        return html_chunks


    def load_chunk_pdf(self, pdf_dir):
        if not os.path.exists(os.path.join(os.getcwd(), pdf_dir)):
            raise FileNotFoundError(f"Directory not found: {os.path.join(os.getcwd(), pdf_dir)}")

        dir_path = os.path.join(os.getcwd(), pdf_dir)
        loader = PyPDFDirectoryLoader(dir_path)
        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=128)
        document_chunks = splitter.split_documents(docs)
        
        # Filter out empty chunks with more validation
        document_chunks = [chunk for chunk in document_chunks if 
                          chunk.page_content and 
                          chunk.page_content.strip() and 
                          len(chunk.page_content.strip()) > 10]

        logger.info("Loaded %d chunks from PDF at '%s'", len(document_chunks), dir_path)
        if not document_chunks:
            logger.warning("No valid chunks found in PDF directory: %s", dir_path)
        return document_chunks

    def map_source(self, docs, source):
        for d in docs:
            d.metadata['source'] = source
        