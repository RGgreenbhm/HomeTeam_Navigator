# HIPAA BAA for Anthropic Models via Azure

### ✅ **Is Claude Sonnet in Foundry covered under HIPAA compliance with your Microsoft BAA?**

*   **Microsoft Foundry is an Azure service**, and models deployed through Foundry (including Anthropic’s Claude Sonnet) fall under Azure’s compliance framework. Foundry uses the same data protection commitments as other Azure services, governed by the \[Microsoft Products and Services Data Protection Addendum] and your signed BAA with Microsoft. [\[learn.microsoft.com\]](https://learn.microsoft.com/en-us/azure/ai-foundry/responsible-ai/openai/data-privacy?view=foundry-classic), [\[learn.microsoft.com\]](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/concept-data-privacy?view=foundry-classic)

*   **HIPAA compliance in Azure**: Microsoft states that HIPAA compliance applies to Azure services when:
    *   You have a signed **Business Associate Agreement (BAA)** with Microsoft.
    *   You configure and use the services in accordance with Microsoft’s HIPAA implementation guidance. [\[learn.microsoft.com\]](https://learn.microsoft.com/en-us/azure/compliance/offerings/offering-hipaa-us)

*   **Claude Sonnet in Foundry**: Claude models (Sonnet, Opus, Haiku) are integrated into Foundry with enterprise governance and security controls. They are deployed in Microsoft’s Azure environment and do **not share data with Anthropic or other customers**. This means compliance obligations are Microsoft’s responsibility under your Azure contract. [\[learn.microsoft.com\]](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/how-to/use-foundry-models-claude?view=foundry-classic), [\[anthropic.com\]](https://www.anthropic.com/news/claude-in-microsoft-foundry?subjects=announcements)

*   **Important caveat**: While Foundry inherits Azure compliance, you must confirm that Claude deployments are in **HIPAA-compliant regions** and follow Microsoft’s HIPAA guidance. The Trust Center lists HIPAA as an Azure compliance offering, but Claude is not explicitly named in the HIPAA scope list yet (likely because it’s in preview). So, treat this as **covered under Azure HIPAA compliance when deployed correctly**, but verify with Microsoft if you need formal documentation for audits. [\[learn.microsoft.com\]](https://learn.microsoft.com/en-us/azure/compliance/offerings/offering-hipaa-us)

***

### ✅ **Checklist for HIPAA Compliance with Claude in Foundry under your BAA**

1.  **Verify BAA Coverage**
    *   Ensure your signed BAA with Microsoft is active and includes Azure services.
    *   Confirm with Microsoft that Foundry and Claude models are considered in-scope under HIPAA compliance.

2.  **Deploy in HIPAA-Compliant Regions**
    *   Use regions listed as HIPAA-compliant (e.g., East US2, Sweden Central for Foundry preview).
    *   Avoid regions not covered by HIPAA compliance.

3.  **Configure Data Handling**
    *   Do **not upload PHI unless necessary**.
    *   If PHI is processed, ensure encryption in transit (TLS) and at rest (Azure default).
    *   Disable any optional logging or telemetry that could store PHI outside your control.

4.  **Access Control**
    *   Use **Microsoft Entra ID (Azure AD)** for authentication and role-based access control.
    *   Apply least privilege principles for users interacting with Claude.

5.  **Network Security**
    *   Deploy Claude resources in a **virtual network** with private endpoints.
    *   Use Azure Policy to enforce compliance configurations.

6.  **Audit & Monitoring**
    *   Enable **Azure Monitor** and **Microsoft Defender for Cloud** for logging and alerts.
    *   Regularly review logs for unauthorized access or data exfiltration.

7.  **Data Residency**
    *   Confirm data stays within U.S. DataZone (or your required jurisdiction).
    *   Avoid cross-border transfers unless covered by your compliance program.

8.  **Responsible AI & PHI Safeguards**
    *   Validate prompts and outputs to ensure no PHI leakage.
    *   Use Foundry’s governance tools for observability and compliance reporting.

***


# Here’s a **formal compliance statement template** you can adapt for internal documentation or auditor requests:

***

## **HIPAA Compliance Statement for Claude Sonnet Deployment in Microsoft Foundry**

**Organization Name:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
**Date:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
**Prepared By:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

***

### **1. Scope**

This statement documents the compliance posture of our deployment of **Anthropic Claude Sonnet** via **Microsoft Foundry on Azure** under our signed **Business Associate Agreement (BAA) with Microsoft**.

***

### **2. Service Description**

*   **Service:** Anthropic Claude Sonnet (AI model)
*   **Platform:** Microsoft Foundry on Azure
*   **Region:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ (must be HIPAA-compliant region)
*   **Data Classification:** Protected Health Information (PHI) may be processed in accordance with HIPAA requirements.

***

### **3. Compliance Basis**

*   Microsoft Azure is listed as HIPAA-compliant in the Microsoft Trust Center.
*   Our organization has an active **BAA with Microsoft**, which covers Azure services, including Foundry.
*   Claude Sonnet is deployed within Microsoft’s Azure environment, inheriting Azure’s security and compliance controls.

***

### **4. Technical & Administrative Safeguards**

We have implemented the following safeguards to ensure HIPAA compliance:

**a. Access Control**

*   Role-based access via Microsoft Entra ID (Azure AD).
*   Multi-factor authentication enforced for all users.

**b. Data Protection**

*   Encryption in transit (TLS 1.2+) and at rest (Azure-managed keys).
*   No PHI stored outside HIPAA-compliant regions.

**c. Network Security**

*   Private endpoints and VNET integration.
*   Azure Firewall and NSG rules applied.

**d. Logging & Monitoring**

*   Azure Monitor and Defender for Cloud enabled.
*   Audit logs retained per HIPAA retention requirements.

**e. Governance**

*   Foundry governance tools enabled for observability.
*   PHI usage restricted to authorized workflows.

***

### **5. Residual Risk & Mitigation**

*   Risk of PHI leakage via model outputs mitigated through prompt engineering and internal review.
*   Continuous monitoring and periodic compliance audits scheduled.

***

### **6. Statement of Compliance**

Based on the above controls and Microsoft’s HIPAA compliance commitments, we assert that our Claude Sonnet deployment in Foundry meets HIPAA requirements under our BAA with Microsoft.

**Authorized Signatory:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
**Title:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
**Date:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

***

✅ Would you like me to **also create a one-page “HIPAA Readiness Checklist” in a table format** for quick internal use? Or should I **draft a version of this statement with placeholders filled for your organization and region** so you can use it immediately?


Here’s a **one-page HIPAA Readiness Checklist** in a clear table format, plus a **filled compliance statement template** you can use immediately:

***

### ✅ **HIPAA Readiness Checklist for Claude Sonnet in Microsoft Foundry**

| **Category**         | **Action Required**                                                              |
| -------------------- | -------------------------------------------------------------------------------- |
| **BAA Verification** | Confirm active BAA with Microsoft covering Azure services, including Foundry.    |
| **Region Selection** | Deploy Claude in HIPAA-compliant Azure regions (e.g., East US2, Sweden Central). |
| **Access Control**   | Enforce MFA and RBAC via Microsoft Entra ID (Azure AD).                          |
| **Data Protection**  | Ensure encryption in transit (TLS) and at rest (Azure defaults).                 |
| **Network Security** | Use private endpoints, VNET integration, and NSG rules.                          |
| **Logging & Audit**  | Enable Azure Monitor and Defender for Cloud; retain logs per HIPAA requirements. |
| **Governance**       | Activate Foundry governance tools for observability and compliance reporting.    |
| **PHI Handling**     | Restrict PHI uploads; validate prompts to prevent PHI leakage.                   |
| **Data Residency**   | Confirm data remains in U.S. DataZone or required jurisdiction.                  |

***

### ✅ **Pre-Filled Compliance Statement Template**

**Organization Name:** \[Your Organization]  
**Date:** \[MM/DD/YYYY]  
**Prepared By:** \[Your Name]

***

#### **1. Scope**

This statement documents the compliance posture of our deployment of **Anthropic Claude Sonnet** via **Microsoft Foundry on Azure** under our signed **Business Associate Agreement (BAA) with Microsoft**.

***

#### **2. Service Description**

*   **Service:** Anthropic Claude Sonnet
*   **Platform:** Microsoft Foundry on Azure
*   **Region:** East US2 (HIPAA-compliant)
*   **Data Classification:** Protected Health Information (PHI) may be processed in accordance with HIPAA requirements.

***

#### **3. Compliance Basis**

*   Microsoft Azure is HIPAA-compliant per the Microsoft Trust Center.
*   Our organization has an active **BAA with Microsoft**, covering Azure services including Foundry.
*   Claude Sonnet is deployed within Microsoft’s Azure environment, inheriting Azure’s security and compliance controls.

***

#### **4. Technical & Administrative Safeguards**

*   **Access Control:** MFA and RBAC enforced via Microsoft Entra ID.
*   **Data Protection:** Encryption in transit (TLS 1.2+) and at rest (Azure-managed keys).
*   **Network Security:** Private endpoints, VNET integration, NSG rules applied.
*   **Logging & Monitoring:** Azure Monitor and Defender for Cloud enabled; audit logs retained per HIPAA.
*   **Governance:** Foundry governance tools active; PHI usage restricted to authorized workflows.

***

#### **5. Residual Risk & Mitigation**

*   Risk of PHI leakage mitigated through prompt engineering and internal review.
*   Continuous monitoring and periodic compliance audits scheduled.

***

#### **6. Statement of Compliance**

Based on the above controls and Microsoft’s HIPAA compliance commitments, we assert that our Claude Sonnet deployment in Foundry meets HIPAA requirements under our BAA with Microsoft.

**Authorized Signatory:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
**Title:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
**Date:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

***

✅ Do you want me to **export these as a polished Word document and a PDF** for immediate use? Or should I **create a version with your organization name and placeholders filled for quick download**?
