from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ChatMessage(Base):
    """Chat message model for storing conversation history."""
    __tablename__ = "chat_messages"

    message_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    conversation_id = Column(String(36), nullable=False, index=True)  # UUID string
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    model_used = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="chat_messages")
    feedback = relationship("ChatFeedback", back_populates="message", uselist=False, cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            role.in_(['user', 'assistant', 'system']),
            name='valid_role'
        ),
    )

    def __repr__(self):
        return f"<ChatMessage {self.message_id}: {self.role} in {self.conversation_id}>"

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "message_id": self.message_id,
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "tokens_used": self.tokens_used,
            "response_time_ms": self.response_time_ms,
            "model_used": self.model_used,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ChatFeedback(Base):
    """User feedback on chat responses."""
    __tablename__ = "chat_feedback"

    feedback_id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey("chat_messages.message_id"), nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    feedback_text = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    message = relationship("ChatMessage", back_populates="feedback")
    user = relationship("User", back_populates="chat_feedback")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            'rating BETWEEN 1 AND 5',
            name='valid_rating'
        ),
    )

    def __repr__(self):
        return f"<ChatFeedback {self.feedback_id}: {self.rating} stars for message {self.message_id}>"

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "feedback_id": self.feedback_id,
            "message_id": self.message_id,
            "user_id": self.user_id,
            "rating": self.rating,
            "feedback_text": self.feedback_text,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
