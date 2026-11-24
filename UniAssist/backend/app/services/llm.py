"""LLM access layer (Gemini by default, OpenAI optional, via LangChain). All model calls go through generate()."""
import json
import os
import re

LANGS = {"en": "English", "kn": "Kannada (ಕನ್ನಡ)", "hi": "Hindi (हिन्दी)"}


class LLMError(Exception):
    """Raised when the model is unavailable or returns unusable output."""


def _text(content):
    if isinstance(content, list):
        return "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
    return content or ""


def provider():
    return os.getenv("LLM_PROVIDER", "gemini").lower()


def model_name():
    if provider() == "gemini":
        return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _build_model(temperature):
    """Create the LangChain chat model for the configured provider."""
    prov = provider()
    if prov == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise LLMError("OPENAI_API_KEY is not configured on the server (see backend/.env).")
        from langchain_openai import ChatOpenAI
        kwargs = {"model": model_name(), "api_key": key, "timeout": 90, "max_retries": 2}
        # Reasoning models (gpt-5*, o1/o3/o4*) only accept their default temperature.
        if not model_name().lower().startswith(("gpt-5", "o1", "o3", "o4")):
            kwargs["temperature"] = temperature
        return ChatOpenAI(**kwargs)
    if prov == "gemini":
        key = os.getenv("GOOGLE_API_KEY")
        if not key:
            raise LLMError("GOOGLE_API_KEY is not configured on the server (see backend/.env).")
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model_name(), google_api_key=key, temperature=temperature)
    raise LLMError(f"Unknown LLM_PROVIDER '{prov}'. Use 'gemini' or 'openai'.")


def generate(system, prompt, temperature=0.2, history=None):
    """Call the configured LLM. `history` is a list of (role, content), role in {'user','assistant'}."""
    try:
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
        llm = _build_model(temperature)
        msgs = [SystemMessage(content=system)]
        for role, content in history or []:
            msgs.append(HumanMessage(content=content) if role == "user" else AIMessage(content=content))
        msgs.append(HumanMessage(content=prompt))
        out = _text(llm.invoke(msgs).content).strip()
    except LLMError:
        raise
    except Exception as e:  # network, quota, safety/content filter, bad key ...
        raise LLMError(f"LLM request failed: {e}") from e
    if not out:
        raise LLMError("The model returned an empty response (it may have been blocked by a content filter). Try rephrasing.")
    return out


def extract_json(text):
    """Parse JSON from a model reply, tolerating ```json fences and surrounding prose."""
    t = re.sub(r"^```(?:json)?|```$", "", (text or "").strip(), flags=re.M).strip()
    for opener, closer in (("[", "]"), ("{", "}")):
        i, j = t.find(opener), t.rfind(closer)
        if i != -1 and j > i:
            try:
                return json.loads(t[i:j + 1])
            except json.JSONDecodeError:
                continue
    raise LLMError("The model returned an unexpected format. Please try again.")
