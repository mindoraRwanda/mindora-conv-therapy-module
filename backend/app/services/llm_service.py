# from langchain.chat_models import ChatOllama
# from langchain.schema import HumanMessage, AIMessage, SystemMessage
# from typing import AsyncGenerator, Dict, List, Any
# import requests

# class LLMService:
#     def __init__(self, model_name: str = "llama3"):
#         """Initialize the LLM service with Ollama"""
#         self.model_name = model_name
#         self.ollama_base_url = "http://localhost:11434"
#         self.chat_model = None
#         self.is_initialized = False
        
#         # Initialize the model
#         self._initialize_model()
    
#     def _initialize_model(self):
#         """Initialize the Ollama chat model"""
#         try:
#             # Check if Ollama is running
#             if not self._is_ollama_running():
#                 print("Ollama is not running. Please start Ollama server first.")
#                 return
                
#             # Check if the model is available
#             if not self._is_model_available():
#                 print(f"Model {self.model_name} not found. Please pull it with: ollama pull {self.model_name}")
#                 return
            
#             # Initialize chat model with LangChain
#             self.chat_model = ChatOllama(
#                 model=self.model_name,
#                 temperature=0.7,
#             )
            
#             self.is_initialized = True
#             print(f"LLM initialized successfully with Ollama model: {self.model_name}")
            
#         except Exception as e:
#             print(f"Error initializing LLM with Ollama: {e}")
#             self.is_initialized = False
    
#     def _is_ollama_running(self):
#         """Check if Ollama server is running"""
#         try:
#             response = requests.get(f"{self.ollama_base_url}/api/tags")
#             return response.status_code == 200
#         except requests.exceptions.ConnectionError:
#             return False
    
#     def _is_model_available(self):
#         """Check if the specified model is available in Ollama"""
#         try:
#             response = requests.get(f"{self.ollama_base_url}/api/tags")
#             if response.status_code == 200:
#                 models = response.json().get("models", [])
#                 model_names = [model.get("name", "") for model in models]
#                 # Check if the exact model name or base model is available
#                 base_model = self.model_name.split(':')[0] if ':' in self.model_name else self.model_name
#                 return any(m == self.model_name or m.startswith(f"{base_model}:") for m in model_names)
#             return False
#         except Exception as e:
#             print(f"Error checking model availability: {e}")
#             return False
#     async def generate_response(
#         self,
#         user_message: str,
#         conversation_history: List[Dict[str, Any]] = None,
#         stream: bool = False
#     ) -> str | AsyncGenerator[str, None]:
#         """Generate response with optional streaming"""
#         if not self.is_initialized:
#             yield "Ollama not initialized."
#             return

#         try:
#             system_message = SystemMessage(content="""
#             You are Mindora, a kind and empathetic mental health assistant.
#             Speak gently, validate feelings, and avoid giving direct medical advice.
#             Encourage users to talk and provide emotional support. Always prioritize user safety and wellbeing.
#             """)

#             messages = [system_message]

#             if conversation_history:
#                 for msg in conversation_history:
#                     if msg["role"] == "user":
#                         messages.append(HumanMessage(content=msg["text"]))
#                     elif msg["role"] == "model":
#                         messages.append(AIMessage(content=msg["text"]))

#             messages.append(HumanMessage(content=user_message))

#             if stream:
#                 # Streaming generator (yield tokens as they arrive)
#                 async for chunk in self.chat_model.astream(messages):
#                     yield chunk.content
#             else:
#                 response = await self.chat_model.ainvoke(messages)
#                 return response.content

#         except Exception as e:
#             yield f"[Error] {str(e)}"    
    
#     # def generate_response(self, user_message: str, conversation_history: List[Dict[str, Any]] = None) -> str:
#     #     """Generate a response using the LLM"""
#     #     if not self.is_initialized:
#     #         return f"Echo: {user_message} (Ollama not initialized)"
        
#     #     try:
#     #         # Create system message for therapy context
#     #         # system_message = SystemMessage(content="""
#     #         # You are a compassionate AI therapy assistant. Provide supportive, empathetic 
#     #         # responses while avoiding medical advice. Focus on active listening, validation,
#     #         # and gentle guidance. Always prioritize user safety and wellbeing.
#     #         # """)
#     #         system_message = SystemMessage(content="""

#     #         """)
            
#     #         # Format conversation history
#     #         messages = [system_message]
            
#     #         if conversation_history:
#     #             for msg in conversation_history:
#     #                 if msg["role"] == "user":
#     #                     messages.append(HumanMessage(content=msg["text"]))
#     #                 elif msg["role"] == "model":
#     #                     messages.append(AIMessage(content=msg["text"]))
            
#     #         # Add the current message if not already included
#     #         if not conversation_history or conversation_history[-1]["role"] != "user":
#     #             messages.append(HumanMessage(content=user_message))
            
#     #         # Generate response
#     #         response = self.chat_model.invoke(messages)
#     #         return response.content
            
#     #     except Exception as e:
#     #         print(f"Error generating response: {e}")
#     #         return f"Sorry, I encountered an error: {str(e)}. Please try again."
from langchain.chat_models import ChatOllama
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from typing import AsyncGenerator, Dict, List, Any
import requests

# Import your retriever
from app.services.retriever_service import RetrieverService

class LLMService:
    """
    A wrapper around LangChain's ChatOllama for generating and streaming responses
    with optional document context from a vector database.
    """

    def __init__(self, model_name: str = "llama3"):
        self.model_name = model_name
        self.ollama_base_url = "http://localhost:11434"
        self.chat_model = None
        self.retriever = RetrieverService()  # <-- Load retriever here
        self.is_initialized = False
        self._initialize_model()

    def _initialize_model(self):
        try:
            if not self._is_ollama_running():
                print("Ollama is not running. Please start the Ollama server.")
                return

            if not self._is_model_available():
                print(f"Model '{self.model_name}' is not available. Please run: ollama pull {self.model_name}")
                return

            self.chat_model = ChatOllama(
                model=self.model_name,
                temperature=0.7,
            )
            self.is_initialized = True
            print(f"LLM initialized with model: {self.model_name}")
        except Exception as e:
            print(f"Error during model initialization: {e}")
            self.is_initialized = False

    def _is_ollama_running(self) -> bool:
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags")
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False

    def _is_model_available(self) -> bool:
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model.get("name", "") for model in models]
                base_model = self.model_name.split(':')[0] if ':' in self.model_name else self.model_name
                return any(m == self.model_name or m.startswith(f"{base_model}:") for m in model_names)
            return False
        except Exception as e:
            print(f"Error checking model availability: {e}")
            return False

  

    async def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a response using LLM with RAG support (retrieves relevant context from documents).
        """
        if not self.is_initialized:
            return "Ollama not initialized."

        try:
            # Retrieve top matching document chunks for user query
            retrieved_chunks = self.retriever.search(user_message, top_k=3)

            # Log retrieved context chunks to confirm RAG is working
            print("\n Retrieved Context for RAG:\n", "\n---\n".join(retrieved_chunks))

            # Merge chunks into a single string for system prompt injection
            retrieved_text = "\n\n".join(retrieved_chunks)

            # Build the system message using the retrieved context
            system_message = SystemMessage(content=f"""
            You are Mindora, a kind and empathetic mental health assistant.

            Use the following context to guide your answer:

            {retrieved_text}

            Speak gently, validate feelings, and avoid giving direct medical advice.
            Encourage users to talk and prioritize their emotional safety and wellbeing.
            """)

            # Compose the conversation history
            messages = [system_message]

            if conversation_history:
                for msg in conversation_history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["text"]))
                    elif msg["role"] == "model":
                        messages.append(AIMessage(content=msg["text"]))

            # Add the current user message
            messages.append(HumanMessage(content=user_message))

            # Invoke the LLM with the full message list
            response = await self.chat_model.ainvoke(messages)
            return response.content

        except Exception as e:
            return f"[Error] {str(e)}"
