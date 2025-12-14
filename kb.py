from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from langchain_community.vectorstores import FAISS

import time

def build_knowledge_base(processed_documents, embeddings):
    # Create Document objects
    documents = [
        Document(page_content=doc['content'], metadata={'url': doc['url']})
        for doc in processed_documents
    ]
    
    # Chunk the documents
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)
    
    # Create FAISS vector store
    # Using local model now, so we can process without sleep
    vectorstore = FAISS.from_documents(chunks, embeddings)
    
    return vectorstore