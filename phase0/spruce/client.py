"""
Spruce Health API client.

Implements the Spruce Health REST API for contact management and messaging.
API Documentation: https://developer.sprucehealth.com/docs/overview

Authentication uses Bearer token in Authorization header.
"""

import os
from datetime import date
from typing import Any, Optional

import httpx
from loguru import logger

from ..models import SpruceContact


class SpruceClient:
    """
    Client for Spruce Health API.

    Provides methods to:
    - Fetch all contacts
    - Search contacts by name/phone
    - Get contact conversations
    - Send SMS messages for outreach

    Usage:
        client = SpruceClient()
        if client.test_connection():
            contacts = client.get_contacts()
    """

    BASE_URL = "https://api.sprucehealth.com/v1"

    def __init__(
        self,
        api_token: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize Spruce client.

        Args:
            api_token: Spruce API token (or set SPRUCE_API_TOKEN env var)
            base_url: API base URL (defaults to production)
        """
        self.api_token = api_token or os.getenv("SPRUCE_API_TOKEN")
        self.base_url = (base_url or self.BASE_URL).rstrip("/")

        self._client: Optional[httpx.Client] = None

    def _ensure_token(self) -> None:
        """Verify API token is set."""
        if not self.api_token:
            raise ValueError(
                "SPRUCE_API_TOKEN not set. "
                "Set it in .env or pass to SpruceClient()"
            )

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client with auth headers."""
        self._ensure_token()

        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=30.0,
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
        return self._client

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response, raising on errors."""
        if response.status_code == 403:
            raise PermissionError(
                "Spruce API returned 403 Forbidden. "
                "Check that your API token is valid and not disabled."
            )
        elif response.status_code == 401:
            raise PermissionError("Spruce API returned 401 Unauthorized.")
        elif response.status_code == 429:
            raise RuntimeError("Spruce API rate limit exceeded. Try again later.")
        elif response.status_code >= 400:
            try:
                error_data = response.json()
                msg = error_data.get("message", response.text)
            except Exception:
                msg = response.text
            raise RuntimeError(f"Spruce API error {response.status_code}: {msg}")

        return response.json()

    def test_connection(self) -> bool:
        """
        Test API connection by fetching contacts (limit 1).

        Returns:
            True if connection successful
        """
        try:
            client = self._get_client()
            response = client.get("/contacts", params={"limit": 1})
            self._handle_response(response)
            logger.info("Spruce API connection successful")
            return True
        except Exception as e:
            logger.error(f"Spruce API connection failed: {e}")
            return False

    def get_contacts(self, limit: int = 100) -> list[SpruceContact]:
        """
        Fetch all contacts from Spruce with pagination.

        Args:
            limit: Number of contacts per page (max usually 100)

        Returns:
            List of SpruceContact objects
        """
        client = self._get_client()
        all_contacts = []
        pagination_token = None

        logger.info("Fetching contacts from Spruce...")

        while True:
            params = {"limit": limit}
            if pagination_token:
                params["paginationToken"] = pagination_token

            response = client.get("/contacts", params=params)
            data = self._handle_response(response)

            contacts = data.get("contacts", data.get("data", []))
            for c in contacts:
                contact = self._parse_contact(c)
                if contact:
                    all_contacts.append(contact)

            # Check for more pages
            if data.get("hasMore") and data.get("paginationToken"):
                pagination_token = data["paginationToken"]
                logger.debug(f"Fetched {len(all_contacts)} contacts, getting next page...")
            else:
                break

        logger.info(f"Fetched {len(all_contacts)} total contacts from Spruce")
        return all_contacts

    def _parse_contact(self, data: dict[str, Any]) -> Optional[SpruceContact]:
        """Parse API response into SpruceContact model."""
        try:
            # Handle date of birth
            dob = None
            dob_str = data.get("dateOfBirth") or data.get("dob")
            if dob_str:
                try:
                    # Try ISO format first
                    dob = date.fromisoformat(dob_str.split("T")[0])
                except (ValueError, AttributeError):
                    pass

            # Parse name - Spruce uses displayName primarily
            display_name = data.get("displayName", "")
            first_name = data.get("firstName")
            last_name = data.get("lastName")

            # If no first/last name, try to parse from displayName
            if not first_name and not last_name and display_name:
                parts = display_name.split()
                if len(parts) >= 2:
                    first_name = parts[0]
                    last_name = parts[-1]
                elif len(parts) == 1:
                    last_name = parts[0]

            return SpruceContact(
                spruce_id=data.get("id", ""),
                first_name=first_name,
                last_name=last_name,
                phone=self._extract_phone(data),
                email=self._extract_email(data),
                date_of_birth=dob,
            )
        except Exception as e:
            logger.warning(f"Error parsing contact: {e}")
            return None

    def _extract_phone(self, data: dict[str, Any]) -> Optional[str]:
        """Extract phone number from contact data."""
        # Try direct fields
        phone = data.get("phone") or data.get("phoneNumber") or data.get("mobile")
        if phone:
            return phone

        # Try nested phone numbers array (Spruce format)
        phones = data.get("phoneNumbers", [])
        if phones and isinstance(phones, list):
            for p in phones:
                if isinstance(p, dict):
                    # Spruce uses displayValue (formatted) or value (E.164)
                    return p.get("displayValue") or p.get("value") or p.get("number")
                elif isinstance(p, str):
                    return p

        return None

    def _extract_email(self, data: dict[str, Any]) -> Optional[str]:
        """Extract email from contact data."""
        email = data.get("email") or data.get("emailAddress")
        if email:
            return email

        # Try nested emails array (Spruce uses emailAddresses)
        emails = data.get("emailAddresses", data.get("emails", []))
        if emails and isinstance(emails, list):
            for e in emails:
                if isinstance(e, dict):
                    return e.get("address") or e.get("value") or e.get("email")
                elif isinstance(e, str):
                    return e

        return None

    def get_contact(self, contact_id: str) -> Optional[SpruceContact]:
        """
        Get a single contact by ID.

        Args:
            contact_id: Spruce contact ID

        Returns:
            SpruceContact if found, None otherwise
        """
        try:
            client = self._get_client()
            response = client.get(f"/contacts/{contact_id}")
            data = self._handle_response(response)
            return self._parse_contact(data)
        except Exception as e:
            logger.error(f"Error fetching contact {contact_id}: {e}")
            return None

    def search_contacts(self, query: str) -> list[SpruceContact]:
        """
        Search contacts by name, phone, or email.

        Args:
            query: Search query string

        Returns:
            List of matching SpruceContacts
        """
        try:
            client = self._get_client()
            response = client.post("/contacts/search", json={"query": query})
            data = self._handle_response(response)

            contacts = []
            for c in data.get("contacts", data.get("data", [])):
                contact = self._parse_contact(c)
                if contact:
                    contacts.append(contact)

            return contacts
        except Exception as e:
            logger.error(f"Error searching contacts: {e}")
            return []

    def find_contact_by_phone(self, phone: str) -> Optional[SpruceContact]:
        """
        Find a contact by phone number.

        Args:
            phone: Phone number to search

        Returns:
            SpruceContact if found, None otherwise
        """
        # Normalize phone number (digits only)
        digits = "".join(c for c in phone if c.isdigit())
        if len(digits) == 11 and digits[0] == "1":
            digits = digits[1:]  # Remove country code

        contacts = self.search_contacts(digits)

        # Find exact match
        for contact in contacts:
            if contact.phone:
                contact_digits = "".join(c for c in contact.phone if c.isdigit())
                if len(contact_digits) == 11 and contact_digits[0] == "1":
                    contact_digits = contact_digits[1:]
                if contact_digits == digits:
                    return contact

        return contacts[0] if contacts else None

    def find_contact_by_name(
        self, first_name: str, last_name: str
    ) -> list[SpruceContact]:
        """
        Find contacts by name.

        Args:
            first_name: First name to search
            last_name: Last name to search

        Returns:
            List of matching SpruceContacts
        """
        query = f"{first_name} {last_name}".strip()
        return self.search_contacts(query)

    def get_contact_conversations(self, contact_id: str) -> list[dict[str, Any]]:
        """
        Get conversations for a contact.

        Args:
            contact_id: Spruce contact ID

        Returns:
            List of conversation data
        """
        try:
            client = self._get_client()
            response = client.get(f"/contacts/{contact_id}/conversations")
            data = self._handle_response(response)
            return data.get("conversations", data.get("data", []))
        except Exception as e:
            logger.error(f"Error fetching conversations: {e}")
            return []

    def list_internal_endpoints(self) -> list[dict[str, Any]]:
        """
        List all internal endpoints (phone numbers, fax, email) for the organization.

        Returns:
            List of endpoint dicts with id, type, address, etc.
        """
        try:
            client = self._get_client()
            response = client.get("/internalendpoints")
            data = self._handle_response(response)
            endpoints = data.get("internalEndpoints", data.get("data", []))
            logger.info(f"Found {len(endpoints)} internal endpoints")
            return endpoints
        except Exception as e:
            logger.error(f"Error listing internal endpoints: {e}")
            return []

    def get_sms_endpoint_id(self, preferred_phone: Optional[str] = None) -> Optional[str]:
        """
        Get the internal endpoint ID for the organization's SMS phone number.

        The API returns endpoints in a nested structure:
        {
            "endpoint": {
                "channel": "phone",
                "id": "...",
                "rawValue": "+12059557605",
                "label": "Green Clinic, Main Phone"
            },
            ...
        }

        Args:
            preferred_phone: Optional phone number to prefer (e.g., from SPRUCE_ORG_PHONE)
                            Can be in any format - will be normalized for matching.

        Returns:
            Endpoint ID for sending SMS, or None if not found
        """
        endpoints = self.list_internal_endpoints()

        # Normalize preferred phone for comparison
        preferred_digits = None
        if preferred_phone:
            preferred_digits = "".join(c for c in preferred_phone if c.isdigit())
            if len(preferred_digits) == 10:
                preferred_digits = "1" + preferred_digits

        phone_endpoints = []

        for ep in endpoints:
            # The actual endpoint data is nested under "endpoint" key
            endpoint_data = ep.get("endpoint", {})
            channel = endpoint_data.get("channel", "")

            if channel.lower() == "phone":
                endpoint_id = endpoint_data.get("id")
                raw_value = endpoint_data.get("rawValue", "")
                label = endpoint_data.get("label", "")

                if endpoint_id:
                    phone_endpoints.append({
                        "id": endpoint_id,
                        "raw_value": raw_value,
                        "label": label,
                    })

                    # Check if this matches the preferred phone
                    if preferred_digits:
                        raw_digits = "".join(c for c in raw_value if c.isdigit())
                        if raw_digits == preferred_digits:
                            logger.info(f"Found preferred SMS endpoint: {label} ({raw_value})")
                            return endpoint_id

        # If no preferred match, use first phone endpoint
        if phone_endpoints:
            first = phone_endpoints[0]
            logger.info(f"Using first phone endpoint: {first['label']} ({first['raw_value']})")
            return first["id"]

        # Fallback: try to use first endpoint of any type (legacy behavior)
        if endpoints:
            endpoint_data = endpoints[0].get("endpoint", {})
            endpoint_id = endpoint_data.get("id")
            if endpoint_id:
                logger.warning(f"No phone endpoint found, using first endpoint: {endpoint_id}")
                return endpoint_id

        logger.error("No internal endpoints found")
        return None

    def send_sms(
        self,
        phone_number: str,
        message: str,
        contact_id: Optional[str] = None,
        internal_endpoint_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Send an SMS message via Spruce.

        Uses the correct Spruce API endpoint:
        POST /internalendpoints/{internalEndpointId}/conversations

        Args:
            phone_number: Destination phone number (E.164, 10-digit, or formatted)
            message: Message text to send
            contact_id: Optional Spruce contact ID (for existing contacts)
            internal_endpoint_id: Optional internal endpoint ID (auto-detected if not provided)

        Returns:
            Response dict with message ID and status
        """
        client = self._get_client()

        # Get internal endpoint ID (organization's Spruce phone number)
        # Use SPRUCE_ORG_PHONE from env to prefer the correct endpoint
        preferred_phone = os.getenv("SPRUCE_ORG_PHONE")
        endpoint_id = internal_endpoint_id or self.get_sms_endpoint_id(preferred_phone)
        if not endpoint_id:
            return {
                "success": False,
                "error": "No SMS endpoint found. Check your Spruce organization settings.",
            }

        # Normalize phone number to E.164 format
        # Handle various formats: (205) 955-7605, 205-955-7605, 2059557605, +12059557605
        digits = "".join(c for c in phone_number if c.isdigit())

        # Handle different digit counts
        if len(digits) == 10:
            # Standard US 10-digit: add country code
            digits = "1" + digits
        elif len(digits) == 11 and digits[0] == "1":
            # Already has US country code
            pass
        elif len(digits) < 10:
            # Too short - log warning but try anyway
            logger.warning(f"Phone number has fewer than 10 digits: {len(digits)} digits")
            digits = "1" + digits.zfill(10)  # Pad with zeros (will likely fail)
        # For 11+ digits not starting with 1, assume international and use as-is

        e164_phone = f"+{digits}"

        # Build message payload per Spruce API spec
        # POST /internalendpoints/{internalEndpointId}/conversations
        # Requires "message" field with "body" as array of elements
        payload = {
            "destination": {
                "smsOrEmailEndpoint": e164_phone,
            },
            "message": {
                "body": [
                    {
                        "type": "text",
                        "value": message,
                    }
                ],
            },
        }

        # If we have a contact ID, include it
        if contact_id:
            payload["destination"]["contactId"] = contact_id

        logger.info(f"Sending SMS to {e164_phone[:7]}*** via endpoint {endpoint_id[:8]}...")
        logger.debug(f"SMS payload: {payload}")

        try:
            response = client.post(
                f"/internalendpoints/{endpoint_id}/conversations",
                json=payload
            )
            # Log raw response for debugging
            logger.debug(f"SMS response status: {response.status_code}")
            logger.debug(f"SMS response body: {response.text[:500] if response.text else 'empty'}")
            data = self._handle_response(response)
            logger.info(f"SMS sent successfully: {data.get('requestId', data.get('id', 'unknown'))}")
            return {
                "success": True,
                "message_id": data.get("requestId") or data.get("id") or data.get("conversationId"),
                "status": data.get("status", "sent"),
                "data": data,
            }
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def send_bulk_sms(
        self,
        recipients: list[dict[str, str]],
        message_template: str,
    ) -> list[dict[str, Any]]:
        """
        Send SMS to multiple recipients with personalization.

        Args:
            recipients: List of dicts with 'phone', 'name', and optionally 'contact_id'
            message_template: Message template with {name} placeholder

        Returns:
            List of results for each recipient
        """
        results = []

        for recipient in recipients:
            phone = recipient.get("phone")
            name = recipient.get("name", "Patient")
            contact_id = recipient.get("contact_id")

            if not phone:
                results.append({
                    "phone": phone,
                    "success": False,
                    "error": "No phone number",
                })
                continue

            # Personalize message
            personalized_message = message_template.format(name=name)

            # Send message
            result = self.send_sms(phone, personalized_message, contact_id)
            result["phone"] = phone
            result["name"] = name
            results.append(result)

        return results

    # =========================================================================
    # Contact Tags
    # =========================================================================

    def list_contact_tags(self) -> list[dict[str, Any]]:
        """
        List all contact tags available to the organization.

        Contact tags are labels on a patient's chart (e.g., "VIP", "Primary Doctor",
        "Location"). Different from conversation tags which are labels on messages.

        Returns:
            List of tag dicts with id, name, color, etc.
        """
        client = self._get_client()
        all_tags = []
        pagination_token = None

        try:
            while True:
                params = {}
                if pagination_token:
                    params["paginationToken"] = pagination_token

                response = client.get("/contacts/tags", params=params)
                data = self._handle_response(response)

                tags = data.get("tags", data.get("data", []))
                all_tags.extend(tags)

                if data.get("hasMore") and data.get("paginationToken"):
                    pagination_token = data["paginationToken"]
                else:
                    break

            logger.info(f"Fetched {len(all_tags)} contact tags from Spruce")
            return all_tags

        except Exception as e:
            logger.error(f"Error fetching contact tags: {e}")
            return []

    def create_contact_tag(self, name: str, color: Optional[str] = None) -> Optional[dict[str, Any]]:
        """
        Create a new contact tag for the organization.

        If the tag already exists, returns the existing tag.

        Args:
            name: Tag name (e.g., "VIP", "APCM Patient")
            color: Optional hex color code

        Returns:
            Tag dict with id, name, color or None on error
        """
        client = self._get_client()

        payload = {"name": name}
        if color:
            payload["color"] = color

        try:
            response = client.post("/contacts/tags", json=payload)
            data = self._handle_response(response)
            logger.info(f"Created/found contact tag: {name}")
            return data
        except Exception as e:
            logger.error(f"Error creating contact tag: {e}")
            return None

    def get_contact_with_tags(self, contact_id: str) -> Optional[dict[str, Any]]:
        """
        Get a contact with full details including tags.

        Args:
            contact_id: Spruce contact ID

        Returns:
            Full contact dict including tags array, or None
        """
        try:
            client = self._get_client()
            response = client.get(f"/contacts/{contact_id}")
            data = self._handle_response(response)
            return data
        except Exception as e:
            logger.error(f"Error fetching contact with tags: {e}")
            return None

    def add_tag_to_contact(self, contact_id: str, tag_id: str) -> bool:
        """
        Add a tag to a contact.

        Args:
            contact_id: Spruce contact ID
            tag_id: Tag ID to add

        Returns:
            True if successful
        """
        client = self._get_client()

        try:
            response = client.post(
                f"/contacts/{contact_id}/tags",
                json={"tagId": tag_id}
            )
            self._handle_response(response)
            logger.info(f"Added tag {tag_id} to contact {contact_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding tag to contact: {e}")
            return False

    def remove_tag_from_contact(self, contact_id: str, tag_id: str) -> bool:
        """
        Remove a tag from a contact.

        Args:
            contact_id: Spruce contact ID
            tag_id: Tag ID to remove

        Returns:
            True if successful
        """
        client = self._get_client()

        try:
            response = client.delete(f"/contacts/{contact_id}/tags/{tag_id}")
            self._handle_response(response)
            logger.info(f"Removed tag {tag_id} from contact {contact_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing tag from contact: {e}")
            return False

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def test_connection() -> bool:
    """
    Test Spruce API connection.

    Returns:
        True if connection successful
    """
    try:
        with SpruceClient() as client:
            return client.test_connection()
    except Exception as e:
        logger.error(f"Spruce connection test failed: {e}")
        return False
