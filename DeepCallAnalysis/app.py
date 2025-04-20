#streamlit run app.py

import streamlit as st
import requests
import pandas as pd
import io

# --- Configuration ---
# Replace with your actual FastAPI backend URL if it's not running locally on port 8000
BACKEND_URL = "http://localhost:8001"
TRANSCRIBE_URL = f"{BACKEND_URL}/transcribe"
ANALYZE_TURNS_URL = f"{BACKEND_URL}/analyze-turns"
ANALYZE_CALL_URL = f"{BACKEND_URL}/analyze-call"

# --- Helper Functions ---
def reset_analysis_state():
    """Clears previous analysis results from session state."""
    keys_to_clear = ['transcription_result', 'turn_analysis_result', 'overall_analysis_result', 'error']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

# --- Streamlit App Layout ---
st.set_page_config(page_title="Audio Analysis App", layout="wide")
st.title("🎙️ Audio Call Analysis")
st.markdown("Upload an audio file to transcribe and analyze the conversation.")

# --- File Uploader ---
# Use a unique key and reset state on new upload
uploaded_file = st.file_uploader(
    "Choose an audio file (.wav, .mp3, .ogg, etc.)",
    type=["wav", "mp3", "ogg", "m4a", "aac", "flac"],
    key="audio_uploader",
    on_change=reset_analysis_state # Reset results if a new file is uploaded
)

if uploaded_file is not None:
    # Display Audio Player
    st.subheader("Uploaded Audio")
    audio_bytes = uploaded_file.getvalue()
    st.audio(audio_bytes, format=uploaded_file.type)

    # --- Analysis Trigger ---
    if st.button("✨ Analyze Audio", key="analyze_button"):
        # Reset previous results before starting a new analysis
        reset_analysis_state()

        files = {'file': (uploaded_file.name, io.BytesIO(audio_bytes), uploaded_file.type)}

        try:
            # --- Step 1: Transcription ---
            with st.spinner("Step 1/3: Transcribing audio... (This may take a while)"):
                response_transcribe = requests.post(TRANSCRIBE_URL, files=files)
                response_transcribe.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                st.session_state.transcription_result = response_transcribe.json()
            st.success("Step 1/3: Transcription complete!")

            # --- Step 2: Overall Call Analysis ---
            if 'transcription_result' in st.session_state:
                 with st.spinner("Step 2/3: Generating overall call summary..."):
                    # The backend expects the transcription result as JSON payload
                    payload_turns = st.session_state.transcription_result
                    headers = {'Content-Type': 'application/json'}
                    response_overall = requests.post(ANALYZE_CALL_URL, json=payload_turns,headers=headers)
                    response_overall.raise_for_status()
                    st.session_state.overall_analysis_result = response_overall.json()
                 st.success("Step 2/3: Overall analysis complete!")
            # --- Step 3: Turn Analysis ---
            if 'transcription_result' in st.session_state:
                with st.spinner("Step 3/3: Analyzing conversation turns..."):
                    # The backend expects the transcription result as JSON payload
                    payload_turns = st.session_state.transcription_result
                    headers = {'Content-Type': 'application/json'}
                    response_turns = requests.post(ANALYZE_TURNS_URL, json=payload_turns,headers=headers)
                    response_turns.raise_for_status()
                    st.session_state.turn_analysis_result = response_turns.json()
                st.success("Step 3/3: Turn analysis complete!")



        except requests.exceptions.RequestException as e:
            st.session_state.error = f"An error occurred during API communication: {e}"
            st.error(st.session_state.error)
        except Exception as e:
            st.session_state.error = f"An unexpected error occurred: {e}"
            st.error(st.session_state.error)

# --- Display Results ---
if 'error' in st.session_state:
    st.error(f"Analysis failed: {st.session_state.error}")

st.divider() # Visual separator
# Use columns for better layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 Overall Call Analysis")
    if 'overall_analysis_result' in st.session_state:
        overall_data = st.session_state.overall_analysis_result
        st.markdown(f"**Summary:**")
        st.write(overall_data.get('summarization', 'N/A'))

        st.markdown(f"**Call Purpose:**")
        st.write(overall_data.get('call_purpose', 'N/A'))

        st.markdown(f"**Topics & Keywords:**")
        keywords = overall_data.get('topics_keywords', [])
        if keywords:
            st.write(", ".join(keywords))
        else:
            st.write("N/A")

        st.markdown(f"**Action Taken During Call:**")
        st.write(overall_data.get('action_taken', 'N/A'))

        st.markdown(f"**Next Action(s) After Call:**")
        st.write(overall_data.get('next_action', 'N/A'))


    elif not uploaded_file:
        st.info("Upload an audio file and click 'Analyze Audio' to see the overall analysis.")
    elif 'analyze_button' in st.session_state and not 'error' in st.session_state:
        st.info("Overall analysis results are pending or were not generated.")


with col2:
    st.subheader("📊 Turn-by-Turn Analysis")
    if 'turn_analysis_result' in st.session_state:
        turn_analysis_data = st.session_state.turn_analysis_result.get("conversation_analysis", [])
        if turn_analysis_data:
            # Combine with transcription for context if available
            transcription_data = st.session_state.get('transcription_result', {}).get("conversation", [])
            
            display_data = []
            for i, analysis in enumerate(turn_analysis_data):
                turn_info = {
                    "Turn": i + 1,
                    "Category": analysis.get('category', 'N/A'),
                    "Sentiment": analysis.get('sentiment', 'N/A'),
                    "Translation (EN)": analysis.get('translation', 'N/A')
                }
                # Add transcript snippet for context if available
                if i < len(transcription_data):
                    turn_info["Transcript Snippet"] = transcription_data[i].get('transcript', '')[:100] + "..." # Show snippet
                    turn_info["Speaker"] = transcription_data[i].get('speaker', 'Unknown')

                display_data.append(turn_info)

            df = pd.DataFrame(display_data)
            # Reorder columns for better readability
            cols_order = ["Turn", "Speaker", "Category", "Sentiment", "Translation (EN)", "Transcript Snippet"]
            cols_available = [col for col in cols_order if col in df.columns]
            st.dataframe(df[cols_available], use_container_width=True)

        else:
            st.info("No turn analysis data found.")
    elif not uploaded_file:
         st.info("Upload an audio file and click 'Analyze Audio' to see the turn analysis.")
    elif 'analyze_button' in st.session_state and not 'error' in st.session_state:
        st.info("Turn analysis results are pending or were not generated.")


