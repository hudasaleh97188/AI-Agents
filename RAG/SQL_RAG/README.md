# CrewAI SQL Assistant with Streamlit

This application allows you to query the Chinook database using natural language. It leverages CrewAI with Gemini AI to interpret your questions, create SQL queries, and return human-readable answers.

## Features

- Natural language querying of SQL databases
- Interactive web interface built with Streamlit
- Specialized AI agents working together to process your query:
  - Database Schema Expert - Analyzes the database structure
  - SQL Architect - Builds optimized SQL queries
  - Query Runner - Executes queries and formats results
- Example questions for easy exploration
- Real-time processing feedback

## Requirements

- Python 3.8+
- Google API key for Gemini AI
- Required Python packages (see requirements.txt)

## Installation

1. Clone this repository or download the code
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Run the Streamlit app:

```bash
streamlit run app.py
```

## Usage

1. Enter your Google API key in the sidebar
2. Type a natural language question about the database or select one of the example questions
3. Click "Submit Question" to process your query
4. View the answer and, optionally, the process logs

## About the Chinook Database

The Chinook database represents a digital media store, including tables for artists, albums, media tracks, invoices, and customers. It's a common sample database used for SQL demonstrations and learning.

## Example Questions

- How many albums do we have?
- How many customers are from USA?
- What is the total number of tracks?
- How many artists are in the database?
- Which genre has the most tracks?
- How many invoices do we have with a total over $10?

## Project Structure

- `app.py` - Main Streamlit application
- `requirements.txt` - Required Python packages

## Technical Details

This application uses:
- **CrewAI** for orchestrating AI agents
- **Google's Gemini AI** for natural language processing
- **SQLAlchemy** for database operations
- **Streamlit** for the web interface
- **Chinook SQLite database** for demonstration

## Note

You need to provide your own Google API key to use this application. The key is stored only in your session and is not saved permanently.
