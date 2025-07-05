# Meeting Analyzer AI 📄

An intelligent meeting analysis tool that automatically transcribes video/audio files, generates structured meeting notes using multiple AI agents, and creates professional Minutes of Meeting (MoM) email drafts.

## Features

- **Multi-format Support**: Accepts video (MP4, MOV, AVI, MKV) and audio (MP3, WAV, M4A, AAC) files
- **Advanced Transcription**: Uses Google Gemini 2.5 Pro for accurate transcription with speaker diarization
- **Dual Note-taking Strategy**: 
  - Predefined structured format
  - AI-recommended format based on meeting type (progress updates, brainstorming, 1-on-1s, interviews, etc.)
- **Automated Email Distribution**: Creates MoM email drafts in Gmail
- **Multi-agent Analysis**: Uses CrewAI with specialized agents for comprehensive meeting analysis
- **Professional Output**: Generates structured notes in Markdown format

## Architecture

The application uses a multi-agent system powered by CrewAI:

1. **Meeting Analyst** - Extracts core content and themes
2. **Action Item Specialist** - Identifies actionable tasks
3. **Content Organizer** - Structures information hierarchically
4. **Quality Assurance Editor** - Ensures accuracy and formatting
5. **Meeting Strategist** - Determines optimal documentation framework
6. **Strategic Note Curator** - Applies sophisticated note-taking methodologies
7. **Email Assistant** - Formats and distributes meeting minutes

## Prerequisites

- Python 3.8 or higher
- Google Cloud Platform account (for Gmail API)
- Google API key (for Gemini AI)
- AssemblyAI API key (optional fallback)

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/meeting-analyzer-ai.git
cd meeting-analyzer-ai
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
Create a `.env` file in the project root:
```env
GOOGLE_API_KEY=your_google_api_key_here
AAI_API_KEY=your_assemblyai_api_key_here
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=your_langfuse_host
```

## Google Gmail API Setup

### Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Navigate to **APIs & Services > Library**
   - Search for "Gmail API"
   - Click on it and press "Enable"

### Step 2: Create OAuth 2.0 Credentials

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. Choose **Desktop application** as the application type
4. Give it a name (e.g., "Meeting Analyzer AI")
5. Download the credentials JSON file
6. Rename it to `credentials.json` and place it in your project root directory

### Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services > OAuth consent screen**
2. Choose **External** user type (unless you're using Google Workspace)
3. Fill in the required information:
   - App name: "Meeting Analyzer AI"
   - User support email: Your email
   - Developer contact information: Your email
4. Add scopes:
   - Click **Add or Remove Scopes**
   - Add `https://mail.google.com/` (full Gmail access)
5. Add test users (your email address) in the **Test users** section
6. Save and continue

### Step 4: First-time Authentication

1. Run the application for the first time:
```bash
streamlit run main.py
```

2. When you first use a Gmail feature, you'll be redirected to Google's OAuth consent screen
3. Sign in with your Google account
4. Grant the necessary permissions
5. A `token.json` file will be created automatically in your project directory

**Important Notes:**
- Keep both `credentials.json` and `token.json` secure and never commit them to version control
- Add them to your `.gitignore` file:
```
credentials.json
token.json
.env
```

## Usage

1. **Start the application:**
```bash
streamlit run main.py
```

2. **Upload your meeting file:**
   - Drag and drop or browse for your video/audio file
   - Supported formats: MP4, MOV, AVI, MKV, MP3, WAV, M4A, AAC

3. **Click "Analyze Meeting"** and wait for processing

4. **Review the results in four tabs:**
   - **Transcription**: Full transcript with speaker identification
   - **Compiled Notes**: Structured notes using predefined format
   - **Strategic Notes**: AI-recommended format based on meeting type
   - **MoM Email Draft**: Professional email draft saved to Gmail

## Project Structure

```
meeting-analyzer-ai/
├── main.py                 # Streamlit main application
├── meeting_crew.py         # CrewAI agents and tasks configuration
├── tools.py               # Gmail integration tools
├── utils.py               # Utility functions for transcription
├── credentials.json       # Google OAuth credentials (you create this)
├── token.json            # Auto-generated OAuth token
├── .env                  # Environment variables
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Dependencies

Create a `requirements.txt` file with:

```txt
streamlit>=1.28.0
crewai>=0.1.0
google-generativeai>=0.3.0
assemblyai>=0.20.0
moviepy>=1.0.3
pydantic>=2.0.0
pydantic-ai>=0.0.12
langchain-community>=0.0.20
python-dotenv>=1.0.0
langfuse>=2.0.0
openlit>=1.0.0
```

## Configuration

### API Keys Required

1. **Google API Key**: 
   - Get from [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Used for Gemini AI transcription and analysis

2. **AssemblyAI API Key** (Optional):
   - Get from [AssemblyAI](https://www.assemblyai.com/)
   - Fallback transcription service

3. **Langfuse Keys** (Optional):
   - For tracking and monitoring AI interactions
   - Sign up at [Langfuse](https://langfuse.com/)

### Gmail Scopes

The application requires the following Gmail scope:
- `https://mail.google.com/` - Full Gmail access for reading, creating drafts, and sending emails

## Troubleshooting

### Common Issues

1. **"File not found" errors**: Ensure all required files are in the project root
2. **Authentication errors**: Check that `credentials.json` is properly configured
3. **API quota exceeded**: Monitor your Google API usage in the Cloud Console
4. **Transcription failures**: Verify audio quality and file format compatibility

### Gmail Authentication Issues

- **Refresh token expired**: Delete `token.json` and re-authenticate
- **Scope errors**: Ensure the Gmail API is enabled in your Google Cloud project
- **Permission denied**: Check that your app is not in testing mode restrictions

## Acknowledgments

- Built with [CrewAI](https://crewai.com/) for multi-agent orchestration
- Uses [Google Gemini](https://deepmind.google/technologies/gemini/) for advanced AI capabilities
- Powered by [Streamlit](https://streamlit.io/) for the web interface
- Integrates with [Gmail API](https://developers.google.com/gmail/api) for email automation
