import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

def create_rag_components(vectorstore):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set. Please set it to your Google API key.")
    
    llm = ChatGoogleGenerativeAI(google_api_key=api_key, model="gemini-2.5-flash", temperature=0.7, max_tokens=500) | StrOutputParser()
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    
    return retriever, llm