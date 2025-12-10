"""AutoScribe Page - Medical note creation with audio capture and AI summarization.

This page provides:
- Rich text input with screenshot paste support
- Audio recording with device selection
- AI-powered note generation (SBAR, Office Note, Video Note)
- Custom prompt support
- HIPAA audit logging
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
import sys
import base64
import tempfile
from typing import Optional

# Clipboard paste support for images
try:
    from streamlit_paste_button import paste_image_button
    PASTE_BUTTON_AVAILABLE = True
except ImportError:
    PASTE_BUTTON_AVAILABLE = False

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_session, init_db
from database.models import User, Patient, PatientNote, AuditLog

st.set_page_config(
    page_title="AutoScribe - Patient Explorer",
    page_icon="📝",
    layout="wide",
)

# Initialize database
init_db()

# Import auth after database init
from auth import require_login, require_permission, show_user_menu

# Require login
user = require_login()
show_user_menu()

# Import autoscribe modules
try:
    from autoscribe.prompt_manager import get_prompt_manager, PromptType
    from autoscribe.audit import get_audit_logger, AuditEvent
    from components.user_banner import show_user_banner, init_session_tracking, get_user_id
except ImportError as e:
    st.error(f"Failed to import AutoScribe modules: {e}")
    st.stop()

# Initialize session tracking for audit
session_id = init_session_tracking()
user_id = get_user_id(user)

# Log session start if not already done
if "autoscribe_session_logged" not in st.session_state:
    try:
        audit = get_audit_logger()
        audit.log_session_start(
            user_id=user_id,
            user_email=getattr(user, 'email', None),
            session_id=session_id,
        )
        st.session_state.autoscribe_session_logged = True
    except Exception as e:
        st.warning(f"Could not log session start: {e}")

# Show user banner
show_user_banner(user, show_logout=True)

st.title("📝 AutoScribe")
st.markdown("Create medical notes from text and audio using AI-powered summarization.")

# Initialize session state
if "generated_note" not in st.session_state:
    st.session_state.generated_note = None
if "audio_segments" not in st.session_state:
    st.session_state.audio_segments = []
if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "audio_transcript_preview" not in st.session_state:
    st.session_state.audio_transcript_preview = None

# =============================================================================
# Patient Selection - Top of Page
# =============================================================================
patient_col1, patient_col2 = st.columns([1, 2])

with patient_col1:
    st.markdown("**👤 Patient:**")

with patient_col2:
    db_session = get_session()
    try:
        patients = db_session.query(Patient).order_by(Patient.last_name).all()

        if not patients:
            st.caption("No patients in database")
            selected_patient = None
        else:
            # Search and select in compact row
            search_col, select_col = st.columns([1, 2])

            with search_col:
                patient_search = st.text_input(
                    "Search",
                    "",
                    key="patient_search_autoscribe",
                    placeholder="Search...",
                    label_visibility="collapsed",
                )

            # Filter patients
            if patient_search:
                filtered_patients = [
                    p for p in patients
                    if patient_search.lower() in p.last_name.lower()
                    or patient_search.lower() in p.first_name.lower()
                    or patient_search.lower() in (p.mrn or "").lower()
                ]
            else:
                filtered_patients = patients

            with select_col:
                if filtered_patients:
                    patient_options = [
                        (p.id, f"{p.last_name}, {p.first_name} ({p.mrn})")
                        for p in filtered_patients[:100]
                    ]

                    # Add "No patient" option at the top
                    patient_options_with_none = [(None, "-- Select patient --")] + patient_options

                    selected_patient = st.selectbox(
                        "Patient",
                        patient_options_with_none,
                        format_func=lambda x: x[1],
                        key="selected_patient_autoscribe",
                        label_visibility="collapsed",
                    )

                    # Store in session state for use in save function
                    if selected_patient and selected_patient[0]:
                        st.session_state.autoscribe_patient_id = selected_patient[0]
                        st.session_state.autoscribe_patient_name = selected_patient[1]
                    else:
                        st.session_state.autoscribe_patient_id = None
                        st.session_state.autoscribe_patient_name = None
                else:
                    st.caption("No matching patients")
                    selected_patient = None
                    st.session_state.autoscribe_patient_id = None
                    st.session_state.autoscribe_patient_name = None
    finally:
        db_session.close()

# Show selected patient confirmation
if st.session_state.get("autoscribe_patient_id"):
    st.success(f"✅ Recording for: **{st.session_state.autoscribe_patient_name}**")

st.divider()

# =============================================================================
# Sidebar - Settings Only
# =============================================================================
with st.sidebar:
    st.subheader("⚙️ Settings")

    # Get prompt manager
    prompt_manager = get_prompt_manager()

    # Note type selection
    st.markdown("### 📋 Note Type")

    note_type = st.radio(
        "Select note format",
        ["SBAR", "Office Note", "Video Note", "Custom"],
        horizontal=False,
        label_visibility="collapsed",
    )

    # Map to PromptType
    prompt_type_map = {
        "SBAR": PromptType.SBAR,
        "Office Note": PromptType.OFFICE_NOTE,
        "Video Note": PromptType.VIDEO_NOTE,
        "Custom": PromptType.CUSTOM,
    }
    selected_prompt_type = prompt_type_map[note_type]

    # Custom prompt selection
    custom_prompt_id = None
    if note_type == "Custom":
        user_prompts = prompt_manager.get_user_prompts(user_id)
        if user_prompts:
            prompt_options = [(p.id, p.name) for p in user_prompts]
            selected = st.selectbox(
                "Select custom prompt",
                prompt_options,
                format_func=lambda x: x[1],
            )
            custom_prompt_id = selected[0] if selected else None
        else:
            st.info("No custom prompts yet. Create one below.")

    st.divider()

    # AI Connection Status
    st.subheader("🔌 AI Connection")

    try:
        from autoscribe.azure_openai import AzureOpenAIClient

        with st.spinner("Testing connection..."):
            client = AzureOpenAIClient()
            if client.test_connection():
                st.success("✅ Azure OpenAI Connected")
            else:
                st.error("❌ Connection failed")
            client.close()

    except ValueError as e:
        st.error(f"Configuration error")
        with st.expander("Details"):
            st.code(str(e))
    except ImportError:
        st.warning("OpenAI package not installed")
    except Exception as e:
        st.error(f"Error: {e}")

    st.divider()

    # Create Custom Prompt
    with st.expander("➕ Create Custom Prompt"):
        new_prompt_name = st.text_input("Prompt Name", key="new_prompt_name")
        new_prompt_desc = st.text_input("Description (optional)", key="new_prompt_desc")
        new_prompt_content = st.text_area(
            "Prompt Content",
            height=150,
            placeholder="Enter your custom prompt instructions...",
            key="new_prompt_content",
        )

        if st.button("Save Prompt", use_container_width=True):
            if new_prompt_name and new_prompt_content:
                try:
                    saved = prompt_manager.save_user_prompt(
                        user_id=user_id,
                        name=new_prompt_name,
                        content=new_prompt_content,
                        description=new_prompt_desc or None,
                    )

                    # Log to audit
                    audit = get_audit_logger()
                    audit.log(
                        user_id=user_id,
                        event_type=AuditEvent.PROMPT_CREATED,
                        details={"prompt_name": new_prompt_name, "prompt_id": saved.id},
                        session_id=session_id,
                    )

                    st.success(f"Saved: {new_prompt_name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save: {e}")
            else:
                st.warning("Name and content required")

# =============================================================================
# Main Content
# =============================================================================

# Additional Context Section
st.subheader("📎 Additional Context")

# Text context input - compact
additional_context = st.text_area(
    "Additional context (optional)",
    height=80,
    max_chars=1000000,
    placeholder="Type additional notes, observations, or context that wasn't in the recording...",
    label_visibility="collapsed",
    key="additional_context",
)

# Multi-modal image input section - compact layout
# Initialize session state for images
if "context_images" not in st.session_state:
    st.session_state.context_images = []
if "pasted_images" not in st.session_state:
    st.session_state.pasted_images = []
if "show_camera" not in st.session_state:
    st.session_state.show_camera = False

# Compact attachment row - three buttons side by side
attach_col1, attach_col2, attach_col3 = st.columns(3)

with attach_col1:
    # File upload
    uploaded_files = st.file_uploader(
        "📎 Browse Files",
        type=["png", "jpg", "jpeg", "gif", "bmp", "webp", "pdf", "txt"],
        accept_multiple_files=True,
        help="Upload screenshots, photos, or documents",
        key="file_uploader",
    )

with attach_col2:
    # Camera capture
    camera_image = None
    if st.session_state.show_camera:
        if st.button("❌ Close Camera", key="close_camera", use_container_width=True):
            st.session_state.show_camera = False
            st.rerun()
    else:
        if st.button("📷 Capture with Camera", key="open_camera", help="Open camera to take a photo", use_container_width=True):
            st.session_state.show_camera = True
            st.rerun()

with attach_col3:
    # Screen snip - guides user to use Win+Shift+S first
    pasted_image = None
    if PASTE_BUTTON_AVAILABLE:
        st.caption("1. Press **Win+Shift+S** to snip")
        pasted_image = paste_image_button(
            label="2. Click to Paste Snip",
            text_color="#ffffff",
            background_color="#2196F3",
            hover_background_color="#1976D2",
            key="paste_button",
        )
        if pasted_image and pasted_image.image_data:
            if pasted_image not in st.session_state.pasted_images:
                st.session_state.pasted_images.append(pasted_image)
                st.rerun()
    else:
        st.caption("Screen snip: **Win+Shift+S**")
        if st.button("📋 Paste from Clipboard", key="screenshot_btn", help="After snipping, click to paste", use_container_width=True):
            st.info("Press **Win+Shift+S** first, select area, then **Ctrl+V** here")

# Show camera input if enabled (compact)
if st.session_state.show_camera:
    camera_image = st.camera_input(
        "Point camera and click to capture",
        help="Click the camera button to capture",
        key="camera_input",
    )

# Show pasted image preview immediately after capture
if st.session_state.pasted_images:
    st.markdown("**📷 Snipped Images:**")
    snip_cols = st.columns(min(len(st.session_state.pasted_images), 4))
    for idx, pasted in enumerate(st.session_state.pasted_images):
        if pasted and pasted.image_data:
            with snip_cols[idx % 4]:
                st.image(pasted.image_data, caption=f"Snip {idx + 1}", use_container_width=True)
    if st.button("🗑️ Clear snipped images", key="clear_snips"):
        st.session_state.pasted_images = []
        st.rerun()

# Process and display all images
all_images = []

if uploaded_files:
    for f in uploaded_files:
        all_images.append({"name": f.name, "data": f, "source": "upload"})

if camera_image:
    all_images.append({"name": "camera_capture.jpg", "data": camera_image, "source": "camera"})

# Add pasted images
for idx, pasted in enumerate(st.session_state.pasted_images):
    if pasted and pasted.image_data:
        all_images.append({
            "name": f"pasted_image_{idx + 1}.png",
            "data": pasted.image_data,
            "source": "clipboard"
        })

# Display image previews
if all_images:
    st.markdown(f"**{len(all_images)} image(s) attached:**")
    preview_cols = st.columns(min(len(all_images), 4))
    for idx, img in enumerate(all_images):
        col_idx = idx % 4
        with preview_cols[col_idx]:
            # Check if it's an image based on type or extension
            is_image = False
            if img["source"] == "clipboard":
                is_image = True
            elif hasattr(img["data"], 'type') and img["data"].type.startswith("image/"):
                is_image = True
            elif img["name"].lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                is_image = True

            if is_image:
                st.image(img["data"], caption=img["name"][:20], use_container_width=True)
            else:
                size_kb = img["data"].size / 1024 if hasattr(img["data"], 'size') else 0
                st.caption(f"📄 {img['name']} ({size_kb:.1f} KB)")

    # Clear pasted images button
    if st.session_state.pasted_images:
        if st.button("🗑️ Clear pasted images", key="clear_pasted"):
            st.session_state.pasted_images = []
            st.rerun()

    # Store in session state for later processing
    st.session_state.context_images = all_images
else:
    st.session_state.context_images = []
    if PASTE_BUTTON_AVAILABLE:
        st.info("No images attached. Use file upload, camera, or paste from clipboard above.")
    else:
        st.info("No images attached. Use file upload or camera above. Install 'streamlit-paste-button' for clipboard paste support.")

st.divider()

# =============================================================================
# Audio Recording Section
# =============================================================================
st.subheader("🎤 Audio Recording")

# Initialize recorded audio in session state
if "recorded_audio" not in st.session_state:
    st.session_state.recorded_audio = None
if "transcription_in_progress" not in st.session_state:
    st.session_state.transcription_in_progress = False

# Browser-based audio recording using Streamlit's built-in widget
audio_recording = st.audio_input(
    "Record visit audio",
    help="Click the microphone to start recording. Click again to stop. Audio is processed locally and sent to Azure Speech Services (HIPAA BAA covered) for transcription.",
)

# If new audio was recorded, store it
if audio_recording is not None:
    st.session_state.recorded_audio = audio_recording

# Show playback and transcribe option if audio exists
if st.session_state.recorded_audio is not None:
    st.markdown("**🎧 Recorded Audio:**")
    st.audio(st.session_state.recorded_audio)

    # Transcription button
    transcribe_btn = st.button(
        "🎯 Transcribe Audio",
        type="primary",
        help="Convert recorded audio to text using Azure Speech Services",
        disabled=st.session_state.transcription_in_progress,
    )

    # Handle transcription
    if transcribe_btn:
        st.session_state.transcription_in_progress = True

        with st.spinner("Transcribing audio... This may take a moment."):
            try:
                # Import Azure Speech client
                from autoscribe.azure_speech import get_azure_speech_client, AzureSpeechClient
                from autoscribe.cost_tracking import get_cost_tracker, ModelType

                # Save audio to temp file
                temp_audio_path = Path(tempfile.mktemp(suffix=".wav"))
                temp_audio_path.write_bytes(st.session_state.recorded_audio.getvalue())

                try:
                    # Get speech client and transcribe
                    speech_client = get_azure_speech_client()
                    result = speech_client.transcribe_file(temp_audio_path)

                    # Store result in preview (don't add to transcript yet)
                    if result.text:
                        st.session_state.audio_transcript_preview = result.text
                        st.session_state.audio_transcript_duration = result.duration_seconds

                        # Log cost - Azure Speech Services pricing
                        try:
                            cost_tracker = get_cost_tracker()
                            cost_tracker.log_usage(
                                user_id=user_id,
                                model_type=ModelType.SPEECH_TO_TEXT,
                                model_name="azure-speech-to-text",
                                audio_seconds=result.duration_seconds,
                                user_email=user.email if user and hasattr(user, 'email') else None,
                                is_admin=user.is_admin if user and hasattr(user, 'is_admin') else False,
                                session_id=st.session_state.session_id,
                                operation="transcribe_audio",
                            )
                        except Exception as cost_err:
                            import logging
                            logging.warning(f"Failed to log transcription cost: {cost_err}")

                        # Log audit event
                        audit = get_audit_logger()
                        audit.log_audio_recorded(
                            user_id=user_id,
                            duration=result.duration_seconds,
                            segment_count=1,
                            session_id=st.session_state.session_id,
                        )
                    else:
                        st.warning("No speech detected in the recording. Please try again.")

                finally:
                    # Clean up temp file
                    if temp_audio_path.exists():
                        temp_audio_path.unlink()

            except ValueError as ve:
                # Azure Speech key not configured
                st.error(f"Azure Speech not configured: {ve}")
                st.info("To enable transcription, set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in your .env file.")
            except Exception as e:
                import logging
                logging.error(f"Transcription error: {e}")
                st.error(f"Transcription failed: {str(e)}")

        st.session_state.transcription_in_progress = False
        st.rerun()

    # Show transcript preview box if transcription exists
    if st.session_state.get("audio_transcript_preview"):
        st.markdown("---")
        st.markdown("**📝 Transcription Preview:**")
        duration = st.session_state.get("audio_transcript_duration", 0)
        st.caption(f"Duration: {duration:.1f} seconds")

        # Show preview in a text area (read-only display)
        st.text_area(
            "Preview",
            value=st.session_state.audio_transcript_preview,
            height=150,
            disabled=True,
            label_visibility="collapsed",
            key="transcript_preview_display",
        )

        # Action buttons for preview
        preview_col1, preview_col2, preview_col3 = st.columns([2, 1, 1])

        with preview_col1:
            if st.button("✅ Add to Transcript", type="primary", use_container_width=True):
                # Append to existing transcript
                existing = st.session_state.transcript.strip()
                if existing:
                    st.session_state.transcript = existing + "\n\n" + st.session_state.audio_transcript_preview
                else:
                    st.session_state.transcript = st.session_state.audio_transcript_preview
                # Clear preview after adding
                st.session_state.audio_transcript_preview = None
                st.session_state.audio_transcript_duration = None
                st.success("Added to transcript!")
                st.rerun()

        with preview_col2:
            if st.button("🗑️ Clear", help="Discard this transcription", use_container_width=True):
                st.session_state.audio_transcript_preview = None
                st.session_state.audio_transcript_duration = None
                st.rerun()

        with preview_col3:
            if st.button("🗑️ Clear All", help="Clear recording and transcription", use_container_width=True):
                st.session_state.recorded_audio = None
                st.session_state.audio_transcript_preview = None
                st.session_state.audio_transcript_duration = None
                st.rerun()

else:
    st.caption("📁 No audio recorded. Click the microphone above to start recording.")

st.divider()

# =============================================================================
# Transcript Section
# =============================================================================
st.subheader("📜 Transcript")

# Manual transcript input (can be populated from audio or typed)
transcript = st.text_area(
    "Transcript",
    value=st.session_state.transcript,
    height=250,
    max_chars=1000000,
    placeholder="Paste or type the visit transcript here, or use audio recording above...",
    label_visibility="collapsed",
    key="transcript_input",
)

# Update session state
st.session_state.transcript = transcript

st.divider()

# =============================================================================
# Note Generation Section
# =============================================================================
st.subheader("📝 Generate Note")

# Note Type Selection - Prominent buttons in main area
st.markdown("**Select Note Type:**")

# Initialize note type in session state if not set
# Default to Office Note for providers (future: differentiate by user role - staff=SBAR, provider=Office Note)
if "selected_note_type" not in st.session_state:
    st.session_state.selected_note_type = "Office Note"

note_btn_col1, note_btn_col2, note_btn_col3, note_btn_col4 = st.columns(4)

with note_btn_col1:
    if st.button(
        "📋 SBAR",
        use_container_width=True,
        type="primary" if st.session_state.selected_note_type == "SBAR" else "secondary",
        help="Situation, Background, Assessment, Recommendations",
    ):
        st.session_state.selected_note_type = "SBAR"
        st.rerun()

with note_btn_col2:
    if st.button(
        "🏥 Office Visit",
        use_container_width=True,
        type="primary" if st.session_state.selected_note_type == "Office Note" else "secondary",
        help="In-person office visit note format",
    ):
        st.session_state.selected_note_type = "Office Note"
        st.rerun()

with note_btn_col3:
    if st.button(
        "📹 Video Visit",
        use_container_width=True,
        type="primary" if st.session_state.selected_note_type == "Video Note" else "secondary",
        help="Virtual/telehealth visit note format",
    ):
        st.session_state.selected_note_type = "Video Note"
        st.rerun()

with note_btn_col4:
    if st.button(
        "✏️ Custom",
        use_container_width=True,
        type="primary" if st.session_state.selected_note_type == "Custom" else "secondary",
        help="Use a custom prompt template",
    ):
        st.session_state.selected_note_type = "Custom"
        st.rerun()

# Update the note_type variable to use session state
note_type = st.session_state.selected_note_type

# Show custom prompt selector if Custom is selected
custom_prompt_id = None
if note_type == "Custom":
    user_prompts = prompt_manager.get_user_prompts(user_id)
    if user_prompts:
        prompt_options = [(p.id, p.name) for p in user_prompts]
        selected = st.selectbox(
            "Select custom prompt",
            prompt_options,
            format_func=lambda x: x[1],
            key="main_custom_prompt_select",
        )
        custom_prompt_id = selected[0] if selected else None
    else:
        st.info("No custom prompts yet. Create one in the sidebar settings.")

# Update prompt type mapping
prompt_type_map = {
    "SBAR": PromptType.SBAR,
    "Office Note": PromptType.OFFICE_NOTE,
    "Video Note": PromptType.VIDEO_NOTE,
    "Custom": PromptType.CUSTOM,
}
selected_prompt_type = prompt_type_map[note_type]

st.caption(f"Selected: **{note_type}**")

st.markdown("---")

# Get patient name from top selector for note generation
# Format is "Last, First (MRN)" - extract first name for personalization
patient_name = None
if st.session_state.get("autoscribe_patient_name"):
    name_parts = st.session_state.autoscribe_patient_name.split(",")
    if len(name_parts) >= 2:
        # Extract first name (before the MRN in parentheses)
        first_part = name_parts[1].strip()
        patient_name = first_part.split("(")[0].strip()

# Generate button
gen_col1, gen_col2 = st.columns([1, 3])

with gen_col1:
    generate_clicked = st.button(
        "🚀 Generate Note",
        type="primary",
        use_container_width=True,
        disabled=not transcript.strip(),
    )

with gen_col2:
    if not transcript.strip():
        st.warning("Enter a transcript to generate a note")

# Generate the note
if generate_clicked and transcript.strip():
    # Get the prompt content
    prompt_content = prompt_manager.get_prompt_for_generation(
        prompt_type=selected_prompt_type,
        user_id=user_id if selected_prompt_type == PromptType.CUSTOM else None,
        custom_prompt_id=custom_prompt_id,
    )

    if not prompt_content:
        st.error("Could not load prompt template. Please check configuration.")
    else:
        try:
            from autoscribe.azure_openai import AzureOpenAIClient

            with st.spinner(f"Generating {note_type} note..."):
                # Build additional context from uploads
                context_parts = []
                if additional_context:
                    context_parts.append(additional_context)

                # Include attached images info
                # Note: Full image processing would require vision model (GPT-4o)
                if st.session_state.context_images:
                    image_names = [img["name"] for img in st.session_state.context_images]
                    context_parts.append(f"Attached images/documents ({len(image_names)}): {', '.join(image_names)}")

                combined_context = "\n\n".join(context_parts) if context_parts else None

                # Generate note
                client = AzureOpenAIClient()

                # Set user context for cost tracking
                is_admin = hasattr(user, 'role') and str(user.role).lower() == 'admin'
                client.set_user_context(
                    user_id=user_id,
                    user_email=getattr(user, 'email', None),
                    is_admin=is_admin,
                    session_id=session_id,
                )

                result = client.generate_note(
                    transcript=transcript,
                    prompt=prompt_content,
                    patient_name=patient_name or None,
                    additional_context=combined_context,
                )
                client.close()

                # Store result
                st.session_state.generated_note = result.content

                # Log to audit
                audit = get_audit_logger()
                audit.log_note_generated(
                    user_id=user_id,
                    prompt_type=note_type,
                    token_count=result.total_tokens,
                    session_id=session_id,
                )

                st.success(f"✅ Note generated! ({result.total_tokens} tokens)")

        except ValueError as e:
            st.error(f"Configuration error: {e}")
            st.info("Please configure AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY in .env")
        except Exception as e:
            st.error(f"Generation failed: {e}")

# =============================================================================
# Generated Note Display
# =============================================================================
if st.session_state.generated_note:
    st.divider()
    st.subheader("📄 Generated Note")

    # Display the note in a text area with word wrap (editable so user can select/copy)
    # Use a unique key based on content hash to prevent stale state
    note_display_key = f"note_display_{hash(st.session_state.generated_note) % 10000}"
    displayed_note = st.text_area(
        "Generated note content",
        value=st.session_state.generated_note,
        height=300,
        label_visibility="collapsed",
        key=note_display_key,
    )
    st.caption("💡 Select text with **Ctrl+A** then **Ctrl+C** to copy")

    # Show "View in Patient Notes" link after saving (before action buttons)
    if st.session_state.get("note_saved_to_patient"):
        saved_patient_id = st.session_state.get("saved_patient_id")
        if saved_patient_id:
            save_col1, save_col2 = st.columns([3, 1])
            with save_col1:
                st.success("✅ Note saved to patient record!")
            with save_col2:
                if st.button("📋 View in Patient Notes →", type="secondary", use_container_width=True):
                    st.session_state.selected_patient_notes = saved_patient_id
                    st.switch_page("pages/13_Patient_Notes.py")

    # Action buttons at the bottom
    action_col1, action_col2 = st.columns(2)

    with action_col1:
        # Dynamic button label based on patient selection
        patient_id = st.session_state.get("autoscribe_patient_id")
        patient_name_display = st.session_state.get("autoscribe_patient_name", "")
        if patient_id:
            save_label = f"💾 Save to: {patient_name_display.split('(')[0].strip()}"
        else:
            save_label = "💾 Save to Patient"

        if st.button(save_label, use_container_width=True, disabled=not patient_id):
            if patient_id:
                # Save note to patient record
                save_session = get_session()
                try:
                    # Create PatientNote
                    new_note = PatientNote(
                        patient_id=patient_id,
                        title=f"{note_type} Note - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                        content=st.session_state.generated_note,
                        note_type="autoscribe",
                        created_by=user.username if user else user_id,
                    )
                    save_session.add(new_note)

                    # Create AuditLog entry
                    audit_entry = AuditLog(
                        patient_id=patient_id,
                        action="create",
                        entity_type="note",
                        entity_id=new_note.id,
                        user_id=user_id,
                        user_name=user.username if user else None,
                        details=f"AutoScribe {note_type} note saved",
                    )
                    save_session.add(audit_entry)

                    save_session.commit()

                    # Also log to AutoScribe audit
                    audit = get_audit_logger()
                    audit.log_note_exported(
                        user_id=user_id,
                        export_type="save_to_patient",
                        patient_id=str(patient_id),
                        session_id=session_id,
                    )

                    st.session_state.note_saved_to_patient = True
                    st.session_state.saved_patient_id = patient_id
                    st.rerun()

                except Exception as e:
                    save_session.rollback()
                    st.error(f"Failed to save note: {e}")
                finally:
                    save_session.close()
            else:
                st.warning("Please select a patient from the sidebar first")

        if not patient_id:
            st.caption("Select a patient to enable")

    with action_col2:
        # Download button
        note_bytes = st.session_state.generated_note.encode('utf-8')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{note_type.lower().replace(' ', '_')}_{timestamp}.txt"

        st.download_button(
            "📤 Download",
            data=note_bytes,
            file_name=filename,
            mime="text/plain",
            use_container_width=True,
        )

    # Clear/Reset button
    st.markdown("---")
    if st.button("🔄 Clear & Start New Note", use_container_width=True):
        # Clear all form state
        st.session_state.generated_note = None
        st.session_state.transcript = ""
        st.session_state.recorded_audio = None
        st.session_state.audio_transcript_preview = None
        st.session_state.audio_transcript_duration = None
        st.session_state.context_images = []
        st.session_state.pasted_images = []
        st.session_state.note_saved_to_patient = False
        st.session_state.saved_patient_id = None
        # Keep patient selection - user likely recording for same patient
        st.rerun()

# =============================================================================
# Footer - Session Info
# =============================================================================
st.divider()
with st.expander("ℹ️ Session Info"):
    st.caption(f"Session ID: {session_id}")
    st.caption(f"User: {getattr(user, 'email', user_id)}")
    st.caption(f"Note Type: {note_type}")

    if "autoscribe_session_start" in st.session_state:
        duration = datetime.now() - st.session_state.autoscribe_session_start
        st.caption(f"Session Duration: {int(duration.total_seconds() // 60)} minutes")
