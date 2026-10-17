import logging
import os
import time

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    InternalServerError,
    RateLimitError,
)
from agents import Model, OpenAIChatCompletionsModel, set_tracing_disabled

load_dotenv()
set_tracing_disabled(True)  # مؤقتًا، هنعمل tracing بتاعنا بعدين

log = logging.getLogger("llm")
logging.basicConfig(level=logging.INFO)

PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "model_env": "GROQ_MODEL",
        "default_model": "llama-3.3-70b-versatile",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "key_env": "GEMINI_API_KEY",
        "model_env": "GEMINI_MODEL",
        "default_model": "gemini-2.5-flash",
    },
}

# الأخطاء اللي معناها "جرّب المزود التاني"
RETRYABLE = (
    RateLimitError,
    InternalServerError,
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
)


def _build_model(name: str) -> OpenAIChatCompletionsModel:
    cfg = PROVIDERS[name]
    api_key = os.getenv(cfg["key_env"])
    if not api_key:
        raise RuntimeError(f"Missing {cfg['key_env']}")
    client = AsyncOpenAI(
        base_url=cfg["base_url"],
        api_key=api_key,
        max_retries=0,
        timeout=60,
    )
    model_name = os.getenv(cfg["model_env"], cfg["default_model"])
    return OpenAIChatCompletionsModel(model=model_name, openai_client=client)


class FallbackModel(Model):
    """موديل بيجرّب المزودين بالترتيب لحد ما واحد ينجح."""

    COOLDOWN_SECONDS = 60

    def __init__(self, names: list[str]):
        self.slots: list[tuple[str, Model]] = []
        for n in names:
            try:
                self.slots.append((n, _build_model(n)))
            except RuntimeError as e:
                log.warning("Skipping provider %s: %s", n, e)
        if not self.slots:
            raise RuntimeError("No LLM provider configured. Check your .env")
        self._blocked_until: dict[str, float] = {}

    def _candidates(self):
        now = time.time()
        ready = [s for s in self.slots if self._blocked_until.get(s[0], 0) <= now]
        return ready or self.slots

    def _mark_failed(self, name: str, err: Exception):
        self._blocked_until[name] = time.time() + self.COOLDOWN_SECONDS
        log.warning("Provider '%s' failed (%s). Switching.", name, type(err).__name__)

    async def get_response(self, *args, **kwargs):
        last_err = None
        for name, model in self._candidates():
            try:
                resp = await model.get_response(*args, **kwargs)
                log.info("Answered by: %s", name)
                return resp
            except RETRYABLE as e:
                last_err = e
                self._mark_failed(name, e)
        raise last_err

    async def stream_response(self, *args, **kwargs):
        last_err = None
        for name, model in self._candidates():
            started = False
            try:
                async for event in model.stream_response(*args, **kwargs):
                    started = True
                    yield event
                return
            except RETRYABLE as e:
                if started:
                    raise
                last_err = e
                self._mark_failed(name, e)
        raise last_err


def get_model() -> Model:
    order = os.getenv("PROVIDER_ORDER", "groq,gemini").split(",")
    return FallbackModel([n.strip() for n in order if n.strip() in PROVIDERS])