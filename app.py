import streamlit as st
import os
import hashlib
from dotenv import load_dotenv
from crawler import crawl_website
from utils import preprocess_documents
from kb import build_knowledge_base
from rag import create_rag_components
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

# --- Configuration ---
FIXED_URL = "https://www.bajajamc.com"
KB_PATH = "kb_index"

st.set_page_config(page_title="Bajaj AMC Chatbot", page_icon="🤖")

st.title("Bajaj AMC AI Assistant")

# --- Sidebar: Knowledge Base Management ---
with st.sidebar:
    st.header("Knowledge Base Status")
    
    # Check if KB exists
    kb_exists = os.path.exists(KB_PATH)
    
    if kb_exists:
        st.success("✅ Knowledge Base Loaded")
        st.info(f"Connected to: {FIXED_URL}")
        if st.button("Rebuild Knowledge Base"):
            st.session_state.force_rebuild = True
            if 'vectorstore' in st.session_state:
                del st.session_state.vectorstore
            st.rerun()
    else:
        st.warning("⚠️ Knowledge Base Missing")
    
    st.markdown("---")
    st.markdown("### Settings")
    st.markdown(f"**Target URL:**\n{FIXED_URL}")
    st.caption("This bot is restricted to Bajaj AMC content only.")

# --- Main Logic ---

# Initialize Embeddings
@st.cache_resource
def get_embedding_model():
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2", 
        model_kwargs={'device': 'cpu'},
        cache_folder="./hf_cache"  # Save model to D: drive (current folder)
    )

# Initialize Embeddings
embeddings = get_embedding_model()

# Load existing KB if available and not rebuilding
if 'vectorstore' not in st.session_state:
    if os.path.exists(KB_PATH) and not st.session_state.get('force_rebuild', False):
        try:
            st.session_state.vectorstore = FAISS.load_local(KB_PATH, embeddings, allow_dangerous_deserialization=True)
        except Exception as e:
            st.error(f"Failed to load knowledge base: {e}")

# Crawling & Building Logic (If KB is missing or Rebuild requested)
if 'vectorstore' not in st.session_state:
    st.subheader("Initialize System")
    st.write(f"The system needs to process content from **{FIXED_URL}** to answer your questions.")
    
    if st.button("Start Processing Website"):
        try:
            status_container = st.empty()
            
            def update_status(crawled_count, queue_size, current_url):
                status_container.info(f"🕸️ **Crawling:** {crawled_count} pages processed | {queue_size} pending\n\nCurrent: `{current_url}`")

            with st.spinner(f"Crawling {FIXED_URL}..."):
                documents = crawl_website(FIXED_URL, max_depth=2, progress_callback=update_status)
            
            status_container.empty()
            
            if not documents:
                st.error("No pages found. Please check the website accessibility.")
                st.stop()
                
            st.success(f"Successfully crawled {len(documents)} pages.")
            
            with st.spinner("Processing text and building index..."):
                processed_docs = preprocess_documents(documents)
                vectorstore = build_knowledge_base(processed_docs, embeddings)
                
            # Save to disk
            vectorstore.save_local(KB_PATH)
            vectorstore.save_local(KB_PATH)
            st.session_state.vectorstore = vectorstore
            st.session_state.force_rebuild = False
            st.rerun() # Refresh to show chat interface
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# --- Chat Interface ---
if 'vectorstore' in st.session_state:
    st.divider()
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("Ask about Bajaj AMC products, funds, or intent..."):
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Generate response
        try:
            with st.spinner("Thinking..."):
                retriever, llm = create_rag_components(st.session_state.vectorstore)
                
                # Retrieve context
                docs = retriever.invoke(prompt)
                context = "\n".join([doc.page_content for doc in docs])
                
                # Construct improved prompt
                full_prompt = (
                    f"You are a helpful assistant for Bajaj AMC. Use the following context to answer the user's question.\n"
                    f"If the answer is not in the context, politely say you don't know.\n\n"
                    f"Context:\n{context}\n\n"
                    f"Question: {prompt}"
                )
                
                # Get answer
                response_text = llm.invoke(full_prompt)

            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                st.markdown(response_text)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            
        except Exception as e:
            st.error(f"Error generating response: {e}")

else:
    # If we are here, it means we are waiting for the user to click "Start Processing" above
    pass