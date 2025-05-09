import streamlit as st
import os
from dotenv import load_dotenv
import tempfile # For handling uploaded file

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# --- Environment and API Key Setup ---
GOOGLE_API_KEY = ""

# --- Core RAG Functions ---

# Use st.cache_resource to cache the RAG chain creation
# The cache key will be based on the PDF content (bytes) and the API key.
@st.cache_resource(show_spinner="Initializing RAG chain... This may take a few moments.")
def initialize_rag_chain(_pdf_bytes, api_key):
    """
    Initializes the RAG chain components from PDF bytes.
    Caches the result to avoid reprocessing the same PDF.
    """
    if not api_key:
        raise ValueError("Google API Key is missing. Please provide it.")

    # Save uploaded bytes to a temporary file for PyPDFLoader
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(_pdf_bytes)
        pdf_path_for_loader = tmp_file.name

    try:
        # 1. Load Document
        loader = PyPDFLoader(pdf_path_for_loader)
        docs = loader.load()
        if not docs:
            raise ValueError("No documents loaded from PDF. It might be empty or corrupted.")

        # 2. Split Document
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)
        if not splits:
            raise ValueError("Document splitting resulted in no chunks.")

        # 3. Create Embeddings & Vector Store
        embeddings_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings_model)

        # 4. Create Retriever
        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={'k': 3})

        # 5. Define Prompt Template
        prompt_template_str = """
        Answer the question based ONLY on the following context.
        If the information is not in the context, clearly state "I don't know based on the provided document."
        Be concise and helpful.

        Context:
        {context}

        Question:
        {question}

        Answer:
        """
        prompt = ChatPromptTemplate.from_template(prompt_template_str)

        # 6. Initialize LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro-exp-03-25",
            temperature=0.1, # Slightly creative but mostly factual
            convert_system_message_to_human=True # Good practice for some models
        )

        # 7. Create RAG Chain
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        return rag_chain, retriever

    except Exception as e:
        # Ensure cleanup of temp file in case of error during processing
        st.error(f"Error during RAG chain initialization: {e}")
        raise
    finally:
        if os.path.exists(pdf_path_for_loader):
            os.remove(pdf_path_for_loader)


# --- Streamlit UI ---
st.set_page_config(page_title="📄 PDF RAG with Gemini", layout="wide")
st.title("📄 PDF RAG with Google Gemini")
st.markdown("Upload a PDF, and ask questions about its content.")

# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "rag_chain" not in st.session_state:
    st.session_state.rag_chain = None
if "retriever" not in st.session_state:
    st.session_state.retriever = None
if "current_pdf_name" not in st.session_state:
    st.session_state.current_pdf_name = None
if "api_key_valid" not in st.session_state:
    st.session_state.api_key_valid = bool(GOOGLE_API_KEY)


# Sidebar for API Key and PDF Upload
with st.sidebar:
    st.header("Configuration")

    # API Key Input if not found
    if not GOOGLE_API_KEY:
        st.info("Your Google API Key is needed to use the app.")
        user_api_key = st.text_input("Enter your Google API Key:", type="password", key="api_key_input_ui")
        if user_api_key:
            GOOGLE_API_KEY = user_api_key # Use user-provided key
            st.session_state.api_key_valid = True # Assume valid for now, will fail later if not
            st.success("API Key entered.")
        else:
            st.session_state.api_key_valid = False
    else:
        st.success("Google API Key loaded from environment/secrets.")
        st.session_state.api_key_valid = True


    uploaded_file = st.file_uploader("Upload your PDF", type="pdf", key="pdf_uploader")

    if uploaded_file is not None:
        if not st.session_state.api_key_valid or not GOOGLE_API_KEY:
            st.warning("Please enter a valid Google API Key to process the PDF.")
        else:
            # Check if it's a new file or if the RAG chain hasn't been initialized
            if st.session_state.current_pdf_name != uploaded_file.name or st.session_state.rag_chain is None:
                try:
                    pdf_bytes = uploaded_file.getvalue()
                    st.session_state.rag_chain, st.session_state.retriever = initialize_rag_chain(pdf_bytes, GOOGLE_API_KEY)
                    st.session_state.current_pdf_name = uploaded_file.name
                    st.session_state.messages = [] # Clear chat history for new PDF
                    st.success(f"PDF '{uploaded_file.name}' processed! You can now ask questions.")
                except Exception as e:
                    st.error(f"Failed to process PDF: {e}")
                    st.session_state.rag_chain = None # Reset on failure
                    st.session_state.retriever = None
                    st.session_state.current_pdf_name = None
    elif st.session_state.current_pdf_name:
        # If no file is uploaded but there was one, clear the state
        st.session_state.rag_chain = None
        st.session_state.retriever = None
        st.session_state.current_pdf_name = None
        st.session_state.messages = []
        st.info("Upload a new PDF to continue.")

# Display chat messages
if st.session_state.rag_chain:
    st.subheader(f"Chat about: {st.session_state.current_pdf_name}")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and "context_chunks" in message:
                with st.expander("View Retrieved Context"):
                    for i, chunk in enumerate(message["context_chunks"]):
                        st.caption(f"Chunk {i+1}:\n{chunk.page_content}")

# Chat input
if st.session_state.rag_chain:
    if prompt := st.chat_input(f"Ask something about {st.session_state.current_pdf_name}..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            with st.spinner("Thinking..."):
                try:
                    answer = st.session_state.rag_chain.invoke(prompt)
                    full_response = answer

                    # Retrieve context for display (optional, but good for transparency)
                    retrieved_docs = []
                    if st.session_state.retriever:
                         retrieved_docs = st.session_state.retriever.invoke(prompt)

                except Exception as e:
                    full_response = f"Sorry, an error occurred: {e}"
                    st.error(full_response)
                    retrieved_docs = [] # Clear context on error

            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response, "context_chunks": retrieved_docs})
else:
    if not st.session_state.api_key_valid:
         st.warning("👈 Please provide your Google API Key in the sidebar to enable PDF processing.")
    else:
        st.info("👈 Upload a PDF file in the sidebar to get started.")

st.markdown("---")
st.markdown("Powered by LangChain, Google Gemini, FAISS, and Streamlit.")