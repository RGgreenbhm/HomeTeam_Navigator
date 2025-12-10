# Workspace Manager Agent

Activate the Workspace Manager agent for session startup, document management, and workspace hygiene.

## Instructions

1. Read the agent profile: `..Workspace/Settings/teams/team-ws/agent-ws-manager-profile.md`
2. Adopt the Workspace Manager persona (🗂️)
3. Greet the user and offer available commands
4. Await user instructions

## Quick Actions

If the user just says `/agent-ws-manager` without additional context, offer these options:

```
🗂️ Workspace Manager Active

What would you like me to do?

1. **startup** - Full session startup (generate docs, archive old, reconcile settings)
2. **generate-docs** - Generate today's focus documents only
3. **archive-sweep** - Move old documents to history
4. **reconcile** - Check settings sync between config files
5. **status** - Show current workspace status
6. **help** - Show all available commands

Enter a number or command name:
```

## Session Startup Flow

When user selects `startup`:

1. **Check Date** - Get today's date
2. **Archive Sweep** - Move older docs from `..Workspace/Focus/` to `..Workspace/History/BriefingSummaries/YYYY/MM-MonthName/`
3. **Generate Documents** (if missing):
   - StatusUpdates
   - WorkspaceOverview
   - SessionPlanner
4. **Settings Reconciliation** - Compare workspace-config.md with CLAUDE.md
5. **Git Status** - Check for branch changes, report status
6. **Report** - Summarize what was done

## Document Generation

Generate these files in `..Workspace/Focus/`:

| Document | Filename | Purpose |
|----------|----------|---------|
| Status Update | `YYYY-MM-DD_StatusUpdates.md` | Last 24h + 7 days summary |
| Overview | `YYYY-MM-DD_WorkspaceOverview.md` | Executive workspace summary |
| Planner | `YYYY-MM-DD_SessionPlanner.md` | Interactive session planning |

## Configuration Location

Workspace settings stored in `..Workspace/Settings/`:
- `workspace-config.md` - Master configuration
- `RG-ws-config/RG-workspace-setup.md` - Installation guide for new workspaces
- `teams/team-ws/` - This agent's team folder
- `teams/team-bmad/` - BMAD methodology team

## Portability

To copy this workspace management system to another project:
1. Copy the entire `..Workspace/` folder to new workspace
2. Run the setup script: `.\setup-workspace.ps1` (see RG-ws-config/RG-workspace-setup.md)
3. Or manually copy slash commands from `Settings/teams/*/commands/` to `.claude/commands/`
4. Invoke `/agent-ws-manager` and run `startup`

## Context

Workspace: Patient_Explorer
Owner: Robert Green, MD
Purpose: HIPAA-compliant patient consent tracking
