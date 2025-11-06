from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
from datetime import datetime

from app.database import get_db
from app.models import User, ChatMessage, ChatFeedback
from app.services.llm import get_llm_service
from app.services.chat import ContextBuilder, SYSTEM_PROMPT_V1, build_user_message


router = APIRouter(prefix="/chat", tags=["chat"])


# Pydantic models for request/response
class ChatRequest(BaseModel):
    user_id: str
    message: str = Field(..., min_length=1, max_length=500, description="User's message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID (optional, will create new if not provided)")


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: int
    response: str
    tokens_used: int
    response_time_ms: int
    model: str
    timestamp: str


class FeedbackRequest(BaseModel):
    message_id: int
    user_id: str
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    feedback_text: Optional[str] = Field(None, max_length=1000)


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """Send a message to the financial chatbot and get AI response.

    This endpoint:
    1. Validates the user exists and has given consent
    2. Builds financial context from user's actual data
    3. Sends the message to the LLM (Claude) with context
    4. Saves both user and assistant messages to database
    5. Returns the AI response

    Args:
        request: ChatRequest with user_id, message, and optional conversation_id

    Returns:
        ChatResponse with AI response and metadata

    Raises:
        404: User not found
        403: User has not provided consent
        500: LLM API error or other server error
    """
    # 1. Validate user exists and has consent
    result = await db.execute(
        select(User).where(User.user_id == request.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {request.user_id} not found"
        )

    if not user.consent_status:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has not provided consent for AI features. Please accept the terms first."
        )

    # 2. Generate or use existing conversation_id
    conversation_id = request.conversation_id or str(uuid.uuid4())

    # 3. Save user message to database
    user_message = ChatMessage(
        user_id=request.user_id,
        conversation_id=conversation_id,
        role="user",
        content=request.message,
        created_at=datetime.utcnow()
    )
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)

    try:
        # 4. Build financial context
        context_builder = ContextBuilder(db)
        context = await context_builder.build_context(request.user_id, max_tokens=6000)

        # 5. Get conversation history (last 5 messages for context)
        history_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .where(ChatMessage.message_id != user_message.message_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(5)
        )
        history = list(reversed(history_result.scalars().all()))

        # Format history for LLM
        history_formatted = [
            {"role": msg.role, "content": msg.content}
            for msg in history
            if msg.role in ["user", "assistant"]  # Skip system messages
        ]

        # 6. Build user message with context
        user_message_with_context = build_user_message(context, request.message)

        # 7. Get LLM response
        llm = get_llm_service()
        llm_response = await llm.send_message(
            system_prompt=SYSTEM_PROMPT_V1,
            user_message=user_message_with_context,
            conversation_history=history_formatted,
            max_tokens=1024,
            temperature=0.7
        )

        # 8. Save assistant response to database
        assistant_message = ChatMessage(
            user_id=request.user_id,
            conversation_id=conversation_id,
            role="assistant",
            content=llm_response["content"],
            tokens_used=llm_response["tokens_used"],
            response_time_ms=llm_response["response_time_ms"],
            model_used=llm_response["model"],
            created_at=datetime.utcnow()
        )
        db.add(assistant_message)
        await db.commit()
        await db.refresh(assistant_message)

        # 9. Return response
        return ChatResponse(
            conversation_id=conversation_id,
            message_id=assistant_message.message_id,
            response=llm_response["content"],
            tokens_used=llm_response["tokens_used"],
            response_time_ms=llm_response["response_time_ms"],
            model=llm_response["model"],
            timestamp=assistant_message.created_at.isoformat()
        )

    except ValueError as e:
        # LLM configuration error (missing API key, etc.)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration error: {str(e)}"
        )

    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Chat error for user {request.user_id}: {str(e)}")

        # Return user-friendly error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="I'm experiencing technical difficulties. Please try again in a moment."
        )


@router.get("/history/{user_id}")
async def get_conversation_history(
    user_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum messages to return"),
    conversation_id: Optional[str] = Query(None, description="Filter by conversation ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation history for a user.

    Returns messages grouped by conversation, with most recent first.

    Args:
        user_id: User ID
        limit: Maximum messages to return (default 50, max 100)
        conversation_id: Optional filter by specific conversation

    Returns:
        Dictionary with conversations and messages
    """
    # Build query
    query = select(ChatMessage).where(ChatMessage.user_id == user_id)

    if conversation_id:
        query = query.where(ChatMessage.conversation_id == conversation_id)

    query = query.order_by(desc(ChatMessage.created_at)).limit(limit)

    # Execute query
    result = await db.execute(query)
    messages = result.scalars().all()

    # Group messages by conversation
    conversations = {}
    for msg in messages:
        conv_id = msg.conversation_id
        if conv_id not in conversations:
            conversations[conv_id] = {
                "conversation_id": conv_id,
                "started_at": msg.created_at.isoformat(),
                "last_message_at": msg.created_at.isoformat(),
                "message_count": 0,
                "messages": []
            }

        conversations[conv_id]["messages"].append(msg.to_dict())
        conversations[conv_id]["message_count"] += 1

        # Update timestamps
        msg_time = msg.created_at
        if msg_time < datetime.fromisoformat(conversations[conv_id]["started_at"].replace("Z", "+00:00")):
            conversations[conv_id]["started_at"] = msg.created_at.isoformat()
        if msg_time > datetime.fromisoformat(conversations[conv_id]["last_message_at"].replace("Z", "+00:00")):
            conversations[conv_id]["last_message_at"] = msg.created_at.isoformat()

    return {
        "user_id": user_id,
        "conversations": list(conversations.values()),
        "total_conversations": len(conversations)
    }


@router.delete("/history/{user_id}")
async def delete_conversation_history(
    user_id: str,
    conversation_id: Optional[str] = Query(None, description="Delete specific conversation (optional)"),
    confirm: bool = Query(False, description="Must be true to confirm deletion"),
    db: AsyncSession = Depends(get_db)
):
    """Delete conversation history for a user.

    Requires confirm=true parameter to prevent accidental deletion.

    Args:
        user_id: User ID
        conversation_id: Optional - delete specific conversation only
        confirm: Must be true to confirm deletion

    Returns:
        Count of deleted messages
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must pass confirm=true to delete conversation history"
        )

    # Build delete query
    query = select(ChatMessage).where(ChatMessage.user_id == user_id)

    if conversation_id:
        query = query.where(ChatMessage.conversation_id == conversation_id)

    # Get messages to delete
    result = await db.execute(query)
    messages = result.scalars().all()
    count = len(messages)

    # Delete messages (this will cascade to feedback via relationship)
    for msg in messages:
        await db.delete(msg)

    await db.commit()

    return {
        "deleted_count": count,
        "user_id": user_id,
        "conversation_id": conversation_id,
        "message": f"Deleted {count} message(s)"
    }


@router.post("/feedback", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """Submit feedback (rating) for a chat message.

    Users can rate assistant messages from 1-5 stars with optional text feedback.

    Args:
        request: FeedbackRequest with message_id, user_id, rating, and optional text

    Returns:
        Created feedback object

    Raises:
        404: Message not found
        400: Duplicate feedback (user already rated this message)
    """
    # Verify message exists
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.message_id == request.message_id)
    )
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message {request.message_id} not found"
        )

    # Check for duplicate feedback
    result = await db.execute(
        select(ChatFeedback)
        .where(ChatFeedback.message_id == request.message_id)
        .where(ChatFeedback.user_id == request.user_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already provided feedback for this message"
        )

    # Create feedback
    feedback = ChatFeedback(
        message_id=request.message_id,
        user_id=request.user_id,
        rating=request.rating,
        feedback_text=request.feedback_text,
        created_at=datetime.utcnow()
    )

    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)

    return {
        "feedback_id": feedback.feedback_id,
        "message": "Thank you for your feedback!",
        "rating": feedback.rating
    }
