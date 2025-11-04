from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Signal(Base):
    __tablename__ = "signals"

    signal_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    signal_type = Column(String, nullable=False, index=True)
    value = Column(Float, nullable=False)
    details = Column(JSON)
    computed_at = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="signals")

    def __repr__(self):
        return f"<Signal {self.signal_type}: {self.value}>"
