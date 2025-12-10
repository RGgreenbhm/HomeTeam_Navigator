"""SMS Templates for Consent Outreach Campaign.

This module provides professionally crafted SMS templates for patient outreach,
with differentiation between APCM and non-APCM patients, and follow-up sequences.

Based on the Phase 0B Consent Outreach Plan.
"""

from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class SMSTemplate:
    """SMS template with metadata."""
    name: str
    category: str  # 'initial', 'follow_up', 'confirmation'
    message: str
    character_count: int
    sms_segments: int  # 160 chars = 1 segment, 306 chars = 2 segments
    is_apcm: bool
    day_offset: int  # 0 for initial, 3/7/14 for follow-ups


# Office phone number for Spruce
DEFAULT_OFFICE_PHONE = "(205) 955-7605"


def get_display_name(first_name: str, preferred_name: Optional[str] = None) -> str:
    """Get the appropriate name to address the patient."""
    if preferred_name:
        return preferred_name
    return first_name


def format_message(template: str, **kwargs) -> str:
    """Format a template with patient data."""
    return template.format(**kwargs)


def count_sms_segments(message: str) -> int:
    """Count how many SMS segments a message will use."""
    length = len(message)
    if length <= 160:
        return 1
    elif length <= 306:
        return 2
    elif length <= 459:
        return 3
    else:
        return (length // 153) + 1  # Concatenated SMS uses 153 chars per segment


# ==============================================================================
# SMS PRIVACY AUTO-REPLY (for patient responses)
# ==============================================================================

TEMPLATE_SMS_PRIVACY_AUTOREPLY = """Thanks for your reply. Note: SMS is not secure for private health info. For confidential matters, call {phone} or use our patient portal. Continued texting implies consent to SMS with this understanding."""

TEMPLATE_SMS_PRIVACY_AUTOREPLY_CONCISE = """Thanks for replying. For private health matters, please call {phone}. SMS is not encrypted and may be intercepted. Reply STOP to opt out."""


# ==============================================================================
# LOCATION UPDATE TEMPLATES (V1.0 - Practice Transition)
# ==============================================================================

TEMPLATE_LOCATION_UPDATE_SMS = """Dr. Green's practice has important updates about our new location. Please follow the link for details and a personalized form to share any questions: {consent_url}"""

TEMPLATE_LOCATION_UPDATE_SMS_FULL = """Hi {name}, Dr. Green's primary care team is moving to a new location. Please follow the link for important information and to share any questions or concerns about this transition: {consent_url}"""


# ==============================================================================
# INITIAL OUTREACH TEMPLATES
# ==============================================================================

TEMPLATE_NON_APCM_INITIAL = """Hi {name}, this is Dr. Robert Green's office.

As you may know, I am transitioning my practice from Southview. To continue providing you excellent care, I need your consent to maintain your medical records.

Please visit this secure link to complete your consent:
{consent_url}

Questions? Reply here or call {phone}.

- Dr. Green's Care Team"""


TEMPLATE_APCM_INITIAL = """Hi {name}, this is Dr. Robert Green's office.

As an APCM patient, I want to continue providing your care coordination services after my transition to Home Team Medical Services in January 2026.

Please visit this link to:
- Continue APCM with Dr. Green
- Confirm records retention consent

{consent_url}

Questions? Reply or call {phone}.

- Dr. Green's Care Team"""


TEMPLATE_APCM_INITIAL_DETAILED = """Hi {name}, this is Dr. Robert Green's office.

As an Advanced Primary Care Management (APCM) patient, I want to continue your care coordination after my transition from Southview to Home Team Medical Services in January 2026.

Please visit this secure link to:
- Continue APCM services with Dr. Green at Home Team
- Authorize us to notify Southview about your choice
- Confirm records retention consent

{consent_url}

Questions? Reply here or call {phone}.

- Dr. Green's Care Team"""


# ==============================================================================
# FOLLOW-UP TEMPLATES
# ==============================================================================

TEMPLATE_FOLLOWUP_DAY3 = """Hi {name}, this is Dr. Green's office.

Just a friendly reminder - we still need your consent to maintain your medical records as Dr. Green transitions from Southview.

Takes less than 2 minutes:
{consent_url}

Thank you!
- Dr. Green's Care Team"""


TEMPLATE_FOLLOWUP_DAY7 = """Hi {name}, this is Dr. Green's office - second reminder.

We haven't heard from you yet about records consent. This is important to ensure continuity of your care.

Please complete this short form:
{consent_url}

Questions? Call {phone}.

- Dr. Green's Care Team"""


TEMPLATE_FOLLOWUP_DAY14_FINAL = """Hi {name} - FINAL REMINDER from Dr. Green's office.

We need your consent to continue as your healthcare provider. Without it, we may not be able to maintain access to your complete medical history.

Please respond today:
{consent_url}

Or call us at {phone}.

- Dr. Green's Care Team"""


TEMPLATE_APCM_FOLLOWUP_DAY3 = """Hi {name}, this is Dr. Green's office.

Reminder: We need your APCM elections to continue your care coordination services with Home Team Medical Services.

Complete your choices here (2 min):
{consent_url}

Thank you!
- Dr. Green's Care Team"""


TEMPLATE_APCM_FOLLOWUP_DAY7 = """Hi {name} - important APCM reminder from Dr. Green's office.

To continue your Advanced Primary Care Management benefits with Dr. Green at Home Team, we need your consent response.

Please complete today:
{consent_url}

Questions? Call {phone}.

- Dr. Green's Care Team"""


TEMPLATE_APCM_FOLLOWUP_DAY14_FINAL = """Hi {name} - FINAL APCM REMINDER.

Without your response, your APCM care coordination will not automatically transfer to Home Team Medical Services.

Protect your benefits - respond today:
{consent_url}

Or call {phone} immediately.

- Dr. Green's Care Team"""


# ==============================================================================
# CONFIRMATION TEMPLATES
# ==============================================================================

TEMPLATE_CONFIRMATION_CONSENTED = """Thank you, {name}!

We've received your consent for records retention. Dr. Green looks forward to continuing your care at Home Team Medical Services.

Confirmation #: {confirmation_id}
Date: {date}

Questions? Call {phone}.

- Dr. Green's Care Team"""


TEMPLATE_CONFIRMATION_APCM_CONSENTED = """Thank you, {name}!

We've received your consent and APCM elections:
- Records Retention: Consented
- APCM with Home Team: {apcm_continue}
{revoke_line}

Confirmation #: {confirmation_id}
Date: {date}

Questions? Call {phone}.

- Dr. Green's Care Team"""


TEMPLATE_CONFIRMATION_DECLINED = """Hi {name},

We've recorded your response. We respect your decision.

If you change your mind or have questions about your medical records and care options, please call us at {phone}.

- Dr. Green's Care Team"""


# ==============================================================================
# TEMPLATE GENERATOR FUNCTIONS
# ==============================================================================

def generate_initial_sms(
    patient_first_name: str,
    patient_preferred_name: Optional[str],
    consent_url: str,
    is_apcm: bool = False,
    use_detailed_apcm: bool = False,
    office_phone: str = DEFAULT_OFFICE_PHONE
) -> SMSTemplate:
    """Generate an initial outreach SMS for a patient.

    Args:
        patient_first_name: Patient's first name
        patient_preferred_name: Patient's preferred name (nickname)
        consent_url: Unique consent portal URL with token
        is_apcm: Whether patient is enrolled in APCM
        use_detailed_apcm: Use longer APCM template with more detail
        office_phone: Office phone number

    Returns:
        SMSTemplate with formatted message and metadata
    """
    name = get_display_name(patient_first_name, patient_preferred_name)

    if is_apcm:
        if use_detailed_apcm:
            template = TEMPLATE_APCM_INITIAL_DETAILED
            template_name = "APCM Initial (Detailed)"
        else:
            template = TEMPLATE_APCM_INITIAL
            template_name = "APCM Initial"
    else:
        template = TEMPLATE_NON_APCM_INITIAL
        template_name = "Non-APCM Initial"

    message = format_message(
        template,
        name=name,
        consent_url=consent_url,
        phone=office_phone
    )

    return SMSTemplate(
        name=template_name,
        category="initial",
        message=message,
        character_count=len(message),
        sms_segments=count_sms_segments(message),
        is_apcm=is_apcm,
        day_offset=0
    )


def generate_followup_sms(
    patient_first_name: str,
    patient_preferred_name: Optional[str],
    consent_url: str,
    day_offset: int,
    is_apcm: bool = False,
    office_phone: str = DEFAULT_OFFICE_PHONE
) -> SMSTemplate:
    """Generate a follow-up SMS for non-responders.

    Args:
        patient_first_name: Patient's first name
        patient_preferred_name: Patient's preferred name
        consent_url: Unique consent portal URL
        day_offset: Days since initial outreach (3, 7, or 14)
        is_apcm: Whether patient is enrolled in APCM
        office_phone: Office phone number

    Returns:
        SMSTemplate with formatted message and metadata
    """
    name = get_display_name(patient_first_name, patient_preferred_name)

    # Select appropriate template based on day offset and APCM status
    if is_apcm:
        if day_offset <= 3:
            template = TEMPLATE_APCM_FOLLOWUP_DAY3
            template_name = "APCM Follow-up Day 3"
        elif day_offset <= 7:
            template = TEMPLATE_APCM_FOLLOWUP_DAY7
            template_name = "APCM Follow-up Day 7"
        else:
            template = TEMPLATE_APCM_FOLLOWUP_DAY14_FINAL
            template_name = "APCM Final Reminder"
    else:
        if day_offset <= 3:
            template = TEMPLATE_FOLLOWUP_DAY3
            template_name = "Follow-up Day 3"
        elif day_offset <= 7:
            template = TEMPLATE_FOLLOWUP_DAY7
            template_name = "Follow-up Day 7"
        else:
            template = TEMPLATE_FOLLOWUP_DAY14_FINAL
            template_name = "Final Reminder"

    message = format_message(
        template,
        name=name,
        consent_url=consent_url,
        phone=office_phone
    )

    return SMSTemplate(
        name=template_name,
        category="follow_up",
        message=message,
        character_count=len(message),
        sms_segments=count_sms_segments(message),
        is_apcm=is_apcm,
        day_offset=day_offset
    )


def generate_confirmation_sms(
    patient_first_name: str,
    patient_preferred_name: Optional[str],
    consented: bool,
    is_apcm: bool = False,
    apcm_continue: Optional[bool] = None,
    apcm_revoke_sv: Optional[bool] = None,
    confirmation_id: Optional[str] = None,
    office_phone: str = DEFAULT_OFFICE_PHONE
) -> SMSTemplate:
    """Generate a confirmation SMS after patient responds.

    Args:
        patient_first_name: Patient's first name
        patient_preferred_name: Patient's preferred name
        consented: Whether patient consented
        is_apcm: Whether patient is enrolled in APCM
        apcm_continue: APCM continuation election (if applicable)
        apcm_revoke_sv: Southview revocation election (if applicable)
        confirmation_id: Unique confirmation number
        office_phone: Office phone number

    Returns:
        SMSTemplate with formatted message and metadata
    """
    name = get_display_name(patient_first_name, patient_preferred_name)
    date_str = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    if not confirmation_id:
        confirmation_id = f"CONF-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    if not consented:
        template = TEMPLATE_CONFIRMATION_DECLINED
        template_name = "Declined Confirmation"
        message = format_message(
            template,
            name=name,
            phone=office_phone
        )
    elif is_apcm and apcm_continue is not None:
        template = TEMPLATE_CONFIRMATION_APCM_CONSENTED
        template_name = "APCM Consent Confirmation"

        apcm_status = "Yes - Continuing" if apcm_continue else "No - Not continuing"
        revoke_line = ""
        if apcm_revoke_sv is not None:
            revoke_status = "Yes" if apcm_revoke_sv else "No"
            revoke_line = f"- Southview Revocation: {revoke_status}"

        message = format_message(
            template,
            name=name,
            apcm_continue=apcm_status,
            revoke_line=revoke_line,
            confirmation_id=confirmation_id,
            date=date_str,
            phone=office_phone
        )
    else:
        template = TEMPLATE_CONFIRMATION_CONSENTED
        template_name = "Consent Confirmation"
        message = format_message(
            template,
            name=name,
            confirmation_id=confirmation_id,
            date=date_str,
            phone=office_phone
        )

    return SMSTemplate(
        name=template_name,
        category="confirmation",
        message=message,
        character_count=len(message),
        sms_segments=count_sms_segments(message),
        is_apcm=is_apcm,
        day_offset=0
    )


def get_all_templates() -> list[dict]:
    """Get all available templates with sample data for preview.

    Returns:
        List of template dictionaries with name, category, sample message, and metadata
    """
    sample_name = "Patricia"
    sample_url = "https://forms.office.com/r/abc123?token=SAMPLE"
    sample_phone = "(555) 123-4567"

    templates = []

    # Initial templates
    for is_apcm in [False, True]:
        sms = generate_initial_sms(
            patient_first_name=sample_name,
            patient_preferred_name=None,
            consent_url=sample_url,
            is_apcm=is_apcm,
            office_phone=sample_phone
        )
        templates.append({
            "name": sms.name,
            "category": sms.category,
            "message": sms.message,
            "characters": sms.character_count,
            "segments": sms.sms_segments,
            "is_apcm": sms.is_apcm,
            "day_offset": sms.day_offset,
        })

    # APCM detailed template
    sms = generate_initial_sms(
        patient_first_name=sample_name,
        patient_preferred_name=None,
        consent_url=sample_url,
        is_apcm=True,
        use_detailed_apcm=True,
        office_phone=sample_phone
    )
    templates.append({
        "name": sms.name,
        "category": sms.category,
        "message": sms.message,
        "characters": sms.character_count,
        "segments": sms.sms_segments,
        "is_apcm": sms.is_apcm,
        "day_offset": sms.day_offset,
    })

    # Follow-up templates
    for day_offset in [3, 7, 14]:
        for is_apcm in [False, True]:
            sms = generate_followup_sms(
                patient_first_name=sample_name,
                patient_preferred_name=None,
                consent_url=sample_url,
                day_offset=day_offset,
                is_apcm=is_apcm,
                office_phone=sample_phone
            )
            templates.append({
                "name": sms.name,
                "category": sms.category,
                "message": sms.message,
                "characters": sms.character_count,
                "segments": sms.sms_segments,
                "is_apcm": sms.is_apcm,
                "day_offset": sms.day_offset,
            })

    # Confirmation templates
    for consented in [True, False]:
        sms = generate_confirmation_sms(
            patient_first_name=sample_name,
            patient_preferred_name=None,
            consented=consented,
            office_phone=sample_phone
        )
        templates.append({
            "name": sms.name,
            "category": sms.category,
            "message": sms.message,
            "characters": sms.character_count,
            "segments": sms.sms_segments,
            "is_apcm": sms.is_apcm,
            "day_offset": sms.day_offset,
        })

    # APCM confirmation
    sms = generate_confirmation_sms(
        patient_first_name=sample_name,
        patient_preferred_name=None,
        consented=True,
        is_apcm=True,
        apcm_continue=True,
        apcm_revoke_sv=True,
        office_phone=sample_phone
    )
    templates.append({
        "name": sms.name,
        "category": sms.category,
        "message": sms.message,
        "characters": sms.character_count,
        "segments": sms.sms_segments,
        "is_apcm": sms.is_apcm,
        "day_offset": sms.day_offset,
    })

    return templates


def get_follow_up_schedule() -> list[dict]:
    """Get the recommended follow-up schedule.

    Returns:
        List of follow-up actions with timing and description
    """
    return [
        {
            "day": 0,
            "action": "Initial Outreach",
            "description": "Send first SMS with consent link",
            "template": "Initial (APCM or Non-APCM)",
            "priority": "High",
        },
        {
            "day": 3,
            "action": "First Reminder",
            "description": "Gentle reminder to non-responders",
            "template": "Follow-up Day 3",
            "priority": "Medium",
        },
        {
            "day": 7,
            "action": "Second Reminder",
            "description": "More urgent reminder with emphasis on importance",
            "template": "Follow-up Day 7",
            "priority": "Medium",
        },
        {
            "day": 14,
            "action": "Final Reminder",
            "description": "Final SMS before phone outreach",
            "template": "Final Reminder",
            "priority": "High",
        },
        {
            "day": 21,
            "action": "Phone Outreach",
            "description": "Staff phone call for persistent non-responders",
            "template": None,
            "priority": "High",
        },
    ]


# ==============================================================================
# V1.0 LOCATION UPDATE & AUTO-REPLY FUNCTIONS
# ==============================================================================

def generate_location_update_sms(
    consent_url: str,
    patient_first_name: Optional[str] = None,
    use_full_template: bool = False,
) -> SMSTemplate:
    """Generate a location update SMS for practice transition.

    This is the V1.0 primary outreach message focused on location change.

    Args:
        consent_url: Personalized consent form URL
        patient_first_name: Patient's first name (optional for short version)
        use_full_template: Use the longer personalized version

    Returns:
        SMSTemplate with formatted message
    """
    if use_full_template and patient_first_name:
        message = format_message(
            TEMPLATE_LOCATION_UPDATE_SMS_FULL,
            name=patient_first_name,
            consent_url=consent_url
        )
        template_name = "Location Update (Full)"
    else:
        message = format_message(
            TEMPLATE_LOCATION_UPDATE_SMS,
            consent_url=consent_url
        )
        template_name = "Location Update (Concise)"

    return SMSTemplate(
        name=template_name,
        category="initial",
        message=message,
        character_count=len(message),
        sms_segments=count_sms_segments(message),
        is_apcm=False,
        day_offset=0
    )


def generate_privacy_autoreply(
    office_phone: str = DEFAULT_OFFICE_PHONE,
    use_concise: bool = True,
) -> SMSTemplate:
    """Generate an SMS privacy disclaimer auto-reply.

    Use this as an auto-response when patients reply to SMS messages.
    Warns them that SMS is not secure and implies consent if they continue.

    HIPAA Note: This message is compliant because:
    - It warns about SMS insecurity (informed consent)
    - Offers secure alternatives (phone, portal)
    - Implies consent for continued SMS communication
    - Does not contain any PHI

    Args:
        office_phone: Office phone number for callback
        use_concise: Use shorter version (recommended for auto-reply)

    Returns:
        SMSTemplate with formatted message
    """
    if use_concise:
        message = format_message(
            TEMPLATE_SMS_PRIVACY_AUTOREPLY_CONCISE,
            phone=office_phone
        )
        template_name = "SMS Privacy Auto-Reply (Concise)"
    else:
        message = format_message(
            TEMPLATE_SMS_PRIVACY_AUTOREPLY,
            phone=office_phone
        )
        template_name = "SMS Privacy Auto-Reply (Full)"

    return SMSTemplate(
        name=template_name,
        category="autoreply",
        message=message,
        character_count=len(message),
        sms_segments=count_sms_segments(message),
        is_apcm=False,
        day_offset=0
    )


def get_v1_outreach_messages(
    consent_url: str,
    patient_first_name: Optional[str] = None,
    office_phone: str = DEFAULT_OFFICE_PHONE,
) -> dict:
    """Get all V1.0 outreach messages for a patient.

    Returns the primary outreach message and the privacy auto-reply.

    Args:
        consent_url: Personalized consent form URL
        patient_first_name: Patient's first name (optional)
        office_phone: Office phone for auto-reply

    Returns:
        Dict with 'outreach' and 'autoreply' SMSTemplate objects
    """
    return {
        "outreach": generate_location_update_sms(
            consent_url=consent_url,
            patient_first_name=patient_first_name,
            use_full_template=bool(patient_first_name)
        ),
        "autoreply": generate_privacy_autoreply(
            office_phone=office_phone,
            use_concise=True
        ),
    }
