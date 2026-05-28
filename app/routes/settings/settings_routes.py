from fastapi import APIRouter, status, Depends, Body
from app.core.security import verify_token
from app.core.response import error_response, success_response
from app.schemas.setting_schema import CreateSettingSchema, UpdateSettingSchema
from app.schemas.user_schema import Role
from app.firebase.firebase_init import db


router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# PUT /settings/save
# Save (or create if missing) the global settings document.
# Only admin-role users can call this.
# ─────────────────────────────────────────────────────────────────────────────
@router.put("/save", status_code=status.HTTP_200_OK)
def saveSettings(
    query: UpdateSettingSchema = Body(default=None),
    current_user: dict = Depends(verify_token)
):
    role = current_user.get("role")

    if role != Role.admin:
        return error_response(message="Only admin can change the settings")

    settings_ref = db.collection("settings").document("global")
    settings_doc = settings_ref.get()

    # ── Document doesn't exist yet → create with defaults + incoming values ──
    if not settings_doc.exists:
        default_settings = CreateSettingSchema().model_dump()

        if query:
            update_data = query.model_dump(exclude_unset=True, exclude_none=True)
            default_settings.update(update_data)

        settings_ref.set(default_settings)

        return success_response(
            message="Settings created and saved successfully",
            data=default_settings
        )

    # ── No body sent → nothing to do ────────────────────────────────────────
    if not query:
        return success_response(message="No changes to save")

    update_data = query.model_dump(exclude_unset=True, exclude_none=True)

    # FIX: was incorrectly returning error_response with a success message
    if not update_data:
        return success_response(message="No changes to save")

    settings_ref.update(update_data)

    return success_response(
        message="Settings updated successfully",
        data=update_data
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /settings
# Return the current global settings.  If the document doesn't exist yet,
# initialise it with schema defaults first.
# Only admin-role users can call this.
# ─────────────────────────────────────────────────────────────────────────────
@router.get("", status_code=status.HTTP_200_OK)
def getSettings(current_user: dict = Depends(verify_token)):

    user_role = current_user.get("role")

    if user_role != Role.admin:
        return error_response(message="Only admin can view settings")

    settings_ref = db.collection("settings").document("global")
    settings_doc = settings_ref.get()

    if not settings_doc.exists:
        default_settings = CreateSettingSchema().model_dump()
        settings_ref.set(default_settings)
        return success_response(
            message="Settings initialised with defaults",
            data=default_settings
        )

    settings_data = settings_doc.to_dict()

    # Guard: ensure holidays is always a list (handles legacy null/missing values)
    if not isinstance(settings_data.get("holidays"), list):
        settings_data["holidays"] = []

    return success_response(
        message="Settings fetched successfully",
        data=settings_data
    )
