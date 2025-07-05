# utils.py
import os
import logging
import moviepy.editor as mp
import assemblyai as aai
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from pydantic_ai import Agent, BinaryContent
import mimetypes
import asyncio  
# Load environment variables from .env file
load_dotenv()

# API Keys
AAI_API_KEY = os.getenv("AAI_API_KEY")

# Configure AssemblyAI client
if AAI_API_KEY:
    aai.settings.api_key = AAI_API_KEY


# --- Pydantic Models for Transcript Processing ---
class SpeakerText(BaseModel):
    speaker: str
    text: str

class TranscriptionResult(BaseModel):
    speakers_text: List[SpeakerText]
    
def video_to_audio(video_file_path: str) -> str:
    """Converts a video file to an audio file."""
    try:
        logging.info(f"Starting video to audio conversion for: {video_file_path}")
        video_clip = mp.VideoFileClip(video_file_path)
        audio_clip = video_clip.audio
        base, _ = os.path.splitext(video_file_path)
        output_audio_path = f"{base}.mp3"
        audio_clip.write_audiofile(output_audio_path, verbose=False, logger=None)
        audio_clip.close()
        video_clip.close()
        logging.info(f"Video converted successfully. Audio saved to: {output_audio_path}")
        return output_audio_path
    except Exception as e:
        logging.error(f"Failed to convert video to audio: {e}")
        raise



# --- Transcription Functions ---

def process_audio_assemblyai(audio_file_path: str) -> TranscriptionResult | None:
    """Processes audio file using AssemblyAI and returns a structured transcript."""
    logging.info(f"Starting transcription with AssemblyAI for {audio_file_path}")
    try:
        config = aai.TranscriptionConfig(speaker_labels=True)
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_file_path, config)

        if transcript.status == aai.TranscriptStatus.error:
            logging.error(f"AssemblyAI transcription failed: {transcript.error}")
            return None

        speakers_text_list = [
            SpeakerText(speaker=f"Speaker {utt.speaker}", text=utt.text)
            for utt in transcript.utterances
        ]
        return TranscriptionResult(speakers_text=speakers_text_list)
    except Exception as e:
        logging.error(f"Error processing transcript with AssemblyAI: {e}", exc_info=True)
        return None


async def process_audio_Gemini(audio_file_path: str) -> TranscriptionResult | None:
    """Processes an audio file using Gemini for transcription and speaker diarization."""
    Transcritor_agent = Agent(
        'google-gla:gemini-2.5-pro',  # Ensure this model supports audio input directly
        output_type=TranscriptionResult,
        system_prompt=""" 
            You are an advanced AI conversation analyzer specializing in call center interactions.
            Analyze the provided audio file thoroughly.

            Your tasks are:
            1.  **Transcription:** Provide a full transcript of the conversation.
            2.  **Speaker Identification:** Identify and label each speaker. Use Speaker and letter like "Speaker A". """,
        name='Call_Transcritor',
    )
    try:
        # 1. Read the audio file into bytes
        with open(audio_file_path, "rb") as f:
            audio_bytes = f.read()

        if not audio_bytes:
            logging.error("Audio file is empty.")
            return None

        # 2. Determine the media type automatically
        media_type, _ = mimetypes.guess_type(audio_file_path)
        if not media_type or not media_type.startswith("audio/"):
            logging.warning(f"Could not determine a valid audio media type for {audio_file_path}. Defaulting to 'audio/mpeg'.")
            media_type = 'audio/mpeg'  # A safe default for .mp3

        # 3. Call the agent with BinaryContent (the pydantic-ai pattern)
        # We use the asynchronous `await` method here.
        logging.info(f"Sending audio ({media_type}) to the pydantic-ai agent...")
        result: TranscriptionResult = await Transcritor_agent.run([
            BinaryContent(data=audio_bytes, media_type=media_type)
        ])
        
        # 4. The result.output is already a validated TranscriptionResult object!
        logging.info("Successfully received and parsed structured transcript from Gemini.")
        return result.output

    except Exception as e:
        logging.error(f"An error occurred during pydantic-ai Gemini processing: {e}", exc_info=True)
        return None
