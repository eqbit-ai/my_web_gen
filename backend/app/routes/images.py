"""
Image search routes — Unsplash + Pexels API for real stock photos.
Used by the generator to embed high-quality images in websites.
"""

import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.utils.auth import decode_access_token

router = APIRouter()
security = HTTPBearer()


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token_data = decode_access_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return token_data


@router.get("/search")
async def search_images(
    q: str = Query(..., min_length=1),
    count: int = Query(default=10, ge=1, le=30),
    user: dict = Depends(require_auth),
):
    """Search for images across Unsplash and Pexels. Returns unified results."""
    unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY")
    pexels_key = os.getenv("PEXELS_API_KEY")

    results = []

    async with httpx.AsyncClient(timeout=10) as client:
        # Unsplash
        if unsplash_key:
            try:
                resp = await client.get(
                    "https://api.unsplash.com/search/photos",
                    params={"query": q, "per_page": count, "orientation": "landscape"},
                    headers={"Authorization": f"Client-ID {unsplash_key}"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for photo in data.get("results", []):
                        results.append(
                            {
                                "id": photo["id"],
                                "source": "unsplash",
                                "url": photo["urls"]["regular"],
                                "thumb": photo["urls"]["small"],
                                "alt": photo.get("alt_description", q),
                                "photographer": photo["user"]["name"],
                                "width": photo["width"],
                                "height": photo["height"],
                            }
                        )
            except Exception:
                pass

        # Pexels
        if pexels_key:
            try:
                resp = await client.get(
                    "https://api.pexels.com/v1/search",
                    params={"query": q, "per_page": count, "orientation": "landscape"},
                    headers={"Authorization": pexels_key},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for photo in data.get("photos", []):
                        results.append(
                            {
                                "id": str(photo["id"]),
                                "source": "pexels",
                                "url": photo["src"]["large"],
                                "thumb": photo["src"]["medium"],
                                "alt": photo.get("alt", q),
                                "photographer": photo["photographer"],
                                "width": photo["width"],
                                "height": photo["height"],
                            }
                        )
            except Exception:
                pass

    return {"images": results, "query": q}
