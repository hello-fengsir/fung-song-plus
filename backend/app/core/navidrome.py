import httpx
from urllib.parse import urlencode
from fastapi import HTTPException
from app.config import settings

class NavidromeClient:
    def _params(self, **params):
        base = {
            "u": settings.navidrome_user,
            "p": settings.navidrome_password,
            "v": "1.16.1",
            "c": settings.navidrome_client,
            "f": "json",
        }
        for k, v in params.items():
            if v is not None and v != "":
                base[k] = v
        return base

    def url(self, endpoint: str, **params) -> str:
        return f"{settings.navidrome_base.rstrip('/')}/rest/{endpoint}?{urlencode(self._params(**params))}"

    async def call(self, endpoint: str, **params) -> dict:
        url = self.url(endpoint, **params)
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
        sr = data.get("subsonic-response", {})
        if sr.get("status") != "ok":
            detail = sr.get("error", {}).get("message") or "Navidrome API error"
            raise HTTPException(status_code=502, detail=detail)
        return sr

navidrome = NavidromeClient()
