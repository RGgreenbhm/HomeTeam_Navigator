# Session Planner: 2025-12-02

**Days to Deadline: 29**

---

## 1. Session Scratch Notes

*Use this space to capture your stream-of-consciousness thoughts at the start of this session. What's on your mind? What prompted you to open this workspace today?*

```
I want to proceed with scaffolding the infrastructure for chart builder app now, especially if I can delegate more of the planning and refining work to BMAD agent team.  The streamlit app looks great, but has kinks that we will work out together with iterative updates.  When I say We, I'm referring to me and the agent team via Claude Code personnas like BMAD master orchestrator.  

Main pain point at the moment is that we really need to configure access to OneNote to get information that lives there right now.  We found out in yesterday's session that the app based permissions are phased out this year by Microsoft, so we must create an interface for users to sign in via their microsoft OAth credentials.  The simplest approach I see here for this is to find a way for me to sign in with mine (since I have user access to the relevant microsoft OneNote Notebook "Green Clinic Team Notebook" on our sharepoint drive on the southviewteam.com domain that I own, separate from southview medical group).  If that proves easy to login and use my OAuth and 2FA, then at that point, it may not be a big deal to allow other users on my human clinical team to use their own login credentials for microsoft via our streamlit app.  Perhaps we could piggy back on the microsoft signin process to accomplish the sign in procedure needed for me to share a beta version of our streamlit app with another user.  

I'd like to create an early alpha version of the streamlit app that I can package in a way that will let me install it on my computer and on my nurse Jenny's computer tomorrow so she and I can test the development product while she is in clinic with me tomorrow.  Perhaps it can suffice at first just to sign in with my microsoft account in order to get into the Streamlit app, and then to assume that if a user can successfully login southviewteam.com or greenclinicteam.com domains via MS for work account, then it's ok for that user to view all the  information we make available to users in the Strealit "Patient Explorer" app. 

Being able to access that Green Clinic Team Notebook securely and with our Azure based Claude model endpoints to process the data would be huge for our ability to carry out automated chart builder activities, since current patient information is already in OneNote with over a years worth of patient visit worksheets containing a rich amount of data.

However, we need a secure way to send a secure link via e-mail and/or text message from the contact information we have already matched against Spruce contact list and the excel file I got for all my current southview patients.  That link needs to take them to a page the lets them view and click to accept and document their consent for me and my direct staff to take the medical information we have on them with us to Home Team in January, and for those who have APCM already (or are about to go on Medicare and become eligible for it), we need the form to also prompt for their permission to transfer consent for me to bill their APCM claims on my home team account (while simultaneously revoking their consent for southview to bill any APCM charges on them after 12/31/2025 without a new agreement with a different MD at the practice).  We already generated content for this messaging here in the workspace folders, so let's leverage that with form design.  Will defer to our agent team to advise on the best option for generating the beta test version, whether that is through a page generated via Microsoft Forms, or a custom website similar to our streamlit app.  THe focus is to use the tools we have currently available to us and to get the agents to carry this as far as possible overnight while I get a few hours of sleep and prepare to hit the ground running again.  

We already verified the Spruce API connection is working well.

Assume that if our BMAD team can get the configuration right, that I can provide working user login in and carry out the manual 2FA process at least once per day when logging into things in general to get started for the day's work.  

```

---

## 2. Proposed Focus Areas

Based on the Workspace Overview and 29-day countdown, here are the prioritized focus areas.

### Focus Area 1: Phase 0 CLI Validation (CRITICAL)

**Priority: CRITICAL** | **Deadline: December 31, 2025**

The CLI tool exists but has never been tested end-to-end. This MUST happen before any outreach begins.

#### Checklist

- [ ] **Step 1: Verify Environment**
  - Activate venv: `.venv\Scripts\activate`
  - Verify `.env` file has real credentials
  - Run `python -m phase0 --help` to confirm CLI loads

- [ ] **Step 2: Test Spruce API Connection**
  - Run `python -m phase0 test-spruce`
  - Verify contact list retrieval works
  - Document contact count returned
  - Note any rate limits or errors

- [ ] **Step 3: Test Excel Patient Loading**
  - Create/obtain test Excel file in `data/`
  - Run `python -m phase0 load-patients data/patients.xlsx`
  - Verify column detection and row counts
  - Check for encoding or format issues

- [ ] **Step 4: Test Spruce Matching**
  - Run `python -m phase0 match-spruce data/patients.xlsx`
  - Review `data/match_results.csv` output
  - Verify matching logic produces reasonable results
  - Note match rate statistics

- [ ] **Step 5: Initialize SharePoint**
  - Configure SharePoint credentials in `.env`
  - Run `python -m phase0 init-sharepoint`
  - Verify list structure matches ConsentRecord model
  - Note any permission errors

- [ ] **Step 6: End-to-End Import Test**
  - Run `python -m phase0 import-to-sharepoint data/patients.xlsx`
  - Verify patients appear in SharePoint list
  - Confirm no PHI in terminal output
  - Run `python -m phase0 status` to see aggregate stats

---

### Focus Area 2: Staff Workflow Documentation

**Priority: HIGH** | **Supports staff adoption**

#### Checklist

- [ ] **Create Consent Tracking Quickstart**
  - Document daily workflow for tracking team
  - Include SharePoint list navigation
  - Status update procedures

- [ ] **Draft Outreach Templates**
  - SMS template for Spruce messaging
  - Phone call script outline
  - Mail letter template

- [ ] **Define Response Handling**
  - How to record "consented"
  - How to record "declined"
  - Escalation for "unreachable"

- [ ] **Legal Documentation Requirements**
  - What must be retained?
  - In what format?
  - For how long?

---

### Focus Area 3: Streamlit App Decision

**Priority: MEDIUM** | **Decision deadline: December 5**

#### Checklist

- [ ] **Quick Evaluation**
  - Run `streamlit run app/main.py`
  - Test patient list view
  - Test consent tracking features

- [ ] **Compare to CLI**
  - Easier for staff?
  - Additional features?
  - Deployment complexity?

- [ ] **Make Decision**
  - [ ] ADOPT: Create parallel deployment plan
  - [ ] DEFER: Document for post-deadline
  - [ ] ARCHIVE: Remove to reduce confusion

---

## 3. Outstanding User To-Dos

*Items carried forward from previous sessions that still need attention.*

| Item | Source Session | Status |
|------|---------------|--------|
| Fill in scratch notes at session start | 2025-12-01 | Not completed |
| Fill in session intentions | 2025-12-01 | Not completed |
| Validate Spruce API credentials | 2025-12-01 | Not started |
| Test Excel patient loading | 2025-12-01 | Not started |
| Initialize SharePoint consent list | 2025-12-01 | Not started |
| End-to-end workflow test | 2025-12-01 | Not started |

---

## 4. Current Session Intentions

### What I Want to Accomplish THIS Session

*Enter your specific goals for this session:*

```
I'm going to bed... it's 2 AM and I need more sleep than this to keep functioning well.  I'm hoping to hand off enough instructions on my scratch notes on this session planner for bmad team to carry out a long run autonomous session lasting at least 4 hours before they need any manual input from me.   


```

### Items to Discuss Now, But Reserve for Future Sessions

*Topics you want to mention or brainstorm, but not necessarily act on today:*

```
I want to apply a framework for how staff approach their day and interact with AI support that mirrors what I have setup here in this VS code workspace with the daily briefs and this session planner to help with focus.  

Also analogous, I like this framework for how clinical staff should approach a patient visit.  I'd like AI Agent KP (defined in another repo) to review all the information we have available on a patient to give a comprehensive medical assessment similar to workspace overview, as well as a review of all interactions and new documents received about the patient since the last PCP visit that would be similar to our status updates briefing.  Then the Session Planner would be similar to a "Visit Planner" that would identify setup tasks for human and agent team members to address in the before, during, and after phases of the clinical encounter.  

We will need a calendar system in our streamlit app that can keep track of when these patients who consent to come over are expected to need a visit and to help us confirm their appointment times as we prepare for a transition. 

I use Athena health at Home Team as EMR, and we FINALLY got API integration and initial test program approved so we can use live data, but my devops and IT team is not yet experienced in working with Athena for data, and I haven't had a chance to check in with them since I last heard they were setting up an azure data factory account to receive the patient information from Athena APIs and Dataview accound (where we are able to login to Snowflake database account that Athena setup for us that can also see live patient data now).  However, Athena owns the Snowflake account and we have limited control over features they don't already give to us. 

Since the Athena platform has been frustrating to troubleshoot and with very limited customer support and very high cost for integrations, we think long term strategy is much more favorable if we can develop our own patient information tracking and team workflow CRM like system that has HIPAA compliant AI infused to follow rules based logic and general principles advised by me as the chief medical officer.  We anticipate using Open EMR and perhaps using that as the backend service while trying to configure everything for our clinical staff to work directly in our custom apps so we can limit them to ONE program interface, while still using a certified EMR for the backend so long as that will suffice for our industry compliance requirements.  

Plan to model our clinical support user interface to incorporate key features of Open Evidence (see openevidence.com) for the kind of medial grade support AI can provide, as well as the user interface on their website for clinical note taking via ambient recording is very slick, and something I'd like to mirror.  

My CEO (and fairly experience python coder) Pat Rutledge and I have identified that we want to move toward using IBMs granite model and develop our own ligher weight AI models and get away from depending on proprietary models from OpenAI, so we can guarantee we know exactly what our models are trained on, and shape model development in alignment with our values and goals.  

Spruce Health has been a reliable telecommunciations partner.  Their phone system works.  We can SMS text and secure message with patients and patietns can attach douments and photos and do secure video calls all with spruce app on their phone or web interface on computer.  The spruce contact system has cards that let us store additional information about patients and tag and rules system for routing contacts based on tags that could be leveraged for more CRM like benefit at a fraction of Salesforce costs.  THe fact that they include API connections at no additional cost is also a huge plus.  So I'm looking to move more in the direction of custom apps, custome models, spruce, and Open EMR, while cutting back from Microsoft and Athena, and other expensive technology vendors with recurring subscriptions that eat into our productivity.  



```

---

## 5. Session Follow-Up Log

*Append notes throughout the session about tasks for next time.*

### Autonomous Session Completed (2025-12-02, ~3:30 AM)

**BMAD Agent Team Work Completed (All 6 Phases):**

| Deliverable | Status | Location |
|-------------|--------|----------|
| MS OAuth Research Report | DONE | `docs/research/2025-12-02_Microsoft-OAuth-OneNote-Integration.md` |
| OpenEvidence UI Analysis | DONE | `docs/research/2025-12-02_OpenEvidence-UI-Patterns.md` |
| Spruce API Documentation | DONE | `docs/research/2025-12-02_Spruce-Health-API-Capabilities.md` |
| KP Good Shepherd Analysis | DONE | `docs/research/2025-12-02_KP-Good-Shepherd-Analysis.md` |
| Architecture Decision Record | DONE | `docs/architecture/2025-12-02_ADR-001-Beta-App-Architecture.md` |
| S5: MS OAuth Story | DONE | `docs/stories/S5-microsoft-oauth-integration.md` |
| S6: OneNote Story | DONE | `docs/stories/S6-onenote-integration.md` |
| S7: Consent Form Story | DONE | `docs/stories/S7-consent-form-setup.md` |
| S8: SMS Campaign Story | DONE | `docs/stories/S8-sms-outreach-campaign.md` |
| Alpha Deployment Guide | DONE | `docs/planning/alpha-deployment-guide.md` |
| Morning Briefing Synthesis | DONE | `..Workspace_Focus/2025-12-02_MorningBriefingSynthesis.md` |

**Web Research Completed:**
- OpenEvidence.com UI patterns documented (Next.js, MUI components, query bar interface)
- Microsoft Graph OAuth 2.0 delegated permissions flow with Python code examples
- Spruce API capabilities confirmed (messaging, webhooks, bulk SMS, CRM features)
- KP Good Shepherd multi-agent framework analyzed (Magentic orchestration pattern)

**Key Decisions Made:**
1. Use MS OAuth as gate with local session (Decision 1 in ADR-001)
2. Use Microsoft Forms for consent collection (hybrid approach)
3. Direct Graph API for OneNote (delegated auth required by March 2025)
4. Batch script launcher for alpha deployment (simple, no packaging)
5. SQLite only for alpha (add sync later)
6. Azure Claude for AI (HIPAA-compliant under MS BAA)

---

### For User (Before Next Session)

| Task | Priority | Notes |
|------|----------|-------|
| Create Microsoft Form | CRITICAL | See BETA-001 story for form structure |
| Paste Form URL into Streamlit | CRITICAL | Outreach Campaign sidebar |
| Deploy to Jenny's machine | HIGH | Run setup-beta.ps1 |
| Test with 5 patients | HIGH | Before bulk launch |

### For Agent (Next Session Prep)

| Task | Priority | Notes |
|------|----------|-------|
| Review MS Form creation results | HIGH | Iterate if issues |
| Support deployment troubleshooting | HIGH | If Jenny has problems |
| Process first batch responses | MEDIUM | Help with bulk import |

### Cloud Agent Delegation Opportunities

| Task | Suggested Agent | Complexity | Notes |
|------|-----------------|------------|-------|
| Code review of phase0/ module | Claude Code | Low | Verify HIPAA compliance in output |
| Generate consent form templates | Claude | Low | Draft for legal review |

### Deferred to v2.0 (January 2025)

| Task | Notes |
|------|-------|
| KP folder / Good Shepherd agent review | Clinical AI framework |
| OpenEvidence UI patterns implementation | Ambient recording |
| Microsoft user OAuth for OneNote | App-only deprecated March 2025 |
| IBM Granite model evaluation | Custom lightweight models |
| OpenEMR integration research | Long-term EMR strategy |
| Athena API / Data Factory | Team currently setting up |

---

## Session Metadata

- **Generated**: 2025-12-02
- **Reference**: 2025-12-02_WorkspaceOverview.md
- **Days to Deadline**: 29
- **Session Start Time**: _______________
- **Session End Time**: _______________

---

*Tip: Fill in Section 1 (Scratch Notes) and Section 4 (Session Intentions) at the START of your session. Update Section 5 (Follow-Up Log) DURING and at the END of your session.*
