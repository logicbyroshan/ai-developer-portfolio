import google.generativeai as genai
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Preferred model names in order of preference
PREFERRED_MODELS = [
    "models/gemini-1.5-flash",
    "models/gemini-1.5-pro",
    "models/gemini-pro",
    "models/gemini-1.0-pro",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-pro",
]


def _get_model(system_instruction):
    """Initialize and return a Gemini model with the given system instruction."""
    if not getattr(settings, "GEMINI_API_KEY", None):
        logger.error("Gemini API key not configured")
        return None, None

    genai.configure(api_key=settings.GEMINI_API_KEY)

    # Discover available models once
    available_models = []
    try:
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                available_models.append(m.name)
    except Exception as list_error:
        logger.warning(f"Could not list models: {list_error}")

    model_names = (available_models or []) + PREFERRED_MODELS

    for model_name in model_names:
        try:
            model = genai.GenerativeModel(
                model_name,
                system_instruction=system_instruction,
            )
            logger.info(f"Initialized model: {model_name}")
            return model, model_name
        except Exception as model_error:
            logger.warning(f"Failed to init {model_name}: {model_error}")
            continue

    logger.error(f"Failed to initialize any Gemini model. Tried: {model_names}")
    return None, None


def ask_gemini(system_instruction, user_message, conversation_history=None):
    """
    Ask Gemini AI a question using separate system instruction and user message.
    Optionally accepts conversation_history (list of {"role": "user"/"model", "parts": ["text"]})
    to maintain multi-turn context within a session.
    """
    try:
        model, used_model_name = _get_model(system_instruction)

        if not model:
            return "I'm sorry, but I'm having trouble connecting to the AI service. Please try again later."

        # Use chat mode with history for multi-turn conversations
        if conversation_history:
            chat = model.start_chat(history=conversation_history)
            response = chat.send_message(user_message)
        else:
            response = model.generate_content(user_message)

        if response and response.text:
            logger.info(f"Generated response using model: {used_model_name}")
            return response.text

        logger.warning("Empty response from Gemini API")
        return "I apologize, but I couldn't generate a response. Please try again."

    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return "I'm experiencing technical difficulties. Please try again later."
