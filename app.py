# Automated Interview Agent - Main Application

import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

# Import voice module functions
from voice_module import listen_to_user, speak_to_user, start_listening, stop_listening, is_recording

# Suppress warnings about OpenAI format
import warnings
import logging
warnings.filterwarnings("ignore", message=".*API key specified is not a valid OpenAI format.*")
logging.getLogger("autogen.oai.client").setLevel(logging.ERROR)

# Load environment variables from .env file
load_dotenv()

# Import autogen in a way that won't break if it's not available
try:
    import autogen
except ImportError:
    # Create a minimal mock for autogen if it's not available
    class MockAutogen:
        class AssistantAgent:
            def __init__(self, name=None, system_message=None, llm_config=None, **kwargs):
                self.name = name
                self.system_message = system_message
                self.llm_config = llm_config
                
        class UserProxyAgent:
            def __init__(self, name=None, human_input_mode=None, code_execution_config=None, **kwargs):
                self.name = name
                self.human_input_mode = human_input_mode
                self.code_execution_config = code_execution_config
                
        class GroupChat:
            def __init__(self, agents=None, messages=None, max_round=None, **kwargs):
                self.agents = agents or []
                self.messages = messages or []
                self.max_round = max_round
                self.speaker_selection_func = None
                
        class GroupChatManager:
            def __init__(self, groupchat=None, llm_config=None, **kwargs):
                self.groupchat = groupchat
                self.llm_config = llm_config
    
    autogen = MockAutogen()

# Custom implementation for Gemini API
class GeminiWrapper:
    """
    A wrapper class for the Gemini API that provides a simplified interface
    for use with AutoGen.
    """
    
    def __init__(self, api_key):
        """
        Initialize the wrapper with the API key.
        
        Args:
            api_key (str): The Google API key for Gemini
        """
        self.api_key = api_key
        genai.configure(api_key=api_key)
    
    def generate_content(self, prompt, model="gemini-2.5-pro", temperature=0.7):
        """
        Generate content using the Gemini API.
        
        Args:
            prompt (str): The prompt to send to the model
            model (str): The model to use
            temperature (float): The temperature parameter
            
        Returns:
            str: The generated text
        """
        try:
            # Configure the generation config
            generation_config = {
                "temperature": temperature,
                "top_p": 0.95,
                "top_k": 0,
                "max_output_tokens": 8192,
            }
            
            # Create the model
            model = genai.GenerativeModel(model_name=model,
                                         generation_config=generation_config)
            
            # Generate content
            response = model.generate_content(prompt)
            
            # Return the text
            return response.text
        except Exception as e:
            print(f"Error generating content: {e}")
            return f"Error: {str(e)}"

# Configure Google Generative AI with API key
api_key = os.environ.get("GOOGLE_API_KEY")
if api_key and api_key != "YOUR_GEMINI_API_KEY_HERE":
    genai.configure(api_key=api_key)

# Create a global instance of the wrapper
gemini_wrapper = None
if os.environ.get("GOOGLE_API_KEY") and os.environ.get("GOOGLE_API_KEY") != "YOUR_GEMINI_API_KEY_HERE":
    gemini_wrapper = GeminiWrapper(os.environ.get("GOOGLE_API_KEY"))

# We no longer need the get_llm_config function since we're using our custom agent implementation

# Define the four core assistant agents with placeholder system messages
# Using appropriate model IDs and temperatures based on their roles

# Import our custom agent implementation
from custom_agents import GeminiAssistantAgent

# Resume Analyzer Agent - High accuracy, low temperature for consistent analysis
resume_analyzer_agent = GeminiAssistantAgent(
    name="ResumeAnalyzerAgent",
    system_message="""You are an expert HR analyst AI, functioning as a silent, backend data processor. Your sole task is to perform a detailed, structured comparison between the provided Job Description (JD) and the Candidate's Resume.

**Instructions:**
1. Rigorously identify all key requirements from the JD. Categorize them into: 'mandatory_skills', 'preferred_skills', 'years_of_experience', and 'education'.
2. Thoroughly parse the entire resume to find explicit evidence that meets each of these identified requirements.
3. Your final output MUST be a single, valid JSON object and nothing else. Do not include any conversational text, greetings, or explanations.
4. The JSON object must have a root key "analysis". This key should contain two child keys: "match" and "gap".
5. Under the "match" key, create an object where each key is a JD requirement that is clearly met by the resume. The value for each key should be a string containing the direct quote from the resume that serves as evidence.
6. Under the "gap" key, create an array of strings. Each string should be a JD requirement that is either not mentioned in the resume or where the evidence is ambiguous or insufficient.
7. Ensure your output is minified, valid JSON. Your entire response will be parsed programmatically.""",
    model="gemini-2.5-pro",
    temperature=0.2
)

# Question Generator Agent - Medium temperature for balanced creativity and structure
question_generator_agent = GeminiAssistantAgent(
    name="QuestionGeneratorAgent",
    system_message="""You are a strategic interview question designer AI. You will receive a JSON object containing a detailed analysis of the matches and gaps between a candidate's resume and a job description. Your exclusive purpose is to generate a targeted and comprehensive set of initial interview questions based on this analysis.

**Instructions:**
1. For each item listed in the "gap" array of the input JSON, you MUST generate one specific technical or situational question designed to probe that particular area of weakness or missing information.
2. For the most critical skills listed in the "match" object (e.g., primary programming language, core technology), you MUST generate one advanced technical question to verify the candidate's depth of knowledge beyond a surface-level claim.
3. You MUST generate exactly two standard behavioral questions to assess soft skills (e.g., "Describe a situation where you had to work with a difficult team member," or "Tell me about a project you are particularly proud of and why.").
4. Your final output must be a single JSON array of strings. Each string in the array is a single interview question.
5. The total number of questions should be between 5 and 8.
6. Do not add any preamble, conclusion, or any text outside of the valid JSON array.""",
    model="gemini-2.5-pro",
    temperature=0.7
)

# Interviewer Agent - Medium-high temperature for natural conversation
interviewer_agent = GeminiAssistantAgent(
    name="InterviewerAgent",
    system_message="""You are 'Alex', a friendly, professional, and highly engaging AI Interviewer. Your role is to conduct a structured yet conversational screening interview.

**Instructions:**
1. You will be provided with a list of questions. Begin the conversation by introducing yourself warmly: "Hello, my name is Alex, and I'll be conducting your initial screening today. I'm looking forward to our conversation. Let's start with the first question." Then, ask the first question from the list.
2. Listen carefully to the candidate's response. Your primary goal is to maintain a natural, flowing conversation, not a rigid interrogation.
3. After the candidate provides their answer, you MUST ask exactly one relevant, insightful follow-up question. This follow-up question must be based directly on the specifics of their response. Its purpose is to dig deeper into their answer, ask for a concrete example, or clarify a point they made.
4. After the candidate answers your follow-up question, smoothly transition to the next main question from the original list.
5. Maintain a positive, encouraging, and professional tone throughout the interview. Keep your own remarks concise and focused on the candidate.
6. When all main questions and their corresponding follow-ups have been asked, you must conclude the interview. Do this by saying: "Thank you very much for your time and for sharing your experience with me. That's all the questions I have for you today. Our HR team will review our conversation and will be in touch with you regarding the next steps. Have a great day!"
7. Immediately after delivering the closing statement, your final output MUST be the single word: TERMINATE""",
    model="gemini-2.5-flash",
    temperature=0.5
)

# Evaluator Agent - Low temperature for objective, consistent evaluation
evaluator_agent = GeminiAssistantAgent(
    name="EvaluatorAgent",
    system_message="""You are a highly analytical and objective AI evaluation engine. Your task is to provide a comprehensive, structured evaluation of a job candidate based on the full interview transcript and the initial resume-to-job-description analysis. Your output must be impartial and based solely on the provided data.

**Instructions:**
1. Your entire output MUST be in Markdown format.
2. Begin with a top-level heading: `# Candidate Evaluation Report`.
3. Create a second-level heading for "Overall Summary". Under this, provide a concise, 3-4 sentence paragraph summarizing the candidate's overall performance, key strengths, and notable weaknesses.
4. Create a second-level heading: `## Detailed Evaluation`. Under this, create a third-level heading for each of the key requirements from the original job description.
5. For each requirement, you must:
   a. Provide a bullet point summarizing the candidate's responses from the transcript that are relevant to this requirement.
   b. Provide a score from 1 to 5 for that requirement (1=Poor, 3=Meets Expectations, 5=Excellent).
   c. Provide a brief "Justification" for the score, citing direct (but brief) quotes from the candidate's answers as evidence.
6. Create a final second-level heading: `## Final Recommendation`. Under this, you must provide one of the following three recommendations:
   * **Strongly Recommend for Next Round:** The candidate significantly exceeds requirements and performed exceptionally well.
   * **Recommend with Reservations:** The candidate meets most core requirements but has specific weaknesses that should be probed in the next round.
   * **Do Not Recommend:** The candidate does not meet the core requirements for the role.
7. Your analysis must be strictly objective. Do not invent information or make assumptions beyond what is present in the transcript and analysis documents.""",
    model="gemini-2.5-pro",
    temperature=0.4
)
# Define the UserProxyAgent to represent the human candidate
user_proxy_agent = autogen.UserProxyAgent(
    name="CandidateAgent",
    human_input_mode="ALWAYS",  # Always wait for human input
    code_execution_config=False  # Candidate will not execute code
)

# Custom speaker selection function to enforce the workflow sequence
def custom_speaker_selection(last_speaker, groupchat):
    """
    Enforces a strict, non-cyclical workflow for the interview process.
    
    Args:
        last_speaker: The agent that spoke last
        groupchat: The GroupChat instance with conversation history
        
    Returns:
        The next agent to speak based on the workflow rules
    """
    # Get the last message to check for special keywords
    messages = groupchat.messages
    last_message = messages[-1]["content"] if messages else ""
    
    # Initial state: User provides resume/JD, then Resume Analyzer starts
    if last_speaker is None or last_speaker == user_proxy_agent:
        # Check if this is the initial message with resume and job description
        if "resume" in last_message.lower() and "job description" in last_message.lower():
            return resume_analyzer_agent
        # Check if we're in the interview loop
        elif last_speaker == interviewer_agent:
            # If TERMINATE is detected, move to evaluation
            if "TERMINATE" in last_message:
                return evaluator_agent
            # Otherwise continue the interview loop
            return user_proxy_agent
        # Default to interviewer for user responses during interview
        else:
            return interviewer_agent
    
    # Resume Analyzer -> Question Generator
    elif last_speaker == resume_analyzer_agent:
        return question_generator_agent
    
    # Question Generator -> Interviewer
    elif last_speaker == question_generator_agent:
        return interviewer_agent
    
    # Interviewer -> User (for response)
    elif last_speaker == interviewer_agent:
        return user_proxy_agent
    
    # Evaluator speaks last, end conversation
    elif last_speaker == evaluator_agent:
        return None
    
    # Default case
    return user_proxy_agent

# Create the GroupChat with all five agents
group_chat = autogen.GroupChat(
    agents=[
        user_proxy_agent,
        resume_analyzer_agent,
        question_generator_agent,
        interviewer_agent,
        evaluator_agent
    ],
    messages=[],
    max_round=50  # Limit the conversation to 50 rounds for safety
)

# Create the GroupChatManager to manage the conversation flow
# Using a custom configuration that doesn't rely on OpenAI format
group_chat_manager = autogen.GroupChatManager(
    groupchat=group_chat,
    llm_config=None  # Disable LLM-based routing to avoid OpenAI format warnings
)

# Set the speaker selection function after initialization
# This is the compatible way to set custom speaker selection in AutoGen 0.9.6
group_chat.speaker_selection_func = custom_speaker_selection

# Streamlit UI Implementation
def main():
    """
    Main Streamlit application function that sets up the UI and handles user interactions.
    """
    try:
        # Set page title and configuration
        st.set_page_config(page_title="AI Interview Agent", layout="wide")
        st.title("AI Interview Agent")
        
        # Check if API key is configured
        if not os.environ.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_API_KEY") == "YOUR_GEMINI_API_KEY_HERE":
            st.error("⚠️ Google API key not configured. Please set your GOOGLE_API_KEY in the .env file.")
            st.stop()
        
        # Initialize session state for chat history if it doesn't exist
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        if "interview_started" not in st.session_state:
            st.session_state.interview_started = False
        
        # Create sidebar for inputs
        with st.sidebar:
            st.header("Interview Setup")
            
            # Candidate name input
            candidate_name = st.text_input("Candidate Name")
            
            # Resume file uploader (PDF only)
            resume_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
            
            # Job description text area
            job_description = st.text_area("Job Description", height=200)
            
            # Voice mode toggle
            voice_mode = st.toggle("Enable Voice Mode", help="Enable voice input and output")
            
            # Start interview button
            start_button = st.button("Start Interview")
            
            # Voice mode info and button
            if voice_mode and st.session_state.interview_started:
                st.info("Voice mode is enabled. Click the button to start speaking, then click again to stop.")
                
                # Check the current recording state from the voice module
                current_recording_state = is_recording()
                
                # Create a button that toggles between "Start Speaking" and "Stop Speaking"
                button_label = "Stop Speaking" if current_recording_state else "Start Speaking"
                speak_button = st.button(button_label, key="speak_toggle")
                
                if speak_button:
                    if current_recording_state:  # Currently recording, so stop
                        with st.spinner("Processing your response..."):
                            # Stop recording and get the transcribed text
                            user_input = stop_listening()
                            
                            if user_input and not user_input.startswith("Sorry"):
                                # Add user message to chat history
                                st.session_state.chat_history.append({
                                    "role": "user",
                                    "content": user_input
                                })
                                
                                try:
                                    # For demo purposes, we'll use our custom Gemini wrapper directly
                                    if gemini_wrapper:
                                        # Generate a response using Gemini
                                        response_prompt = f"""
                                        You are 'Alex', a friendly, professional AI interviewer.
                                        
                                        The candidate just said: "{user_input}"
                                        
                                        Respond to their answer and ask a relevant follow-up question.
                                        Keep your response conversational and engaging.
                                        """
                                        
                                        response_text = gemini_wrapper.generate_content(
                                            response_prompt,
                                            model="gemini-2.5-pro",
                                            temperature=0.5
                                        )
                                        
                                        # Add the response to chat history
                                        st.session_state.chat_history.append({
                                            "role": "assistant",
                                            "content": response_text
                                        })
                                        
                                        # Convert response to speech
                                        try:
                                            speak_to_user(response_text)
                                        except Exception as tts_error:
                                            st.warning(f"⚠️ Text-to-speech error: {str(tts_error)}")
                                    else:
                                        # Fallback if no API key is available
                                        mock_responses = [
                                            "That's interesting! Could you tell me more about your approach to problem-solving?",
                                            "Thanks for sharing. How do you typically handle challenging situations in a team environment?",
                                            "I appreciate your detailed answer. Can you give me a specific example of how you've applied these skills?",
                                            "That's helpful context. What would you say is your greatest strength in this area?",
                                            "Great explanation. How do you stay updated with the latest developments in your field?"
                                        ]
                                        import random
                                        response_text = random.choice(mock_responses)
                                        
                                        st.session_state.chat_history.append({
                                            "role": "assistant",
                                            "content": response_text
                                        })
                                        
                                        # Convert response to speech
                                        try:
                                            speak_to_user(response_text)
                                        except Exception as tts_error:
                                            st.warning(f"⚠️ Text-to-speech error: {str(tts_error)}")
                                except Exception as agent_error:
                                    st.error(f"❌ Error processing response: {str(agent_error)}")
                            else:
                                st.error(user_input)
                            
                            # Rerun to update UI
                            st.rerun()
                    else:  # Not recording, so start
                        # Start recording
                        success = start_listening()
                        if success:
                            # Rerun to update the UI
                            st.rerun()
                        else:
                            st.error("Failed to start recording. Please try again.")
                
                # Show recording indicator if currently recording
                if current_recording_state:
                    # Create a more noticeable recording indicator
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.markdown("### 🔴")
                    with col2:
                        st.info("Recording... Click 'Stop Speaking' when you're done.")
            
            # Reset interview button
            if st.session_state.interview_started:
                if st.button("Reset Interview"):
                    st.session_state.chat_history = []
                    st.session_state.interview_started = False
                    st.rerun()
        
        # Main chat interface
        chat_container = st.container()
        
        with chat_container:
            # Display chat history
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
            
            # Handle interview start
            if start_button and not st.session_state.interview_started:
                # Enhanced input validation
                validation_errors = []
                
                if not candidate_name or not candidate_name.strip():
                    validation_errors.append("Candidate name is required")
                elif len(candidate_name.strip()) < 2:
                    validation_errors.append("Candidate name must be at least 2 characters long")
                
                if not resume_file:
                    validation_errors.append("Resume file is required")
                elif resume_file.size > 10 * 1024 * 1024:  # 10MB limit
                    validation_errors.append("Resume file must be smaller than 10MB")
                
                if not job_description or not job_description.strip():
                    validation_errors.append("Job description is required")
                elif len(job_description.strip()) < 50:
                    validation_errors.append("Job description must be at least 50 characters long")
                
                if validation_errors:
                    for error in validation_errors:
                        st.error(f"❌ {error}")
                else:
                    # Process the resume file (in a real app, you would extract text from PDF)
                    # For this implementation, we'll simulate resume text
                    resume_text = f"Sample resume text for {candidate_name}"
                    
                    # Create initial message with resume and job description
                    initial_message = f"""
                    Resume: {resume_text}
                    
                    Job Description: {job_description}
                    
                    Please analyze the resume against the job description.
                    """
                    
                    # Add system message to chat history
                    st.session_state.chat_history.append({
                        "role": "system",
                        "content": f"Interview started for candidate: {candidate_name}"
                    })
                    
                    # Set interview started flag
                    st.session_state.interview_started = True
                    
                    try:
                        # For demo purposes, we'll use our custom Gemini wrapper directly
                        # instead of going through AutoGen, which requires more complex setup
                        if gemini_wrapper:
                            with st.spinner("Analyzing resume..."):
                                # Generate a sample analysis using Gemini
                                analysis_prompt = f"""
                                You are an expert HR analyst. Analyze this resume against the job description:
                                
                                Resume: {resume_text}
                                
                                Job Description: {job_description}
                                
                                Provide a detailed analysis in JSON format with 'match' and 'gap' sections.
                                """
                                
                                analysis = gemini_wrapper.generate_content(
                                    analysis_prompt, 
                                    model="gemini-2.5-pro", 
                                    temperature=0.2
                                )
                                
                                # Add the analysis to chat history
                                st.session_state.chat_history.append({
                                    "role": "assistant",
                                    "content": f"Resume Analysis:\n\n{analysis}"
                                })
                                
                                # Generate interview questions
                                questions_prompt = f"""
                                Based on this analysis: {analysis}
                                
                                Generate 5 interview questions that would be good to ask this candidate.
                                Format as a numbered list.
                                """
                                
                                questions = gemini_wrapper.generate_content(
                                    questions_prompt,
                                    model="gemini-2.5-pro",
                                    temperature=0.7
                                )
                                
                                # Add the questions to chat history
                                st.session_state.chat_history.append({
                                    "role": "assistant",
                                    "content": f"Interview Questions:\n\n{questions}"
                                })
                        else:
                            # Fallback if no API key is available
                            st.warning("⚠️ No valid Gemini API key found. Using mock responses.")
                            
                            # Add mock responses to chat history
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": "Resume Analysis: This is a mock analysis. In a real application, this would be generated by the Gemini API."
                            })
                            
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": "Interview Questions:\n\n1. Tell me about your experience with Python.\n2. How do you handle difficult team situations?\n3. What project are you most proud of and why?\n4. How do you stay updated with the latest technologies?\n5. Where do you see yourself in 5 years?"
                            })
                    except Exception as e:
                        st.error(f"❌ Error starting interview: {str(e)}")
                        st.session_state.interview_started = False
                        return
                    
                    # Rerun to update UI
                    st.rerun()
            
            # Chat input for ongoing conversation (only if voice mode is disabled)
            if st.session_state.interview_started and not voice_mode:
                user_input = st.chat_input("Your response")
                
                if user_input:
                    # Add user message to chat history
                    st.session_state.chat_history.append({
                        "role": "user",
                        "content": user_input
                    })
                    
                    try:
                        # For demo purposes, we'll use our custom Gemini wrapper directly
                        if gemini_wrapper:
                            with st.spinner("Processing..."):
                                # Generate a response using Gemini
                                response_prompt = f"""
                                You are 'Alex', a friendly, professional AI interviewer.
                                
                                The candidate just said: "{user_input}"
                                
                                Respond to their answer and ask a relevant follow-up question.
                                Keep your response conversational and engaging.
                                """
                                
                                response = gemini_wrapper.generate_content(
                                    response_prompt,
                                    model="gemini-2.5-pro",
                                    temperature=0.5
                                )
                                
                                # Add the response to chat history
                                st.session_state.chat_history.append({
                                    "role": "assistant",
                                    "content": response
                                })
                        else:
                            # Fallback if no API key is available
                            mock_responses = [
                                "That's interesting! Could you tell me more about your approach to problem-solving?",
                                "Thanks for sharing. How do you typically handle challenging situations in a team environment?",
                                "I appreciate your detailed answer. Can you give me a specific example of how you've applied these skills?",
                                "That's helpful context. What would you say is your greatest strength in this area?",
                                "Great explanation. How do you stay updated with the latest developments in your field?"
                            ]
                            import random
                            response = random.choice(mock_responses)
                            
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": response
                            })
                    except Exception as e:
                        st.error(f"❌ Error processing response: {str(e)}")
                    
                    # Rerun to update UI
                    st.rerun()
            
            # Voice mode instructions
            elif st.session_state.interview_started and voice_mode:
                st.info("Voice mode is enabled. Use the 'Start Speaking' button in the sidebar to begin recording, then click 'Stop Speaking' when you're done.")
    
    except Exception as e:
        st.error(f"❌ An unexpected error occurred: {str(e)}")
        st.error("Please refresh the page and try again. If the problem persists, check your API configuration.")

# Run the Streamlit app
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()