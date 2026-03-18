"""
Job queue routes — submit async generation jobs and poll for status/results.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.utils.auth import decode_access_token
from app.utils.niches import detect_niche
from app.utils.redis_client import create_job, get_job, get_user_jobs

router = APIRouter()
security = HTTPBearer()


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token_data = decode_access_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return token_data


class SubmitJobRequest(BaseModel):
    prompt: str
    niche: str | None = None
    designSystem: dict | None = None
    sessionId: str | None = None


@router.post("/submit")
async def submit_job(req: SubmitJobRequest, user: dict = Depends(require_auth)):
    """Submit a website generation job to the background queue."""
    niche_key = req.niche or detect_niche(req.prompt)

    payload = {
        "prompt": req.prompt,
        "niche": niche_key,
        "designSystem": req.designSystem,
        "sessionId": req.sessionId,
        "user_id": user["user_id"],
    }

    try:
        job_id = await create_job("generate", payload, str(user["user_id"]))
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    return {
        "jobId": job_id,
        "status": "pending",
        "message": "Job submitted. Poll /api/jobs/{jobId} for status.",
    }


@router.get("/{job_id}")
async def get_job_status(job_id: str, user: dict = Depends(require_auth)):
    """Get the current status and result of a job."""
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Only allow the owner to see their job
    if str(job.get("user_id")) != str(user["user_id"]):
        raise HTTPException(status_code=403, detail="Not your job")

    response = {
        "jobId": job_id,
        "status": job["status"],
        "progress": job.get("progress", 0),
        "progressMessage": job.get("progress_message", ""),
        "createdAt": job.get("created_at"),
    }

    if job["status"] == "completed" and job.get("result"):
        result = job["result"]
        # Store in generator sessions so section/component editing works
        if isinstance(result, dict) and result.get("success"):
            await _store_in_sessions(job_id, result, str(user["user_id"]))
        response["result"] = result
        response["sessionId"] = job_id  # Use job_id as session_id

    if job["status"] == "failed":
        response["error"] = job.get("error", "Unknown error")

    return response


@router.get("/")
async def list_jobs(user: dict = Depends(require_auth)):
    """List recent jobs for the authenticated user."""
    jobs = await get_user_jobs(str(user["user_id"]))
    return {
        "jobs": [
            {
                "jobId": j.get("id", ""),
                "status": j.get("status", ""),
                "type": j.get("type", ""),
                "progress": float(j.get("progress", 0)),
                "progressMessage": j.get("progress_message", ""),
                "createdAt": j.get("created_at"),
            }
            for j in jobs
        ]
    }


@router.delete("/{job_id}")
async def cancel_job(job_id: str, user: dict = Depends(require_auth)):
    """Cancel a pending job (removes from queue, marks as failed)."""
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if str(job.get("user_id")) != str(user["user_id"]):
        raise HTTPException(status_code=403, detail="Not your job")

    if job["status"] == "pending":
        from app.utils.redis_client import update_job

        await update_job(job_id, status="failed", error="Cancelled by user", progress_message="Cancelled")
        return {"success": True, "message": "Job cancelled"}

    return {"success": False, "message": f"Cannot cancel job in '{job['status']}' state"}


async def _store_in_sessions(job_id: str, result: dict, user_id: str):
    """Store job result in Redis session for section/component editing."""
    try:
        from app.utils.session_store import save_session as redis_save_session

        website = result.get("website", {})
        await redis_save_session(
            job_id,
            {
                "html": website.get("html", ""),
                "css": website.get("css", ""),
                "js": website.get("js", ""),
                "niche": result.get("niche"),
                "design_system": result.get("designSystem"),
                "prompts": [result.get("prompt", "")],
                "versions": [],
                "current_version": 1,
                "user_id": user_id,
            },
        )
    except Exception:
        pass
