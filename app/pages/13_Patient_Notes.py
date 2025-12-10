"""Patient Notes - Local patient notes management (OneNote alternative)."""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_session, init_db
from database.models import Patient, PatientNote, AuditLog

st.set_page_config(
    page_title="Patient Notes - Patient Explorer",
    page_icon="📝",
    layout="wide",
)

# Initialize database
init_db()

# Import auth after database init
from auth import require_login, require_permission, has_permission, show_user_menu

# Require login and patient view permission
user = require_login()
require_permission("view_patients")
show_user_menu()

st.title("📝 Patient Notes")
st.markdown("Securely store and manage patient notes locally. All notes are stored in the encrypted SQLite database.")
st.divider()


# Note type configuration
NOTE_TYPES = {
    "general": ("📋", "General"),
    "outreach": ("📞", "Outreach"),
    "clinical": ("🏥", "Clinical"),
    "admin": ("📁", "Administrative"),
}


def get_note_icon(note_type: str) -> str:
    """Get icon for a note type."""
    return NOTE_TYPES.get(note_type, ("📋", "General"))[0]


def create_note(patient_id: int, title: str, content: str, note_type: str, username: str) -> bool:
    """Create a new patient note."""
    session = get_session()
    try:
        note = PatientNote(
            patient_id=patient_id,
            title=title,
            content=content,
            note_type=note_type,
            created_by=username,
        )
        session.add(note)

        # Audit log
        audit = AuditLog(
            patient_id=patient_id,
            action="create",
            entity_type="note",
            entity_id=note.id,
            details=f"Created note: {title}",
            user_name=username,
        )
        session.add(audit)

        session.commit()
        return True
    except Exception as e:
        session.rollback()
        st.error(f"Error creating note: {e}")
        return False
    finally:
        session.close()


def update_note(note_id: int, title: str, content: str, note_type: str, is_pinned: bool, username: str) -> bool:
    """Update an existing patient note."""
    session = get_session()
    try:
        note = session.query(PatientNote).get(note_id)
        if not note:
            return False

        old_title = note.title
        note.title = title
        note.content = content
        note.note_type = note_type
        note.is_pinned = is_pinned
        note.updated_by = username

        # Audit log
        audit = AuditLog(
            patient_id=note.patient_id,
            action="update",
            entity_type="note",
            entity_id=note_id,
            details=f"Updated note: {old_title} -> {title}",
            user_name=username,
        )
        session.add(audit)

        session.commit()
        return True
    except Exception as e:
        session.rollback()
        st.error(f"Error updating note: {e}")
        return False
    finally:
        session.close()


def delete_note(note_id: int, username: str) -> bool:
    """Delete a patient note."""
    session = get_session()
    try:
        note = session.query(PatientNote).get(note_id)
        if not note:
            return False

        patient_id = note.patient_id
        title = note.title

        session.delete(note)

        # Audit log
        audit = AuditLog(
            patient_id=patient_id,
            action="delete",
            entity_type="note",
            entity_id=note_id,
            details=f"Deleted note: {title}",
            user_name=username,
        )
        session.add(audit)

        session.commit()
        return True
    except Exception as e:
        session.rollback()
        st.error(f"Error deleting note: {e}")
        return False
    finally:
        session.close()


# Sidebar with patient selection
with st.sidebar:
    st.subheader("🔍 Select Patient")

    session = get_session()
    try:
        patients = session.query(Patient).order_by(Patient.last_name).all()

        if not patients:
            st.warning("No patients in database")
            selected_patient = None
        else:
            # Search filter
            search = st.text_input("Search (name or MRN)", "", key="patient_search")

            # Filter patients
            if search:
                filtered_patients = [
                    p for p in patients
                    if search.lower() in p.last_name.lower()
                    or search.lower() in p.first_name.lower()
                    or search.lower() in (p.mrn or "").lower()
                ]
            else:
                filtered_patients = patients

            if filtered_patients:
                patient_options = [
                    (p.id, f"{p.last_name}, {p.first_name} ({p.mrn})")
                    for p in filtered_patients[:100]
                ]

                selected_patient = st.selectbox(
                    "Patient",
                    patient_options,
                    format_func=lambda x: x[1],
                    key="selected_patient_notes"
                )
            else:
                st.caption("No matching patients")
                selected_patient = None

    finally:
        session.close()

    st.divider()

    st.subheader("📊 Notes Summary")

    if selected_patient:
        session = get_session()
        try:
            note_count = session.query(PatientNote).filter(
                PatientNote.patient_id == selected_patient[0]
            ).count()

            pinned_count = session.query(PatientNote).filter(
                PatientNote.patient_id == selected_patient[0],
                PatientNote.is_pinned == True
            ).count()

            st.metric("Total Notes", note_count)
            st.metric("Pinned", pinned_count)
        finally:
            session.close()


# Main content
if not selected_patient:
    st.info("Select a patient from the sidebar to view or create notes.")
else:
    patient_id = selected_patient[0]

    session = get_session()
    try:
        patient = session.query(Patient).get(patient_id)

        # Patient header
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            display_name = f"{patient.first_name} {patient.last_name}"
            if patient.preferred_name:
                display_name += f' "{patient.preferred_name}"'
            st.markdown(f"### {display_name}")
            st.caption(f"MRN: {patient.mrn}")

        with col2:
            if patient.apcm_enrolled:
                st.success("🏥 APCM Patient")
            if patient.consent:
                status = patient.consent.status.value.replace("_", " ").title()
                st.caption(f"Consent: {status}")

        with col3:
            if patient.phone:
                st.caption(f"📞 {patient.phone}")

        st.divider()

        # Tabs for viewing and creating notes
        tabs = st.tabs(["📋 View Notes", "➕ Add Note"])

        with tabs[0]:
            # Get notes for this patient
            notes = session.query(PatientNote).filter(
                PatientNote.patient_id == patient_id
            ).order_by(
                PatientNote.is_pinned.desc(),
                PatientNote.created_at.desc()
            ).all()

            if not notes:
                st.info("No notes for this patient yet. Use the 'Add Note' tab to create one.")
            else:
                # Filter by type
                type_filter = st.selectbox(
                    "Filter by type",
                    ["All"] + [f"{v[0]} {v[1]}" for v in NOTE_TYPES.values()],
                    key="note_type_filter"
                )

                for note in notes:
                    # Apply filter
                    if type_filter != "All":
                        type_label = NOTE_TYPES.get(note.note_type, ("", ""))[1]
                        if type_label not in type_filter:
                            continue

                    icon = get_note_icon(note.note_type)
                    pin_icon = "📌 " if note.is_pinned else ""
                    title_display = note.title or "Untitled Note"

                    with st.expander(f"{pin_icon}{icon} **{title_display}** - {note.created_at.strftime('%Y-%m-%d %H:%M')}"):
                        # Note content
                        st.markdown(note.content)

                        st.divider()

                        # Metadata
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.caption(f"Created by: {note.created_by or 'Unknown'}")
                            st.caption(f"Created: {note.created_at.strftime('%Y-%m-%d %H:%M')}")
                        with col2:
                            if note.updated_by:
                                st.caption(f"Updated by: {note.updated_by}")
                                st.caption(f"Updated: {note.updated_at.strftime('%Y-%m-%d %H:%M')}")
                        with col3:
                            type_label = NOTE_TYPES.get(note.note_type, ("📋", "General"))[1]
                            st.caption(f"Type: {type_label}")

                        # Actions
                        if has_permission("edit_patients"):
                            st.divider()
                            action_col1, action_col2, action_col3 = st.columns(3)

                            with action_col1:
                                if st.button("✏️ Edit", key=f"edit_{note.id}"):
                                    st.session_state[f"editing_note_{note.id}"] = True
                                    st.rerun()

                            with action_col2:
                                pin_label = "📌 Unpin" if note.is_pinned else "📌 Pin"
                                if st.button(pin_label, key=f"pin_{note.id}"):
                                    update_note(
                                        note.id,
                                        note.title,
                                        note.content,
                                        note.note_type,
                                        not note.is_pinned,
                                        user.username if user else None
                                    )
                                    st.rerun()

                            with action_col3:
                                if st.button("🗑️ Delete", key=f"delete_{note.id}"):
                                    st.session_state[f"confirm_delete_{note.id}"] = True
                                    st.rerun()

                            # Confirm delete dialog
                            if st.session_state.get(f"confirm_delete_{note.id}"):
                                st.warning("Are you sure you want to delete this note?")
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("Yes, delete", key=f"confirm_yes_{note.id}"):
                                        if delete_note(note.id, user.username if user else None):
                                            st.success("Note deleted")
                                            del st.session_state[f"confirm_delete_{note.id}"]
                                            st.rerun()
                                with col2:
                                    if st.button("Cancel", key=f"confirm_no_{note.id}"):
                                        del st.session_state[f"confirm_delete_{note.id}"]
                                        st.rerun()

                            # Edit form
                            if st.session_state.get(f"editing_note_{note.id}"):
                                st.markdown("---")
                                st.markdown("**Edit Note:**")

                                edit_title = st.text_input(
                                    "Title",
                                    value=note.title or "",
                                    key=f"edit_title_{note.id}"
                                )

                                edit_content = st.text_area(
                                    "Content",
                                    value=note.content,
                                    height=200,
                                    key=f"edit_content_{note.id}"
                                )

                                edit_type = st.selectbox(
                                    "Type",
                                    list(NOTE_TYPES.keys()),
                                    index=list(NOTE_TYPES.keys()).index(note.note_type) if note.note_type in NOTE_TYPES else 0,
                                    format_func=lambda x: f"{NOTE_TYPES[x][0]} {NOTE_TYPES[x][1]}",
                                    key=f"edit_type_{note.id}"
                                )

                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("💾 Save Changes", key=f"save_{note.id}"):
                                        if update_note(
                                            note.id,
                                            edit_title,
                                            edit_content,
                                            edit_type,
                                            note.is_pinned,
                                            user.username if user else None
                                        ):
                                            st.success("Note updated!")
                                            del st.session_state[f"editing_note_{note.id}"]
                                            st.rerun()

                                with col2:
                                    if st.button("Cancel", key=f"cancel_edit_{note.id}"):
                                        del st.session_state[f"editing_note_{note.id}"]
                                        st.rerun()

        with tabs[1]:
            st.subheader("Create New Note")

            if not has_permission("edit_patients"):
                st.warning("You don't have permission to create notes.")
            else:
                with st.form("new_note_form"):
                    new_title = st.text_input("Title (optional)", placeholder="Note title...")

                    new_type = st.selectbox(
                        "Note Type",
                        list(NOTE_TYPES.keys()),
                        format_func=lambda x: f"{NOTE_TYPES[x][0]} {NOTE_TYPES[x][1]}"
                    )

                    new_content = st.text_area(
                        "Content",
                        placeholder="Enter note content...",
                        height=200
                    )

                    submitted = st.form_submit_button("💾 Save Note", type="primary")

                    if submitted:
                        if not new_content:
                            st.error("Please enter note content")
                        else:
                            if create_note(
                                patient_id,
                                new_title,
                                new_content,
                                new_type,
                                user.username if user else None
                            ):
                                st.success("Note created!")
                                st.rerun()

                st.divider()

                # Quick note templates
                st.markdown("**Quick Templates:**")

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("📞 Outreach Attempt", use_container_width=True):
                        st.session_state["quick_template"] = {
                            "title": f"Outreach - {datetime.now().strftime('%Y-%m-%d')}",
                            "type": "outreach",
                            "content": f"""**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Method:** SMS / Phone / In-Person
**Result:** Reached / No Answer / Left Message / Wrong Number

**Notes:**
-
"""
                        }
                        st.rerun()

                with col2:
                    if st.button("📋 Follow-up Required", use_container_width=True):
                        st.session_state["quick_template"] = {
                            "title": "Follow-up Required",
                            "type": "admin",
                            "content": f"""**Follow-up needed for:**
-

**By date:** {(datetime.now()).strftime('%Y-%m-%d')}
**Assigned to:**
**Status:** Pending

**Notes:**
-
"""
                        }
                        st.rerun()

                # Apply quick template
                if "quick_template" in st.session_state:
                    tmpl = st.session_state["quick_template"]
                    st.info(f"Template loaded: {tmpl['title']}")
                    st.text_area("Preview", value=tmpl["content"], height=150, disabled=True)

                    if st.button("Use This Template"):
                        create_note(
                            patient_id,
                            tmpl["title"],
                            tmpl["content"],
                            tmpl["type"],
                            user.username if user else None
                        )
                        del st.session_state["quick_template"]
                        st.success("Note created from template!")
                        st.rerun()

                    if st.button("Clear Template"):
                        del st.session_state["quick_template"]
                        st.rerun()

    finally:
        session.close()


# Footer
st.divider()
st.caption("""
**About Patient Notes:**
- Notes are stored locally in the encrypted SQLite database
- All note activity is logged for HIPAA compliance
- Use note types to categorize: General, Outreach, Clinical, Administrative
- Pin important notes to keep them at the top
""")
