from fastapi import Header, HTTPException
import os

CLIENT_KEY = os.getenv("CLIENT_KEY")  # optional small client key to reduce casual abuse

async def verify_client_key(x_client_key: str = Header(None)):
    """If CLIENT_KEY is set on the server, require the header x-client-key to match it.
    If CLIENT_KEY is not set, allow requests (useful for local dev)."""
    if CLIENT_KEY is None:
        return True
    if not x_client_key or x_client_key != CLIENT_KEY:
        raise HTTPException(status_code=401, detail="Invalid client key") 
    return True
