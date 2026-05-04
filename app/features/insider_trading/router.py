from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from core.database import get_session
from features.insider_trading.models import InsiderTrade
from typing import List

router = APIRouter(prefix="/api/insider-trades", tags=["insider_trading"])

@router.get("/", response_model=List[InsiderTrade])
def get_all_insider_trades(session: Session = Depends(get_session)):
    """
    Returns all insider trading data records.
    """
    trades = session.exec(select(InsiderTrade)).all()
    return trades
