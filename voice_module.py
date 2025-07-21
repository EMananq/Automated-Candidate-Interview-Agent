"""
Voice interaction module for the Automated Interview Agent.
This module provides functions for speech-to-text and text-to-speech conversion.
"""

import speech_recognition as sr
import pyttsx3
import time
import threading

# Global variables for recording state
_recording = False
_audio_data = None
_recognizer = sr.Recognizer()
_stop_listening = None

def start_listening():
    """
    Start listening in the background.
    
    Returns:
        bool: True if listening started successfully, False otherwise
    """
    global _recording, _audio_data, _recognizer, _stop_listening
    
    if _recording:
        return False  # Already recording
    
    try:
        # Reset audio data
        _audio_data = None
        
        # Create a callback function to store audio data
        def audio_callback(recognizer, audio):
            global _audio_data
            _audio_data = audio
        
        # Start listening in the background
        source = sr.Microphone()
        with source as s:
            # Adjust for ambient noise
            _recognizer.adjust_for_ambient_noise(s, duration=0.5)
        
        _stop_listening = _recognizer.listen_in_background(source, audio_callback)
        _recording = True
        return True
    except Exception as e:
        print(f"Error starting listening: {e}")
        return False

def stop_listening():
    """
    Stop listening and process the recorded audio.
    
    Returns:
        str: The recognized text, or an error message if recognition fails
    """
    global _recording, _audio_data, _recognizer, _stop_listening
    
    if not _recording:
        return "Not currently recording."
    
    try:
        # Stop the background listener
        if _stop_listening:
            _stop_listening(wait_for_stop=True)
            _stop_listening = None
        
        # Reset recording state
        _recording = False
        
        # If no audio was captured
        if _audio_data is None:
            return "Sorry, I didn't hear anything. Please try again."
        
        # Process the audio data
        print("Processing speech...")
        try:
            # Convert speech to text using Google's speech recognition
            text = _recognizer.recognize_google(_audio_data)
            return text
        except sr.UnknownValueError:
            return "Sorry, I couldn't understand what you said. Please try again."
        except sr.RequestError:
            return "Sorry, there was an error with the speech recognition service. Please try again."
        except Exception as e:
            print(f"Error in speech recognition: {e}")
            return f"Sorry, an error occurred: {str(e)}"
    except Exception as e:
        print(f"Error stopping listening: {e}")
        _recording = False
        return f"Sorry, an error occurred: {str(e)}"

def is_recording():
    """
    Check if recording is currently active.
    
    Returns:
        bool: True if recording is active, False otherwise
    """
    global _recording
    return _recording

def listen_to_user(timeout=5, phrase_time_limit=None, stop_callback=None):
    """
    Legacy function for compatibility. 
    Listen to the user's speech and convert it to text.
    
    Args:
        timeout (int): The maximum number of seconds to wait for speech
        phrase_time_limit (int): The maximum number of seconds for a phrase
        stop_callback (callable): A callback function that returns True when listening should stop
        
    Returns:
        str: The recognized text, or an error message if recognition fails
    """
    # Initialize recognizer
    recognizer = sr.Recognizer()
    
    try:
        # Use the microphone as source
        with sr.Microphone() as source:
            print("Listening...")
            
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            # Listen for speech
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            
            print("Processing speech...")
            
            # Convert speech to text using Google's speech recognition
            text = recognizer.recognize_google(audio)
            
            return text
    except sr.WaitTimeoutError:
        return "Sorry, I didn't hear anything. Please try again."
    except sr.UnknownValueError:
        return "Sorry, I couldn't understand what you said. Please try again."
    except sr.RequestError:
        return "Sorry, there was an error with the speech recognition service. Please try again."
    except Exception as e:
        print(f"Error in speech recognition: {str(e)}")
        return f"Sorry, an error occurred: {str(e)}"

def speak_to_user(text):
    """
    Convert text to speech and play it.
    
    Args:
        text (str): The text to convert to speech
    """
    try:
        # Initialize the text-to-speech engine
        engine = pyttsx3.init()
        
        # Set properties (optional)
        # engine.setProperty('rate', 150)  # Speed of speech
        # engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
        
        # Convert text to speech
        engine.say(text)
        
        # Wait for speech to complete
        engine.runAndWait()
    except Exception as e:
        print(f"Error in text-to-speech: {str(e)}")
        # Silently fail - don't raise exceptions from TTS errors