from langchain.chat_models import ChatOllama
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from typing import Dict, List, Any
import requests

class LLMService:
    def __init__(self, model_name: str = "gemma3:4b"):
        """Initialize the LLM service with Ollama"""
        self.model_name = model_name
        self.ollama_base_url = "http://localhost:11434"
        self.chat_model = None
        self.is_initialized = False
        
        # Initialize the model
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the Ollama chat model"""
        try:
            # Check if Ollama is running
            if not self._is_ollama_running():
                print("Ollama is not running. Please start Ollama server first.")
                return
                
            # Check if the model is available
            if not self._is_model_available():
                print(f"Model {self.model_name} not found. Please pull it with: ollama pull {self.model_name}")
                return
            
            # Initialize chat model with LangChain
            self.chat_model = ChatOllama(
                model=self.model_name,
                temperature=0.7,
            )
            
            self.is_initialized = True
            print(f"LLM initialized successfully with Ollama model: {self.model_name}")
            
        except Exception as e:
            print(f"Error initializing LLM with Ollama: {e}")
            self.is_initialized = False
    
    def _is_ollama_running(self):
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags")
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False
    
    def _is_model_available(self):
        """Check if the specified model is available in Ollama"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model.get("name", "") for model in models]
                # Check if the exact model name or base model is available
                base_model = self.model_name.split(':')[0] if ':' in self.model_name else self.model_name
                return any(m == self.model_name or m.startswith(f"{base_model}:") for m in model_names)
            return False
        except Exception as e:
            print(f"Error checking model availability: {e}")
            return False
    
    def generate_response(self, user_message: str, conversation_history: List[Dict[str, Any]] = None) -> str:
        """Generate a response using the LLM"""
        if not self.is_initialized:
            return f"Echo: {user_message} (Ollama not initialized)"
        
        try:
            # Create system message for therapy context
            # system_message = SystemMessage(content="""
            # You are a compassionate AI therapy assistant. Provide supportive, empathetic 
            # responses while avoiding medical advice. Focus on active listening, validation,
            # and gentle guidance. Always prioritize user safety and wellbeing.
            # """)
            system_message = SystemMessage(content="""

            """)
            
            # Format conversation history
            messages = [system_message]
            
            if conversation_history:
                for msg in conversation_history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["text"]))
                    elif msg["role"] == "model":
                        messages.append(AIMessage(content=msg["text"]))
            
            # Add the current message if not already included
            if not conversation_history or conversation_history[-1]["role"] != "user":
                messages.append(HumanMessage(content=user_message))
            
            # Generate response
            response = self.chat_model.invoke(messages)
            return response.content
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return f"Sorry, I encountered an error: {str(e)}. Please try again."
