#!/usr/bin/env python3
"""
Integration tests for the Automated Interview Agent.
This file contains tests for the complete agent workflow, voice functionality,
and error handling scenarios.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
import json

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modules to test
from voice_module import listen_to_user, speak_to_user
import app

class TestVoiceModule(unittest.TestCase):
    """Test cases for voice interaction functionality."""
    
    @patch('voice_module.sr.Microphone')
    @patch('voice_module.sr.Recognizer')
    def test_listen_to_user_success(self, mock_recognizer_class, mock_microphone):
        """Test successful speech recognition."""
        # Setup mocks
        mock_recognizer = Mock()
        mock_recognizer_class.return_value = mock_recognizer
        mock_recognizer.recognize_google.return_value = "Hello, this is a test"
        
        mock_source = Mock()
        mock_microphone.return_value.__enter__.return_value = mock_source
        
        # Test the function
        result = listen_to_user()
        
        # Assertions
        self.assertEqual(result, "Hello, this is a test")
        mock_recognizer.adjust_for_ambient_noise.assert_called_once()
        mock_recognizer.listen.assert_called_once()
        mock_recognizer.recognize_google.assert_called_once()
    
    @patch('voice_module.sr.Microphone')
    @patch('voice_module.sr.Recognizer')
    def test_listen_to_user_unknown_value_error(self, mock_recognizer_class, mock_microphone):
        """Test handling of unintelligible speech."""
        # Setup mocks
        mock_recognizer = Mock()
        mock_recognizer_class.return_value = mock_recognizer
        mock_recognizer.recognize_google.side_effect = Exception("UnknownValueError")
        
        mock_source = Mock()
        mock_microphone.return_value.__enter__.return_value = mock_source
        
        # Test the function
        result = listen_to_user()
        
        # Assertions
        self.assertIn("Sorry", result)
    
    @patch('voice_module.pyttsx3.init')
    def test_speak_to_user_success(self, mock_init):
        """Test successful text-to-speech conversion."""
        # Setup mocks
        mock_engine = Mock()
        mock_init.return_value = mock_engine
        
        # Test the function
        speak_to_user("Hello, this is a test")
        
        # Assertions
        mock_engine.say.assert_called_once_with("Hello, this is a test")
        mock_engine.runAndWait.assert_called_once()
    
    @patch('voice_module.pyttsx3.init')
    def test_speak_to_user_error_handling(self, mock_init):
        """Test error handling in text-to-speech conversion."""
        # Setup mocks to raise an exception
        mock_init.side_effect = Exception("TTS Error")
        
        # Test the function (should not raise an exception)
        try:
            speak_to_user("Hello, this is a test")
        except Exception:
            self.fail("speak_to_user raised an exception when it should handle errors gracefully")

class TestAppConfiguration(unittest.TestCase):
    """Test cases for application configuration and setup."""
    
    def test_gemini_wrapper_initialization(self):
        """Test GeminiWrapper initialization with valid API key."""
        # Set up environment variable
        os.environ["GOOGLE_API_KEY"] = "test_api_key"
        
        # Test the wrapper initialization
        wrapper = app.GeminiWrapper("test_api_key")
        
        # Assertions
        self.assertEqual(wrapper.api_key, "test_api_key")
    
    def test_gemini_wrapper_generate_content(self):
        """Test GeminiWrapper generate_content method with mock."""
        # This is a placeholder test that would need to be implemented with proper mocking
        # of the Gemini API responses
        pass

class TestAgentWorkflow(unittest.TestCase):
    """Test cases for agent workflow and interactions."""
    
    def setUp(self):
        """Set up test environment."""
        os.environ["GOOGLE_API_KEY"] = "test_api_key"
    
    def test_resume_analyzer_agent_creation(self):
        """Test that Resume Analyzer Agent is created with correct configuration."""
        agent = app.resume_analyzer_agent
        
        # Assertions
        self.assertEqual(agent.name, "ResumeAnalyzerAgent")
        self.assertIn("expert HR analyst", agent.system_message)
        self.assertIn("JSON object", agent.system_message)
        self.assertIn("analysis", agent.system_message)
    
    def test_question_generator_agent_creation(self):
        """Test that Question Generator Agent is created with correct configuration."""
        agent = app.question_generator_agent
        
        # Assertions
        self.assertEqual(agent.name, "QuestionGeneratorAgent")
        self.assertIn("strategic interview question designer", agent.system_message)
        self.assertIn("JSON array", agent.system_message)
        self.assertIn("5 and 8", agent.system_message)
    
    def test_interviewer_agent_creation(self):
        """Test that Interviewer Agent is created with correct configuration."""
        agent = app.interviewer_agent
        
        # Assertions
        self.assertEqual(agent.name, "InterviewerAgent")
        self.assertIn("Alex", agent.system_message)
        self.assertIn("TERMINATE", agent.system_message)
        self.assertIn("follow-up question", agent.system_message)
    
    def test_evaluator_agent_creation(self):
        """Test that Evaluator Agent is created with correct configuration."""
        agent = app.evaluator_agent
        
        # Assertions
        self.assertEqual(agent.name, "EvaluatorAgent")
        self.assertIn("evaluation engine", agent.system_message)
        self.assertIn("Markdown format", agent.system_message)
        self.assertIn("Candidate Evaluation Report", agent.system_message)
    
    def test_custom_speaker_selection_logic(self):
        """Test the custom speaker selection function logic."""
        # Create mock objects
        mock_groupchat = Mock()
        mock_groupchat.messages = [{"content": "Resume: test resume\nJob Description: test job"}]
        
        # Test initial state - should return resume analyzer
        next_speaker = app.custom_speaker_selection(None, mock_groupchat)
        self.assertEqual(next_speaker, app.resume_analyzer_agent)
        
        # Test resume analyzer -> question generator
        next_speaker = app.custom_speaker_selection(app.resume_analyzer_agent, mock_groupchat)
        self.assertEqual(next_speaker, app.question_generator_agent)
        
        # Test question generator -> interviewer
        next_speaker = app.custom_speaker_selection(app.question_generator_agent, mock_groupchat)
        self.assertEqual(next_speaker, app.interviewer_agent)
        
        # Test interviewer -> user proxy
        next_speaker = app.custom_speaker_selection(app.interviewer_agent, mock_groupchat)
        self.assertEqual(next_speaker, app.user_proxy_agent)

class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling scenarios."""
    
    def test_api_key_validation(self):
        """Test API key validation in GeminiAssistantAgent."""
        # Save the original API key
        original_api_key = os.environ.get("GOOGLE_API_KEY")
        
        try:
            # Test with placeholder API key
            os.environ["GOOGLE_API_KEY"] = "YOUR_GEMINI_API_KEY_HERE"
            
            # Import the custom agent class
            from custom_agents import GeminiAssistantAgent
            
            with self.assertRaises(ValueError) as context:
                GeminiAssistantAgent(
                    name="TestAgent",
                    system_message="Test system message",
                    model="gemini-2.5-pro",
                    temperature=0.5
                )
            
            self.assertIn("not set", str(context.exception))
        finally:
            # Restore the original API key
            if original_api_key:
                os.environ["GOOGLE_API_KEY"] = original_api_key
            elif "GOOGLE_API_KEY" in os.environ:
                del os.environ["GOOGLE_API_KEY"]
    
    def test_gemini_wrapper_error_handling(self):
        """Test error handling in GeminiWrapper."""
        # Save the original API key
        original_api_key = os.environ.get("GOOGLE_API_KEY")
        
        try:
            # Set up environment variable
            os.environ["GOOGLE_API_KEY"] = "test_api_key"
            
            # Create a wrapper instance
            wrapper = app.GeminiWrapper("test_api_key")
            
            # Test with an invalid model name (should return an error message)
            response = wrapper.generate_content("Test prompt", model="invalid-model")
            self.assertTrue(response.startswith("Error:"))
        finally:
            # Restore the original API key
            if original_api_key:
                os.environ["GOOGLE_API_KEY"] = original_api_key
            elif "GOOGLE_API_KEY" in os.environ:
                del os.environ["GOOGLE_API_KEY"]

def run_integration_tests():
    """Run all integration tests."""
    print("🧪 Running Automated Interview Agent Integration Tests...")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestVoiceModule))
    test_suite.addTest(unittest.makeSuite(TestAppConfiguration))
    test_suite.addTest(unittest.makeSuite(TestAgentWorkflow))
    test_suite.addTest(unittest.makeSuite(TestErrorHandling))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All integration tests passed!")
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)