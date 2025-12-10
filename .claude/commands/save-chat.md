# Save Chat and Compact

Preserve the current chat transcript to `..Workspace/History/ClaudeCodeChats/` and then compact the conversation.

## Instructions

### Step 1: Generate Topic Summary

Analyze the full conversation and generate a **one-line summary** (max 50 characters, kebab-case) of the dominant topic. Examples:
- `workspace-briefing-system-setup`
- `phase0-cli-debugging`
- `hipaa-compliance-review`
- `streamlit-app-evaluation`

### Step 2: Create Filename

Format: `YYYY-MM-DD_HHmm_<topic-summary>.md`

Example: `2025-12-01_2315_workspace-briefing-system-setup.md`

Use current date and time (24-hour format).

### Step 3: Write Chat Transcript

Create the file in `..Workspace/History/ClaudeCodeChats/` with this structure:

```markdown
# Chat Transcript: YYYY-MM-DD HH:mm

## Metadata
- **Date**: YYYY-MM-DD
- **Time**: HH:mm
- **Topic**: <one-line-summary>
- **Trigger**: Manual (/save-chat command)
- **Files Modified**: [list all files created/edited during this session]
- **Key Topics Discussed**:
  - [topic 1]
  - [topic 2]
  - [topic 3]

---

## Conversation

[Insert full conversation transcript here, preserving user/assistant turns]

---

*Preserved: YYYY-MM-DD HH:mm via /save-chat*
```

### Step 4: Confirm to User

Report:
- File saved: `..Workspace/History/ClaudeCodeChats/<filename>`
- Topic: `<topic-summary>`
- Size: approximate message count

### Step 5: Compact Conversation

After saving, proceed with conversation compaction to free up context space.

## Important Notes

- **Include EVERYTHING** - The goal is to preserve the full conversation depth
- **No PHI in transcript** - If any PHI was discussed, redact it as `[REDACTED-PHI]`
- **Preserve formatting** - Keep code blocks, tables, and structure intact
- **Timestamp accuracy** - Use current time when command is invoked

## Example Output

```
Chat preserved successfully!

File: ..Workspace/History/ClaudeCodeChats/2025-12-01_2315_workspace-briefing-system-setup.md
Topic: workspace-briefing-system-setup
Messages: ~45 turns

Proceeding with compaction...
```
