# Story S6: OneNote Integration

**Epic:** Data Integration
**Priority:** HIGH
**Points:** 13
**Sprint:** Dec 9-15, 2025
**Depends On:** S5 (Microsoft OAuth)

---

## User Story

**As a** provider
**I want to** access patient worksheets from Green Clinic Team Notebook
**So that** I can review patient history and build care plans

---

## Acceptance Criteria

### AC1: Notebook Discovery
- [ ] App finds "Green Clinic Team Notebook" after login
- [ ] Lists all sections in the notebook
- [ ] Shows page count per section
- [ ] Handles case where notebook not accessible

### AC2: Section Navigation
- [ ] Can browse sections (likely organized by patient/date)
- [ ] Section list shows last modified date
- [ ] Can search for specific section by name

### AC3: Page Content Display
- [ ] Can view page content in app
- [ ] Renders HTML content from OneNote
- [ ] Handles images, tables, embedded content
- [ ] Shows page title and last modified

### AC4: Patient Matching
- [ ] Can link OneNote page to patient record
- [ ] Searches patient by name/MRN in page title
- [ ] Stores link in database for future reference

### AC5: Content Extraction
- [ ] Extracts text content for AI processing
- [ ] Handles common worksheet formats
- [ ] Preserves structure (headers, lists, tables)

---

## Technical Tasks

### Task 1: OneNoteClient Class
```python
# app/onenote_client.py
class OneNoteClient:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://graph.microsoft.com/v1.0/me/onenote"

    def list_notebooks(self) -> List[dict]:
        # GET /me/onenote/notebooks
        pass

    def find_green_clinic_notebook(self) -> Optional[dict]:
        # Find notebook by name
        pass

    def list_sections(self, notebook_id: str) -> List[dict]:
        # GET /notebooks/{id}/sections
        pass

    def list_pages(self, section_id: str) -> List[dict]:
        # GET /sections/{id}/pages
        pass

    def get_page_content(self, page_id: str) -> str:
        # GET /pages/{id}/content (returns HTML)
        pass
```

### Task 2: Streamlit OneNote Page
```python
# app/pages/X_OneNote_Browser.py
import streamlit as st
from onenote_client import OneNoteClient

st.title("OneNote Browser")

# Requires MS OAuth token
if "ms_token" not in st.session_state:
    st.warning("Please sign in with Microsoft first")
    st.stop()

client = OneNoteClient(st.session_state["ms_token"])

# Notebook selection
notebooks = client.list_notebooks()
selected = st.selectbox("Select Notebook", notebooks)

# Section list
if selected:
    sections = client.list_sections(selected["id"])
    for section in sections:
        with st.expander(section["displayName"]):
            pages = client.list_pages(section["id"])
            for page in pages:
                if st.button(page["title"], key=page["id"]):
                    content = client.get_page_content(page["id"])
                    st.html(content)
```

### Task 3: Content Parser
```python
# app/onenote_parser.py
from bs4 import BeautifulSoup

class OneNoteParser:
    def __init__(self, html_content: str):
        self.soup = BeautifulSoup(html_content, 'html.parser')

    def get_text(self) -> str:
        # Extract plain text
        pass

    def get_structured_content(self) -> dict:
        # Extract headers, lists, tables
        pass

    def extract_patient_info(self) -> dict:
        # Parse common worksheet patterns
        # Returns: name, DOB, chief complaint, etc.
        pass
```

### Task 4: Patient Linking
- [ ] Add OneNote page reference to Patient model
- [ ] UI for linking page to patient
- [ ] Search patients when viewing page
- [ ] Store mapping in database

### Task 5: Azure Claude Integration
```python
# Process OneNote content with AI
from azure_claude import AzureClaudeClient

async def analyze_worksheet(page_content: str) -> dict:
    client = AzureClaudeClient()
    prompt = f"""
    Analyze this patient worksheet and extract:
    - Patient demographics
    - Chief complaint
    - History of present illness
    - Current medications
    - Assessment and plan

    Worksheet content:
    {page_content}
    """
    return await client.generate(prompt)
```

---

## API Reference

### List Notebooks
```
GET https://graph.microsoft.com/v1.0/me/onenote/notebooks
Authorization: Bearer {token}
```

### List Sections
```
GET https://graph.microsoft.com/v1.0/me/onenote/notebooks/{id}/sections
```

### List Pages
```
GET https://graph.microsoft.com/v1.0/me/onenote/sections/{id}/pages
```

### Get Page Content
```
GET https://graph.microsoft.com/v1.0/me/onenote/pages/{id}/content
Accept: text/html
```

---

## Dependencies

- S5: Microsoft OAuth Integration (completed)
- BeautifulSoup4 (`pip install beautifulsoup4`)
- Microsoft Graph API permissions (Notes.Read, Notes.Read.All)

---

## Definition of Done

- [ ] Can browse Green Clinic Team Notebook
- [ ] Can view page content in app
- [ ] Can extract text for AI processing
- [ ] Can link pages to patient records
- [ ] Error handling for API failures
- [ ] Manual testing with real notebook

---

## Notes

- Green Clinic Team Notebook is on SharePoint (southviewteam.com)
- Access via user's delegated permissions
- Content is HTML - may need sanitization before display
- Large notebooks may need pagination

---

## Worksheet Patterns to Handle

Based on historical usage, worksheets may contain:
- Patient name in title
- Visit date
- Chief complaint
- Vitals
- Assessment notes
- Plan items
- Follow-up instructions

AI parsing should handle variations in format.

---

*Created: 2025-12-02*
