# BMAD Method Reference

**Consolidated reference for the BMAD methodology.**

Access via `/agent-master-bmad` which spawns the BMAD Master Orchestrator agent.

---

## Overview

BMAD (Build Measure Analyze Decide) is a structured methodology for product development with specialized agent personas, tasks, templates, and workflows.

**Location:** `.bmad-core/` directory

---

## Agent Personas

The BMAD Master can invoke any of these specialized perspectives:

| Agent | Icon | Specialty |
|-------|------|-----------|
| BMad Master | 🧙 | Universal executor - runs any task |
| Analyst | 🔍 | Research, brainstorming, elicitation |
| John (PM) | 📋 | PRDs, product strategy |
| Product Owner | ✅ | Validation, document sharding |
| Winston (Architect) | 🏗️ | System design, architecture |
| UX Expert | 🎨 | UI/UX, front-end specifications |
| Scrum Master | 📊 | Sprints, story drafting |
| Quinn (QA) | 🧪 | Testing, quality gates |
| Developer | 💻 | Implementation |

---

## Tasks (23 Available)

### Planning & Research
| Task | File | Purpose |
|------|------|---------|
| Brainstorming Session | `facilitate-brainstorming-session.md` | Structured ideation |
| Deep Research Prompt | `create-deep-research-prompt.md` | Generate research queries |
| Advanced Elicitation | `advanced-elicitation.md` | Extract requirements |
| Document Project | `document-project.md` | Document existing codebase |
| Index Docs | `index-docs.md` | Create documentation index |

### Document Creation
| Task | File | Purpose |
|------|------|---------|
| Create Document | `create-doc.md` | Create doc from template |
| Shard Document | `shard-doc.md` | Break large doc into pieces |
| Correct Course | `correct-course.md` | Realign project direction |

### Story & Epic Management
| Task | File | Purpose |
|------|------|---------|
| Create Next Story | `create-next-story.md` | Draft next story from epic |
| Validate Next Story | `validate-next-story.md` | Validate story completeness |
| Brownfield Create Epic | `brownfield-create-epic.md` | Epic for existing project |
| Brownfield Create Story | `brownfield-create-story.md` | Story for existing project |

### QA & Testing
| Task | File | Purpose |
|------|------|---------|
| Risk Profile | `risk-profile.md` | Assess implementation risks |
| Test Design | `test-design.md` | Create test strategy |
| Trace Requirements | `trace-requirements.md` | Map tests to requirements |
| NFR Assessment | `nfr-assess.md` | Non-functional requirements |
| Review Story | `review-story.md` | Full quality review |
| QA Gate | `qa-gate.md` | Quality gate decision |
| Apply QA Fixes | `apply-qa-fixes.md` | Implement QA feedback |

### UI/Frontend
| Task | File | Purpose |
|------|------|---------|
| Generate AI Frontend Prompt | `generate-ai-frontend-prompt.md` | Prompt for Lovable/V0 |

---

## Templates (13 Available)

### Product Documentation
- `prd.md` - Product Requirements Document
- `brownfield-prd.md` - PRD for existing projects
- `project-brief.md` - Executive project summary
- `market-research.md` - Market analysis template
- `competitor-analysis.md` - Competitive landscape

### Architecture
- `architecture.md` - System architecture doc
- `brownfield-architecture.md` - Architecture for existing projects
- `front-end-architecture.md` - Frontend-specific architecture
- `fullstack-architecture.md` - Full-stack architecture
- `front-end-spec.md` - Frontend specification

### Development
- `story.md` - User story template
- `qa-gate.md` - Quality gate checklist
- `brainstorming-output.md` - Brainstorming session output

---

## Checklists (6 Available)

| Checklist | Purpose |
|-----------|---------|
| `architect.md` | Architecture review |
| `pm.md` | Product management review |
| `po-master.md` | Product owner validation |
| `story-draft.md` | Story draft quality |
| `story-dod.md` | Story definition of done |
| `change.md` | Change request validation |

---

## Workflows (6 Available)

### Greenfield (New Projects)
- `greenfield-fullstack.md` - Full-stack new project
- `greenfield-service.md` - Backend service new project
- `greenfield-ui.md` - Frontend new project

### Brownfield (Existing Projects)
- `brownfield-fullstack.md` - Full-stack existing project
- `brownfield-service.md` - Backend service existing
- `brownfield-ui.md` - Frontend existing project

---

## Knowledge Base (6 Resources)

| Resource | Content |
|----------|---------|
| `bmad-kb.md` | Complete BMAD methodology guide |
| `brainstorming-techniques.md` | Ideation methods |
| `elicitation-methods.md` | Requirements gathering |
| `technical-preferences.md` | Project-specific tech choices |
| `test-levels-framework.md` | Testing level definitions |
| `test-priorities-matrix.md` | Test prioritization |

---

## Typical Workflows

### Planning Phase
```
1. Research & Brainstorm (Analyst)
2. Create PRD (PM)
3. Create Frontend Spec (UX - if UI project)
4. Create Architecture (Architect)
5. Validate Documents (PO)
6. Shard PRD and Architecture (PO)
```

### Development Phase
```
7. Create Next Story (SM)
8. Risk Assessment (QA - if high-risk)
9. Validate Story (PO - optional)
10. Implement Story (Dev)
11. Review & QA Gate (QA)
12. Commit → Repeat
```

---

## File Structure

```
.bmad-core/
├── agents/        # Agent persona definitions (10)
├── tasks/         # Executable task workflows (23)
├── templates/     # Document templates (13)
├── checklists/    # Quality checklists (6)
├── workflows/     # Complete process workflows (6)
├── data/          # Knowledge base resources (6)
└── core-config.yaml  # Project configuration
```

---

## Access

**Primary:** Use `/agent-master-bmad` to spawn the BMAD Master Orchestrator

The Master can access all agents, tasks, templates, and workflows through the Team Consultation or Exhaustive Report modes.

---

*Reference Version: 1.0*
*Consolidated: 2025-12-03*
