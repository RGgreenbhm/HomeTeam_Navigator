# HomeTeam_Navigator Setup Reminder

## Claude Code Access

**IMPORTANT**: Grant Claude Code access to this repository before your first coding session.

### Steps to Enable Claude Code:
1. Go to GitHub Settings for this repository
2. Navigate to: Settings > Integrations > GitHub Apps
3. Find "Claude Code" and grant access to `RGgreenbhm/HomeTeam_Navigator`
4. Alternatively, grant organization-wide access if available

## First Session Checklist

- [ ] Grant Claude Code repository access (see above)
- [ ] Create `.env` file from `.env.template`
- [ ] Configure Spruce API credentials for Home Team
- [ ] Set up Azure storage account: `sthometeamworkspace`
- [ ] Run `pip install -r requirements.txt`
- [ ] Test connection: `python -m phase0 test-spruce`

## Cross-Reference Setup

When importing patients who transferred from Green Clinic:
- Include `green_clinic_mrn` field in patient data
- This enables lookup by original Green Clinic MRN

## Inbound Email Monitoring

Monitor: **info@hometeammed.com** for:
- Patient record transfer requests
- Consent form submissions
- Green Clinic transfer communications

---

*Created: December 10, 2025*
