# main.py
import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic_ai import Agent, BinaryContent
from models import AudioAnalysis, CallAnalysis, OverallCallAnalysisResult 
import google.generativeai as genai
from dotenv import load_dotenv
import uvicorn
import logging # Added for better error logging
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware if your Streamlit app runs on a different origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins (adjust for production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Agent Configurations ===

# --- Configure the Agent ---
Transcritor_agent = Agent(
    'google-gla:gemini-2.5-pro-exp-03-25', # Ensure this model supports audio input directly
    output_type=AudioAnalysis,
    system_prompt="""
        You are an advanced AI conversation analyzer specializing in call center interactions.
        Analyze the provided audio file thoroughly.

        Your tasks are:
        1.  **Transcription:** Provide a full transcript of the conversation.
        2.  **Speaker Identification:** Identify and label each speaker. Use "Agent" and "Customer". If a name is clearly mentioned (e.g., "My name is Mohammed"), include it in parentheses like "Agent (Mohammed)" or "Customer (Sarah)". If no name is mentioned, just use "Agent" or "Customer".
        3.  **Timestamps:** For each distinct utterance or sentence, provide the start and end time in HH:MM:SS format relative to the beginning of the audio. Ensure `startTime` and `endTime` are accurate for each segment.
        4.  **Emotion Detection:** For each utterance, determine the primary emotion conveyed (e.g., Neutral, Happy, Sad, Angry, Frustrated, Confused, Polite, Empathetic).""",
    name='Call_Transcritor',
    # Consider adding error handling/retry logic if needed via pydantic-ai config
)

# --- Configure the Agent ---
call_analyzer_agent = Agent(
    model='google-gla:gemini-2.5-pro-exp-03-25',
    output_type=CallAnalysis,
    system_prompt=(
        "You are an expert conversation analyst. Your task is to analyze each turn in a customer service call.\n\n"
        "For each conversation turn, return the following fields:\n"
        "1. category: One of the following - 'PII Stated', 'Product Issues', 'Complaint', 'Churn Indicators', 'Suggestion', or 'None'\n"
        "2. sentiment: One of - 'Positive', 'Negative', or 'Neutral'\n"
        "3. translation: English translation of the transcript\n\n"
        "**Output Format:**\n"
        "Respond with a single JSON object in the following format:\n\n"
        "{\n"
        "  \"conversation\": [\n"
        "    {\n"
        "      \"category\": \"...\",\n"
        "      \"sentiment\": \"...\",\n"
        "      \"translation\": \"...\"\n"
        "    },\n"
        "    ...\n"
        "  ]\n"
        "}\n\n"
        "Only output valid JSON. Do not include any explanations or commentary. Do not include markdown."
    ),
    name='Call_Analyzer'
)

# --- Configure the Agent ---
overallcall_analyzer_agent = Agent(
    'google-gla:gemini-2.5-pro-exp-03-25',
    output_type=OverallCallAnalysisResult,
    instructions=[
        "Based *only* on the provided transcript data (input is a JSON object conforming to the AudioAnalysis schema), extract the following information and structure your response according to the OverallCallAnalysisResult schema:",
        "1.Summarization: Provide a concise summary of the entire call, focusing on the main reason, key points, decisions, and outcome.",
        "2.Call Purpose: State the primary reason for the call (e.g., Inquire about billing discrepancy, Request password reset).",
        "3.Topics & Keywords: List the main topics discussed and significant keywords (e.g., 'billing', 'invoice #12345', 'password reset').",
        "4.Action Taken: List specific actions *completed during* the call (e.g., 'Agent updated customer address'). If none, state explicitly or return empty list/string.",
        "5.Next Action: List actions agreed upon to be taken *after* the call. Specify who is responsible if possible (e.g., 'Agent will escalate ticket'). If none, state explicitly or return null/empty string.",
        "Provide the output strictly in the requested JSON format corresponding to the OverallCallAnalysisResult schema."
    ],
    name='Overall_Call_Analyzer',
)

# === API Endpoints ===

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Receives an audio file, transcribes it, identifies speakers,
    timestamps, and emotions using the Transcritor_agent.
    """
    logger.info(f"Received file: {file.filename}, Content-Type: {file.content_type}")

    # --- Input Validation ---
    if not file.content_type or not file.content_type.startswith("audio/"):
        logger.warning(f"Received non-audio file type: {file.content_type}")

    try:
        # --- Read File Content ---
        audio_bytes = await file.read()
        if not audio_bytes:
             raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        logger.info(f"Read {len(audio_bytes)} bytes from {file.filename}")

        # --- Call Agent ---
        # Use await agent.run() for async endpoint
        # Pass the correct media_type from the upload
        result: AudioAnalysis = await Transcritor_agent.run([
            BinaryContent(data=audio_bytes, media_type=file.content_type)
        ])
        logger.info(f"Transcription successful for {file.filename}")
        return result.output.model_dump()


    except Exception as e:
        logger.error(f"Error during transcription for {file.filename}: {e}", exc_info=True)
    finally:
        # Ensure the file handle is closed
        await file.close()
        logger.debug(f"Closed file handle for {file.filename}")




@app.post("/analyze-turns")
async def analyze_turns(conversation: AudioAnalysis): # FastAPI validates input into AudioAnalysis object
    """
    Analyzes each turn of the conversation for category, sentiment, and translation.
    Expects input conforming to the AudioAnalysis model.
    """
    logger.info(f"Received conversation object for turn analysis with {len(conversation.conversation)} turns.")
    agent_result = None # Initialize agent_result
    try:
        # --- FIX: Convert Pydantic object to a JSON-compatible dictionary ---
        # Using mode='json' ensures complex types are pre-serialized correctly
        conversation_dict = conversation.model_dump_json()
        logger.debug(f"Passing dictionary (mode='json') to call_analyzer_agent: {str(conversation_dict)[:500]}...")

        # Pass the dictionary to the agent
        agent_result = await call_analyzer_agent.run(conversation_dict) # agent_result holds the structured output or raw data if parsing failed

        return agent_result.output.model_dump() # Return the validated Pydantic model

    except Exception as e:
        # Log the exception type and message clearly
        logger.error(f"{type(e).__name__} during turn analysis: {e}", exc_info=True)

        # Try to log raw agent output if available and exception occurred after agent call
        if agent_result:
             raw_output = getattr(agent_result, 'raw_output', str(agent_result)) # Attempt to get raw output
             logger.error(f"Raw agent output during error: {raw_output[:1000]}...") # Log snippet

        # Specific check for the TypeError
        if isinstance(e, TypeError) and "BaseModel.__init__()" in str(e):
             detail_msg = "Internal Error: Failed to parse LLM response into expected structure (BaseModel init error)."
        else:
             detail_msg = f"Error analyzing conversation turns: {type(e).__name__}"

        raise HTTPException(status_code=500, detail=detail_msg)


@app.post("/analyze-call")
async def analyze_overall(conversation: AudioAnalysis): # FastAPI validates input
    """
    Generates an overall analysis of the call (summary, purpose, etc.).
    Expects input conforming to the AudioAnalysis model.
    """
    logger.info(f"Received conversation object for overall analysis with {len(conversation.conversation)} turns.")
    agent_result = None
    try:
        # Convert Pydantic object to a JSON-compatible dictionary
        conversation_dict = conversation.model_dump_json()
        logger.debug(f"Passing dictionary (mode='json') to overallcall_analyzer_agent: {str(conversation_dict)[:500]}...")

        # Pass the dictionary to the agent
        agent_result = await overallcall_analyzer_agent.run(conversation_dict)

        logger.info("Overall call analysis successful and output validated.")
        return agent_result.output.model_dump()

    except Exception as e:
        logger.error(f"{type(e).__name__} during overall call analysis: {e}", exc_info=True)
        if agent_result:
             raw_output = getattr(agent_result, 'raw_output', str(agent_result))
             logger.error(f"Raw overall agent output during error: {raw_output[:1000]}...")

        if isinstance(e, TypeError) and "BaseModel.__init__()" in str(e):
             detail_msg = "Internal Error: Failed to parse LLM response into expected structure (BaseModel init error)."
        else:
             detail_msg = f"Error generating overall call analysis: {type(e).__name__}"

        raise HTTPException(status_code=500, detail=detail_msg)
if __name__ == "__main__":
    # Removed the extra comma at the end of the uvicorn.run line
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)