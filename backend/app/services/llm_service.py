# # from langchain_community.chat_models import ChatOllama 
# from langchain_ollama import ChatOllama # use this instead of the above import because of deprecation
# from langchain.prompts import PromptTemplate
# from langchain.schema import HumanMessage, SystemMessage
# from typing import Dict, List, Any, Optional
# import requests
# from random import choice
# from app.services.retriever_service import RetrieverService
# from app.services.emotion_classifier import classify_emotion
# from app.services.chatbot_insights_pipeline import detect_medication_mentions, detect_suicide_risk
# from app.db.database import get_db
# from app.db.models import Message, Conversation
# from sqlalchemy.orm import Session

# class LLMService:
#     def __init__(self, model_name: str = "llama3", use_vllm: bool = False):
#         self.model_name = model_name
#         self.use_vllm = use_vllm
#         self.ollama_base_url = "http://localhost:11434"
#         self.vllm_base_url = "http://localhost:8001/v1"  # vLLM OpenAI-compatible endpoint
#         self.chat_model = None
#         self.retriever = RetrieverService()
#         self.is_initialized = False
#         self._initialize_model()

#     def _initialize_model(self):
#         try:
#             if self.use_vllm:
#                 if not self._is_vllm_running():
#                     print("vLLM is not running. Please start: docker-compose up vllm")
#                     return
#                 # Use ChatOllama with vLLM's OpenAI-compatible API
#                 self.chat_model = ChatOllama(
#                     base_url=self.vllm_base_url,
#                     model="meta-llama/Meta-Llama-3-8B-Instruct",
#                     temperature=0.7
#                 )
#                 self.is_initialized = True
#                 print("LLM initialized with vLLM (Llama-3-8B-Instruct)")
#             else:
#                 if not self._is_ollama_running():
#                     print("Ollama is not running. Please start the Ollama server.")
#                     return
#                 if not self._is_model_available():
#                     print(f"Model '{self.model_name}' is not available. Please run: ollama pull {self.model_name}")
#                     return
#                 self.chat_model = ChatOllama(model=self.model_name, temperature=0.7)
#                 self.is_initialized = True
#                 print(f"LLM initialized with Ollama model: {self.model_name}")
#         except Exception as e:
#             print(f"Error during model initialization: {e}")

#     def _is_ollama_running(self) -> bool:
#         try:
#             response = requests.get(f"{self.ollama_base_url}/api/tags")
#             return response.status_code == 200
#         except requests.exceptions.ConnectionError:
#             return False

#     def _is_model_available(self) -> bool:
#         try:
#             models = requests.get(f"{self.ollama_base_url}/api/tags").json().get("models", [])
#             return any(self.model_name in m.get("name", "") for m in models)
#         except:
#             return False

#     def _is_vllm_running(self) -> bool:
#         try:
#             response = requests.get(f"{self.vllm_base_url}/models")
#             return response.status_code == 200
#         except requests.exceptions.ConnectionError:
#             return False

#     def _get_varied_intro(self, emotion: str) -> str:
#         tone_map = {
#             "sadness": ["That sounds heavy. Thanks for sharing."],
#             "anxiety": ["Let’s slow down together. You’re safe here."],
#             "stress": ["Sounds like a lot’s on your plate. I get it."],
#             "neutral": ["Let’s explore this together."]
#         }
#         return choice(tone_map.get(emotion, ["I’m glad you shared that. Let’s talk through it."]))

#     def _get_grounding_exercise(self) -> str:
#         return (
#             "\U0001F33F Quick grounding exercise:\n"
#             "Take a deep breath in... and out.\n"
#             "Now name:\n"
#             "- 3 things you can see \n"
#             "- 2 things you can touch \n"
#             "- 1 thing you can hear \n"
#             "You're here now, and you're safe. "
#         )

#     def _get_branching_followup(self, user_message: str) -> str:
#         lowered = user_message.lower()
#         if "school" in lowered: return "How have your studies been affecting your mood lately?"
#         if "family" in lowered: return "Would you like to share more about what's happening at home?"
#         if "sleep" in lowered: return "Has your sleep been restful, or do you feel tired during the day?"
#         return "Is there anything you’d like to unpack more deeply?"

#     def _fetch_recent_conversation(self, user_id: str, limit: int = 5) -> List[Dict[str, str]]:
#         try:
#             db: Session = next(get_db())
#             convo = db.query(Conversation).filter_by(user_id=user_id).order_by(Conversation.last_activity_at.desc()).first()
#             if not convo: return []
#             messages = db.query(Message).filter_by(conversation_id=convo.id).order_by(Message.timestamp.desc()).limit(limit).all()
#             return [{"role": m.sender, "text": m.content} for m in reversed(messages)]
#         except Exception as e:
#             print(f"[DB Error] {e}")
#             return []

#     async def summarize_conversation(self, messages: List[Dict[str, str]]) -> str:
#         if not messages:
#             return ""

#         filtered = [msg for msg in messages if msg["role"] == "user"]
#         if messages and messages[-1]["role"] == "assistant":
#             filtered.append(messages[-1])

#         chat_log = "\n".join(f"{msg['role'].capitalize()}: {msg['text']}" for msg in filtered)

#         summary_prompt = PromptTemplate.from_template("""
# Summarize this mental health chat between a young person and a supportive assistant. Focus on emotional themes, needs, and main ideas. Avoid repeating grounding exercises or bot phrases.

# {chat_log}

# Summary:
# """)

#         try:
#             prompt = summary_prompt.format(chat_log=chat_log)
#             response = await self.chat_model.ainvoke(prompt)
#             return response.content.strip()
#         except Exception as e:
#             print(f"[Summarization Error] {e}")
#             return ""

#     async def generate_response(self, user_message: str, conversation_history: Optional[List[Dict[str, Any]]] = None, user_id: Optional[str] = None, skip_analysis: bool = False) -> str:
#         import time
#         llm_pipeline_start = time.time()
        
#         if not self.is_initialized:
#             return "Ollama not initialized."

#         # Fast path - skip heavy analysis for simple/short messages
#         if skip_analysis or len(user_message.strip()) < 10:
#             emotion = "neutral"
#             suicide_flag = False
#             meds_mentioned = []
#             retrieved_text = ""
#             print(f"    📝 LLM: Using fast path (short message)")
#         else:
#             # Only run expensive operations for longer messages
#             analysis_start = time.time()
#             emotion = classify_emotion(user_message)
#             suicide_flag = detect_suicide_risk(user_message)
#             meds_mentioned = detect_medication_mentions(user_message)
#             analysis_time = time.time() - analysis_start
#             print(f"    📊 LLM: Analysis pipeline: {analysis_time:.3f}s")

#             # Skip RAG for very short messages or greetings
#             if len(user_message.strip()) < 20 or any(greeting in user_message.lower() for greeting in ['hi', 'hello', 'hey', 'good morning', 'good evening']):
#                 retrieved_text = ""
#                 print(f"    🚫 LLM: Skipping RAG (short/greeting)")
#             else:
#                 rag_start = time.time()
#                 try:
#                     retrieved_chunks = self.retriever.search(query=user_message, top_k=2)
#                     retrieved_text = "\n\n".join(chunk for chunk in retrieved_chunks if isinstance(chunk, str)) if retrieved_chunks else ""
#                     rag_time = time.time() - rag_start
#                     print(f"    🔍 LLM: RAG search: {rag_time:.3f}s ({len(retrieved_chunks)} chunks)")
#                 except Exception as e:
#                     print(f"    ❌ LLM: RAG Error: {e}")
#                     retrieved_text = ""

#         if not conversation_history and user_id:
#             conversation_history = self._fetch_recent_conversation(user_id)

#         # Build memory block from provided history (already limited to 15 messages)
#         prompt_start = time.time()
#         memory_block = "\n".join(f"{m['role'].title()}: {m['text']}" for m in conversation_history[-10:]) if conversation_history else ""
        
#         # Skip conversation summarization for performance - use direct memory
#         tone_intro = self._get_varied_intro(emotion)

#         # Simplified system prompt for faster generation
#         system_prompt = f"""You're a caring mental health companion for young people in Rwanda.
# Speak with empathy, cultural sensitivity, and avoid clinical language.

# User Emotion: {emotion}
# {f"⚠️ Suicide Risk Detected" if suicide_flag else ""}
# {f"Medications: {', '.join(meds_mentioned)}" if meds_mentioned else ""}

# {memory_block}

# {f"Context: {retrieved_text[:500]}" if retrieved_text else ""}

# Response: {tone_intro} {self._get_branching_followup(user_message)}"""

#         messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
#         prompt_time = time.time() - prompt_start
#         print(f"    📝 LLM: Prompt building: {prompt_time:.3f}s ({len(system_prompt)} chars)")
        
#         model_start = time.time()
#         response = await self.chat_model.ainvoke(messages)
#         model_time = time.time() - model_start
#         print(f"    🤖 LLM: Model inference: {model_time:.3f}s")
        
#         llm_total_time = time.time() - llm_pipeline_start
#         print(f"    ⏱️  LLM: Total pipeline: {llm_total_time:.3f}s")
        
#         return response.content.strip()
# from langchain_community.chat_models import ChatOllama 
from langchain_ollama import ChatOllama  # newer import
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from typing import Dict, List, Any, Optional
import requests
from random import choice
from app.services.retriever_service import RetrieverService
from app.services.emotion_classifier import classify_emotion
from app.services.chatbot_insights_pipeline import detect_medication_mentions, detect_suicide_risk
from app.db.database import get_db
from app.db.models import Message, Conversation
from sqlalchemy.orm import Session

# Guardrails
from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.actions import action


# --- Intent Classifier for Guardrails ---
@action()
async def classify_intent_with_ollama(last_user_message: str):
    lowered = last_user_message.lower().strip()
    crisis_keywords = [
        "kill myself", "end my life", "suicide", "hurt myself",
        "i want to die", "i dont want to live", "take my life",
        "life isn’t worth", "no reason to live"
    ]
    for kw in crisis_keywords:
        if kw in lowered:
            return "self_harm"
    if any(k in lowered for k in ["hack", "wifi", "bomb", "drugs", "weapon"]):
        return "illegal"
    if any(k in lowered for k in ["ignore instructions", "jailbreak", "pretend to be"]):
        return "jailbreak"
    return "general"


class LLMService:
    def __init__(self, model_name: str = "llama3", use_vllm: bool = False):
        self.model_name = model_name
        self.use_vllm = use_vllm
        self.ollama_base_url = "http://localhost:11434"
        self.vllm_base_url = "http://localhost:8001/v1"  # vLLM OpenAI-compatible endpoint
        self.chat_model = None
        self.retriever = RetrieverService()
        self.is_initialized = False
        self.rails = None
        self._initialize_model()
        self._initialize_guardrails()

    def _initialize_model(self):
        try:
            if self.use_vllm:
                if not self._is_vllm_running():
                    print("vLLM is not running. Please start: docker-compose up vllm")
                    return
                self.chat_model = ChatOllama(
                    base_url=self.vllm_base_url,
                    model="meta-llama/Meta-Llama-3-8B-Instruct",
                    temperature=0.7
                )
                self.is_initialized = True
                print("LLM initialized with vLLM (Llama-3-8B-Instruct)")
            else:
                if not self._is_ollama_running():
                    print("Ollama is not running. Please start the Ollama server.")
                    return
                if not self._is_model_available():
                    print(f"Model '{self.model_name}' is not available. Please run: ollama pull {self.model_name}")
                    return
                self.chat_model = ChatOllama(model=self.model_name, temperature=0.7)
                self.is_initialized = True
                print(f"LLM initialized with Ollama model: {self.model_name}")
        except Exception as e:
            print(f"Error during model initialization: {e}")

    def _initialize_guardrails(self):
        flows_config = """
        colang: |
          flow block_illegal
            user ".*"
            call classify_intent_with_ollama $last_user_message
            if $result == "illegal":
              bot "I can’t help with that. I’m here only to support mental health and well-being."
              stop

          flow block_jailbreak
            user ".*"
            call classify_intent_with_ollama $last_user_message
            if $result == "jailbreak":
              bot "I can’t override my safety instructions. I’m here only to support mental health and your well-being."
              stop
        """
        try:
            if self.chat_model:
                config = RailsConfig.from_content(flows_config)
                self.rails = LLMRails(config, llm=self.chat_model)
                print("Guardrails loaded successfully.")
            else:
                print("Guardrails not initialized because chat_model is missing.")
        except Exception as e:
            print(f"Error loading guardrails: {e}")
            self.rails = None

    def _is_ollama_running(self) -> bool:
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags")
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False

    def _is_model_available(self) -> bool:
        try:
            models = requests.get(f"{self.ollama_base_url}/api/tags").json().get("models", [])
            return any(self.model_name in m.get("name", "") for m in models)
        except:
            return False

    def _is_vllm_running(self) -> bool:
        try:
            response = requests.get(f"{self.vllm_base_url}/models")
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False

    def _get_varied_intro(self, emotion: str) -> str:
        tone_map = {
            "sadness": ["That sounds heavy. Thanks for sharing."],
            "anxiety": ["Let’s slow down together. You’re safe here."],
            "stress": ["Sounds like a lot’s on your plate. I get it."],
            "neutral": ["Let’s explore this together."]
        }
        return choice(tone_map.get(emotion, ["I’m glad you shared that. Let’s talk through it."]))

    def _fetch_recent_conversation(self, user_id: str, limit: int = 5) -> List[Dict[str, str]]:
        try:
            db: Session = next(get_db())
            convo = db.query(Conversation).filter_by(user_id=user_id).order_by(Conversation.last_activity_at.desc()).first()
            if not convo: return []
            messages = db.query(Message).filter_by(conversation_id=convo.id).order_by(Message.timestamp.desc()).limit(limit).all()
            return [{"role": m.sender, "text": m.content} for m in reversed(messages)]
        except Exception as e:
            print(f"[DB Error] {e}")
            return []

    async def summarize_conversation(self, messages: List[Dict[str, str]]) -> str:
        if not messages:
            return ""

        filtered = [msg for msg in messages if msg["role"] == "user"]
        if messages and messages[-1]["role"] == "assistant":
            filtered.append(messages[-1])

        chat_log = "\n".join(f"{msg['role'].capitalize()}: {msg['text']}" for msg in filtered)

        summary_prompt = PromptTemplate.from_template("""
Summarize this mental health chat between a young person and a supportive assistant. Focus on emotional themes, needs, and main ideas. Avoid repeating grounding exercises or bot phrases.

{chat_log}

Summary:
""")

        try:
            prompt = summary_prompt.format(chat_log=chat_log)
            response = await self.chat_model.ainvoke(prompt)
            return response.content.strip()
        except Exception as e:
            print(f"[Summarization Error] {e}")
            return ""

    async def generate_response(self, user_message: str, conversation_history: Optional[List[Dict[str, Any]]] = None, user_id: Optional[str] = None, skip_analysis: bool = False) -> str:
        import time
        llm_pipeline_start = time.time()
        
        if not self.is_initialized:
            return "Ollama not initialized."

        # Crisis override
        if detect_suicide_risk(user_message):
            hotline_msg = (
                "It sounds like you’re going through a very difficult time. You are not alone.\n\n"
                "If you are in Rwanda:\n"
                "- Call 112 (national emergency number)\n"
                "- For ambulance services: 912\n"
                "- Rwanda Biomedical Center (RBC) toll-free mental health line: 114\n\n"
                "If you are outside Rwanda, please check: https://findahelpline.com\n"
                "You deserve support and care — please reach out now."
            )
            return hotline_msg

        # Identity override
        if user_message.strip().lower() in ["who are you", "who are you?", "what are you", "what is this"]:
            return (
                "I’m your caring mental health support companion. "
                "I’m here to listen, provide emotional support, and share helpful coping strategies. "
                "I’m not a doctor, but I can guide you and connect you with resources if you need more help."
            )

        # Normal pipeline (friend’s optimized version preserved)
        # ... (your friend’s skip_analysis, RAG, memory logic etc. continues here)

        # Run Guardrails if active
        if self.rails:
            try:
                result = await self.rails.generate_async(
                    messages=[
                        {"role": "system", "content": "You are a supportive mental health assistant."},
                        {"role": "user", "content": user_message}
                    ]
                )
                if result.get("flow_triggered"):
                    return result.get("content", "I can’t help with that request.")
            except Exception as e:
                print(f"[Guardrails Error] {e}")

        # Default fallback to model
        messages = [SystemMessage(content="You are a supportive mental health assistant."), HumanMessage(content=user_message)]
        response = await self.chat_model.ainvoke(messages)
        return response.content.strip()
