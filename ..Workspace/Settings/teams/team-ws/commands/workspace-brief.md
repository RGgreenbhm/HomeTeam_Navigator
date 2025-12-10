# Generate Workspace Focus Documents

Generate all three workspace focus documents for today's date.

## Instructions

Using Claude Opus 4.5 in agent mode, perform a comprehensive review of the workspace and generate the following three documents:

### 1. Status Update

Review git history, file modifications, and document changes to create:
- **File**: `..Workspace/Focus/YYYY-MM-DD_StatusUpdates.md`
- **Content**:
  - Summary of work accomplished in the last 24 hours
  - Summary of progress over the last week
  - Key metrics (files changed, commits made, documents created/updated)

### 2. Workspace Overview

Analyze the entire workspace to create an executive summary:
- **File**: `..Workspace/Focus/YYYY-MM-DD_WorkspaceOverview.md`
- **Content**:
  - What information the workspace contains
  - What the workspace goals appear to be at present
  - Which areas or topics are currently active
  - Top 3 areas of focus most ripe for additional development

### 3. Session Planner

Based on the Workspace Overview and previous sessions, create an interactive session planner:
- **File**: `..Workspace/Focus/YYYY-MM-DD_SessionPlanner.md`
- **Content**:
  - **Section 1: Session Scratch Notes** - Empty area for user's stream-of-consciousness thoughts
  - **Section 2: Proposed Focus Areas** - Top 3 focus areas with actionable checklists
  - **Section 3: Outstanding User To-Dos** - Carried forward from last 5 SessionPlanner files
  - **Section 4: Current Session Intentions** - Areas for user to enter this-session goals vs future items
  - **Section 5: Session Follow-Up Log** - Tables for user tasks, agent tasks, and cloud agent delegation

## Execution Steps

1. Check today's date and verify if today's documents already exist in `..Workspace/Focus/`
2. If documents exist, ask user if they want to regenerate
3. **Archive Sweep**: Before generating new documents:
   - Check if `..Workspace/History/BriefingSummaries/YYYY/` folder exists (current year). Create if not.
   - Check if `..Workspace/History/BriefingSummaries/YYYY/MM-MonthName/` folder exists. Create if not.
   - Move any SessionPlanner, StatusUpdates, or WorkspaceOverview files with dates **older than today** to the appropriate archive folder
4. **Review Previous Sessions**: Read last 5 SessionPlanner files to identify:
   - Outstanding user to-do items
   - Patterns in focus areas
   - Uncompleted tasks to carry forward
5. Review git log for recent commits (last 7 days)
6. Scan workspace files for recent modifications
7. Read key documents (CLAUDE.md, README.md, LESSONS-LEARNED.md)
8. Analyze active development areas
9. Generate all three documents in `..Workspace/Focus/`
10. Report completion to user

Replace YYYY-MM-DD with today's date in format: 2025-12-01

## Month Name Reference

| Number | Folder Name |
|--------|-------------|
| 01 | 01-January |
| 02 | 02-February |
| 03 | 03-March |
| 04 | 04-April |
| 05 | 05-May |
| 06 | 06-June |
| 07 | 07-July |
| 08 | 08-August |
| 09 | 09-September |
| 10 | 10-October |
| 11 | 11-November |
| 12 | 12-December |

## Session Planner Template Structure

```markdown
# Session Planner: YYYY-MM-DD

## 1. Session Scratch Notes
[Empty area for user input]

## 2. Proposed Focus Areas
### Focus Area 1: [Title]
- [ ] Task 1
- [ ] Task 2
[repeat for 3 focus areas]

## 3. Outstanding User To-Dos
| Item | Source Session | Status |
|------|---------------|--------|

## 4. Current Session Intentions
### What I Want to Accomplish THIS Session
[Empty area for user input]

### Items to Discuss Now, But Reserve for Future Sessions
[Empty area for user input]

## 5. Session Follow-Up Log
### For User (Before Next Session)
| Task | Priority | Notes |

### For Agent (Next Session Prep)
| Task | Priority | Notes |

### Cloud Agent Delegation Opportunities
| Task | Suggested Agent | Complexity | Notes |
```
