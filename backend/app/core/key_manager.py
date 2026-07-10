import itertools
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def _build_key_list() -> list[str]:
    keys = []
    if settings.groq_api_key:
        keys.append(settings.groq_api_key)
    if settings.groq_api_keys:
        extras = [k.strip() for k in settings.groq_api_keys.split(",") if k.strip()]
        keys.extend(extras)
    return keys or ["no-key-configured"]

_keys = _build_key_list()
_cycle = itertools.cycle(_keys)

def get_next_key() -> str:
    key = next(_cycle)
    logger.debug(f"Using Groq key: ...{key[-6:]}")
    return key