# OpenEvidence UI/UX Patterns Analysis

**Date:** 2025-12-02
**Status:** Research Complete
**Purpose:** Inform Patient Explorer clinical UI design

---

## Executive Summary

OpenEvidence is a leading medical AI platform integrating content from NEJM, JAMA, and NCCN Guidelines. Their interface provides a model for how to present medical-grade AI assistance to clinicians.

---

## Key Clinical Features

### 1. Medical Content Integration
- Integrates NEJM, JAMA Network, NCCN Guidelines
- Multimedia and clinical findings aggregation
- Evidence-based responses grounded in peer-reviewed literature

### 2. Provider Verification
- Access restricted to verified U.S. healthcare providers
- Mobile apps (iOS/Android) for authenticated clinicians
- Free access model for qualified users

### 3. Trusted Partners
- NCCN (National Comprehensive Cancer Network)
- ACC (American College of Cardiology)
- ADA (American Diabetes Association)
- AAFP (American Academy of Family Physicians)
- AAOS, AAO-HNS, ACEP

---

## UI/UX Design Patterns

### 1. Navigation & Layout

**Sticky Header Navigation**
- Persistent access to tools (scroll-margin-top: 65px)
- Quick access to search/query functions
- User account/logout always visible

**Responsive Grid Layouts**
- 1-column on mobile
- 2-column on desktop (900px+ breakpoints)
- Query bar constrained to 768px max-width for readability

### 2. Input Components

**Query Interface**
- Central query bar for clinical questions
- Floating labels with validation states
- Clear call-to-action for submitting questions

**Chat-Style Interaction**
- Conversational AI interface
- Previous queries accessible
- Context preserved across questions

### 3. Visual Hierarchy

**Button Patterns**
- Primary: Filled orange/red (#e4643d) for main actions
- Secondary: Outlined for alternative actions
- Tertiary: Text-only for less important actions

**Information Architecture**
- Evidence sources prominently displayed
- Citations linked to original publications
- Confidence indicators for AI responses

### 4. Credibility Signals

**Trust Indicators**
- Partnership logos displayed prominently
- "Backed by Sequoia, Google Ventures, Kleiner Perkins"
- Content agreements with premium medical journals
- Clear disclaimers about AI limitations

---

## Technical Architecture (Observed)

### Frontend Stack
- **Framework:** Next.js (observed `/_next/image` paths)
- **Styling:** Material Design (MUI) components
- **State:** localStorage for preferences/theme

### Feature Management
- Waffle flags system for A/B testing and feature rollouts
- Server-side attachment handling
- Subscription/team management logic

### Authentication Flow
- Log In / Sign Up entry points in header
- Subscription validation (personal, team, free tier)
- Regional gating (Australia, UAE detection)

---

## Patterns to Adopt for Patient Explorer

### 1. Clinical Query Interface

**Recommendation:** Add a clinical AI assistant page with:
- Central query input for patient-specific questions
- Context awareness (current patient selected)
- Evidence-based response formatting

**Implementation:**
```python
# Streamlit implementation concept
st.text_input("Ask about this patient...", key="clinical_query")
if st.button("Ask AI Assistant"):
    response = azure_claude.query(
        patient_context=current_patient,
        question=st.session_state.clinical_query,
        guidelines=["AAFP", "ADA"]  # Relevant guidelines
    )
    st.markdown(response.answer)
    st.caption(f"Sources: {response.citations}")
```

### 2. Evidence Display Pattern

**Recommendation:** When AI provides recommendations, show:
- Primary answer in clear language
- Supporting evidence with citations
- Confidence level indicator
- Link to original sources

**Visual Format:**
```
[AI Response]
Based on current guidelines...

[Evidence Panel]
- AAFP Guidelines 2024: "..."
- ADA Standards of Care: "..."

[Confidence: High] [Sources: 3 guidelines]
```

### 3. Sticky Navigation for Clinical Workflow

**Recommendation:** Persistent navigation showing:
- Current patient context
- Quick actions (Notes, Orders, Messages)
- AI assistant trigger

### 4. Mobile-First Design

**Recommendation:** Ensure Streamlit pages work on mobile:
- Single-column layouts for small screens
- Touch-friendly buttons (44px minimum)
- Simplified navigation on mobile

### 5. Ambient Recording Interface (Future)

**OpenEvidence Feature:** Voice-to-note transcription

**Future Implementation for Patient Explorer:**
- Browser audio recording via Web Audio API
- Azure Speech-to-Text for transcription
- Azure Claude for clinical note structuring
- SOAP note generation from transcription

---

## Ambient Recording Technical Approach

### Phase 1: Browser-Based Recording
```javascript
// Web Audio API for browser recording
navigator.mediaDevices.getUserMedia({ audio: true })
  .then(stream => {
    const mediaRecorder = new MediaRecorder(stream);
    // Record audio chunks
  });
```

### Phase 2: Azure Speech Services
```python
# Azure Speech-to-Text
import azure.cognitiveservices.speech as speechsdk

speech_config = speechsdk.SpeechConfig(
    subscription=os.environ.get("AZURE_SPEECH_KEY"),
    region="eastus"
)
# Continuous recognition for medical conversation
```

### Phase 3: Clinical Note Generation
```python
# Azure Claude for SOAP note generation
prompt = f"""
Transcription: {transcription}
Patient Context: {patient_summary}

Generate a SOAP note from this clinical encounter.
"""
response = azure_claude.generate(prompt)
```

---

## Design System Recommendations

### Color Palette
| Use | Color | Hex |
|-----|-------|-----|
| Primary Action | Orange/Red | #e4643d |
| Success/Consent | Green | #28a745 |
| Warning/Pending | Yellow | #ffc107 |
| Danger/Declined | Red | #dc3545 |
| Info/Neutral | Blue | #17a2b8 |

### Typography
- Headers: System font (SF Pro, Segoe UI)
- Body: 16px base, 1.5 line height
- Code/Data: Monospace for MRNs, codes

### Spacing
- Base unit: 8px
- Consistent padding: 16px, 24px, 32px
- Card margin: 16px between sections

---

## Streamlit Theming

### Custom Theme (`.streamlit/config.toml`)
```toml
[theme]
primaryColor = "#e4643d"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

---

## Implementation Priority

### Phase 1 (Consent Outreach - Current)
- Simple, clean consent tracking UI
- Clear status indicators
- Mobile-responsive design

### Phase 2 (Chart Builder - January 2025)
- Clinical query interface
- Evidence display patterns
- OneNote integration

### Phase 3 (Full Clinical Support - Q2 2025)
- Ambient recording
- KP agent integration
- OpenEvidence-style AI assistant

---

## References

- [OpenEvidence.com](https://openevidence.com)
- Material Design Guidelines
- WCAG 2.1 Accessibility Standards
- HIPAA UI/UX Best Practices

---

*Generated: 2025-12-02 by BMAD Research Agent*
