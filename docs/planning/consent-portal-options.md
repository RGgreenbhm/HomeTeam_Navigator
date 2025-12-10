# Consent Portal Options Analysis

## Your Microsoft 365 Licenses

With **Teams Premium** and **Business Premium** (or higher), you have access to:
- Microsoft Forms (Pro features)
- Power Automate (workflow automation)
- SharePoint (secure document storage)
- Azure AD (identity management)
- Teams (secure messaging)

All under your existing **HIPAA BAA with Microsoft**.

---

## Option 1: Microsoft Forms (Recommended Quick Start)

### How It Works
```
Spruce SMS → Unique Form Link → Microsoft Form → Power Automate → SharePoint/Streamlit
```

### Pros
| Advantage | Details |
|-----------|---------|
| **Under existing BAA** | Already HIPAA-compliant with your M365 agreement |
| **No code required** | Build forms in minutes with drag-and-drop |
| **Automatic data collection** | Responses stored in SharePoint automatically |
| **Power Automate integration** | Can trigger workflows on submission |
| **Mobile-friendly** | Works great on patient phones |
| **Fast deployment** | Could be live today |

### Cons
| Limitation | Workaround |
|------------|------------|
| **No DOB verification built-in** | Use unique links per patient instead |
| **Limited customization** | Acceptable for consent forms |
| **Form URL exposes form ID** | Generate unique tokens, embed in form URL params |
| **No native Streamlit sync** | Use Power Automate webhook or poll SharePoint |

### Implementation Steps
1. Create Microsoft Form with consent questions
2. Generate unique patient tokens in Streamlit
3. Create Form links: `https://forms.microsoft.com/...?patient_token=ABC123`
4. Power Automate: On submission → Update SharePoint list → Webhook to Streamlit
5. Send links via Spruce bulk notification

### Sample Form Structure
```
Page 1: Practice Transition Information
- [Read-only text explaining Dr. Green's transition]
- [Checkbox] I have read and understand the above

Page 2: Your Consent Choices
- [Checkbox] I consent to Dr. Green maintaining my medical records
- [Radio] APCM Patients Only:
  - ○ Continue APCM with Dr. Green at Home Team
  - ○ Do not continue APCM
- [Checkbox] I authorize notifying Southview of my choice

Page 3: Confirmation
- [Text] Your Name (to confirm identity)
- [Date] Today's Date
- [Submit]
```

---

## Option 2: SharePoint + Power Apps

### How It Works
```
Spruce SMS → SharePoint Link → Power App Form → SharePoint List → Power Automate → Streamlit
```

### Pros
| Advantage | Details |
|-----------|---------|
| **More customization** | Full control over form design |
| **Built-in authentication** | Can require M365 login (for staff tracking) |
| **Deeper SharePoint integration** | Direct list updates |
| **Conditional logic** | Show/hide questions based on answers |

### Cons
| Limitation | Impact |
|------------|--------|
| **Learning curve** | Takes longer to build |
| **Overkill for simple forms** | Microsoft Forms is simpler |
| **Patient login friction** | External users need SharePoint guest access or anonymous forms |

### Best For
- Internal staff use (tracking consent status)
- Complex multi-step workflows
- When you need audit trail beyond Forms

---

## Option 3: Teams Secure Links (Bookings/Virtual Appointments)

### How It Works
```
Spruce SMS → Teams Meeting Link → Virtual Consent Appointment → Manual Entry
```

### Pros
| Advantage | Details |
|-----------|---------|
| **Personal touch** | Can explain transition verbally |
| **High consent rate** | Patients trust video call |
| **Immediate questions answered** | No confusion about options |
| **Verbal consent documented** | Recording available |

### Cons
| Limitation | Impact |
|------------|--------|
| **Not scalable** | Can't do 1,383 patients quickly |
| **Scheduling overhead** | Need availability slots |
| **Requires patient action** | Must join meeting |

### Best For
- High-value APCM patients who need explanation
- Patients who don't respond to SMS
- Complex consent scenarios

---

## Option 4: Custom Azure Portal (Future)

### How It Works
```
Spruce SMS → Azure Static Web App → DOB Verification → Custom Form → Azure Function → Streamlit DB
```

### Pros
| Advantage | Details |
|-----------|---------|
| **Full control** | Exactly what you want |
| **Best UX** | Custom branding, flow |
| **Direct DB integration** | Real-time updates to Streamlit |
| **DOB verification** | Built-in identity confirmation |
| **Token expiration** | Single-use links |

### Cons
| Limitation | Impact |
|------------|--------|
| **Development time** | 1-2 weeks to build |
| **Requires Azure setup** | Static Web App + Functions |
| **Maintenance** | Code to maintain |

### Best For
- Phase 2 after quick wins with Forms
- When Forms limitations become blockers
- Professional patient experience

---

## Recommended Approach: Phased Implementation

### Phase 1: Microsoft Forms (This Week)
1. Create consent form in Microsoft Forms
2. Generate unique tokens in Streamlit (I'll add this)
3. Create Power Automate flow to update SharePoint
4. Test with 10 patients via Spruce
5. Monitor response rates

### Phase 2: Optimize (Weeks 2-3)
1. Refine form based on patient feedback
2. Add automated reminders via Spruce
3. Build SharePoint → Streamlit sync
4. Track consent completion rates

### Phase 3: Custom Portal (If Needed)
1. Build Azure Static Web App
2. Add DOB verification
3. Direct database integration
4. Professional branded experience

---

## Quick Start: Microsoft Forms Setup

### Step 1: Create the Form
1. Go to https://forms.microsoft.com
2. Click "New Form"
3. Title: "Dr. Green Practice Transition - Consent Form"
4. Add sections as outlined above

### Step 2: Configure Settings
- Settings → Who can fill out this form: **Anyone can respond**
- Settings → Record name: **Yes** (for audit)
- Settings → Shuffle questions: **No**

### Step 3: Get Shareable Link
- Click "Collect responses" → "Link"
- Copy the base URL
- We'll append patient tokens: `?token=UNIQUE_ID`

### Step 4: Power Automate Flow
1. Trigger: "When a new response is submitted"
2. Action: "Get response details"
3. Action: "Create item in SharePoint list"
4. (Optional) Action: "HTTP POST to Streamlit webhook"

### Step 5: Streamlit Integration
I'll add a page to:
- Generate unique tokens per patient
- Build personalized Form URLs
- Track who's been sent links
- Monitor completions

---

## Security Considerations

| Requirement | Microsoft Forms Solution |
|-------------|-------------------------|
| **HIPAA Compliance** | Under your existing BAA |
| **Patient Identity** | Unique token + name confirmation |
| **Audit Trail** | Forms logs all submissions with timestamps |
| **Data Encryption** | Microsoft 365 encryption at rest and in transit |
| **Access Control** | Only you see responses |
| **Consent Documentation** | Stored in SharePoint with timestamp |

---

## Next Steps

1. **You decide**: Start with Microsoft Forms or go straight to custom?
2. **I'll build**: Token generator and Form URL builder in Streamlit
3. **You create**: The Microsoft Form with consent questions
4. **We test**: Small batch via Spruce
5. **Scale up**: Full outreach campaign

---

*Document created: November 30, 2025*
