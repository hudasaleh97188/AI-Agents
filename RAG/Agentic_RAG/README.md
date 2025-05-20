# 🧠 Agentic RAG Project

This project implements an **Agentic Retrieval-Augmented Generation (RAG)** system using **Supabase** as a vector store and **Google Generative AI** models for embedding and response generation. It's designed to ingest and intelligently retrieve information from various document types (PDFs, Word documents), allowing users to interact with documents through a smart agent interface.

A key feature is the intelligent document ingestion logic that avoids redundancy by detecting only new or modified files using MD5 hashes — perfect for collaborative and evolving datasets.

---

## 🚀 Features

- ✅ **Intelligent Document Ingestion**  
  Automatically detects and processes **only new or modified PDF and Word documents** by computing and comparing file hashes, avoiding duplicate entries.

- 🗄️ **Supabase Vector Store**  
  Utilizes Supabase with the `pgvector` extension for fast and scalable vector-based document retrieval.

- 🧠 **Google Generative AI Embeddings**  
  Uses `models/embedding-001` to generate high-quality document embeddings.

- 🔗 **LangChain-Powered Agentic Pipeline**  
  Built on [LangChain](https://www.langchain.com) with structured agents (`create_structured_chat_agent`) and tools for seamless RAG workflows.

- 💬 **Agentic Query Answering**  
  A LangChain agent searches the vector store and formulates intelligent responses to user queries.

- 🌐 **Streamlit Interface**  
  Intuitive web interface for uploading documents and querying the system.

- 📊 **Langfuse Integration (Optional)**  
  Enables tracing, observability, and monitoring of agent behavior with Langfuse.

---

## ⚙️ Setup & Installation

### 1. 🧾 Supabase Setup

**a. Create a Supabase Project**  
Visit [supabase.com](https://supabase.com), create a new project.

**b. Run SQL Schema**  
Run the `supabase.sql` script in the SQL Editor to:

- Enable the `pgvector` extension  
- Create the `documents` table  
- Define vector indexes  
- Add the `match_documents` similarity search function

---

### 2. 🔑 Get API Keys

| Key | How to Get |
|-----|------------|
| **Supabase URL & Service Key** | From your Supabase Project: `Settings > API` |
| **Google API Key** | From [Google AI Studio](https://aistudio.google.com/) > get API key. |
| **Langfuse Keys (Optional)** | From your Langfuse dashboard after signing up. |

---

### 3. 🔐 Environment Variables

Create a `.env` file in your project root:

```env
SUPABASE_URL="your_supabase_url"
SUPABASE_SERVICE_KEY="your_supabase_service_key"
GOOGLE_API_KEY="your_google_api_key"

# Optional: Langfuse
LANGFUSE_PUBLIC_KEY="your_langfuse_public_key"
LANGFUSE_SECRET_KEY="your_langfuse_secret_key"
LANGFUSE_HOST="your_langfuse_host"
```
### 4. 📦 Install Dependencies

First, ensure you have Python 3.9+ installed in your environment.

Install all required Python packages using:

```bash
pip install -r requirements.txt
```
### 5. 📄 Document Ingestion

Place your `.pdf` and `.docx` files inside the `data/` directory at the root of your project:

```yaml
Agentic_RAG/
├── data/
│ ├── example.pdf
│ └── notes.docx
```
To ingest the documents into your Supabase vector store, run the following script:

```bash
python load_data.py
```
This script performs the following actions:
* Scans the data/ directory for PDF and Word files.
* Computes an MD5 hash for each file to uniquely identify its content.
* Checks whether the document has already been ingested by querying Supabase using the file hash.
* Skips files that haven't changed, avoiding redundant storage.
* Splits documents into chunks and stores them as embeddings in Supabase.

### 6. 💡 Run the RAG Interface

Start the Streamlit app:

```bash
streamlit run rag_streamlit.py
```
### 🧩 Architecture Overview
```yaml
📄 Documents (PDF/DOCX)
    |
    V
📦 load_data.py 
    → Embedding via Google Generative AI
    → Stored in Supabase (with hash & metadata)
    |
    V
🤖 Agentic LangChain Agent
    → Queries vector store
    → Responds using context-relevant chunks
    |
    V
🧑‍💻 Streamlit UI or API
```
### 📈 Optional: Enable Langfuse Tracing
Langfuse provides observability into your LangChain agents. Once you set your Langfuse keys in .env, you'll see traces of your agent runs, tool calls, and LLM completions.
