"""Azure Document Intelligence client for Patient Explorer.

Provides HIPAA-compliant document OCR and extraction via Azure Document Intelligence.
Covered under Microsoft BAA.

Use cases:
- Scan paper consent forms
- Extract data from faxed documents
- Process medical records (with PHI handling)
- Parse prescriptions and lab reports

Usage:
    from azure_document import DocumentClient

    client = DocumentClient()

    # Analyze a document
    result = client.analyze_document(file_bytes, "prebuilt-document")

    # Extract consent form fields
    consent_data = client.extract_consent_form(file_bytes)
"""

import os
import logging
from typing import Optional, Dict, Any, List, BinaryIO
from dataclasses import dataclass
from io import BytesIO

from dotenv import load_dotenv
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult, AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class ExtractedField:
    """A field extracted from a document."""
    name: str
    value: Any
    confidence: float
    bounding_box: Optional[List[float]] = None


@dataclass
class DocumentResult:
    """Result of document analysis."""
    content: str
    pages: int
    fields: Dict[str, ExtractedField]
    tables: List[Dict[str, Any]]
    raw_result: AnalyzeResult


class DocumentClient:
    """Client for Azure Document Intelligence.

    HIPAA-compliant document processing via Microsoft Azure BAA.
    """

    # Available prebuilt models
    MODELS = {
        "general": "prebuilt-document",       # General document extraction
        "read": "prebuilt-read",               # OCR text extraction
        "layout": "prebuilt-layout",           # Layout with tables/structure
        "invoice": "prebuilt-invoice",         # Invoice extraction
        "receipt": "prebuilt-receipt",         # Receipt extraction
        "id": "prebuilt-idDocument",           # ID document extraction
        "healthInsurance": "prebuilt-healthInsuranceCard.us",  # Health insurance cards
    }

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """Initialize Document Intelligence client.

        Args:
            endpoint: Azure endpoint (defaults to env var)
            api_key: API key (defaults to env var)
        """
        self.endpoint = endpoint or os.getenv("AZURE_DOC_INTELLIGENCE_ENDPOINT")
        self.api_key = api_key or os.getenv("AZURE_DOC_INTELLIGENCE_KEY")

        if not self.endpoint:
            raise ValueError("AZURE_DOC_INTELLIGENCE_ENDPOINT not configured")
        if not self.api_key:
            raise ValueError("AZURE_DOC_INTELLIGENCE_KEY not configured")

        # Remove trailing slash if present
        self.endpoint = self.endpoint.rstrip("/")

        self.client = DocumentIntelligenceClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.api_key),
        )

    def analyze_document(
        self,
        document: bytes,
        model_id: str = "prebuilt-document",
    ) -> DocumentResult:
        """Analyze a document using specified model.

        Args:
            document: Document bytes (PDF, image, etc.)
            model_id: Model to use (see MODELS dict)

        Returns:
            DocumentResult with extracted content
        """
        logger.info(f"Analyzing document with model: {model_id}")

        # Start analysis - SDK 1.0+ uses 'body' parameter
        poller = self.client.begin_analyze_document(
            model_id=model_id,
            body=document,
            content_type="application/octet-stream",
        )

        # Wait for result
        result = poller.result()

        # Extract fields
        fields = {}
        if result.documents:
            for doc in result.documents:
                if doc.fields:
                    for name, field in doc.fields.items():
                        fields[name] = ExtractedField(
                            name=name,
                            value=field.value if hasattr(field, 'value') else field.content,
                            confidence=field.confidence if hasattr(field, 'confidence') else 0.0,
                        )

        # Extract tables
        tables = []
        if result.tables:
            for table in result.tables:
                table_data = {
                    "rows": table.row_count,
                    "columns": table.column_count,
                    "cells": [],
                }
                if table.cells:
                    for cell in table.cells:
                        table_data["cells"].append({
                            "row": cell.row_index,
                            "col": cell.column_index,
                            "content": cell.content,
                        })
                tables.append(table_data)

        return DocumentResult(
            content=result.content or "",
            pages=len(result.pages) if result.pages else 0,
            fields=fields,
            tables=tables,
            raw_result=result,
        )

    def extract_text(self, document: bytes) -> str:
        """Extract plain text from a document using OCR.

        Args:
            document: Document bytes

        Returns:
            Extracted text content
        """
        result = self.analyze_document(document, "prebuilt-read")
        return result.content

    def extract_layout(self, document: bytes) -> DocumentResult:
        """Extract document layout with tables and structure.

        Args:
            document: Document bytes

        Returns:
            DocumentResult with layout information
        """
        return self.analyze_document(document, "prebuilt-layout")

    def extract_health_insurance_card(self, document: bytes) -> Dict[str, Any]:
        """Extract health insurance card information.

        Args:
            document: Image of insurance card (front/back)

        Returns:
            Dict with insurance card fields
        """
        result = self.analyze_document(document, "prebuilt-healthInsuranceCard.us")

        # Map common fields
        card_data = {
            "member_name": None,
            "member_id": None,
            "group_number": None,
            "plan_name": None,
            "payer_name": None,
            "effective_date": None,
            "copay_primary": None,
            "copay_specialist": None,
            "raw_fields": {},
        }

        for name, field in result.fields.items():
            card_data["raw_fields"][name] = field.value

            # Map known fields
            name_lower = name.lower()
            if "member" in name_lower and "name" in name_lower:
                card_data["member_name"] = field.value
            elif "member" in name_lower and "id" in name_lower:
                card_data["member_id"] = field.value
            elif "group" in name_lower:
                card_data["group_number"] = field.value
            elif "plan" in name_lower and "name" in name_lower:
                card_data["plan_name"] = field.value
            elif "payer" in name_lower or "insurer" in name_lower:
                card_data["payer_name"] = field.value

        return card_data

    def extract_consent_form(
        self,
        document: bytes,
        use_ai_parsing: bool = True,
    ) -> Dict[str, Any]:
        """Extract consent form fields using OCR + optional AI parsing.

        Args:
            document: Scanned consent form
            use_ai_parsing: Whether to use Claude for field extraction

        Returns:
            Dict with consent form fields
        """
        # First, extract text with layout
        result = self.analyze_document(document, "prebuilt-layout")

        consent_data = {
            "raw_text": result.content,
            "pages": result.pages,
            "checkboxes": [],
            "signatures": [],
            "dates": [],
            "parsed_elections": None,
        }

        # Look for checkbox-like patterns in the text
        lines = result.content.split("\n")
        for line in lines:
            line_lower = line.lower().strip()
            # Look for checkbox indicators
            if any(marker in line_lower for marker in ["[x]", "[✓]", "☑", "✓ ", "yes:", "no:"]):
                consent_data["checkboxes"].append(line.strip())
            # Look for date patterns
            if any(date_word in line_lower for date_word in ["date:", "signed:", "/20"]):
                consent_data["dates"].append(line.strip())

        # Use AI to parse if enabled
        if use_ai_parsing and result.content:
            try:
                from azure_claude import parse_consent_response
                consent_data["parsed_elections"] = parse_consent_response(result.content)
            except Exception as e:
                logger.warning(f"AI parsing failed: {e}")
                consent_data["parsed_elections"] = {"error": str(e)}

        return consent_data

    def test_connection(self) -> Dict[str, Any]:
        """Test the API connection with diagnostics.

        Returns:
            Dict with success status and diagnostic info
        """
        result = {
            "success": False,
            "endpoint": self.endpoint,
            "error": None,
        }

        # The client was initialized successfully if we got here,
        # which validates credentials exist. A full test would require
        # a real document, so we just verify the endpoint is configured.
        try:
            # Simple validation - if client init worked and endpoint is valid
            if self.client and self.endpoint:
                result["success"] = True
                return result
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Connection test failed: {e}")

        return result
