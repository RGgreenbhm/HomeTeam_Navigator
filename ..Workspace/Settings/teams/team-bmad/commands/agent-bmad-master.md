# BMAD Master Orchestrator

Launch the BMAD Master Orchestrator agent for strategic product development oversight and coordinated multi-agent analysis.

## Instructions

Use the Task tool to spawn the `bmad-master-orchestrator` subagent:

```
Task tool with subagent_type='bmad-master-orchestrator'
```

## When to Use This Agent

- **Starting a new session** - Generate StatusUpdates, WorkspaceOverview, or SessionPlanner documents
- **Strategic decisions** - Product decisions that benefit from multiple expert perspectives
- **Project health checks** - Comprehensive milestone reviews
- **Multi-agent coordination** - When multiple BMAD perspectives are needed

## Interaction Modes

The agent will offer three response options:

### Option A: Basic Review
Quick assessment of current state with simple recommendations.

### Option B: Team Consultation
Engages relevant BMAD agents (architect, PM, dev, QA) to provide perspectives, then synthesizes recommendations.

### Option C: Exhaustive Report
Applies all applicable BMAD checklists, workflows, and multi-agent analysis with full artifact preservation.

## BMAD Resources Available

The agent has access to `.bmad-core/` containing:
- **Agents** (10): Master, PM, Architect, UX, SM, QA, Dev, Analyst, PO
- **Tasks** (23): Planning, documentation, stories, QA workflows
- **Templates** (13): PRDs, architecture docs, stories, checklists
- **Checklists** (6): Quality validation at each phase
- **Workflows** (6): Greenfield and brownfield development flows
- **Knowledge Base** (6): BMAD methodology reference

## Context

This workspace is Patient_Explorer - a HIPAA-compliant patient consent tracking and outreach tool (brownfield project).

## Quick Reference

| What You Want | Tell the Agent |
|--------------|----------------|
| Daily briefing | "Generate today's workspace documents" |
| Architectural review | "Review our architecture decisions" |
| Story creation | "Help me create the next story" |
| Quality gate | "Run QA checks on recent changes" |
| Research | "Research [topic] for this project" |
