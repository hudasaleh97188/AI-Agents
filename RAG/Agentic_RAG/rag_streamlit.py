# import libraries
import os
from dotenv import load_dotenv
import streamlit as st
from langchain.agents import AgentExecutor
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain.agents import create_tool_calling_agent, create_structured_chat_agent
from langchain import hub
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_core.tools import tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langfuse.callback import CallbackHandler
from supabase.client import Client, create_client

# load environment variables
load_dotenv()  
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
LANGFUSE_PUBLIC_KEY=os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY=os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST=os.getenv("LANGFUSE_HOST")
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")

# initiating supabase
supabase: Client = create_client(supabase_url, supabase_key)

# Initialize Langfuse and tracer
langfuse_handler = CallbackHandler(
    public_key=LANGFUSE_PUBLIC_KEY,
    secret_key=LANGFUSE_SECRET_KEY,
    host=LANGFUSE_HOST
)

# initiating embeddings model
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001"
                                          , google_api_key=GOOGLE_API_KEY)

# initiating vector store
vector_store = SupabaseVectorStore(
    embedding=embeddings,
    client=supabase,
    table_name="documents",
    query_name="match_documents",
)
 
# initiating llm
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0,
    api_key=GOOGLE_API_KEY
)

# pulling prompt from hub
prompt = hub.pull("hwchase17/structured-chat-agent")



# creating the retriever tool
@tool(response_format="content_and_artifact")
def retrieve(query: str):
    """Retrieve information related to a query."""
    retrieved_docs = vector_store.similarity_search(query, k=4)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs

# combining all tools
tools = [retrieve]

# initiating the agent
agent = create_structured_chat_agent(llm=llm, tools=tools, prompt=prompt)

# create the agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# initiating streamlit app
st.set_page_config(page_title="Chatbot - Agentic RAG", page_icon="🚀")
st.title("Chatbot - Agentic RAG")

# initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# display chat messages from history on app rerun
for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.markdown(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            st.markdown(message.content)


# create the bar where we can type messages
user_question = st.chat_input("Input your question")


# did the user submit a prompt?
if user_question:

    # add the message from the user (prompt) to the screen with streamlit
    with st.chat_message("user"):
        st.markdown(user_question)
        st.session_state.messages.append(HumanMessage(user_question))


    # invoking the agent
    # Only pass the last 5 messages as chat history (recent history)
    result = agent_executor.invoke({"input": user_question, "chat_history":st.session_state.messages[-5:]},config={"callbacks": [langfuse_handler]})

    ai_message = result["output"]

    # adding the response from the llm to the screen (and chat)
    with st.chat_message("assistant"):
        st.markdown(ai_message)
        st.session_state.messages.append(AIMessage(ai_message))