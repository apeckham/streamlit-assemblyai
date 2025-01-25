import streamlit as st
import assemblyai as aai
import tempfile
import time
import os

st.title("Audio Transcription with Speaker Diarization")

# Get API key from query params or user input
default_api_key = st.query_params.get("api_key", "")
api_key = st.text_input("AssemblyAI API Key", value=default_api_key, type="password")

# File upload
uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav", "m4a"])

# Clear transcript if file is removed
if not uploaded_file and "transcript" in st.session_state:
    st.session_state.transcript = None
    st.session_state.last_file = None

if uploaded_file and api_key:
    # Initialize session state for transcript
    if "transcript" not in st.session_state:
        st.session_state.transcript = None
    
    # Only transcribe if we don't have a transcript or if the file changed
    if st.session_state.transcript is None or st.session_state.get('last_file') != uploaded_file.name:
        # Configure AssemblyAI
        aai.settings.api_key = api_key
        transcriber = aai.Transcriber()
        
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix="." + uploaded_file.name.split(".")[-1]) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                audio_path = tmp_file.name

            with st.spinner('Transcribing... This may take up to a minute.'):
                # Configure transcription with speaker diarization
                config = aai.TranscriptionConfig(speaker_labels=True)
                
                # Start transcription
                st.session_state.transcript = transcriber.transcribe(audio_path, config)
                st.session_state.last_file = uploaded_file.name
                
                # Delete the temporary file
                os.unlink(audio_path)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.session_state.transcript = None
    
    # Display transcript if available
    if st.session_state.transcript:
        if st.session_state.transcript.status == aai.TranscriptStatus.error:
            st.error(f"Transcription failed: {st.session_state.transcript.error}")
        else:
            # Format text with speaker labels and escape for HTML/JS
            formatted_text = []
            for utterance in st.session_state.transcript.utterances:
                formatted_text.append(f"Speaker {utterance.speaker}: {utterance.text}")
            formatted_text = "\n\n".join(formatted_text)
            
            import html
            escaped_formatted_text = html.escape(formatted_text).replace('"', '&quot;')

            # Add Alpine.js and clipboard plugin
            st.components.v1.html(f"""
                <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
                <script src="https://cdn.jsdelivr.net/npm/@ryangjchandler/alpine-clipboard@2.x.x/dist/alpine-clipboard.js" defer></script>
                <div x-data>
                    <div x-clipboard.raw="{escaped_formatted_text}" style="cursor:pointer;text-decoration:underline">
                        Copy Full Transcript
                    </div>
                </div>
            """, height=50)
            
            # Display speaker-separated transcript
            st.subheader("Transcript by Speaker")
            for utterance in st.session_state.transcript.utterances:
                st.write(f"Speaker {utterance.speaker}: {utterance.text}")

elif not api_key:
    st.warning("Please enter your AssemblyAI API key to continue.")
elif not uploaded_file:
    st.warning("Please upload an audio file to begin transcription.")
