#%%import os
from crewai.tools import tool
from langchain_community.agent_toolkits import GmailToolkit
from langchain_community.tools.gmail.utils import (
    build_resource_service,
    get_gmail_credentials,
)
from typing import Union, List, Optional
# --- 1. Initialize the Gmail Toolkit ---
print("Initializing Gmail Toolkit...")
credentials = get_gmail_credentials(
    token_file="token.json",
    scopes=["https://mail.google.com/"],
    client_secrets_file="credentials.json",
)
api_resource = build_resource_service(credentials=credentials)
gmail_toolkit = GmailToolkit(api_resource=api_resource)
print("Gmail Toolkit Initialized.")
#%%

# --- 2. Create a dictionary to access tools by name (The Fix) ---
# This is much safer than relying on list index.
langchain_tools = gmail_toolkit.get_tools()
gmail_tools_map = {tool.name: tool for tool in langchain_tools}

# Let's see the actual tool names available, this is good for debugging
print("Available LangChain tool names:")
for name in gmail_tools_map.keys():
    print(f"- {name}")
# Expected output will include: search_gmail, get_gmail_message, send_gmail_message, create_gmail_draft


# --- 3. Define Tools using the @tool Decorator ---

@tool("Search Gmail")
def search_gmail(query: str) -> str:
    """
    Searches the user's Gmail inbox with a specific query.
    The input is a standard Gmail search query string (e.g., 'from:elon@x.com is:unread').
    Returns a list of email snippets with their IDs.
    """
    # Access the tool by its official name
    search_tool = gmail_tools_map['search_gmail']
    return search_tool.run(query)

@tool("Read Email Content")
def read_email(email_id: str) -> str:
    """
    Reads the full content of a specific email.
    The input MUST be the 'id' of the email, which can be obtained from the 'Search Gmail' tool.
    Returns the email's content, including sender, subject, and body.
    """
    # The tool for reading a message is named 'get_gmail_message'
    read_tool = gmail_tools_map['get_gmail_message']
    return read_tool.run(email_id)


@tool("Send Email")
def send_email(to: Union[str, List[str]], subject: str, body: str, cc: Optional[Union[str, List[str]]] = None, bcc: Optional[Union[str, List[str]]] = None) -> str:
    """
    Sends an email to specified recipient(s).
    
    Parameters:
        to: A single email address or a list of email addresses.
        subject: The subject of the email.
        body: The main content of the email (HTML allowed).
        cc: Optional CC recipients.
        bcc: Optional BCC recipients.
    
    Returns:
        Result of sending the email.
    """
    send_tool = gmail_tools_map['send_gmail_message']
    payload = {
        "message": body,
        "to": to,
        "subject": subject,
    }

    if cc:
        payload["cc"] = cc
    if bcc:
        payload["bcc"] = bcc

    return send_tool.run(payload)

@tool("Create Email Draft")
def create_draft(to: str, subject: str, body: str) -> str:
    """
    Creates a draft email in the user's Gmail account but does not send it.
    The 'to' argument is the recipient's email address (e.g., 'example@gmail.com').
    The 'subject' argument is the subject of the email.
    The 'body' argument is the main content of the email.
    """
    # 1. Access the underlying LangChain tool by its official name
    draft_tool = gmail_tools_map['create_gmail_draft']

    # 2. Prepare the input as a dictionary that matches 'CreateDraftSchema'
    tool_input = {
        "to": [to],         
        "subject": subject,  
        "message": body      
    }

    # 3. Call the tool's .run() method with the single dictionary argument.
    return draft_tool.run(tool_input)
