"""
Custom agent implementations for the Automated Interview Agent.
This module provides custom agent implementations that don't rely on OpenAI's API format.
"""

import os
import google.generativeai as genai
from typing import Dict, Any, Optional, List, Union

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
    
    autogen = MockAutogen()

class GeminiAssistantAgent(autogen.AssistantAgent):
    """
    A custom AssistantAgent that uses Google's Gemini API directly instead of
    relying on AutoGen's OpenAI client.
    """
    
    def __init__(
        self,
        name: str,
        system_message: str,
        model: str = "gemini-2.5-pro",
        temperature: float = 0.7,
        *args,
        **kwargs
    ):
        """
        Initialize a GeminiAssistantAgent.
        
        Args:
            name: The name of the agent
            system_message: The system message that defines the agent's behavior
            model: The Gemini model to use
            temperature: The temperature parameter for generation
            *args, **kwargs: Additional arguments to pass to the parent class
        """
        # Remove llm_config from kwargs if present to avoid OpenAI client initialization
        if "llm_config" in kwargs:
            del kwargs["llm_config"]
            
        # Create a valid llm_config that will pass validation
        valid_llm_config = {
            "config_list": [
                {
                    "model": model,
                    "api_key": os.environ.get("GOOGLE_API_KEY", "dummy_key"),
                    "api_type": "openai"
                }
            ],
            "temperature": temperature
        }
            
        # Initialize the parent class with a valid llm_config
        super().__init__(
            name=name,
            system_message=system_message,
            llm_config=valid_llm_config,
            *args,
            **kwargs
        )
        
        # Store Gemini-specific parameters
        self.model = model
        self.temperature = temperature
        
        # Configure Gemini API
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE":
            raise ValueError("GOOGLE_API_KEY not found or not set. Please check your .env file.")
        
        genai.configure(api_key=api_key)
    
    def generate_reply(
        self,
        messages: List[Dict[str, str]],
        sender=None,
        **kwargs
    ) -> Union[str, Dict[str, Any], None]:
        """
        Generate a reply using the Gemini API instead of AutoGen's default mechanism.
        
        Args:
            messages: The conversation history
            sender: The agent that sent the last message
            **kwargs: Additional arguments
            
        Returns:
            The generated reply
        """
        # Convert messages to a format suitable for Gemini
        prompt = self._format_messages_for_gemini(messages)
        
        try:
            # Configure the generation config
            generation_config = {
                "temperature": self.temperature,
                "top_p": 0.95,
                "top_k": 0,
                "max_output_tokens": 8192,
            }
            
            # Create the model
            model = genai.GenerativeModel(
                model_name=self.model,
                generation_config=generation_config
            )
            
            # Generate content
            response = model.generate_content(prompt)
            
            # Return the text
            return response.text
        except Exception as e:
            print(f"Error generating content with Gemini: {e}")
            return f"Error: {str(e)}"
    
    def _format_messages_for_gemini(self, messages: List[Dict[str, str]]) -> str:
        """
        Format the conversation history for Gemini.
        
        Args:
            messages: The conversation history
            
        Returns:
            A formatted prompt string
        """
        # Start with the system message
        formatted_prompt = f"System: {self.system_message}\n\n"
        
        # Add the conversation history
        for message in messages:
            role = message.get("role", "user")
            if role == "user":
                formatted_prompt += f"User: {message['content']}\n\n"
            elif role == "assistant":
                formatted_prompt += f"Assistant: {message['content']}\n\n"
            else:
                formatted_prompt += f"{role.capitalize()}: {message['content']}\n\n"
        
        # Add a final prompt for the assistant to respond
        formatted_prompt += "Assistant: "
        
        return formatted_prompt