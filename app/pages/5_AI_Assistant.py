"""AI Assistant Page - HIPAA-compliant AI tools via Azure Foundry Claude."""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_session, init_db
from database.models import Patient, Consent, ConsentStatus

st.set_page_config(
    page_title="AI Assistant - Patient Explorer",
    page_icon="🤖",
    layout="wide",
)

# Initialize database
init_db()

# Import auth after database init
from auth import require_login, require_permission, show_user_menu

# Require login and AI permission
user = require_login()
require_permission("use_ai")
show_user_menu()

st.title("🤖 AI Assistant")
st.markdown("HIPAA-compliant AI tools powered by Azure Foundry Claude (under Microsoft BAA).")
st.divider()


def get_ai_client():
    """Get Azure Claude client, with caching."""
    try:
        from azure_claude import AzureClaudeClient
        return AzureClaudeClient()
    except Exception as e:
        st.error(f"Failed to initialize AI client: {e}")
        return None


# Sidebar - Connection Status & Model Selection
with st.sidebar:
    st.subheader("🔌 AI Connection")

    try:
        from azure_claude import AzureClaudeClient, ModelTier

        client = AzureClaudeClient()
        with st.spinner("Testing connection..."):
            if client.test_connection():
                st.success("✅ Connected to Azure Claude")
            else:
                st.error("❌ Connection failed")
        client.close()

    except ValueError as e:
        st.error(f"Configuration error: {e}")
        st.info("Check AZURE_CLAUDE_ENDPOINT and AZURE_CLAUDE_API_KEY in .env")
    except Exception as e:
        st.error(f"Error: {e}")

    st.divider()

    st.subheader("⚙️ Settings")

    model_choice = st.selectbox(
        "Default Model",
        [
            ("Haiku (Fast/Cheap)", "haiku"),
            ("Sonnet (Balanced)", "sonnet"),
            ("Opus (Most Capable)", "opus"),
        ],
        index=1,
        format_func=lambda x: x[0]
    )[1]

    st.caption("""
    **Model Guide:**
    - **Haiku**: SMS drafts, simple tasks
    - **Sonnet**: Most tasks, good balance
    - **Opus**: Complex reasoning only
    """)


# Main content tabs
tabs = st.tabs(["📱 SMS Drafting", "📋 Care Plan Helper", "💬 Ask Claude", "📊 Usage Stats"])

with tabs[0]:
    st.subheader("Draft Consent SMS Messages")

    st.markdown("""
    Generate personalized SMS messages for consent outreach.
    Uses **Claude Haiku** for fast, cost-effective generation.
    """)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        # Patient selection
        session = get_session()
        try:
            patients_with_tokens = session.query(Patient).filter(
                Patient.consent_token.isnot(None),
                Patient.spruce_matched == True
            ).all()

            patient_options = [
                (p.id, f"{p.last_name}, {p.first_name} ({p.mrn})")
                for p in patients_with_tokens
            ]

            if patient_options:
                selected_patient_id = st.selectbox(
                    "Select Patient",
                    patient_options,
                    format_func=lambda x: x[1]
                )[0]

                patient = session.query(Patient).get(selected_patient_id)
            else:
                st.warning("No patients with consent tokens. Generate tokens first in Outreach Campaign.")
                patient = None

        finally:
            session.close()

    with col2:
        # Form URL
        form_url = st.text_input(
            "Microsoft Forms Base URL",
            placeholder="https://forms.microsoft.com/r/...",
            help="Your consent form URL"
        )

    if patient and form_url:
        st.divider()

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"**Patient:** {patient.first_name} {patient.last_name}")
            if patient.preferred_name:
                st.markdown(f"**Preferred Name:** {patient.preferred_name}")
            st.markdown(f"**APCM:** {'Yes' if patient.apcm_enrolled else 'No'}")
            st.markdown(f"**Token:** `{patient.consent_token}`")

        with col2:
            if st.button("✨ Generate SMS", type="primary", use_container_width=True):
                try:
                    from azure_claude import draft_consent_sms, AzureClaudeClient

                    # Build consent URL
                    consent_url = f"{form_url}?token={patient.consent_token}"

                    with st.spinner("Generating SMS..."):
                        client = AzureClaudeClient()
                        sms_text = draft_consent_sms(
                            patient_name=f"{patient.first_name} {patient.last_name}",
                            preferred_name=patient.preferred_name,
                            consent_url=consent_url,
                            is_apcm=patient.apcm_enrolled,
                            client=client,
                        )
                        client.close()

                    st.session_state["generated_sms"] = sms_text

                except Exception as e:
                    st.error(f"Generation failed: {e}")

        # Display generated SMS
        if "generated_sms" in st.session_state:
            st.divider()
            st.markdown("**Generated SMS:**")
            sms = st.text_area(
                "Edit if needed",
                value=st.session_state["generated_sms"],
                height=100,
                label_visibility="collapsed"
            )

            char_count = len(sms)
            if char_count <= 160:
                st.caption(f"✅ {char_count}/160 characters (1 SMS)")
            elif char_count <= 320:
                st.caption(f"⚠️ {char_count}/320 characters (2 SMS segments)")
            else:
                st.caption(f"❌ {char_count} characters (too long)")

            # Copy button
            st.code(sms, language=None)


with tabs[1]:
    st.subheader("Care Plan Helper")

    st.markdown("""
    Generate care plan sections based on patient conditions and context.
    Uses **Claude Sonnet** for balanced clinical reasoning.
    """)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        condition = st.text_input(
            "Condition/Diagnosis",
            placeholder="e.g., Type 2 Diabetes, Hypertension, COPD",
        )

    with col2:
        # Quick condition buttons
        st.markdown("**Common Conditions:**")
        quick_conditions = st.columns(3)
        with quick_conditions[0]:
            if st.button("Diabetes", use_container_width=True):
                condition = "Type 2 Diabetes Mellitus"
        with quick_conditions[1]:
            if st.button("HTN", use_container_width=True):
                condition = "Hypertension"
        with quick_conditions[2]:
            if st.button("CHF", use_container_width=True):
                condition = "Congestive Heart Failure"

    patient_context = st.text_area(
        "Patient Context (optional)",
        placeholder="Age, relevant history, current medications, recent labs, social factors...",
        height=100,
    )

    if st.button("📋 Generate Care Plan Section", type="primary"):
        if not condition:
            st.warning("Please enter a condition")
        else:
            try:
                from azure_claude import generate_care_plan_section, AzureClaudeClient

                with st.spinner("Generating care plan..."):
                    client = AzureClaudeClient()
                    care_plan = generate_care_plan_section(
                        condition=condition,
                        patient_context=patient_context or "No additional context provided",
                        client=client,
                    )
                    client.close()

                st.divider()
                st.markdown("### Generated Care Plan Section")
                st.markdown(care_plan)

                # Copy option
                with st.expander("Copy as plain text"):
                    st.code(care_plan, language=None)

            except Exception as e:
                st.error(f"Generation failed: {e}")


with tabs[2]:
    st.subheader("Ask Claude")

    st.markdown("""
    General AI assistant for clinical documentation, summarization, and queries.
    Select model based on task complexity.
    """)

    st.divider()

    # System prompt selection
    system_prompts = {
        "General Assistant": "You are a helpful medical documentation assistant.",
        "Clinical Summarizer": """You are a clinical documentation specialist.
Summarize information concisely and accurately.
Use standard medical terminology.
Maintain HIPAA compliance.""",
        "Patient Communication": """You are helping draft patient communications.
Use clear, simple language appropriate for patients.
Be warm but professional.
Avoid medical jargon when possible.""",
        "Custom": None,
    }

    prompt_type = st.selectbox(
        "Context/Role",
        list(system_prompts.keys()),
    )

    if prompt_type == "Custom":
        system_prompt = st.text_area(
            "Custom System Prompt",
            placeholder="Define the AI's role and behavior...",
            height=80,
        )
    else:
        system_prompt = system_prompts[prompt_type]
        with st.expander("View system prompt"):
            st.code(system_prompt)

    # Model selection for this query
    query_model = st.radio(
        "Model for this query",
        ["Haiku (Fast)", "Sonnet (Balanced)", "Opus (Most Capable)"],
        index=1,
        horizontal=True,
    )

    model_map = {
        "Haiku (Fast)": "haiku",
        "Sonnet (Balanced)": "sonnet",
        "Opus (Most Capable)": "opus",
    }

    # User input
    user_query = st.text_area(
        "Your Question or Request",
        placeholder="Enter your question or paste text to analyze...",
        height=150,
    )

    if st.button("🚀 Send to Claude", type="primary"):
        if not user_query:
            st.warning("Please enter a question or request")
        else:
            try:
                from azure_claude import AzureClaudeClient, ModelTier

                model_enum = {
                    "haiku": ModelTier.HAIKU,
                    "sonnet": ModelTier.SONNET,
                    "opus": ModelTier.OPUS,
                }[model_map[query_model]]

                with st.spinner(f"Asking Claude ({query_model})..."):
                    client = AzureClaudeClient()
                    response = client.send_message(
                        user_query,
                        model=model_enum,
                        system_prompt=system_prompt,
                    )
                    client.close()

                st.divider()
                st.markdown("### Response")
                st.markdown(response.content)

                # Token usage
                st.caption(
                    f"Tokens: {response.input_tokens} input, {response.output_tokens} output | "
                    f"Model: {response.model}"
                )

            except Exception as e:
                st.error(f"Request failed: {e}")


with tabs[3]:
    st.subheader("Usage Statistics")

    st.markdown("""
    Track AI usage for cost monitoring and optimization.
    *Note: Detailed usage tracking coming in future update.*
    """)

    st.divider()

    st.info("""
    **Cost Estimates (approximate):**

    | Model | Input (per 1M tokens) | Output (per 1M tokens) |
    |-------|----------------------|------------------------|
    | Haiku | ~$0.25 | ~$1.25 |
    | Sonnet | ~$3.00 | ~$15.00 |
    | Opus | ~$15.00 | ~$75.00 |

    **Recommendation:** Use Haiku for SMS drafting, Sonnet for most tasks.
    Reserve Opus for complex clinical reasoning only.
    """)

    st.divider()

    st.markdown("### Quick Cost Calculator")

    col1, col2, col3 = st.columns(3)

    with col1:
        calc_model = st.selectbox(
            "Model",
            ["Haiku", "Sonnet", "Opus"]
        )

    with col2:
        input_tokens = st.number_input("Input Tokens", value=1000, step=100)

    with col3:
        output_tokens = st.number_input("Output Tokens", value=500, step=100)

    # Cost calculation (approximate)
    costs = {
        "Haiku": (0.25, 1.25),
        "Sonnet": (3.00, 15.00),
        "Opus": (15.00, 75.00),
    }

    input_cost, output_cost = costs[calc_model]
    total_cost = (input_tokens / 1_000_000 * input_cost) + (output_tokens / 1_000_000 * output_cost)

    st.metric(
        "Estimated Cost",
        f"${total_cost:.6f}",
        help="Based on approximate token pricing"
    )

    # Bulk estimate
    st.divider()
    st.markdown("### Bulk SMS Campaign Estimate")

    num_patients = st.number_input("Number of patients", value=100, step=10)

    # Assuming ~200 tokens input, ~100 tokens output per SMS
    bulk_cost = num_patients * ((200 / 1_000_000 * 0.25) + (100 / 1_000_000 * 1.25))

    st.metric(
        f"Est. cost for {num_patients} SMS drafts (Haiku)",
        f"${bulk_cost:.4f}",
        help="~200 input tokens, ~100 output tokens per message"
    )
