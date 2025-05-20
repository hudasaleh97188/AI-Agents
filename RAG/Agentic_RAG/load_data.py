
# import libraries
import os
from dotenv import load_dotenv
import os
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, UnstructuredWordDocumentLoader
import hashlib
from supabase.client import Client, create_client
from langchain_core.documents import Document

# load environment variables
load_dotenv()  

# initiate supabase db
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# initiate embeddings model
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

#Compute the MD5 hash and return its hexadecimal representation
def compute_file_hash(filepath):
    with open(filepath, "rb") as f:
        file_content = f.read()
    return hashlib.md5(file_content).hexdigest()

# Check if the hash exist (file saved before or not)
def is_file_already_ingested(supabase, file_hash):
    response = supabase.table("documents").select("id").eq("metadata->>hash", file_hash).execute()
    return len(response.data) > 0


# Load PDFs from the directory
pdf_loader = DirectoryLoader("data", glob="**/*.pdf", loader_cls=PyPDFLoader)

# Load Word docs from the same directory
docx_loader = DirectoryLoader("data", glob="**/*.docx", loader_cls=UnstructuredWordDocumentLoader)

all_documents = []

for loader in [pdf_loader, docx_loader]:
    raw_docs = loader.load()
    for doc in raw_docs:
        file_path = doc.metadata.get("source")
        file_hash = compute_file_hash(file_path)

        # Skip if already exists
        if is_file_already_ingested(supabase, file_hash):
            continue

        # Add hash to metadata for future reference
        doc.metadata["hash"] = file_hash
        all_documents.append(doc)


# split the documents in multiple chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
docs = text_splitter.split_documents(all_documents)

# store chunks in vector store
vector_store = SupabaseVectorStore.from_documents(
    docs,
    embeddings,
    client=supabase,
    table_name="documents",
    query_name="match_documents",
    chunk_size=1000,
)
