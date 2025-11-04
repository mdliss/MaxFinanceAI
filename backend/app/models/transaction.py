from sqlalchemy import Column, String, Float, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String, primary_key=True, index=True)
    account_id = Column(String, ForeignKey("accounts.account_id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    merchant_name = Column(String)
    merchant_entity_id = Column(String)
    payment_channel = Column(String)
    category_primary = Column(String)
    category_detailed = Column(String)
    pending = Column(Boolean, default=False)

    # Relationships
    account = relationship("Account", back_populates="transactions")
    user = relationship("User", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction {self.transaction_id}: {self.amount} on {self.date}>"
