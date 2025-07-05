# app.py
import streamlit as st
import os
import tempfile
import logging

# Import from our new modules
from utils import video_to_audio, process_audio_Gemini
from meeting_crew import run_crew_analysis

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="Meeting Analyzer AI", layout="wide")
st.title("📄 Meeting Analyzer AI")
st.markdown("Upload a meeting video or audio file to get a full transcription, structured notes, and a draft MoM email.")

# --- Session State Initialization ---
def init_session_state():
    keys_to_init = {
        'analysis_complete': False,
        'transcript': None,
        'compiled_notes': "",
        'strategic_notes': "",
        'mom_draft_result': ""
    }
    for key, default_value in keys_to_init.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

init_session_state()

# --- Main App Logic ---
# File Uploader
uploaded_file = st.file_uploader(
    "Choose a video or audio file",
    type=['mp4', 'mov', 'avi', 'mkv', 'mp3', 'wav', 'm4a', 'aac']
)

if uploaded_file is not None:
    if st.button("Analyze Meeting"):
        with st.spinner("Analyzing... This may take a few minutes."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                input_file_path = tmp_file.name
            
            audio_file_path = None
            try:
                # 1. Convert video to audio if necessary
                file_extension = os.path.splitext(input_file_path)[1].lower()
                if file_extension in ['.mp4', '.mov', '.avi', '.mkv']:
                    st.info("Video file detected. Converting to audio...")
                    audio_file_path = video_to_audio(input_file_path)
                else:
                    st.info("Audio file detected.")
                    audio_file_path = input_file_path

                # 2. Transcribe the audio
                if audio_file_path:
                    st.info("Transcribing audio...")
                    import asyncio
                    structured_transcript = asyncio.run(process_audio_Gemini(audio_file_path))
                    #structured_transcript = await process_audio_Gemini(audio_file_path)
                    st.session_state.transcript = structured_transcript

                    # 3. Run the CrewAI analysis
                    if structured_transcript:
                        meeting_transcript_text = structured_transcript.model_dump_json(indent=2)
                        st.info("Transcription complete. Running analysis crew...")
                        
                        analysis_results = run_crew_analysis(meeting_transcript_text)
                        
                        # 4. Store results directly in session state
                        st.session_state.compiled_notes = analysis_results.get("compiled_notes", "No compiled notes generated.")
                        st.session_state.strategic_notes = analysis_results.get("strategic_notes", "No strategic notes generated.")
                        st.session_state.mom_draft_result = analysis_results.get("mom_draft_result", "No MoM draft generated.")
                        st.session_state.analysis_complete = True
                        st.success("Analysis Complete!")
                    else:
                        st.error("Could not generate a transcript. Halting analysis.")

            except Exception as e:
                st.error(f"An error occurred during processing: {e}")
                logging.error(f"An error occurred: {e}", exc_info=True)
            finally:
                # Clean up temporary files
                if 'input_file_path' in locals() and os.path.exists(input_file_path): os.unlink(input_file_path)
                if audio_file_path and audio_file_path != input_file_path and os.path.exists(audio_file_path): os.unlink(audio_file_path)

# --- Display Results ---
if st.session_state.analysis_complete:
    st.header("📊 Analysis Results")
    tab1, tab2, tab3, tab4 = st.tabs(["🔊 Transcription", "📝 Compiled Notes", "🎯 Strategic Notes", "📧 MoM Email Draft"])

    with tab1:
        st.subheader("Meeting Transcription")
        if st.session_state.transcript:
            for utterance in st.session_state.transcript.speakers_text:
                st.markdown(f"**{utterance.speaker}:** {utterance.text}")
        else:
            st.warning("No transcript data available.")

    with tab2:
        st.subheader("Compiled Notes (General Analysis)")
        st.markdown(st.session_state.compiled_notes)

    with tab3:
        st.subheader("Strategic Notes (Targeted Analysis)")
        st.markdown(st.session_state.strategic_notes)
        
        
    with tab4:
        st.subheader("Minutes of Meeting (MoM) Email Draft")
        st.markdown(st.session_state.compiled_notes)
        st.text_area(
            "Agent Output", 
            value=st.session_state.mom_draft_result, 
            height=400,
            disabled=True,
            help="This is the complete output from the email agent, including confirmation and a preview."
        )