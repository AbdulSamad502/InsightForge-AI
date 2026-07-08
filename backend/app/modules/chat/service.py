import json
import logging
import pandas as pd
from pathlib import Path
from sqlalchemy.orm import Session

from app.modules.chat import repository
from app.modules.chat.schemas import (
    CreateSessionRequest, SendMessageRequest,
    ChatMessageResponse, ChatSessionResponse, AgentResponse,
)
from app.modules.datasets.repository import get_dataset_by_id
from app.core.exceptions import DatasetNotFoundError, AgentError
from app.ai.agent.intent_classifier import classify_intent
from app.ai.agent.executor import run_agent

logger = logging.getLogger(__name__)


def _load_dataframe(dataset_id: str, user_id: str, db: Session) -> pd.DataFrame:
    """Load the dataset file into a pandas DataFrame."""
    dataset = get_dataset_by_id(db, dataset_id)
    if not dataset or dataset.user_id != user_id:
        raise DatasetNotFoundError(dataset_id)

    file_path = Path(dataset.file_path)
    if not file_path.exists():
        raise DatasetNotFoundError(dataset_id)

    if dataset.file_type == "csv":
        return pd.read_csv(file_path, low_memory=False)
    else:
        return pd.read_excel(file_path, engine="openpyxl")


async def create_session(
    data: CreateSessionRequest, user_id: str, db: Session
) -> ChatSessionResponse:
    """Create a new chat session linked to a dataset."""
    # Verify dataset exists and belongs to user
    dataset = get_dataset_by_id(db, data.dataset_id)
    if not dataset or dataset.user_id != user_id:
        raise DatasetNotFoundError(data.dataset_id)

    session = repository.create_session(
        db=db,
        user_id=user_id,
        dataset_id=data.dataset_id,
        title=data.title,
    )
    return ChatSessionResponse.model_validate(session)


async def send_message(
    session_id: str,
    data: SendMessageRequest,
    user_id: str,
    db: Session,
) -> AgentResponse:
    """
    Main message handler:
    load df → classify intent → run agent → save messages → return response
    """
    # Verify session belongs to user
    session = repository.get_session(db, session_id)
    if not session or session.user_id != user_id:
        raise AgentError("Session not found.")

    # Save user message first
    user_msg = repository.save_message(
        db=db,
        session_id=session_id,
        role="user",
        content=data.message,
    )

    try:
        # Load DataFrame
        df = _load_dataframe(session.dataset_id, user_id, db)
        columns = list(df.columns)

        # Classify intent (fast model)
        intent = await classify_intent(data.message, columns)

        # Run the agent (main model)
        agent_result = await run_agent(
            question=data.message,
            df=df,
            session_id=session_id,
            intent=intent,
        )

        # Parse chart_data — store as dict if valid JSON
        chart_data_dict = None
        if agent_result.get("chart_json"):
            try:
                chart_data_dict = json.loads(agent_result["chart_json"])
            except (json.JSONDecodeError, TypeError):
                chart_data_dict = None

        # Update session title from first message
        if not session.title:
            title = data.message[:80] + ("..." if len(data.message) > 80 else "")
            repository.update_session_title(db, session_id, title)

        # Save assistant message
        assistant_msg = repository.save_message(
            db=db,
            session_id=session_id,
            role="assistant",
            content=agent_result["text"],
            chart_data=chart_data_dict,
            insight=agent_result.get("insight"),
            recommendation=agent_result.get("recommendation"),
            intent_type=agent_result.get("intent"),
        )

        logger.info(
            f"Message processed: session={session_id} "
            f"intent={intent.value} has_chart={chart_data_dict is not None}"
        )

        return AgentResponse(
            message=ChatMessageResponse.model_validate(assistant_msg),
            session_id=session_id,
        )

    except Exception as e:
        logger.error(f"Message processing failed: {e}", exc_info=True)
        # Save error message so conversation history is complete
        error_msg = repository.save_message(
            db=db,
            session_id=session_id,
            role="assistant",
            content=f"I encountered an error: {str(e)}. Please try again.",
        )
        return AgentResponse(
            message=ChatMessageResponse.model_validate(error_msg),
            session_id=session_id,
        )


def get_sessions(user_id: str, db: Session) -> list:
    return repository.get_sessions_by_user(db, user_id)


def get_session_with_messages(
    session_id: str, user_id: str, db: Session
) -> ChatSessionResponse:
    session = repository.get_session(db, session_id)
    if not session or session.user_id != user_id:
        raise AgentError("Session not found.")
    messages = repository.get_messages_by_session(db, session_id)
    response = ChatSessionResponse.model_validate(session)
    response.messages = [ChatMessageResponse.model_validate(m) for m in messages]
    return response
