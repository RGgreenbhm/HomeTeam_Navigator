"""
Spruce Response Sync Module

Pulls consent form responses from Spruce conversations and updates the local database.
This module syncs data from Spruce (source of truth) to Patient Explorer.

Usage:
    from app.spruce_response_sync import sync_consent_responses
    results = sync_consent_responses(db)
"""

import os
import re
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple

import requests

from app.database import get_db, Patient

# Configure logging
logger = logging.getLogger(__name__)

# Configuration
SPRUCE_API_TOKEN = os.getenv("SPRUCE_API_TOKEN", "")
SPRUCE_BASE_URL = "https://api.sprucehealth.com/v1"

# Pattern to identify consent form responses in messages
CONSENT_FORM_MARKER = "[Auto-captured via Patient Explorer Consent Form]"


class SpruceResponseSync:
    """Syncs consent form responses from Spruce to local database."""

    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or SPRUCE_API_TOKEN
        if not self.api_token:
            raise ValueError("SPRUCE_API_TOKEN not configured")

        self.base_url = SPRUCE_BASE_URL

    def _headers(self) -> dict:
        """Get API request headers."""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def get_recent_conversations(
        self,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent conversations from Spruce.

        Args:
            limit: Maximum number of conversations to fetch
            since: Only fetch conversations modified after this time

        Returns:
            List of conversation dicts
        """
        params = {"limit": limit}

        response = requests.get(
            f"{self.base_url}/conversations",
            headers=self._headers(),
            params=params
        )
        response.raise_for_status()

        conversations = response.json().get("conversations", [])

        # Filter by modified time if specified
        if since:
            since_str = since.isoformat()
            conversations = [
                c for c in conversations
                if c.get("modifiedAt", "") >= since_str
            ]

        return conversations

    def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get messages (conversation items) from a specific conversation.

        Args:
            conversation_id: Spruce conversation ID
            limit: Maximum messages to fetch

        Returns:
            List of message dicts
        """
        response = requests.get(
            f"{self.base_url}/conversations/{conversation_id}/items",
            headers=self._headers(),
            params={"limit": limit}
        )
        response.raise_for_status()

        return response.json().get("items", [])

    def find_consent_responses(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Find messages that are consent form responses.

        Args:
            messages: List of message dicts from Spruce

        Returns:
            List of consent response dicts with parsed data
        """
        responses = []

        for msg in messages:
            text = msg.get("text", "")

            # Check if this is a consent form response
            if CONSENT_FORM_MARKER not in text:
                continue

            # Parse the response
            parsed = self._parse_consent_response(text)
            if parsed:
                parsed["message_id"] = msg.get("id")
                parsed["conversation_id"] = msg.get("conversationId")
                parsed["received_at"] = msg.get("createdAt")
                responses.append(parsed)

        return responses

    def _parse_consent_response(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse a consent form response message into structured data.

        Args:
            text: Message text from Spruce

        Returns:
            Dict with parsed fields or None if parsing fails
        """
        try:
            data = {}

            # Extract token
            token_match = re.search(r"Token:\s*(\S+)", text)
            if token_match:
                data["token"] = token_match.group(1)

            # Extract name
            name_match = re.search(r"Name:\s*(.+?)(?:\n|$)", text)
            if name_match:
                data["full_name"] = name_match.group(1).strip()

            # Extract DOB
            dob_match = re.search(r"DOB:\s*(.+?)(?:\n|$)", text)
            if dob_match:
                data["date_of_birth"] = dob_match.group(1).strip()

            # Extract contact method
            method_match = re.search(r"Preferred Method:\s*(.+?)(?:\n|$)", text)
            if method_match:
                data["contact_method"] = method_match.group(1).strip()

            # Extract consent status
            consent_match = re.search(r"Consent Given:\s*(.+?)(?:\n|$)", text)
            if consent_match:
                consent_text = consent_match.group(1).strip().lower()
                data["consent_given"] = "yes" in consent_text

            # Extract provider preference
            provider_match = re.search(r"Provider Choice:\s*(.+?)(?:\n|$)", text)
            if provider_match:
                data["provider_preference"] = provider_match.group(1).strip()

            # Extract questions
            questions_match = re.search(
                r"QUESTIONS/CONCERNS\s*-+\s*(.+?)(?:=|$)",
                text,
                re.DOTALL
            )
            if questions_match:
                questions = questions_match.group(1).strip()
                if questions and questions.lower() != "none":
                    data["questions"] = questions

            return data if data else None

        except Exception as e:
            logger.warning(f"Failed to parse consent response: {e}")
            return None

    def sync_to_database(
        self,
        responses: List[Dict[str, Any]],
        db
    ) -> Dict[str, int]:
        """
        Update local database with consent responses.

        Args:
            responses: List of parsed consent responses
            db: Database session

        Returns:
            Dict with counts: {"updated": n, "not_found": n, "errors": n}
        """
        stats = {"updated": 0, "not_found": 0, "errors": 0}

        for response in responses:
            try:
                # Try to find patient by token first
                token = response.get("token")
                patient = None

                if token:
                    # Look up patient by consent token
                    patient = db.query(Patient).filter(
                        Patient.consent_token == token
                    ).first()

                # If not found by token, try by name + DOB
                if not patient and response.get("full_name"):
                    name_parts = response["full_name"].split()
                    if len(name_parts) >= 2:
                        first_name = name_parts[0]
                        last_name = " ".join(name_parts[1:])

                        patient = db.query(Patient).filter(
                            Patient.first_name.ilike(f"%{first_name}%"),
                            Patient.last_name.ilike(f"%{last_name}%")
                        ).first()

                if patient:
                    # Update patient record
                    if response.get("consent_given"):
                        patient.consent_status = "consented"
                        patient.consent_date = datetime.utcnow()
                    else:
                        patient.consent_status = "declined"

                    if response.get("contact_method"):
                        patient.preferred_contact = response["contact_method"]

                    if response.get("provider_preference"):
                        patient.provider_preference = response["provider_preference"]

                    if response.get("questions"):
                        # Append to notes
                        existing_notes = patient.notes or ""
                        patient.notes = f"{existing_notes}\n\n[Form Response {datetime.utcnow().strftime('%Y-%m-%d')}]\n{response['questions']}"

                    patient.form_response_received = True
                    patient.form_response_date = datetime.utcnow()

                    stats["updated"] += 1
                    logger.info(f"Updated patient: {patient.id}")

                else:
                    stats["not_found"] += 1
                    logger.warning(
                        f"Patient not found for response: {response.get('full_name', 'Unknown')}"
                    )

            except Exception as e:
                stats["errors"] += 1
                logger.error(f"Error updating patient: {e}")

        # Commit changes
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Database commit failed: {e}")
            raise

        return stats

    def sync_all(
        self,
        db,
        since_days: int = 7
    ) -> Dict[str, Any]:
        """
        Full sync: fetch responses from Spruce and update database.

        Args:
            db: Database session
            since_days: Only sync responses from the last N days

        Returns:
            Dict with sync results
        """
        since = datetime.utcnow() - timedelta(days=since_days)

        results = {
            "conversations_checked": 0,
            "responses_found": 0,
            "patients_updated": 0,
            "patients_not_found": 0,
            "errors": 0,
            "sync_time": datetime.utcnow().isoformat(),
        }

        try:
            # Get recent conversations
            conversations = self.get_recent_conversations(limit=100, since=since)
            results["conversations_checked"] = len(conversations)

            all_responses = []

            # Check each conversation for consent responses
            for conv in conversations:
                try:
                    messages = self.get_conversation_messages(conv["id"])
                    responses = self.find_consent_responses(messages)
                    all_responses.extend(responses)
                except Exception as e:
                    logger.warning(f"Error processing conversation {conv['id']}: {e}")
                    results["errors"] += 1

            results["responses_found"] = len(all_responses)

            # Update database
            if all_responses:
                sync_stats = self.sync_to_database(all_responses, db)
                results["patients_updated"] = sync_stats["updated"]
                results["patients_not_found"] = sync_stats["not_found"]
                results["errors"] += sync_stats["errors"]

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            results["error_message"] = str(e)

        return results


# =============================================================================
# Convenience Functions
# =============================================================================

def sync_consent_responses(db, since_days: int = 7) -> Dict[str, Any]:
    """
    Sync consent form responses from Spruce to local database.

    Args:
        db: Database session
        since_days: Only sync responses from the last N days

    Returns:
        Dict with sync results
    """
    try:
        sync = SpruceResponseSync()
        return sync.sync_all(db, since_days=since_days)
    except ValueError as e:
        logger.error(f"Sync configuration error: {e}")
        return {"error": str(e), "sync_time": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return {"error": str(e), "sync_time": datetime.utcnow().isoformat()}


def get_sync_status() -> Dict[str, Any]:
    """
    Check if Spruce sync is configured and working.

    Returns:
        Dict with configuration status
    """
    status = {
        "configured": bool(SPRUCE_API_TOKEN),
        "api_token_set": bool(SPRUCE_API_TOKEN),
        "api_reachable": False,
        "last_check": datetime.utcnow().isoformat(),
    }

    if SPRUCE_API_TOKEN:
        try:
            response = requests.get(
                f"{SPRUCE_BASE_URL}/contacts",
                headers={
                    "Authorization": f"Bearer {SPRUCE_API_TOKEN}",
                    "Accept": "application/json",
                },
                params={"limit": 1},
                timeout=10
            )
            status["api_reachable"] = response.status_code == 200
            status["api_status_code"] = response.status_code
        except Exception as e:
            status["api_error"] = str(e)

    return status
