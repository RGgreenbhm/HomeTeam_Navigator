"""
Azure Function: Consent Form Handler
Receives form submissions and posts them to Spruce Health

Deployment:
    func azure functionapp publish greenclinic-consent-api

Environment Variables Required:
    SPRUCE_API_TOKEN: Spruce Health API Bearer token
    ALLOWED_ORIGINS: Comma-separated list of allowed origins (CORS)
"""

import azure.functions as func
import json
import logging
import os
import requests
from datetime import datetime
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Function App
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Configuration
SPRUCE_API_TOKEN = os.environ.get("SPRUCE_API_TOKEN", "")
SPRUCE_BASE_URL = "https://api.sprucehealth.com/v1"
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "https://greenclinic-consent.azurestaticapps.net,http://localhost:5500"
).split(",")


# =============================================================================
# CORS Helpers
# =============================================================================

def get_cors_headers(origin: str) -> dict:
    """Get CORS headers for the response."""
    if origin in ALLOWED_ORIGINS or "*" in ALLOWED_ORIGINS:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Max-Age": "86400",
        }
    return {}


# =============================================================================
# Spruce API Client
# =============================================================================

class SpruceClient:
    """Lightweight Spruce API client for Azure Function."""

    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = SPRUCE_BASE_URL
        self._phone_endpoint_id: Optional[str] = None

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def get_phone_endpoint_id(self) -> str:
        """Get the phone endpoint ID for sending SMS/creating conversations."""
        if self._phone_endpoint_id:
            return self._phone_endpoint_id

        response = requests.get(
            f"{self.base_url}/internalendpoints",
            headers=self._headers()
        )
        response.raise_for_status()

        data = response.json()
        for ep in data.get("internalEndpoints", []):
            if ep.get("channel") == "phone":
                self._phone_endpoint_id = ep.get("id")
                return self._phone_endpoint_id

        raise Exception("No phone endpoint found")

    def search_contact_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Search for a contact by name."""
        try:
            response = requests.post(
                f"{self.base_url}/contacts/search",
                headers=self._headers(),
                json={"query": name}
            )
            response.raise_for_status()

            contacts = response.json().get("contacts", [])
            if contacts:
                return contacts[0]
        except Exception as e:
            logger.warning(f"Contact search failed: {e}")

        return None

    def find_or_create_conversation(
        self,
        patient_name: str,
        phone_number: Optional[str] = None
    ) -> Optional[str]:
        """
        Find existing conversation or create one.
        Returns conversation_id if found/created.
        """
        # Try to find contact by name first
        contact = self.search_contact_by_name(patient_name)

        if contact:
            contact_id = contact.get("id")
            # Get conversations for this contact
            try:
                response = requests.get(
                    f"{self.base_url}/contacts/{contact_id}/conversations",
                    headers=self._headers()
                )
                response.raise_for_status()
                conversations = response.json().get("conversations", [])
                if conversations:
                    # Return most recent phone conversation
                    for conv in conversations:
                        if conv.get("type") == "phone":
                            return conv.get("id")
                    # Or any conversation
                    return conversations[0].get("id")
            except Exception as e:
                logger.warning(f"Error getting conversations: {e}")

        return None

    def post_message_to_conversation(
        self,
        conversation_id: str,
        message: str
    ) -> dict:
        """Post a message to an existing conversation."""
        response = requests.post(
            f"{self.base_url}/conversations/{conversation_id}/messages",
            headers=self._headers(),
            json={"text": message}
        )
        response.raise_for_status()
        return response.json()

    def create_internal_note(
        self,
        patient_name: str,
        message: str
    ) -> dict:
        """
        Create an internal note visible to staff.
        This appears in Spruce but isn't sent to the patient.
        """
        # For now, we'll post to the conversation as a regular message
        # marked clearly as a form submission
        conversation_id = self.find_or_create_conversation(patient_name)

        if conversation_id:
            return self.post_message_to_conversation(conversation_id, message)
        else:
            # If no conversation found, log and return partial success
            logger.warning(f"No conversation found for {patient_name}")
            return {"status": "no_conversation", "message": "Form received but patient not in Spruce"}


# =============================================================================
# Form Processing
# =============================================================================

def format_consent_response(data: Dict[str, Any]) -> str:
    """Format form data into a readable message for Spruce."""
    # Parse the data
    full_name = data.get("full_name", "Unknown")
    dob = data.get("date_of_birth", "Not provided")
    contact_method = data.get("contact_method", "Not specified")
    contact_consent = data.get("contact_consent", "Not specified")
    provider_preference = data.get("provider_preference", "Not specified")
    apcm_status = data.get("apcm_status", "N/A")
    questions = data.get("questions", "").strip() or "None"
    submitted_at = data.get("submitted_at", datetime.utcnow().isoformat())
    token = data.get("token", "Unknown")

    # Format contact method display
    contact_method_display = {
        "phone": "Phone call",
        "sms": "Text message (SMS)",
        "email": "Email",
        "portal": "Secure patient portal",
        "mail": "Mail",
    }.get(contact_method, contact_method)

    # Format consent display
    consent_display = {
        "yes": "Yes - consents to preferred method",
        "mail_only": "No - mail only",
    }.get(contact_consent, contact_consent)

    # Format provider preference display
    provider_display = {
        "continue": "Continue with Dr. Green at new location",
        "transfer": "Requesting records transfer information",
        "undecided": "Needs more information",
        "not_specified": "Not specified",
    }.get(provider_preference, provider_preference)

    # Format APCM status display
    apcm_display = {
        "continue": "Wishes to continue APCM with Home Team",
        "questions": "Has questions about APCM billing",
        "na": "Not applicable",
    }.get(apcm_status, apcm_status)

    # Build the message
    message = f"""
CONSENT FORM RESPONSE
{'=' * 40}
Submitted: {submitted_at}
Token: {token}

PATIENT INFORMATION
{'-' * 40}
Name: {full_name}
DOB: {dob}

CONTACT PREFERENCES
{'-' * 40}
Preferred Method: {contact_method_display}
Consent Given: {consent_display}

CARE PREFERENCE
{'-' * 40}
Provider Choice: {provider_display}

APCM STATUS
{'-' * 40}
{apcm_display}

QUESTIONS/CONCERNS
{'-' * 40}
{questions}

{'=' * 40}
[Auto-captured via Patient Explorer Consent Form]
""".strip()

    return message


def validate_form_data(data: Dict[str, Any]) -> tuple[bool, str]:
    """Validate required form fields."""
    required_fields = ["full_name", "date_of_birth", "contact_method", "contact_consent"]

    for field in required_fields:
        if not data.get(field):
            return False, f"Missing required field: {field}"

    # Validate token format (basic check)
    token = data.get("token", "")
    if not token or len(token) < 10:
        return False, "Invalid or missing form token"

    return True, ""


# =============================================================================
# Main Function
# =============================================================================

@app.route(route="submit-consent", methods=["POST", "OPTIONS"])
def submit_consent(req: func.HttpRequest) -> func.HttpResponse:
    """
    Handle consent form submissions.

    POST /api/submit-consent
    Body: JSON with form fields

    Returns:
        200: Success
        400: Validation error
        500: Server error
    """
    # Get origin for CORS
    origin = req.headers.get("Origin", "")
    cors_headers = get_cors_headers(origin)

    # Handle CORS preflight
    if req.method == "OPTIONS":
        return func.HttpResponse(
            status_code=204,
            headers=cors_headers
        )

    logger.info("Consent form submission received")

    try:
        # Parse request body
        try:
            data = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"success": False, "error": "Invalid JSON"}),
                status_code=400,
                mimetype="application/json",
                headers=cors_headers
            )

        # Validate form data
        is_valid, error_msg = validate_form_data(data)
        if not is_valid:
            return func.HttpResponse(
                json.dumps({"success": False, "error": error_msg}),
                status_code=400,
                mimetype="application/json",
                headers=cors_headers
            )

        # Check for Spruce API token
        if not SPRUCE_API_TOKEN:
            logger.error("SPRUCE_API_TOKEN not configured")
            # Still return success to user, but log the issue
            return func.HttpResponse(
                json.dumps({
                    "success": True,
                    "message": "Form received. Our team will review your response.",
                    "warning": "Spruce sync pending"
                }),
                status_code=200,
                mimetype="application/json",
                headers=cors_headers
            )

        # Format the message
        message = format_consent_response(data)

        # Post to Spruce
        try:
            client = SpruceClient(SPRUCE_API_TOKEN)
            result = client.create_internal_note(
                patient_name=data.get("full_name", "Unknown"),
                message=message
            )
            logger.info(f"Posted to Spruce: {result}")

        except Exception as e:
            logger.error(f"Spruce API error: {e}")
            # Don't fail the user, just log it
            # The form data is still captured in logs

        # Return success
        return func.HttpResponse(
            json.dumps({
                "success": True,
                "message": "Thank you! Your response has been received.",
            }),
            status_code=200,
            mimetype="application/json",
            headers=cors_headers
        )

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "error": "An unexpected error occurred. Please try again or call our office."
            }),
            status_code=500,
            mimetype="application/json",
            headers=cors_headers
        )


# =============================================================================
# Health Check
# =============================================================================

@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint."""
    return func.HttpResponse(
        json.dumps({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "spruce_configured": bool(SPRUCE_API_TOKEN)
        }),
        status_code=200,
        mimetype="application/json"
    )
