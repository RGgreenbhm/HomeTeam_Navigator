# KP (Good Shepherd) Clinical Agent Analysis

**Date:** 2025-12-02
**Status:** Research Complete
**Source:** V:\Projects\KP
**Purpose:** Integration planning for Patient Explorer

---

## Executive Summary

KP ("Good Shepherd") is a multi-agent clinical AI orchestration system built on Microsoft Agent Framework with Magentic orchestration. It provides collaborative AI-assisted patient care through specialized agents.

This framework represents the future clinical AI vision for Patient Explorer and provides patterns for:
- Visit planning (mirroring workspace briefing system)
- Multi-agent collaboration
- Human-in-the-loop clinical workflows
- HIPAA-compliant AI assistance

---

## Architecture Overview

### Technology Stack

| Component | Technology |
|-----------|------------|
| Framework | Microsoft Agent Framework |
| Orchestration | Magentic pattern |
| Models | Azure OpenAI / GitHub Models |
| Runtime | Python 3.10+ |
| Auth | Azure AI Foundry / GitHub PAT |

### Agent Roles

| Agent | Responsibility |
|-------|----------------|
| **Triage** | Initial assessment, vital signs, urgency |
| **Diagnostics** | Differential diagnosis, test ordering |
| **Treatment** | Evidence-based treatment plans |
| **Coordination** | Follow-up, referrals, care transitions |
| **Documentation** | Clinical notes, billing codes |

---

## Magentic Orchestration Pattern

### Core Concepts

1. **Task Ledger** - Maintains facts and plan for the case
2. **Progress Ledger** - Tracks completed and pending tasks
3. **Orchestrator** - Decides which agent acts next
4. **Stall Detection** - Prevents infinite loops
5. **Adaptive Replanning** - Adjusts based on new information

### Workflow Example

```python
# Patient case → Multi-agent assessment → Care plan
workflow = create_kp_workflow()

case = """
Patient: 45-year-old male presenting with:
- Persistent fatigue (3 weeks)
- Occasional chest discomfort
- Family history of coronary artery disease
"""

async for event in workflow.run_stream(case):
    if isinstance(event, MagenticAgentMessageEvent):
        print(f"[{event.agent_name}]: {event.message.text}")
```

---

## Workspace → Visit Model Translation

### Dr. Green's Vision (from SessionPlanner)

The workspace briefing system provides a template for clinical visit planning:

| Workspace Model | Clinical Visit Model |
|-----------------|---------------------|
| **Workspace Overview** | Comprehensive Medical Assessment |
| **Status Updates** | Interaction History Briefing |
| **Session Planner** | Visit Planner |

### Implementation Concept

#### 1. Medical Assessment (like Workspace Overview)

```python
class PatientAssessment:
    """Executive summary of patient's clinical status"""

    def generate(self, patient_id):
        return {
            "summary": "...",  # Current condition summary
            "active_problems": [...],  # Active diagnoses
            "medications": [...],  # Current medications
            "recent_labs": [...],  # Key lab values
            "care_gaps": [...],  # Preventive care due
            "risk_factors": [...]  # Clinical risks
        }
```

#### 2. Interaction History (like Status Updates)

```python
class InteractionHistory:
    """Changes since last PCP visit"""

    def generate(self, patient_id, since_date):
        return {
            "new_documents": [...],  # Received records
            "messages": [...],  # Patient communications
            "calls": [...],  # Phone encounters
            "portal_activity": [...],  # Patient portal use
            "external_visits": [...]  # ER, specialist visits
        }
```

#### 3. Visit Planner (like Session Planner)

```python
class VisitPlanner:
    """Structured workflow for clinical encounter"""

    def generate(self, patient_id, visit_type):
        return {
            "before_visit": [
                {"task": "Review labs", "agent": "diagnostics"},
                {"task": "Check refill requests", "agent": "human"},
            ],
            "during_visit": [
                {"task": "Vitals", "agent": "human"},
                {"task": "History update", "agent": "documentation"},
                {"task": "Assessment", "agent": "diagnostics"},
            ],
            "after_visit": [
                {"task": "Generate note", "agent": "documentation"},
                {"task": "Schedule follow-up", "agent": "coordination"},
            ]
        }
```

---

## HIPAA Compliance Features

### From KP Implementation

1. **Secure Context Management** - PHI handled in encrypted memory
2. **Audit Trail** - All agent interactions logged
3. **Safety Guardrails** - Medication interaction checks
4. **Human-in-the-Loop** - Provider approves care plans

### Alignment with Patient Explorer

- Both use Azure-based AI (covered under Microsoft BAA)
- Both require local encryption (BitLocker)
- Both maintain audit logging
- Both require provider oversight

---

## Integration Roadmap

### Phase 0 (Current - Consent Outreach)

No KP integration needed. Focus on:
- Consent tracking
- Spruce messaging
- SharePoint sync

### Phase 1A (January 2025 - Chart Builder)

Begin KP-style patterns:
- OneNote worksheet parsing
- Basic patient assessment generation
- Documentation agent concepts

### Phase 1B (February 2025 - Clinical Support)

Introduce KP agents:
- Triage assessment from worksheets
- Treatment planning assistance
- Care gap identification

### Phase 2 (Q2 2025 - Full Integration)

Deploy full KP framework:
- Multi-agent orchestration
- Ambient recording + documentation
- Real-time clinical support

---

## BMAD Framework in KP

KP includes a comprehensive BMAD installation:

### Available Agents (BMM Module)
- Analyst
- Architect
- Developer
- Frame Expert (diagrams/wireframes)
- PM
- SM
- TEA (Test Engineering Architect)
- Tech Writer
- UX Designer

### Workflow Categories

1. **Analysis** - Brainstorming, research, product briefs
2. **Planning** - PRD, tech specs, epics/stories, UX design
3. **Solutioning** - Architecture, implementation readiness
4. **Implementation** - Story development, code review, sprint planning

### Test Architecture Knowledge Base

Extensive testing patterns:
- Component TDD
- Contract testing
- Feature flags
- Playwright configuration
- Risk governance

---

## Core Values (Inferred from KP)

### Clinical AI Principles

1. **Assistive, Not Autonomous**
   - AI supports provider decisions
   - Human approval required for care plans
   - "Not a replacement for clinical judgment"

2. **Evidence-Based**
   - Recommendations grounded in guidelines
   - Citations provided
   - Uncertainty acknowledged

3. **Safety First**
   - Medication interaction checks
   - Contraindication warnings
   - Escalation paths for high-risk findings

4. **Privacy Paramount**
   - HIPAA compliance built-in
   - Minimum necessary access
   - Audit everything

5. **Collaborative**
   - Multi-stakeholder (human + AI)
   - Clear role definitions
   - Handoff protocols

---

## Implementation Recommendations

### For Patient Explorer

1. **Adopt Workspace → Visit pattern**
   - Patient Overview (comprehensive assessment)
   - Visit Briefing (recent interactions)
   - Visit Planner (checklist for encounter)

2. **Start with Documentation Agent**
   - Parse OneNote worksheets
   - Generate visit summaries
   - Structure for chart building

3. **Add Triage/Assessment Later**
   - Risk stratification
   - Care gap identification
   - Follow-up prioritization

4. **Eventual Multi-Agent Orchestration**
   - Full KP integration
   - Magentic pattern for complex cases
   - Human-in-the-loop workflows

### Technical Steps

1. Review KP source code for agent definitions
2. Adapt agent patterns for Patient Explorer context
3. Build documentation agent first (lowest risk)
4. Test with de-identified data
5. Iterate based on clinical feedback

---

## Resources

### KP Repository

```
V:\Projects\KP\
├── README.md           # Project overview (reviewed)
├── HIERARCHICAL_ORCHESTRATION.md  # Orchestration patterns
├── BMAD_AGENT_REFERENCE.md        # BMAD usage
├── src/kp/agents/      # Agent implementations
├── .bmad/bmm/          # BMAD module with workflows
```

### Key Files to Review

- `src/kp/orchestration.py` - Magentic workflow setup
- `src/kp/agents/documentation.py` - Documentation agent
- `src/kp/safety.py` - Safety guardrails
- `.bmad/bmm/agents/` - All BMAD agent definitions

---

## Connection to Strategic Vision

### User's Long-Term Goals (from SessionPlanner)

1. **Custom Models** - IBM Granite, own lightweight models
2. **Data Sovereignty** - Know training data, align with values
3. **Single Interface** - One app for clinical staff
4. **Cost Reduction** - Move away from expensive vendors
5. **CRM Capabilities** - Leverage Spruce tags/routing

### KP Alignment

KP provides the clinical AI foundation while allowing:
- Model swapping (Azure → IBM Granite)
- Custom agent development
- Integration with Spruce for communication
- Extension for team workflows

---

*Generated: 2025-12-02 by BMAD Research Agent*
