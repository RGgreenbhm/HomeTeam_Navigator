# Plaud Webhook Integration Specification

**Date**: December 8, 2025  
**Status**: Design Complete - Awaiting Plaud Developer Portal Access  
**For**: Patient Explorer V1.0

---

## Overview

Plaud is a HIPAA-compliant AI voice recorder and transcription platform. This document specifies how Patient Explorer will integrate with Plaud to automatically receive clinical encounter transcripts.

### Key Facts About Plaud

- **HIPAA Compliant**: Full SOC 2, HIPAA, GDPR, and EN18031 compliance
- **API**: REST API with OAuth2 authentication
- **Webhooks**: Real-time notifications for transcription completion
- **Output Format**: JSON with structured transcripts, summaries, and metadata
- **Healthcare Focus**: Specifically designed for EHR integration

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PLAUD TRANSCRIPT FLOW                                │
└─────────────────────────────────────────────────────────────────────────┘

  Plaud Device                    Plaud Cloud                   Patient Explorer
  (@greenclinicteam.com)          (HIPAA Compliant)             (Azure + Streamlit)
       │                               │                              │
       │  1. Record Encounter          │                              │
       │─────────────────────────────►│                              │
       │                               │                              │
       │                               │  2. Transcribe + Summarize   │
       │                               │──────────────────────────────│
       │                               │                              │
       │                               │  3. Webhook: transcription   │
       │                               │     completed                │
       │                               │─────────────────────────────►│
       │                               │                              │
       │                               │                   4. Store in│
       │                               │                      Azure   │
       │                               │                   5. Match to│
       │                               │                      Patient │
       │                               │                              │
```

---

## Plaud API Authentication

Based on Plaud documentation:

```python
import base64
import os
import requests

# Environment variables
PLAUD_CLIENT_ID = os.getenv("PLAUD_CLIENT_ID")
PLAUD_CLIENT_SECRET = os.getenv("PLAUD_CLIENT_SECRET_KEY")

def get_plaud_api_token():
    """Generate API token from credentials."""
    credentials = base64.b64encode(
        f"{PLAUD_CLIENT_ID}:{PLAUD_CLIENT_SECRET}".encode()
    ).decode()
    
    response = requests.post(
        'https://api.plaud.ai/apis/oauth/api-token',
        headers={
            'Authorization': f'Bearer {credentials}',
            'Content-Type': 'application/json'
        }
    )
    
    token_data = response.json()
    return token_data['api_token']
```

---

## Webhook Configuration

### Step 1: Register Webhook in Plaud Developer Portal

Configure in Plaud Dashboard:
- **Name**: `Patient-Explorer-Transcript-Webhook`
- **Callback URL**: `https://<your-azure-function>.azurewebsites.net/api/plaud-webhook`
- **Events**: 
  - `audio_transcribe.completed`
  - `ai_summary.completed` (if available)

### Step 2: Environment Variables

```env
# Plaud API Configuration
PLAUD_CLIENT_ID=your_client_id
PLAUD_CLIENT_SECRET_KEY=your_secret_key
PLAUD_WEBHOOK_SECRET=your_webhook_signing_secret
PLAUD_COMPANY_DOMAIN=greenclinicteam.com
```

---

## Webhook Payload Structure (Estimated)

Based on Plaud documentation and common webhook patterns:

```json
{
  "event_type": "audio_transcribe.completed",
  "timestamp": "2025-12-08T14:30:00Z",
  "data": {
    "file_id": "file_abc123",
    "owner_id": "user_xyz789",
    "owner_email": "drgreen@greenclinicteam.com",
    "device_id": "device_456",
    "recording": {
      "duration_seconds": 1847,
      "recorded_at": "2025-12-08T14:00:00Z",
      "title": "Patient Visit - Smith, John",
      "format": "opus"
    },
    "transcription": {
      "status": "completed",
      "language": "en",
      "confidence": 0.94,
      "text": "Full transcription text here...",
      "segments": [
        {
          "start": "0:00:00",
          "end": "0:00:15",
          "speaker": "SPEAKER_1",
          "text": "Good morning, how are you feeling today?"
        },
        {
          "start": "0:00:16",
          "end": "0:00:28",
          "speaker": "SPEAKER_2",
          "text": "I've been having some chest pain for the past few days..."
        }
      ],
      "speakers": {
        "SPEAKER_1": {"label": "Provider"},
        "SPEAKER_2": {"label": "Patient"}
      }
    },
    "summary": {
      "status": "completed",
      "brief": "45-year-old male presents with 3-day history of substernal chest pain...",
      "key_points": [
        "Chief complaint: Chest pain x 3 days",
        "Character: Substernal, non-radiating",
        "Associated symptoms: Mild shortness of breath"
      ],
      "action_items": [
        "Order EKG",
        "Schedule stress test",
        "Follow up in 1 week"
      ]
    },
    "metadata": {
      "custom_fields": {
        "patient_name": "Smith, John",
        "appointment_type": "Follow-up"
      }
    },
    "download_urls": {
      "audio": "https://api.plaud.ai/files/file_abc123/audio?token=...",
      "transcript_json": "https://api.plaud.ai/files/file_abc123/transcript?token=..."
    }
  }
}
```

---

## Webhook Receiver Implementation

### Option A: Azure Function (Recommended for Production)

```python
# azure_function/plaud_webhook/__init__.py

import azure.functions as func
import hmac
import hashlib
import json
import os
import logging
from datetime import datetime

def verify_plaud_signature(payload: bytes, signature: str) -> bool:
    """Verify webhook signature from Plaud."""
    secret = os.environ.get('PLAUD_WEBHOOK_SECRET')
    if not secret or not signature:
        return False
    
    expected = hmac.new(
        secret.encode('utf-8'),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Plaud webhook received')
    
    # 1. Verify signature
    signature = req.headers.get('Plaud-Signature')
    if not verify_plaud_signature(req.get_body(), signature):
        logging.warning('Invalid Plaud signature')
        return func.HttpResponse("Invalid signature", status_code=400)
    
    # 2. Parse event
    try:
        event = req.get_json()
        event_type = event.get('event_type')
        data = event.get('data', {})
    except Exception as e:
        logging.error(f"Failed to parse webhook: {e}")
        return func.HttpResponse("Invalid JSON", status_code=400)
    
    # 3. Filter by company domain
    owner_email = data.get('owner_email', '')
    allowed_domain = os.environ.get('PLAUD_COMPANY_DOMAIN', 'greenclinicteam.com')
    
    if not owner_email.endswith(f'@{allowed_domain}'):
        logging.info(f"Ignoring webhook from {owner_email}")
        return func.HttpResponse("OK", status_code=200)
    
    # 4. Handle transcription completed event
    if event_type == 'audio_transcribe.completed':
        process_transcript(data)
    
    return func.HttpResponse("OK", status_code=200)


def process_transcript(data: dict):
    """Process completed transcription."""
    file_id = data.get('file_id')
    owner_email = data.get('owner_email')
    recording = data.get('recording', {})
    transcription = data.get('transcription', {})
    summary = data.get('summary', {})
    
    # Create transcript record
    transcript_record = {
        "id": file_id,
        "source": "plaud",
        "recorded_by": owner_email,
        "recorded_at": recording.get('recorded_at'),
        "duration_seconds": recording.get('duration_seconds'),
        "title": recording.get('title'),
        "transcript_text": transcription.get('text'),
        "segments": transcription.get('segments', []),
        "summary": summary.get('brief'),
        "key_points": summary.get('key_points', []),
        "action_items": summary.get('action_items', []),
        "patient_id": None,  # To be matched
        "processed_at": datetime.utcnow().isoformat(),
        "status": "pending_patient_match"
    }
    
    # Save to Azure Blob Storage
    save_transcript_to_azure(transcript_record)
    
    # Attempt automatic patient matching
    attempt_patient_match(transcript_record)


def save_transcript_to_azure(record: dict):
    """Save transcript to Azure Blob Storage."""
    from azure.storage.blob import BlobServiceClient
    
    connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
    container_name = "patient-data"
    
    blob_service = BlobServiceClient.from_connection_string(connection_string)
    container = blob_service.get_container_client(container_name)
    
    # Save to transcripts folder
    blob_name = f"transcripts/{record['id']}.json"
    blob_client = container.get_blob_client(blob_name)
    
    blob_client.upload_blob(
        json.dumps(record, indent=2),
        overwrite=True
    )
    
    logging.info(f"Saved transcript {record['id']} to Azure")


def attempt_patient_match(transcript: dict):
    """
    Attempt to match transcript to patient.
    
    Matching strategies:
    1. Recording title contains patient name
    2. Scheduled appointment at similar time
    3. Manual matching in UI
    """
    title = transcript.get('title', '')
    recorded_at = transcript.get('recorded_at')
    
    # Strategy 1: Parse patient name from title
    # Expected format: "Patient Visit - LastName, FirstName"
    if ' - ' in title:
        name_part = title.split(' - ')[-1].strip()
        if ',' in name_part:
            last_name, first_name = [n.strip() for n in name_part.split(',', 1)]
            # Search patient database
            # patient = search_patient_by_name(last_name, first_name)
    
    # Strategy 2: Match by scheduled appointment time
    # Look for appointments within 30 minutes of recording time
    # patient = find_patient_by_appointment_time(recorded_at)
    
    # If no automatic match, leave for manual matching
    pass
```

### Option B: Streamlit Endpoint (Development Only)

For development/testing, you can add a webhook receiver directly in Streamlit:

```python
# app/pages/25_Plaud_Transcripts.py

import streamlit as st
import json
from datetime import datetime

st.set_page_config(page_title="Plaud Transcripts", page_icon="🎙️", layout="wide")

st.title("🎙️ Plaud Transcripts")

# Tab layout
tab1, tab2, tab3 = st.tabs(["Pending Review", "Matched", "All Transcripts"])

with tab1:
    st.subheader("Transcripts Pending Patient Match")
    
    # Load pending transcripts from Azure
    pending = load_transcripts_by_status("pending_patient_match")
    
    for transcript in pending:
        with st.expander(f"📝 {transcript['title']} - {transcript['recorded_at'][:10]}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write("**Summary:**")
                st.write(transcript.get('summary', 'No summary available'))
                
                st.write("**Key Points:**")
                for point in transcript.get('key_points', []):
                    st.write(f"• {point}")
                
                st.write("**Action Items:**")
                for item in transcript.get('action_items', []):
                    st.write(f"☐ {item}")
            
            with col2:
                st.write("**Match to Patient:**")
                
                # Patient selector
                patients = load_patient_list()
                patient_options = [f"{p['last_name']}, {p['first_name']}" for p in patients]
                
                selected = st.selectbox(
                    "Select patient",
                    options=[""] + patient_options,
                    key=f"match_{transcript['id']}"
                )
                
                if selected and st.button("Match", key=f"btn_{transcript['id']}"):
                    match_transcript_to_patient(transcript['id'], selected)
                    st.success(f"Matched to {selected}")
                    st.rerun()

with tab2:
    st.subheader("Matched Transcripts")
    matched = load_transcripts_by_status("matched")
    
    for transcript in matched:
        st.write(f"✅ {transcript['title']} → {transcript['patient_name']}")

with tab3:
    st.subheader("All Transcripts")
    # Show all transcripts with filters
```

---

## Patient Matching Strategies

### Strategy 1: Recording Title Convention

Encourage providers to name recordings with patient identifier:

```
"Visit - Smith, John - 12/08/2025"
"Follow-up - Mary Johnson"
"AWV - Robert Brown"
```

Parser:
```python
def parse_patient_from_title(title: str) -> tuple:
    """Extract patient name from recording title."""
    patterns = [
        r"(?:Visit|Follow-up|AWV|New Patient)\s*[-–]\s*([^-–]+)",
        r"([A-Z][a-z]+),\s*([A-Z][a-z]+)",  # LastName, FirstName
    ]
    # ... matching logic
```

### Strategy 2: Appointment Time Matching

Match recording timestamp to scheduled appointments:

```python
def find_patient_by_appointment(recorded_at: datetime, tolerance_minutes: int = 30):
    """Find patient who had appointment near recording time."""
    # Query appointments within tolerance window
    # Return best match or candidates for manual selection
```

### Strategy 3: Manual Matching UI

Always provide fallback for manual patient selection in the Transcripts page.

---

## Data Flow to Patient Record

Once matched, transcript data is added to patient's JSON record:

```json
{
  "id": "patient-uuid",
  "demographics": { ... },
  "encounters": [
    {
      "id": "enc-123",
      "date": "2025-12-08",
      "type": "office_visit",
      "provider": "Dr. Green",
      "plaud_transcript_id": "file_abc123",
      "summary": "45-year-old male presents with chest pain...",
      "source": "plaud"
    }
  ],
  "transcripts": [
    {
      "id": "file_abc123",
      "source": "plaud",
      "recorded_at": "2025-12-08T14:00:00Z",
      "duration_seconds": 1847,
      "azure_blob_path": "transcripts/file_abc123.json",
      "summary": "...",
      "matched_at": "2025-12-08T15:00:00Z",
      "matched_by": "drgreen@greenclinicteam.com"
    }
  ]
}
```

---

## Environment Configuration

Add to `.env`:

```env
# Plaud Integration
PLAUD_CLIENT_ID=your_client_id
PLAUD_CLIENT_SECRET_KEY=your_secret_key
PLAUD_WEBHOOK_SECRET=your_webhook_signing_secret
PLAUD_COMPANY_DOMAIN=greenclinicteam.com
PLAUD_API_BASE_URL=https://api.plaud.ai

# Azure Function (for webhook receiver)
AZURE_FUNCTION_URL=https://patient-explorer-plaud.azurewebsites.net
```

---

## Implementation Checklist

### Phase 1: Plaud Portal Setup (Waiting on Access)
- [ ] Receive Plaud Developer Portal credentials
- [ ] Create company profile for @greenclinicteam.com
- [ ] Register webhook endpoint
- [ ] Obtain webhook signing secret
- [ ] Test webhook with sample data

### Phase 2: Azure Function Deployment
- [ ] Create Azure Function App
- [ ] Deploy webhook receiver function
- [ ] Configure environment variables
- [ ] Test signature verification
- [ ] Test transcript storage to Azure Blob

### Phase 3: Streamlit Integration
- [ ] Create Plaud Transcripts page
- [ ] Implement pending transcript queue
- [ ] Build patient matching UI
- [ ] Add matched transcripts to patient records
- [ ] Create transcript viewer component

### Phase 4: Patient Matching Automation
- [ ] Implement title parsing for patient names
- [ ] Add appointment time matching
- [ ] Build confidence scoring for matches
- [ ] Create manual override workflow

---

## Security Considerations

1. **Webhook Verification**: Always verify `Plaud-Signature` header
2. **Domain Filtering**: Only process webhooks from @greenclinicteam.com users
3. **HIPAA Compliance**: 
   - Plaud is HIPAA compliant
   - Azure Blob Storage with encryption
   - No PHI in logs
4. **Access Control**: Only authenticated users can view/match transcripts

---

## References

- [Plaud Developer Documentation](https://docs.plaud.ai/)
- [Plaud Webhook Events Guide](https://docs.plaud.ai/documentation/developer_guides/webhook_events)
- [Plaud API Authorization](https://docs.plaud.ai/api_guide/api_intro/authorization)
- [Plaud Developer Platform Announcement](https://www.plaud.ai/blogs/news/plaud-developer-platform)

---

*Document Version: 1.0*  
*Created: December 8, 2025*  
*Status: Design complete, awaiting Plaud developer access*
