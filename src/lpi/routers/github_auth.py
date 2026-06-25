import os

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

load_dotenv()

router = APIRouter()

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

# --- Pydantic Models for Request Validation ---


class TokenExchangeRequest(BaseModel):
    code: str
    user_id: str


class FetchRepoRequest(BaseModel):
    user_id: str
    repo_owner: str
    repo_name: str


class TrackRepoRequest(BaseModel):
    user_id: str
    repo_owner: str
    repo_name: str


# ADDED: New model for the disconnect request
class DisconnectRepoRequest(BaseModel):
    user_id: str
    repo_owner: str
    repo_name: str


# --- Mock Database ---
# In production, this saves to your database table: user_id -> github_access_token
token_db: dict[str, str] = {}

# Reverse mapping: "owner/repo" -> user_id, populated when a webhook is registered.
repo_db: dict[str, str] = {}

# --- Configuration ---
# Your webhook receiver URL.
WEBHOOK_TARGET_URL = "https://balance-suburb-singular.ngrok-free.dev/api/v1/webhooks/github"


# --- Endpoints ---


@router.post("/exchange-token", status_code=status.HTTP_200_OK)
async def exchange_github_token(request: TokenExchangeRequest):
    """
    1. The frontend passes the temporary 'code' here.
    2. We trade it using our application's secret keys.
    3. We securely save the resulting access token for this specific user.
    """
    url = "https://github.com/login/oauth/access_token"
    payload = {
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": request.code,
    }
    headers = {"Accept": "application/json"}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        data = response.json()

    if "error" in data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=data.get("error_description", "Authentication failed"),
        )

    access_token = data.get("access_token")

    # Securely save this token tied to the user's profile
    token_db[request.user_id] = access_token

    return {"status": "success", "message": "GitHub account linked securely!"}


@router.get("/user-repositories/{user_id}", status_code=status.HTTP_200_OK)
async def list_user_repositories(user_id: str):
    """
    Dynamically fetches all repositories (including private ones)
    that this specific user owns, so the frontend can populate a selection dropdown.
    """
    access_token = token_db.get(user_id)
    if not access_token:
        raise HTTPException(status_code=404, detail="User has not connected their GitHub account.")

    url = "https://api.github.com/user/repos?per_page=100&sort=updated"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "LPI-Platform-Backend",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="Failed to fetch repositories from GitHub."
        )

    repos = response.json()

    repo_list = [
        {
            "id": repo["id"],
            "name": repo["name"],
            "full_name": repo["full_name"],
            "private": repo["private"],
            "owner": repo["owner"]["login"],
            "html_url": repo["html_url"],
            "permissions": repo.get("permissions", {}),
        }
        for repo in repos
    ]

    return {"repositories": repo_list}


@router.post("/track-repo", status_code=status.HTTP_200_OK)
async def auto_register_webhook(request: TrackRepoRequest):
    """
    The frontend hits this when the user selects a specific repo from the dropdown.
    We use their saved token to automatically attach our webhook to that exact repo.
    """
    access_token = token_db.get(request.user_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="No GitHub account linked.")

    url = f"https://api.github.com/repos/{request.repo_owner}/{request.repo_name}/hooks"

    payload = {
        "name": "web",
        "active": True,
        "events": ["push", "pull_request", "pull_request_review"],
        "config": {"url": WEBHOOK_TARGET_URL, "content_type": "json"},
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)

    if response.status_code not in [200, 201]:
        if response.status_code == 422:
            repo_db[f"{request.repo_owner}/{request.repo_name}"] = request.user_id
            return {"status": "success", "message": "Webhook already tracking this repo!"}
        raise HTTPException(status_code=response.status_code, detail="Failed to register webhook.")

    repo_db[f"{request.repo_owner}/{request.repo_name}"] = request.user_id
    return {"status": "success", "message": f"Successfully tracking {request.repo_name}!"}


# ADDED: The new Disconnect Endpoint
@router.post("/disconnect-repo", status_code=status.HTTP_200_OK)
async def disconnect_github(request: DisconnectRepoRequest):
    """
    Finds our specific webhook on the user's GitHub repo, deletes it, 
    and removes their access token from the local database.
    """
    access_token = token_db.get(request.user_id)
    if not access_token:
        raise HTTPException(status_code=404, detail="No GitHub account linked.")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    async with httpx.AsyncClient() as client:
        # Step 1: List all webhooks for this repo to find ours
        hooks_url = f"https://api.github.com/repos/{request.repo_owner}/{request.repo_name}/hooks"
        hooks_response = await client.get(hooks_url, headers=headers)

        if hooks_response.status_code == 200:
            hooks = hooks_response.json()
            target_hook_id = None

            # Find the webhook that points to our WEBHOOK_TARGET_URL
            for hook in hooks:
                if hook.get("config", {}).get("url") == WEBHOOK_TARGET_URL:
                    target_hook_id = hook["id"]
                    break

            # Step 2: Delete the webhook if we found it
            if target_hook_id:
                delete_url = f"{hooks_url}/{target_hook_id}"
                await client.delete(delete_url, headers=headers)

    # Step 3: Remove the token and repo mapping from our local mock DB
    if request.user_id in token_db:
        del token_db[request.user_id]
    repo_db.pop(f"{request.repo_owner}/{request.repo_name}", None)

    return {"status": "success", "message": f"Successfully disconnected from {request.repo_name}."}


@router.post("/disconnect-account/{user_id}", status_code=status.HTTP_200_OK)
async def disconnect_github_account(user_id: str):
    """
    Clears the stored GitHub oauth access token for this specific user ID,
    disconnecting their entire account profile integration.
    """
    if user_id in token_db:
        del token_db[user_id]
        return {"status": "success", "message": "Successfully disconnected your GitHub account."}
    raise HTTPException(status_code=404, detail="No GitHub account linked.")

