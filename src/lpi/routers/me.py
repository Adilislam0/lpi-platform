from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from lpi import store
from lpi.middleware.auth import UserContext, get_current_user_context

router = APIRouter()

# 1. Define the expected payload from the frontend
class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[date] = None
    bio: Optional[str] = None

# 2. Existing GET route
@router.get("/", response_model=UserContext)
def get_me(user_context: UserContext = Depends(get_current_user_context)) -> UserContext:
    """Return the authenticated user's context (including admin status)."""
    return user_context

# 3. New PATCH route for profile updates
@router.patch("/profile", summary="Update user profile")
def update_profile(
    profile_data: ProfileUpdate,
    user_context: UserContext = Depends(get_current_user_context),
):
    """Updates the authenticated user's profile details."""
    # exclude_unset ensures we only update fields the user actually submitted
    updates = profile_data.model_dump(exclude_unset=True)
    
    if "dob" in updates and updates["dob"]:
        updates["dob"] = updates["dob"].isoformat()
        
    if not updates:
        return {"status": "no changes provided"}

    # Use the user_id from the verified JWT context
    updated_user = store.update_user_profile(user_id=user_context.user_id, updates=updates)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile in database."
        )

    return {"status": "success", "profile": updated_user}