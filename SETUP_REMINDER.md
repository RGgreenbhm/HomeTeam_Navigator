# HomeTeam_Navigator Setup Reminder

## Claude Code Access

**Local CLI (Primary Use)**: No setup needed! Just open terminal in this folder and run `claude`.

### Optional: GitHub Actions Integration
If you want Claude to automatically review PRs on GitHub:
1. Go to: https://github.com/apps/claude
2. Install for `RGgreenbhm/HomeTeam_Navigator`
3. Add `ANTHROPIC_API_KEY` to repository secrets (Settings > Secrets > Actions)

## First Session Checklist

- [ ] (Optional) Install Claude GitHub App for PR reviews
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
