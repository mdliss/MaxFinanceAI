from sqlalchemy import Column, String, Float, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Liability(Base):
    __tablename__ = "liabilities"

    liability_id = Column(String, primary_key=True, index=True)
    account_id = Column(String, ForeignKey("accounts.account_id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    type = Column(String, nullable=False)
    apr_percentage = Column(Float)
    apr_type = Column(String)
    minimum_payment_amount = Column(Float)
    last_payment_amount = Column(Float)
    is_overdue = Column(Boolean, default=False)
    next_payment_due_date = Column(Date)
    last_statement_balance = Column(Float)
    interest_rate = Column(Float)

    # Relationships
    account = relationship("Account", back_populates="liabilities")
    user = relationship("User", back_populates="liabilities")

    def __repr__(self):
        return f"<Liability {self.liability_id}: {self.type}>"
