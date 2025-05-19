from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.tradier_service import get_tradier_quote, get_tradier_chains, submit_tradier_order

router = APIRouter(prefix="/tradier", tags=["tradier"])

@router.get("/quote/{symbol}")
async def quote(symbol: str):
    try:
        return get_tradier_quote(symbol.upper())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/chains/{symbol}")
async def chains(symbol: str, expiration: str = None):
    try:
        return get_tradier_chains(symbol.upper(), expiration)
    except Exception as e:
        raise HTTPException(400, str(e))

class TradierOrder(BaseModel):
    account_id: str
    symbol:     str
    qty:        int
    side:       str

@router.post("/order")
async def order(req: TradierOrder):
    try:
        return submit_tradier_order(req.account_id, req.symbol, req.qty, req.side)
    except Exception as e:
        raise HTTPException(400, str(e)) 