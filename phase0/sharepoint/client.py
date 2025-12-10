"""
SharePoint client for consent tracking.

Uses Office365-REST-Python-Client to interact with SharePoint Lists
for tracking patient consent status.

The consent data is stored in a SharePoint List with columns:
- MRN (text)
- PatientName (text)
- ConsentStatus (choice)
- ConsentMethod (choice)
- OutreachDate (datetime)
- ResponseDate (datetime)
- Notes (text)
- SpruceMatched (yes/no)
- CreatedBy (person)
- ModifiedBy (person)
"""

import os
from datetime import datetime
from typing import Optional

from loguru import logger

from ..models import ConsentRecord, ConsentStatus, ConsentMethod

# Office365 imports
try:
    from office365.runtime.auth.client_credential import ClientCredential
    from office365.sharepoint.client_context import ClientContext
    from office365.sharepoint.lists.list import List as SPList
    SHAREPOINT_AVAILABLE = True
except ImportError:
    SHAREPOINT_AVAILABLE = False
    logger.warning("Office365-REST-Python-Client not available")


class SharePointClient:
    """
    Client for SharePoint consent tracking.

    Manages a SharePoint List that stores consent records.

    Usage:
        client = SharePointClient()
        client.create_consent_list()  # One-time setup
        client.add_consent_record(record)
        records = client.get_all_records()
    """

    CONSENT_LIST_NAME = "PatientConsentTracking"

    def __init__(
        self,
        site_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        """
        Initialize SharePoint client.

        Args:
            site_url: SharePoint site URL (or SHAREPOINT_SITE_URL env var)
            client_id: Azure AD app client ID (or SHAREPOINT_CLIENT_ID env var)
            client_secret: Azure AD app client secret (or SHAREPOINT_CLIENT_SECRET env var)
        """
        if not SHAREPOINT_AVAILABLE:
            raise ImportError("Office365-REST-Python-Client is required")

        self.site_url = site_url or os.getenv("SHAREPOINT_SITE_URL")
        self.client_id = client_id or os.getenv("SHAREPOINT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("SHAREPOINT_CLIENT_SECRET")

        self._ctx: Optional[ClientContext] = None

    def _ensure_credentials(self) -> None:
        """Verify credentials are set."""
        if not self.site_url:
            raise ValueError("SHAREPOINT_SITE_URL not set")
        if not self.client_id:
            raise ValueError("SHAREPOINT_CLIENT_ID not set")
        if not self.client_secret:
            raise ValueError("SHAREPOINT_CLIENT_SECRET not set")

    def _get_context(self) -> "ClientContext":
        """Get or create SharePoint context."""
        if self._ctx is None:
            self._ensure_credentials()
            credentials = ClientCredential(self.client_id, self.client_secret)
            self._ctx = ClientContext(self.site_url).with_credentials(credentials)
            logger.info(f"Connected to SharePoint: {self.site_url}")
        return self._ctx

    def create_consent_list(self) -> bool:
        """
        Create the consent tracking list if it doesn't exist.

        This is a one-time setup operation.

        Returns:
            True if list was created or already exists
        """
        ctx = self._get_context()

        # Check if list exists
        try:
            lists = ctx.web.lists
            ctx.load(lists)
            ctx.execute_query()

            existing = [l for l in lists if l.properties.get("Title") == self.CONSENT_LIST_NAME]
            if existing:
                logger.info(f"List '{self.CONSENT_LIST_NAME}' already exists")
                return True
        except Exception as e:
            logger.error(f"Error checking for existing list: {e}")

        # Create list
        logger.info(f"Creating list '{self.CONSENT_LIST_NAME}'...")

        try:
            # Create the list
            list_info = {
                "Title": self.CONSENT_LIST_NAME,
                "Description": "Patient consent tracking for record retention",
                "BaseTemplate": 100,  # Generic list
            }
            new_list = ctx.web.lists.add(list_info)
            ctx.execute_query()

            # Add custom columns
            self._add_list_columns(new_list)

            logger.info(f"List '{self.CONSENT_LIST_NAME}' created successfully")
            return True

        except Exception as e:
            logger.error(f"Error creating list: {e}")
            return False

    def _add_list_columns(self, sp_list: "SPList") -> None:
        """Add custom columns to the consent list."""
        ctx = self._get_context()

        # Column definitions
        columns = [
            ("MRN", "Text", True),
            ("PatientName", "Text", True),
            ("ConsentStatus", "Choice", True),
            ("ConsentMethod", "Choice", False),
            ("OutreachDate", "DateTime", False),
            ("ResponseDate", "DateTime", False),
            ("ConsentDate", "DateTime", False),
            ("Notes", "Note", False),
            ("SprucePatientId", "Text", False),
            ("SpruceMatched", "Boolean", False),
        ]

        for col_name, col_type, required in columns:
            try:
                if col_type == "Text":
                    sp_list.fields.add_text_field(col_name, required=required)
                elif col_type == "Note":
                    sp_list.fields.add_note_field(col_name)
                elif col_type == "DateTime":
                    sp_list.fields.add_date_time_field(col_name)
                elif col_type == "Boolean":
                    sp_list.fields.add_boolean_field(col_name)
                elif col_type == "Choice":
                    if col_name == "ConsentStatus":
                        choices = [s.value for s in ConsentStatus]
                    elif col_name == "ConsentMethod":
                        choices = [m.value for m in ConsentMethod]
                    else:
                        choices = []
                    sp_list.fields.add_choice_field(col_name, choices)

                ctx.execute_query()
                logger.debug(f"Added column: {col_name}")

            except Exception as e:
                logger.warning(f"Error adding column {col_name}: {e}")

    def add_consent_record(self, record: ConsentRecord) -> bool:
        """
        Add a consent record to SharePoint.

        Args:
            record: ConsentRecord to add

        Returns:
            True if successful
        """
        ctx = self._get_context()

        try:
            sp_list = ctx.web.lists.get_by_title(self.CONSENT_LIST_NAME)

            item_data = {
                "Title": record.mrn,  # Required field
                "MRN": record.mrn,
                "PatientName": record.patient_name,
                "ConsentStatus": record.status.value,
                "ConsentMethod": record.method.value,
                "Notes": record.notes or "",
                "SprucePatientId": record.spruce_patient_id or "",
                "SpruceMatched": record.spruce_matched,
            }

            # Add dates if set
            if record.outreach_date:
                item_data["OutreachDate"] = record.outreach_date.isoformat()
            if record.response_date:
                item_data["ResponseDate"] = record.response_date.isoformat()
            if record.consent_date:
                item_data["ConsentDate"] = record.consent_date.isoformat()

            sp_list.add_item(item_data)
            ctx.execute_query()

            logger.info(f"Added consent record for {record.mrn}")
            return True

        except Exception as e:
            logger.error(f"Error adding consent record: {e}")
            return False

    def update_consent_status(
        self,
        mrn: str,
        status: ConsentStatus,
        method: Optional[ConsentMethod] = None,
        response_date: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Update consent status for a patient.

        Args:
            mrn: Patient MRN
            status: New consent status
            method: Consent method (if status is CONSENTED)
            response_date: When patient responded
            notes: Additional notes

        Returns:
            True if successful
        """
        ctx = self._get_context()

        try:
            sp_list = ctx.web.lists.get_by_title(self.CONSENT_LIST_NAME)
            items = sp_list.items.filter(f"MRN eq '{mrn}'")
            ctx.load(items)
            ctx.execute_query()

            if not items:
                logger.warning(f"No record found for MRN: {mrn}")
                return False

            item = items[0]
            item.set_property("ConsentStatus", status.value)

            if method:
                item.set_property("ConsentMethod", method.value)
            if response_date:
                item.set_property("ResponseDate", response_date.isoformat())
            if notes:
                item.set_property("Notes", notes)

            item.update()
            ctx.execute_query()

            logger.info(f"Updated consent status for {mrn}: {status.value}")
            return True

        except Exception as e:
            logger.error(f"Error updating consent status: {e}")
            return False

    def get_all_records(self) -> list[ConsentRecord]:
        """
        Get all consent records from SharePoint.

        Returns:
            List of ConsentRecord objects
        """
        ctx = self._get_context()

        try:
            sp_list = ctx.web.lists.get_by_title(self.CONSENT_LIST_NAME)
            items = sp_list.items
            ctx.load(items)
            ctx.execute_query()

            records = []
            for item in items:
                props = item.properties
                record = ConsentRecord(
                    mrn=props.get("MRN", ""),
                    patient_name=props.get("PatientName", ""),
                    status=ConsentStatus(props.get("ConsentStatus", "pending")),
                    method=ConsentMethod(props.get("ConsentMethod", "n/a")),
                    notes=props.get("Notes"),
                    spruce_patient_id=props.get("SprucePatientId"),
                    spruce_matched=props.get("SpruceMatched", False),
                )
                records.append(record)

            logger.info(f"Retrieved {len(records)} consent records")
            return records

        except Exception as e:
            logger.error(f"Error getting consent records: {e}")
            return []

    def get_records_by_status(self, status: ConsentStatus) -> list[ConsentRecord]:
        """Get records filtered by consent status."""
        all_records = self.get_all_records()
        return [r for r in all_records if r.status == status]
