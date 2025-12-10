# SharePoint Architecture Proposal

**Status:** Idea - Pending BMAD Analysis
**Created:** December 1, 2025
**Priority:** Future consideration

---

## Proposal Summary

Integrate SharePoint as a team collaboration layer for Patient Explorer:

1. **Store patient database on SharePoint** - Team-accessible data
2. **Leverage access logs** - Built-in M365 audit compliance
3. **Publish Streamlit as SharePoint site** - Single URL for team (online mode)
4. **Fallback to local Streamlit** - Offline capability preserved

---

## Questions for BMAD Analysis

### Analyst (Mary)
- What team collaboration workflows exist today?
- How do staff currently share patient status updates?
- What offline scenarios need support?
- Who needs access and from where?

### Architect (Winston)
- PHI handling in SharePoint lists - acceptable under BAA?
- Sync conflict resolution between local SQLite and SharePoint
- Performance implications for list-based queries
- Authentication flow for Streamlit ↔ SharePoint

### PM (John)
- User stories for team collaboration
- Acceptance criteria for offline/online modes
- Migration path from current architecture

### UX (Sally)
- How would team members access the app?
- What's the experience when offline?
- SharePoint embedding limitations

---

## Preliminary Architecture Options

### Option A: SharePoint for Non-PHI Tracking Only
- Consent status (no PHI)
- Audit logs
- Team assignments

### Option B: Full SharePoint Database
- All patient data in SharePoint lists
- Local cache for offline
- Requires careful PHI handling

### Option C: Azure App Service + SharePoint Dashboard
- Host Streamlit on Azure (internal)
- SharePoint for dashboards/reporting only

---

## Next Steps

Run through BMAD agent questioning when ready to implement team collaboration features.

---

*Filed: December 1, 2025*
