import logging
from langchain.memory import ConversationBufferWindowMemory

logger = logging.getLogger(__name__)

# In-memory store: {session_id: ConversationBufferWindowMemory}
# On server restart, memory resets — that's fine for V1
# V2 will persist this to Redis
_memory_store: dict[str, ConversationBufferWindowMemory] = {}


def get_memory(session_id: str) -> ConversationBufferWindowMemory:
    """
    Returns the memory for a session.
    Creates a new one if it doesn't exist.
    Keeps last 10 conversation turns.
    """
    if session_id not in _memory_store:
        _memory_store[session_id] = ConversationBufferWindowMemory(
            k=10,  # remember last 10 turns
            memory_key="chat_history",
            return_messages=True,
        )
        logger.info(f"Created new memory for session: {session_id}")
    return _memory_store[session_id]


def clear_memory(session_id: str) -> None:
    """Clear memory for a session (e.g., when user starts a new chat)."""
    if session_id in _memory_store:
        del _memory_store[session_id]
        logger.info(f"Cleared memory for session: {session_id}")


def get_active_session_count() -> int:
    """How many sessions are currently in memory."""
    return len(_memory_store)
