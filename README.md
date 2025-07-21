# Automated Interview Agent

A comprehensive AI-powered interview system built with Microsoft AutoGen, featuring multiple specialized agents that work together to conduct technical interviews. The system supports both text and voice interactions through a Streamlit web interface.

## Features

- **Multi-Agent Architecture**: Four specialized AI agents working in orchestrated workflow
- **Voice Interaction**: Speech-to-text and text-to-speech capabilities
- **Resume Analysis**: Automated comparison between resumes and job descriptions
- **Strategic Question Generation**: Targeted questions based on candidate gaps and strengths
- **Natural Conversation Flow**: AI interviewer with follow-up questions
- **Comprehensive Evaluation**: Structured candidate assessment reports

## Architecture

### AI Integration

The application uses Google's Gemini API to power the interview process:

1. **Resume Analysis**: Gemini analyzes resumes against job descriptions, identifying matches and gaps
2. **Question Generation**: Generates targeted interview questions based on the analysis
3. **Conversational Interviewing**: "Alex" persona conducts natural, conversational interviews
4. **Voice Interaction**: Optional speech-to-text and text-to-speech capabilities

### Workflow

```
User Input (Resume + JD) → Resume Analysis → Question Generation → Interactive Interview
```

## Installation

### Prerequisites

- Python 3.8 or higher (tested with Python 3.12)
- AutoGen 0.9.6
- Google Generative AI Python SDK
- Microphone and speakers (for voice mode)
- Google Gemini API key (available on Google AI Studio)

### Setup

1. **Clone or download the project files**

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   - Copy the `.env` file and update it with your Google Gemini API key:
   ```
   GOOGLE_API_KEY="your_gemini_api_key_here"
   ```
   - You can get a Gemini API key from [Google AI Studio](https://aistudio.google.com/)

5. **Run tests** (optional but recommended):
   ```bash
   python run_tests.py
   ```

## Usage

### Starting the Application

```bash
streamlit run app.py
```

The application will open in your web browser at `http://localhost:8501`.

### Using the Interface

1. **Setup Interview**:
   - Enter candidate name
   - Upload resume (PDF format)
   - Paste job description
   - Toggle voice mode if desired

2. **Start Interview**:
   - Click "Start Interview"
   - The system will automatically analyze the resume and generate questions

3. **Conduct Interview**:
   - **Text Mode**: Type responses in the chat input
   - **Voice Mode**: Click "Click and Speak" button to provide verbal responses

4. **Review Results**:
   - The system provides a comprehensive evaluation report at the end

## Configuration

### Model Configuration

The system uses Google's Gemini models for all agents:

- **Resume Analyzer**: `gemini-pro` (temperature: 0.2) - High accuracy
- **Question Generator**: `gemini-pro` (temperature: 0.7) - Balanced creativity
- **Interviewer**: `gemini-pro` (temperature: 0.5) - Natural conversation
- **Evaluator**: `gemini-pro` (temperature: 0.4) - Objective analysis
- **Group Chat Manager**: `gemini-pro` (temperature: 0.3) - Efficient routing

### Voice Configuration

Voice settings can be adjusted in `voice_module.py`:

```python
# Adjust speech recognition timeout
audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)

# Adjust text-to-speech properties
engine.setProperty('rate', 150)    # Speed of speech
engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
```

## Testing

### Running Tests

```bash
# Run all tests
python run_tests.py

# Run only integration tests
python test_integration.py
```

### Test Coverage

The test suite covers:

- **Voice Module**: Speech recognition and text-to-speech functionality
- **Configuration**: API key validation and parameter checking
- **Agent Workflow**: Agent creation and speaker selection logic
- **Error Handling**: Various error scenarios and recovery
- **Integration**: End-to-end workflow testing

### Manual Testing Scenarios

1. **Basic Interview Flow**:
   - Upload a sample resume
   - Enter a job description
   - Complete a full interview cycle

2. **Voice Mode Testing**:
   - Enable voice mode
   - Test speech recognition with clear speech
   - Test with background noise
   - Verify text-to-speech output

3. **Error Scenarios**:
   - Invalid API key
   - Large resume files
   - Empty job descriptions
   - Network connectivity issues

## Troubleshooting

### Common Issues

1. **API Key Errors**:
   - Ensure your OpenRouter API key is correctly set in `.env`
   - Verify the key has sufficient credits

2. **Voice Recognition Issues**:
   - Check microphone permissions
   - Ensure stable internet connection for Google Speech API
   - Try speaking more clearly or adjusting microphone settings

3. **Audio Output Issues**:
   - Check speaker/headphone connections
   - Verify system audio settings
   - Try restarting the application

4. **Import Errors**:
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version compatibility

### Error Messages

- **"OPENROUTER_API_KEY not found"**: Configure your API key in the `.env` file
- **"Sorry, I couldn't understand"**: Speech recognition failed, try speaking more clearly
- **"Error processing response"**: Network or API issue, check connection and try again

## Development

### Project Structure

```
AutomatedInterviewAgent/
├── app.py                 # Main Streamlit application
├── voice_module.py        # Voice interaction functions
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables
├── test_integration.py   # Integration tests
├── run_tests.py         # Test runner
└── README.md            # This file
```

### Adding New Features

1. **New Agent**: Create agent in `app.py` with appropriate system message
2. **Voice Features**: Extend `voice_module.py` with new functions
3. **UI Components**: Add Streamlit components in the `main()` function
4. **Tests**: Add corresponding tests in `test_integration.py`

### Contributing

1. Follow the existing code style and structure
2. Add tests for new functionality
3. Update documentation as needed
4. Test thoroughly before submitting changes

## License

This project is provided as-is for educational and development purposes.

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review the test output for specific error details
3. Ensure all dependencies and configuration are correct

---

**Note**: This application requires an active internet connection for AI model API calls and speech recognition services.