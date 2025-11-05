from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import Account, User
from pydantic import BaseModel

router = APIRouter(prefix="/accounts", tags=["accounts"])


class AccountResponse(BaseModel):
    account_id: str
    user_id: str
    type: str
    subtype: Optional[str] = None
    available_balance: Optional[float] = None
    current_balance: Optional[float] = None
    credit_limit: Optional[float] = None
    iso_currency_code: str = "USD"
    holder_category: Optional[str] = None
    utilization: Optional[float] = None  # Calculated for credit accounts

    class Config:
        from_attributes = True


class CreditUtilizationResponse(BaseModel):
    total_balance: float
    total_limit: float
    utilization_percentage: float
    accounts: List[AccountResponse]


@router.get("/{user_id}", response_model=List[AccountResponse])
async def get_user_accounts(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all accounts for a user.

    Returns all account types including:
    - Checking accounts
    - Savings accounts
    - Credit cards
    - Money market accounts
    - HSA accounts
    """
    # Check if user exists
    result = await db.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get all accounts
    result = await db.execute(
        select(Account).where(Account.user_id == user_id)
    )
    accounts = result.scalars().all()

    # Calculate utilization for credit accounts
    response_accounts = []
    for account in accounts:
        account_dict = {
            "account_id": account.account_id,
            "user_id": account.user_id,
            "type": account.type,
            "subtype": account.subtype,
            "available_balance": account.available_balance,
            "current_balance": account.current_balance,
            "credit_limit": account.credit_limit,
            "iso_currency_code": account.iso_currency_code,
            "holder_category": account.holder_category,
        }

        # Calculate utilization for credit cards
        if account.type == "credit" and account.credit_limit and account.credit_limit > 0:
            account_dict["utilization"] = (account.current_balance / account.credit_limit) * 100

        response_accounts.append(AccountResponse(**account_dict))

    return response_accounts


@router.get("/{user_id}/credit-utilization", response_model=CreditUtilizationResponse)
async def get_credit_utilization(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get credit utilization summary for a user.

    Calculates:
    - Total balance across all credit cards
    - Total credit limit
    - Overall utilization percentage
    """
    # Check if user exists
    result = await db.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get all credit accounts
    result = await db.execute(
        select(Account).where(
            Account.user_id == user_id,
            Account.type == "credit"
        )
    )
    credit_accounts = result.scalars().all()

    if not credit_accounts:
        return CreditUtilizationResponse(
            total_balance=0.0,
            total_limit=0.0,
            utilization_percentage=0.0,
            accounts=[]
        )

    total_balance = sum(acc.current_balance or 0 for acc in credit_accounts)
    total_limit = sum(acc.credit_limit or 0 for acc in credit_accounts)

    utilization_percentage = 0.0
    if total_limit > 0:
        utilization_percentage = (total_balance / total_limit) * 100

    # Format accounts with utilization
    response_accounts = []
    for account in credit_accounts:
        account_dict = {
            "account_id": account.account_id,
            "user_id": account.user_id,
            "type": account.type,
            "subtype": account.subtype,
            "available_balance": account.available_balance,
            "current_balance": account.current_balance,
            "credit_limit": account.credit_limit,
            "iso_currency_code": account.iso_currency_code,
            "holder_category": account.holder_category,
        }

        if account.credit_limit and account.credit_limit > 0:
            account_dict["utilization"] = (account.current_balance / account.credit_limit) * 100

        response_accounts.append(AccountResponse(**account_dict))

    return CreditUtilizationResponse(
        total_balance=total_balance,
        total_limit=total_limit,
        utilization_percentage=round(utilization_percentage, 2),
        accounts=response_accounts
    )
