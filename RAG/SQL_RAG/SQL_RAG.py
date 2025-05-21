import streamlit as st
import sqlite3
import requests
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from langchain_community.utilities import SQLDatabase
from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool

# Setting up page configuration
st.set_page_config(
    page_title="CrewAI SQL Assistant",
    page_icon="🤖",
    layout="wide"
)

# Styling and layout
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        margin-bottom: 2rem;
    }
    .response-box {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin-top: 20px;
    }
    .stProgress > div > div > div {
        background-color: #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 class='main-header'>CrewAI SQL Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Ask questions about your database in natural language</p>", unsafe_allow_html=True)

@st.cache_resource
def get_engine_for_chinook_db():
    """Pull sql file, populate in-memory database, and create engine."""
    url = "https://raw.githubusercontent.com/lerocha/chinook-database/master/ChinookDatabase/DataSources/Chinook_Sqlite.sql"
    with st.spinner("Loading the Chinook database..."):
        response = requests.get(url)
        sql_script = response.text

        connection = sqlite3.connect(":memory:", check_same_thread=False)
        connection.executescript(sql_script)
        engine = create_engine(
            "sqlite://",
            creator=lambda: connection,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
        st.success("Database loaded successfully!")
        return engine

# Initialize database connection when the app loads
if 'db_engine' not in st.session_state:
    st.session_state.db_engine = get_engine_for_chinook_db()
    st.session_state.db = SQLDatabase(st.session_state.db_engine)

# Setup LLM (with API key handling)
if 'llm' not in st.session_state:
    # Check for API key in session state first
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ""

# Sidebar for API key configuration
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Enter Google API Key:", value=st.session_state.api_key, type="password")
    
    if api_key:
        st.session_state.api_key = api_key
        st.session_state.llm = LLM(model="gemini/gemini-2.0-flash", provider="google", api_key=api_key)
        st.success("API key configured")
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This app uses CrewAI and Google's Gemini model to:
    1. Analyze database schema
    2. Construct SQL queries
    3. Execute and format results
    
    The Chinook database is a sample database that represents a digital media store.
    """)

# Tool definitions for CrewAI
@tool("List Database Tables")
def list_tables_tool():
    """Returns a list of table names available in the database."""
    from langchain_community.tools.sql_database.tool import ListSQLDatabaseTool
    return ListSQLDatabaseTool(db=st.session_state.db).invoke("")

@tool("Get Table Schema")
def get_schema_tool(table_names: str):
    """Returns the schema for the specified table(s)."""
    from langchain_community.tools.sql_database.tool import InfoSQLDatabaseTool
    return InfoSQLDatabaseTool(db=st.session_state.db).invoke(table_names)

@tool("Execute SQL Query")
def execute_query_tool(sql_query: str):
    """Executes an SQL query against the database."""
    from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
    executor_tool = QuerySQLDataBaseTool(db=st.session_state.db)
    return executor_tool.invoke(sql_query)

# Define agents
def create_crew():
    schema_agent = Agent(
        role="Database Schema Expert",
        goal="Interpret and explain the database schema.",
        backstory="You understand the structure of the database, including tables, schemas, and relationships.",
        tools=[list_tables_tool, get_schema_tool],
        verbose=True,
        llm=st.session_state.llm,
        allow_delegation=False
    )

    query_builder_agent = Agent(
        role="SQL Architect",
        goal="Construct precise SQL queries based on the user query and schema_agent output.",
        backstory="You use natural language, database schema, and business rules to generate valid and optimized SQL queries.",
        verbose=True,
        llm=st.session_state.llm,
        allow_delegation=False
    )

    executor_agent = Agent(
        role="Query Runner",
        goal="Execute SQL and return clear, structured answers.",
        backstory="You take SQL queries, run them on the database, and format the results in human-readable form.",
        tools=[execute_query_tool],
        verbose=True,
        llm=st.session_state.llm,
        allow_delegation=False
    )

    # Define tasks
    task_1 = Task(
        description= "Analyze the database schema and identify which tables and columns are relevant "
        "to the user query {input}. Refine the user query to include those details.",
        agent=schema_agent,
        expected_output=(
            "A concise summary identifying the database table and column(s) needed to answer the user question. "
            "This should clearly state the target table and the mechanism "
        )
    )

    task_2 = Task(
        description=(
            "Based on the schema analysis summary provided by the previous task, construct the precise SQL query "
            "needed to answer the user query {input} in the database. Ensure the query is syntactically correct. "
            "Validate syntax before finalizing."
        ),
        agent=query_builder_agent,
        expected_output=(
            "A single, ready-to-execute SQL query string that accurately reflects the requirement to answer the user question "
            "based on the identified table and criteria. "
        )
    )

    task_3 = Task(
        description=(
            "Take the provided SQL query string. Execute this query against the database using the 'Execute SQL Query' tool. "
            "Retrieve the raw result (which should be a count). "
            "Format this numerical result into a clear, friendly, natural language sentence that directly answers the original user query: '{input}'."
        ),
        agent=executor_agent,
        expected_output=(
            "A final, human-readable sentence stating the numbers and info needed "
            "The sentence should directly answer the initial question. "
        )
    )

    # Create crew
    return Crew(
        agents=[schema_agent, query_builder_agent, executor_agent],
        tasks=[task_1, task_2, task_3],
        verbose=True
    )

# Main query input
user_question = st.text_input("Ask a question about the Chinook database:", "How many albums do we have?")

# Example questions for quick access
st.markdown("### Example questions:")
col1, col2 = st.columns(2)
examples = [
    "How many albums do we have?",
    "How many customers are from USA?",
    "What is the total number of tracks?",
    "How many artists are in the database?",
    "Which genre has the most tracks?",
    "How many invoices do we have with a total over $10?"
]

# Create two columns of example buttons
with col1:
    for i in range(0, len(examples), 2):
        if st.button(examples[i]):
            user_question = examples[i]
            st.session_state.user_question = user_question
            #st.rerun 

with col2:
    for i in range(1, len(examples), 2):
        if st.button(examples[i]):
            user_question = examples[i]
            st.session_state.user_question = user_question
            #st.rerun 

# Process the query
if st.button("Submit Question") or ('user_question' in st.session_state and st.session_state.user_question == user_question):
    # Save current question to session state
    st.session_state.user_question = user_question
    
    # Check if API key is provided
    if not st.session_state.get('api_key'):
        st.error("Please enter your Google API key in the sidebar first!")
    else:
        with st.spinner("Analyzing your question and searching the database..."):
            # Progress bar for visual feedback
            progress_bar = st.progress(0)
            
            # Update progress stages
            st.markdown("### Processing stages:")
            stage1 = st.empty()
            stage2 = st.empty()
            stage3 = st.empty()
            
            try:
                # Process with CrewAI
                stage1.info("Stage 1/3: Analyzing database schema...")
                progress_bar.progress(20)
                
                crew = create_crew()
                
                # Start processing
                progress_bar.progress(40)
                stage2.info("Stage 2/3: Building SQL query...")
                progress_bar.progress(60)
                
                stage3.info("Stage 3/3: Executing query and formatting results...")
                result = crew.kickoff(inputs={"input": user_question})
                progress_bar.progress(100)
                
                # Clear progress indicators
                stage1.success("Stage 1/3: Database schema analyzed")
                stage2.success("Stage 2/3: SQL query built")
                stage3.success("Stage 3/3: Results processed")
                
                # Display the result
                st.markdown("### Answer")
                st.markdown(f"<div class='response-box'>{result}</div>", unsafe_allow_html=True)
                
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.markdown("Please check your API key and try again.")