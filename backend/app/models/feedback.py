from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.database import Base


class Feedback(Base):
    __tablename__ = "feedback"

    feedback_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    recommendation_id = Column(Integer, ForeignKey("recommendations.recommendation_id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 scale
    comment = Column(Text, nullable=True)
    feedback_type = Column(String, nullable=False)  # "helpful", "not_helpful", "irrelevant", etc.
    created_at = Column(DateTime, default=func.now(), nullable=False)
