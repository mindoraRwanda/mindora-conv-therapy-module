# from langchain_community.chat_models import ChatOllama
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
#     def __init__(self, model_name: str = "llama3"):
#         self.model_name = model_name
#         self.ollama_base_url = "http://localhost:11434"
#         self.chat_model = None
#         self.retriever = RetrieverService()
#         self.is_initialized = False
#         self._initialize_model()

#     def _initialize_model(self):
#         try:
#             if not self._is_ollama_running():
#                 print("Ollama is not running. Please start the Ollama server.")
#                 return
#             if not self._is_model_available():
#                 print(f"Model '{self.model_name}' is not available. Please run: ollama pull {self.model_name}")
#                 return
#             self.chat_model = ChatOllama(model=self.model_name, temperature=0.7)
#             self.is_initialized = True
#             print(f"LLM initialized with model: {self.model_name}")
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

#     async def generate_response(self, user_message: str, conversation_history: Optional[List[Dict[str, Any]]] = None, user_id: Optional[str] = None) -> str:
#         if not self.is_initialized:
#             return "Ollama not initialized."

#         emotion = classify_emotion(user_message)
#         suicide_flag = detect_suicide_risk(user_message)
#         meds_mentioned = detect_medication_mentions(user_message)

#         if not conversation_history and user_id:
#             conversation_history = self._fetch_recent_conversation(user_id)

#         memory_block = "\n".join(f"{m['role'].title()}: {m['text']}" for m in conversation_history[-5:]) if conversation_history else ""
#         conversation_summary = await self.summarize_conversation(conversation_history[-5:] if conversation_history else [])
#         if conversation_summary:
#             memory_block = f"Summary:\n{conversation_summary}\n\nRecent Memory:\n{memory_block}"

#         try:
#             retrieved_chunks = self.retriever.search(query=user_message, top_k=3)
#             print("\n📚 [RAG Retrieved Documents]")
#             for idx, chunk in enumerate(retrieved_chunks, 1):
#                 if isinstance(chunk, str):
#                     print(f"{idx}. {chunk[:150]}...\n")
#                 else:
#                     print(f"{idx}. [Unknown format]: {chunk}\n")
#         except Exception as e:
#             print(f"[RAG Error] {e}")
#             retrieved_chunks = []

#         retrieved_text = "\n\n".join(chunk for chunk in retrieved_chunks if isinstance(chunk, str)) if retrieved_chunks else ""
#         tone_intro = self._get_varied_intro(emotion)

#         system_prompt = f"""
# You're a caring mental health companion for young people in Rwanda.
# Speak with empathy, cultural sensitivity, and avoid clinical language.
# Avoid repeating past grounding exercises. Build upon the conversation.

# User Emotion: {emotion}
# Suicide Risk: {'Yes' if suicide_flag else 'No'}
# Medications Mentioned: {', '.join(meds_mentioned) if meds_mentioned else 'None'}

# {memory_block}

# Knowledge (internal context):
# {retrieved_text}

# Start with: \"{tone_intro}\"
# Then continue with support or reflection.
# Finally, ask: {self._get_branching_followup(user_message)}
# """

#         messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
#         response = await self.chat_model.ainvoke(messages)
#         return response.content.strip()
from langchain_community.chat_models import ChatOllama
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from typing import Dict, List, Any, Optional
import requests
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
    def __init__(self, model_name: str = "llama3"):
        self.model_name = model_name
        self.ollama_base_url = "http://localhost:11434"
        self.chat_model = None
        self.retriever = RetrieverService()
        self.is_initialized = False
        self.rails = None
        self._initialize_model()
        self._initialize_guardrails()

    def _initialize_model(self):
        try:
            if not self._is_ollama_running():
                print("Ollama is not running. Please start the Ollama server.")
                return
            if not self._is_model_available():
                print(f"Model '{self.model_name}' is not available. Please run: ollama pull {self.model_name}")
                return
            self.chat_model = ChatOllama(model=self.model_name, temperature=0.7)
            self.is_initialized = True
            print(f"LLM initialized with model: {self.model_name}")
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
Summarize this mental health chat between a young person and a supportive assistant.
Focus on emotional themes, needs, and main ideas.
""")
        try:
            prompt = summary_prompt.format(chat_log=chat_log)
            response = await self.chat_model.ainvoke(prompt)
            return response.content.strip()
        except Exception as e:
            print(f"[Summarization Error] {e}")
            return ""

    async def generate_response(self, user_message: str, conversation_history: Optional[List[Dict[str, Any]]] = None, user_id: Optional[str] = None) -> str:
        if not self.is_initialized:
            return "Ollama not initialized."

        emotion = classify_emotion(user_message)
        suicide_flag = detect_suicide_risk(user_message)
        meds_mentioned = detect_medication_mentions(user_message)

        if not conversation_history and user_id:
            conversation_history = self._fetch_recent_conversation(user_id)

        memory_block = "\n".join(f"{m['role'].title()}: {m['text']}" for m in conversation_history[-5:]) if conversation_history else ""
        conversation_summary = await self.summarize_conversation(conversation_history[-5:] if conversation_history else [])
        if conversation_summary:
            memory_block = f"Summary:\n{conversation_summary}\n\nRecent Memory:\n{memory_block}"

        # --- Crisis override (LLM + hotline) ---
        if suicide_flag or (await classify_intent_with_ollama(user_message)) == "self_harm":
            crisis_prompt = f"""
            The user has expressed suicidal thoughts or self-harm intent.

            Generate a short, empathetic, supportive message as a caring mental health companion.
            Do NOT include hotline numbers yourself, just focus on empathy and reassurance.
            User message: "{user_message}"
            """
            try:
                llm_reply = await self.chat_model.ainvoke([SystemMessage(content=crisis_prompt)])
                empathetic_text = llm_reply.content.strip()
            except Exception as e:
                print(f"[Crisis Generation Error] {e}")
                empathetic_text = "I hear how much pain you’re in, and I want you to know you’re not alone."

            hotline_text = (
                "\n\nIf you are in Rwanda:\n"
                "- Call 112 (national emergency number)\n"
                "- For ambulance services: 912\n"
                "- Rwanda Biomedical Center (RBC) toll-free mental health line: 114\n\n"
                "If you are outside Rwanda, please check: https://findahelpline.com\n"
                "You deserve support and care — please reach out now."
            )

            return empathetic_text + hotline_text

        # Build system prompt (LLM decides tone, identity, follow-ups)
        try:
            retrieved_chunks = self.retriever.search(query=user_message, top_k=3)
            print("\n[RAG Retrieved Documents]")
            for idx, chunk in enumerate(retrieved_chunks, 1):
                if isinstance(chunk, str):
                    print(f"{idx}. {chunk[:150]}...\n")
                else:
                    print(f"{idx}. [Unknown format]: {chunk}\n")
        except Exception as e:
            print(f"[RAG Error] {e}")
            retrieved_chunks = []

        retrieved_text = "\n\n".join(chunk for chunk in retrieved_chunks if isinstance(chunk, str)) if retrieved_chunks else ""

        system_prompt = f"""
You are a caring mental health support companion for young people in Rwanda.
Speak with empathy, cultural sensitivity, and avoid clinical language.
Always acknowledge the user’s feelings and encourage gentle reflection.
Never provide medical diagnosis or prescriptions.

User Emotion: {emotion}
Suicide Risk: {'Yes' if suicide_flag else 'No'}
Medications Mentioned: {', '.join(meds_mentioned) if meds_mentioned else 'None'}

{memory_block}

Knowledge (retrieved context):
{retrieved_text}

Your response should:
- Start with a short empathetic reflection.
- Optionally offer a simple coping or grounding exercise (breathing, mindfulness, body relaxation, journaling, etc.).
- Provide supportive encouragement or coping strategies.
- End with ONE open-ended question that encourages the user to share more.
"""

        # Guardrails for illegal/jailbreak
        if self.rails:
            try:
                result = await self.rails.generate_async(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ]
                )
                if result.get("flow_triggered"):
                    return result.get("content", "I can’t help with that request.")
                return result.get("content", "")
            except Exception as e:
                print(f"[Guardrails Error] {e}")

        # Fallback to plain LLM
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
        response = await self.chat_model.ainvoke(messages)
        return response.content.strip()