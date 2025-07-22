# from langchain_community.chat_models import ChatOllama
# from langchain.schema import HumanMessage, AIMessage, SystemMessage
# from typing import AsyncGenerator, Dict, List, Any
# import requests
# from app.services.retriever_service import RetrieverService
# from app.services.emotion_classifier import classify_emotion  # Emotion detection
# from app.services.chatbot_insights_pipeline import detect_medication_mentions, detect_suicide_risk

# class LLMService:
#     """
#     A wrapper around LangChain's ChatOllama for generating and streaming responses
#     with optional document context from a vector database.
#     Emotion-aware, self-hosted, production-ready.
#     Includes medication and suicide-risk awareness.
#     """

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

#             self.chat_model = ChatOllama(
#                 model=self.model_name,
#                 temperature=0.7,
#             )
#             self.is_initialized = True
#             print(f"LLM initialized with model: {self.model_name}")
#         except Exception as e:
#             print(f"Error during model initialization: {e}")
#             self.is_initialized = False

#     def _is_ollama_running(self) -> bool:
#         try:
#             response = requests.get(f"{self.ollama_base_url}/api/tags")
#             return response.status_code == 200
#         except requests.exceptions.ConnectionError:
#             return False

#     def _is_model_available(self) -> bool:
#         try:
#             response = requests.get(f"{self.ollama_base_url}/api/tags")
#             if response.status_code == 200:
#                 models = response.json().get("models", [])
#                 model_names = [model.get("name", "") for model in models]
#                 base_model = self.model_name.split(':')[0] if ':' in self.model_name else self.model_name
#                 return any(m == self.model_name or m.startswith(f"{base_model}:") for m in model_names)
#             return False
#         except Exception as e:
#             print(f"Error checking model availability: {e}")
#             return False

    
#     async def generate_response(
#     self,
#     user_message: str,
#     conversation_history: List[Dict[str, Any]] = None,
#     user_id: str = None  # Optional if you implement persistent memory later
# ) -> str:
#         if not self.is_initialized:
#             return "Ollama not initialized."

#         try:
#             retrieved_chunks = []

#             # Step 1: Emotion classification
#             emotion = classify_emotion(user_message)
#             print(f"[Emotion Detected] {emotion}")

#             # Step 2: Suicide risk and medication detection
#             suicide_flag = detect_suicide_risk(user_message)
#             meds_mentioned = detect_medication_mentions(user_message)

#             # Step 3: RAG document retrieval
#             try:
#                 retrieved_chunks = self.retriever.search(user_message, top_k=3)
#                 if retrieved_chunks:
#                     print("\n[Retrieved Context for RAG]\n", "\n---\n".join(retrieved_chunks))
#                 else:
#                     print("\n[No documents retrieved. Falling back to generic prompt.]")
#             except Exception as retrieval_error:
#                 print(f"\n[Retrieval error] {retrieval_error}")

#             retrieved_text = "\n\n".join(retrieved_chunks) if retrieved_chunks else "[No context]"

#             # Step 4: Tone mapping by emotion
#             emotion_tone_map = {
#                 "sadness": "Be especially warm and reassuring.",
#                 "anxiety": "Speak calmly and help ground the user.",
#                 "fear": "Provide emotional safety and reassurance.",
#                 "anger": "Acknowledge the frustration gently.",
#                 "joy": "Encourage and celebrate progress.",
#                 "guilt": "Be non-judgmental and accepting.",
#                 "craving": "Use motivational interviewing tone.",
#                 "numbness": "Speak softly and encourage openness.",
#                 "stress": "Help the user feel less overwhelmed.",
#                 "neutral": "Speak naturally and supportively."
#             }
#             emotion_guidance = emotion_tone_map.get(emotion, "Speak with empathy.")

#             # Step 5: Memory windowing
#             memory_messages = []
#             if conversation_history:
#                 for msg in conversation_history[-5:]:
#                     if msg["role"] == "user":
#                         memory_messages.append(f"User: {msg['text']}")
#                     elif msg["role"] == "model":
#                         memory_messages.append(f"Bot: {msg['text']}")
#             memory_block = "\n".join(memory_messages)

#             # Step 6: Optional summarization placeholder
#             conversation_summary = ""  # In the future, generate summary and inject here
#             if conversation_summary:
#                 memory_block = f"[Summary of earlier conversation]\n{conversation_summary}\n\n{memory_block}"

#             # Step 7: Final therapeutic system prompt (your original, preserved)
#             system_prompt = f"""
#     You are a supportive, therapeutic conversational partner. Your goal is not to give complete answers all at once. Instead, you guide the user gently through their thoughts and feelings, one step at a time.

#     # Maintain a calm, warm, human tone. Ask open-ended and reflective questions when appropriate. Build the conversation slowly and meaningfully—like a walk through someone’s emotions or ideas.

#     # Avoid overwhelming the user with too much information. Let your responses encourage continued dialogue, introspection, and emotional clarity.

#     Emotion detected: **{emotion}**
#     {emotion_guidance}

#     Suicide risk: {'HIGH - be extra cautious and empathetic.' if suicide_flag else 'Low'}
#     Medications mentioned: {', '.join(meds_mentioned) if meds_mentioned else 'None'}

#     Conversation memory:
#     {memory_block}

#     Use the following context if relevant:
#     {retrieved_text}

#     💡 Response Guidelines:
#     Respond with kindness, but avoid overuse of emotional phrases or artificial warmth like "dear one" or "*warm smile*".

#     Use short, clear sentences. When giving suggestions or advice:
#     - Break them into steps using numbers or bullet points.
#     - Use simple language appropriate for both fluent and emerging English speakers in Rwanda.
#     - Keep tone friendly, professional, and grounded.

#     - Speak simply, clearly, and kindly.
#     - Avoid dramatic expressions like "*smile*", "dear one", or roleplay behavior.
#     - DO NOT use markdown symbols like **bold** or *italics*.
#     - Use numbered steps (1., 2., 3.) when explaining strategies.
#     - You may use basic emojis sparingly (🙂, 🙏, 🧘) to feel human — but stay professional.

#     Avoid medical diagnoses or clinical labels. Focus on:
#     - Helping the user feel heard
#     - Sharing emotional support strategies 
#     - Encouraging self-awareness and positive action

#     You are a supportive, emotionally intelligent mental health assistant. When replying to users, always format your responses clearly and warmly. Follow these formatting rules:

#     1. Use short, clear paragraphs.
#     2. Use numbered lists when giving step-by-step advice.
#     3. Use bullet points (-) when listing tips or suggestions.
#     4. Use *italics* to emphasize key ideas or emotional validation (but not too much).
#     5. Include emojis occasionally (1–2 per message) to express warmth or support — e.g., 😊, 🙏, 🌱, 💛.
#     6. Always leave blank lines between sections or list items for readability.
#     7. Never use bold (** **), headers (###), code blocks, or markdown tables.
#     8. End each message with a gentle follow-up question to keep the conversation going (e.g., "Would you like to try that with me?" or "How have you been feeling today?").

#     Examples of good formatting:

#     ---

#     I'm really sorry you're feeling this way — you're not alone, and I'm here for you.

#     Here are a few small steps that might help:

#     1. *Try to eat a little something*, even if it’s small — your body needs energy.
#     2. *Practice deep breathing* — inhale slowly for 4 counts, hold, and exhale.
#     3. *Reach out to someone you trust* — talking helps lighten the load. 🙏

#     Let’s try a simple grounding technique called the *5-4-3-2-1* method. It can help when your thoughts feel overwhelming.

#     - 👀 **5 things you can see** – look around and name them.
#     - ✋ **4 things you can touch** – your clothes, a chair, your hair.
#     - 👂 **3 things you can hear** – maybe a bird, a car, or your own breath.
#     - 👃 **2 things you can smell** – or imagine a smell you like.
#     - 👅 **1 thing you can taste** – even if it’s just your tongue.

#     Take your time. Breathe slowly as you do this.  
#     Would you like to try it now together?

#     ---

#     Always respond with kindness and calm presence.

#     End with an open invitation to continue the conversation, not a fixed conclusion.
#             """

#             # Step 8: Build message chain
#             messages = [SystemMessage(content=system_prompt)]
#             messages.append(HumanMessage(content=user_message))

#             # Step 9: Get LLM response
#             response = await self.chat_model.ainvoke(messages)
#             return response.content

#         except Exception as e:
#             return f"[Error] {str(e)}"
from langchain_community.chat_models import ChatOllama
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from typing import AsyncGenerator, Dict, List, Any
import requests
from random import choice
from app.services.retriever_service import RetrieverService
from app.services.emotion_classifier import classify_emotion  # Emotion detection
from app.services.chatbot_insights_pipeline import detect_medication_mentions, detect_suicide_risk

class LLMService:
    def __init__(self, model_name: str = "llama3"):
        self.model_name = model_name
        self.ollama_base_url = "http://localhost:11434"
        self.chat_model = None
        self.retriever = RetrieverService()
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

    def _get_varied_intro(self, emotion: str) -> str:
        tone_map = {
            "sadness": [
                "That sounds heavy. Thanks for sharing.",
                "I'm really sorry you're feeling like this. That takes courage to say.",
                "That's a lot to carry — I'm here for you."
            ],
            "anxiety": [
                "Let’s slow down together. You’re safe here.",
                "It’s okay to feel overwhelmed. Let's breathe together.",
                "Those racing thoughts must be exhausting — let’s unpack them." 
            ],
            "stress": [
                "Sounds like a lot’s on your plate. I get it.",
                "It makes sense you feel this way given everything going on.",
                "You're under a lot right now — that pressure adds up."
            ],
            "neutral": [
                "Let’s explore this together.",
                "I'm here to walk through this with you.",
                "Let's take it one step at a time." 
            ]
        }
        return choice(tone_map.get(emotion, ["I’m glad you shared that. Let’s talk through it."]))

    # (Summarization, grounding, rubric, follow-up logic remains unchanged)

    async def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, Any]] = None,
        user_id: str = None
    ) -> str:
        if not self.is_initialized:
            return "Ollama not initialized."

        try:
            emotion = classify_emotion(user_message)
            suicide_flag = detect_suicide_risk(user_message)
            meds_mentioned = detect_medication_mentions(user_message)

            memory_messages = []
            if conversation_history:
                for msg in conversation_history[-5:]:
                    role = msg["role"]
                    text = msg["text"]
                    memory_messages.append(f"{role.title()}: {text}")
            memory_block = "\n".join(memory_messages)

            conversation_summary = await self.summarize_conversation(conversation_history[-5:] if conversation_history else [])
            if conversation_summary:
                memory_block = f"Summary:\n{conversation_summary}\n\nRecent Memory:\n{memory_block}"

            try:
                retrieved_chunks = self.retriever.search(
                    query=user_message,
                    top_k=3,
                    emotion=emotion,
                    suicide_risk=suicide_flag,
                    meds=meds_mentioned,
                    context_summary=conversation_summary
                )
            except Exception as e:
                print(f"[RAG Error] {e}")
                retrieved_chunks = []

            retrieved_text = "\n\n".join(retrieved_chunks) if retrieved_chunks else "[No context found]"
            tone_intro = self._get_varied_intro(emotion)

            risk_check = ""
            if suicide_flag:
                risk_check = (
                    "Sometimes when people feel this way, they have thoughts about not wanting to be here.\n"
                    "Have you felt anything like that? It’s okay to talk about it. 🙏\n"
                )

            followup = self._get_branching_followup(user_message)

            system_prompt = f"""
You're a caring mental health companion for young people in Rwanda.

Start responses with varied emotional reflections. Avoid scripted phrases.
Use informal tone, natural phrasing, and local empathy.

Emotion: {emotion}
Risk: {'🚨 High (check gently)' if suicide_flag else 'Low'}
Medications: {', '.join(meds_mentioned) if meds_mentioned else 'None'}

Memory:
{memory_block}

Knowledge:
{retrieved_text}

Response Style:
- Avoid repeating identical phrases in multiple turns
- Mirror and expand emotional context
- Gently ask about risk when needed
- Speak casually, like a supportive peer
- Use 1–2 emojis (e.g., 🌱, 🙏) max
- Ask one follow-up at the end
---
Start your reply with something like:
"{tone_intro}"

{risk_check}
{self._get_grounding_exercise()}

{followup}

{self._get_response_rubric()}
---
"""
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
            response = await self.chat_model.ainvoke(messages)
            return response.content

        except Exception as e:
            return f"[Error] {str(e)}"
