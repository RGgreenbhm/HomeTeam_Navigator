"""Diagnostic script to test Azure API connections.

This script tests connections to various Azure services:

V1.0 (Working):
- Azure Claude API - AI assistance
- Azure Document Intelligence - OCR processing
- Microsoft Graph API (DELEGATED) - User sign-in OAuth via ms_oauth.py
  - OneNote, SharePoint, Planner, To Do - all work with delegated permissions

V1.1 (Deferred):
- Microsoft Graph API (APP-ONLY) - Client credentials flow
  - Background operations without user sign-in
  - Requires Application permissions with admin consent

For V1.0, the app uses:
- Delegated Graph API (user signs in with Microsoft account)
- Local SQLite database for patient data
- Azure Blob Storage (via CLI auth)
- Spruce Health API
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("Patient Explorer - API Connection Diagnostics")
print("=" * 60)

# 1. Check environment variables
print("\n1. Environment Variables:")
print("-" * 40)

claude_endpoint = os.getenv("AZURE_CLAUDE_ENDPOINT")
claude_key = os.getenv("AZURE_CLAUDE_API_KEY")
doc_endpoint = os.getenv("AZURE_DOC_INTELLIGENCE_ENDPOINT")
doc_key = os.getenv("AZURE_DOC_INTELLIGENCE_KEY")
tenant_id = os.getenv("AZURE_TENANT_ID")
client_id = os.getenv("AZURE_CLIENT_ID")
client_secret = os.getenv("AZURE_CLIENT_SECRET")

print(f"AZURE_CLAUDE_ENDPOINT: {'Set' if claude_endpoint else 'MISSING'}")
if claude_endpoint:
    print(f"  -> {claude_endpoint[:50]}...")
print(f"AZURE_CLAUDE_API_KEY: {'Set (' + str(len(claude_key)) + ' chars)' if claude_key else 'MISSING'}")

print(f"AZURE_DOC_INTELLIGENCE_ENDPOINT: {'Set' if doc_endpoint else 'MISSING'}")
print(f"AZURE_DOC_INTELLIGENCE_KEY: {'Set' if doc_key else 'MISSING'}")

print(f"AZURE_TENANT_ID: {'Set' if tenant_id else 'MISSING'}")
print(f"AZURE_CLIENT_ID: {'Set' if client_id else 'MISSING'}")
print(f"AZURE_CLIENT_SECRET: {'Set' if client_secret else 'MISSING'}")

# 2. Test Azure Claude API
print("\n2. Azure Claude API Test:")
print("-" * 40)

try:
    from azure_claude import AzureClaudeClient
    print("  Client import: OK")

    client = AzureClaudeClient()
    print("  Client init: OK")
    print(f"  Endpoint: {client.endpoint}")

    result = client.test_connection()
    print(f"  Connection test: {'SUCCESS' if result['success'] else 'FAILED'}")
    if result['success']:
        print(f"  Auth method: {result['auth_method']}")
    else:
        print(f"  Error: {result['error']}")

    client.close()

except Exception as e:
    print(f"  ERROR: {e}")

# 3. Test Document Intelligence
print("\n3. Azure Document Intelligence Test:")
print("-" * 40)

try:
    from azure_document import DocumentClient
    print("  Client import: OK")

    doc_client = DocumentClient()
    print("  Client init: OK")
    print(f"  Endpoint: {doc_client.endpoint}")

    result = doc_client.test_connection()
    print(f"  Connection test: {'SUCCESS' if result.get('success') else 'FAILED'}")
    if result.get("error"):
        print(f"  Error: {result['error']}")

except Exception as e:
    print(f"  ERROR: {e}")

# 4. Test Microsoft Graph
print("\n4. Microsoft Graph API Test:")
print("-" * 40)
print("  V1.0: Uses DELEGATED auth (user sign-in via ms_oauth.py)")
print("  V1.1: Will add APP-ONLY auth (client credentials)")

# Test app-only auth (requires client_secret)
if client_secret:
    print("\n  Testing APP-ONLY auth (V1.1):")
    try:
        from microsoft_graph import GraphClient
        print("    Client import: OK")

        graph_client = GraphClient()
        print("    Client init: OK")

        result = graph_client.test_connection()
        print(f"    Connection test: {'SUCCESS' if result.get('success') else 'FAILED'}")

        if result.get("success"):
            print(f"    Organization: {result.get('organization', 'Unknown')}")
        elif result.get("hint"):
            print(f"    Hint: {result['hint'][:100]}...")
        if result.get("error"):
            print(f"    Error: {result['error'][:100]}...")

        graph_client.close()

    except Exception as e:
        print(f"    ERROR: {e}")
else:
    print("\n  APP-ONLY auth: SKIPPED (no AZURE_CLIENT_SECRET)")
    print("  This is expected - V1.0 uses delegated auth instead")

print("\n  DELEGATED auth (V1.0): Requires user to sign in via app UI")
print("  Test by running the Streamlit app and clicking 'Sign in with Microsoft'")

# 5. Raw HTTP test for Claude
print("\n5. Raw HTTP Test (Claude Endpoint):")
print("-" * 40)

try:
    import httpx

    # Test with api-key header
    print("  Testing with 'api-key' header...")
    headers1 = {
        "Content-Type": "application/json",
        "api-key": claude_key,
        "anthropic-version": "2023-06-01",
    }

    payload = {
        "model": "claude-haiku-4-5",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "Hi"}],
    }

    with httpx.Client(timeout=30.0) as http:
        resp1 = http.post(claude_endpoint, headers=headers1, json=payload)
        print(f"    Status: {resp1.status_code}")
        if resp1.status_code != 200:
            print(f"    Response: {resp1.text[:200]}")

    # Test with x-api-key header
    print("  Testing with 'x-api-key' header...")
    headers2 = {
        "Content-Type": "application/json",
        "x-api-key": claude_key,
        "anthropic-version": "2023-06-01",
    }

    with httpx.Client(timeout=30.0) as http:
        resp2 = http.post(claude_endpoint, headers=headers2, json=payload)
        print(f"    Status: {resp2.status_code}")
        if resp2.status_code != 200:
            print(f"    Response: {resp2.text[:200]}")

    # Test with Authorization Bearer
    print("  Testing with 'Authorization: Bearer' header...")
    headers3 = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {claude_key}",
        "anthropic-version": "2023-06-01",
    }

    with httpx.Client(timeout=30.0) as http:
        resp3 = http.post(claude_endpoint, headers=headers3, json=payload)
        print(f"    Status: {resp3.status_code}")
        if resp3.status_code != 200:
            print(f"    Response: {resp3.text[:200]}")

except Exception as e:
    print(f"  ERROR: {e}")

print("\n" + "=" * 60)
print("Diagnostics complete.")
print("=" * 60)
