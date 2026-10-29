import os, jwt, requests
from functools import lru_cache
from fastapi import APIRouter, HTTPException, Request, Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
clerk_router = APIRouter(prefix="/api")
CLERK_API="https://api.clerk.com/v1"
@clerk_router.get("/clerk/config")
def clerk_config():
    key=os.environ.get("CLERK_PUBLISHABLE_KEY",""); return {"enabled":bool(key and os.environ.get("CLERK_SECRET_KEY")),"publishable_key":key,"proxy_url":""}
@lru_cache(maxsize=1)
def jwks(secret): return jwt.PyJWKClient(f"{CLERK_API}/jwks", headers={"Authorization":f"Bearer {secret}","User-Agent":"morrow-market"}, lifespan=3600)
def verify(token):
    secret=os.environ.get("CLERK_SECRET_KEY","")
    try: return jwt.decode(token, jwks(secret).get_signing_key_from_jwt(token).key, algorithms=["RS256"], leeway=5)
    except jwt.PyJWTError: raise HTTPException(401,"Invalid or expired session")
def require_user(request: Request):
    token=request.headers.get("authorization","")
    if not token.lower().startswith("bearer "): raise HTTPException(401,"Not signed in")
    claims=verify(token[7:]); return {"user_id":claims["sub"],"claims":claims}