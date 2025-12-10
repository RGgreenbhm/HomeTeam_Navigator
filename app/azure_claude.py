"""Azure Foundry Claude API client for Patient Explorer.

Provides HIPAA-compliant AI capabilities via Azure Foundry Claude models.
All models are covered under the Microsoft BAA.

Available models:
- claude-sonnet-4-5: Balanced performance/cost (default)
- claude-haiku-4-5: Fast, low-cost for simple tasks
- claude-opus-4-5: Most capable for complex reasoning

Usage:
    from azure_claude import AzureClaudeClient, ModelTier

    client = AzureClaudeClient()

    # Simple message
    response = client.send_message("Summarize this patient note...")

    # With specific model
    response = client.send_message(
        "Draft a consent SMS...",
        model=ModelTier.HAIKU  # Fast/cheap for templates
    )
"""

import os
import json
import logging
from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class ModelTier(Enum):
    """Model tiers with cost/capability tradeoffs."""
    HAIKU = "claude-haiku-4-5"      # Fast, cheap - templates, simple tasks
    SONNET = "claude-sonnet-4-5"    # Balanced - default for most tasks
    OPUS = "claude-opus-4-5"        # Most capable - complex reasoning


@dataclass
class ClaudeResponse:
    """Structured response from Claude API."""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    stop_reason: str
    raw_response: Dict[str, Any]


class AzureClaudeClient:
    """Client for Azure Foundry Claude API.

    HIPAA-compliant AI via Microsoft Azure BAA.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        default_model: ModelTier = ModelTier.SONNET,
    ):
        """Initialize Azure Claude client.

        Args:
            endpoint: Azure Foundry endpoint (defaults to env var)
            api_key: API key (defaults to env var)
            default_model: Default model tier to use
        """
        self.endpoint = endpoint or os.getenv("AZURE_CLAUDE_ENDPOINT")
        self.api_key = api_key or os.getenv("AZURE_CLAUDE_API_KEY")
        self.default_model = default_model

        if not self.endpoint:
            raise ValueError("AZURE_CLAUDE_ENDPOINT not configured")
        if not self.api_key:
            raise ValueError("AZURE_CLAUDE_API_KEY not configured")

        # HTTP client with timeout
        self.http_client = httpx.Client(timeout=60.0)

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers for Azure Foundry Claude.

        Azure AI Foundry with Anthropic models uses 'x-api-key' header
        (Anthropic standard), not the Azure 'api-key' header.
        """
        return {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

    def send_message(
        self,
        message: str,
        model: Optional[ModelTier] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> ClaudeResponse:
        """Send a message to Claude and get a response.

        Args:
            message: User message to send
            model: Model tier to use (defaults to client default)
            system_prompt: Optional system prompt for context
            max_tokens: Maximum response tokens
            temperature: Response creativity (0-1)

        Returns:
            ClaudeResponse with content and metadata
        """
        model_id = (model or self.default_model).value

        payload = {
            "model": model_id,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "user", "content": message}
            ],
        }

        if system_prompt:
            payload["system"] = system_prompt

        if temperature != 0.7:
            payload["temperature"] = temperature

        logger.debug(f"Sending request to Azure Claude ({model_id})")

        response = self.http_client.post(
            self.endpoint,
            headers=self._get_headers(),
            json=payload,
        )

        if response.status_code != 200:
            logger.error(f"Azure Claude error: {response.status_code} - {response.text}")
            raise Exception(f"Azure Claude API error: {response.status_code} - {response.text}")

        data = response.json()

        # Extract response content
        content = ""
        if data.get("content"):
            for block in data["content"]:
                if block.get("type") == "text":
                    content += block.get("text", "")

        return ClaudeResponse(
            content=content,
            model=data.get("model", model_id),
            input_tokens=data.get("usage", {}).get("input_tokens", 0),
            output_tokens=data.get("usage", {}).get("output_tokens", 0),
            stop_reason=data.get("stop_reason", ""),
            raw_response=data,
        )

    def send_conversation(
        self,
        messages: List[Dict[str, str]],
        model: Optional[ModelTier] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> ClaudeResponse:
        """Send a multi-turn conversation to Claude.

        Args:
            messages: List of {"role": "user"|"assistant", "content": "..."}
            model: Model tier to use
            system_prompt: Optional system prompt
            max_tokens: Maximum response tokens

        Returns:
            ClaudeResponse with content and metadata
        """
        model_id = (model or self.default_model).value

        payload = {
            "model": model_id,
            "max_tokens": max_tokens,
            "messages": messages,
        }

        if system_prompt:
            payload["system"] = system_prompt

        response = self.http_client.post(
            self.endpoint,
            headers=self._get_headers(),
            json=payload,
        )

        if response.status_code != 200:
            raise Exception(f"Azure Claude API error: {response.status_code} - {response.text}")

        data = response.json()

        content = ""
        if data.get("content"):
            for block in data["content"]:
                if block.get("type") == "text":
                    content += block.get("text", "")

        return ClaudeResponse(
            content=content,
            model=data.get("model", model_id),
            input_tokens=data.get("usage", {}).get("input_tokens", 0),
            output_tokens=data.get("usage", {}).get("output_tokens", 0),
            stop_reason=data.get("stop_reason", ""),
            raw_response=data,
        )

    def test_connection(self) -> Dict[str, Any]:
        """Test the API connection with diagnostics.

        Returns:
            Dict with success status and diagnostic info
        """
        result = {
            "success": False,
            "endpoint": self.endpoint,
            "error": None,
            "auth_method": "x-api-key",
        }

        try:
            response = self.send_message(
                "Reply with just 'OK'",
                model=ModelTier.HAIKU,
                max_tokens=10,
            )
            if "OK" in response.content.upper():
                result["success"] = True
                return result
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Connection test failed: {e}")

        return result

    def close(self):
        """Close the HTTP client."""
        self.http_client.close()


# =============================================================================
# Task-Specific Helpers
# =============================================================================

def draft_consent_sms(
    patient_name: str,
    preferred_name: Optional[str],
    consent_url: str,
    is_apcm: bool = False,
    client: Optional[AzureClaudeClient] = None,
) -> str:
    """Draft a personalized consent SMS message.

    Uses Haiku for fast, low-cost generation.

    Args:
        patient_name: Full patient name
        preferred_name: Preferred/nickname if available
        consent_url: Personalized consent form URL
        is_apcm: Whether patient is in APCM program
        client: Optional existing client (creates new if None)

    Returns:
        SMS message text
    """
    _client = client or AzureClaudeClient()

    display_name = preferred_name or patient_name.split()[0]

    context = "APCM patient who needs to decide about continuing care management" if is_apcm else "patient"

    prompt = f"""Draft a brief, friendly SMS (under 160 chars if possible, max 320 chars) for a {context}.

Patient name to use: {display_name}
Consent form URL: {consent_url}
Practice: Home Team Medical Services (transitioning from Dr. Green's practice)

Requirements:
- Professional but warm tone
- Clear call to action
- Include the URL
- Don't use emojis
- HIPAA compliant (no PHI in message)

Return ONLY the SMS text, nothing else."""

    response = _client.send_message(
        prompt,
        model=ModelTier.HAIKU,
        max_tokens=200,
        temperature=0.5,
    )

    if not client:
        _client.close()

    return response.content.strip()


def parse_consent_response(
    response_text: str,
    client: Optional[AzureClaudeClient] = None,
) -> Dict[str, Any]:
    """Parse a patient's consent form response using AI.

    Args:
        response_text: Raw form response text
        client: Optional existing client

    Returns:
        Dict with parsed consent elections
    """
    _client = client or AzureClaudeClient()

    prompt = f"""Parse this consent form response and extract the patient's elections.

Response text:
---
{response_text}
---

Return a JSON object with these fields:
- consents_to_records_retention: boolean or null
- continues_apcm_with_hometeam: boolean or null (if APCM patient)
- revokes_southview_billing: boolean or null (if APCM patient)
- patient_name_confirmed: string or null
- response_date: string (ISO format) or null
- notes: any additional relevant information

Return ONLY valid JSON, no explanation."""

    response = _client.send_message(
        prompt,
        model=ModelTier.SONNET,
        max_tokens=500,
        temperature=0.2,
    )

    if not client:
        _client.close()

    try:
        # Try to parse JSON from response
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content)
    except json.JSONDecodeError:
        return {"raw_response": response.content, "parse_error": True}


def summarize_patient_notes(
    notes: str,
    client: Optional[AzureClaudeClient] = None,
) -> str:
    """Summarize patient notes for care plan generation.

    Args:
        notes: Raw patient notes/captures
        client: Optional existing client

    Returns:
        Summarized notes
    """
    _client = client or AzureClaudeClient()

    system_prompt = """You are a medical assistant helping summarize patient information.
Be concise, accurate, and maintain HIPAA compliance.
Focus on clinically relevant information."""

    prompt = f"""Summarize these patient notes for care plan documentation:

{notes}

Provide a structured summary with:
1. Key diagnoses/conditions
2. Current medications (if mentioned)
3. Recent visits/encounters
4. Important clinical notes
5. Follow-up needs"""

    response = _client.send_message(
        prompt,
        model=ModelTier.SONNET,
        system_prompt=system_prompt,
        max_tokens=1000,
    )

    if not client:
        _client.close()

    return response.content


def generate_care_plan_section(
    condition: str,
    patient_context: str,
    client: Optional[AzureClaudeClient] = None,
) -> str:
    """Generate a care plan section for a specific condition.

    Args:
        condition: The medical condition
        patient_context: Relevant patient information
        client: Optional existing client

    Returns:
        Care plan section text
    """
    _client = client or AzureClaudeClient()

    system_prompt = """You are a clinical documentation assistant.
Generate evidence-based care plan content.
Use standard medical terminology.
Be specific and actionable."""

    prompt = f"""Generate a care plan section for: {condition}

Patient context:
{patient_context}

Include:
1. Goals (SMART format)
2. Interventions
3. Patient education points
4. Monitoring/follow-up schedule
5. When to escalate care"""

    response = _client.send_message(
        prompt,
        model=ModelTier.SONNET,
        system_prompt=system_prompt,
        max_tokens=1500,
    )

    if not client:
        _client.close()

    return response.content
