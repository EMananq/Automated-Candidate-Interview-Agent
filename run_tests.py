#!/usr/bin/env python3
"""
Test runner for the Automated Interview Agent.
This script runs all tests and provides a comprehensive test report.
"""

import os
import sys
import subprocess
import importlib.util

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'streamlit',
        'python-dotenv',
        'SpeechRecognition',
        'PyAudio',
        'pyttsx3',
        'rich'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'python-dotenv':
                import dotenv
            elif package == 'SpeechRecognition':
                import speech_recognition
            elif package == 'PyAudio':
                import pyaudio
            else:
                __import__(package.lower())
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed!")
    return True

def check_environment():
    """Check environment configuration."""
    print("\n🔧 Checking environment configuration...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        return False
    
    print("✅ .env file exists")
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key or api_key == 'YOUR_GEMINI_API_KEY_HERE':
            print("⚠️  GOOGLE_API_KEY not configured (tests will use mock)")
        else:
            print("✅ GOOGLE_API_KEY configured")
    except Exception as e:
        print(f"❌ Error loading environment: {e}")
        return False
    
    return True

def run_unit_tests():
    """Run unit tests."""
    print("\n🧪 Running unit tests...")
    
    try:
        # Import and run integration tests
        from test_integration import run_integration_tests
        success = run_integration_tests()
        return success
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def test_voice_module():
    """Test voice module functionality (with mocks)."""
    print("\n🎤 Testing voice module...")
    
    try:
        from voice_module import listen_to_user, speak_to_user
        print("✅ Voice module imports successfully")
        
        # Test speak_to_user with a short message (this will actually speak)
        print("🔊 Testing text-to-speech (you should hear a message)...")
        speak_to_user("Testing voice module")
        print("✅ Text-to-speech test completed")
        
        return True
    except Exception as e:
        print(f"❌ Voice module test failed: {e}")
        return False

def test_app_startup():
    """Test that the main app can be imported without errors."""
    print("\n🚀 Testing app startup...")
    
    try:
        # Set a test API key to avoid validation errors
        os.environ['GOOGLE_API_KEY'] = 'test_key_for_import'
        
        # Mock autogen to avoid actual API calls
        import sys
        import types
        
        # Create a mock autogen module
        mock_autogen = types.ModuleType('autogen')
        
        # Create mock classes
        class MockAgent:
            def __init__(self, name=None, system_message=None, llm_config=None, **kwargs):
                self.name = name
                self.system_message = system_message
                self.llm_config = llm_config
        
        class MockGroupChat:
            def __init__(self, agents=None, messages=None, max_round=None, **kwargs):
                self.agents = agents or []
                self.messages = messages or []
                self.max_round = max_round
                self.speaker_selection_func = None
        
        class MockGroupChatManager:
            def __init__(self, groupchat=None, llm_config=None, **kwargs):
                self.groupchat = groupchat
                self.llm_config = llm_config
        
        # Add mock classes to the mock module
        mock_autogen.AssistantAgent = MockAgent
        mock_autogen.UserProxyAgent = MockAgent
        mock_autogen.GroupChat = MockGroupChat
        mock_autogen.GroupChatManager = MockGroupChatManager
        mock_autogen.Agent = MockAgent  # Add the missing Agent class
        
        # Save the original module if it exists
        original_autogen = sys.modules.get('autogen')
        
        # Add the mock module to sys.modules
        sys.modules['autogen'] = mock_autogen
        
        try:
            # Now import app with the mock autogen
            import importlib
            if 'app' in sys.modules:
                del sys.modules['app']  # Remove any previous import
            import app
            print("✅ App imports successfully")
            
            # Test that agents are created
            agents = [
                app.resume_analyzer_agent,
                app.question_generator_agent,
                app.interviewer_agent,
                app.evaluator_agent,
                app.user_proxy_agent
            ]
            
            for agent in agents:
                if hasattr(agent, 'name'):
                    print(f"✅ {agent.name} created successfully")
                else:
                    print(f"❌ Agent missing name attribute")
                    return False
            
            print("✅ All agents created successfully")
            return True
        finally:
            # Restore the original module if it existed
            if original_autogen:
                sys.modules['autogen'] = original_autogen
            elif 'autogen' in sys.modules:
                del sys.modules['autogen']
    
    except Exception as e:
        print(f"❌ App startup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner function."""
    print("🤖 Automated Interview Agent - Test Suite")
    print("=" * 50)
    
    # Track test results
    test_results = []
    
    # Run dependency check
    test_results.append(("Dependencies", check_dependencies()))
    
    # Run environment check
    test_results.append(("Environment", check_environment()))
    
    # Run app startup test
    test_results.append(("App Startup", test_app_startup()))
    
    # Run unit tests
    test_results.append(("Unit Tests", run_unit_tests()))
    
    # Run voice module test (optional, as it requires audio hardware)
    try:
        test_results.append(("Voice Module", test_voice_module()))
    except Exception as e:
        print(f"⚠️  Voice module test skipped: {e}")
        test_results.append(("Voice Module", None))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print("-" * 20)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, result in test_results:
        if result is True:
            print(f"✅ {test_name}: PASSED")
            passed += 1
        elif result is False:
            print(f"❌ {test_name}: FAILED")
            failed += 1
        else:
            print(f"⚠️  {test_name}: SKIPPED")
            skipped += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed == 0:
        print("\n🎉 All tests passed! The Automated Interview Agent is ready to use.")
        print("\nTo start the application, run:")
        print("streamlit run app.py")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please fix the issues before using the application.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)