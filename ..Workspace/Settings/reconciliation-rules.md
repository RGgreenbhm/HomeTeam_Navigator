# Settings Reconciliation Rules

This document defines how configuration should be synchronized across workspace files.

---

## Source of Truth Hierarchy

1. **`..Workspace/Settings/workspace-config.md`** - Master configuration
2. **`CLAUDE.md`** - AI assistant instructions (should mirror settings)
3. **`README.md`** - User-facing overview (should reference settings)

---

## Reconciliation Process

### At Session Startup

1. **Read master config**: Load `..Workspace/Settings/workspace-config.md`

2. **Check CLAUDE.md alignment**:
   - Verify folder structure matches
   - Verify HIPAA rules match
   - Verify session startup rules match
   - Report discrepancies if found

3. **Check README.md alignment**:
   - Verify project overview matches
   - Verify quick start commands match
   - Report discrepancies if found

4. **If discrepancies found**:
   - List specific differences
   - Ask user: "Should I update [file] to match workspace-config.md?"
   - Apply changes only with user approval

---

## What to Reconcile

### Always Sync
- Folder structure descriptions
- HIPAA compliance rules
- Session startup procedures
- Archive settings

### User Discretion
- Project-specific content (may differ between files)
- Detailed technical instructions (CLAUDE.md may have more detail)
- User-facing summaries (README.md may be simplified)

### Never Auto-Change
- Files in `..Workspace/Reference/` (user-managed)
- Patient data files
- API credentials or secrets

---

## Reconciliation Report Format

When reporting discrepancies, use this format:

```
## Settings Reconciliation Check

### Status: [SYNCED | DISCREPANCIES FOUND]

#### CLAUDE.md
- [ ] Folder structure: [MATCH | MISMATCH]
- [ ] HIPAA rules: [MATCH | MISMATCH]
- [ ] Session rules: [MATCH | MISMATCH]

#### README.md
- [ ] Project overview: [MATCH | MISMATCH]
- [ ] Commands: [MATCH | MISMATCH]

#### Action Required
[List specific updates needed, if any]
```

---

## Manual Override

If user explicitly updates CLAUDE.md or README.md with new content:
- Ask if `workspace-config.md` should be updated to match
- Document the change source in version notes

---

*Last Updated: December 1, 2025*
