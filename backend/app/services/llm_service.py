# from langchain_community.chat_models import ChatOllama 
from langchain_ollama import ChatOllama  # updated import
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

    def _is_vllm_running(self) -> bool:
        try:
            response = requests.get(f"{self.vllm_base_url}/models")
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False

    async def _get_branching_followup(self, user_message: str) -> str:
        """Use LLM to generate a natural follow-up instead of hardcoded school/family/sleep rules."""
        prompt = f"""
        The user just said: "{user_message}"

        Generate one short, empathetic follow-up question that encourages them to open up.
        Do not give advice. Keep it supportive and conversational.
        """
        try:
            reply = await self.chat_model.ainvoke([SystemMessage(content=prompt)])
            return reply.content.strip()
        except:
            return "Would you like to share a bit more about how you're feeling?"

    async def _get_grounding_exercise(self) -> str:
        """Ask LLM to generate grounding exercise suggestions instead of hardcoding."""
        prompt = """
        Suggest one short grounding exercise for anxiety or stress.
        Keep it simple, kind, and suitable for young people in Rwanda.
        Example formats: breathing, noticing surroundings, or body relaxation.
        """
        try:
            reply = await self.chat_model.ainvoke([SystemMessage(content=prompt)])
            return reply.content.strip()
        except:
            return "Take a deep breath in... and out. Now notice 3 things you can see around you."

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
Focus on emotional themes, needs, and main ideas. Avoid repeating grounding exercises or bot phrases.

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

    async def generate_response(self, user_message: str, conversation_history: Optional[List[Dict[str, Any]]] = None,
                                user_id: Optional[str] = None, skip_analysis: bool = False) -> str:
        import time
        llm_pipeline_start = time.time()

        if not self.is_initialized:
            return "Ollama not initialized."

        # Run analysis
        emotion = classify_emotion(user_message)
        suicide_flag = detect_suicide_risk(user_message)
        meds_mentioned = detect_medication_mentions(user_message)

        # Crisis override → hotline numbers are fixed, but phrasing is LLM-generated
        if suicide_flag or (await classify_intent_with_ollama(user_message)) == "self_harm":
            hotline_info = """
            If you are in Rwanda:
            - Call 112 (national emergency number)
            - For ambulance services: 912
            - Rwanda Biomedical Center (RBC) toll-free mental health line: 114

            If you are outside Rwanda, please check: https://findahelpline.com
            """
            crisis_prompt = f"""
            The user is experiencing a mental health crisis.
            Write a compassionate, empathetic response.
            End by sharing this hotline info clearly:

            {hotline_info}
            """
            response = await self.chat_model.ainvoke([SystemMessage(content=crisis_prompt)])
            return response.content.strip()

        # Handle identity questions ("who are you?")
        if user_message.strip().lower() in ["who are you", "who are you?", "what are you", "what is this"]:
            return (
                "I’m your caring mental health support companion. "
                "I’m here to listen, provide emotional support, and share helpful coping strategies. "
                "I’m not a doctor, but I can guide you, remind you that you’re not alone, "
                "and connect you with resources if you need more help."
            )

        # Build memory block
        if not conversation_history and user_id:
            conversation_history = self._fetch_recent_conversation(user_id)
        memory_block = "\n".join(f"{m['role'].title()}: {m['text']}" for m in conversation_history[-10:]) if conversation_history else ""

        # RAG retrieval
        retrieved_text = ""
        try:
            retrieved_chunks = self.retriever.search(query=user_message, top_k=2)
            retrieved_text = "\n\n".join(chunk for chunk in retrieved_chunks if isinstance(chunk, str)) if retrieved_chunks else ""
        except Exception as e:
            print(f"[RAG Error] {e}")

        # Build system prompt
        followup = await self._get_branching_followup(user_message)
        grounding = await self._get_grounding_exercise()

        system_prompt = f"""You're a caring mental health companion for young people in Rwanda.
Speak with empathy, cultural sensitivity, and avoid clinical language.

User Emotion: {emotion}
Suicide Risk: {"Yes" if suicide_flag else "No"}
Medications Mentioned: {', '.join(meds_mentioned) if meds_mentioned else "None"}

{memory_block}

Knowledge (internal context):
{retrieved_text}

When appropriate, you may suggest a grounding exercise like:
{grounding}

Finally, ask: {followup}
"""

        # Try Guardrails first
        if self.rails:
            try:
                result = await self.rails.generate_async(
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}]
                )
                if result.get("flow_triggered"):
                    return result.get("content", "I can’t help with that request.")
                return result.get("content", "")
            except Exception as e:
                print(f"[Guardrails Error] {e}")

        # Fallback: plain LLM
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
        response = await self.chat_model.ainvoke(messages)

        llm_total_time = time.time() - llm_pipeline_start
        print(f"LLM pipeline completed in {llm_total_time:.3f}s")

        return response.content.strip()
