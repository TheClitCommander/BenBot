import os, requests

TOKEN = os.getenv("TRADIER_TOKEN")
BASE  = os.getenv("TRADIER_BASE_URL")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept":        "application/json",
}

def get_tradier_quote(symbol: str) -> dict:
    r = requests.get(
        f"{BASE}/markets/quotes",
        params={"symbols": symbol},
        headers=HEADERS
    )
    r.raise_for_status()
    return r.json()["quotes"]["quote"]

def get_tradier_chains(symbol: str, expiration: str = None) -> dict:
    params = {"symbol": symbol}
    if expiration:
        params["expiration"] = expiration
    r = requests.get(f"{BASE}/markets/options/chains", params=params, headers=HEADERS)
    r.raise_for_status()
    return r.json()

def submit_tradier_order(account_id: str, symbol: str, qty: int, side: str):
    payload = {
        "class":      "equity",
        "symbol":     symbol,
        "side":       side,
        "quantity":   qty,
        "type":       "market",
        "duration":   "day",
        "account_id": account_id,
    }
    r = requests.post(f"{BASE}/accounts/{account_id}/orders", data=payload, headers=HEADERS)
    r.raise_for_status()
    return r.json() 