"""Add Data - Upload documents, paste screenshots, or import from OneNote.

Central data ingestion page for Patient Explorer. Supports:
- Document upload with Azure Blob Storage backup
- Screenshot paste with AI-powered extraction
- OneNote notebook selection and import
- OCR text extraction from images
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys
import base64
from io import BytesIO

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_session, init_db
from database.models import Patient, Consent, ConsentStatus

# Import paste button component
from streamlit_paste_button import paste_image_button

st.set_page_config(
    page_title="Add Data - Patient Explorer",
    page_icon="📥",
    layout="wide",
)

# Initialize database
init_db()

# Import auth after database init
from auth import require_login, require_permission, has_permission, show_user_menu

# Require login and scanner permission
user = require_login()
require_permission("use_scanner")
show_user_menu()

st.title("📥 Add Data")
st.markdown("Upload documents, paste screenshots, or import from OneNote to add patient data.")
st.divider()


def pil_to_bytes(pil_image) -> bytes:
    """Convert PIL image to bytes."""
    buffer = BytesIO()
    pil_image.save(buffer, format="PNG")
    return buffer.getvalue()


# Initialize session state
if "add_data_messages" not in st.session_state:
    st.session_state.add_data_messages = []

if "add_data_images" not in st.session_state:
    st.session_state.add_data_images = []

if "add_data_last_paste_id" not in st.session_state:
    st.session_state.add_data_last_paste_id = None

if "add_data_processed_uploads" not in st.session_state:
    st.session_state.add_data_processed_uploads = set()

if "add_data_extracted_data" not in st.session_state:
    st.session_state.add_data_extracted_data = {}

if "selected_notebook" not in st.session_state:
    st.session_state.selected_notebook = None

if "selected_sections" not in st.session_state:
    st.session_state.selected_sections = []


# =============================================================================
# Sidebar - Services Status & Settings
# =============================================================================

with st.sidebar:
    st.subheader("🔌 Services Status")

    # Check Document Intelligence
    doc_available = False
    try:
        from azure_document import DocumentClient
        doc_client = DocumentClient()
        st.success("✅ Azure Document Intelligence")
        doc_available = True
    except Exception as e:
        st.warning(f"⚠️ Document Intelligence")
        st.caption(str(e)[:50])

    # Check Claude AI
    ai_available = False
    try:
        from azure_claude import AzureClaudeClient
        ai_client = AzureClaudeClient()
        st.success("✅ Azure Claude AI")
        ai_client.close()
        ai_available = True
    except Exception as e:
        st.warning(f"⚠️ Claude AI")
        st.caption(str(e)[:50])

    # Check Microsoft OAuth
    ms_available = False
    try:
        from ms_oauth import is_user_authenticated, get_ms_user, show_ms_login_button, handle_oauth_callback
        # Handle any OAuth callback
        handle_oauth_callback()
        if is_user_authenticated():
            ms_user = get_ms_user()
            st.success(f"✅ Microsoft 365")
            st.caption(f"Signed in as {ms_user.get('display_name', 'User')}")
            ms_available = True
        else:
            st.info("🔐 Microsoft 365 - Sign in required")
    except Exception as e:
        st.warning("⚠️ Microsoft 365")
        st.caption(str(e)[:50])

    st.divider()

    # Settings
    st.subheader("⚙️ Settings")

    model_choice = st.selectbox(
        "AI Model",
        [("Haiku (Fast)", "haiku"), ("Sonnet (Balanced)", "sonnet")],
        format_func=lambda x: x[0]
    )[1]

    auto_ocr = st.checkbox("Auto-extract text from images", value=True)

    st.divider()

    # Data extraction targets
    st.subheader("📊 Extraction Targets")

    extraction_targets = st.multiselect(
        "What to extract",
        [
            "Patient Demographics",
            "Insurance Information",
            "Medications",
            "Diagnoses/Conditions",
            "Vital Signs",
            "Lab Results",
            "Visit Notes",
            "Consent Elections",
        ],
        default=["Patient Demographics"]
    )

    st.divider()

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.add_data_messages = []
        st.session_state.add_data_images = []
        st.session_state.add_data_last_paste_id = None
        st.session_state.add_data_processed_uploads = set()
        st.session_state.add_data_extracted_data = {}
        st.rerun()


# =============================================================================
# Main Content - Tabbed Interface
# =============================================================================

tabs = st.tabs(["📋 Upload & Paste", "📓 OneNote Import", "💬 AI Chat", "📊 Extracted Data"])


# =============================================================================
# Tab 1: Upload & Paste Documents
# =============================================================================

with tabs[0]:
    st.subheader("Upload Documents or Paste Screenshots")

    st.markdown("""
    Add patient data by uploading documents or pasting screenshots from your EMR.
    The AI will help extract patient information automatically.
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📋 Paste from Clipboard**")
        st.caption("Copy an image (Ctrl+C), then click below")

        paste_result = paste_image_button(
            label="📋 Click to Paste Screenshot",
            key="add_data_paste_btn",
        )

        if paste_result.image_data is not None:
            img_bytes = pil_to_bytes(paste_result.image_data)
            paste_id = hash(img_bytes[:100])
            if paste_id != st.session_state.add_data_last_paste_id:
                st.session_state.add_data_last_paste_id = paste_id
                st.session_state.add_data_images.append({
                    "bytes": img_bytes,
                    "name": f"Screenshot_{datetime.now().strftime('%H%M%S')}"
                })
                st.rerun()

    with col2:
        st.markdown("**📁 Upload Files**")
        st.caption("PDF, PNG, JPG, or TIFF files")

        uploads = st.file_uploader(
            "Upload Documents",
            type=["png", "jpg", "jpeg", "pdf", "tiff", "bmp"],
            accept_multiple_files=True,
            key="add_data_upload_btn",
            label_visibility="collapsed"
        )
        if uploads:
            for f in uploads:
                fid = f"{f.name}_{f.size}"
                if fid not in st.session_state.add_data_processed_uploads:
                    st.session_state.add_data_processed_uploads.add(fid)
                    st.session_state.add_data_images.append({
                        "bytes": f.read(),
                        "name": f.name
                    })
            st.rerun()

    # Show attached documents
    if st.session_state.add_data_images:
        st.divider()
        st.markdown(f"**📎 {len(st.session_state.add_data_images)} document(s) ready:**")

        img_cols = st.columns(min(len(st.session_state.add_data_images), 4))
        for i, img in enumerate(st.session_state.add_data_images):
            with img_cols[i % 4]:
                st.image(img["bytes"], caption=img.get("name", f"Doc {i+1}"), width=150)
                if st.button("❌ Remove", key=f"rm_doc_{i}"):
                    st.session_state.add_data_images.pop(i)
                    st.rerun()

        st.divider()

        # Quick actions
        st.markdown("**Quick Actions:**")
        action_cols = st.columns(4)

        with action_cols[0]:
            if st.button("🔍 Run OCR Only", use_container_width=True):
                if doc_available:
                    with st.spinner("Extracting text..."):
                        try:
                            from azure_document import DocumentClient
                            client = DocumentClient()
                            all_text = []

                            for img in st.session_state.add_data_images:
                                result = client.analyze_document(img["bytes"], "prebuilt-read")
                                all_text.append(f"**{img.get('name', 'Document')}:**\n{result.content}")

                            st.session_state.add_data_messages.append({
                                "role": "assistant",
                                "content": "**OCR Extracted Text:**\n\n" + "\n\n---\n\n".join(all_text)
                            })
                            st.success("Text extracted! See AI Chat tab.")
                        except Exception as e:
                            st.error(f"OCR Error: {e}")
                else:
                    st.error("Document Intelligence not available")

        with action_cols[1]:
            if st.button("🧠 Extract with AI", use_container_width=True, type="primary"):
                # Navigate to AI Chat tab with extraction prompt
                st.session_state.add_data_messages.append({
                    "role": "user",
                    "content": "Extract all patient information from these documents and organize it clearly.",
                    "images": st.session_state.add_data_images.copy()
                })
                st.info("Processing... Switch to AI Chat tab to see results.")
                st.rerun()

        with action_cols[2]:
            if st.button("💾 Save to Azure", use_container_width=True):
                st.info("Azure Blob Storage upload coming soon...")

        with action_cols[3]:
            if st.button("🗑️ Clear All", use_container_width=True):
                st.session_state.add_data_images = []
                st.session_state.add_data_processed_uploads = set()
                st.rerun()

    else:
        st.info("""
        **How to add documents:**

        1. **Paste**: Copy an image from your EMR (Ctrl+C), then click the paste button
        2. **Upload**: Drag files or click to upload PDFs, images, or scanned documents

        **Supported document types:**
        - Screenshots from EMR systems (eClinicalWorks, Epic, etc.)
        - Scanned patient forms
        - Insurance cards
        - Lab results and reports
        - Any text-containing images

        Documents will be processed with OCR and AI to extract patient data automatically.
        """)


# =============================================================================
# Tab 2: OneNote Import
# =============================================================================

with tabs[1]:
    st.subheader("Import from OneNote")

    st.markdown("""
    Connect to your Microsoft 365 account to import patient notes from OneNote notebooks.
    Select specific sections or section groups to import.
    """)

    if not ms_available:
        st.warning("Sign in to Microsoft 365 to access OneNote notebooks.")

        try:
            from ms_oauth import show_ms_login_button
            show_ms_login_button()
        except Exception as e:
            st.error(f"Microsoft OAuth not configured: {e}")
            st.caption("Set AZURE_CLIENT_ID and AZURE_TENANT_ID in .env")
    else:
        # User is authenticated - show notebook selector
        try:
            from ms_oauth import get_user_graph_client

            client = get_user_graph_client()
            if client:
                # Fetch notebooks
                with st.spinner("Loading OneNote notebooks..."):
                    notebooks = client.list_notebooks()

                if notebooks:
                    st.markdown("### Select Notebook")

                    notebook_options = [(None, "-- Select a Notebook --")] + [
                        (nb["id"], nb["displayName"])
                        for nb in notebooks
                    ]

                    selected_nb = st.selectbox(
                        "Notebook",
                        notebook_options,
                        format_func=lambda x: x[1],
                        key="onenote_notebook_select"
                    )

                    if selected_nb and selected_nb[0]:
                        st.session_state.selected_notebook = selected_nb

                        # Fetch sections for selected notebook
                        with st.spinner("Loading sections..."):
                            sections = client.list_notebook_sections(selected_nb[0])

                        if sections:
                            st.markdown("### Select Sections to Import")

                            # Multi-select for sections
                            section_options = [
                                (s["id"], s["displayName"])
                                for s in sections
                            ]

                            selected_secs = st.multiselect(
                                "Sections",
                                section_options,
                                format_func=lambda x: x[1],
                                key="onenote_sections_select"
                            )

                            st.session_state.selected_sections = selected_secs

                            if selected_secs:
                                st.success(f"Selected {len(selected_secs)} section(s)")

                                # Preview section contents
                                with st.expander("Preview Section Pages"):
                                    for sec_id, sec_name in selected_secs:
                                        st.markdown(f"**{sec_name}:**")
                                        try:
                                            pages = client.list_section_pages(sec_id)
                                            for page in pages[:5]:  # Show first 5 pages
                                                st.caption(f"- {page.get('title', 'Untitled')}")
                                            if len(pages) > 5:
                                                st.caption(f"  ...and {len(pages) - 5} more pages")
                                        except Exception as e:
                                            st.caption(f"Error loading pages: {e}")

                                st.divider()

                                col1, col2 = st.columns(2)

                                with col1:
                                    if st.button("📥 Import Selected Sections", type="primary", use_container_width=True):
                                        with st.spinner("Importing from OneNote..."):
                                            imported_count = 0
                                            for sec_id, sec_name in selected_secs:
                                                try:
                                                    pages = client.list_section_pages(sec_id)
                                                    for page in pages:
                                                        try:
                                                            content = client.get_page_content(page["id"])
                                                            # Store for processing
                                                            st.session_state.add_data_messages.append({
                                                                "role": "system",
                                                                "content": f"**Imported from OneNote: {sec_name} / {page.get('title', 'Untitled')}**\n\n{content[:2000]}..."
                                                            })
                                                            imported_count += 1
                                                        except Exception as e:
                                                            st.warning(f"Could not import page: {e}")
                                                except Exception as e:
                                                    st.error(f"Error importing section {sec_name}: {e}")

                                            st.success(f"Imported {imported_count} pages! See AI Chat tab.")

                                with col2:
                                    if st.button("🔍 Extract Patient Data", use_container_width=True):
                                        st.info("Import sections first, then use AI Chat to extract data.")
                        else:
                            st.info("No sections found in this notebook.")
                else:
                    st.info("No OneNote notebooks found. Create a notebook in OneNote first.")

                client.close()
            else:
                st.error("Could not connect to Microsoft Graph")

        except Exception as e:
            st.error(f"Error accessing OneNote: {e}")
            st.caption("You may need to sign in again.")


# =============================================================================
# Tab 3: AI Chat Interface
# =============================================================================

with tabs[2]:
    st.subheader("AI-Powered Data Extraction")

    # Display chat history
    for msg in st.session_state.add_data_messages:
        if msg["role"] == "system":
            with st.expander(f"📓 {msg['content'][:50]}..."):
                st.markdown(msg["content"])
        else:
            with st.chat_message(msg["role"]):
                if msg.get("images"):
                    img_cols = st.columns(min(len(msg["images"]), 3))
                    for i, img in enumerate(msg["images"]):
                        with img_cols[i % 3]:
                            st.image(img["bytes"], width=100)
                if msg.get("content"):
                    st.markdown(msg["content"])

    # Chat input
    st.markdown("---")
    st.markdown("**Chat with AI about your documents:**")

    user_input = st.chat_input("Tell the AI what to extract (e.g., 'Find all medications listed')...")

    if user_input:
        # Add user message
        user_msg = {
            "role": "user",
            "content": user_input,
            "images": st.session_state.add_data_images.copy() if st.session_state.add_data_images else [],
        }
        st.session_state.add_data_messages.append(user_msg)

        # Process with AI
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                try:
                    extracted_texts = []

                    # OCR if enabled and images present
                    if auto_ocr and st.session_state.add_data_images and doc_available:
                        from azure_document import DocumentClient
                        doc_client = DocumentClient()

                        for i, img in enumerate(st.session_state.add_data_images):
                            try:
                                result = doc_client.analyze_document(img["bytes"], "prebuilt-read")
                                if result.content:
                                    img_name = img.get("name", f"Image {i+1}")
                                    extracted_texts.append(f"**{img_name}:**\n{result.content}")
                            except Exception as e:
                                extracted_texts.append(f"**Image {i+1}:** [OCR failed: {e}]")

                    # Build system prompt based on extraction targets
                    target_instructions = ""
                    if extraction_targets:
                        target_instructions = f"""
Focus on extracting the following types of information:
{chr(10).join(f'- {t}' for t in extraction_targets)}

Format extracted data clearly with labels. If information is not found, indicate "Not found" rather than guessing.
"""

                    system_prompt = f"""You are a medical data extraction assistant for Patient Explorer.
Your job is to help clinical staff extract and organize patient information from documents.

{target_instructions}

Guidelines:
- Be precise and accurate - this is medical data
- Maintain HIPAA compliance awareness
- Structure data clearly for easy entry into the system
- Ask clarifying questions if documents are unclear
- Flag any concerning or inconsistent information
- When extracting dates, use YYYY-MM-DD format
- When extracting phone numbers, use (XXX) XXX-XXXX format
"""

                    # Build prompt
                    prompt = f"User request: {user_input}\n\n"
                    if extracted_texts:
                        prompt += "Document text extracted via OCR:\n\n" + "\n\n---\n\n".join(extracted_texts)
                    elif st.session_state.add_data_messages:
                        # Include any OneNote imports
                        onenote_content = [m["content"] for m in st.session_state.add_data_messages if m["role"] == "system"]
                        if onenote_content:
                            prompt += "OneNote imported content:\n\n" + "\n\n---\n\n".join(onenote_content)
                    else:
                        prompt += "[No documents attached - please upload or paste documents first]"

                    # Send to Claude
                    if ai_available:
                        from azure_claude import AzureClaudeClient, ModelTier
                        model_map = {"haiku": ModelTier.HAIKU, "sonnet": ModelTier.SONNET}

                        client = AzureClaudeClient()
                        response = client.send_message(
                            prompt,
                            model=model_map[model_choice],
                            system_prompt=system_prompt,
                            max_tokens=3000
                        )
                        client.close()

                        st.markdown(response.content)
                        st.caption(f"Model: {model_choice} | Tokens: {response.input_tokens} in, {response.output_tokens} out")

                        st.session_state.add_data_messages.append({
                            "role": "assistant",
                            "content": response.content
                        })
                    else:
                        # Fallback: just show extracted text
                        if extracted_texts:
                            output = "**Extracted Text (AI unavailable):**\n\n" + "\n\n".join(extracted_texts)
                            st.markdown(output)
                            st.session_state.add_data_messages.append({
                                "role": "assistant",
                                "content": output
                            })
                        else:
                            st.warning("No AI or OCR available to process documents.")

                except Exception as e:
                    st.error(f"Error processing: {e}")

        # Clear images after processing
        st.session_state.add_data_images = []
        st.rerun()

    # Quick action prompts
    if st.session_state.add_data_images or st.session_state.add_data_messages:
        st.markdown("---")
        st.markdown("**Quick Prompts:**")
        prompt_cols = st.columns(4)

        quick_prompts = [
            ("📋 Extract All", "Extract all patient information from these documents and organize it clearly."),
            ("🏥 Demographics", "Extract patient demographics: name, DOB, address, phone, email, MRN if present."),
            ("💊 Medications", "List all medications mentioned with dosages and frequencies."),
            ("📝 Summarize", "Provide a brief clinical summary of these documents."),
        ]

        for col, (label, prompt) in zip(prompt_cols, quick_prompts):
            with col:
                if st.button(label, use_container_width=True):
                    st.session_state.add_data_messages.append({
                        "role": "user",
                        "content": prompt,
                        "images": st.session_state.add_data_images.copy()
                    })
                    st.session_state.add_data_images = []
                    st.rerun()


# =============================================================================
# Tab 4: Extracted Data Review
# =============================================================================

with tabs[3]:
    st.subheader("Review Extracted Data")

    if st.session_state.add_data_extracted_data:
        for category, data in st.session_state.add_data_extracted_data.items():
            with st.expander(f"**{category}**", expanded=True):
                if isinstance(data, dict):
                    for k, v in data.items():
                        st.text_input(k, value=v, key=f"extract_{category}_{k}")
                else:
                    st.text_area(category, value=str(data), key=f"extract_{category}")

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Save to Patient Record", type="primary", use_container_width=True):
                st.info("Patient matching and data save coming soon...")

        with col2:
            if st.button("☁️ Upload to Azure", use_container_width=True):
                st.info("Azure Blob Storage upload coming soon...")

    else:
        st.info("""
        **How to populate extracted data:**

        1. Go to **Upload & Paste** tab and add documents
        2. Use **AI Chat** tab to ask AI to extract specific information
        3. Review and edit the extracted data here
        4. Save to patient records or upload to Azure

        **Example workflow:**
        - Upload a screenshot of patient demographics from your EMR
        - Ask AI: "Extract patient name, DOB, phone, and address"
        - Review the extracted data
        - Save to the patient's record
        """)

    st.divider()

    # Link to patient
    st.subheader("🔗 Link to Patient")

    session = get_session()
    try:
        patients = session.query(Patient).order_by(Patient.last_name).limit(50).all()

        if patients:
            patient_options = [(0, "-- Select Patient (or create new) --")] + [
                (p.id, f"{p.last_name}, {p.first_name} ({p.mrn})")
                for p in patients
            ]

            selected_patient = st.selectbox(
                "Select Patient",
                patient_options,
                format_func=lambda x: x[1],
                key="add_data_patient_link"
            )

            if selected_patient and selected_patient[0] != 0:
                st.success(f"Ready to link data to patient ID {selected_patient[0]}")

                if st.button("📥 Import Extracted Data to Patient", use_container_width=True):
                    st.info("Data import functionality coming soon...")

            st.caption("Or create a new patient from the extracted data:")
            if st.button("➕ Create New Patient", use_container_width=True):
                st.info("New patient creation from extracted data coming soon...")

        else:
            st.info("No patients in database yet. Use Patient List to add patients, or create from extracted data.")

    finally:
        session.close()


# =============================================================================
# Footer
# =============================================================================

st.divider()
st.caption("""
**Add Data** - Central data ingestion for Patient Explorer

- **Upload & Paste**: Add documents from your computer or paste screenshots
- **OneNote Import**: Connect to Microsoft 365 and import from OneNote notebooks
- **AI Chat**: Ask the AI to extract specific patient information
- **Extracted Data**: Review and save extracted data to patient records
""")
