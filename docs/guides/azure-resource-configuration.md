# Azure Resource Configuration Reference

This document captures the Azure resource configuration for Patient_Explorer, including naming conventions, settings, and tagging standards for consistency across related projects.

## Resource Summary

| Resource | Name | Resource Group | Region |
|----------|------|----------------|--------|
| Storage Account | `stgreenclinicworkspace` | `Green_Clinic` | East US 2 |
| Container | `workspace-sync` | - | - |

## Subscription Context

- **Subscription Name**: PAYG-RG-Dev
- **Subscription ID**: `ec8ffbbb-516a-42e9-8489-9c2245954a0d`
- **Primary Admin**: rgreen@greenclinicteam.com

---

## Storage Account Configuration

### Basic Settings

| Setting | Value | Notes |
|---------|-------|-------|
| **Performance** | Standard | Cost-effective for document storage |
| **Redundancy** | GRS (Geo-Redundant) | Required for HIPAA disaster recovery |
| **Account Kind** | StorageV2 | General-purpose v2 |
| **Access Tier** | Hot | Frequently accessed files |

### Security Settings (Advanced Tab)

| Setting | Value | HIPAA Requirement |
|---------|-------|-------------------|
| Require secure transfer | Enabled | Yes - TLS in transit |
| Minimum TLS version | 1.2 | Yes - Modern encryption |
| Allow blob anonymous access | Disabled | Yes - No public data |
| Enable storage account key access | Enabled | Default |
| Default Azure AD authorization | Disabled | Using RBAC instead |

### Networking Settings

| Setting | Value | Notes |
|---------|-------|-------|
| Network access | Public (all networks) | Protected by Azure AD RBAC |
| Routing preference | Microsoft network | Lower latency |

### Data Protection Settings

| Setting | Value | Notes |
|---------|-------|-------|
| Point-in-time restore | Disabled | Not needed for our use case |
| Soft delete for blobs | Enabled, 7 days | Recover accidental deletions |
| Soft delete for containers | Enabled, 7 days | Recover accidental deletions |
| Soft delete for file shares | Enabled, 7 days | Default |
| Blob versioning | Enabled | Track .env and file history |
| Blob change feed | Disabled | Not needed |

### Encryption Settings

| Setting | Value | Notes |
|---------|-------|-------|
| Encryption type | Microsoft-managed keys (MMK) | AES-256, HIPAA compliant |
| CMK support scope | Blobs and files only | We only use blob storage |
| Infrastructure encryption | Disabled | Standard encryption sufficient |

---

## Tagging Standards

Use these tags consistently across all Green Clinic / Patient Explorer Azure resources:

### Required Tags

| Tag Name | Description | Example Values |
|----------|-------------|----------------|
| `Environment` | Deployment environment | `Production`, `Development`, `Staging` |
| `Project` | Project identifier | `Patient_Explorer`, `Green_Clinic_Portal` |
| `Purpose` | Specific resource purpose | `PHI-workspace-sync`, `API-backend`, `Database` |
| `Compliance` | Regulatory compliance | `HIPAA`, `None` |
| `Owner` | Primary contact email | `rgreen@greenclinicteam.com` |
| `CostCenter` | Billing/cost allocation | `Green_Clinic`, `Home_Team_Medical` |

### Tag Values for This Project

```
Environment   = Production
Project       = Patient_Explorer
Purpose       = PHI-workspace-sync
Compliance    = HIPAA
Owner         = rgreen@greenclinicteam.com
CostCenter    = Green_Clinic
```

### Tagging Best Practices

1. **Always apply all 6 tags** to every resource for consistent tracking
2. **Use underscores** in multi-word values (e.g., `Patient_Explorer`, not `Patient-Explorer`)
3. **Owner should be @greenclinicteam.com** domain (post-transition standard)
4. **Mark HIPAA compliance** explicitly for audit purposes

---

## Container Configuration

### workspace-sync Container

| Setting | Value |
|---------|-------|
| Name | `workspace-sync` |
| Public access level | Private (no anonymous access) |
| Purpose | Sync gitignored PHI data between devices |

### Planned Blob Structure

```
workspace-sync/
├── data/                    # Patient data files (PHI)
│   └── *.xlsx, *.db, etc.
├── config/                  # Configuration files
│   └── .env                 # Environment credentials
└── logs/                    # Application logs
    └── *.log
```

---

## RBAC Configuration

### Role Assignments

| User | Role | Scope |
|------|------|-------|
| rgreen@greenclinicteam.com | Storage Blob Data Contributor | Storage Account |
| rgreen@southviewteam.com | Storage Blob Data Contributor | Storage Account (transition period) |

### Role Description

**Storage Blob Data Contributor** allows:
- Read, write, and delete blob data
- Does NOT allow managing storage account settings
- Suitable for data sync operations

---

## Related Resources in Green_Clinic Resource Group

| Resource Type | Name | Purpose |
|---------------|------|---------|
| Azure OpenAI | (existing) | AI Foundry for Claude models |
| Document Intelligence | (existing) | OCR processing |
| SQL Server | (existing) | Application database |
| SQL Database | (existing) | Application data |
| **Storage Account** | stgreenclinic | **NEW - Workspace sync** |

---

## CLI Reference

### Login to Azure

```bash
az login
```

### Verify Storage Account

```bash
az storage account show \
  --name stgreenclinicworkspace \
  --resource-group Green_Clinic \
  --query "{name:name, location:location, sku:sku.name}"
```

### List Containers

```bash
az storage container list \
  --account-name stgreenclinicworkspace \
  --auth-mode login \
  --query "[].name"
```

### Upload Test File

```bash
az storage blob upload \
  --account-name stgreenclinicworkspace \
  --container-name workspace-sync \
  --name test.txt \
  --data "Hello Azure" \
  --auth-mode login
```

---

## Security Checklist

- [x] **Encryption at rest**: AES-256 (Microsoft-managed keys)
- [x] **Encryption in transit**: TLS 1.2+ required
- [x] **No anonymous access**: Public blob access disabled
- [x] **Azure AD authentication**: RBAC for authorized users only
- [x] **Soft delete enabled**: 7-day recovery window
- [x] **Blob versioning**: Track file history
- [x] **Geo-redundancy**: RA-GRS for disaster recovery with read access
- [x] **HIPAA compliance tags**: Explicitly marked
- [x] **Default OAuth authentication**: Enabled

---

*Created: 2025-12-08*
*Last Updated: 2025-12-08*
*Storage Account URL: https://stgreenclinicworkspace.blob.core.windows.net*
